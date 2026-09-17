"""Compile-only integrity guard for generated Calibration V1 launchers."""

from __future__ import annotations

import hashlib
import py_compile
import subprocess
from pathlib import Path


def _lf_equivalent(checkout: bytes, committed: bytes) -> bool:
    return checkout.replace(b"\r\n", b"\n") == committed.replace(b"\r\n", b"\n")


def validate_launcher(
    path: Path,
    *,
    git_root: Path | None = None,
    repository_path: str | None = None,
    expected_committed_sha256: str | None = None,
    sidecar: Path | None = None,
) -> str:
    """Compile after strict Git-blob authentication; LF/CRLF checkout drift only is accepted."""
    before = path.read_bytes()
    digest = hashlib.sha256(before).hexdigest().upper()
    if repository_path is not None:
        if git_root is None or expected_committed_sha256 is None or sidecar is None:
            raise RuntimeError("complete committed launcher authentication is required")
        committed = subprocess.check_output(
            ["git", "show", f"HEAD:{repository_path}"], cwd=git_root
        )
        committed_digest = hashlib.sha256(committed).hexdigest().upper()
        if committed_digest != expected_committed_sha256.upper():
            raise RuntimeError("committed launcher blob hash mismatch")
        sidecar_digest = sidecar.read_text(encoding="ascii").strip().split()[0].upper()
        if sidecar_digest != committed_digest:
            raise RuntimeError("launcher sidecar hash mismatch")
        if not _lf_equivalent(before, committed):
            raise RuntimeError("checkout launcher differs from committed blob")
    py_compile.compile(str(path), doraise=True)
    if path.read_bytes() != before:
        raise RuntimeError("launcher changed during compile validation")
    return digest
