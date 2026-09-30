"""Build Round 3 reports, ledger records, and persistent card-role evidence."""

# Evidence-contract tables intentionally retain readable long lines.
# ruff: noqa: E501, I001

from __future__ import annotations

import hashlib
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import run_objective_balance_lab_round3 as r3  # noqa: E402
import run_objective_balance_lab_round1 as r1  # noqa: E402

OBL = ROOT / "docs/objective-balance-lab"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rates(games: list[dict], deck: str) -> dict[str, float]:
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


def extremes(matchups: dict[str, float]) -> dict[str, object]:
    worst = max(matchups, key=lambda k: abs(matchups[k] - 0.5))
    return {
        "worst_matchup": worst,
        "worst_matchup_win_rate": matchups[worst],
        "over_60_40": sum(v > 0.6 or v < 0.4 for v in matchups.values()),
        "over_70_30": sum(v > 0.7 or v < 0.3 for v in matchups.values()),
    }


def summarize(games: list[dict], deck: str) -> dict:
    base = r1.aggregate(games, (deck,))[deck]
    matchup = rates(games, deck)
    return {
        **base,
        "matchup_win_rates": matchup,
        "mean_matchup_balance_error": round(
            sum(abs(v - 0.5) for v in matchup.values()) / len(matchup), 6
        ),
        "median_matchup_deviation": round(
            statistics.median(abs(v - 0.5) for v in matchup.values()), 6
        ),
        "extremes": extremes(matchup),
        "runtime_errors": sum(bool(g.get("runtime_error")) for g in games if deck in g["seats"]),
    }


def hypothesis_result(deck: str, parent: dict, candidate: dict) -> str:
    improvement = candidate["mean_matchup_balance_error"] < parent["mean_matchup_balance_error"]
    wr = candidate["win_rate"] - parent["win_rate"]
    if deck in {"raphael", "shredder"}:
        if improvement and wr <= 0:
            return "SUPPORTED"
        if improvement or wr < 0:
            return "PARTIALLY_SUPPORTED"
        return "FALSIFIED"
    if improvement and wr >= 0:
        return "SUPPORTED"
    if improvement or wr > 0:
        return "PARTIALLY_SUPPORTED"
    return "FALSIFIED"


def verdict(parent: dict, candidate: dict, identity: str) -> str:
    delta = candidate["mean_matchup_balance_error"] - parent["mean_matchup_balance_error"]
    extreme_delta = candidate["extremes"]["over_70_30"] - parent["extremes"]["over_70_30"]
    if identity == "IDENTITY_DILUTED":
        return "REJECT_IDENTITY_REGRESSION"
    if delta <= -0.005 and extreme_delta <= 0:
        return "ACCEPT_FOR_COMBINED_MATRIX"
    if delta < 0:
        return "PROMISING_NEEDS_VARIANT"
    if abs(delta) < 0.001:
        return "INCONCLUSIVE"
    return "REJECT_BALANCE_REGRESSION"


def fmt_diff(diff: dict) -> str:
    adds = ", ".join(
        f"+{v['candidate'] - v['parent']} {k}"
        for k, v in diff.items()
        if v["candidate"] > v["parent"]
    )
    removes = ", ".join(
        f"-{v['parent'] - v['candidate']} {k}"
        for k, v in diff.items()
        if v["candidate"] < v["parent"]
    )
    return "; ".join(x for x in (removes, adds) if x)


