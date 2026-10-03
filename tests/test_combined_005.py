"""Combined 005 stays a provenance-only, zero-new-game composition."""

import json
from pathlib import Path

from tools.validate_combined_005 import validate

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/objective-balance-lab/COMBINED_005_EVIDENCE.json"


def test_combined_005_reuses_all_cells_and_improves_baseline():
    assert validate() == {
        "status": "PASS",
        "matchups": 45,
        "logical_games": 4500,
        "reused_games": 4500,
        "new_games": 0,
        "provenance_fingerprints": 45,
        "runtime_errors": 0,
    }
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert evidence["provenance_counts"] == {
        "BASELINE_002_REUSED": 28,
        "ROUND_5_REUSED": 16,
        "COMBINED_004_REUSED": 1,
    }
    assert evidence["combined_005_global_metrics"]["mean_matchup_balance_error"] == 0.176667
    assert evidence["environment_decision"] == "COMBINED_ENVIRONMENT_IMPROVED"
