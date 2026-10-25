from __future__ import annotations

import importlib.util
import inspect
import json
import sys
from pathlib import Path

import pytest

from tmnt_design_studio.calibration_integrity import CheckpointIntegrityError, WriterLock
from tmnt_design_studio.calibration_runner import ProtocolViolation

sys.path.insert(0, str(Path(__file__).parents[1] / "tools"))
_SPEC = importlib.util.spec_from_file_location(
    "bad_guys_initial_calibration",
    Path(__file__).parents[1] / "tools/run_bad_guys_initial_calibration.py",
)
assert _SPEC and _SPEC.loader
launcher = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(launcher)


def _small_schedule() -> list[dict[str, object]]:
    return [
        {
            "game_id": "g0",
            "pairing_id": "pair",
            "orientation": "candidate_first",
            "seed": 1,
            "opponent": "april_oneil",
            "seats": ["candidate", "april_oneil"],
        },
        {
            "game_id": "g1",
            "pairing_id": "pair",
            "orientation": "opponent_first",
            "seed": 2,
            "opponent": "april_oneil",
            "seats": ["april_oneil", "candidate"],
        },
    ]


@pytest.fixture
def small_contract(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(launcher, "EXPECTED_GAMES", 2)
    monkeypatch.setattr(launcher, "EXPECTED_MATCHUPS", 1)
    monkeypatch.setattr(launcher, "GAMES_PER_MATCHUP", 2)
    monkeypatch.setattr(launcher, "build_schedule", lambda root: _small_schedule())


def _result(row: dict[str, object]) -> dict[str, object]:
    return {"game_id": row["game_id"], "terminal": True}


def test_schedule_is_exactly_900_and_balanced():
    schedule = launcher.build_schedule()
    assert len(schedule) == 900
    assert len({row["pairing_id"] for row in schedule}) == 9
    for pairing in {row["pairing_id"] for row in schedule}:
        rows = [row for row in schedule if row["pairing_id"] == pairing]
        assert len(rows) == 100
        assert sum(row["orientation"] == "candidate_first" for row in rows) == 50
        assert sum(row["orientation"] == "opponent_first" for row in rows) == 50
    assert len({row["game_id"] for row in schedule}) == 900


def test_identity_failure_happens_before_executor(monkeypatch, tmp_path: Path, small_contract):
    calls = 0

    def reject(_root):
        raise launcher.ProvenanceError("identity mismatch")

    monkeypatch.setattr(launcher, "authenticate_inputs", reject)

    def executor(_row):
        nonlocal calls
        calls += 1
        return {}

    with pytest.raises(launcher.ProvenanceError):
        launcher.run_calibration(tmp_path, tmp_path / "checkpoint.json", executor=executor)
    assert calls == 0


def test_entrypoint_delegates_to_guarded_runner(monkeypatch, tmp_path: Path, small_contract):
    called = {}

    monkeypatch.setattr(launcher, "authenticate_inputs", lambda root: {})

    def guarded(schedule, checkpoint, executor, **kwargs):
        called.update(schedule=len(schedule), checkpoint=checkpoint, kwargs=kwargs)
        return {"completed_games": 2}

    monkeypatch.setattr(launcher, "run_checkpointed_schedule", guarded)
    result = launcher.run_calibration(tmp_path, tmp_path / "checkpoint.json", executor=_result)
    assert result == {"completed_games": 2}
    assert called["schedule"] == 2
    assert called["kwargs"]["expected_matchups"] == 1


def test_fresh_checkpoint_and_resume_do_not_replay_completed_games(
    monkeypatch, tmp_path: Path, small_contract
):
    monkeypatch.setattr(launcher, "authenticate_inputs", lambda root: {})
    checkpoint = tmp_path / "checkpoint.json"
    calls: list[str] = []

    def first(row):
        calls.append(str(row["game_id"]))
        if row["game_id"] == "g1":
            raise RuntimeError("interrupted")
        return _result(row)

    with pytest.raises(RuntimeError):
        launcher.run_calibration(tmp_path, checkpoint, executor=first)
    assert calls == ["g0", "g1"]

    def resumed(row):
        calls.append(str(row["game_id"]))
        return _result(row)

    launcher.run_calibration(tmp_path, checkpoint, executor=resumed)
    assert calls == ["g0", "g1", "g1"]
    assert json.loads(checkpoint.read_text())["completed_games"] == 2


def test_duplicate_and_unauthorized_results_are_rejected(monkeypatch, tmp_path, small_contract):
    monkeypatch.setattr(launcher, "authenticate_inputs", lambda root: {})
    with pytest.raises(ProtocolViolation):
        launcher.run_calibration(
            tmp_path,
            tmp_path / "duplicate.json",
            executor=lambda row: {"game_id": "g0"},
        )
    with pytest.raises(ProtocolViolation):
        launcher.run_calibration(
            tmp_path,
            tmp_path / "unauthorized.json",
            executor=lambda row: {"game_id": "not-scheduled"},
        )


def test_corrupt_checkpoint_is_rejected(monkeypatch, tmp_path, small_contract):
    monkeypatch.setattr(launcher, "authenticate_inputs", lambda root: {})
    checkpoint = tmp_path / "corrupt.json"
    checkpoint.write_text('{"records": [}', encoding="utf-8")
    with pytest.raises(CheckpointIntegrityError):
        launcher.run_calibration(tmp_path, checkpoint, executor=_result)


def test_competing_writer_is_rejected(monkeypatch, tmp_path, small_contract):
    monkeypatch.setattr(launcher, "authenticate_inputs", lambda root: {})
    checkpoint = tmp_path / "locked.json"
    with WriterLock(checkpoint, "other"), pytest.raises(CheckpointIntegrityError):
        launcher.run_calibration(tmp_path, checkpoint, executor=_result)


def test_incomplete_run_never_publishes_completion(monkeypatch, tmp_path, small_contract):
    monkeypatch.setattr(launcher, "authenticate_inputs", lambda root: {})
    checkpoint = tmp_path / "partial.json"
    with pytest.raises(RuntimeError):
        launcher.run_calibration(
            tmp_path, checkpoint, executor=lambda row: (_ for _ in ()).throw(RuntimeError("stop"))
        )
    assert not checkpoint.exists()


def test_launcher_has_no_competing_persistence_path():
    source = inspect.getsource(launcher)
    assert "run_checkpointed_schedule" in source
    assert "json.dump(" not in source
    assert ".write_text(" not in source


def test_injected_executor_proves_simulator_is_not_invoked(monkeypatch, tmp_path, small_contract):
    monkeypatch.setattr(launcher, "authenticate_inputs", lambda root: {})
    monkeypatch.setattr(
        launcher,
        "run_smoke_game",
        lambda *_args, **_kwargs: pytest.fail("Magic simulator was invoked"),
    )
    launcher.run_calibration(tmp_path, tmp_path / "mock.json", executor=_result)
