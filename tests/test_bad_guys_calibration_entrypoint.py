"""Durable CLI must not start a new run or choose a simulator executor."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from tmnt_design_studio.resume_authorization import ResumeRefused

sys.path.insert(0, str(Path(__file__).parents[1] / "tools"))
spec = importlib.util.spec_from_file_location(
    "bad_guys_initial_calibration",
    Path(__file__).parents[1] / "tools/run_bad_guys_initial_calibration.py",
)
assert spec and spec.loader
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


def test_schedule_is_exactly_900_and_balanced():
    schedule = launcher.build_schedule()
    assert len(schedule) == len({row["game_id"] for row in schedule}) == 900
    assert len({row["pairing_id"] for row in schedule}) == 9
    for pairing in {row["pairing_id"] for row in schedule}:
        rows = [row for row in schedule if row["pairing_id"] == pairing]
        assert len(rows) == 100
        assert sum(row["orientation"] == "candidate_first" for row in rows) == 50
        assert sum(row["orientation"] == "opponent_first" for row in rows) == 50


@pytest.mark.parametrize("exists", [True, False])
@pytest.mark.parametrize("injected", [True, False])
def test_no_implicit_authority_or_new_run(tmp_path, exists, injected):
    checkpoint = tmp_path / "checkpoint.json"
    if exists:
        checkpoint.write_bytes(b"unchanged evidence")
    calls = []
    executor = (lambda row: calls.append(row)) if injected else None
    with pytest.raises(ResumeRefused, match="authority"):
        launcher.run_calibration(checkpoint=checkpoint, executor=executor)
    assert not calls
    if exists:
        assert checkpoint.read_bytes() == b"unchanged evidence"
    else:
        assert not checkpoint.exists()


def test_cli_does_not_mint_authority(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "argv", ["launcher", "--checkpoint", str(tmp_path / "missing")])
    with pytest.raises(ResumeRefused, match="authority"):
        launcher.main()
