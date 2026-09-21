"""Resolve the authenticated external live-evidence target for Calibration V1."""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections.abc import Callable
from pathlib import Path, PureWindowsPath

LIVE_VOLUME = "G:"
LIVE_EVIDENCE_ROOT = r"G:\cardcade\calibration-runs"
RUN_ID_RE = re.compile(r"^CALIBRATION_V1_\d{8}T\d{6}Z_[0-9a-f]{12}$")


class StorageTargetViolation(RuntimeError):
    """Raised when a live calibration target is not contract-safe."""


def _authenticated_reservation(repository_root: Path, run_id: str) -> dict[str, object]:
    reservation_dir = repository_root / "docs" / "cardcade" / run_id
    packet_path = reservation_dir / "RESERVATION.json"
    sidecar_path = reservation_dir / "RESERVATION.json.sha256"
    try:
        payload = packet_path.read_bytes()
        sidecar = sidecar_path.read_text(encoding="ascii").split()[0].upper()
        packet = json.loads(payload)
    except (OSError, IndexError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StorageTargetViolation("banked reservation is missing or malformed") from exc
    digest = hashlib.sha256(payload).hexdigest().upper()
    if sidecar != digest:
        raise StorageTargetViolation("banked reservation sidecar does not authenticate JSON")
    if packet.get("run_id") != run_id:
        raise StorageTargetViolation("run ID does not match the banked reservation")
    if packet.get("execution_authorized") is not False:
        raise StorageTargetViolation("reservation authorizes execution")
    if packet.get("games_executed") != 0 or packet.get("seeds_consumed") != 0:
        raise StorageTargetViolation("reservation is not unused")
    if packet.get("wrapper_generated") is not False:
        raise StorageTargetViolation("reservation already has a generated wrapper")
    return packet


def _validated_root() -> PureWindowsPath:
    root = PureWindowsPath(LIVE_EVIDENCE_ROOT)
    if root.drive.upper() != LIVE_VOLUME or root.root != "\\":
        raise StorageTargetViolation("live evidence root is not the qualified G: volume")
    if root.parts != ("G:\\", "cardcade", "calibration-runs"):
        raise StorageTargetViolation("live evidence root is not the governed path")
    return root


def resolve_live_evidence_target(
    repository_root: Path,
    run_id: str,
    *,
    target_exists: Callable[[str], bool] = os.path.exists,
) -> str:
    """Return the exact unused G: target for an authenticated reserved run.

    This function performs no directory creation and writes no evidence.
    """
    if not RUN_ID_RE.fullmatch(run_id):
        raise StorageTargetViolation("malformed calibration run ID")
    _authenticated_reservation(repository_root.resolve(), run_id)
    target = _validated_root() / run_id
    rendered = str(target)
    if target.drive.upper() != LIVE_VOLUME or target.parent != _validated_root():
        raise StorageTargetViolation("resolved target left the qualified live evidence root")
    if target_exists(rendered):
        raise StorageTargetViolation("live evidence target already exists")
    return rendered
