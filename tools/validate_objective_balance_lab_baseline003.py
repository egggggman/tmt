"""Validate the exact two-deck, simulation-free Baseline 003 promotion."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
sys.path.insert(0, str(ROOT / "tools"))

import run_combined_004 as c4  # noqa: E402
import run_objective_balance_lab_round1 as r1  # noqa: E402
from objective_balance_lab_semantic_identity import identity  # noqa: E402
from validate_combined_005 import validate as validate_combined005  # noqa: E402
from validate_objective_balance_lab_baseline003_metrics import (  # noqa: E402
    validate as validate_metrics,
)

PROMOTED = {
    "shredder": (
        "OBL-R5-SHREDDER-B",
        "1ce0828b6ac107bc8cdf2e0b965d919e83941316803880a71d11bbbb48902fc1",
    ),
    "april_oneil": (
        "OBL-R5-APRIL_ONEIL-A",
        "ebaff265d90b5cfbec4f7e9662a9d105f9ef8f58a17b06949626ed2ff898b8b7",
    ),
}


def read(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def git_bytes(relative: str, commit: str = "HEAD") -> bytes:
    return subprocess.check_output(["git", "show", f"{commit}:{relative}"], cwd=ROOT)


def validate() -> dict:
    combined_validation = validate_combined005()
    assert combined_validation["status"] == "PASS"
    assert combined_validation["new_games"] == 0
    metrics_validation = validate_metrics()
    assert metrics_validation["status"] == "PASS"
    baseline = read("docs/objective-balance-lab/baselines/OBL_BASELINE_003_MANIFEST.json")
    parent = read("docs/objective-balance-lab/baselines/OBL_BASELINE_002_MANIFEST.json")
    combined = read("docs/objective-balance-lab/COMBINED_005_EVIDENCE.json")
    combined_manifest = read("docs/objective-balance-lab/combined/OBL_COMBINED_005_MANIFEST.json")
    round5 = read("docs/objective-balance-lab/ROUND_5_EVIDENCE.json")
    registry = read("docs/objective-balance-lab/ENVIRONMENT_REGISTRY.json")
    ledger = read("docs/objective-balance-lab/EXPERIMENT_LEDGER.json")
    assert baseline["environment_id"] == registry["environment_id"] == "OBL-BASELINE-003"
    assert registry["current_baseline_manifest"] == {
        "path": "docs/objective-balance-lab/baselines/OBL_BASELINE_003_MANIFEST.json",
        "sha256": hashlib.sha256(
            (OBL / "baselines/OBL_BASELINE_003_MANIFEST.json").read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest(),
    }
    assert baseline["state"] == registry["status"] == "OFFICIAL_BASELINE"
    assert parent["environment_id"] == "OBL-BASELINE-002"
    assert baseline["lineage_parent_environment"] == "OBL-BASELINE-002"
    assert baseline["source_combined_environment"] == "OBL-COMBINED-005"
    assert baseline["promotion_authority"] == "OBL-COMBINED-005"
    assert baseline["promotion_id"] == ledger["promotion_status"] == "OBL-PROMOTION-003"
    assert baseline["source_combined_state"] == "COMBINED_VALIDATED"
    assert ledger["combined_validation_state"] == {"OBL-COMBINED-005": "COMBINED_VALIDATED"}
    assert registry["source_combined_state"] == "COMBINED_VALIDATED"
    assert (
        baseline["repository_sha"]
        == registry["repository_sha"]
        == "ed8848c51750d7b2343a35877857304d88371a5e"
    )
    assert baseline["semantic_runtime_sha256"] == identity()["aggregate_semantic_runtime_sha256"]
    assert baseline["semantic_runtime_sha256"] == combined["semantic_runtime_sha256"]
    assert baseline["schedule_identity"] == combined["schedule_sha256"]
    assert (
        baseline["next_gate"]
        == registry["next_gate"]
        == ledger["next_gate"]
        == "ROUND_6_EXPERIMENT_DESIGN"
    )
    assert registry["superseded_environments"][-1] == {
        "environment_id": "OBL-BASELINE-002",
        "status": "SUPERSEDED",
    }
    assert len({row["environment_id"] for row in registry["superseded_environments"]}) == 3
    assert set(baseline["promotion_experiment_ids"]) == {item[0] for item in PROMOTED.values()}
    assert set(combined_manifest["selected_experiments"]) == set(
        baseline["promotion_experiment_ids"]
    )
    assert set(baseline["retained_baseline_decks"]) == set(r1.DECKS) - set(PROMOTED)
    parent_decks = {row["deck_key"]: row for row in parent["decks"]}
    current_decks = {row["deck_key"]: row for row in baseline["decks"]}
    selected_decks = {row["deck_key"]: row for row in combined_manifest["decks"]}
    registry_decks = {row["deck_key"]: row for row in registry["decks"]}
    assert (
        len(parent_decks) == len(current_decks) == len(selected_decks) == len(registry_decks) == 10
    )
    assert set(parent_decks) == set(current_decks) == set(selected_decks) == set(registry_decks)
    cards = r1.catalog()
    for deck, row in current_decks.items():
        old = parent_decks[deck]
        selected = selected_decks[deck]
        assert row["sha256"] == selected["sha256"] == registry_decks[deck]["sha256"]
        assert row["parent_baseline_sha256"] == old["sha256"]
        assert row["parent_environment_id"] == "OBL-BASELINE-002"
        assert row["environment_id"] == "OBL-BASELINE-003"
        assert registry_decks[deck]["official_current_baseline_version"] == "OBL-BASELINE-003"
        assert row["source_path"] == registry_decks[deck]["source_path"]
        assert sum(r1.validate_deck(ROOT / row["source_path"], cards)["cards"].values()) == 60
        if deck in PROMOTED:
            experiment_id, expected_sha = PROMOTED[deck]
            source = round5["candidate_manifests"][experiment_id]
            assert row["sha256"] == expected_sha == source["candidate_sha256"]
            assert row["promotion_experiment_id"] == experiment_id
            assert row["promotion_status"] == "PROMOTED"
            assert (
                row["exact_diff"]
                == selected["exact_diff"]
                == {
                    "removals": source["removals"],
                    "additions": source["additions"],
                }
            )
            assert source["parent_sha256"] == old["sha256"]
            candidate_bytes = git_bytes(source["candidate_path"])
            artifact_bytes = (ROOT / row["source_path"]).read_bytes()
            assert artifact_bytes == candidate_bytes
            assert hashlib.sha256(artifact_bytes).hexdigest() == expected_sha
            if not subprocess.run(
                ["git", "cat-file", "-e", f"HEAD:{row['source_path']}"],
                cwd=ROOT,
                stderr=subprocess.DEVNULL,
                check=False,
            ).returncode:
                assert git_bytes(row["source_path"]) == candidate_bytes
            assert (
                combined["candidate_decisions"][experiment_id]["combined_verdict"]
                == "COMBINED_VALIDATION_PASSED"
            )
            assert (
                combined["candidate_decisions"][experiment_id]["promotion_eligibility"]
                == "PROMOTION_ELIGIBLE"
            )
            assert registry_decks[deck]["promotion_status"] == f"PROMOTED: {experiment_id}"
        else:
            c4.verify_deck_bytes(row["source_path"], row["sha256"])
            assert row["sha256"] == old["sha256"]
            assert row["source_path"] == old["source_path"]
            assert row["exact_diff"] == {"removals": {}, "additions": {}}
            assert row["promotion_experiment_id"] is None
            assert (
                row["promotion_status"]
                == registry_decks[deck]["promotion_status"]
                == "BASELINE_RETAINED"
            )
    ledger_by_id = {row["experiment_id"]: row for row in ledger["experiments"]}
    assert len(ledger_by_id) == len(ledger["experiments"])
    assert {
        row["experiment_id"]
        for row in ledger["experiments"]
        if row.get("promotion_status") == "PROMOTED"
    } == {
        "OBL-R1-LEONARDO-A",
        "OBL-R2-DONATELLO-A",
        "OBL-R2-BEBOP_ROCKSTEADY-B",
        "OBL-R2-CASEY_JONES-B",
        "OBL-R4-RAPHAEL-C",
        *[item[0] for item in PROMOTED.values()],
    }
    for deck, (experiment_id, expected_sha) in PROMOTED.items():
        row = ledger_by_id[experiment_id]
        assert row["candidate"]["sha256"] == expected_sha
        assert row["verdict"] == row["promotion_status"] == "PROMOTED"
        assert row["promotion"]["new_environment"] == "OBL-BASELINE-003"
        assert row["promotion"]["source_combined_environment"] == "OBL-COMBINED-005"
        assert row["promotion"]["combined_validation"] == "COMBINED_VALIDATED"
        assert row["promotion"]["identity_classification"] == row["identity_classification"]
        if deck == "april_oneil":
            assert row["aliases"] == row["promotion"]["aliases"] == ["OBL-R5-APRIL-A"]
    for experiment_id in ("OBL-R5-SHREDDER-A", "OBL-R5-KRANG-A", "OBL-R5-KRANG-B"):
        assert ledger_by_id[experiment_id]["promotion_status"] != "PROMOTED"
    history_path = "docs/objective-balance-lab/PROMOTION_HISTORY.md"
    history = (ROOT / history_path).read_text(encoding="utf-8")
    marker = "\n## Promotion OBL-PROMOTION-003"
    assert marker in history
    previous_history = history.split(marker, 1)[0]
    assert hashlib.sha256(previous_history.encode("utf-8")).hexdigest() == (
        "7ea6d6a23a3ac92c43eb43649ce37ab93ddafc077ae31e84b25caf93282344a1"
    )
    assert history.count("## Promotion OBL-PROMOTION-003") == 1
    assert history.count("### Shredder — OBL-PROMOTION-003-SHREDDER") == 1
    assert history.count("### April O'Neil — OBL-PROMOTION-003-APRIL_ONEIL") == 1
    assert "Krang vs Shredder 12/88" in history
    assert "12/88" in registry["carried_forward_risk"]
    for name in ("ENVIRONMENT_REGISTRY.md", "EXPERIMENT_LEDGER.md", "PROMOTION_HISTORY.md"):
        markdown = OBL / name
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", markdown.read_text(encoding="utf-8")):
            if "://" not in target and not target.startswith("#"):
                assert (markdown.parent / target.split("#", 1)[0].strip("<>")).is_file(), (
                    name,
                    target,
                )
    assert not subprocess.check_output(
        [
            "git",
            "diff",
            "--name-only",
            "HEAD",
            "--",
            "decks",
            "docs/objective-balance-lab/candidates",
        ],
        cwd=ROOT,
        text=True,
    ).strip()
    return {
        "status": "PASS",
        "environment": "OBL-BASELINE-003",
        "official_decks": 10,
        "promoted": [item[0] for item in PROMOTED.values()],
        "new_simulations": 0,
    }


def main() -> int:
    print(json.dumps(validate(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
