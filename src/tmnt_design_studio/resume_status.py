"""Bounded, status-only telemetry. Never authenticates or opens a checkpoint."""

from __future__ import annotations

import multiprocessing
import os
import secrets
import tempfile
import time
from contextlib import suppress
from pathlib import Path

from tmnt_design_studio.calibration_integrity import _replace_with_retry
from tmnt_design_studio.monitor_cleanup import MonitorFailure, claim_monitor
from tmnt_design_studio.monitor_cleanup import cleanup_status as cleanup_status
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
    """Bound the caller, retain unresolved ownership, and never accept a late sample.

    Failure keeps the legacy UNKNOWN mapping; MonitorFailure.report() exposes
    timeout/ownership and original cleanup errors. OS exit cannot be guaranteed.
    """
    if type(timeout) not in (int, float) or not 0 < timeout <= 0.25:
        return {"state": "UNKNOWN"}
    started = time.monotonic()
    deadline = started + timeout
    try:
        require(grant is not None, "authorized telemetry root required")
        # Only lexical checks here. Disk metadata and handle validation run in
        # the supervised child, so slow storage cannot block this caller.
        path = Path(path).absolute()
        require(path == grant.root.absolute() / STATUS_NAME, "outside authorized telemetry root")
        require(grant.authorization == authorization, "telemetry authority mismatch")
        require(0 < timeout <= 0.25 and 0 < max_age <= 5.0, "invalid monitor bounds")
    except (OSError, ValueError, TypeError, EOFError, ResumeRefused):
        return {"state": "UNKNOWN"}

    owner, claimed = claim_monitor(deadline)
    if not claimed:
        return MonitorFailure("OWNERSHIP_UNRESOLVED", owner)

    def sample() -> None:
        context = multiprocessing.get_context("spawn")
        require(not owner.cancelled.is_set(), "cancelled setup")
        owner.buffer = context.RawArray("B", MAX_BYTES + 4)
        require(not owner.cancelled.is_set(), "cancelled setup")
        owner.worker = context.Process(
            target=_worker, args=(str(path), grant, owner.buffer), daemon=True
        )
        require(not owner.cancelled.is_set(), "cancelled start")
        owner.stage = "STARTING"
        owner.worker.start()
        if time.monotonic() >= owner.work_deadline:
            owner.cancelled.set()
            raise ResumeRefused("startup timeout")
        owner.stage = "READING"
        owner.worker.join(timeout=max(0, owner.work_deadline - time.monotonic()))
        if owner.worker.is_alive():
            owner.cancelled.set()
            raise ResumeRefused("sample timeout")
        require(owner.worker.exitcode == 0, "sample failure")
        length = int.from_bytes(bytes(owner.buffer[:4]), "little")
        require(0 < length <= MAX_BYTES, "incomplete status response")
        payload = parse_status(
            bytes(owner.buffer[4 : 4 + length]), authorization=authorization, max_age=max_age
        )
        require(time.monotonic() <= deadline and not owner.cancelled.is_set(), "late sample")
        owner.result = payload

    owner.launch(sample)
    completed = owner.finished.wait(max(0, deadline - time.monotonic()))
    if not completed or time.monotonic() > deadline or owner.cancelled.is_set():
        owner.cancelled.set()
        return MonitorFailure("TIMEOUT", owner)
    if (
        owner.closed.is_set()
        and owner.result is not None
        and not owner.cancelled.is_set()
        and not owner.errors
    ):
        return owner.result
    return MonitorFailure("UNAVAILABLE" if owner.closed.is_set() else "OWNERSHIP_UNRESOLVED", owner)
