"""Terminal-contract regression only; never runs the calibration schedule."""

import hashlib
import json
from pathlib import Path

import pytest

from tmnt_design_studio import calibration_executor as adapter
from tmnt_design_studio import stage002
from tmnt_design_studio.calibration_runner import ProtocolMember
from tmnt_design_studio.engine07 import CardFact, Game, TurnStep

ROOT = Path(__file__).resolve().parents[1]
STOP = ROOT / "docs/cardcade/CALIBRATION_V1_20260914T224952Z_c3e745631702"
LAND = CardFact("Plains", "", 0, "Basic Land — Plains")


def failed_member():
    stop = json.loads((STOP / "RUN_STOP.json").read_bytes())
    row = stop["failed_execution"]
    return ProtocolMember(
        row["member_id"],
        row["block"],
        row["pair_index"],
        row["orientation"],
        row["seed"],
        tuple(row["decks"]),
    )


def canonical(result):
    return json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def test_exact_failed_member_terminal_and_duplicate_evidence(tmp_path):
    member = failed_member()
    table_path = ROOT / "docs/cardcade/CALIBRATION_SEED_TABLE_V1.json"
    manifest = json.loads((STOP / "RUN_MANIFEST.json").read_bytes())
    assert (
        hashlib.sha256(table_path.read_bytes()).hexdigest() == manifest["seed_table_sha256"].lower()
    )
    row = json.loads(table_path.read_bytes())["rows"][0]
    assert (
        row["block"],
        row["pair_index"],
        row["orientation"],
        int(row["seed"]),
        tuple(row["decks"]),
    ) == (member.block, member.pair_index, member.orientation, member.seed, member.decks)
    first = adapter.execute_member(ROOT, member, 0)
    second = adapter.execute_member(ROOT, member, 1)
    a, b = canonical(first), canonical(second)
    assert a == b
    authority = first["authoritative_state_fingerprint_preimage"]
    assert first["terminal"] is True
    assert first["winner"] == member.decks[authority["winner_index"]] == "april_oneil"
    assert first["turns_started"] == first["turn"] == authority["turn"] == 19
    assert [e["turn"] for e in first["events"] if e["event"] == "turn_started"] == list(
        range(1, 20)
    )
    assert authority["players"][1]["lost"] is True
    assert authority["players"][1]["life"] == -5
    assert any(
        e["event"] == "player_lost"
        and e["player"] == "bebop_rocksteady"
        and e["reason"] == "life_zero_or_less"
        for e in first["events"]
    )
    failed = json.loads((STOP / "FAILED_EXECUTION.json").read_bytes())
    original = next(f["result"] for f in failed["frames"] if "result" in f)
    assert {
        k: v for k, v in first.items() if k not in ("terminal", "turns_started", "member_id")
    } == original
    for name, raw in [("primary.json", a), ("duplicate.json", b)]:
        (tmp_path / name).write_bytes(raw)
        (tmp_path / (name + ".sha256")).write_text(hashlib.sha256(raw).hexdigest() + "\n")
    report = {
        "status": "DIAGNOSTIC_REGRESSION_PASS",
        "calibration_observations": 0,
        "member_id": member.member_id,
        "seed": member.seed,
        "executions": 2,
        "duplicate_equal": True,
        "primary_sha256": hashlib.sha256(a).hexdigest(),
        "duplicate_sha256": hashlib.sha256(b).hexdigest(),
        "terminal": first["terminal"],
        "winner": first["winner"],
        "winner_index": authority["winner_index"],
        "turns_started": first["turns_started"],
        "terminal_reason": "life_zero_or_less",
        "original_raw_result_preserved_except_contract_fields": True,
        "authoritative_state_fingerprint": first["authoritative_state_fingerprint"],
        "seed_table_sha256": manifest["seed_table_sha256"],
    }
    (tmp_path / "REGRESSION.json").write_text(json.dumps(report, indent=2) + "\n")


def test_game_snapshot_contract_is_authoritative_for_both_winners():
    for loser in (0, 1):
        game = Game(([LAND] * 60, [LAND] * 60), seed=7)
        initial = game.snapshot()
        assert initial["terminal"] is False
        assert initial["winner"] is None
        assert initial["turns_started"] == game.turn == 0
        game.begin_turn()
        assert game.snapshot()["turns_started"] == game.turn == 1
        game.players[loser].life = 0
        game.check_life()
        result = game.snapshot()
        assert result["terminal"] is True
        assert game.winner == 1 - loser
        assert result["winner"] == game.players[game.winner].name
        assert result["players"][loser]["loss_reason"] == "life_zero_or_less"
        assert result["authoritative_state_fingerprint_preimage"]["winner_index"] == game.winner


@pytest.mark.parametrize("terminal", [None, False, "true", 1])
def test_executor_rejects_missing_false_or_nonboolean_terminal(monkeypatch, terminal):
    result = {"turn": 19, "turns_started": 19}
    if terminal is not None:
        result["terminal"] = terminal
    monkeypatch.setattr(adapter, "run_game", lambda *args: result)
    with pytest.raises(RuntimeError, match="without terminal state"):
        adapter.execute_member(ROOT, failed_member())


@pytest.mark.parametrize("turns", [None, "19", True, -1, 18, 120])
def test_executor_rejects_missing_inconsistent_or_out_of_range_turns(monkeypatch, turns):
    result = {"terminal": True, "turn": 19 if turns != 120 else 120, "turns_started": turns}
    monkeypatch.setattr(adapter, "run_game", lambda *args: result)
    with pytest.raises(RuntimeError, match="turns_started|turn 120"):
        adapter.execute_member(ROOT, failed_member())


@pytest.mark.parametrize("win_on_119", [False, True])
def test_stage_prevents_turn_120_and_accepts_authoritative_win_on_119(monkeypatch, win_on_119):
    instances = []

    class BoundaryGame(Game):
        def __init__(self, *args, **kwargs):
            super().__init__(([LAND] * 200, [LAND] * 200), seed=7)
            self._turn = 118
            self._active_player = 1
            self._step = TurnStep.CLEANUP
            instances.append(self)

        def _on_enter_step(self, step):
            super()._on_enter_step(step)
            if win_on_119 and self.turn == 119 and step is TurnStep.DRAW:
                self.players[1].life = 0
                self.check_life()

    monkeypatch.setattr(stage002, "Game", BoundaryGame)
    if win_on_119:
        result = adapter.execute_member(ROOT, failed_member())
        assert result["terminal"] is True
        assert result["turns_started"] == result["turn"] == 119
        assert result["winner"] == instances[0].players[0].name
    else:
        with pytest.raises(RuntimeError, match="attempted to begin turn 120"):
            adapter.execute_member(ROOT, failed_member())
        assert instances[0].winner is None
    assert instances[0].turn == 119
    assert [e["turn"] for e in instances[0].events if e["event"] == "turn_started"] == [119]
