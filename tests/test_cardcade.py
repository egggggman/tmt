import json
from pathlib import Path

import pytest

from tmnt_design_studio.cardcade import load_roster, run_round_robin, validate_roster, write_run

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
