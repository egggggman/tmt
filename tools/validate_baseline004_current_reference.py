"""Validate the registry handoff to the corrected Baseline 004 simulation control."""

from __future__ import annotations

import gzip
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
sys.path.insert(0, str(ROOT / "tools"))

from objective_balance_lab_semantic_identity import identity  # noqa: E402


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blob(path: Path) -> str:
    return subprocess.check_output(
        ["git", "hash-object", str(path.relative_to(ROOT))], cwd=ROOT, text=True
    ).strip()


def main() -> None:
    registry = load(OBL / "ENVIRONMENT_REGISTRY.json")
    ledger = load(OBL / "EXPERIMENT_LEDGER.json")
    manifest_path = OBL / "baselines/OBL_BASELINE_004_MANIFEST.json"
    manifest = load(manifest_path)
    analysis_path = OBL / "BASELINE_004_CYCLING_PILOT_ANALYSIS.json"
    analysis = load(analysis_path)
    diagnosis_path = OBL / "ROUND_8_BEBOP_CORRECTED_CONTROL_DIAGNOSTIC.json"
    diagnosis = load(diagnosis_path)
    control_path = OBL / "BASELINE_004_CYCLING_PILOT_CONTROL.json.gz"
    control = json.loads(gzip.decompress(control_path.read_bytes()))
    report_path = OBL / "BASELINE_004_CYCLING_PILOT_CONTROL.md"
    if registry["environment_id"] == "OBL-BASELINE-005":
        historical = registry["baseline_004_historical_reference"]
        saved = historical["simulation_control"]
        assert blob(manifest_path) == historical["manifest"]["git_blob_sha1"]
        assert saved["control_id"] == control["evidence_id"]
        assert saved["sha256"] == sha(control_path)
        assert saved["git_blob_sha1"] == blob(control_path)
        assert saved["analysis_git_blob_sha1"] == blob(analysis_path)
        assert saved["diagnosis_git_blob_sha1"] == blob(diagnosis_path)
        assert saved["semantic_runtime_sha256"] == control["semantic_runtime_sha256"]
        assert saved["schedule_sha256"] == control["schedule_sha256"]
        assert saved["games"] == len(control["games"]) == 4500
        assert saved["matchups"] == len(control["cell_hashes"]) == 45
        assert saved["deterministic_replay_samples"] == len(control["replays"]) == 6
        assert control["runtime_errors"] == saved["decks_changed"] == 0
        assert historical["reference_evidence"] == {
            "path": str(report_path.relative_to(ROOT)),
            "git_blob_sha1": blob(report_path),
        }
        assert historical["environment_metrics"] == {
            key: analysis["new_global_metrics"][key] for key in historical["environment_metrics"]
        }
        assert {row["deck_key"]: row["sha256"] for row in control["baseline_decks"]} == {
            row["deck_key"]: row["sha256"] for row in manifest["decks"]
        }
        print("Baseline 004 historical simulation reference: PASS; 4,500 preserved games")
        return
    current = registry["current_simulation_control"]
    old = registry["original_promotion_reference"]

    assert (
        registry["environment_id"]
        == ledger["environment_id"]
        == manifest["environment_id"]
        == "OBL-BASELINE-004"
    )
    assert (
        blob(manifest_path)
        == registry["current_baseline_manifest"]["git_blob_sha1"]
        == diagnosis["manifest_git_blob_sha1"]
    )
    assert manifest["semantic_runtime_sha256"] == old["semantic_runtime_sha256"]
    assert old["environment_metrics"] == manifest["environment_metrics"]
    assert old["reference_evidence"]["path"].endswith("COMBINED_006_R7A_RESULTS.md")
    assert registry["source_combined_evidence"] == manifest["source_combined_evidence"]
    assert registry["promotion_status"] == "PROMOTED_FROM_OBL-COMBINED-006"
    assert manifest["promotion_experiment_ids"] == ["OBL-R7-KRANG-A"]

    assert current["control_id"] == control["evidence_id"] == diagnosis["control_id"]
    assert current["path"] == str(control_path.relative_to(ROOT))
    assert (
        current["sha256"]
        == sha(control_path)
        == analysis["control_evidence_sha256"]
        == diagnosis["control_sha256"]
    )
    assert current["git_blob_sha1"] == blob(control_path)
    assert current["analysis_git_blob_sha1"] == blob(analysis_path)
    assert current["diagnosis_git_blob_sha1"] == blob(diagnosis_path)
    assert registry["reference_evidence"] == {
        "path": str(report_path.relative_to(ROOT)),
        "git_blob_sha1": blob(report_path),
    }
    runtime = identity()["aggregate_semantic_runtime_sha256"]
    assert (
        runtime
        == registry["semantic_runtime_sha256"]
        == current["semantic_runtime_sha256"]
        == control["semantic_runtime_sha256"]
    )
    assert current["schedule_sha256"] == manifest["schedule_identity"] == control["schedule_sha256"]
    assert control["status"] == "COMPLETE" and len(control["games"]) == 4500
    assert len(control["cell_hashes"]) == 45 and len(control["replays"]) == 6
    assert control["runtime_errors"] == diagnosis["new_games"] == current["decks_changed"] == 0
    assert diagnosis["games_analyzed"] == 900 and diagnosis["candidate_authorized"] is False
    assert registry["environment_metrics"] == {
        key: analysis["new_global_metrics"][key] for key in old["environment_metrics"]
    }
    manifest_decks = {row["deck_key"]: row["sha256"] for row in manifest["decks"]}
    assert {row["deck_key"]: row["sha256"] for row in control["baseline_decks"]} == manifest_decks
    assert {row["deck_key"]: row["sha256"] for row in registry["decks"]} == manifest_decks
    for row in registry["decks"]:
        metric = analysis["new_per_deck"][row["deck_key"]]
        assert row["aggregate_baseline_win_rate"] == metric["win_rate"]
        assert row["mean_matchup_balance_error"] == metric["mean_matchup_balance_error"]
        assert (
            registry["per_deck_metrics"][row["deck_key"]]["matchup_win_rates"]
            == metric["matchup_win_rates"]
        )
    assert (
        registry["next_gate"]
        == ledger["next_gate"]
        == "ROUND_8_BEBOP_CORRECTED_CONTROL_DIAGNOSIS_INTERPRETATION"
    )
    assert "no Round 8 candidate" in (OBL / "ENVIRONMENT_REGISTRY.md").read_text(encoding="utf-8")
    print(
        "Baseline 004 current simulation reference: PASS; decks changed: 0; new diagnostic games: 0"
    )


if __name__ == "__main__":
    main()
