"""Point the Baseline 004 registry at its validated current-runtime control.

Combined 006 and the original Baseline 004 manifest remain immutable promotion
history. This updates simulation-reference metadata only, with no deck changes.
"""

# Complete registry Markdown rows are retained as literals.
# ruff: noqa: E501

from __future__ import annotations

import gzip
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
REGISTRY = OBL / "ENVIRONMENT_REGISTRY.json"
REGISTRY_MD = OBL / "ENVIRONMENT_REGISTRY.md"
LEDGER = OBL / "EXPERIMENT_LEDGER.json"
MANIFEST = OBL / "baselines/OBL_BASELINE_004_MANIFEST.json"
CONTROL = OBL / "BASELINE_004_CYCLING_PILOT_CONTROL.json.gz"
REPORT = OBL / "BASELINE_004_CYCLING_PILOT_CONTROL.md"
ANALYSIS = OBL / "BASELINE_004_CYCLING_PILOT_ANALYSIS.json"
DIAGNOSIS = OBL / "ROUND_8_BEBOP_CORRECTED_CONTROL_DIAGNOSTIC.json"
GATE = "ROUND_8_BEBOP_CORRECTED_CONTROL_DIAGNOSIS_INTERPRETATION"


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blob(path: Path) -> str:
    return subprocess.check_output(
        ["git", "hash-object", str(path.relative_to(ROOT))], cwd=ROOT, text=True
    ).strip()


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def main() -> None:
    registry = read(REGISTRY)
    ledger = read(LEDGER)
    manifest = read(MANIFEST)
    analysis = read(ANALYSIS)
    diagnosis = read(DIAGNOSIS)
    control = json.loads(gzip.decompress(CONTROL.read_bytes()))
    assert (
        registry["environment_id"]
        == ledger["environment_id"]
        == manifest["environment_id"]
        == "OBL-BASELINE-004"
    )
    assert manifest["semantic_runtime_sha256"] == analysis["prior_semantic_runtime_sha256"]
    assert registry["source_combined_evidence"] == manifest["source_combined_evidence"]
    assert analysis["control_evidence_sha256"] == diagnosis["control_sha256"] == sha(CONTROL)
    assert (
        analysis["new_semantic_runtime_sha256"]
        == diagnosis["semantic_runtime_sha256"]
        == control["semantic_runtime_sha256"]
    )
    assert (
        analysis["schedule_sha256"] == manifest["schedule_identity"] == control["schedule_sha256"]
    )
    assert control["status"] == "COMPLETE" and len(control["games"]) == 4500
    assert len(control["cell_hashes"]) == 45 and len(control["replays"]) == 6
    assert diagnosis["games_analyzed"] == 900 and diagnosis["new_games"] == 0
    assert {row["deck_key"]: row["sha256"] for row in registry["decks"]} == {
        row["deck_key"]: row["sha256"] for row in manifest["decks"]
    }
    assert "original_promotion_reference" not in registry, "refuse to overwrite promotion snapshot"
    registry["original_promotion_reference"] = {
        "semantic_runtime_sha256": registry["semantic_runtime_sha256"],
        "reference_evidence": registry["reference_evidence"],
        "environment_metrics": registry["environment_metrics"],
        "per_deck_metrics": registry["per_deck_metrics"],
        "next_gate": registry["next_gate"],
    }
    registry["semantic_runtime_sha256"] = control["semantic_runtime_sha256"]
    registry["reference_evidence"] = {"path": relative(REPORT), "git_blob_sha1": blob(REPORT)}
    registry["current_simulation_control"] = {
        "control_id": control["evidence_id"],
        "path": relative(CONTROL),
        "git_blob_sha1": blob(CONTROL),
        "sha256": sha(CONTROL),
        "analysis_path": relative(ANALYSIS),
        "analysis_git_blob_sha1": blob(ANALYSIS),
        "diagnosis_path": relative(DIAGNOSIS),
        "diagnosis_git_blob_sha1": blob(DIAGNOSIS),
        "semantic_runtime_sha256": control["semantic_runtime_sha256"],
        "schedule_sha256": control["schedule_sha256"],
        "games": 4500,
        "matchups": 45,
        "deterministic_replay_samples": 6,
        "decks_changed": 0,
    }
    keys = registry["environment_metrics"]
    registry["environment_metrics"] = {key: analysis["new_global_metrics"][key] for key in keys}
    for deck in registry["decks"]:
        key = deck["deck_key"]
        measured = analysis["new_per_deck"][key]
        deck["aggregate_baseline_win_rate"] = measured["win_rate"]
        deck["mean_matchup_balance_error"] = measured["mean_matchup_balance_error"]
    registry["per_deck_metrics"] = {}
    for key, measured in analysis["new_per_deck"].items():
        extreme = max(
            measured["matchup_win_rates"],
            key=lambda opponent: abs(measured["matchup_win_rates"][opponent] - 0.5),
        )
        registry["per_deck_metrics"][key] = {
            **measured,
            "most_extreme_matchup": {
                "opponent": extreme,
                "win_rate": measured["matchup_win_rates"][extreme],
            },
        }
    registry["carried_forward_risk"] = (
        "Bebop & Rocksteady remains the lowest aggregate deck at 23.33% in the "
        "corrected 4,500-game control; Raphael and Shredder remain strong at "
        "69.78% and 69.44%. Round 8 diagnosis is pending Design Studio interpretation."
    )
    registry["next_gate"] = ledger["next_gate"] = GATE
    REGISTRY.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    LEDGER.write_text(json.dumps(ledger, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    metrics = registry["environment_metrics"]
    lines = [
        "# Objective Balance Lab — Environment Registry",
        "",
        "Experiments are cheap. Promotion is expensive.",
        "",
        "## Current environment",
        "",
        "- Environment ID: `OBL-BASELINE-004`",
        "- State: `OFFICIAL_BASELINE`; the ten deck lists and their hashes are unchanged.",
        "- Lineage: `OBL-BASELINE-003` → `OBL-COMBINED-006` → `OBL-BASELINE-004`",
        f"- Current simulation runtime: `{registry['semantic_runtime_sha256']}`",
        f"- Current control: `{control['evidence_id']}` — [4,500-game evidence](BASELINE_004_CYCLING_PILOT_CONTROL.json.gz), [45-cell results](BASELINE_004_CYCLING_PILOT_CONTROL.md).",
        f"- Founding promotion: `OBL-PROMOTION-004`; Combined 006 and the [original Baseline 004 manifest](baselines/OBL_BASELINE_004_MANIFEST.json) remain historical and unchanged under runtime `{manifest['semantic_runtime_sha256']}`.",
        "- Deck changed in founding promotion: Krang only. Decks changed by this control refresh: **zero**.",
        f"- Next gate: `{GATE}`. [B&R corrected-control diagnosis](ROUND_8_BEBOP_CORRECTED_CONTROL_DIAGNOSTIC.md) is read-only; no Round 8 candidate is authorized.",
        "",
        f"Current control metrics: mean matchup balance error **{metrics['mean_matchup_balance_error']:.2%}**, median deviation **{metrics['median_matchup_deviation']:.0%}**, >60/40 **{metrics['over_60_40']}**, >70/30 **{metrics['over_70_30']}**, WR spread **{metrics['aggregate_win_rate_spread']:.2%}**, WR standard deviation **{metrics['aggregate_win_rate_stddev']:.2%}**.",
        "",
        "| Deck | Version | Source | SHA-256 | Current WR | Current balance error | Promotion |",
        "|---|---|---|---|---:|---:|---|",
    ]
    for deck in registry["decks"]:
        lines.append(
            f"| {deck['deck']} | `{deck['official_current_baseline_version']}` | `{deck['source_path']}` | `{deck['sha256']}` | {deck['aggregate_baseline_win_rate']:.2%} | {deck['mean_matchup_balance_error']:.2%} | {deck['promotion_status']} |"
        )
    lines += [
        "",
        "The original Combined 006 metrics remain in the immutable Baseline 004 promotion manifest and in `original_promotion_reference` in the machine registry. All older baselines, prototypes, candidates, controls, and raw evidence remain preserved.",
        "",
    ]
    REGISTRY_MD.write_text("\n".join(lines), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "BASELINE_004_CURRENT_SIMULATION_REFERENCE_REFRESHED",
                "control": control["evidence_id"],
                "decks_changed": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
