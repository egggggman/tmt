"""Promote the Combined 005 Shredder/April subset without running games."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
SOURCE_REPOSITORY_SHA = "ed8848c51750d7b2343a35877857304d88371a5e"
PARENT_ID = "OBL-BASELINE-002"
COMBINED_ID = "OBL-COMBINED-005"
BASELINE_ID = "OBL-BASELINE-003"
PROMOTION_ID = "OBL-PROMOTION-003"
NEXT_GATE = "ROUND_6_EXPERIMENT_DESIGN"
COMBINED_PATH = "docs/objective-balance-lab/COMBINED_005_EVIDENCE.json"
COMBINED_MANIFEST_PATH = "docs/objective-balance-lab/combined/OBL_COMBINED_005_MANIFEST.json"
ROUND5_PATH = "docs/objective-balance-lab/ROUND_5_EVIDENCE.json"
BASELINE_PATH = "docs/objective-balance-lab/baselines/OBL_BASELINE_003_MANIFEST.json"
HISTORY_PATH = "docs/objective-balance-lab/PROMOTION_HISTORY.md"
PROMOTIONS = {
    "shredder": {
        "experiment_id": "OBL-R5-SHREDDER-B",
        "artifact": "docs/objective-balance-lab/baselines/SHREDDER_OBL_BASELINE_003.txt",
        "identity": "IDENTITY_PRESERVED",
    },
    "april_oneil": {
        "experiment_id": "OBL-R5-APRIL_ONEIL-A",
        "artifact": "docs/objective-balance-lab/baselines/APRIL_ONEIL_OBL_BASELINE_003.txt",
        "identity": "IDENTITY_STRENGTHENED",
        "aliases": ["OBL-R5-APRIL-A"],
    },
}


def read(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def write_json(relative: str, payload: dict) -> None:
    (ROOT / relative).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def git_bytes(relative: str) -> bytes:
    return subprocess.check_output(["git", "show", f"HEAD:{relative}"], cwd=ROOT)


def git_sha(relative: str) -> str:
    return hashlib.sha256(git_bytes(relative)).hexdigest()


def main() -> int:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    assert head == SOURCE_REPOSITORY_SHA
    old = read("docs/objective-balance-lab/baselines/OBL_BASELINE_002_MANIFEST.json")
    combined = read(COMBINED_PATH)
    combined_manifest = read(COMBINED_MANIFEST_PATH)
    round5 = read(ROUND5_PATH)
    registry = read("docs/objective-balance-lab/ENVIRONMENT_REGISTRY.json")
    ledger = read("docs/objective-balance-lab/EXPERIMENT_LEDGER.json")
    assert old["environment_id"] == registry["environment_id"] == PARENT_ID
    assert registry["status"] == "OFFICIAL_BASELINE"
    assert combined["environment_id"] == combined_manifest["environment_id"] == COMBINED_ID
    assert combined["parent_environment"] == combined_manifest["parent_environment"] == PARENT_ID
    assert combined["environment_decision"] == "COMBINED_ENVIRONMENT_IMPROVED"
    assert combined["logical_matchups"] == combined_manifest["logical_matchups"] == 45
    assert combined["logical_games"] == combined_manifest["logical_games"] == 4500
    assert combined["reused_games"] == combined_manifest["reused_games"] == 4500
    assert combined["newly_executed_games"] == combined_manifest["newly_executed_games"] == 0
    assert combined["runtime_errors"] == 0
    assert len(combined["provenance"]) == 45
    assert Counter(row["provenance"] for row in combined["provenance"]) == {
        "BASELINE_002_REUSED": 28,
        "ROUND_5_REUSED": 16,
        "COMBINED_004_REUSED": 1,
    }
    assert len(combined["combined_games"]) == 4500
    assert (
        old["semantic_runtime_sha256"]
        == combined["semantic_runtime_sha256"]
        == combined_manifest["semantic_runtime_sha256"]
    )
    assert old["schedule_identity"] == combined["schedule_sha256"]
    assert combined["recommended_promotion_subset"] == [
        row["experiment_id"] for row in PROMOTIONS.values()
    ]
    assert combined["combined_005_global_metrics"]["worst_matchup"]["win_rates"] == {
        "krang": 0.12,
        "shredder": 0.88,
    }
    old_decks = {row["deck_key"]: row for row in old["decks"]}
    selected_decks = {row["deck_key"]: row for row in combined_manifest["decks"]}
    assert len(old_decks) == len(selected_decks) == 10
    assert set(combined_manifest["selected_experiments"]) == {
        row["experiment_id"] for row in PROMOTIONS.values()
    }

    for deck, promotion in PROMOTIONS.items():
        experiment_id = promotion["experiment_id"]
        decision = combined["candidate_decisions"][experiment_id]
        assert decision["combined_verdict"] == "COMBINED_VALIDATION_PASSED"
        assert decision["promotion_eligibility"] == "PROMOTION_ELIGIBLE"
        isolated = round5["candidate_manifests"][experiment_id]
        record = next(x for x in ledger["experiments"] if x["experiment_id"] == experiment_id)
        assert record["identity_classification"] == promotion["identity"]
        assert record["promotion_status"] == "EXPERIMENTAL"
        assert isolated["parent_sha256"] == old_decks[deck]["sha256"]
        assert isolated["candidate_sha256"] == selected_decks[deck]["sha256"]
        assert isolated["candidate_path"] == selected_decks[deck]["source_path"]
        candidate_bytes = git_bytes(isolated["candidate_path"])
        assert hashlib.sha256(candidate_bytes).hexdigest() == isolated["candidate_sha256"]
        artifact_path = ROOT / promotion["artifact"]
        assert not artifact_path.exists(), (
            f"Preserved promoted artifact already exists: {artifact_path}"
        )
        artifact_path.write_bytes(candidate_bytes)
        assert artifact_path.read_bytes() == candidate_bytes

    for deck, selected in selected_decks.items():
        if deck not in PROMOTIONS:
            assert selected["sha256"] == old_decks[deck]["sha256"]
            assert selected["source_path"] == old_decks[deck]["source_path"]
            assert selected["exact_diff"] == {"removals": {}, "additions": {}}

    authority_ref = {"path": COMBINED_PATH, "sha256": git_sha(COMBINED_PATH)}
    round5_ref = {"path": ROUND5_PATH, "sha256": git_sha(ROUND5_PATH)}
    combined_manifest_ref = {
        "path": COMBINED_MANIFEST_PATH,
        "sha256": git_sha(COMBINED_MANIFEST_PATH),
    }
    fingerprint_digest = hashlib.sha256(
        json.dumps(
            sorted(
                (
                    {"decks": row["decks"], "fingerprint": row["matchup_fingerprint"]}
                    for row in combined["provenance"]
                ),
                key=lambda row: row["decks"],
            ),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    deck_rows = []
    for previous in old["decks"]:
        deck = previous["deck_key"]
        item = dict(previous)
        item["environment_id"] = BASELINE_ID
        item["official_current_baseline_version"] = BASELINE_ID
        item["parent_environment_id"] = PARENT_ID
        item["lineage_parent_environment"] = PARENT_ID
        item["parent_baseline_sha256"] = previous["sha256"]
        item["inherited_promotion_experiment_id"] = previous.get("promotion_experiment_id")
        item["promotion_experiment_id"] = None
        item["promotion_status"] = "BASELINE_RETAINED"
        item["source_combined_environment"] = COMBINED_ID
        item["source_combined_evidence"] = authority_ref
        item["exact_diff"] = {"removals": {}, "additions": {}}
        if deck in PROMOTIONS:
            promotion = PROMOTIONS[deck]
            experiment_id = promotion["experiment_id"]
            selected = selected_decks[deck]
            item.update(
                {
                    "source_kind": "promoted_candidate",
                    "source_path": promotion["artifact"],
                    "sha256": selected["sha256"],
                    "promotion_experiment_id": experiment_id,
                    "promotion_status": "PROMOTED",
                    "promotion_authority": COMBINED_ID,
                    "promotion_aliases": promotion.get("aliases", []),
                    "exact_diff": selected["exact_diff"],
                }
            )
        deck_rows.append(item)

    metrics = combined["combined_005_global_metrics"]
    per_deck_metrics = {
        deck: combined["per_deck_comparison"][deck]["combined_005"] for deck in old_decks
    }
    baseline003 = {
        "schema": "objective-balance-lab-official-baseline-v1",
        "environment_id": BASELINE_ID,
        "state": "OFFICIAL_BASELINE",
        "repository_sha": SOURCE_REPOSITORY_SHA,
        "semantic_runtime_sha256": old["semantic_runtime_sha256"],
        "lineage_parent_environment": PARENT_ID,
        "source_combined_environment": COMBINED_ID,
        "source_combined_state": "COMBINED_VALIDATED",
        "source_combined_evidence": authority_ref,
        "source_combined_manifest": combined_manifest_ref,
        "promotion_evidence": [round5_ref, authority_ref],
        "promotion_authority": COMBINED_ID,
        "promotion_id": PROMOTION_ID,
        "promotion_experiment_ids": [row["experiment_id"] for row in PROMOTIONS.values()],
        "retained_baseline_decks": [
            row["deck_key"] for row in deck_rows if row["deck_key"] not in PROMOTIONS
        ],
        "schedule_identity": combined["schedule_sha256"],
        "matchup_fingerprint_digest_sha256": fingerprint_digest,
        "environment_metrics": metrics,
        "per_deck_metrics": per_deck_metrics,
        "per_deck_win_rates": {
            deck: combined["combined_005_deck_summary"][deck]["win_rate"] for deck in old_decks
        },
        "decks": deck_rows,
        "next_gate": NEXT_GATE,
        "carried_forward_risk": (
            "Krang vs Shredder: 12/88; priority diagnostic for the next experimental round."
        ),
    }
    write_json(BASELINE_PATH, baseline003)
    manifest_sha = hashlib.sha256(
        (ROOT / BASELINE_PATH).read_bytes().replace(b"\r\n", b"\n")
    ).hexdigest()

    registry.update(
        {
            "environment_id": BASELINE_ID,
            "current_baseline_manifest": {"path": BASELINE_PATH, "sha256": manifest_sha},
            "repository_sha": SOURCE_REPOSITORY_SHA,
            "status": "OFFICIAL_BASELINE",
            "promotion_status": f"PROMOTED_FROM_{COMBINED_ID}",
            "lineage_parent_environment": PARENT_ID,
            "source_combined_environment": COMBINED_ID,
            "source_combined_state": "COMBINED_VALIDATED",
            "source_combined_evidence": authority_ref,
            "reference_evidence": authority_ref,
            "promotion_evidence": [round5_ref, authority_ref],
            "semantic_runtime_sha256": old["semantic_runtime_sha256"],
            "schedule_identity": combined["schedule_sha256"],
            "environment_metrics": metrics,
            "per_deck_metrics": per_deck_metrics,
            "next_gate": NEXT_GATE,
            "carried_forward_risk": baseline003["carried_forward_risk"],
            "superseded_environments": [
                *registry["superseded_environments"],
                {"environment_id": PARENT_ID, "status": "SUPERSEDED"},
            ],
        }
    )
    for entry in registry["decks"]:
        deck = entry["deck_key"]
        baseline_row = next(row for row in deck_rows if row["deck_key"] == deck)
        entry.update(
            {
                "official_current_baseline_version": BASELINE_ID,
                "source_path": baseline_row["source_path"],
                "sha256": baseline_row["sha256"],
                "aggregate_baseline_win_rate": baseline003["per_deck_win_rates"][deck],
                "mean_matchup_balance_error": per_deck_metrics[deck]["mean_matchup_balance_error"],
                "promotion_status": (
                    f"PROMOTED: {PROMOTIONS[deck]['experiment_id']}"
                    if deck in PROMOTIONS
                    else "BASELINE_RETAINED"
                ),
            }
        )
        if deck in PROMOTIONS:
            experiment_id = PROMOTIONS[deck]["experiment_id"]
            entry["candidate_lineage"] = list(
                dict.fromkeys([*entry["candidate_lineage"], experiment_id])
            )
            entry["current_strongest_experimental_candidate"] = experiment_id
            entry["candidate_status"] = "PROMOTED"
        if deck == "shredder":
            entry["next_experimental_question"] = (
                "Diagnose the residual 88/12 Shredder advantage against Krang "
                "without repeating prior shell swaps."
            )
        elif deck == "krang":
            entry["next_experimental_question"] = (
                "Diagnose the 12/88 Shredder matchup under Baseline 003; "
                "Krang B was not eligible in Combined 004."
            )
        elif deck == "april_oneil":
            entry["next_experimental_question"] = (
                "Find further proactive, resourceful improvement; April remains "
                "below center despite promotion."
            )
    write_json("docs/objective-balance-lab/ENVIRONMENT_REGISTRY.json", registry)

    for deck, promotion in PROMOTIONS.items():
        experiment_id = promotion["experiment_id"]
        record = next(row for row in ledger["experiments"] if row["experiment_id"] == experiment_id)
        record["verdict"] = "PROMOTED"
        record["promotion_status"] = "PROMOTED"
        record["combined_validation"] = "COMBINED_VALIDATED"
        record["promotion"] = {
            "promotion_id": PROMOTION_ID,
            "promotion_record_id": f"{PROMOTION_ID}-{deck.upper()}",
            "prior_environment": PARENT_ID,
            "new_environment": BASELINE_ID,
            "source_combined_environment": COMBINED_ID,
            "combined_evidence": authority_ref,
            "combined_validation": "COMBINED_VALIDATED",
            "combined_verdict": "COMBINED_VALIDATION_PASSED",
            "promotion_eligibility": "PROMOTION_ELIGIBLE",
            "identity_classification": promotion["identity"],
            "promoted_artifact": promotion["artifact"],
            "aliases": promotion.get("aliases", []),
            "authorization": "explicit Objective Balance Lab promotion request",
        }
        if promotion.get("aliases"):
            record["aliases"] = promotion["aliases"]
    ledger["environment_id"] = BASELINE_ID
    ledger["repository_sha"] = SOURCE_REPOSITORY_SHA
    ledger["promotion_status"] = PROMOTION_ID
    ledger["combined_validation_state"] = {COMBINED_ID: "COMBINED_VALIDATED"}
    ledger["next_gate"] = NEXT_GATE
    write_json("docs/objective-balance-lab/EXPERIMENT_LEDGER.json", ledger)

    registry_lines = [
        "# Objective Balance Lab — Environment Registry",
        "",
        "Experiments are cheap. Promotion is expensive.",
        "",
        "## Current environment",
        "",
        f"- Environment ID: `{BASELINE_ID}`",
        f"- Repository SHA: `{SOURCE_REPOSITORY_SHA}`",
        "- State: `OFFICIAL_BASELINE`",
        f"- Lineage: `{PARENT_ID}` → `{COMBINED_ID}` → `{BASELINE_ID}`",
        f"- Semantic runtime: `{old['semantic_runtime_sha256']}`",
        f"- Next gate: **{NEXT_GATE}**",
        "",
        "Baseline 002 is now `SUPERSEDED`, not deleted. Combined 005 is `COMBINED_VALIDATED` "
        "as promotion authority; its historical evidence remains unchanged.",
        "",
        f"Exact reference metrics are copied from [Combined 005](COMBINED_005_EVIDENCE.json): "
        f"mean balance error {metrics['mean_matchup_balance_error']:.4%}, "
        f"median deviation {metrics['median_matchup_deviation']:.0%}, "
        f">60/40 {metrics['over_60_40']}, >70/30 {metrics['over_70_30']}, "
        f"WR spread {metrics['aggregate_win_rate_spread']:.4%}, WR standard deviation "
        f"{metrics['aggregate_win_rate_stddev']:.4%}, first-player rate "
        f"{metrics['mean_first_player_result_rate']:.4%}, mean turn "
        f"{metrics['mean_ending_turn']}, median turn {metrics['median_ending_turn']:g}.",
        "",
        "**Carried-forward risk:** Krang loses 12/88 to Shredder, the environment's "
        "worst matchup. This is a priority diagnostic, not a deck change in this promotion.",
        "",
        "| Deck | Version | Source | SHA-256 | WR | Balance error | Promotion |",
        "|---|---|---|---|---:|---:|---|",
    ]
    for row in deck_rows:
        deck = row["deck_key"]
        registry_lines.append(
            f"| {row['deck']} | `{BASELINE_ID}` | `{row['source_path']}` | `{row['sha256']}` "
            f"| {baseline003['per_deck_win_rates'][deck]:.2%} "
            f"| {per_deck_metrics[deck]['mean_matchup_balance_error']:.2%} "
            f"| {row['promotion_status']} |"
        )
    registry_lines += [
        "",
        "All older baselines, candidate files, raw evidence, and "
        "rejected/inconclusive verdicts are preserved.",
        "",
    ]
    (OBL / "ENVIRONMENT_REGISTRY.md").write_text("\n".join(registry_lines), encoding="utf-8")

    ledger_lines = [
        "# Objective Balance Lab — Experiment Ledger",
        "",
        "Historical isolated evidence and verdicts remain traceable. Only Shredder B and April A "
        "were promoted after [Combined 005](COMBINED_005_RESULTS.md) validation; "
        "`OBL-R5-APRIL-A` remains an alias of `OBL-R5-APRIL_ONEIL-A`.",
        "",
        "| Experiment | Round | Deck | Parent | Candidate | Verdict | Promotion |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in ledger["experiments"]:
        parent = row.get("parent_deck_hash", row.get("parent", {}).get("sha256", ""))
        candidate = row.get("candidate_deck_hash", row.get("candidate", {}).get("sha256", ""))
        ledger_lines.append(
            f"| `{row['experiment_id']}` | {row['round']} | {row['deck']} | `{parent}` "
            f"| `{candidate}` | {row.get('verdict')} | {row.get('promotion_status')} |"
        )
    ledger_lines += ["", "Round 5 isolated source: [evidence](ROUND_5_EVIDENCE.json).", ""]
    (OBL / "EXPERIMENT_LEDGER.md").write_text("\n".join(ledger_lines), encoding="utf-8")

    history_path = ROOT / HISTORY_PATH
    history_before = history_path.read_text(encoding="utf-8")
    assert "## Promotion OBL-PROMOTION-003" not in history_before
    global_before = old["environment_metrics"]
    header = [
        f"## Promotion {PROMOTION_ID}",
        "",
        f"- Date: `{date.today().isoformat()}`; source repository commit: "
        f"`{SOURCE_REPOSITORY_SHA}`",
        f"- Prior environment: `{PARENT_ID}` (`SUPERSEDED`)",
        f"- New environment: `{BASELINE_ID}` (`OFFICIAL_BASELINE`)",
        f"- Lineage: `{PARENT_ID}` → `{COMBINED_ID}` (`COMBINED_VALIDATED`) → `{BASELINE_ID}`",
        f"- Combined evidence: `{COMBINED_PATH}` (`{authority_ref['sha256']}`)",
        f"- Semantic runtime: `{old['semantic_runtime_sha256']}`",
        f"- Mean matchup balance error: {global_before['mean_matchup_balance_error']:.4%} → "
        f"{metrics['mean_matchup_balance_error']:.4%}",
        f"- >60/40 matchups: {global_before['over_60_40']} → {metrics['over_60_40']}; "
        f">70/30: {global_before['over_70_30']} → {metrics['over_70_30']}",
        f"- WR spread: {global_before['aggregate_win_rate_spread']:.4%} → "
        f"{metrics['aggregate_win_rate_spread']:.4%}",
        "- Both isolated candidate effects persisted or strengthened under Combined 005; "
        "promotion is based on the combined ten-deck environment, not isolated WR alone.",
        "- Carried-forward risk: **Krang vs Shredder 12/88**, the worst matchup; "
        "priority diagnostic for the next round.",
        "- New simulations: `0`; new logical games: `0`",
        "- Authorization: explicit Objective Balance Lab promotion request",
        "",
    ]
    for deck, promotion in PROMOTIONS.items():
        experiment_id = promotion["experiment_id"]
        record = next(row for row in ledger["experiments"] if row["experiment_id"] == experiment_id)
        diff = "; ".join(
            [f"-{count} {name}" for name, count in record["exact_removals"].items()]
            + [f"+{count} {name}" for name, count in record["exact_additions"].items()]
        )
        header += [
            f"### {record['deck']} — {PROMOTION_ID}-{deck.upper()}",
            "",
            f"- Candidate: `{experiment_id}`"
            + (f" (alias `{promotion['aliases'][0]}`)" if promotion.get("aliases") else ""),
            f"- Parent baseline: `{PARENT_ID}`; new baseline: `{BASELINE_ID}`",
            f"- Parent deck SHA-256: `{record['parent']['sha256']}`",
            f"- Promoted deck SHA-256: `{record['candidate']['sha256']}`",
            f"- Exact diff: `{diff}`",
            f"- Combined authority: `{COMBINED_ID}`; evidence `{COMBINED_PATH}`",
            f"- Semantic runtime: `{old['semantic_runtime_sha256']}`",
            f"- Identity: `{promotion['identity']}`",
            "- Combined result: `COMBINED_VALIDATION_PASSED`; "
            "eligibility: `PROMOTION_ELIGIBLE`; state: `PROMOTED`",
            "",
        ]
    history_path.write_text(history_before + "\n" + "\n".join(header), encoding="utf-8")
    print(
        json.dumps(
            {
                "environment": BASELINE_ID,
                "promoted": [row["experiment_id"] for row in PROMOTIONS.values()],
                "manifest_sha256": manifest_sha,
                "semantic_runtime_sha256": old["semantic_runtime_sha256"],
                "new_simulations": 0,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