def main() -> int:
    evidence_path = OBL / "ROUND_3_EVIDENCE.json"
    payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    baseline = json.loads((OBL / "COMBINED_001_EVIDENCE.json").read_text(encoding="utf-8"))
    cards = r1.catalog()
    results = {}
    identities = {
        "OBL-R3-RAPHAEL-A": "IDENTITY_STRENGTHENED",
        "OBL-R3-RAPHAEL-B": "IDENTITY_STRENGTHENED",
        "OBL-R3-SHREDDER-A": "IDENTITY_PRESERVED",
        "OBL-R3-SHREDDER-B": "IDENTITY_PRESERVED",
        "OBL-R3-APRIL_ONEIL-A": "IDENTITY_STRENGTHENED",
        "OBL-R3-APRIL_ONEIL-B": "IDENTITY_PRESERVED",
        "OBL-R3-KRANG-A": "IDENTITY_STRENGTHENED",
        "OBL-R3-KRANG-B": "IDENTITY_STRENGTHENED",
    }
    for experiment_id, manifest in payload["candidate_manifests"].items():
        deck = manifest["deck_key"]
        parent = baseline["combined_summary"][deck]
        candidate = summarize(payload["candidate_results"][experiment_id], deck)
        result = {
            "parent_win_rate": parent["win_rate"],
            "candidate_win_rate": candidate["win_rate"],
            "balance_error_parent": parent["mean_matchup_balance_error"],
            "balance_error_candidate": candidate["mean_matchup_balance_error"],
            "balance_delta": round(
                candidate["mean_matchup_balance_error"] - parent["mean_matchup_balance_error"], 6
            ),
            "matchup_deltas": {
                k: round(candidate["matchup_win_rates"][k] - parent["matchup_win_rates"][k], 6)
                for k in candidate["matchup_win_rates"]
            },
            "parent_extremes": parent["extremes"],
            "candidate_extremes": candidate["extremes"],
            "parent_mean_turn": parent["average_turn"],
            "candidate_mean_turn": candidate["average_turn"],
            "parent_median_turn": parent["median_turn"],
            "candidate_median_turn": candidate["median_turn"],
            "parent_first_player_rate": parent["first_player_rate"],
            "candidate_first_player_rate": candidate["first_player_rate"],
            "parent_first_play": parent["first_play"],
            "candidate_first_play": candidate["first_play"],
            "parent_interaction_casts": parent["interaction_casts"],
            "candidate_interaction_casts": candidate["interaction_casts"],
            "identity_classification": identities[experiment_id],
            "hypothesis_result": hypothesis_result(deck, parent, candidate),
            "verdict": verdict(parent, candidate, identities[experiment_id]),
            "candidate_summary": candidate,
        }
        results[experiment_id] = result
    payload["results"] = results
    payload["synthesis"] = {}
    for deck, spec in r3.TARGETS.items():
        ids = list(spec["candidates"])
        best = min(ids, key=lambda i: results[i]["balance_delta"])
        failure = max(ids, key=lambda i: results[i]["balance_delta"])
        eligible = [
            i
            for i in ids
            if results[i]["verdict"] in {"ACCEPT_FOR_COMBINED_MATRIX", "PROMISING_NEEDS_VARIANT"}
        ]
        payload["synthesis"][deck] = {
            "best_candidate": best,
            "most_informative_failure": failure,
            "strongest_card_role_signal": fmt_diff(
                payload["candidate_manifests"][best]["exact_diff"]
            ),
            "candidate_suitable_for_combined_002": bool(eligible),
            "unresolved_question": r3.HYPOTHESES[best],
        }
    payload["provisional_combined_002_pool"] = {
        deck: data["best_candidate"]
        for deck, data in payload["synthesis"].items()
        if data["candidate_suitable_for_combined_002"]
    }
    evidence_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    checkpoint = OBL / "ROUND_3_EVIDENCE.checkpoint.json"
    checkpoint.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    role_path = OBL / "CARD_ROLE_EVIDENCE.json"
    role = json.loads(role_path.read_text(encoding="utf-8"))
    role["round3_evidence_path"] = "docs/objective-balance-lab/ROUND_3_EVIDENCE.json"
    for experiment_id, manifest in payload["candidate_manifests"].items():
        result = results[experiment_id]
        for card_name, counts in manifest["exact_diff"].items():
            delta = counts["candidate"] - counts["parent"]
            record = cards[card_name]
            role["records"].append(
                {
                    "experiment_id": experiment_id,
                    "round": "R3",
                    "deck": manifest["deck"],
                    "candidate": experiment_id,
                    "card": card_name,
                    "copies_changed": delta,
                    "replacement_relationship": fmt_diff(manifest["exact_diff"]),
                    "mana_value": record.get("cmc"),
                    "card_type": record.get("type_line"),
                    "rules_text": record.get("oracle_text"),
                    "semantic_support": "PASSED_PRE_SCREEN",
                    "aggregate_win_rate_delta": round(
                        result["candidate_win_rate"] - result["parent_win_rate"], 6
                    ),
                    "matchup_deltas": result["matchup_deltas"],
                    "balance_error_delta": result["balance_delta"],
                    "early_board_delta": {k: None for k in ("3", "5", "7")},
                    "interaction_delta": None,
                    "signature_delta": None,
                    "engine_activation_delta": None,
                    "identity_result": result["identity_classification"],
                    "hypothesis_result": result["hypothesis_result"],
                    "causality_note": "Associational evidence from an isolated 900-game slice; not a card-level causal claim.",
                }
            )
    role_path.write_text(json.dumps(role, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    ledger_path = OBL / "EXPERIMENT_LEDGER.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    for experiment_id, manifest in payload["candidate_manifests"].items():
        result = results[experiment_id]
        ledger["experiments"].append(
            {
                "experiment_id": experiment_id,
                "round": "R3",
                "deck": manifest["deck"],
                "deck_key": manifest["deck_key"],
                "parent": {
                    "path": manifest["parent_path"],
                    "sha256": manifest["parent_sha256"],
                    "environment_id": "OBL-BASELINE-001",
                },
                "candidate": {
                    "path": manifest["candidate_path"],
                    "sha256": manifest["candidate_sha256"],
                    "label": experiment_id.rsplit("-", 1)[-1],
                },
                "exact_additions": {
                    k: v["candidate"] - v["parent"]
                    for k, v in manifest["exact_diff"].items()
                    if v["candidate"] > v["parent"]
                },
                "exact_removals": {
                    k: v["parent"] - v["candidate"]
                    for k, v in manifest["exact_diff"].items()
                    if v["candidate"] < v["parent"]
                },
                "hypothesis": manifest["hypothesis"],
                "schedule_identity": payload["schedule_sha256"],
                "source_evidence": {
                    "path": "docs/objective-balance-lab/ROUND_3_EVIDENCE.json",
                    "sha256": sha(evidence_path),
                },
                "result_metrics": {
                    k: v for k, v in result.items() if k not in {"candidate_summary"}
                },
                "identity_classification": result["identity_classification"],
                "hypothesis_result": result["hypothesis_result"],
                "verdict": result["verdict"],
                "promotion_status": "NOT_PROMOTED_COMBINED_MATRIX_REQUIRED",
            }
        )
    ledger["next_gate"] = "SELECT COMBINED-MATRIX CANDIDATES FOR OBL-COMBINED-002"
    ledger_path.write_text(
        json.dumps(ledger, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    lines = [
        "# Objective Balance Lab — Round 3 Delta Results",
        "",
        "All eight candidates completed 900 games against the nine OBL-BASELINE-001 opponents (7,200 games total). Negative Balance Δ is an improvement. Historical R1/R2 results remain contextual because their isolated parents predate OBL-BASELINE-001.",
        "",
        "| Experiment | Parent WR | Candidate WR | Balance Δ | >60/40 | >70/30 | Hypothesis | Verdict |",
        "|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for experiment_id, result in results.items():
        e = result["candidate_extremes"]
        lines.append(
            f"| `{experiment_id}` | {result['parent_win_rate']:.2%} | {result['candidate_win_rate']:.2%} | {result['balance_delta']:+.2%} | {e['over_60_40']} | {e['over_70_30']} | {result['hypothesis_result']} | {result['verdict']} |"
        )
    lines += ["", "## Per-candidate matchup deltas", ""]
    for experiment_id, result in results.items():
        lines.append(f"### `{experiment_id}` — {result['identity_classification']}")
        lines.append("")
        lines.append("; ".join(f"{k}: {v:+.2%}" for k, v in result["matchup_deltas"].items()))
        lines.append("")
    lines += ["## Synthesis", ""]
    for deck, data in payload["synthesis"].items():
        lines.append(
            f"- **{r3.TARGETS[deck]['display']}** — best `{data['best_candidate']}`; informative failure `{data['most_informative_failure']}`; Combined 002 suitable: `{data['candidate_suitable_for_combined_002']}`; unresolved question: {data['unresolved_question']}"
        )
    lines += [
        "",
        f"Provisional Combined 002 pool: `{json.dumps(payload['provisional_combined_002_pool'], sort_keys=True)}`.",
        "",
        "Machine-readable evidence: `ROUND_3_EVIDENCE.json`; checkpoint: `ROUND_3_EVIDENCE.checkpoint.json`; pre-screen: `ROUND_3_CANDIDATES.md`; card-role dataset: `CARD_ROLE_EVIDENCE.json`.",
    ]
    (OBL / "ROUND_3_DELTA_RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Stable human ledger is append-only: preserve every historical line verbatim.
    md = (OBL / "EXPERIMENT_LEDGER.md").read_text(encoding="utf-8").rstrip().splitlines()
    md += ["", "## Round 3 appended records", ""]
    for item in ledger["experiments"]:
        if item["round"] == "R3":
            m = payload["candidate_manifests"][item["experiment_id"]]
            rr = results[item["experiment_id"]]
            md.append(
                f"| `{item['experiment_id']}` | R3 | {item['deck']} | {fmt_diff(m['exact_diff'])} | {rr['parent_win_rate']:.2%} | {rr['candidate_win_rate']:.2%} | {rr['balance_delta']:+.2%} | {rr['identity_classification']} | {rr['verdict']} | NOT PROMOTED |"
            )
    (OBL / "EXPERIMENT_LEDGER.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "candidates": len(results),
                "games": payload["counts"]["completed_games"],
                "pool": payload["provisional_combined_002_pool"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
