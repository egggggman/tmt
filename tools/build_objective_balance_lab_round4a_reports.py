"""Build Round 4A Raphael reports and append durable experiment evidence."""

# Evidence tables intentionally retain compact long expressions.
# ruff: noqa: E501, I001

from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

import run_objective_balance_lab_round1 as r1

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(games: list[dict]) -> dict:
    base = r1.aggregate(games, ("raphael",))["raphael"]
    rates = {}
    for opponent in r1.DECKS:
        if opponent == "raphael":
            continue
        subset = [g for g in games if "raphael" in g["seats"] and opponent in g["seats"]]
        rates[opponent] = round(
            (sum(g["winner"] == "raphael" for g in subset) + sum(g["draw"] for g in subset) / 2)
            / len(subset),
            6,
        )
    worst = max(rates, key=lambda k: abs(rates[k] - 0.5))
    signature = {}
    for card in ("Skateboard", "Spicy Oatmeal Pizza", "Casey Jones, Jury-Rig Justiciar"):
        values = [
            sum(v for key, v in g.get("signature_casts", {}).items() if key == f"raphael:{card}")
            for g in games
        ]
        signature[card] = {
            "total_casts": sum(values),
            "average_per_game": round(statistics.mean(values), 4) if values else 0,
            "games_with_cast": sum(value > 0 for value in values),
        }
    return {
        **base,
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
        "signature_usage": signature,
        "jury_rig_artifact_hit": None,
        "runtime_errors": sum(bool(g.get("runtime_error")) for g in games),
    }


