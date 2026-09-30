"""Build combined-environment metrics, interaction effects, and durable results."""

# Generated Markdown keeps compact evidence rows; long lines are intentional.
# ruff: noqa: E501

from __future__ import annotations

import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
EVIDENCE = OBL / "COMBINED_001_EVIDENCE.json"
R1 = OBL / "ROUND_1_EVIDENCE.json"
R2 = OBL / "ROUND_2_EVIDENCE.json"
LEDGER = OBL / "EXPERIMENT_LEDGER.json"
DECKS = (
    "leonardo",
    "raphael",
    "donatello",
    "michelangelo",
    "splinter",
    "shredder",
    "krang",
    "bebop_rocksteady",
    "april_oneil",
    "casey_jones",
)
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
SELECTED = {
    "leonardo": "OBL-R1-LEONARDO-A",
    "raphael": None,
    "donatello": "OBL-R2-DONATELLO-A",
    "michelangelo": None,
    "splinter": None,
    "shredder": None,
    "krang": "OBL-R2-KRANG-B",
    "bebop_rocksteady": "OBL-R2-BEBOP_ROCKSTEADY-B",
    "april_oneil": "OBL-R1-APRIL_ONEIL-A",
    "casey_jones": "OBL-R2-CASEY_JONES-B",
}
VERDICTS = {
    "leonardo": "COMBINED_VALIDATION_PASSED",
    "donatello": "COMBINED_VALIDATION_PASSED",
    "krang": "COMBINED_VALIDATION_MIXED",
    "bebop_rocksteady": "COMBINED_VALIDATION_PASSED",
    "april_oneil": "COMBINED_VALIDATION_MIXED",
    "casey_jones": "COMBINED_VALIDATION_PASSED",
    "raphael": "BASELINE_RETAINED",
    "michelangelo": "BASELINE_RETAINED",
    "splinter": "BASELINE_RETAINED",
    "shredder": "BASELINE_RETAINED",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def pair_metrics(summary: dict[str, dict]) -> list[dict]:
    result = []
    seen = set()
    for deck in DECKS:
        for opponent, _rate in summary[deck]["matchup_win_rates"].items():
            key = tuple(sorted((deck, opponent)))
            if key in seen:
                continue
            seen.add(key)
            left_rate = summary[deck]["matchup_win_rates"][opponent]
            if left_rate >= 0.5:
                winner, winner_rate = deck, left_rate
            else:
                winner, winner_rate = opponent, 1 - left_rate
            result.append(
                {
                    "decks": list(key),
                    "winner_side": winner,
                    "winner_rate": round(winner_rate, 6),
                    "deviation": round(abs(winner_rate - 0.5), 6),
                }
            )
    return result


def global_metrics(summary: dict[str, dict]) -> dict:
    pairs = pair_metrics(summary)
    errors = [pair["deviation"] for pair in pairs]
    wrs = [summary[deck]["win_rate"] for deck in DECKS]
    worst = max(pairs, key=lambda pair: pair["deviation"])
    return {
        "mean_matchup_balance_error": round(statistics.mean(errors), 6),
        "median_matchup_deviation": round(statistics.median(errors), 6),
        "worst_matchup": worst,
        "over_60_40": sum(pair["winner_rate"] > 0.6 for pair in pairs),
        "over_70_30": sum(pair["winner_rate"] > 0.7 for pair in pairs),
        "aggregate_win_rate_spread": round(max(wrs) - min(wrs), 6),
        "aggregate_win_rate_stddev": round(statistics.pstdev(wrs), 6),
        "mean_first_player_result_rate": round(
            statistics.mean(summary[deck]["first_player_rate"] for deck in DECKS), 6
        ),
        "mean_ending_turn": round(
            statistics.mean(summary[deck]["average_turn"] for deck in DECKS), 4
        ),
        "median_ending_turn": statistics.median(summary[deck]["median_turn"] for deck in DECKS),
    }


def isolated_record(exp_id: str, ledger: dict) -> dict:
    return next(record for record in ledger["experiments"] if record["experiment_id"] == exp_id)


def effect(deck: str, combined: dict, baseline: dict, ledger: dict) -> dict | None:
    exp_id = SELECTED[deck]
    if not exp_id:
        return None
    record = isolated_record(exp_id, ledger)
    isolated_delta = record["result_metrics"]["balance_delta"]
    combined_delta = round(
        combined[deck]["mean_matchup_balance_error"] - baseline[deck]["mean_matchup_balance_error"],
        6,
    )
    if isolated_delta < -0.00005 and combined_delta < -0.00005:
        classification = (
            "DELTA_STRENGTHENS"
            if abs(combined_delta) > abs(isolated_delta)
            else "DELTA_WEAKENS"
            if abs(combined_delta) < abs(isolated_delta)
            else "DELTA_PERSISTS"
        )
    elif abs(isolated_delta) <= 0.00005 and abs(combined_delta) <= 0.00005:
        classification = "DELTA_PERSISTS"
    elif isolated_delta * combined_delta < 0:
        classification = "DELTA_REVERSES"
    elif abs(combined_delta) > abs(isolated_delta):
        classification = "DELTA_STRENGTHENS"
    else:
        classification = "DELTA_WEAKENS"
    return {
        "experiment_id": exp_id,
        "isolated_balance_delta": isolated_delta,
        "combined_balance_delta": combined_delta,
        "classification": classification,
    }


def main() -> None:
    evidence = load(EVIDENCE)
    load(R1)
    load(R2)
    ledger = load(LEDGER)
    baseline = evidence["baseline_summary"]
    combined = evidence["combined_summary"]
    base_global = global_metrics(baseline)
    combined_global = global_metrics(combined)
    effects = {deck: effect(deck, combined, baseline, ledger) for deck in DECKS}
    per_deck = {}
    for deck in DECKS:
        per_deck[deck] = {
            "deck": DISPLAY[deck],
            "selected_experiment_id": SELECTED[deck] or "BASELINE",
            "baseline": baseline[deck],
            "combined": combined[deck],
            "win_rate_delta": round(combined[deck]["win_rate"] - baseline[deck]["win_rate"], 6),
            "balance_error_delta": round(
                combined[deck]["mean_matchup_balance_error"]
                - baseline[deck]["mean_matchup_balance_error"],
                6,
            ),
            "verdict": VERDICTS[deck],
            "promotion_eligibility": "PROMOTION_ELIGIBLE"
            if VERDICTS[deck] == "COMBINED_VALIDATION_PASSED"
            else "NOT_PROMOTION_ELIGIBLE",
        }
    enriched = dict(evidence)
    enriched["global_metrics"] = {
        "baseline": base_global,
        "combined": combined_global,
        "delta": {
            key: round(combined_global[key] - base_global[key], 6)
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
    enriched["interaction_effects"] = effects
    enriched["per_deck_validation"] = per_deck
    enriched["environment_decision"] = "COMBINED_ENVIRONMENT_IMPROVED"
    enriched["promotion_note"] = (
        "Recommendations only; no candidate or official baseline is promoted."
    )
    EVIDENCE.write_text(json.dumps(enriched, indent=2) + "\n", encoding="utf-8")

    def percent(value: float) -> str:
        return f"{value:.2%}"

    lines = [
        "# OBL-COMBINED-001 Results",
        "",
        "This is a combined validation experiment, not a promotion. The provisional environment uses the frozen Round 1 schedule for 4,500 games and compares directly with the banked `OBL-BASELINE-000` 4,500-game baseline.",
        "",
        "## Decision",
        "",
        "**COMBINED_ENVIRONMENT_IMPROVED**",
        "",
        f"Global Mean Matchup Balance Error improved from {percent(base_global['mean_matchup_balance_error'])} to {percent(combined_global['mean_matchup_balance_error'])} ({(combined_global['mean_matchup_balance_error'] - base_global['mean_matchup_balance_error']) * 100:+.2f} pp). This is not an automatic promotion: Krang and April remain mixed at the deck gate, and explicit promotion is separate.",
        "",
        "## Global metrics",
        "",
        "| Metric | OBL-BASELINE-000 | OBL-COMBINED-001 | Δ |",
        "|---|---:|---:|---:|",
    ]
    for key, label in [
        ("mean_matchup_balance_error", "Mean Matchup Balance Error"),
        ("median_matchup_deviation", "Median matchup deviation"),
        ("aggregate_win_rate_spread", "Aggregate deck WR spread"),
        ("aggregate_win_rate_stddev", "Aggregate deck WR standard deviation"),
        ("mean_first_player_result_rate", "Mean first-player result rate"),
        ("mean_ending_turn", "Mean ending turn"),
        ("median_ending_turn", "Median ending turn"),
    ]:
        b, c = base_global[key], combined_global[key]
        lines.append(
            f"| {label} | {percent(b) if 'turn' not in key else f'{b:.2f}'} | {percent(c) if 'turn' not in key else f'{c:.2f}'} | {(c - b) * 100:+.2f} pp |"
            if "turn" not in key
            else f"| {label} | {b:.2f} | {c:.2f} | {c - b:+.2f} |"
        )
    lines += [
        f"| >60/40 matchups | {base_global['over_60_40']} | {combined_global['over_60_40']} | {combined_global['over_60_40'] - base_global['over_60_40']:+d} |",
        f"| >70/30 matchups | {base_global['over_70_30']} | {combined_global['over_70_30']} | {combined_global['over_70_30'] - base_global['over_70_30']:+d} |",
        f"| Worst matchup | {DISPLAY[base_global['worst_matchup']['winner_side']]} over {DISPLAY[[d for d in base_global['worst_matchup']['decks'] if d != base_global['worst_matchup']['winner_side']][0]]} ({percent(base_global['worst_matchup']['winner_rate'])}) | {DISPLAY[combined_global['worst_matchup']['winner_side']]} over {DISPLAY[[d for d in combined_global['worst_matchup']['decks'] if d != combined_global['worst_matchup']['winner_side']][0]]} ({percent(combined_global['worst_matchup']['winner_rate'])}) | changed |",
        "",
        "## Per-deck comparison",
        "",
        "| Deck | Selected build | WR baseline→combined | Balance error baseline→combined | >60/40 baseline→combined | >70/30 baseline→combined | Worst matchup baseline→combined | Verdict | Promotion |",
        "|---|---|---:|---:|---:|---:|---|---|---|",
    ]
    for deck in DECKS:
        b, c = baseline[deck], combined[deck]
        p_w, c_w = b["extremes"]["worst_matchup"], c["extremes"]["worst_matchup"]
        lines.append(
            f"| {DISPLAY[deck]} | `{SELECTED[deck] or 'BASELINE'}` | {percent(b['win_rate'])}→{percent(c['win_rate'])} | {percent(b['mean_matchup_balance_error'])}→{percent(c['mean_matchup_balance_error'])} ({(c['mean_matchup_balance_error'] - b['mean_matchup_balance_error']) * 100:+.2f} pp) | {b['extremes']['over_60_40']}→{c['extremes']['over_60_40']} | {b['extremes']['over_70_30']}→{c['extremes']['over_70_30']} | {DISPLAY[p_w]}→{DISPLAY[c_w]} | {VERDICTS[deck]} | {'PROMOTION_ELIGIBLE' if VERDICTS[deck] == 'COMBINED_VALIDATION_PASSED' else 'NOT_PROMOTION_ELIGIBLE'} |"
        )
    lines += [
        "",
        "## Interaction effects",
        "",
        "| Selected candidate | Isolated Balance Δ | Combined Balance Δ | Classification |",
        "|---|---:|---:|---|",
    ]
    for deck in DECKS:
        if effects[deck]:
            item = effects[deck]
            lines.append(
                f"| `{item['experiment_id']}` | {item['isolated_balance_delta'] * 100:+.2f} pp | {item['combined_balance_delta'] * 100:+.2f} pp | {item['classification']} |"
            )
    lines += [
        "",
        "## Findings",
        "",
        "- Raphael and Shredder remained unchanged; the selected weaker-deck improvements reduced Raphael's aggregate WR from 76.78% to 75.11% and Shredder's from 73.00% to 72.44%.",
        "- April and Bebop & Rocksteady both improved materially in the combined environment, though April's isolated balance gain weakened.",
        "- Donatello R2A strengthened in the combined environment: its balance-error delta improved from -0.78 pp isolated to -2.22 pp combined.",
        "- Krang R2B reversed from a slight isolated improvement (-0.11 pp) to a slight combined regression (+0.11 pp), and remains mixed.",
        "- Casey R2B retained a favorable balance direction (-1.00 pp combined) and reduced >70/30 matchups 3→2.",
        "- Authoritative telemetry includes W/L/D, first-player result, ending turn, first-play proxies, battlefield presence, interaction casts, signature casts, runtime fingerprints, and matchup rates. Hand size, unused mana, flood/screw, stranded cards, engine activation, stabilization, lethal pressure, and loss causes remain unavailable and are not fabricated.",
        "",
        "No deck file was overwritten. No candidate was promoted. The next governance action remains explicit promotion review after any future authorization, not automatic baseline replacement.",
    ]
    (OBL / "COMBINED_001_RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
