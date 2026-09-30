"""Create the authoritative OBL-BASELINE-001 promotion layer."""

# Generated governance Markdown keeps wide evidence tables and prose rows.
# ruff: noqa: E501

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
REGISTRY_PATH = OBL / "ENVIRONMENT_REGISTRY.json"
LEDGER_PATH = OBL / "EXPERIMENT_LEDGER.json"
COMBINED_MANIFEST_PATH = OBL / "combined/OBL_COMBINED_001_MANIFEST.json"
COMBINED_EVIDENCE_PATH = OBL / "COMBINED_001_EVIDENCE.json"
ROUND1_EVIDENCE_PATH = OBL / "ROUND_1_EVIDENCE.json"
BASELINE_MANIFEST_PATH = OBL / "baselines/OBL_BASELINE_001_MANIFEST.json"
REPOSITORY_SHA = "7d74d24226f904dfb85b3c4a9e57ab8f9de5500a"
PROMOTED = {
    "OBL-R1-LEONARDO-A",
    "OBL-R2-DONATELLO-A",
    "OBL-R2-BEBOP_ROCKSTEADY-B",
    "OBL-R2-CASEY_JONES-B",
}
RETAINED = {"raphael", "michelangelo", "splinter", "shredder", "krang", "april_oneil"}
DISPLAY = {
    "leonardo": "Leonardo",
    "raphael": "Raphael",
    "donatello": "Donatello",
    "michelangelo": "Michelangelo",
    "splinter": "Splinter",
    "shredder": "Shredder",
    "krang": "Krang",
    "bebop_rocksteady": "Bebop & Rocksteady",
    "april_oneil": "April O'Neil",
    "casey_jones": "Casey Jones",
}


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    return hashlib.sha256(subprocess.check_output(["git", "show", f"HEAD:{relative}"])).hexdigest()


def card_diff(record: dict) -> str:
    additions = ", ".join(f"+{count} {name}" for name, count in record["exact_additions"].items())
    removals = ", ".join(f"-{count} {name}" for name, count in record["exact_removals"].items())
    return "; ".join(part for part in (removals, additions) if part) or "None"


