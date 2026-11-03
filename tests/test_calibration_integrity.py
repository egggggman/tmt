from pathlib import Path

import pytest

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
