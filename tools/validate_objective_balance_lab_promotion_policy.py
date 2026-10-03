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
    require(registry["status"] == "OFFICIAL_BASELINE", "No official baseline")
    require(
        registry["environment_id"] in {"OBL-BASELINE-002", "OBL-BASELINE-003"},
        "Unknown current baseline",
    )
    for rejected_id in ("OBL-R4-RAPHAEL-A", "OBL-R4-RAPHAEL-B", "OBL-R4-RAPHAEL-D"):
        rejected = next(row for row in ledger["experiments"] if row["experiment_id"] == rejected_id)
        require(rejected["promotion_status"] != "PROMOTED", f"Unexpected promotion: {rejected_id}")
    history = (OBL / "PROMOTION_HISTORY.md").read_text(encoding="utf-8")
    require(
        history.count("## Promotion OBL-PROMOTION-002") == 1, "Promotion history is not append-only"
    )
    validate_baseline002()
    if registry["environment_id"] == "OBL-BASELINE-003":
        from validate_objective_balance_lab_baseline003_metrics import validate as validate003

        baseline003 = load("docs/objective-balance-lab/baselines/OBL_BASELINE_003_MANIFEST.json")
        combined005 = load("docs/objective-balance-lab/COMBINED_005_EVIDENCE.json")
        promoted = {"OBL-R5-SHREDDER-B", "OBL-R5-APRIL_ONEIL-A"}
        require(
            set(baseline003["promotion_experiment_ids"]) == promoted,
            "Unexpected Baseline 003 promotion subset",
        )
        require(
            combined005["environment_decision"] == "COMBINED_ENVIRONMENT_IMPROVED",
            "Combined 005 did not improve",
        )
        for experiment_id in promoted:
            decision = combined005["candidate_decisions"][experiment_id]
            candidate = next(
                row for row in ledger["experiments"] if row["experiment_id"] == experiment_id
            )
            require(
                decision["combined_verdict"] == "COMBINED_VALIDATION_PASSED"
                and decision["promotion_eligibility"] == "PROMOTION_ELIGIBLE",
                f"Combined gate failed: {experiment_id}",
            )
            require(
                candidate["verdict"] == candidate["promotion_status"] == "PROMOTED",
                f"Candidate state failed: {experiment_id}",
            )
        for experiment_id in ("OBL-R5-SHREDDER-A", "OBL-R5-KRANG-A", "OBL-R5-KRANG-B"):
            candidate = next(
                row for row in ledger["experiments"] if row["experiment_id"] == experiment_id
            )
            require(
                candidate["promotion_status"] != "PROMOTED", f"Wrong promotion: {experiment_id}"
            )
        require(
            history.count("## Promotion OBL-PROMOTION-003") == 1, "Promotion 003 is not append-only"
        )
        validate003()
    print(
        json.dumps(
            {
                "status": "PASS",
                "promotion": "OBL-PROMOTION-003"
                if registry["environment_id"] == "OBL-BASELINE-003"
                else "OBL-PROMOTION-002",
                "simulations": 0,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
