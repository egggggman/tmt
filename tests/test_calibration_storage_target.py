import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "calibration_storage_target", ROOT / "scripts/calibration_storage_target.py"
)
target = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(target)
StorageTargetViolation = target.StorageTargetViolation
resolve_live_evidence_target = target.resolve_live_evidence_target


RUN_ID = "CALIBRATION_V1_20260921T050741Z_98aa7d180751"
EXPECTED = rf"G:\cardcade\calibration-runs\{RUN_ID}"


def make_reservation(tmp_path, run_id=RUN_ID, **updates):
    directory = tmp_path / "docs" / "cardcade" / run_id
    directory.mkdir(parents=True)
    payload = {
        "execution_authorized": False,
        "games_executed": 0,
        "run_id": run_id,
        "seeds_consumed": 0,
        "wrapper_generated": False,
    }
    payload.update(updates)
    raw = (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode()
    (directory / "RESERVATION.json").write_bytes(raw)
    (directory / "RESERVATION.json.sha256").write_text(
        f"{hashlib.sha256(raw).hexdigest().upper()}  RESERVATION.json\n",
        encoding="ascii",
    )
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "docs/cardcade"], cwd=tmp_path, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=storage-test",
            "-c",
            "user.email=storage-test@example.invalid",
            "commit",
            "-qm",
            "bank reservation",
        ],
        cwd=tmp_path,
        check=True,
    )
    return tmp_path


def test_v17_resolves_to_exact_target_without_writing(tmp_path):
    root = make_reservation(tmp_path)
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    assert resolve_live_evidence_target(root, RUN_ID, target_exists=lambda _: False) == EXPECTED
    assert sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*")) == before


def test_committed_reservation_and_crlf_equivalent_checkout_succeeds(tmp_path):
    root = make_reservation(tmp_path)
    packet = root / "docs" / "cardcade" / RUN_ID / "RESERVATION.json"
    sidecar = packet.with_suffix(".json.sha256")
    packet.write_bytes(packet.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    sidecar.write_bytes(sidecar.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))

    assert resolve_live_evidence_target(root, RUN_ID, target_exists=lambda _: False) == EXPECTED


def test_recomputed_checkout_sidecar_cannot_replace_committed_reservation(tmp_path):
    root = make_reservation(tmp_path)
    packet = root / "docs" / "cardcade" / RUN_ID / "RESERVATION.json"
    sidecar = packet.with_suffix(".json.sha256")
    raw = packet.read_bytes().replace(b'"games_executed": 0', b'"games_executed": 1')
    packet.write_bytes(raw)
    sidecar.write_text(
        f"{hashlib.sha256(raw).hexdigest().upper()}  RESERVATION.json\n", encoding="ascii"
    )
    with pytest.raises(StorageTargetViolation, match="checkout reservation differs"):
        resolve_live_evidence_target(root, RUN_ID, target_exists=lambda _: False)


def test_modified_checkout_sidecar_fails_closed(tmp_path):
    root = make_reservation(tmp_path)
    sidecar = root / "docs" / "cardcade" / RUN_ID / "RESERVATION.json.sha256"
    sidecar.write_text("0" * 64 + "  RESERVATION.json\n", encoding="ascii")
    with pytest.raises(StorageTargetViolation, match="sidecar differs"):
        resolve_live_evidence_target(root, RUN_ID, target_exists=lambda _: False)


def test_different_drive_and_mismatched_run_id_fail_closed(tmp_path, monkeypatch):
    root = make_reservation(tmp_path)
    monkeypatch.setattr(target, "LIVE_EVIDENCE_ROOT", r"F:\cardcade\calibration-runs")
    with pytest.raises(StorageTargetViolation, match="qualified G:"):
        resolve_live_evidence_target(root, RUN_ID, target_exists=lambda _: False)

    monkeypatch.setattr(target, "LIVE_EVIDENCE_ROOT", r"G:\cardcade\calibration-runs")
    with pytest.raises(StorageTargetViolation, match="banked reservation"):
        resolve_live_evidence_target(root, "CALIBRATION_V1_20260921T050741Z_000000000000")


def test_existing_conflicting_target_fails_closed(tmp_path):
    root = make_reservation(tmp_path)
    with pytest.raises(StorageTargetViolation, match="already exists"):
        resolve_live_evidence_target(root, RUN_ID, target_exists=lambda _: True)


def test_reservation_state_must_be_unused(tmp_path):
    root = make_reservation(tmp_path, games_executed=1)
    with pytest.raises(StorageTargetViolation, match="unused"):
        resolve_live_evidence_target(root, RUN_ID, target_exists=lambda _: False)
