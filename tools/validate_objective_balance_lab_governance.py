"""Validate the OBL registry, lineage, and promotion governance contracts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

# ruff: noqa: E501

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
DECKS = {
    "LEONARDO",
    "RAPHAEL",
    "DONATELLO",
    "MICHELANGELO",
    "SPLINTER",
    "SHREDDER",
    "KRANG",
    "BEBOP_ROCKSTEADY",
    "APRIL_ONEIL",
    "CASEY_JONES",
}
EXPECTED_MAIN = "4f2d69d87bf5a3cbb4d8d9a2508be3851eb2e836"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    registry = json.loads((OBL / "ENVIRONMENT_REGISTRY.json").read_text(encoding="utf-8"))
    ledger = json.loads((OBL / "EXPERIMENT_LEDGER.json").read_text(encoding="utf-8"))
    assert registry["environment_id"] == "OBL-BASELINE-000"
    assert registry["repository_sha"] == EXPECTED_MAIN
    assert registry["status"] == "BASELINE"
    assert registry["promotion_status"] == "NO_PROMOTIONS"
    assert registry["next_gate"] == "SELECT COMBINED-MATRIX CANDIDATES"
    assert len(registry["decks"]) == 10
    assert {deck["deck_key"].upper() for deck in registry["decks"]} == DECKS
    for deck in registry["decks"]:
        path = ROOT / deck["source_path"]
        assert path.exists()
        assert sha(path) == deck["sha256"]
        assert deck["promotion_status"] == "BASELINE_UNCHANGED; no candidate promoted"
        assert deck["candidate_lineage"]

    assert len(ledger["experiments"]) == 30
    assert len({record["experiment_id"] for record in ledger["experiments"]}) == 30
    assert sum(record["round"] == "R1" for record in ledger["experiments"]) == 10
    assert sum(record["round"] == "R2" for record in ledger["experiments"]) == 20
    for record in ledger["experiments"]:
        parent = ROOT / record["parent"]["path"]
        candidate = ROOT / record["candidate"]["path"]
        assert parent.exists() and candidate.exists()
        assert sha(parent) == record["parent"]["sha256"]
        assert sha(candidate) == record["candidate"]["sha256"]
        assert record["source_evidence"]["path"] in {
            "docs/objective-balance-lab/ROUND_1_EVIDENCE.json",
            "docs/objective-balance-lab/ROUND_2_EVIDENCE.json",
        }
        evidence = ROOT / record["source_evidence"]["path"]
        assert sha(evidence) == record["source_evidence"]["sha256"]
        assert record["promotion_status"] == "NOT_PROMOTED_COMBINED_MATRIX_REQUIRED"
        assert record["verdict"] != "PROMOTED"

    assert all(record["result_metrics"] for record in ledger["experiments"])
    assert not any(record["promotion_status"] == "PROMOTED" for record in ledger["experiments"])
    print(
        json.dumps(
            {
                "environment": "OBL-BASELINE-000",
                "official_decks": 10,
                "r1_experiments": 10,
                "r2_experiments": 20,
                "promoted": 0,
                "next_gate": "SELECT COMBINED-MATRIX CANDIDATES",
            }
        )
    )


if __name__ == "__main__":
    main()
