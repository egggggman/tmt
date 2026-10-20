"""Fail-closed persistence and read-back validation for simulation artifacts."""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import uuid
import zlib
from collections.abc import Mapping
from pathlib import Path
from typing import Any


class ArtifactIntegrityError(ValueError):
    """Raised when an artifact cannot be authenticated or reconstructed."""


def _bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _check_manifest(payload: Mapping[str, Any], expected: Mapping[str, Any] | None) -> None:
    if expected is None:
        return
    for key, value in expected.items():
        if payload.get(key) != value:
            raise ArtifactIntegrityError(
                f"manifest mismatch for {key!r}: expected {value!r}, got {payload.get(key)!r}"
            )


def read_validated_artifact(
    path: Path,
    *,
    expected_sha256: str | None = None,
    expected_manifest: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], str]:
    """Read, decompress, parse, and authenticate one finalized artifact."""

    try:
        raw = path.read_bytes()
        payload = json.loads(gzip.decompress(raw))
    except (
        OSError,
        EOFError,
        gzip.BadGzipFile,
        zlib.error,
        json.JSONDecodeError,
        UnicodeDecodeError,
    ) as exc:
        raise ArtifactIntegrityError(f"invalid gzip artifact {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ArtifactIntegrityError(f"artifact payload must be an object: {path}")
    digest = sha256_bytes(raw)
    if expected_sha256 is not None and digest != expected_sha256:
        raise ArtifactIntegrityError(
            f"artifact hash mismatch: expected {expected_sha256}, got {digest}"
        )
    _check_manifest(payload, expected_manifest)
    return payload, digest


def write_validated_artifact(
    path: Path,
    payload: Mapping[str, Any],
    *,
    expected_manifest: Mapping[str, Any] | None = None,
) -> str:
    """Atomically publish a validated gzip artifact and verify durable read-back.

    A failed temporary write is retained with a ``.quarantine`` suffix and is
    never reported as the finalized artifact.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    raw = gzip.compress(_bytes(payload), mtime=0)
    try:
        with temp.open("xb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        read_validated_artifact(temp, expected_manifest=expected_manifest)
        os.replace(temp, path)
        # Verify the bytes after the atomic publication, not only the temp file.
        _, digest = read_validated_artifact(path, expected_manifest=expected_manifest)
        return digest
    except Exception:
        if temp.exists():
            quarantine = temp.with_suffix(".quarantine")
            os.replace(temp, quarantine)
        raise


def assert_new_control_classification(payload: Mapping[str, Any]) -> None:
    """Reject the historical exception on any newly-created control."""

    if payload.get("historical_classification") == "HISTORICAL_CORRUPT_EXCLUDED":
        raise ArtifactIntegrityError(
            "historical corruption exception is not valid for new controls"
        )
