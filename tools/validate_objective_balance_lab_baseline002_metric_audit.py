"""Validate the Baseline 002 metric audit against raw Combined 003 games."""

from __future__ import annotations

import json

from objective_balance_lab_promotion_metrics import (
    AUTHORITY_PATH,
    OBL,
    load,
    recorded_evidence_sha,
    require,
    validate_baseline002,
)


def main() -> int:
    audit = load("docs/objective-balance-lab/BASELINE_002_METRIC_AUDIT.json")
    old = load("docs/objective-balance-lab/COMBINED_001_EVIDENCE.json")
    authority = load(AUTHORITY_PATH)
    metrics, per_deck, digest = validate_baseline002()
    require(audit["conclusion"] == "BASELINE_002_METADATA_CORRECTED", "Wrong audit conclusion")
    require(audit["baseline_environment"] == "OBL-BASELINE-002", "Wrong baseline identity")
    require(
        audit["recorded_evidence_sha256_line_endings"] == "CRLF", "Unknown evidence hash convention"
    )
    require(
        audit["promotion_authority"] == authority["environment_id"], "Wrong promotion authority"
    )
    require(audit["authority_source"]["path"] == AUTHORITY_PATH, "Wrong audit source")
    require(
        audit["authority_source"]["sha256"] == recorded_evidence_sha(AUTHORITY_PATH),
        "Audit source SHA mismatch",
    )
    require(
        audit["erroneous_metric_source"]["sha256"]
        == recorded_evidence_sha(audit["erroneous_metric_source"]["path"]),
        "Historical evidence SHA mismatch",
    )
    require(
        audit["erroneous_reported_mean_balance_error"]
        == old["global_metrics"]["combined"]["mean_matchup_balance_error"],
        "The 19.33% source is not Combined 001",
    )
    require(audit["global_metrics"] == metrics, "Audit global metrics differ from raw games")
    require(audit["per_deck_win_rates"] == per_deck, "Audit deck WRs differ from raw games")
    require(audit["matchup_fingerprint_digest_sha256"] == digest, "Audit cell digest mismatch")
    require(audit["matchup_cells"] == 45 and audit["logical_games"] == 4500, "Wrong sample size")
    require(
        audit["new_simulations"] == authority["newly_executed_games"] == 0, "Unexpected simulations"
    )
    require(audit["schedule_sha256"] == authority["schedule_sha256"], "Schedule mismatch")
    require(
        audit["semantic_runtime_sha256"] == authority["semantic_runtime_sha256"],
        "Semantic runtime mismatch",
    )
    require((OBL / "BASELINE_002_METRIC_AUDIT.md").is_file(), "Missing human audit report")
    print(
        json.dumps(
            {
                "status": "PASS",
                "conclusion": audit["conclusion"],
                "mean_matchup_balance_error": metrics["mean_matchup_balance_error"],
                "matchups": audit["matchup_cells"],
                "logical_games": audit["logical_games"],
                "new_simulations": 0,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
