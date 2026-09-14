import json

import pytest

from tmnt_design_studio.calibration_runner import ProtocolViolation, execute_protocol


def table(path):
    path.write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "block": 0,
                        "pair_index": 0,
                        "orientation": "canonical",
                        "seed": 7,
                        "decks": ["a", "b"],
                    },
                    {
                        "block": 0,
                        "pair_index": 0,
                        "orientation": "reversed",
                        "seed": 8,
                        "decks": ["a", "b"],
                    },
                ]
            }
        )
    )

    return path


def test_tiny_protocol_completes_with_duplicate_authentication(tmp_path):
    seed = tmp_path / "seeds.json"
    table(seed)

    def ex(member, duplicate):
        return {"member_id": member.member_id, "seed": member.seed}

    result = execute_protocol(seed, tmp_path / "out", ex)
    assert result["status"] == "COMPLETE_PENDING_AUDIT" and result["completed_members"] == 2
    assert all(row.get("duplicate_equal", True) for row in result["ledger"])


def test_duplicate_mismatch_fails_closed_and_preserves_ledger(tmp_path):
    seed = tmp_path / "seeds.json"
    table(seed)

    def ex(member, duplicate):
        return {"member_id": member.member_id, "n": duplicate}

    try:
        execute_protocol(seed, tmp_path / "out", ex)
    except ProtocolViolation as exc:
        assert "fail-closed" in str(exc)
    else:
        raise AssertionError("expected stop")
    stop = json.loads((tmp_path / "out" / "EXECUTION_LEDGER.json").read_text())
    assert stop["status"] == "FAIL_CLOSED_STOP" and stop["failed_member"] == "b0000-p00-canonical"


def test_strict_schedule_rejects_truncated_manifest(tmp_path):
    path = table(tmp_path / "seed.json")
    with pytest.raises(ProtocolViolation, match="dimensions"):
        execute_protocol(
            path, tmp_path / "out", lambda member, duplicate: {"terminal": True}, strict=True
        )


def test_strict_turn_boundary_fails_closed(tmp_path, monkeypatch):
    path = table(tmp_path / "seed.json")
    import tmnt_design_studio.calibration_runner as runner

    original = runner.load_members
    monkeypatch.setattr(runner, "load_members", lambda *args, **kwargs: original(path))
    with pytest.raises(ProtocolViolation, match="turn 120"):
        execute_protocol(
            path,
            tmp_path / "out",
            lambda member, duplicate: {"terminal": True, "turns_started": 120},
            strict=True,
        )
