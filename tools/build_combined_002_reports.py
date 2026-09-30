"""Build human reports and the auditable manifest for Combined 002."""

# Evidence tables intentionally retain compact long expressions.
# ruff: noqa: E501, I001

from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

import run_objective_balance_lab_round1 as r1
import run_combined_002 as c2

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def matchup_rates(games: list[dict], deck: str) -> dict[str, float]:
    result = {}
    for opponent in r1.DECKS:
        if opponent == deck:
            continue
        subset = [g for g in games if deck in g["seats"] and opponent in g["seats"]]
        result[opponent] = round(
            (sum(g["winner"] == deck for g in subset) + sum(g["draw"] for g in subset) / 2)
            / len(subset),
            6,
        )
    return result


def summary(games: list[dict], deck: str) -> dict:
    aggregate = r1.aggregate(games, (deck,))[deck]
    rates = matchup_rates(games, deck)
    worst = max(rates, key=lambda k: abs(rates[k] - 0.5))
    return {
        **aggregate,
        "matchup_win_rates": rates,
        "mean_matchup_balance_error": round(
            sum(abs(v - 0.5) for v in rates.values()) / len(rates), 6
        ),
        "median_matchup_deviation": round(
            statistics.median(abs(v - 0.5) for v in rates.values()), 6
        ),
        "extremes": {
            "worst_matchup": worst,
            "worst_matchup_win_rate": rates[worst],
            "over_60_40": sum(v > 0.6 or v < 0.4 for v in rates.values()),
            "over_70_30": sum(v > 0.7 or v < 0.3 for v in rates.values()),
        },
        "runtime_errors": sum(bool(g.get("runtime_error")) for g in games if deck in g["seats"]),
    }


def global_metrics(summaries: dict[str, dict], games: list[dict]) -> dict:
    cells = []
    for index, left in enumerate(r1.DECKS):
        for right in r1.DECKS[index + 1 :]:
            rate = summaries[left]["matchup_win_rates"][right]
            cells.append((left, right, rate))
    rates = [rate for _, _, rate in cells]
    deck_wrs = [item["win_rate"] for item in summaries.values()]
    worst_left, worst_right, worst_rate = max(cells, key=lambda item: abs(item[2] - 0.5))
    return {
        "mean_matchup_balance_error": round(statistics.mean(abs(rate - 0.5) for rate in rates), 6),
        "median_matchup_deviation": round(statistics.median(abs(rate - 0.5) for rate in rates), 6),
        "worst_matchup": {
            "decks": [worst_left, worst_right],
            "winner_side": worst_left if worst_rate > 0.5 else worst_right,
            "winner_rate": max(worst_rate, 1 - worst_rate),
            "deviation": abs(worst_rate - 0.5),
        },
        "over_60_40": sum(rate > 0.6 or rate < 0.4 for rate in rates),
        "over_70_30": sum(rate > 0.7 or rate < 0.3 for rate in rates),
        "aggregate_win_rate_spread": round(max(deck_wrs) - min(deck_wrs), 6),
        "aggregate_win_rate_stddev": round(statistics.pstdev(deck_wrs), 6),
        "mean_first_player_result_rate": round(
            statistics.mean(item["first_player_rate"] for item in summaries.values()), 6
        ),
        "mean_ending_turn": round(statistics.mean(g["turn"] for g in games), 4),
        "median_ending_turn": statistics.median(g["turn"] for g in games),
    }


def classify(isolated: float, combined: float) -> str:
    if isolated == 0 or combined == 0 or isolated * combined < 0:
        return "DELTA_REVERSES" if isolated * combined < 0 else "DELTA_WEAKENS"
    if abs(combined) < abs(isolated) * 0.75:
        return "DELTA_WEAKENS"
    if abs(combined) > abs(isolated) * 1.25:
        return "DELTA_STRENGTHENS"
    return "DELTA_PERSISTS"


