import hashlib
import importlib.util
import json
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


def make_reservation(tmp_path, run_id=RUN_ID):
    directory = tmp_path / "docs" / "cardcade" / run_id
    directory.mkdir(parents=True)
    payload = {
        "execution_authorized": False,
        "games_executed": 0,
        "run_id": run_id,
        "seeds_consumed": 0,
        "wrapper_generated": False,
    }
    raw = (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode()
    (directory / "RESERVATION.json").write_bytes(raw)
    (directory / "RESERVATION.json.sha256").write_text(
        f"{hashlib.sha256(raw).hexdigest().upper()}  RESERVATION.json\n",
        encoding="ascii",
    )
    return tmp_path


def test_v17_resolves_to_exact_target_without_writing(tmp_path):
    root = make_reservation(tmp_path)
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    assert resolve_live_evidence_target(root, RUN_ID, target_exists=lambda _: False) == EXPECTED
    assert sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*")) == before


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
    root = make_reservation(tmp_path)
    packet = root / "docs" / "cardcade" / RUN_ID / "RESERVATION.json"
    payload = json.loads(packet.read_text(encoding="utf-8"))
    payload["games_executed"] = 1
    raw = (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode()
    packet.write_bytes(raw)
    (packet.parent / "RESERVATION.json.sha256").write_text(
        f"{hashlib.sha256(raw).hexdigest().upper()}  RESERVATION.json\n", encoding="ascii"
    )
    with pytest.raises(StorageTargetViolation, match="unused"):
        resolve_live_evidence_target(root, RUN_ID, target_exists=lambda _: False)
