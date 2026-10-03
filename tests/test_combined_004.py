"""Combined 004's composed matrix must stay authenticated and simulation-free in tests."""

import json
from pathlib import Path

from tools.validate_combined_004 import validate

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/objective-balance-lab/COMBINED_004_EVIDENCE.json"


def test_combined_004_provenance_and_metrics():
    assert validate(replay=False) == {
        "status": "PASS",
        "logical_matchups": 45,
        "logical_games": 4500,
        "reused_games": 4200,
        "new_games": 300,
        "runtime_errors": 0,
        "replayed_fingerprints": 0,
    }
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert evidence["provenance_counts"] == {
        "BASELINE_002_REUSED": 21,
        "ROUND_5_REUSED": 21,
        "COMBINED_004_NEW_PAIRING": 3,
    }
    assert evidence["baseline_global_metrics"]["mean_matchup_balance_error"] == 0.189556
    assert evidence["combined_global_metrics"]["mean_matchup_balance_error"] == 0.172222
    assert evidence["environment_decision"] == "COMBINED_ENVIRONMENT_IMPROVED"