def main() -> int:
    evidence_path = OBL / "COMBINED_002_EVIDENCE.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    baseline = json.loads((OBL / "COMBINED_001_EVIDENCE.json").read_text(encoding="utf-8"))
    round3 = json.loads((OBL / "ROUND_3_EVIDENCE.json").read_text(encoding="utf-8"))
    composed = evidence["combined_results"]
    baseline_summaries = baseline["combined_summary"]
    combined_summaries = {deck: summary(composed, deck) for deck in r1.DECKS}
    baseline_global = baseline["global_metrics"]["combined"]
    combined_global = global_metrics(combined_summaries, composed)
    evidence["baseline_001_summary"] = baseline_summaries
    evidence["combined_002_summary"] = combined_summaries
    evidence["global_metrics"] = {
        "baseline_001": baseline_global,
        "combined_002": combined_global,
        "delta": {
            key: round(combined_global[key] - baseline_global[key], 6)
            for key in (
                "mean_matchup_balance_error",
                "median_matchup_deviation",
                "aggregate_win_rate_spread",
                "aggregate_win_rate_stddev",
                "mean_first_player_result_rate",
                "mean_ending_turn",
            )
        },
    }

    isolated = {
        "april_oneil": round3["results"][c2.APRIL_ID],
        "krang": round3["results"][c2.KRANG_ID],
    }
    interaction = {}
    for deck, experiment_id in (("april_oneil", c2.APRIL_ID), ("krang", c2.KRANG_ID)):
        iso_delta = isolated[deck]["balance_delta"]
        combined_delta = round(
            combined_summaries[deck]["mean_matchup_balance_error"]
            - baseline_summaries[deck]["mean_matchup_balance_error"],
            6,
        )
        interaction[deck] = {
            "experiment_id": experiment_id,
            "isolated_balance_delta": iso_delta,
            "combined_balance_delta": combined_delta,
            "classification": classify(iso_delta, combined_delta),
            "isolated_win_rate": isolated[deck]["candidate_win_rate"],
            "baseline_win_rate": baseline_summaries[deck]["win_rate"],
            "combined_win_rate": combined_summaries[deck]["win_rate"],
            "new_pairing_matchup": combined_summaries[deck]["matchup_win_rates"][
                "krang" if deck == "april_oneil" else "april_oneil"
            ],
        }
    evidence["interaction_effects"] = interaction
    april_pass = (
        combined_summaries["april_oneil"]["mean_matchup_balance_error"]
        < baseline_summaries["april_oneil"]["mean_matchup_balance_error"]
        and combined_summaries["april_oneil"]["extremes"]["over_70_30"]
        <= baseline_summaries["april_oneil"]["extremes"]["over_70_30"]
    )
    krang_mixed = (
        combined_summaries["krang"]["mean_matchup_balance_error"]
        < baseline_summaries["krang"]["mean_matchup_balance_error"]
        and combined_summaries["krang"]["extremes"]["over_60_40"]
        > baseline_summaries["krang"]["extremes"]["over_60_40"]
    )
    evidence["candidate_decisions"] = {
        "april_oneil": {
            "combined_validation": "COMBINED_VALIDATION_PASSED"
            if april_pass
            else "COMBINED_VALIDATION_MIXED",
            "promotion_eligibility": "PROMOTION_ELIGIBLE"
            if april_pass
            else "NOT_PROMOTION_ELIGIBLE",
        },
        "krang": {
            "combined_validation": "COMBINED_VALIDATION_MIXED"
            if krang_mixed
            else "COMBINED_VALIDATION_FAILED",
            "promotion_eligibility": "NOT_PROMOTION_ELIGIBLE",
        },
    }
    global_delta = (
        combined_global["mean_matchup_balance_error"]
        - baseline_global["mean_matchup_balance_error"]
    )
    evidence["environment_decision"] = (
        "COMBINED_ENVIRONMENT_IMPROVED"
        if global_delta < -0.005 and combined_global["over_70_30"] <= baseline_global["over_70_30"]
        else "COMBINED_ENVIRONMENT_MIXED"
        if global_delta < 0
        else "COMBINED_ENVIRONMENT_REGRESSED"
    )
    evidence["manifest_path"] = "docs/objective-balance-lab/combined/OBL_COMBINED_002_MANIFEST.json"
    evidence_path.write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (OBL / "COMBINED_002_EVIDENCE.checkpoint.json").write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    baseline_manifest = json.loads(
        (OBL / "baselines/OBL_BASELINE_001_MANIFEST.json").read_text(encoding="utf-8")
    )
    selected = []
    for item in baseline_manifest["decks"]:
        deck = item["deck_key"]
        if deck == "april_oneil":
            m = round3["candidate_manifests"][c2.APRIL_ID]
            selected.append(
                {
                    "deck": item["deck"],
                    "deck_key": deck,
                    "source_kind": "round3_candidate",
                    "source_path": m["candidate_path"],
                    "sha256": m["candidate_sha256"],
                    "parent_baseline_sha256": item["sha256"],
                    "promotion_experiment_id": c2.APRIL_ID,
                    "exact_diff": m["exact_diff"],
                    "selection_rationale": "Accepted isolated value result; selected for Combined 002.",
                }
            )
        elif deck == "krang":
            m = round3["candidate_manifests"][c2.KRANG_ID]
            selected.append(
                {
                    "deck": item["deck"],
                    "deck_key": deck,
                    "source_kind": "round3_candidate",
                    "source_path": m["candidate_path"],
                    "sha256": m["candidate_sha256"],
                    "parent_baseline_sha256": item["sha256"],
                    "promotion_experiment_id": c2.KRANG_ID,
                    "exact_diff": m["exact_diff"],
                    "selection_rationale": "Promising but higher-risk isolated result; included to test the open engine-consistency question.",
                }
            )
        else:
            selected.append(
                {
                    "deck": item["deck"],
                    "deck_key": deck,
                    "source_kind": "baseline_001",
                    "source_path": item["source_path"],
                    "sha256": item["sha256"],
                    "parent_baseline_sha256": item["sha256"],
                    "promotion_experiment_id": None,
                    "exact_diff": {"additions": {}, "removals": {}},
                    "selection_rationale": "Frozen unchanged from OBL-BASELINE-001.",
                }
            )
    manifest = {
        "schema": "objective-balance-lab-combined-manifest-v2",
        "environment_id": "OBL-COMBINED-002",
        "state": "EXPERIMENTAL_COMBINED_ENVIRONMENT",
        "repository_sha": "ca3b6b83f59f449091f103d1e94c117ddb9ff5fa",
        "parent_environment_id": "OBL-BASELINE-001",
        "selection_experiment_ids": [c2.APRIL_ID, c2.KRANG_ID],
        "source_evidence": {
            "path": "docs/objective-balance-lab/COMBINED_002_EVIDENCE.json",
            "sha256": sha(evidence_path),
        },
        "selected_decks": selected,
    }
    manifest_path = OBL / "combined/OBL_COMBINED_002_MANIFEST.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    lines = [
        "# OBL-COMBINED-002 Selection",
        "",
        "Selected provisional candidates are April A and Krang A. The other eight decks are byte-identical to OBL-BASELINE-001. This environment is experimental and no promotion occurs.",
        "",
        "| Deck | Selection | Source | Rationale |",
        "|---|---|---|---|",
    ]
    for item in selected:
        lines.append(
            f"| {item['deck']} | `{item['promotion_experiment_id'] or 'OBL-BASELINE-001'}` | `{item['source_path']}` | {item['selection_rationale']} |"
        )
    lines += [
        "",
        "The logical matrix is 4,500 games. Exactly 4,400 games are authenticated reuse and exactly 100 April-vs-Krang games are newly executed. No full matrix rerun occurred.",
        "",
        "Provenance counts: 28 `BASELINE_001_REUSED`, 8 `ROUND_3_APRIL_REUSED`, 8 `ROUND_3_KRANG_REUSED`, 1 `COMBINED_002_NEW_PAIRING`.",
    ]
    (OBL / "COMBINED_002_SELECTION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    lines = [
        "# OBL-COMBINED-002 Results",
        "",
        f"Logical games: **4,500**. Newly executed: **100**. Reused authenticated games: **4,400**. Environment decision: **{evidence['environment_decision']}**.",
        "",
        "## Global metrics",
        "",
        "| Metric | OBL-BASELINE-001 | OBL-COMBINED-002 | Δ |",
        "|---|---:|---:|---:|",
    ]
    for key in (
        "mean_matchup_balance_error",
        "median_matchup_deviation",
        "over_60_40",
        "over_70_30",
        "aggregate_win_rate_spread",
        "mean_first_player_result_rate",
        "mean_ending_turn",
        "median_ending_turn",
    ):
        b = baseline_global[key]
        c = combined_global[key]
        d = c - b if isinstance(c, (int, float)) else "n/a"
        lines.append(f"| {key} | {b} | {c} | {d} |")
    lines += [
        "",
        "## Deck metrics",
        "",
        "| Deck | Baseline WR | Combined WR | Balance error baseline → combined | 60/40 | 70/30 | Worst matchup |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for deck in r1.DECKS:
        b = baseline_summaries[deck]
        c = combined_summaries[deck]
        lines.append(
            f"| {deck} | {b['win_rate']:.2%} | {c['win_rate']:.2%} | {b['mean_matchup_balance_error']:.2%} → {c['mean_matchup_balance_error']:.2%} | {b['extremes']['over_60_40']} → {c['extremes']['over_60_40']} | {b['extremes']['over_70_30']} → {c['extremes']['over_70_30']} | {b['extremes']['worst_matchup']} {b['extremes']['worst_matchup_win_rate']:.2%} → {c['extremes']['worst_matchup']} {c['extremes']['worst_matchup_win_rate']:.2%} |"
        )
    lines += [
        "",
        "## Candidate interaction",
        "",
        f"- April A: isolated {isolated['april_oneil']['candidate_win_rate']:.2%}, combined {combined_summaries['april_oneil']['win_rate']:.2%}; balance classification `{interaction['april_oneil']['classification']}`; April-vs-Krang rate `{interaction['april_oneil']['new_pairing_matchup']:.2%}`.",
        f"- Krang A: isolated {isolated['krang']['candidate_win_rate']:.2%}, combined {combined_summaries['krang']['win_rate']:.2%}; balance classification `{interaction['krang']['classification']}`; Krang-vs-April rate `{interaction['krang']['new_pairing_matchup']:.2%}`.",
        "",
        "April is `COMBINED_VALIDATION_PASSED` and `PROMOTION_ELIGIBLE` only if its composed balance and extreme metrics improve; Krang is treated as the higher-risk mixed candidate and is not promotion-eligible.",
        "",
        "Machine evidence: `COMBINED_002_EVIDENCE.json`; manifest: `combined/OBL_COMBINED_002_MANIFEST.json`; new pairing: `COMBINED_002_NEW_PAIRING.json`.",
    ]
    (OBL / "COMBINED_002_RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "environment_decision": evidence["environment_decision"],
                "baseline_global": baseline_global,
                "combined_global": combined_global,
                "interaction": interaction,
                "candidate_decisions": evidence["candidate_decisions"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