def write_markdown(registry: dict, ledger: dict, baseline_manifest: dict) -> None:
    evidence_ref = baseline_manifest["source_combined_evidence"]
    registry_lines = [
        "# Objective Balance Lab — Environment Registry",
        "",
        "This is the authoritative human-readable record of the current ten-deck environment. Experiments are cheap. Promotion is expensive.",
        "",
        "## Current environment",
        "",
        "- Environment ID: `OBL-BASELINE-001`",
        f"- Repository SHA: `{REPOSITORY_SHA}`",
        "- State: `BASELINE`",
        "- Lineage parent: `OBL-BASELINE-000` (`SUPERSEDED`)",
        "- Source combined environment: `OBL-COMBINED-001`",
        "- Next gate: **ROUND_3_EXPERIMENT_DESIGN**",
        "- Promotion basis: combined-environment evidence, not isolated win rate alone.",
        "",
        "## Official baselines",
        "",
        "| Deck | Official version | Source | SHA-256 | Current WR | Mean Matchup Balance Error | Candidate state | Identity | Semantic confidence | Promotion | Next question |",
        "|---|---|---|---|---:|---:|---|---|---|---|---|",
    ]
    for deck in registry["decks"]:
        registry_lines.append(
            f"| {deck['deck']} | `{deck['official_current_baseline_version']}` | `{deck['source_path']}` | `{deck['sha256']}` | {deck['aggregate_baseline_win_rate']:.2%} | {deck['mean_matchup_balance_error']:.2%} | {deck['candidate_status']} | {deck['identity_status']} | {deck['semantic_confidence_status']} | {deck['promotion_status']} | {deck['next_experimental_question']} |"
        )
    registry_lines += [
        "",
        "OBL-BASELINE-000 remains preserved as the superseded parent environment. OBL-COMBINED-001 remains preserved as the combined validation evidence. No rejected or inconclusive historical experiment was changed.",
        "",
        "The unresolved priorities are Raphael and Shredder overperformance, April and Krang underperformance, Leonardo weakness, Splinter above center, and Michelangelo's semantically difficult movement.",
        "",
    ]
    (OBL / "ENVIRONMENT_REGISTRY.md").write_text("\n".join(registry_lines), encoding="utf-8")

    ledger_lines = [
        "# Objective Balance Lab — Experiment Ledger",
        "",
        "This ledger preserves every isolated experiment. Four candidates are now `PROMOTED` only because they passed OBL-COMBINED-001 validation. All other records remain historical evidence.",
        "",
        "| Experiment ID | Round | Deck | Parent | Exact diff | Candidate WR | Parent WR | Balance Δ | Identity | Verdict | Promotion status | Evidence | Key lesson |",
        "|---|---|---|---|---|---:|---:|---:|---|---|---|---|---|",
    ]
    for record in ledger["experiments"]:
        metrics = record["result_metrics"]
        lesson = record.get("key_lesson", "See source evidence and combined validation records.")
        ledger_lines.append(
            f"| `{record['experiment_id']}` | {record['round']} | {record['deck']} | `{record['parent']['sha256'][:12]}…` | {card_diff(record)} | {metrics['candidate_win_rate']:.2%} | {metrics['parent_win_rate']:.2%} | {metrics['balance_delta'] * 100:+.2f} pp | {record.get('identity_classification', 'SEE EVIDENCE')} | {record['verdict']} | {record['promotion_status']} | `{record['source_evidence']['path']}` | {lesson} |"
        )
    ledger_lines += [
        "",
        "Promotion eligibility is not inferred from isolated results. The four promoted records cite `OBL-COMBINED-001`; Krang R2B and April R1A were not promoted because their combined validation was mixed or weakened.",
        "",
    ]
    (OBL / "EXPERIMENT_LEDGER.md").write_text("\n".join(ledger_lines), encoding="utf-8")

    history_path = OBL / "PROMOTION_HISTORY.md"
    history = history_path.read_text(encoding="utf-8")
    marker = "## Promotion OBL-PROMOTION-001"
    if marker not in history:
        history += "\n" + "\n".join(
            [
                marker,
                "",
                "- Prior environment: `OBL-BASELINE-000` (`SUPERSEDED`)",
                "- New environment: `OBL-BASELINE-001`",
                "- Source combined environment: `OBL-COMBINED-001`",
                "- Repository commit: `7d74d24226f904dfb85b3c4a9e57ab8f9de5500a`",
                "- Authorization: explicit Objective Balance Lab promotion request",
                "- Basis: combined-environment evidence, not isolated win rate alone",
                "- Promoted experiments: `OBL-R1-LEONARDO-A`, `OBL-R2-DONATELLO-A`, `OBL-R2-BEBOP_ROCKSTEADY-B`, `OBL-R2-CASEY_JONES-B`",
                "- Retained baseline decks: Raphael, Michelangelo, Splinter, Shredder, Krang, April O'Neil",
                "- Combined evidence: `docs/objective-balance-lab/COMBINED_001_EVIDENCE.json`",
                f"- Combined evidence SHA-256: `{evidence_ref['sha256']}`",
                "- Mean Matchup Balance Error: `20.96% → 19.33%` (`-1.62 pp`)",
                "- 70/30 matchups: `21 → 19`",
                "- Aggregate WR spread: `51.11% → 48.56%`",
                "- First-player rate: essentially neutral (`50.38% → 50.40%`)",
                "",
                "Krang R2B was not eligible because its isolated improvement reversed/mixed in the combined meta. April R1A weakened in the combined meta and was not eligible. No simulation was rerun and no legacy prototype file was overwritten.",
                "",
            ]
        )
        history_path.write_text(history, encoding="utf-8")
    elif "Combined evidence SHA-256" not in history:
        history = history.replace(
            "- Combined evidence: `docs/objective-balance-lab/COMBINED_001_EVIDENCE.json`",
            "- Combined evidence: `docs/objective-balance-lab/COMBINED_001_EVIDENCE.json`\n"
            f"- Combined evidence SHA-256: `{evidence_ref['sha256']}`",
        )
        history_path.write_text(history, encoding="utf-8")


