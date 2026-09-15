"""Compile-only integrity guard for generated Calibration V1 launchers."""

from __future__ import annotations

import hashlib
import py_compile
from pathlib import Path


def validate_launcher(path: Path) -> str:
    """Compile exact on-disk bytes and reject any change during validation."""
    before = path.read_bytes()
    digest = hashlib.sha256(before).hexdigest()
    py_compile.compile(str(path), doraise=True)
    after = path.read_bytes()
    if after != before:
        raise RuntimeError("launcher changed during compile validation")
    return digest
