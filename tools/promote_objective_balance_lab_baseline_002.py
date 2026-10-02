"""Promote the combined-validated Raphael R4-C candidate to Baseline 002."""

# Governance Markdown is generated with intentionally wide evidence rows.
# ruff: noqa: E501

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
CURRENT = "1c9b70358ab663f6872bf6b9cf2e96f4cac80ce2"
RUNTIME = "78bcce5b5f635f11c67247df91f90fef2bf0dbf948973c5c1ac38419f28b0e25"
EXPERIMENT = "OBL-R4-RAPHAEL-C"
RAPHAEL_PATH = "docs/objective-balance-lab/baselines/RAPHAEL_OBL_BASELINE_002.txt"


def read(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def write(relative: str, value: object) -> None:
    path = ROOT / relative
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


def logical_sha(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_text(encoding="utf-8").encode("utf-8")).hexdigest()


def main() -> int:
    registry = read("docs/objective-balance-lab/ENVIRONMENT_REGISTRY.json")
    ledger = read("docs/objective-balance-lab/EXPERIMENT_LEDGER.json")
    old_manifest = read("docs/objective-balance-lab/baselines/OBL_BASELINE_001_MANIFEST.json")
    combined = read("docs/objective-balance-lab/COMBINED_003_RUNTIME_COMPATIBLE_EVIDENCE.json")
    identity = read("docs/objective-balance-lab/SEMANTIC_RUNTIME_IDENTITY.json")
    r4b = read("docs/objective-balance-lab/ROUND_4B_RAPHAEL_EVIDENCE.json")
    combined_path = "docs/objective-balance-lab/COMBINED_003_RUNTIME_COMPATIBLE_EVIDENCE.json"
    promotion_evidence_paths = [
        "docs/objective-balance-lab/ROUND_4B_RAPHAEL_EVIDENCE.json",
        "docs/objective-balance-lab/ROUND_4A_POST_SUPPORT_EVIDENCE.json",
        "docs/objective-balance-lab/BASELINE_001_RUNTIME_REFRESH_EVIDENCE.json",
        combined_path,
    ]
    candidate = r4b["candidate_manifests"][EXPERIMENT]
    promoted_sha = logical_sha(RAPHAEL_PATH)
    assert promoted_sha == candidate["candidate_sha256"]
    assert identity["current"]["aggregate_semantic_runtime_sha256"] == RUNTIME
    assert combined["semantic_runtime_sha256"] == RUNTIME
    metrics = combined["combined_global_metrics"]
    combined_sha = sha(combined_path)
    promotion_evidence = [{"path": path, "sha256": sha(path)} for path in promotion_evidence_paths]
    baseline002_decks = []
    for old in old_manifest["decks"]:
        item = dict(old)
        item["environment_id"] = "OBL-BASELINE-002"
        item["official_current_baseline_version"] = "OBL-BASELINE-002"
        item["parent_environment_id"] = "OBL-BASELINE-001"
        item["lineage_parent_environment"] = "OBL-BASELINE-001"
        item["source_combined_environment"] = "OBL-COMBINED-003"
        item["source_combined_evidence"] = {"path": combined_path, "sha256": combined_sha}
        item["promotion_status"] = (
            "PROMOTED" if old["deck_key"] == "raphael" else "BASELINE_RETAINED"
        )
        if old["deck_key"] == "raphael":
            item.update(
                {
                    "source_kind": "promoted_candidate",
                    "source_path": RAPHAEL_PATH,
                    "sha256": promoted_sha,
                    "parent_baseline_sha256": old["sha256"],
                    "promotion_experiment_id": EXPERIMENT,
                    "exact_diff": candidate["exact_diff"],
                    "promotion_authority": "OBL-COMBINED-003",
                }
            )
        else:
            item["promotion_experiment_id"] = None
        baseline002_decks.append(item)
    baseline002 = {
        "schema": "objective-balance-lab-official-baseline-v1",
        "environment_id": "OBL-BASELINE-002",
        "state": "OFFICIAL_BASELINE",
        "repository_sha": CURRENT,
        "semantic_runtime_sha256": RUNTIME,
        "lineage_parent_environment": "OBL-BASELINE-001",
        "source_combined_environment": "OBL-COMBINED-003",
        "source_combined_evidence": {"path": combined_path, "sha256": combined_sha},
        "promotion_evidence": promotion_evidence,
        "promotion_authority": "OBL-COMBINED-003",
        "promotion_experiment_ids": [EXPERIMENT],
        "retained_baseline_decks": [
            item["deck_key"] for item in baseline002_decks if item["deck_key"] != "raphael"
        ],
        "schedule_identity": combined["schedule_sha256"],
        "environment_metrics": metrics,
        "decks": baseline002_decks,
        "next_gate": "ROUND_5_EXPERIMENT_DESIGN",
    }
    baseline002_path = "docs/objective-balance-lab/baselines/OBL_BASELINE_002_MANIFEST.json"
    write(baseline002_path, baseline002)
    baseline002_sha = sha(baseline002_path)

    registry.update(
        {
            "environment_id": "OBL-BASELINE-002",
            "repository_sha": CURRENT,
            "status": "OFFICIAL_BASELINE",
            "promotion_status": "PROMOTED_FROM_OBL-COMBINED-003",
            "lineage_parent_environment": "OBL-BASELINE-001",
            "source_combined_environment": "OBL-COMBINED-003",
            "next_gate": "ROUND_5_EXPERIMENT_DESIGN",
            "semantic_runtime_sha256": RUNTIME,
            "source_combined_evidence": {"path": combined_path, "sha256": combined_sha},
            "reference_evidence": {"path": combined_path, "sha256": combined_sha},
            "environment_metrics": metrics,
            "promotion_evidence": promotion_evidence,
            "superseded_environments": [
                {"environment_id": "OBL-BASELINE-000", "status": "SUPERSEDED"},
                {"environment_id": "OBL-BASELINE-001", "status": "SUPERSEDED"},
            ],
        }
    )
    registry["decks"] = []
    for item in baseline002_decks:
        entry = next(
            entry
            for entry in read("docs/objective-balance-lab/ENVIRONMENT_REGISTRY.json")["decks"]
            if entry["deck_key"] == item["deck_key"]
        )
        entry.update(
            {
                "official_current_baseline_version": "OBL-BASELINE-002",
                "source_path": item["source_path"],
                "sha256": item["sha256"],
                "candidate_status": "PROMOTED"
                if item["deck_key"] == "raphael"
                else entry.get("candidate_status", "BASELINE_RETAINED"),
                "promotion_status": "PROMOTED: OBL-R4-RAPHAEL-C"
                if item["deck_key"] == "raphael"
                else "BASELINE_RETAINED",
                "aggregate_baseline_win_rate": combined["combined_deck_summary"][item["deck_key"]][
                    "win_rate"
                ],
                "mean_matchup_balance_error": combined["per_deck_comparison"][item["deck_key"]][
                    "combined"
                ]["mean_matchup_balance_error"],
            }
        )
        if item["deck_key"] == "raphael":
            lineage = entry.get("candidate_lineage", []) + [EXPERIMENT]
            entry["candidate_lineage"] = list(dict.fromkeys(lineage))
            entry["current_strongest_experimental_candidate"] = EXPERIMENT
            entry["next_experimental_question"] = (
                "Assess the remaining Raphael overperformance from Baseline 002."
            )
        registry["decks"].append(entry)
    write("docs/objective-balance-lab/ENVIRONMENT_REGISTRY.json", registry)

    record = next(item for item in ledger["experiments"] if item["experiment_id"] == EXPERIMENT)
    record.update(
        {
            "verdict": "PROMOTED",
            "promotion_status": "PROMOTED",
            "source_evidence": combined_path,
            "semantic_runtime_sha256": RUNTIME,
            "promotion": {
                "promotion_id": "OBL-PROMOTION-002",
                "prior_environment": "OBL-BASELINE-001",
                "new_environment": "OBL-BASELINE-002",
                "source_combined_environment": "OBL-COMBINED-003",
                "combined_validation": "COMBINED_VALIDATED",
                "combined_evidence": {"path": combined_path, "sha256": combined_sha},
                "promotion_evidence": promotion_evidence,
                "promotion_authority": "explicit Objective Balance Lab promotion request",
            },
        }
    )
    ledger["environment_id"] = "OBL-BASELINE-002"
    ledger["repository_sha"] = CURRENT
    ledger["promotion_status"] = "OBL-PROMOTION-002"
    ledger["next_gate"] = "ROUND_5_EXPERIMENT_DESIGN"
    write("docs/objective-balance-lab/EXPERIMENT_LEDGER.json", ledger)

    registry_lines = [
        "# Objective Balance Lab — Environment Registry",
        "",
        "Experiments are cheap. Promotion is expensive.",
        "",
        "## Current environment",
        "",
        "- Environment ID: `OBL-BASELINE-002`",
        f"- Repository SHA: `{CURRENT}`",
        "- State: `OFFICIAL_BASELINE`",
        "- Lineage: `OBL-BASELINE-001` → `OBL-COMBINED-003` → `OBL-BASELINE-002`",
        "- Semantic runtime: `" + RUNTIME + "`",
        "- Next gate: **ROUND_5_EXPERIMENT_DESIGN**",
        "",
        (
            "Official reference metrics come from the runtime-compatible `OBL-COMBINED-003` evidence: "
            f"mean matchup balance error **{metrics['mean_matchup_balance_error']:.4%}** "
            f"({metrics['mean_matchup_balance_error']:.2%} to two decimal places), "
            f"median deviation {metrics['median_matchup_deviation']:.0%}, "
            f"{metrics['over_60_40']} matchups over 60/40, {metrics['over_70_30']} over 70/30, "
            f"WR spread {metrics['aggregate_win_rate_spread']:.4%}, "
            f"first-player result rate {metrics['mean_first_player_result_rate']:.4%}, "
            f"mean ending turn {metrics['mean_ending_turn']}, and median ending turn "
            f"{metrics['median_ending_turn']:g}. The worst matchup is April O'Neil versus Raphael "
            "at 9/91. See [Baseline 002 metric audit](BASELINE_002_METRIC_AUDIT.md)."
        ),
        "",
        "| Deck | Version | Source | SHA-256 | WR | Balance error | Promotion |",
        "|---|---|---|---|---:|---:|---|",
    ]
    for item in baseline002_decks:
        s = combined["combined_deck_summary"][item["deck_key"]]
        e = combined["per_deck_comparison"][item["deck_key"]]["combined"][
            "mean_matchup_balance_error"
        ]
        promotion = (
            "PROMOTED: OBL-R4-RAPHAEL-C" if item["deck_key"] == "raphael" else "BASELINE_RETAINED"
        )
        registry_lines.append(
            f"| {item['deck']} | `OBL-BASELINE-002` | `{item['source_path']}` | `{item['sha256']}` | {s['win_rate']:.2%} | {e:.2%} | {promotion} |"
        )
    registry_lines += [
        "",
        "OBL-BASELINE-001 and all prior candidate/evidence artifacts remain preserved and immutable. No other deck was promoted.",
        "",
    ]
    (OBL / "ENVIRONMENT_REGISTRY.md").write_text("\n".join(registry_lines), encoding="utf-8")

    ledger_lines = [
        "# Objective Balance Lab — Experiment Ledger",
        "",
        "All Round 1–4B experiments remain permanent evidence. OBL-R4-RAPHAEL-C is now promoted only after runtime-compatible Combined 003 validation.",
        "",
        "| Experiment | Round | Deck | Parent | Candidate | Verdict | Promotion |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in ledger["experiments"]:
        parent = item.get("parent_deck_hash", item.get("parent", {}).get("sha256", ""))
        candidate_hash = item.get(
            "candidate_deck_hash", item.get("candidate", {}).get("sha256", "")
        )
        ledger_lines.append(
            f"| `{item['experiment_id']}` | {item['round']} | {item['deck']} | `{parent}` | `{candidate_hash}` | {item.get('verdict')} | {item.get('promotion_status')} |"
        )
    (OBL / "EXPERIMENT_LEDGER.md").write_text("\n".join(ledger_lines) + "\n", encoding="utf-8")

    history_path = OBL / "PROMOTION_HISTORY.md"
    history = history_path.read_text(encoding="utf-8")
    if "## Promotion OBL-PROMOTION-002" not in history:
        history += f"""\n## Promotion OBL-PROMOTION-002\n\n- Date: `{date.today().isoformat()}`\n- Prior environment: `OBL-BASELINE-001` (`SUPERSEDED`)\n- New environment: `OBL-BASELINE-002` (`OFFICIAL_BASELINE`)\n- Source combined environment: `OBL-COMBINED-003`\n- Deck: Raphael\n- Candidate: `{EXPERIMENT}`\n- Parent deck SHA-256: `{candidate["parent_sha256"]}`\n- Promoted deck SHA-256: `{promoted_sha}`\n- Exact diff: `-2 Casey Jones, Jury-Rig Justiciar; -1 Mutant Town Musicians; +2 Skateboard; +1 Spicy Oatmeal Pizza`\n- Combined evidence: `{combined_path}` (`{combined_sha}`)\n- Promotion evidence: Round 4B candidate, R4 utility semantic enablement, Baseline 001 runtime refresh, and runtime-compatible Combined 003 evidence.\n- Semantic runtime: `{RUNTIME}`\n- Combined verdict: `COMBINED_VALIDATED`; promotion eligibility: `PROMOTION_ELIGIBLE`\n- Reason: lower mean matchup balance error, fewer 60/40 matchups, improved worst matchup, persistent Raphael balance reduction, and strengthened identity. The aggregate WR-spread increase is recorded as an accepted tradeoff.\n- Simulations run: `0`\n- Authorization: explicit Objective Balance Lab promotion request\n\n"""
    history_path.write_text(history, encoding="utf-8")
    print(
        json.dumps(
            {
                "environment": "OBL-BASELINE-002",
                "promoted": EXPERIMENT,
                "promoted_sha": promoted_sha,
                "manifest_sha": baseline002_sha,
                "combined_evidence_sha": combined_sha,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
