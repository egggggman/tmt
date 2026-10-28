"""Bounded, status-only telemetry. Never authenticates or opens a checkpoint."""

from __future__ import annotations

import multiprocessing
import os
import secrets
import tempfile
import threading
import time
from contextlib import suppress
from pathlib import Path

from tmnt_design_studio.calibration_integrity import _replace_with_retry
from tmnt_design_studio.resume_authorization import (
    ResumeRefused,
    encoded,
    require,
    strict_json,
)
from tmnt_design_studio.resume_paths import STATUS_NAME as STATUS_NAME
from tmnt_design_studio.resume_paths import (
    TelemetryGrant,
    telemetry_root,
    verify_status_handle,
)

PROTOCOL = "durable-status-v1"
MAX_BYTES = 4096


def status_path(path: Path, grant: TelemetryGrant | None = None) -> Path:
    require(grant is not None, "authorized telemetry root required")
    return grant.validate(path)


def publish_status(
    path: Path,
    *,
    authorization: str,
    count: int,
    checkpoint_sha256: str,
    grant: TelemetryGrant | None = None,
) -> None:
    path = status_path(path, grant)
    require(grant.authorization == authorization, "telemetry authority mismatch")
    data = encoded(
        dict(
            protocol=PROTOCOL,
            authorization=authorization,
            committed_games=count,
            checkpoint_sha256=checkpoint_sha256,
            heartbeat=time.time(),
        )
    )
    require(len(data) <= MAX_BYTES, "status too large")
    with telemetry_root(grant, path) as directory_fd:
        if directory_fd is None:
            fd, temporary = tempfile.mkstemp(prefix=".status-", dir=path.parent)
        else:
            temporary = ".status-" + secrets.token_hex(16)
            fd = os.open(
                temporary,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=directory_fd,
            )
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            grant.validate(path)
            if directory_fd is None:
                _replace_with_retry(temporary, path)
            else:
                _replace_with_retry(temporary, Path(STATUS_NAME), directory_fd=directory_fd)
        finally:
            if directory_fd is None:
                if os.path.exists(temporary):
                    os.unlink(temporary)
            else:
                with suppress(FileNotFoundError):
                    os.unlink(temporary, dir_fd=directory_fd)


def _read_shared(path: str, grant: TelemetryGrant) -> bytes:
    with telemetry_root(grant, Path(path)) as directory_fd:
        return _read_handle(path, grant, directory_fd)


