"""Round 5 report calculations must agree with the audited parent evidence."""

import json
from pathlib import Path

from tools.build_objective_balance_lab_round5_results import summarize
from tools.validate_objective_balance_lab_round5_results import validate

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/objective-balance-lab/COMBINED_003_RUNTIME_COMPATIBLE_EVIDENCE.json"


def test_parent_summaries_use_authenticated_baseline002_games():
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    for deck, expected_wr, expected_error in (
        ("shredder", 0.75, 0.25),
        ("april_oneil", 0.257778, 0.242222),
        ("krang", 0.351111, 0.195556),
    ):
        summary = summarize(evidence["combined_games"], deck)
        assert summary["win_rate"] == expected_wr
        assert summary["mean_matchup_balance_error"] == expected_error
        assert summary["games"] == 900
        assert summary["battlefield_presence"]["3"]["observed_games"] > 0
        assert summary["battlefield_presence"]["3"]["mean_creatures_if_observed"] > 0


def test_round5_results_are_complete_and_governance_safe():
    assert validate(replay=False) == {
        "status": "PASS",
        "candidates": 5,
        "games": 4500,
        "runtime_errors": 0,
        "replayed_fingerprints": 0,
    }
