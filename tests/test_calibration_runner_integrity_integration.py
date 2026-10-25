import json
from pathlib import Path

import pytest

from tmnt_design_studio.calibration_integrity import (
    CheckpointAccumulator,
    CheckpointIntegrityError,
)
from tmnt_design_studio.calibration_runner import ProtocolViolation, run_checkpointed_schedule


def schedule() -> list[dict[str, str]]:
    return [
        {
            "game_id": f"{pair}-{orientation}-{index}",
            "pairing_id": pair,
            "orientation": orientation,
        }
        for pair in ("a", "b")
        for orientation in ("candidate_first", "opponent_first")
        for index in range(2)
    ]


def result(row: dict[str, str]) -> dict[str, str]:
    return {"game_id": row["game_id"], "outcome": "mock"}


def run(path: Path, fn=result):
    return run_checkpointed_schedule(
        schedule(), path, fn, writer_id="runner", expected_matchups=2, games_per_matchup=4
    )


def test_fresh_progression_and_exact_completion(tmp_path: Path) -> None:
    path = tmp_path / "checkpoint.json"
    summary = run(path)
    assert summary["completed_games"] == 8
    assert len(json.loads(path.read_text())["records"]) == 8


def test_interrupted_resume_does_not_replay_completed_records(tmp_path: Path) -> None:
    path = tmp_path / "checkpoint.json"
    calls = []

    def stop_after_two(row):
        calls.append(row["game_id"])
        if len(calls) == 3:
            raise RuntimeError("interrupt")
        return result(row)

    with pytest.raises(RuntimeError):
        run(path, stop_after_two)
    first_calls = list(calls)
    run(path)
    assert calls == first_calls


def test_repeated_write_and_duplicate_result_rejection(tmp_path: Path) -> None:
    path = tmp_path / "checkpoint.json"
    run(path)
    payload = json.loads(path.read_text())
    payload["records"].append(payload["records"][0])
    path.write_text(json.dumps(payload))
    with pytest.raises(CheckpointIntegrityError):
        run(path)


def test_wrong_or_unauthorized_game_is_rejected(tmp_path: Path) -> None:
    def forged(row):
        return {"game_id": "forged"}

    with pytest.raises(ProtocolViolation):
        run(tmp_path / "checkpoint.json", forged)


def test_corrupt_checkpoint_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "checkpoint.json"
    path.write_text("not json")
    with pytest.raises(CheckpointIntegrityError):
        run(path)


def test_incomplete_checkpoint_cannot_be_accepted(tmp_path: Path) -> None:
    path = tmp_path / "checkpoint.json"
    calls = []

    def stop(row):
        calls.append(row["game_id"])
        if len(calls) == 3:
            raise RuntimeError("stop")
        return result(row)

    with pytest.raises(RuntimeError):
        run(path, stop)
    payload = json.loads(path.read_text())
    assert payload["completed_games"] == 2


def test_second_writer_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "checkpoint.json"
    lock = Path(f"{path}.lock")
    lock.write_text("other-process\n")
    with pytest.raises(CheckpointIntegrityError, match="ownership"):
        run(path)


def test_schedule_shape_is_enforced(tmp_path: Path) -> None:
    bad = schedule()[:-1]
    with pytest.raises(CheckpointIntegrityError):
        run_checkpointed_schedule(
            bad,
            tmp_path / "checkpoint.json",
            result,
            writer_id="runner",
            expected_matchups=2,
            games_per_matchup=4,
        )


def test_no_duplicate_execution_on_completed_resume(tmp_path: Path) -> None:
    path = tmp_path / "checkpoint.json"
    calls = []
    run(path, lambda row: calls.append(row["game_id"]) or result(row))
    initial = list(calls)
    run(path, lambda row: (_ for _ in ()).throw(AssertionError("replayed")))
    assert len(initial) == 8


def test_stream_restore_matches_whole_file_restore_and_write(tmp_path: Path) -> None:
    source = tmp_path / "source.json"
    run(source)
    payload = json.loads(source.read_text(encoding="utf-8"))

    whole_file = CheckpointAccumulator(schedule(), writer_id="runner")
    whole_file.restore(payload, take_ownership=True)
    streaming = CheckpointAccumulator(schedule(), writer_id="runner")
    streaming.restore_stream(source)
    assert streaming.snapshot() == whole_file.snapshot()

    output = tmp_path / "streamed.json"
    streaming.write(output, writer_id="runner", return_snapshot=False)
    assert output.read_bytes() == source.read_bytes()


def test_stream_restore_accepts_empty_partial_checkpoint(tmp_path: Path) -> None:
    source = tmp_path / "empty.json"
    empty = CheckpointAccumulator(schedule(), writer_id="runner")
    empty.write(source, writer_id="runner", return_snapshot=False)
    restored = CheckpointAccumulator(schedule(), writer_id="runner")
    restored.restore_stream(source)
    assert restored.snapshot()["completed_games"] == 0


@pytest.mark.parametrize(
    "corruption",
    [
        "declared_count",
        "schedule_digest",
        "schedule_games",
        "duplicate_id",
        "unauthorized_id",
        "record_order",
        "missing_game_id",
        "truncated_file",
        "trailing_data",
        "malformed_record_json",
        "oversized_line",
    ],
)
def test_stream_restore_rejects_corrupt_checkpoints(tmp_path: Path, corruption: str) -> None:
    path = tmp_path / "checkpoint.json"
    run(path)
    raw = path.read_bytes()
    if corruption == "truncated_file":
        path.write_bytes(raw[:-10])
    elif corruption == "trailing_data":
        path.write_bytes(raw + b"garbage")
    elif corruption == "malformed_record_json":
        path.write_bytes(raw.replace(b'"outcome": "mock"', b'"outcome": }', 1))
    else:
        payload = json.loads(raw)
        records = payload["records"]
        if corruption == "oversized_line":
            records[0]["large_field"] = "x" * (8 * 1024 * 1024 + 1)
        elif corruption == "declared_count":
            payload["completed_games"] -= 1
        elif corruption == "schedule_digest":
            payload["schedule_digest"] = "0" * 64
        elif corruption == "schedule_games":
            payload["schedule_games"] += 1
        elif corruption == "duplicate_id":
            records[-1] = dict(records[0])
        elif corruption == "unauthorized_id":
            records[0]["game_id"] = "forged-game-id"
        elif corruption == "record_order":
            records[0], records[1] = records[1], records[0]
        elif corruption == "missing_game_id":
            del records[0]["game_id"]
        path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(CheckpointIntegrityError):
        run(path)
