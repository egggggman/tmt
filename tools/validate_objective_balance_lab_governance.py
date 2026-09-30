"""Validate the OBL registry, lineage, and promotion governance contracts."""

from __future__ import annotations

import hashlib
import json
import subprocess
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
EXPECTED_MAIN = "7d74d24226f904dfb85b3c4a9e57ab8f9de5500a"
PROMOTED = {
    "OBL-R1-LEONARDO-A",
    "OBL-R2-DONATELLO-A",
    "OBL-R2-BEBOP_ROCKSTEADY-B",
    "OBL-R2-CASEY_JONES-B",
}


def sha(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    return hashlib.sha256(subprocess.check_output(["git", "show", f"HEAD:{relative}"])).hexdigest()


def main() -> None:
    registry = json.loads((OBL / "ENVIRONMENT_REGISTRY.json").read_text(encoding="utf-8"))
    ledger = json.loads((OBL / "EXPERIMENT_LEDGER.json").read_text(encoding="utf-8"))
    manifest = json.loads((OBL / "baselines/OBL_BASELINE_001_MANIFEST.json").read_text(encoding="utf-8"))
    combined_manifest = json.loads((OBL / "combined/OBL_COMBINED_001_MANIFEST.json").read_text(encoding="utf-8"))
    assert registry["environment_id"] == "OBL-BASELINE-001"
    assert registry["repository_sha"] == EXPECTED_MAIN
    assert registry["status"] == "BASELINE"
    assert registry["promotion_status"] == "PROMOTED_FROM_OBL-BASELINE-000"
    assert registry["next_gate"] == "ROUND_3_EXPERIMENT_DESIGN"
    assert registry["lineage_parent_environment"] == "OBL-BASELINE-000"
    assert len(registry["decks"]) == 10
    assert {deck["deck_key"].upper() for deck in registry["decks"]} == DECKS
    assert manifest["environment_id"] == "OBL-BASELINE-001"
    assert manifest["repository_sha"] == EXPECTED_MAIN
    assert manifest["lineage_parent_environment"] == "OBL-BASELINE-000"
    assert manifest["source_combined_environment"] == "OBL-COMBINED-001"
    assert {item["promotion_experiment_id"] for item in manifest["decks"]} == PROMOTED | {None}
    assert len(manifest["decks"]) == 10
    assert combined_manifest["environment_id"] == "OBL-COMBINED-001"
    assert combined_manifest["state"] == "EXPERIMENTAL_COMBINED_ENVIRONMENT"
    manifest_by_key = {item["deck_key"]: item for item in manifest["decks"]}
    combined_by_key = {item["deck_key"]: item for item in combined_manifest["selected_decks"]}
    for deck in registry["decks"]:
        path = ROOT / deck["source_path"]
        assert path.exists()
        assert deck["candidate_lineage"]
        assert manifest_by_key[deck["deck_key"]]["sha256"] == deck["sha256"]
        assert deck["official_current_baseline_version"] == "OBL-BASELINE-001"
        assert combined_by_key[deck["deck_key"]]["parent_baseline_sha256"] == manifest_by_key[deck["deck_key"]]["parent_baseline_sha256"]
        assert not subprocess.run(["git", "diff", "--quiet", "HEAD", "--", deck["source_path"]], check=False).returncode

    assert len(ledger["experiments"]) == 30
    assert len({record["experiment_id"] for record in ledger["experiments"]}) == 30
    assert sum(record["round"] == "R1" for record in ledger["experiments"]) == 10
    assert sum(record["round"] == "R2" for record in ledger["experiments"]) == 20
    for record in ledger["experiments"]:
        parent = ROOT / record["parent"]["path"]
        candidate = ROOT / record["candidate"]["path"]
        assert parent.exists() and candidate.exists()
        assert not subprocess.run(["git", "diff", "--quiet", "HEAD", "--", record["parent"]["path"]], check=False).returncode
        assert sha(candidate) == record["candidate"]["sha256"]
        assert record["source_evidence"]["path"] in {
            "docs/objective-balance-lab/ROUND_1_EVIDENCE.json",
            "docs/objective-balance-lab/ROUND_2_EVIDENCE.json",
        }
        evidence = ROOT / record["source_evidence"]["path"]
        assert evidence.exists()
        if record["experiment_id"] in PROMOTED:
            assert record["promotion_status"] == "PROMOTED"
            assert record["verdict"] == "PROMOTED"
            assert record["promotion"]["new_environment"] == "OBL-BASELINE-001"
        else:
            assert record["promotion_status"] != "PROMOTED"
            assert record["verdict"] != "PROMOTED"

    assert all(record["result_metrics"] for record in ledger["experiments"])
    assert {record["experiment_id"] for record in ledger["experiments"] if record["promotion_status"] == "PROMOTED"} == PROMOTED
    history = (OBL / "PROMOTION_HISTORY.md").read_text(encoding="utf-8")
    assert "OBL-PROMOTION-001" in history
    assert "OBL-BASELINE-000" in history and "OBL-BASELINE-001" in history
    print(
        json.dumps(
            {
                "environment": "OBL-BASELINE-001",
                "official_decks": 10,
                "r1_experiments": 10,
                "r2_experiments": 20,
                "promoted": len(PROMOTED),
                "next_gate": "ROUND_3_EXPERIMENT_DESIGN",
            }
        )
    )


if __name__ == "__main__":
    main()
