import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
BASELINE = ROOT / "docs/cardcade/CALIBRATION_RELEASE_BASELINE_REFRESH_V16.json"
sys.path.insert(0, str(ROOT))

from scripts.calibration_run_reservation import ReservationViolation, reserve_run  # noqa: E402


def _fixture(tmp_path):
    repo = tmp_path / "repo"
    (repo / "docs/cardcade").mkdir(parents=True)
    target = repo / "docs/cardcade/CALIBRATION_RELEASE_BASELINE_REFRESH_V16.json"
    target.write_bytes(BASELINE.read_bytes())
    digest = hashlib.sha256(target.read_bytes()).hexdigest().upper()
    target.with_suffix(".json.sha256").write_text(f"{digest}  {target.name}\n", encoding="ascii")
    git_env = {
        **os.environ,
        "GIT_AUTHOR_DATE": "2026-09-20T12:00:00Z",
        "GIT_COMMITTER_DATE": "2026-09-20T12:00:00Z",
    }
    for command in (
        ["git", "init", "-q"],
        ["git", "add", "."],
        [
            "git",
            "-c",
            "user.name=test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-qm",
            "fixture",
        ],
    ):
        subprocess.run(command, cwd=repo, check=True, env=git_env)
    return repo


def test_valid_reservation_is_deterministic_and_non_executing(tmp_path):
    repo = _fixture(tmp_path)
    seed = repo / "docs/cardcade/CALIBRATION_SEED_TABLE_V2.json"
    entropy = repo / "docs/cardcade/CALIBRATION_SEED_TABLE_V2_ENTROPY.bin"
    seed.write_bytes(b"sealed-seed-fixture")
    entropy.write_bytes(b"sealed-entropy-fixture")
    before = {path: path.read_bytes() for path in (seed, entropy)}
    first = reserve_run(repo, timestamp="20260920T120000Z")
    equivalent_repo = _fixture(tmp_path / "equivalent")
    equivalent = reserve_run(equivalent_repo, timestamp="20260920T120000Z")
    run_dir = repo / first["run_directory_rel"]
    assert first["run_id"] == equivalent["run_id"]
    assert first["execution_authorized"] is False
    assert first["games_executed"] == first["seeds_consumed"] == 0
    assert first["wrapper_generated"] is False
    assert first["execution_wrapper_rel"].endswith(f"/{first['run_id']}/launcher.py")
    assert sorted(p.name for p in run_dir.iterdir()) == [
        "RESERVATION.json",
        "RESERVATION.json.sha256",
    ]
    assert json.loads((run_dir / "RESERVATION.json").read_bytes()) == first
    assert not list(run_dir.glob("*.jsonl"))
    assert {path: path.read_bytes() for path in (seed, entropy)} == before


def test_repeat_and_existing_directory_collisions_fail_closed(tmp_path):
    repo = _fixture(tmp_path)
    first = reserve_run(repo, timestamp="20260920T120001Z")
    with pytest.raises(ReservationViolation, match="already exists"):
        reserve_run(repo, timestamp="20260920T120001Z")
    other = reserve_run(repo, timestamp="20260920T120002Z")
    other_dir = repo / other["run_directory_rel"]
    for path in other_dir.iterdir():
        path.unlink()
    with pytest.raises(ReservationViolation, match="already exists"):
        reserve_run(repo, timestamp="20260920T120002Z")
    assert first["run_id"] != other["run_id"]


@pytest.mark.parametrize("timestamp", ["20260920", "20261301T120000Z", "20260920T120000+00:00"])
def test_malformed_timestamp_fails_before_reservation(tmp_path, timestamp):
    repo = _fixture(tmp_path)
    with pytest.raises(ReservationViolation, match="timestamp"):
        reserve_run(repo, timestamp=timestamp)
    assert list((repo / "docs/cardcade").iterdir()) == [
        repo / "docs/cardcade/CALIBRATION_RELEASE_BASELINE_REFRESH_V16.json",
        repo / "docs/cardcade/CALIBRATION_RELEASE_BASELINE_REFRESH_V16.json.sha256",
    ]


def test_authority_mutation_fails_closed_without_reserving(tmp_path):
    repo = _fixture(tmp_path)
    baseline = repo / "docs/cardcade/CALIBRATION_RELEASE_BASELINE_REFRESH_V16.json"
    data = json.loads(baseline.read_bytes())
    data["execution_authorized"] = True
    baseline.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ReservationViolation, match="sidecar|checkout|authorizes"):
        reserve_run(repo, timestamp="20260920T120003Z")
    assert not any(p.name.startswith("CALIBRATION_V1_") for p in (repo / "docs/cardcade").iterdir())
