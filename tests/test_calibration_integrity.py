import errno
import json
from pathlib import Path

import pytest

import tmnt_design_studio.calibration_integrity as integrity
from tmnt_design_studio.calibration_integrity import (
    CheckpointAccumulator,
    CheckpointIntegrityError,
    canonical_digest,
    validate_checkpoint,
    validate_schedule,
)


def schedule() -> list[dict[str, str]]:
    return [
        {
            "game_id": f"a-{i}",
            "pairing_id": "a",
            "orientation": "candidate_first" if i < 2 else "opponent_first",
        }
        for i in range(4)
    ] + [
        {
            "game_id": f"b-{i}",
            "pairing_id": "b",
            "orientation": "candidate_first" if i < 2 else "opponent_first",
        }
        for i in range(4)
    ]


def test_schedule_requires_exact_cells_and_balanced_starts() -> None:
    result = validate_schedule(
        schedule(), expected_games=8, expected_matchups=2, games_per_matchup=4
    )
    assert result["schedule_digest"] == canonical_digest(schedule())


def test_schedule_rejects_duplicate_or_missing_identity() -> None:
    duplicate = schedule()
    duplicate[-1]["game_id"] = duplicate[0]["game_id"]
    with pytest.raises(CheckpointIntegrityError):
        validate_schedule(duplicate, expected_games=8, expected_matchups=2, games_per_matchup=4)
    with pytest.raises(CheckpointIntegrityError):
        validate_schedule(
            schedule()[:-1], expected_games=8, expected_matchups=2, games_per_matchup=4
        )


def test_append_once_and_repeated_write_are_idempotent(tmp_path: Path) -> None:
    acc = CheckpointAccumulator(schedule(), writer_id="runner")
    acc.append({"game_id": "a-0", "winner": "x"}, writer_id="runner")
    path = tmp_path / "checkpoint.json"
    first = acc.write(path, writer_id="runner")
    second = acc.write(path, writer_id="runner")
    assert first == second
    assert len(second["records"]) == 1
    with pytest.raises(CheckpointIntegrityError):
        acc.append({"game_id": "a-0", "winner": "x"}, writer_id="runner")


def test_rejects_unauthorized_writer_and_game() -> None:
    acc = CheckpointAccumulator(schedule(), writer_id="runner")
    with pytest.raises(CheckpointIntegrityError):
        acc.append({"game_id": "a-0"}, writer_id="other")
    with pytest.raises(CheckpointIntegrityError):
        acc.append({"game_id": "not-scheduled"}, writer_id="runner")


def test_checkpoint_rejects_duplicate_or_unauthorized_records() -> None:
    acc = CheckpointAccumulator(schedule(), writer_id="runner")
    payload = acc.snapshot()
    payload["records"] = [{"game_id": "a-0"}, {"game_id": "a-0"}]
    with pytest.raises(CheckpointIntegrityError):
        validate_checkpoint(payload, schedule())
    payload["records"] = [{"game_id": "forged"}]
    with pytest.raises(CheckpointIntegrityError):
        validate_checkpoint(payload, schedule())


def test_checkpoint_digest_is_deterministic() -> None:
    acc = CheckpointAccumulator(schedule(), writer_id="runner")
    acc.append({"game_id": "b-3", "winner": "x"}, writer_id="runner")
    assert acc.snapshot() == acc.snapshot()


def test_streamed_write_keeps_original_json_format(tmp_path: Path) -> None:
    acc = CheckpointAccumulator(schedule(), writer_id="runner")
    acc.append({"game_id": "a-0", "winner": "x", "events": [{"kind": "mock"}]}, writer_id="runner")
    path = tmp_path / "checkpoint.json"
    summary = acc.write(path, writer_id="runner", return_snapshot=False)
    expected = (json.dumps(acc.snapshot(), sort_keys=True, indent=2) + "\n").encode("utf-8")
    assert path.read_bytes() == expected
    assert summary["completed_games"] == 1 and "records" not in summary


def test_replace_retries_same_temporary_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    acc = CheckpointAccumulator(schedule(), writer_id="runner")
    acc.append({"game_id": "a-0", "winner": "x"}, writer_id="runner")
    path = tmp_path / "checkpoint.json"
    real_replace = integrity.os.replace
    calls: list[str] = []
    delays: list[float] = []

    def transient(source, destination):
        calls.append(source)
        if len(calls) < 3:
            raise PermissionError(errno.EACCES, "temporary sharing denial")
        real_replace(source, destination)

    monkeypatch.setattr(integrity.os, "replace", transient)
    monkeypatch.setattr(integrity.time, "sleep", delays.append)
    acc.write(path, writer_id="runner", return_snapshot=False)
    assert len(calls) == 3 and len(set(calls)) == 1
    assert delays == [0.05, 0.1]
    assert json.loads(path.read_text())["completed_games"] == 1


def test_replace_failure_preserves_prior_checkpoint(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    acc = CheckpointAccumulator(schedule(), writer_id="runner")
    acc.append({"game_id": "a-0", "winner": "x"}, writer_id="runner")
    path = tmp_path / "checkpoint.json"
    acc.write(path, writer_id="runner", return_snapshot=False)
    original = path.read_bytes()
    acc.append({"game_id": "a-1", "winner": "y"}, writer_id="runner")
    first_error = PermissionError(errno.EACCES, "first denial")
    calls = 0

    def denied(_source, _destination):
        nonlocal calls
        calls += 1
        raise first_error if calls == 1 else PermissionError(errno.EACCES, "later denial")

    monkeypatch.setattr(integrity.os, "replace", denied)
    monkeypatch.setattr(integrity.time, "sleep", lambda _seconds: None)
    with pytest.raises(PermissionError) as raised:
        acc.write(path, writer_id="runner", return_snapshot=False)
    assert raised.value is first_error
    assert calls == 8
    assert path.read_bytes() == original
    assert not list(tmp_path.glob(".checkpoint.json.*"))


def test_checkpoint_rejects_wrong_counts_and_order() -> None:
    acc = CheckpointAccumulator(schedule(), writer_id="runner")
    acc.append({"game_id": "a-0"}, writer_id="runner")
    acc.append({"game_id": "a-1"}, writer_id="runner")
    payload = acc.snapshot()
    payload["completed_games"] = 3
    with pytest.raises(CheckpointIntegrityError, match="completed count"):
        validate_checkpoint(payload, schedule())
    payload["completed_games"] = 2
    payload["records"].reverse()
    with pytest.raises(CheckpointIntegrityError, match="out of schedule order"):
        validate_checkpoint(payload, schedule())
