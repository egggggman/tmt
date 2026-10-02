"""Validate Baseline 002 promotion lineage and deck identities."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from objective_balance_lab_promotion_metrics import validate_baseline002

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
RUNTIME = "78bcce5b5f635f11c67247df91f90fef2bf0dbf948973c5c1ac38419f28b0e25"
EXPERIMENT = "OBL-R4-RAPHAEL-C"


def logical_sha(path: Path) -> str:
    return hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()


def main() -> int:
    manifest = json.loads(
        (OBL / "baselines/OBL_BASELINE_002_MANIFEST.json").read_text(encoding="utf-8")
    )
    old = json.loads((OBL / "baselines/OBL_BASELINE_001_MANIFEST.json").read_text(encoding="utf-8"))
    registry = json.loads((OBL / "ENVIRONMENT_REGISTRY.json").read_text(encoding="utf-8"))
    ledger = json.loads((OBL / "EXPERIMENT_LEDGER.json").read_text(encoding="utf-8"))
    combined = json.loads(
        (OBL / "COMBINED_003_RUNTIME_COMPATIBLE_EVIDENCE.json").read_text(encoding="utf-8")
    )
    identity = json.loads((OBL / "SEMANTIC_RUNTIME_IDENTITY.json").read_text(encoding="utf-8"))
    r4c = json.loads((OBL / "ROUND_4B_RAPHAEL_EVIDENCE.json").read_text(encoding="utf-8"))[
        "candidate_manifests"
    ][EXPERIMENT]
    assert manifest["environment_id"] == registry["environment_id"] == "OBL-BASELINE-002"
    assert manifest["state"] == registry["status"] == "OFFICIAL_BASELINE"
    assert manifest["semantic_runtime_sha256"] == combined["semantic_runtime_sha256"] == RUNTIME
    assert identity["current"]["aggregate_semantic_runtime_sha256"] == RUNTIME
    assert manifest["source_combined_environment"] == "OBL-COMBINED-003"
    assert (
        manifest["source_combined_evidence"]["path"]
        == "docs/objective-balance-lab/COMBINED_003_RUNTIME_COMPATIBLE_EVIDENCE.json"
    )
    assert manifest["schedule_identity"] == combined["schedule_sha256"]
    assert len(manifest["decks"]) == 10
    old_by_key = {row["deck_key"]: row for row in old["decks"]}
    for row in manifest["decks"]:
        path = ROOT / row["source_path"]
        assert path.exists()
        assert (
            sum(
                int(line.split(" ", 1)[0])
                for line in path.read_text(encoding="utf-8").splitlines()
                if line and line != "Deck"
            )
            == 60
        )
        if row["deck_key"] == "raphael":
            assert row["promotion_experiment_id"] == EXPERIMENT
            assert row["sha256"] == r4c["candidate_sha256"] == logical_sha(path)
            assert row["parent_baseline_sha256"] == old_by_key["raphael"]["sha256"]
        else:
            assert row["sha256"] == old_by_key[row["deck_key"]]["sha256"]
            assert row["source_path"] == old_by_key[row["deck_key"]]["source_path"]
            assert row["promotion_experiment_id"] is None
    record = next(row for row in ledger["experiments"] if row["experiment_id"] == EXPERIMENT)
    assert record["verdict"] == record["promotion_status"] == "PROMOTED"
    assert record["promotion"]["new_environment"] == "OBL-BASELINE-002"
    assert sum(row.get("promotion_status") == "PROMOTED" for row in ledger["experiments"]) == 5
    assert "OBL-PROMOTION-002" in (OBL / "PROMOTION_HISTORY.md").read_text(encoding="utf-8")
    validate_baseline002()
    assert not subprocess.check_output(
        ["git", "diff", "--name-only", "--", "decks"], cwd=ROOT, text=True
    ).strip()
    print(
        json.dumps(
            {
                "status": "PASS",
                "environment": "OBL-BASELINE-002",
                "official_decks": 10,
                "promoted": EXPERIMENT,
                "simulations": 0,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
