"""Trusted telemetry location and pre-write role checks; no authority is issued here."""

from __future__ import annotations

import os
import stat
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from tmnt_design_studio.resume_authorization import plain_path, require

STATUS_NAME = "durable-status.json"


def directory_identity(path: Path) -> tuple[int, int]:
    info = path.stat()
    require(stat.S_ISDIR(info.st_mode), "directory required")
    return info.st_dev, info.st_ino


def disjoint(left: Path, right: Path) -> bool:
    return not (left.is_relative_to(right) or right.is_relative_to(left))


@dataclass(frozen=True)
class TelemetryGrant:
    """In-process trusted capability, independent of status/checkpoint contents."""

    root: Path
    root_identity: tuple[int, int]
    protected_roots: tuple[Path, ...]
    authorization: str

    def validate(self, path: Path) -> Path:
        root = plain_path(self.root)
        require(directory_identity(root) == tuple(self.root_identity), "telemetry root replaced")
        require(bool(self.protected_roots), "protected file roles required")
        for protected in self.protected_roots:
            require(disjoint(root, plain_path(protected)), "telemetry/protected role overlap")
        candidate = plain_path(path)
        require(candidate == root / STATUS_NAME, "outside authorized telemetry root")
        if candidate.exists():
            require(stat.S_ISREG(candidate.stat().st_mode), "regular status file required")
        return candidate


@contextmanager
def telemetry_root(grant: TelemetryGrant, path: Path):
    """Pin directory identity; Windows also denies renaming the opened root."""
    candidate = grant.validate(path)
    handle = None
    kernel = None
    descriptor = None
    try:
        if os.name == "nt":
            import ctypes
            import ctypes.wintypes as w

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
            handle = kernel.CreateFileW(str(grant.root), 0x80, 3, None, 3, 0x02200000, None)
            if handle == w.HANDLE(-1).value:
                handle = None
                raise ctypes.WinError(ctypes.get_last_error())
            require(
                windows_handle_path(handle) == plain_path(grant.root), "root handle path mismatch"
            )
        else:
            descriptor = os.open(grant.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            info = os.fstat(descriptor)
            require(
                (info.st_dev, info.st_ino) == tuple(grant.root_identity), "root handle mismatch"
            )
        grant.validate(candidate)
        yield descriptor
        grant.validate(candidate)
    finally:
        if handle is not None:
            kernel.CloseHandle(handle)
        if descriptor is not None:
            os.close(descriptor)


def verify_status_handle(descriptor: int, path: Path, grant: TelemetryGrant) -> None:
    """Check opened object identity, not just the caller's spelling of its path."""
    grant.validate(path)
    opened, current = os.fstat(descriptor), path.stat()
    require(stat.S_ISREG(opened.st_mode) and opened.st_nlink == 1, "status handle alias")
    require((opened.st_dev, opened.st_ino) == (current.st_dev, current.st_ino), "status replaced")
    if os.name == "nt":
        import msvcrt

        require(
            windows_handle_path(msvcrt.get_osfhandle(descriptor)) == path,
            "opened outside telemetry root",
        )


def windows_handle_path(handle) -> Path:
    import ctypes
    import ctypes.wintypes as w

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetFinalPathNameByHandleW.argtypes = [w.HANDLE, w.LPWSTR, w.DWORD, w.DWORD]
    kernel.GetFinalPathNameByHandleW.restype = w.DWORD
    buffer = ctypes.create_unicode_buffer(32768)
    size = kernel.GetFinalPathNameByHandleW(handle, buffer, len(buffer), 0)
    require(0 < size < len(buffer), "handle path unavailable")
    name = buffer.value
    if name.startswith("\\\\?\\UNC\\"):
        name = "\\\\" + name[8:]
    elif name.startswith("\\\\?\\"):
        name = name[4:]
    return Path(name)
