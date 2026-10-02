"""Check the explicit Combined 003 gate behind Baseline 002 promotion."""

from __future__ import annotations

import json

from objective_balance_lab_promotion_metrics import OBL, load, require, validate_baseline002


def main() -> int:
    manifest = load("docs/objective-balance-lab/baselines/OBL_BASELINE_002_MANIFEST.json")
    authority = load("docs/objective-balance-lab/COMBINED_003_RUNTIME_COMPATIBLE_EVIDENCE.json")
    ledger = load("docs/objective-balance-lab/EXPERIMENT_LEDGER.json")
    registry = load("docs/objective-balance-lab/ENVIRONMENT_REGISTRY.json")
    record = next(
        row for row in ledger["experiments"] if row["experiment_id"] == "OBL-R4-RAPHAEL-C"
    )
    require(
        authority["environment_decision"] == "COMBINED_ENVIRONMENT_IMPROVED",
        "Combined gate did not improve",
    )
    require(
        authority["raphael_analysis"]["combined_validation"] == "COMBINED_VALIDATION_PASSED",
        "Candidate did not pass combined validation",
    )
    require(
        authority["raphael_analysis"]["promotion_eligibility"] == "PROMOTION_ELIGIBLE",
        "Candidate was not eligible",
    )
    require(
        authority["raphael_analysis"]["identity"] == "IDENTITY_STRENGTHENED",
        "Candidate identity weakened",
    )
    require(
        record["verdict"] == record["promotion_status"] == "PROMOTED",
        "Candidate promotion state mismatch",
    )
    require(
        manifest["promotion_experiment_ids"] == [record["experiment_id"]],
        "Manifest promotion selection mismatch",
    )
    require(registry["status"] == "OFFICIAL_BASELINE", "Baseline 002 is not official")
    for rejected_id in ("OBL-R4-RAPHAEL-A", "OBL-R4-RAPHAEL-B", "OBL-R4-RAPHAEL-D"):
        rejected = next(row for row in ledger["experiments"] if row["experiment_id"] == rejected_id)
        require(rejected["promotion_status"] != "PROMOTED", f"Unexpected promotion: {rejected_id}")
    history = (OBL / "PROMOTION_HISTORY.md").read_text(encoding="utf-8")
    require(
        history.count("## Promotion OBL-PROMOTION-002") == 1, "Promotion history is not append-only"
    )
    validate_baseline002()
    print(json.dumps({"status": "PASS", "promotion": "OBL-PROMOTION-002", "simulations": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
