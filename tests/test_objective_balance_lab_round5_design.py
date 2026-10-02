"""Round 5 design checks must never launch a match simulation."""

from tools.validate_objective_balance_lab_round5_design import _payable, validate


def test_round5_candidate_design_is_reproducible_and_simulation_free():
    assert validate() == {
        "status": "PASS",
        "candidates": 5,
        "planned_games": 4500,
        "new_simulations": 0,
    }


def test_standard_hybrid_cost_is_payable_without_commander_color_identity():
    assert _payable("{1}{U/R}", "U")
    assert _payable("{1}{U/R}", "R")
    assert not _payable("{1}{U/R}", "B")
    assert not _payable("{1}{W}", "U")