def _read_handle(path: str, grant: TelemetryGrant, directory_fd: int | None = None) -> bytes:
    if os.name != "nt":
        descriptor = os.open(STATUS_NAME, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory_fd)
        with os.fdopen(descriptor, "rb") as handle:
            verify_status_handle(handle.fileno(), Path(path), grant)
            return handle.read(MAX_BYTES + 1)
    import ctypes
    import ctypes.wintypes as w
    import msvcrt

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [
        w.LPCWSTR,
        w.DWORD,
        w.DWORD,
        w.LPVOID,
        w.DWORD,
        w.DWORD,
        w.HANDLE,
    ]
    kernel.CreateFileW.restype = w.HANDLE
    kernel.CloseHandle.argtypes = [w.HANDLE]
    # Read access only; non-inheritable; share read/write/delete. No checkpoint path.
    handle = kernel.CreateFileW(path, 0x80000000, 7, None, 3, 0x00200080, None)
    if handle == w.HANDLE(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        fd = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
    except BaseException:
        kernel.CloseHandle(handle)
        raise
    with os.fdopen(fd, "rb") as stream:
        verify_status_handle(stream.fileno(), Path(path), grant)
        return stream.read(MAX_BYTES + 1)


def _worker(path: str, grant: TelemetryGrant, buffer) -> None:
    try:
        data = _read_shared(path, grant)
        require(len(data) <= MAX_BYTES, "oversized status")
        buffer[4 : 4 + len(data)] = data
        buffer[:4] = len(data).to_bytes(4, "little")
    except (OSError, ValueError, ResumeRefused):
        return


def parse_status(data: bytes, *, authorization: str, max_age: float = 5.0) -> dict:
    require(0 < len(data) <= MAX_BYTES, "invalid status length")
    payload = strict_json(data)
    require(isinstance(payload, dict), "invalid status object")
    require(payload.get("protocol") == PROTOCOL, "unsupported status protocol")
    require(payload.get("authorization") == authorization, "foreign status")
    count = payload.get("committed_games")
    require(type(count) is int and 732 <= count <= 900, "invalid progress")
    checkpoint_hash = payload.get("checkpoint_sha256")
    require(
        isinstance(checkpoint_hash, str)
        and len(checkpoint_hash) == 64
        and all(c in "0123456789abcdef" for c in checkpoint_hash),
        "invalid reported hash",
    )
    heartbeat = payload.get("heartbeat")
    require(type(heartbeat) in (int, float), "invalid heartbeat")
    require(0 <= time.time() - heartbeat <= max_age, "stale/future heartbeat")
    return {**payload, "state": "REPORTED_ONLY"}


def read_status(
    path: Path,
    *,
    authorization: str,
    timeout: float = 0.25,
    max_age: float = 5.0,
    grant: TelemetryGrant | None = None,
) -> dict:
    """Return UNKNOWN on unavailable/incompatible telemetry; kill slow read workers.

    Timeout includes worker startup; a slow host may report UNKNOWN. This is a
    supervisory deadline, not a hard real-time scheduling guarantee.
    """
    if type(timeout) not in (int, float) or not 0 < timeout <= 0.25:
        return {"state": "UNKNOWN"}
    started = time.monotonic()
    deadline = started + timeout
    work_deadline = started + timeout * 0.6  # Reserve time for termination and reap.
    worker = None
    buffer = None
    ready, cancelled = threading.Event(), threading.Event()
    cleanup = threading.Lock()
    launch_errors = []

    def stop() -> None:
        if not cleanup.acquire(timeout=max(0, deadline - time.monotonic())):
            return
        try:
            if worker is not None and worker.pid is not None:
                if worker.is_alive():
                    worker.terminate()
                worker.join(timeout=max(0, deadline - time.monotonic()))
                if not worker.is_alive():
                    worker.close()
        except (OSError, ValueError, AssertionError):
            return  # A concurrent late start/cleanup still returns UNKNOWN.
        finally:
            cleanup.release()

    def launch() -> None:
        nonlocal worker, buffer
        try:
            context = multiprocessing.get_context("spawn")
            if cancelled.is_set():
                return
            buffer = context.RawArray("B", MAX_BYTES + 4)
            if cancelled.is_set():
                return
            worker = context.Process(target=_worker, args=(str(path), grant, buffer), daemon=True)
            if cancelled.is_set():
                worker.close()
                return
            worker.start()
        except Exception as error:
            launch_errors.append(error)
        finally:
            ready.set()
        if cancelled.is_set():
            stop()  # Also cancel a start that completed after the caller's budget.

    try:
        require(grant is not None, "authorized telemetry root required")
        # Only lexical checks here. Disk metadata and handle validation run in
        # the supervised child, so slow storage cannot block this caller.
        path = Path(path).absolute()
        require(path == grant.root.absolute() / STATUS_NAME, "outside authorized telemetry root")
        require(grant.authorization == authorization, "telemetry authority mismatch")
        require(0 < timeout <= 0.25 and 0 < max_age <= 5.0, "invalid monitor bounds")
        # Fixed shared memory replaces framed pipe receive completely. Read only
        # after child exit: partial/in-progress responses are never accepted.
        threading.Thread(target=launch, daemon=True).start()
        require(ready.wait(max(0, work_deadline - time.monotonic())), "startup timeout")
        require(not launch_errors, "worker startup failed")
        worker.join(timeout=max(0, work_deadline - time.monotonic()))
        require(not worker.is_alive() and worker.exitcode == 0, "status timeout/failure")
        length = int.from_bytes(bytes(buffer[:4]), "little")
        require(0 < length <= MAX_BYTES, "incomplete status response")
        payload = parse_status(
            bytes(buffer[4 : 4 + length]), authorization=authorization, max_age=max_age
        )
        require(time.monotonic() <= deadline, "status deadline exceeded")
        return payload
    except (OSError, ValueError, TypeError, EOFError, ResumeRefused):
        return {"state": "UNKNOWN"}
    finally:
        cancelled.set()
        stop()
