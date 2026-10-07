"""Independently authenticate the proposed Baseline 005 promotion; no simulations."""

from __future__ import annotations

import gzip
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
SOURCE_COMMIT = "df15e8bff151d07ea5018d8766bba3553eb7b200"
RUNTIME = "d4466241f0ffeaca809cd6a05210ad53b9af1011a1d7f833de88657c1cf00924"
CANDIDATE_SHA = "aaa61d3a3d65f7c8ab74062cc8f41d220a46066b44c28e3c71921c570a6b66ed"


def load(path: Path) -> dict:
    return (
        json.loads(gzip.decompress(path.read_bytes()))
        if path.suffix == ".gz"
        else json.loads(path.read_text())
    )


def sha(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes().replace(b"\r\n", b"\n") if path.suffix != ".gz" else path.read_bytes()
    ).hexdigest()


def blob(path: Path) -> str:
    return subprocess.check_output(
        ["git", "hash-object", str(path.relative_to(ROOT))], cwd=ROOT, text=True
    ).strip()


def deck(path: Path) -> Counter[str]:
    lines = path.read_text().splitlines()
    assert lines[0] == "Deck"
    cards: Counter[str] = Counter()
    for line in lines[1:]:
        count, name = line.split(" ", 1)
        cards[name] += int(count)
    assert sum(cards.values()) == 60
    return cards