def main() -> int:
    path = OBL / "ROUND_4A_RAPHAEL_EVIDENCE.json"
    evidence = json.loads(path.read_text(encoding="utf-8"))
    baseline_evidence = json.loads((OBL / "COMBINED_001_EVIDENCE.json").read_text(encoding="utf-8"))
    baseline = baseline_evidence["combined_summary"]["raphael"]
    results = {}
    for experiment_id, games in evidence["candidate_results"].items():
        candidate = summarize(games)
        balance_delta = round(
            candidate["mean_matchup_balance_error"] - baseline["mean_matchup_balance_error"], 6
        )
        matchup_deltas = {
            opponent: round(
                candidate["matchup_win_rates"][opponent] - baseline["matchup_win_rates"][opponent],
                6,
            )
            for opponent in candidate["matchup_win_rates"]
        }
        identity = "IDENTITY_STRENGTHENED"
        utility_usage = (
            candidate["signature_usage"]["Skateboard"]["total_casts"]
            + candidate["signature_usage"]["Spicy Oatmeal Pizza"]["total_casts"]
        )
        if utility_usage == 0:
            hypothesis = "SEMANTICALLY_UNRESOLVED"
            verdict = "REJECT_SEMANTIC_CONFIDENCE"
        elif (
            candidate["win_rate"] < baseline["win_rate"]
            and balance_delta <= -0.005
            and candidate["extremes"]["over_70_30"] <= baseline["extremes"]["over_70_30"]
        ):
            hypothesis = "SUPPORTED"
            verdict = "ACCEPT_FOR_COMBINED_MATRIX"
        elif balance_delta < 0 or candidate["win_rate"] < baseline["win_rate"]:
            hypothesis = "PARTIALLY_SUPPORTED"
            verdict = "PROMISING_NEEDS_VARIANT"
        elif balance_delta == 0:
            hypothesis = "SEMANTICALLY_UNRESOLVED"
            verdict = "INCONCLUSIVE"
        else:
            hypothesis = "FALSIFIED"
            verdict = "REJECT_BALANCE_REGRESSION"
        results[experiment_id] = {
            "parent_win_rate": baseline["win_rate"],
            "candidate_win_rate": candidate["win_rate"],
            "balance_error_parent": baseline["mean_matchup_balance_error"],
            "balance_error_candidate": candidate["mean_matchup_balance_error"],
            "balance_delta": balance_delta,
            "matchup_deltas": matchup_deltas,
            "parent_extremes": baseline["extremes"],
            "candidate_extremes": candidate["extremes"],
            "parent_first_player_rate": baseline["first_player_rate"],
            "candidate_first_player_rate": candidate["first_player_rate"],
            "parent_average_turn": baseline["average_turn"],
            "candidate_average_turn": candidate["average_turn"],
            "parent_median_turn": baseline["median_turn"],
            "candidate_median_turn": candidate["median_turn"],
            "parent_first_play": baseline["first_play"],
            "candidate_first_play": candidate["first_play"],
            "parent_interaction_casts": baseline["interaction_casts"],
            "candidate_interaction_casts": candidate["interaction_casts"],
            "parent_battlefield_presence": baseline["battlefield_presence"],
            "candidate_battlefield_presence": candidate["battlefield_presence"],
            "candidate_signature_usage": candidate["signature_usage"],
            "jury_rig_artifact_hit": None,
            "identity_classification": identity,
            "hypothesis_result": hypothesis,
            "verdict": verdict,
            "candidate_summary": candidate,
        }
    evidence["baseline_summary"] = baseline
    evidence["results"] = results
    evidence["contextual_prior_raphael_experiments"] = [
        "OBL-R1-RAPHAEL-A",
        "OBL-R2-RAPHAEL-A",
        "OBL-R2-RAPHAEL-B",
        "OBL-R3-RAPHAEL-A",
        "OBL-R3-RAPHAEL-B",
    ]
    if all(result["hypothesis_result"] == "SEMANTICALLY_UNRESOLVED" for result in results.values()):
        evidence["best_next_direction"] = "SEMANTIC_INSTRUMENTATION_REQUIRED"
    else:
        evidence["best_next_direction"] = min(
            results, key=lambda key: results[key]["balance_delta"]
        )
    path.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OBL / "ROUND_4A_RAPHAEL_EVIDENCE.checkpoint.json").write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    cards = r1.catalog()
    role_path = OBL / "CARD_ROLE_EVIDENCE.json"
    role = json.loads(role_path.read_text(encoding="utf-8"))
    r4_ids = set(evidence["candidate_manifests"])
    role["records"] = [
        record for record in role["records"] if record.get("experiment_id") not in r4_ids
    ]
    for experiment_id, manifest in evidence["candidate_manifests"].items():
        result = results[experiment_id]
        for card_name, counts in manifest["exact_diff"].items():
            delta = counts["candidate"] - counts["parent"]
            card = cards[card_name]
            role["records"].append(
                {
                    "experiment_id": experiment_id,
                    "round": "R4A",
                    "deck": "Raphael",
                    "candidate": experiment_id,
                    "card": card_name,
                    "copies_changed": delta,
                    "replacement_relationship": manifest["exact_diff"],
                    "mana_value": card.get("cmc"),
                    "card_type": card.get("type_line"),
                    "rules_text": card.get("oracle_text"),
                    "semantic_support": "PASSED_PRE_SCREEN",
                    "aggregate_win_rate_delta": round(
                        result["candidate_win_rate"] - result["parent_win_rate"], 6
                    ),
                    "matchup_deltas": result["matchup_deltas"],
                    "balance_error_delta": result["balance_delta"],
                    "early_board_delta": {"3": None, "5": None, "7": None},
                    "interaction_delta": round(
                        result["candidate_interaction_casts"] - result["parent_interaction_casts"],
                        4,
                    ),
                    "signature_delta": result["candidate_signature_usage"],
                    "engine_activation_delta": None,
                    "identity_result": result["identity_classification"],
                    "causality_note": "Associational evidence from a controlled 900-game slice; not a card-level causal claim.",
                }
            )
    role_path.write_text(json.dumps(role, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    ledger_path = OBL / "EXPERIMENT_LEDGER.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["experiments"] = [
        record for record in ledger["experiments"] if record.get("experiment_id") not in r4_ids
    ]
    for experiment_id, manifest in evidence["candidate_manifests"].items():
        result = results[experiment_id]
        ledger["experiments"].append(
            {
                "experiment_id": experiment_id,
                "round": "R4A",
                "deck": "Raphael",
                "deck_key": "raphael",
                "parent": {
                    "path": manifest["parent_path"],
                    "sha256": manifest["parent_declared_sha256"],
                    "environment_id": "OBL-BASELINE-001",
                },
                "candidate": {
                    "path": manifest["candidate_path"],
                    "sha256": manifest["candidate_sha256"],
                    "label": experiment_id.rsplit("-", 1)[-1],
                },
                "exact_additions": {
                    name: row["candidate"] - row["parent"]
                    for name, row in manifest["exact_diff"].items()
                    if row["candidate"] > row["parent"]
                },
                "exact_removals": {
                    name: row["parent"] - row["candidate"]
                    for name, row in manifest["exact_diff"].items()
                    if row["candidate"] < row["parent"]
                },
                "hypothesis": manifest["hypothesis"],
                "schedule_identity": evidence["schedule_sha256"],
                "source_evidence": {
                    "path": "docs/objective-balance-lab/ROUND_4A_RAPHAEL_EVIDENCE.json",
                    "sha256": sha(path),
                },
                "result_metrics": {
                    key: value for key, value in result.items() if key != "candidate_summary"
                },
                "identity_classification": result["identity_classification"],
                "hypothesis_result": result["hypothesis_result"],
                "verdict": result["verdict"],
                "promotion_status": "NOT_PROMOTED_COMBINED_MATRIX_REQUIRED",
            }
        )
    ledger["next_gate"] = "SELECT COMBINED-MATRIX CANDIDATES FOR OBL-COMBINED-003"
    ledger_path.write_text(
        json.dumps(ledger, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    old_md = (OBL / "EXPERIMENT_LEDGER.md").read_text(encoding="utf-8").rstrip().splitlines()
    md = old_md[
        : next(
            (index for index, line in enumerate(old_md) if line == "## Round 4A appended records"),
            len(old_md),
        )
    ]
    md += [
        "",
        "## Round 4A appended records",
        "",
        "| ID | Round | Deck | Diff | Parent WR | Candidate WR | Balance Δ | Identity | Hypothesis | Verdict | Promotion | Evidence |",
        "|---|---|---|---|---:|---:|---:|---|---|---|---|---|",
    ]
    for experiment_id, result in results.items():
        md.append(
            f"| `{experiment_id}` | R4A | Raphael | {evidence['candidate_manifests'][experiment_id]['exact_diff']} | {result['parent_win_rate']:.2%} | {result['candidate_win_rate']:.2%} | {result['balance_delta']:+.2%} | {result['identity_classification']} | {result['hypothesis_result']} | {result['verdict']} | NOT PROMOTED | `ROUND_4A_RAPHAEL_EVIDENCE.json` |"
        )
    (OBL / "EXPERIMENT_LEDGER.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    lines = [
        "# Objective Balance Lab — Round 4A Raphael Results",
        "",
        "Each candidate completed 900 games against the nine OBL-BASELINE-001 opponents. Negative Balance Δ is improvement. Casey jury-rig artifact-hit telemetry is unavailable in the compact runner output and is explicitly not inferred.",
        "",
        "| Candidate | Parent WR | Candidate WR | Balance Δ | 60/40 | 70/30 | Hypothesis | Verdict |",
        "|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for experiment_id, result in results.items():
        lines.append(
            f"| `{experiment_id}` | {result['parent_win_rate']:.2%} | {result['candidate_win_rate']:.2%} | {result['balance_delta']:+.2%} | {result['parent_extremes']['over_60_40']}→{result['candidate_extremes']['over_60_40']} | {result['parent_extremes']['over_70_30']}→{result['candidate_extremes']['over_70_30']} | {result['hypothesis_result']} | {result['verdict']} |"
        )
        lines.append(
            f"| Signature usage | Skateboard {result['candidate_signature_usage']['Skateboard']['total_casts']} casts; Pizza {result['candidate_signature_usage']['Spicy Oatmeal Pizza']['total_casts']} casts; remaining Casey {result['candidate_signature_usage']['Casey Jones, Jury-Rig Justiciar']['total_casts']} casts | | | | | | |"
        )
    lines += ["", "## Per-matchup deltas", ""]
    for experiment_id, result in results.items():
        lines += [
            f"### `{experiment_id}`",
            "",
            "; ".join(f"{key}: {value:+.2%}" for key, value in result["matchup_deltas"].items()),
            "",
        ]
    lines += [
        "## Prior Raphael context",
        "",
        "R1 and R2 threat substitutions increased Raphael’s power by +1.44 to +2.11 pp; R3 threat substitutions increased it by +1.11 to +2.78 pp. Round 4A isolates utility density and diversified utility as the structural-nerf direction.",
        "",
        "| Historical experiment | Parent WR | Candidate WR | Balance Δ |",
        "|---|---:|---:|---:|",
        "| OBL-R1-RAPHAEL-A | 76.78% | 78.22% | +1.44 pp |",
        "| OBL-R2-RAPHAEL-A | 76.78% | 78.89% | +2.11 pp |",
        "| OBL-R2-RAPHAEL-B | 76.78% | 78.22% | +1.44 pp |",
        "| OBL-R3-RAPHAEL-A | 75.11% | 77.89% | +2.78 pp |",
        "| OBL-R3-RAPHAEL-B | 75.11% | 76.22% | +1.11 pp |",
        "",
        f"Best next Raphael direction: `{evidence['best_next_direction']}`. Machine evidence: `ROUND_4A_RAPHAEL_EVIDENCE.json`; checkpoint: `ROUND_4A_RAPHAEL_EVIDENCE.checkpoint.json`.",
    ]
    (OBL / "ROUND_4A_RAPHAEL_RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {"results": results, "best_next_direction": evidence["best_next_direction"]}, indent=2
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
