"""Build a non-authorizing, pre-generation Calibration V1 launcher manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections.abc import Callable
from pathlib import Path

from scripts.calibration_storage_target import resolve_live_evidence_target

BASELINE_REL = "docs/cardcade/CALIBRATION_RELEASE_BASELINE_REFRESH_V16.json"
SEED_REL = "docs/cardcade/CALIBRATION_SEED_TABLE_V2.json"
MANIFEST_NAME = "LAUNCHER_RELEASE_MANIFEST_V1.json"
SHA256_RE = re.compile(r"^[0-9A-F]{64}$")


class LauncherReleaseViolation(RuntimeError):
    """Raised when pre-generation launcher identity cannot be authenticated."""


def _git_blob(root: Path, relative: str) -> bytes:
    try:
        return subprocess.check_output(["git", "show", f"HEAD:{relative}"], cwd=root)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise LauncherReleaseViolation(f"missing committed release input: {relative}") from exc


def _equivalent(checkout: bytes, committed: bytes) -> bool:
    return checkout.replace(b"\r\n", b"\n") == committed.replace(b"\r\n", b"\n")


def _checkout_bytes(root: Path, relative: str) -> bytes:
    return (root / relative).read_bytes()


def _authenticated_json(root: Path, relative: str, sidecar_relative: str) -> tuple[dict, str]:
    committed = _git_blob(root, relative)
    committed_sidecar = _git_blob(root, sidecar_relative)
    checkout = _checkout_bytes(root, relative)
    checkout_sidecar = _checkout_bytes(root, sidecar_relative)
    if not _equivalent(checkout, committed):
        raise LauncherReleaseViolation(f"checkout differs from committed release input: {relative}")
    if not _equivalent(checkout_sidecar, committed_sidecar):
        raise LauncherReleaseViolation(
            f"checkout differs from committed release sidecar: {sidecar_relative}"
        )
    try:
        expected = committed_sidecar.decode("ascii").split()[0].upper()
        packet = json.loads(committed)
    except (IndexError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LauncherReleaseViolation(f"malformed committed release input: {relative}") from exc
    digest = hashlib.sha256(committed).hexdigest().upper()
    if expected != digest or not SHA256_RE.fullmatch(expected):
        raise LauncherReleaseViolation(f"release sidecar does not authenticate: {relative}")
    return packet, digest


def build_manifest(
    repository_root: Path,
    run_id: str,
    *,
    renderer_source_sha256: str,
    target_exists: Callable[[str], bool],
) -> tuple[dict, bytes]:
    root = repository_root.resolve()
    reservation_rel = f"docs/cardcade/{run_id}/RESERVATION.json"
    reservation_sidecar_rel = f"{reservation_rel}.sha256"
    reservation, reservation_hash = _authenticated_json(
        root, reservation_rel, reservation_sidecar_rel
    )
    if reservation.get("run_id") != run_id:
        raise LauncherReleaseViolation("run ID does not match the committed reservation")
    if reservation.get("execution_authorized") is not False:
        raise LauncherReleaseViolation("reservation authorizes execution")
    if reservation.get("wrapper_generated") is not False:
        raise LauncherReleaseViolation("reservation already has a generated wrapper")
    baseline, baseline_hash = _authenticated_json(root, BASELINE_REL, f"{BASELINE_REL}.sha256")
    if baseline.get("execution_authorized") is not False:
        raise LauncherReleaseViolation("V16 baseline authorizes execution")
    if baseline.get("protocol") != "V1":
        raise LauncherReleaseViolation("V16 baseline is not Protocol V1")
    schedule = baseline.get("schedule")
    if not isinstance(schedule, dict) or schedule.get("distinct_games") != 184320:
        raise LauncherReleaseViolation("V1 schedule identity is incomplete")
    if schedule.get("executions") != 368640:
        raise LauncherReleaseViolation("V1 execution count is incomplete")
    renderer_source_sha256 = renderer_source_sha256.upper()
    if not SHA256_RE.fullmatch(renderer_source_sha256):
        raise LauncherReleaseViolation("renderer source hash is malformed")
    output_rel = resolve_live_evidence_target(root, run_id, target_exists=target_exists)
    manifest_rel = f"docs/cardcade/{run_id}/{MANIFEST_NAME}"
    manifest = {
        "scheme": "calibration-launcher-release-manifest-v1",
        "execution_authorized": False,
        "launcher_generated": False,
        "generated_launcher_sha256": None,
        "run_id": run_id,
        "reservation": {"rel": reservation_rel, "sha256": reservation_hash},
        "release_baseline": {"rel": BASELINE_REL, "sha256": baseline_hash},
        "renderer": {
            "rel": "scripts/calibration_runtime_wrapper.py",
            "sha256": renderer_source_sha256,
        },
        "launcher_rel": reservation.get("execution_wrapper_rel"),
        "output_rel": output_rel,
        "render_inputs": {
            "packet_rel": BASELINE_REL,
            "packet_sha256": baseline_hash,
            "release_manifest_rel": manifest_rel,
            "release_manifest_sidecar_rel": f"{manifest_rel}.sha256",
            "seed_rel": SEED_REL,
            "seed_sha256": baseline.get("seed_table_v2_sha256"),
        },
        "accepted_runtime": baseline.get("accepted_runtime"),
        "protocol": baseline.get("protocol"),
        "protocol_identity": baseline.get("protocol_identity"),
        "seed_table_v2_sha256": baseline.get("seed_table_v2_sha256"),
        "seed_table_v2_entropy_sha256": baseline.get("seed_table_v2_entropy_sha256"),
        "schedule": schedule,
    }
    payload = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode("utf-8")
    return manifest, payload


def write_manifest(repository_root: Path, run_id: str, renderer_source_sha256: str) -> str:
    root = repository_root.resolve()
    _, payload = build_manifest(
        root,
        run_id,
        renderer_source_sha256=renderer_source_sha256,
        target_exists=lambda path: Path(path).exists(),
    )
    target = root / "docs" / "cardcade" / run_id / MANIFEST_NAME
    sidecar = target.with_suffix(target.suffix + ".sha256")
    if target.exists() or sidecar.exists():
        raise LauncherReleaseViolation("launcher release manifest already exists")
    target.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest().upper()
    sidecar.write_text(f"{digest}  {MANIFEST_NAME}\n", encoding="ascii")
    return digest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--renderer-source-sha256", required=True)
    args = parser.parse_args()
    print(write_manifest(args.repository_root, args.run_id, args.renderer_source_sha256))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
