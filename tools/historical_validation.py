"""Authenticate historical bytes without depending on checkout line endings."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path


def authenticated_bytes(path: Path, root: Path, commit: str = "HEAD") -> bytes:
    """Return raw Git bytes after checking the artifact actually being validated.

    Only text LF/CRLF conversion is permitted; binary artifacts remain exact.
    Never fall back to unauthenticated checkout bytes when Git authority is absent.
    """
    relative = path.relative_to(root).as_posix()
    committed = subprocess.check_output(["git", "show", f"{commit}:{relative}"], cwd=root)
    local = path.read_bytes()
    if path.suffix == ".gz" or b"\0" in committed:
        matches = local == committed
    else:
        matches = local.replace(b"\r\n", b"\n") == committed.replace(b"\r\n", b"\n")
    if not matches:
        raise ValueError(f"historical artifact differs from Git authority: {relative}")
    return committed


def authenticated_sha256(path: Path, root: Path, commit: str = "HEAD") -> str:
    return hashlib.sha256(authenticated_bytes(path, root, commit)).hexdigest()


def recorded_checkout_sha_matches(path: Path, recorded: str, root: Path) -> bool:
    """Check legacy checkout hashes without rewriting their recorded SHA-256.

    Some early evidence recorded Windows checkout bytes rather than Git bytes.
    Reconstruct only LF and CRLF serializations of the authenticated artifact.
    Committed-byte contracts must use authenticated_sha256 instead.
    """
    raw = authenticated_bytes(path, root)
    lf = raw.replace(b"\r\n", b"\n")
    versions = {raw, lf, lf.replace(b"\n", b"\r\n")}
    return recorded in {hashlib.sha256(value).hexdigest() for value in versions}


def authenticated_blob_oid(path: Path, root: Path) -> str:
    """Hash the authenticated blob without applying checkout clean filters again."""
    raw = authenticated_bytes(path, root)
    return (
        subprocess.check_output(["git", "hash-object", "--stdin"], input=raw, cwd=root)
        .decode("ascii")
        .strip()
    )
