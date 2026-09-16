import json
from pathlib import Path

import pytest

from tmnt_design_studio.calibration_runner import (
    ProtocolMember,
    ProtocolViolation,
    execute_protocol,
    load_members,
)


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


def test_executor_builds_fresh_spec_and_propagates_result(tmp_path, monkeypatch):
    from tmnt_design_studio import calibration_executor as adapter

    seen = []

    def fake_run(root, spec, pilot):
        seen.append((spec, pilot))
        return {"terminal": True, "turn": 3, "turns_started": 3, "telemetry": []}

    monkeypatch.setattr(adapter, "run_game", fake_run)
    monkeypatch.setattr(adapter, "_frozen_deck_path", lambda root, deck: f"decks/{deck}/frozen.txt")
    member = ProtocolMember("b0000-p00-canonical", 0, 0, "canonical", 7, ("a", "b"))
    first = adapter.execute_member(tmp_path, member, 0)
    second = adapter.execute_member(tmp_path, member, 1)
    assert first["turns_started"] == 3
    assert first["member_id"] == second["member_id"]
    assert seen[0][0].orientation == "canonical"
    assert seen[0][0].seats[0].display_id == "a"
    assert seen[1][1] is not seen[0][1]


def test_executor_rejects_nonterminal_result(tmp_path, monkeypatch):
    from tmnt_design_studio import calibration_executor as adapter

    monkeypatch.setattr(adapter, "run_game", lambda *args: {"terminal": False})
    monkeypatch.setattr(adapter, "_frozen_deck_path", lambda root, deck: f"decks/{deck}/frozen.txt")
    member = ProtocolMember("b0000-p00-canonical", 0, 0, "canonical", 7, ("a", "b"))
    with pytest.raises(RuntimeError, match="terminal"):
        adapter.execute_member(tmp_path, member)


def test_authoritative_blob_auth_accepts_crlf_checkout(monkeypatch):
    import hashlib
    import subprocess

    import tmnt_design_studio.calibration_runner as runner

    path = Path(__file__).parents[1] / "docs/cardcade/CALIBRATION_SEED_TABLE_V2.json"
    canonical = subprocess.check_output(
        ["git", "show", f"HEAD:{path.relative_to(path.parents[2]).as_posix()}"]
    )
    original_read = Path.read_bytes

    def checkout_bytes(candidate):
        return canonical.replace(b" ", b"\r\n") if candidate == path else original_read(candidate)

    monkeypatch.setattr(Path, "read_bytes", checkout_bytes)
    members = runner.load_members(path, expected_sha256=hashlib.sha256(canonical).hexdigest())
    assert len(members) == 184320


def test_checkout_divergence_is_rejected(monkeypatch):
    import tmnt_design_studio.calibration_runner as runner

    path = Path(__file__).parents[1] / "docs/cardcade/CALIBRATION_SEED_TABLE_V2.json"
    original_read = Path.read_bytes

    def altered(candidate):
        raw = original_read(candidate)
        return raw.replace(b"184320", b"184321", 1) if candidate == path else raw

    monkeypatch.setattr(Path, "read_bytes", altered)
    with pytest.raises(ProtocolViolation, match="diverges"):
        runner.load_members(
            path, expected_sha256="6BE94F69A2E9432E615AEA7A8592D68B6537998B3F7355A60191A29E71DC6E5C"
        )


def test_outside_repository_path_fails_closed(tmp_path):
    path = tmp_path / "seed.json"
    path.write_text('{"rows": []}')
    with pytest.raises(ProtocolViolation, match="outside the repository"):
        load_members(path, expected_sha256="0" * 64)
