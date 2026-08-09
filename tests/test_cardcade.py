import json
from pathlib import Path

import pytest

from tmnt_design_studio.cardcade import (
    _pilot,
    compare_runs,
    load_roster,
    run_round_robin,
    validate_roster,
    write_run,
)

ROOT = Path(__file__).parents[1]
ROSTER = ROOT / "cardcade" / "roster-0.1.json"


def test_beta_roster_has_ten_structurally_valid_decks():
    roster = load_roster(ROSTER)
    assert len(validate_roster(roster, ROOT)) == 10


def test_smoke_round_robin_is_complete_balanced_and_reproducible():
    roster = load_roster(ROSTER)
    first = run_round_robin(roster, 20, 20260809)
    second = run_round_robin(roster, 20, 20260809)
    assert first == second
    assert first["total_games"] == 900
    assert len(first["pairings"]) == 45
    for pairing in first["pairings"].values():
        rows = [
            row for row in first["matches"]
            if {row["deck_a"], row["deck_b"]} == {pairing["deck_a"], pairing["deck_b"]}
        ]
        assert sum(row["starting_player"] == pairing["deck_a"] for row in rows) == 10
        assert sum(row["starting_player"] == pairing["deck_b"] for row in rows) == 10


def test_run_artifacts_include_ten_by_ten_matrix(tmp_path):
    result = run_round_robin(load_roster(ROSTER), 20, 7)
    write_run(result, tmp_path)
    matrix = json.loads((tmp_path / "matchup-matrix.json").read_text())
    assert len(matrix) == 10
    assert all(len(row) == 10 for row in matrix.values())


def test_odd_games_are_rejected_because_starts_cannot_be_balanced():
    with pytest.raises(ValueError, match="positive even"):
        run_round_robin(load_roster(ROSTER), 19, 7)


def test_artifact_pilots_emit_setup_payoff_and_sequencing_telemetry():
    import random

    roster = {deck.id: deck for deck in load_roster(ROSTER)}
    for deck_id in ("donatello", "krang"):
        states = [_pilot(random.Random(seed), roster[deck_id], True) for seed in range(100)]
        assert any(state["artifact_setup_cast"] >= 2 for state in states)
        assert any(state["artifact_payoffs_cast"] > 0 for state in states)
        assert all("artifact_sequencing_holds" in state for state in states)
    assert any(
        _pilot(random.Random(seed), roster["krang"], True)["affinity_mana_saved"] > 0
        for seed in range(100)
    )


def test_interaction_is_only_valued_when_opposing_board_has_targets():
    result = run_round_robin(load_roster(ROSTER), 20, 19)
    for match in result["matches"]:
        for deck_id, state in match["players"].items():
            opponent_id = match["deck_b"] if deck_id == match["deck_a"] else match["deck_a"]
            assert state["interaction_used"] <= match["players"][opponent_id]["board_t8"]
            assert state["interaction_used"] + state["interaction_dead"] == state["interaction"]


def test_sensitivity_comparison_preserves_protocol_and_reports_diagnostics():
    roster = load_roster(ROSTER)
    run = run_round_robin(roster, 20, 23)
    comparison = compare_runs(run, run)
    assert comparison["protocol"]["total_games"] == 900
    assert all(row["shift"] == 0 for row in comparison["matchup_shifts"])
    assert set(comparison["diagnostics"]) == {"donatello", "krang", "shredder"}
