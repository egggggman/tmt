"""Reserve a Protocol V1 calibration identity without preparing or executing a run."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

BASELINE_REL = "docs/cardcade/CALIBRATION_RELEASE_BASELINE_REFRESH_V16.json"
RUN_ROOT_REL = "docs/cardcade"
WRAPPER_NAME = "launcher.py"
RUN_ID_RE = re.compile(r"^CALIBRATION_V1_(\d{8}T\d{6}Z)_([0-9a-f]{12})$")
SHA256_RE = re.compile(r"^[0-9A-Fa-f]{64}$")


class ReservationViolation(RuntimeError):
    """Raised when the V16 reservation authority or target is not safe."""


def _git_blob(root: Path, relative: str) -> bytes:
    try:
        return subprocess.check_output(["git", "show", f"HEAD:{relative}"], cwd=root)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ReservationViolation(f"unable to read authoritative Git blob: {relative}") from exc


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest().upper()


def _read_sha_sidecar(path: Path) -> str:
    try:
        value = path.read_text(encoding="ascii").split()[0]
    except (OSError, IndexError, UnicodeDecodeError) as exc:
        raise ReservationViolation(f"missing or malformed hash sidecar: {path}") from exc
    if not SHA256_RE.fullmatch(value):
        raise ReservationViolation(f"malformed hash sidecar: {path}")
    return value.upper()


def _authority(root: Path) -> dict[str, object]:
    baseline_path = root / BASELINE_REL
    committed = _git_blob(root, BASELINE_REL)
    committed_hash = _sha256(committed)
    sidecar_hash = _read_sha_sidecar(baseline_path.with_suffix(".json.sha256"))
    if sidecar_hash != committed_hash:
        raise ReservationViolation("V16 baseline sidecar does not authenticate its Git blob")
    if baseline_path.read_bytes().replace(b"\r\n", b"\n") != committed.replace(b"\r\n", b"\n"):
        raise ReservationViolation("V16 baseline checkout differs from its Git blob")
    try:
        packet = json.loads(committed)
    except json.JSONDecodeError as exc:
        raise ReservationViolation("V16 baseline is not valid JSON") from exc
    if packet.get("scheme") != "calibration-release-baseline-refresh-v16":
        raise ReservationViolation("unexpected V16 baseline scheme")
    if packet.get("protocol") != "V1":
        raise ReservationViolation("V16 baseline is not Protocol V1")
    if packet.get("execution_authorized") is not False:
        raise ReservationViolation("V16 baseline authorizes execution")
    accepted_runtime = packet.get("accepted_runtime")
    protocol_identity = packet.get("protocol_identity")
    if not isinstance(accepted_runtime, str) or not re.fullmatch(r"[0-9a-f]{40}", accepted_runtime):
        raise ReservationViolation("V16 accepted runtime identity is malformed")
    if not isinstance(protocol_identity, str) or not re.fullmatch(
        r"[0-9a-f]{40}", protocol_identity
    ):
        raise ReservationViolation("V16 protocol identity is malformed")
    try:
        audited_main = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ReservationViolation("unable to identify audited Git HEAD") from exc
    if not re.fullmatch(r"[0-9a-f]{40}", audited_main):
        raise ReservationViolation("audited Git HEAD is malformed")
    return {
        "audited_main_commit": audited_main,
        "accepted_runtime": accepted_runtime,
        "protocol": "V1",
        "protocol_identity": protocol_identity,
        "v16_baseline_rel": BASELINE_REL,
        "v16_baseline_sha256": committed_hash,
        "seed_table_v2_sha256": packet.get("seed_table_v2_sha256"),
        "seed_table_v2_entropy_sha256": packet.get("seed_table_v2_entropy_sha256"),
    }


def _timestamp(value: str | None) -> str:
    if value is None:
        return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    if not re.fullmatch(r"\d{8}T\d{6}Z", value):
        raise ReservationViolation("timestamp must be UTC YYYYMMDDTHHMMSSZ")
    try:
        datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
    except ValueError as exc:
        raise ReservationViolation("timestamp is not a valid UTC instant") from exc
    return value


def reserve_run(repository_root: Path, *, timestamp: str | None = None) -> dict[str, object]:
    """Reserve one identity by atomically creating its otherwise-empty run directory."""
    root = repository_root.resolve()
    authority = _authority(root)
    stamp = _timestamp(timestamp)
    identity = {**authority, "timestamp_utc": stamp}
    suffix = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:12]
    run_id = f"CALIBRATION_V1_{stamp}_{suffix}"
    run_root = root / RUN_ROOT_REL
    target = run_root / run_id
    wrapper_rel = f"{RUN_ROOT_REL}/{run_id}/{WRAPPER_NAME}"
    reservation = {
        "scheme": "calibration-run-reservation-v1",
        "execution_authorized": False,
        "run_id": run_id,
        "run_directory_rel": f"{RUN_ROOT_REL}/{run_id}",
        "execution_wrapper_rel": wrapper_rel,
        "reservation_identity": identity,
        "reservation_state": "RESERVED_NOT_EXECUTED",
        "games_executed": 0,
        "seeds_consumed": 0,
        "wrapper_generated": False,
    }
    payload = (json.dumps(reservation, sort_keys=True, indent=2) + "\n").encode("utf-8")
    try:
        target.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise ReservationViolation(f"run identity already exists: {run_id}") from exc
    try:
        (target / "RESERVATION.json").write_bytes(payload)
        (target / "RESERVATION.json.sha256").write_text(
            f"{_sha256(payload)}  RESERVATION.json\n", encoding="ascii"
        )
    except OSError as exc:
        raise ReservationViolation(
            "reservation directory was created but could not be sealed"
        ) from exc
    return reservation


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    print(json.dumps(reserve_run(args.repository_root), sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