def validate() -> None:
    old_path = OBL / "baselines/OBL_BASELINE_004_MANIFEST.json"
    old = load(old_path)
    new_path = OBL / "baselines/OBL_BASELINE_005_MANIFEST.json"
    new = load(new_path)
    registry = load(OBL / "ENVIRONMENT_REGISTRY.json")
    ledger = load(OBL / "EXPERIMENT_LEDGER.json")
    combined_manifest = load(OBL / "combined/OBL_COMBINED_007_MANIFEST.json")
    combined = load(OBL / "COMBINED_007_R8A_EVIDENCE.json.gz")
    isolated = load(OBL / "ROUND_8_A_EVIDENCE.json.gz")
    readiness = load(OBL / "ROUND_8_A_SEMANTIC_READINESS.json")
    assert (
        subprocess.check_output(
            ["git", "show", f"{SOURCE_COMMIT}:{old_path.relative_to(ROOT)}"], cwd=ROOT
        )
        == old_path.read_bytes()
    )
    assert old["environment_id"] == "OBL-BASELINE-004"
    assert (
        new["environment_id"]
        == registry["environment_id"]
        == ledger["environment_id"]
        == "OBL-BASELINE-005"
    )
    assert new["lineage_parent_environment"] == "OBL-BASELINE-004"
    assert (
        new["source_combined_environment"]
        == combined_manifest["environment_id"]
        == combined["environment_id"]
        == "OBL-COMBINED-007"
    )
    assert new["promotion_id"] == ledger["promotion_status"] == "OBL-PROMOTION-005"
    assert new["promotion_experiment_ids"] == ["OBL-R8-BEBOP-A"]
    assert (
        new["semantic_runtime_sha256"]
        == registry["semantic_runtime_sha256"]
        == combined["semantic_runtime_sha256"]
        == isolated["semantic_runtime_sha256"]
        == readiness["semantic_runtime_sha256"]
        == RUNTIME
    )
    assert new["schedule_identity"] == combined["schedule_sha256"]
    assert (
        combined["logical_matchups"] == 45
        and combined["logical_games"] == combined["reused_games"] == 4500
    )
    assert combined["newly_executed_games"] == combined["runtime_errors"] == 0
    assert len(combined["combined_games"]) == 4500
    assert (
        new["environment_metrics"]
        == registry["environment_metrics"]
        == {k: combined["combined_global_metrics"][k] for k in old["environment_metrics"]}
    )
    assert new["per_deck_metrics"] == registry["per_deck_metrics"] == combined["combined_per_deck"]
    assert new["per_deck_win_rates"] == {
        k: row["win_rate"] for k, row in combined["combined_per_deck"].items()
    }
    assert registry["current_baseline_manifest"] == {
        "path": str(new_path.relative_to(ROOT)),
        "git_blob_sha1": blob(new_path),
    }
    assert registry["baseline_004_historical_reference"]["manifest"] == {
        "path": str(old_path.relative_to(ROOT)),
        "git_blob_sha1": blob(old_path),
    }
    assert registry["current_simulation_reference"]["sha256"] == sha(
        OBL / "COMBINED_007_R8A_EVIDENCE.json.gz"
    )
    assert registry["current_simulation_reference"]["logical_games"] == 4500
    assert registry["current_simulation_reference"]["semantic_runtime_sha256"] == RUNTIME
    assert registry["reference_evidence"]["git_blob_sha1"] == blob(
        OBL / "COMBINED_007_R8A_RESULTS.md"
    )
    for label, path in (
        ("source_combined_evidence", OBL / "COMBINED_007_R8A_EVIDENCE.json.gz"),
        ("source_combined_results", OBL / "COMBINED_007_R8A_RESULTS.md"),
        ("source_combined_manifest", OBL / "combined/OBL_COMBINED_007_MANIFEST.json"),
    ):
        assert new[label] == {"path": str(path.relative_to(ROOT)), "git_blob_sha1": blob(path)}
    assert new["promotion_evidence"] == [
        {
            "path": "docs/objective-balance-lab/ROUND_8_A_EVIDENCE.json.gz",
            "sha256": sha(OBL / "ROUND_8_A_EVIDENCE.json.gz"),
        },
        {
            "path": "docs/objective-balance-lab/COMBINED_007_R8A_EVIDENCE.json.gz",
            "git_blob_sha1": blob(OBL / "COMBINED_007_R8A_EVIDENCE.json.gz"),
        },
    ]
    old_decks = {r["deck_key"]: r for r in old["decks"]}
    new_decks = {r["deck_key"]: r for r in new["decks"]}
    assert old_decks.keys() == new_decks.keys()
    assert [key for key in old_decks if old_decks[key]["sha256"] != new_decks[key]["sha256"]] == [
        "bebop_rocksteady"
    ]
    for key in old_decks:
        if key != "bebop_rocksteady":
            assert new_decks[key]["source_path"] == old_decks[key]["source_path"]
            assert new_decks[key]["sha256"] == old_decks[key]["sha256"]
            path = ROOT / new_decks[key]["source_path"]
            assert path.read_bytes() == subprocess.check_output(
                ["git", "show", f"{SOURCE_COMMIT}:{path.relative_to(ROOT)}"], cwd=ROOT
            )
    candidate = OBL / "candidates/BEBOP_ROCKSTEADY_OBL_R8_A.txt"
    promoted = OBL / "baselines/BEBOP_ROCKSTEADY_OBL_BASELINE_005.txt"
    prototype = ROOT / "decks/bebop_rocksteady/PROTOTYPE_0.3.txt"
    assert (
        sha(candidate)
        == sha(promoted)
        == sha(prototype)
        == new_decks["bebop_rocksteady"]["sha256"]
        == isolated["candidate_deck_sha256"]
        == CANDIDATE_SHA
    )
    assert (
        new_decks["bebop_rocksteady"]["exact_diff"]
        == readiness["exact_diff"]
        == {"removals": {"Illegitimate Business": 2}, "additions": {"Primordial Pachyderm": 2}}
    )
    parent = deck(ROOT / old_decks["bebop_rocksteady"]["source_path"])
    child = deck(candidate)
    assert {
        name: n - child.get(name, 0) for name, n in parent.items() if n > child.get(name, 0)
    } == {"Illegitimate Business": 2}
    assert {
        name: n - parent.get(name, 0) for name, n in child.items() if n > parent.get(name, 0)
    } == {"Primordial Pachyderm": 2}
    catalog = {
        row["name"]: row
        for row in json.loads((ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json").read_text())
    }
    assert catalog["Illegitimate Business"]["type_line"] == "Land"
    assert parent["Forest"] + parent["Swamp"] == child["Forest"] + child["Swamp"] == 20
    assert sum(n for name, n in parent.items() if "Land" in catalog[name]["type_line"]) == 24
    assert sum(n for name, n in child.items() if "Land" in catalog[name]["type_line"]) == 22
    for path in (OBL / "ROUND_8_A_EVIDENCE.json.gz", OBL / "COMBINED_007_R8A_EVIDENCE.json.gz"):
        assert path.read_bytes() == subprocess.check_output(
            ["git", "show", f"{SOURCE_COMMIT}:{path.relative_to(ROOT)}"], cwd=ROOT
        )
    record = next(r for r in ledger["experiments"] if r["experiment_id"] == "OBL-R8-BEBOP-A")
    assert record["promotion_status"] == record["verdict"] == "PROMOTED"
    assert record["promotion"]["new_environment"] == "OBL-BASELINE-005"
    assert ledger["combined_validation_state"]["OBL-COMBINED-007"] == "COMBINED_VALIDATED"
    assert "20 basic lands" in (OBL / "ROUND_8_A_RESULTS.md").read_text()
    assert "20 basic lands" in (OBL / "COMBINED_007_R8A_RESULTS.md").read_text()
    assert "total lands" in (OBL / "ROUND_8_A_LAND_COUNT_PROVENANCE.md").read_text()
    assert "no R8-B authorized" in (OBL / "ENVIRONMENT_REGISTRY.md").read_text()
    print(
        "Baseline 005 promotion draft: PASS; B&R only; "
        "20 basics unchanged, 24 -> 22 total lands; 0 new games"
    )


if __name__ == "__main__":
    validate()