def main() -> None:
    registry = read(REGISTRY_PATH)
    ledger = read(LEDGER_PATH)
    combined_manifest = read(COMBINED_MANIFEST_PATH)
    combined_evidence = read(COMBINED_EVIDENCE_PATH)
    round1_evidence = read(ROUND1_EVIDENCE_PATH)
    records = {record["experiment_id"]: record for record in ledger["experiments"]}
    if registry.get("environment_id") == "OBL-BASELINE-001":
        baseline_manifest = read(BASELINE_MANIFEST_PATH)
        baseline_manifest["source_combined_evidence"]["sha256"] = sha(COMBINED_EVIDENCE_PATH)
        for item in baseline_manifest["decks"]:
            if item["promotion_experiment_id"] in PROMOTED:
                item["sha256"] = records[item["promotion_experiment_id"]]["candidate"]["sha256"]
            else:
                item["source_path"] = round1_evidence["manifests"]["baseline"][item["deck_key"]][
                    "path"
                ]
                item["sha256"] = item["parent_baseline_sha256"]
                item["exact_diff"] = {"additions": {}, "removals": {}}
                item["source_kind"] = "retained_baseline"
            item["source_combined_evidence"]["sha256"] = sha(COMBINED_EVIDENCE_PATH)
        write(BASELINE_MANIFEST_PATH, baseline_manifest)
        for deck in registry["decks"]:
            manifest_deck = next(
                item for item in baseline_manifest["decks"] if item["deck_key"] == deck["deck_key"]
            )
            deck["source_path"] = manifest_deck["source_path"]
            deck["sha256"] = manifest_deck["sha256"]
        write(REGISTRY_PATH, registry)
        write_markdown(registry, ledger, baseline_manifest)
        return
    assert registry["environment_id"] == "OBL-BASELINE-000"
    assert combined_manifest["environment_id"] == "OBL-COMBINED-001"
    assert combined_evidence["environment_decision"] == "COMBINED_ENVIRONMENT_IMPROVED"

    selected = {item["deck_key"]: item for item in combined_manifest["selected_decks"]}
    validation = combined_evidence["per_deck_validation"]
    for experiment_id in PROMOTED:
        record = records[experiment_id]
        assert record["verdict"] == "ACCEPTED_FOR_COMBINED_MATRIX"
        deck_key = record["deck_key"]
        assert selected[deck_key]["experiment_id"] == experiment_id
        assert validation[deck_key]["verdict"] == "COMBINED_VALIDATION_PASSED"
        assert validation[deck_key]["promotion_eligibility"] == "PROMOTION_ELIGIBLE"

    evidence_ref = {
        "path": "docs/objective-balance-lab/COMBINED_001_EVIDENCE.json",
        "sha256": sha(COMBINED_EVIDENCE_PATH),
    }
    baseline_decks = []
    for item in combined_manifest["selected_decks"]:
        deck_key = item["deck_key"]
        source_path = ROOT / item["source_path"]
        experiment_id = item["experiment_id"]
        if experiment_id in PROMOTED:
            source_kind = "promoted_candidate"
            promotion_status = "PROMOTED"
            source_path = item["source_path"]
            source_sha = records[experiment_id]["candidate"]["sha256"]
            exact_diff = item["exact_diff"]
        else:
            source_kind = "retained_baseline"
            promotion_status = "BASELINE_RETAINED"
            source_path = round1_evidence["manifests"]["baseline"][deck_key]["path"]
            source_sha = item["parent_baseline_sha256"]
            exact_diff = {"additions": {}, "removals": {}}
        baseline_decks.append(
            {
                "deck": item["deck"],
                "deck_key": deck_key,
                "source_kind": source_kind,
                "source_path": source_path,
                "sha256": source_sha,
                "parent_environment_id": "OBL-BASELINE-000",
                "parent_baseline_sha256": item["parent_baseline_sha256"],
                "promotion_experiment_id": experiment_id if experiment_id in PROMOTED else None,
                "exact_diff": exact_diff,
                "source_combined_environment": "OBL-COMBINED-001",
                "source_combined_evidence": evidence_ref,
                "promotion_status": promotion_status,
            }
        )
    baseline_manifest = {
        "schema": "objective-balance-lab-official-baseline-v1",
        "environment_id": "OBL-BASELINE-001",
        "state": "BASELINE",
        "repository_sha": REPOSITORY_SHA,
        "lineage_parent_environment": "OBL-BASELINE-000",
        "source_combined_environment": "OBL-COMBINED-001",
        "source_combined_evidence": evidence_ref,
        "promotion_experiment_ids": sorted(PROMOTED),
        "retained_baseline_decks": sorted(RETAINED),
        "next_gate": "ROUND_3_EXPERIMENT_DESIGN",
        "decks": baseline_decks,
    }
    write(BASELINE_MANIFEST_PATH, baseline_manifest)

    combined_summary = combined_evidence["combined_summary"]
    updated_decks = []
    for old in registry["decks"]:
        item = next(entry for entry in baseline_decks if entry["deck_key"] == old["deck_key"])
        metrics = combined_summary[item["deck_key"]]
        experiment_id = item["promotion_experiment_id"]
        old["official_current_baseline_version"] = "OBL-BASELINE-001"
        old["source_path"] = item["source_path"]
        old["sha256"] = item["sha256"]
        old["aggregate_baseline_win_rate"] = metrics["win_rate"]
        old["mean_matchup_balance_error"] = metrics["mean_matchup_balance_error"]
        old["current_strongest_experimental_candidate"] = experiment_id
        old["candidate_status"] = (
            "PROMOTED" if experiment_id in PROMOTED else old["candidate_status"]
        )
        old["promotion_status"] = (
            f"PROMOTED: {experiment_id}"
            if experiment_id in PROMOTED
            else "BASELINE_RETAINED; no eligible candidate promoted"
        )
        old["next_experimental_question"] = {
            "raphael": "Reduce Casey Jones density without increasing Raphael's already-high power.",
            "michelangelo": "Find a semantically observable unconventional lever.",
            "splinter": "Find a semantically observable patient-control lever.",
            "shredder": "Reduce major overperformance with a distinguishable pressure or interaction change.",
            "krang": "Find an engine route toward center without adding matchup extremes; R2B was mixed.",
            "april_oneil": "Increase resourceful adaptability; R1 weakened in the combined meta.",
        }.get(item["deck_key"], old["next_experimental_question"])
        updated_decks.append(old)
    registry.update(
        {
            "environment_id": "OBL-BASELINE-001",
            "repository_sha": REPOSITORY_SHA,
            "status": "BASELINE",
            "promotion_status": "PROMOTED_FROM_OBL-BASELINE-000",
            "lineage_parent_environment": "OBL-BASELINE-000",
            "source_combined_environment": "OBL-COMBINED-001",
            "source_combined_evidence": evidence_ref,
            "next_gate": "ROUND_3_EXPERIMENT_DESIGN",
            "promotion_experiment_ids": sorted(PROMOTED),
            "decks": updated_decks,
            "superseded_environments": [
                {"environment_id": "OBL-BASELINE-000", "status": "SUPERSEDED"},
            ],
        }
    )
    write(REGISTRY_PATH, registry)

    for experiment_id in PROMOTED:
        record = records[experiment_id]
        record["promotion_status"] = "PROMOTED"
        record["verdict"] = "PROMOTED"
        record["promotion"] = {
            "promotion_id": "OBL-PROMOTION-001",
            "prior_environment": "OBL-BASELINE-000",
            "new_environment": "OBL-BASELINE-001",
            "source_combined_environment": "OBL-COMBINED-001",
            "combined_validation": "COMBINED_VALIDATION_PASSED",
            "combined_evidence": evidence_ref,
        }
    ledger.update(
        {
            "repository_sha": REPOSITORY_SHA,
            "environment_id": "OBL-BASELINE-001",
            "promotion_status": "OBL-PROMOTION-001",
            "next_gate": "ROUND_3_EXPERIMENT_DESIGN",
            "experiments": list(records.values()),
        }
    )
    write(LEDGER_PATH, ledger)
    write_markdown(registry, ledger, baseline_manifest)


if __name__ == "__main__":
    main()
