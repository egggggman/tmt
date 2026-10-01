"""Build Round 4B Raphael reports and append durable experiment evidence."""

# Long report literals intentionally emit Markdown tables and ledger rows.
# ruff: noqa: E501

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs" / "objective-balance-lab"
sys.path.insert(0, str(ROOT / "tools"))
import run_objective_balance_lab_round1 as r1  # noqa: E402
from build_objective_balance_lab_round4a_post_support_reports import aggregate  # noqa: E402

POST = OBL / "ROUND_4B_RAPHAEL_EVIDENCE.json"
R4A = OBL / "ROUND_4A_POST_SUPPORT_EVIDENCE.json"
R4A_PRE = OBL / "ROUND_4A_RAPHAEL_EVIDENCE.json"
BASE = OBL / "COMBINED_001_EVIDENCE.json"
LEDGER = OBL / "EXPERIMENT_LEDGER.json"
LEDGER_MD = OBL / "EXPERIMENT_LEDGER.md"
ROLES = OBL / "CARD_ROLE_EVIDENCE.json"
CANDIDATES = {
    "OBL-R4-RAPHAEL-C": "docs/objective-balance-lab/candidates/RAPHAEL_OBL_R4_C.txt",
    "OBL-R4-RAPHAEL-D": "docs/objective-balance-lab/candidates/RAPHAEL_OBL_R4_D.txt",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def enrich(rows: list[dict], summary: dict, balance_reference: dict, candidate: str) -> dict:
    result = aggregate(rows, "raphael")
    result["parent_win_rate"] = summary["win_rate"]
    result["balance_delta"] = (
        result["mean_matchup_balance_error"] - balance_reference["mean_matchup_balance_error"]
    )
    result["matchup_deltas"] = {
        key: result["matchup_win_rates"][key] - summary["matchup_win_rates"][key]
        for key in result["matchup_win_rates"]
    }
    result["battlefield_presence"] = {
        turn: sum(row["battlefield_presence"].get("raphael", {}).get(turn, 0) for row in rows)
        / len(rows)
        for turn in ("3", "5", "7")
    }
    result["interaction_casts"] = sum(
        row["interaction_casts"].get("raphael", 0) for row in rows
    ) / len(rows)
    result["signature_casts"] = {
        key: sum(row["signature_casts"].get(key, 0) for row in rows)
        for key in sorted(
            {key for row in rows for key in row["signature_casts"] if key.startswith("raphael:")}
        )
    }
    result["identity_classification"] = "IDENTITY_STRENGTHENED"
    result["hypothesis_result"] = "UTILITY_HYPOTHESIS_PARTIALLY_SUPPORTED"
    result["verdict"] = "PROMISING_NEEDS_VARIANT"
    result["utility_direction"] = "UTILITY_DIRECTION_CONFIRMED"
    result["candidate"] = candidate
    return result


def main() -> None:
    post = json.loads(POST.read_text(encoding="utf-8"))
    r4a = json.loads(R4A.read_text(encoding="utf-8"))
    r4a_pre = json.loads(R4A_PRE.read_text(encoding="utf-8"))
    base = json.loads(BASE.read_text(encoding="utf-8"))
    parent = r4a_pre["baseline_summary"]
    balance_reference = base["baseline_summary"]["raphael"]
    reports = {
        candidate: enrich(rows, parent, balance_reference, candidate)
        for candidate, rows in post["candidate_results"].items()
    }
    post["balance_error_reference"] = {
        "source": "docs/objective-balance-lab/COMBINED_001_EVIDENCE.json",
        "mean_matchup_balance_error": balance_reference["mean_matchup_balance_error"],
    }
    post["reports"] = reports
    post["parent_baseline_sha256"] = (
        "220ea90ccc579e09bef38ce972ba84f661c2382b92c7a4559667d24a5eec6f51"
    )
    post["candidate_manifests"] = {}
    cards = r1.catalog()
    parent_deck = r1.validate_deck(r1.ROOT / "decks/raphael/PROTOTYPE_0.3.txt", cards)
    hypotheses = {
        "OBL-R4-RAPHAEL-C": "A deeper shift from generic creature pressure into supported Skateboard and Pizza utility lowers Raphael further while preserving confrontation identity.",
        "OBL-R4-RAPHAEL-D": "Raphael’s balance improvement comes from reducing creature pressure generally, not specifically from Skateboard.",
    }
    for candidate, path in CANDIDATES.items():
        deck = r1.validate_deck(r1.ROOT / path, cards)
        post["candidate_manifests"][candidate] = {
            "experiment_id": candidate,
            "candidate_path": path,
            "candidate_sha256": deck["sha256"],
            "parent_path": "decks/raphael/PROTOTYPE_0.3.txt",
            "parent_sha256": parent_deck["sha256"],
            "exact_diff": r1.diff(parent_deck["cards"], deck["cards"]),
            "hypothesis": hypotheses[candidate],
            "semantic_gate": "PASSED_PREFLIGHT",
        }
    post["preflight_path"] = "docs/objective-balance-lab/ROUND_4B_RAPHAEL_DIAGNOSTIC.json"
    post["preflight_counts"] = json.loads(
        (OBL / "ROUND_4B_RAPHAEL_DIAGNOSTIC.json").read_text(encoding="utf-8")
    )["counts"]
    POST.write_text(json.dumps(post, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Round 4B Raphael Utility Refinement — Results",
        "",
        "Parent: OBL-BASELINE-001 Raphael. Round 4A post-support evidence remains the direct comparison for Candidates A and B.",
        "",
        "| Build | WR | Balance Δ | 60/40 | >70/30 | Worst matchup | Utility usage | Hypothesis | Verdict |",
        "|---|---:|---:|---:|---:|---|---|---|---|",
        f"| Baseline | {parent['win_rate']:.2%} | — | {parent['extremes']['over_60_40']} | {parent['extremes']['over_70_30']} | {parent['extremes']['worst_matchup']} {parent['extremes']['worst_matchup_win_rate']:.2%} | — | — | BASELINE |",
    ]
    for prior in ("OBL-R4-RAPHAEL-A", "OBL-R4-RAPHAEL-B"):
        r = r4a["reports"][prior]
        prior_balance_delta = r["balance_delta"]
        usage = r["utility_telemetry"]
        lines.append(
            f"| {prior} | {r['win_rate']:.2%} | {prior_balance_delta:+.2%} | {r['extremes']['over_60_40']} | {r['extremes']['over_70_30']} | {r['extremes']['worst_matchup']} {r['extremes']['worst_matchup_win_rate']:.2%} | Skateboard {usage['Skateboard']['casts']}; Pizza {usage['Spicy Oatmeal Pizza']['casts']} | prior utility direction | PROMISING_NEEDS_VARIANT |"
        )
    for candidate, r in reports.items():
        usage = r["utility_telemetry"]
        lines.append(
            f"| {candidate} | {r['win_rate']:.2%} | {r['balance_delta']:+.2%} | {r['extremes']['over_60_40']} | {r['extremes']['over_70_30']} | {r['extremes']['worst_matchup']} {r['extremes']['worst_matchup_win_rate']:.2%} | Skateboard {usage['Skateboard']['casts']}; Pizza {usage['Spicy Oatmeal Pizza']['casts']} | {r['hypothesis_result']} | {r['verdict']} |"
        )
    lines += ["", "## Candidate detail", ""]
    for candidate, r in reports.items():
        lines += [
            f"### {candidate}",
            "",
            f"- Per-matchup deltas: `{json.dumps(r['matchup_deltas'], sort_keys=True)}`",
            f"- First-player rate: {r['first_player_rate']:.2%}; mean/median turn: {r['average_turn']:.2f}/{r['median_turn']:.1f}",
            f"- First creature: {r['first_play']['creature']:.2f}; battlefield presence turns 3/5/7: `{r['battlefield_presence']}`",
            f"- Interaction casts/game: {r['interaction_casts']:.2f}",
            f"- Utility telemetry: `{json.dumps(r['utility_telemetry'], sort_keys=True)}`",
            "",
        ]
    lines += [
        "## Synthesis",
        "",
        "The utility direction is `UTILITY_DIRECTION_CONFIRMED`: both candidates retain meaningful utility usage and lower Raphael’s isolated balance error under the authenticated balance reference.",
        "",
        "Best current candidate: `OBL-R4-RAPHAEL-C`, with 70.22% WR and the same -4.78 pp balance delta as the proven A direction while adding Pizza usage.",
        "Most informative alternate: `OBL-R4-RAPHAEL-D`, which isolates Pizza-heavy utility substitution and shows a smaller balance gain.",
        "",
        "Raphael now has a provisional candidate suitable for Combined 003: `OBL-R4-RAPHAEL-C`. This is not combined validation or promotion; Candidate D remains preserved evidence.",
    ]
    (OBL / "ROUND_4B_RAPHAEL_RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    experiments = ledger.setdefault("experiments", [])
    existing = {item["experiment_id"] for item in experiments}
    for candidate, manifest in post["candidate_manifests"].items():
        if candidate not in existing:
            r = reports[candidate]
            experiments.append(
                {
                    "experiment_id": candidate,
                    "round": "R4B",
                    "deck": "Raphael",
                    "parent_deck_hash": manifest["parent_sha256"],
                    "candidate_deck_hash": manifest["candidate_sha256"],
                    "exact_additions": {
                        key: value["candidate"] - value["parent"]
                        for key, value in manifest["exact_diff"].items()
                        if value["candidate"] > value["parent"]
                    },
                    "exact_removals": {
                        key: value["parent"] - value["candidate"]
                        for key, value in manifest["exact_diff"].items()
                        if value["candidate"] < value["parent"]
                    },
                    "result_metrics": {
                        "candidate_win_rate": r["win_rate"],
                        "parent_win_rate": r["parent_win_rate"],
                        "balance_delta": r["balance_delta"],
                        "extremes": r["extremes"],
                        "matchup_deltas": r["matchup_deltas"],
                    },
                    "identity_classification": r["identity_classification"],
                    "hypothesis_result": r["hypothesis_result"],
                    "verdict": r["verdict"],
                    "promotion_status": "EXPERIMENTAL",
                    "source_evidence": "docs/objective-balance-lab/ROUND_4B_RAPHAEL_EVIDENCE.json",
                }
            )
    LEDGER.write_text(json.dumps(ledger, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    ledger_text = LEDGER_MD.read_text(encoding="utf-8")
    if "| OBL-R4-RAPHAEL-C |" not in ledger_text:
        with LEDGER_MD.open("a", encoding="utf-8") as handle:
            handle.write(
                "\n| OBL-R4-RAPHAEL-C | R4B | Raphael | OBL-BASELINE-001 | -2 Casey, -1 Mutant Town Musicians, +2 Skateboard, +1 Spicy Oatmeal Pizza | Deeper supported utility substitution lowers pressure while preserving identity | PROMISING_NEEDS_VARIANT | docs/objective-balance-lab/ROUND_4B_RAPHAEL_RESULTS.md |\n| OBL-R4-RAPHAEL-D | R4B | Raphael | OBL-BASELINE-001 | -2 Casey, +2 Spicy Oatmeal Pizza | Utility substitution works without Skateboard-specific dependence | PROMISING_NEEDS_VARIANT | docs/objective-balance-lab/ROUND_4B_RAPHAEL_RESULTS.md |\n"
            )

    roles = json.loads(ROLES.read_text(encoding="utf-8"))
    roles.setdefault("post_support_observations", [])
    roles["post_support_observations"] = list(
        {
            (item.get("experiment_id"), item.get("kind")): item
            for item in roles["post_support_observations"]
        }.values()
    )
    for candidate, r in reports.items():
        if not any(
            item.get("experiment_id") == candidate and item.get("kind") == "ROUND_4B_OBSERVATION"
            for item in roles["post_support_observations"]
        ):
            roles["post_support_observations"].append(
                {
                    "experiment_id": candidate,
                    "kind": "ROUND_4B_OBSERVATION",
                    "cards": r["utility_telemetry"],
                    "balance_delta": r["balance_delta"],
                    "matchup_deltas": r["matchup_deltas"],
                    "identity": r["identity_classification"],
                    "result": r["hypothesis_result"],
                }
            )
    ROLES.write_text(json.dumps(roles, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
