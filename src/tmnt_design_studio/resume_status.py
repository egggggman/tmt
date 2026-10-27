"""Bounded, status-only telemetry. Never authenticates or opens a checkpoint."""

from __future__ import annotations

import multiprocessing
import os
import tempfile
import time
from pathlib import Path

from tmnt_design_studio.calibration_integrity import _replace_with_retry
from tmnt_design_studio.resume_authorization import (
    ResumeRefused,
    encoded,
    plain_path,
    require,
    strict_json,
)

PROTOCOL = "durable-status-v1"
STATUS_NAME = "durable-status.json"
MAX_BYTES = 4096


def status_path(path: Path) -> Path:
    require(path.name == STATUS_NAME, "status-only filename required")
    return plain_path(path)


def publish_status(path: Path, *, authorization: str, count: int, checkpoint_sha256: str) -> None:
    path = status_path(path)
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
    fd, temporary = tempfile.mkstemp(prefix=".status-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        _replace_with_retry(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _read_shared(path: str) -> bytes:
    if os.name != "nt":
        with open(path, "rb") as handle:
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
    handle = kernel.CreateFileW(path, 0x80000000, 7, None, 3, 0x80, None)
    if handle == w.HANDLE(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        fd = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
    except BaseException:
        kernel.CloseHandle(handle)
        raise
    with os.fdopen(fd, "rb") as stream:
        return stream.read(MAX_BYTES + 1)


def _worker(path: str, connection) -> None:
    try:
        # Close the file before sending bytes; no tail-following persistent handle.
        connection.send_bytes(_read_shared(path))
    except (OSError, ValueError):
        connection.send_bytes(b"")
    finally:
        connection.close()


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
    path: Path, *, authorization: str, timeout: float = 0.25, max_age: float = 5.0
) -> dict:
    """Return UNKNOWN on unavailable/incompatible telemetry; kill slow read workers.

    Timeout includes worker startup; a slow host may report UNKNOWN. This is a
    supervisory deadline, not a hard real-time scheduling guarantee.
    """
    worker = None
    receiver = sender = None
    try:
        path = status_path(path)
        require(0 < timeout <= 0.25 and 0 < max_age <= 5.0, "invalid monitor bounds")
        context = multiprocessing.get_context("spawn")
        receiver, sender = context.Pipe(duplex=False)
        worker = context.Process(target=_worker, args=(str(path), sender), daemon=True)
        started = time.monotonic()
        worker.start()
        sender.close()
        require(receiver.poll(max(0, timeout - (time.monotonic() - started))), "status timeout")
        data = receiver.recv_bytes(MAX_BYTES + 1)
        return parse_status(data, authorization=authorization, max_age=max_age)
    except (OSError, ValueError, TypeError, EOFError, ResumeRefused):
        return {"state": "UNKNOWN"}
    finally:
        if worker is not None and worker.pid is not None:
            if worker.is_alive():
                worker.terminate()
            worker.join()
        for pipe in (receiver, sender):
            if pipe is not None:
                pipe.close()
