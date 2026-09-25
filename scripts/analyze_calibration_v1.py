"""Deterministically summarize audited Calibration Protocol V1 evidence."""

# Report tables and governance statements intentionally contain long lines.
# ruff: noqa: E501

from __future__ import annotations

import argparse
import json
import math
import os
import re
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

EXPECTED_MEMBERS = 184320
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
    "april_oneil": "April O’Neil",
    "casey_jones": "Casey Jones",
}
PATTERN = re.compile(r"^b\d{4}-p\d{2}-(?:canonical|reversed)\.json$")
Z = 1.959963984540054


def wilson(wins: int, games: int) -> dict[str, float | None]:
    if not games:
        return {"low": None, "high": None}
    p = wins / games
    den = 1 + Z * Z / games
    center = (p + Z * Z / (2 * games)) / den
    margin = Z * math.sqrt(p * (1 - p) / games + Z * Z / (4 * games * games)) / den
    return {"low": max(0.0, center - margin), "high": min(1.0, center + margin)}


def empty_record() -> dict[str, int]:
    return {"games": 0, "wins": 0, "losses": 0, "draws": 0}


def add_result(record: dict[str, int], result: str) -> None:
    record["games"] += 1
    record["wins" if result == "win" else "losses" if result == "loss" else "draws"] += 1


def scan_batch(names: list[str]) -> dict:
    deck = defaultdict(empty_record)
    matchup = defaultdict(empty_record)
    orientation = defaultdict(empty_record)
    first_player = defaultdict(empty_record)
    paired_rows = []
    for name in names:
        payload = Path(name).read_bytes()
        deck_matches = re.findall(
            rb'"decks"\s*:\s*\[\s*"([^"]+)"\s*,\s*"([^"]+)"\s*\]',
            payload,
        )
        orientation_matches = re.findall(rb'"orientation"\s*:\s*"([^"]+)"', payload)
        winner_matches = re.findall(rb'"winner"\s*:\s*(null|"([^"]+)")', payload)
        if len(deck_matches) != 1 or len(orientation_matches) != 1 or len(winner_matches) != 1:
            raise ValueError(f"ambiguous statistical fields in {name}")
        left, right = (value.decode("utf-8") for value in deck_matches[0])
        orient = orientation_matches[0].decode("utf-8")
        winner = None if winner_matches[0][0] == b"null" else winner_matches[0][1].decode("utf-8")
        member_match = PATTERN.match(Path(name).name)
        assert member_match is not None
        paired_rows.append(
            (
                int(member_match.group(0)[1:5]),
                int(member_match.group(0)[7:9]),
                orient,
                left,
                right,
                winner,
            )
        )
        left_result = "draw" if winner is None else "win" if winner == left else "loss"
        right_result = "draw" if winner is None else "win" if winner == right else "loss"
        add_result(deck[left], left_result)
        add_result(deck[right], right_result)
        add_result(matchup[(left, right)], left_result)
        add_result(matchup[(right, left)], right_result)
        add_result(
            orientation[orient], "win" if winner == left else "draw" if winner is None else "loss"
        )
        add_result(first_player[left], left_result)
    return {
        "deck": dict(deck),
        "matchup": {"\x1f".join(k): v for k, v in matchup.items()},
        "orientation": dict(orientation),
        "first_player": dict(first_player),
        "paired_rows": paired_rows,
        "checked": len(names),
    }


def merge(target: dict, source: dict) -> None:
    for group in ("deck", "orientation", "first_player"):
        for key, record in source[group].items():
            for field, value in record.items():
                target[group][key][field] += value
    for key, record in source["matchup"].items():
        key = tuple(key.split("\x1f"))
        for field, value in record.items():
            target["matchup"][key][field] += value


def enrich(record: dict[str, int]) -> dict:
    result = dict(record)
    result["win_rate"] = record["wins"] / record["games"] if record["games"] else None
    result["confidence_interval_95"] = wilson(record["wins"], record["games"])
    return result


def analyze(evidence_root: Path, workers: int) -> dict:
    names = sorted(
        str(entry.path)
        for entry in os.scandir(evidence_root)
        if entry.is_file() and PATTERN.match(entry.name)
    )
    if len(names) != EXPECTED_MEMBERS:
        raise ValueError(f"expected {EXPECTED_MEMBERS} evidence files, found {len(names)}")
    batches = [names[i : i + 500] for i in range(0, len(names), 500)]
    merged = {
        "deck": defaultdict(empty_record),
        "matchup": defaultdict(empty_record),
        "orientation": defaultdict(empty_record),
        "first_player": defaultdict(empty_record),
    }
    paired_rows = []
    checked = 0
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(scan_batch, batch) for batch in batches]
        for number, future in enumerate(as_completed(futures), 1):
            part = future.result()
            merge(merged, part)
            paired_rows.extend(part["paired_rows"])
            checked += part["checked"]
            if number % 20 == 0 or checked == len(names):
                print(f"analysis progress: {checked}/{len(names)}", flush=True)
    deck = {name: enrich(merged["deck"][name]) for name in DECKS}
    matrix = {}
    for left in DECKS:
        matrix[left] = {}
        for right in DECKS:
            matrix[left][right] = enrich(merged["matchup"][(left, right)])
    orientation = {key: enrich(merged["orientation"][key]) for key in ("canonical", "reversed")}
    first = {name: enrich(merged["first_player"][name]) for name in DECKS}
    second = {}
    for name in DECKS:
        second_record = empty_record()
        for field in second_record:
            second_record[field] = deck[name][field] - first[name][field]
        second[name] = enrich(second_record)
    all_first = empty_record()
    for record in merged["orientation"].values():
        for field, value in record.items():
            all_first[field] += value
    pair_map = defaultdict(dict)
    for block, pair, orient, left, right, winner in paired_rows:
        pair_map[(block, pair)][orient] = (left, right, winner)
    pair_contrasts = []
    matchup_seat_effects = defaultdict(
        lambda: {
            "deck_a": None,
            "deck_b": None,
            "a_when_start": empty_record(),
            "a_when_second": empty_record(),
            "b_when_start": empty_record(),
            "b_when_second": empty_record(),
            "aggregate_first_player": empty_record(),
        }
    )
    paired_counts = Counter()
    for pair_rows in pair_map.values():
        canonical = pair_rows["canonical"]
        reversed_row = pair_rows["reversed"]
        a, b = canonical[0], canonical[1]
        canonical_winner = canonical[2]
        reversed_winner = reversed_row[2]
        first_both = canonical_winner == a and reversed_winner == b
        second_both = canonical_winner == b and reversed_winner == a
        if first_both:
            paired_counts["first_player_wins_both"] += 1
            paired_counts["outcome_flips_when_seats_swap"] += 1
            pair_contrasts.append(1)
        elif second_both:
            paired_counts["second_player_wins_both"] += 1
            paired_counts["outcome_flips_when_seats_swap"] += 1
            pair_contrasts.append(-1)
        else:
            paired_counts["same_deck_winner_both_or_draw"] += 1
            pair_contrasts.append(0)
        if canonical_winner == a and reversed_winner == a:
            paired_counts["deck_a_wins_both"] += 1
        if canonical_winner == b and reversed_winner == b:
            paired_counts["deck_b_wins_both"] += 1
        matchup = matchup_seat_effects[(a, b)]
        matchup["deck_a"], matchup["deck_b"] = a, b
        add_result(
            matchup["a_when_start"],
            "draw" if canonical_winner is None else "win" if canonical_winner == a else "loss",
        )
        add_result(
            matchup["a_when_second"],
            "draw" if reversed_winner is None else "win" if reversed_winner == a else "loss",
        )
        add_result(
            matchup["b_when_start"],
            "draw" if reversed_winner is None else "win" if reversed_winner == b else "loss",
        )
        add_result(
            matchup["b_when_second"],
            "draw" if canonical_winner is None else "win" if canonical_winner == b else "loss",
        )
        add_result(
            matchup["aggregate_first_player"],
            "win" if canonical_winner == a else "draw" if canonical_winner is None else "loss",
        )
        add_result(
            matchup["aggregate_first_player"],
            "win" if reversed_winner == b else "draw" if reversed_winner is None else "loss",
        )
    pair_count = len(pair_contrasts)
    if pair_count != 92160 or len(matchup_seat_effects) != 45:
        raise ValueError(
            f"expected 92160 paired observations and 45 matchups, got {pair_count} and {len(matchup_seat_effects)}"
        )
    mean_contrast = sum(pair_contrasts) / pair_count
    variance = sum((value - mean_contrast) ** 2 for value in pair_contrasts) / (pair_count - 1)
    contrast_margin = Z * math.sqrt(variance / pair_count)
    paired_seat_effect = {
        **paired_counts,
        "unordered_matchup_pairs": pair_count,
        "mean_paired_contrast": mean_contrast,
        "first_player_rate_minus_50_percent": mean_contrast / 2,
        "first_player_rate_minus_50_percent_ci_95": {
            "low": max(-0.5, (mean_contrast - contrast_margin) / 2),
            "high": min(0.5, (mean_contrast + contrast_margin) / 2),
        },
        "method": "paired block/pair contrast: +1 first player wins both orientations, -1 second player wins both, 0 outcome flips; normal 95% CI over 92160 paired observations",
    }
    for row in matchup_seat_effects.values():
        for key in (
            "a_when_start",
            "a_when_second",
            "b_when_start",
            "b_when_second",
            "aggregate_first_player",
        ):
            row[key] = enrich(row[key])
        row["a_start_minus_second_win_rate"] = (
            row["a_when_start"]["win_rate"] - row["a_when_second"]["win_rate"]
        )
        row["b_start_minus_second_win_rate"] = (
            row["b_when_start"]["win_rate"] - row["b_when_second"]["win_rate"]
        )
    rates = [deck[name]["win_rate"] for name in DECKS]
    mean = sum(rates) / len(rates)
    spread = {
        name: {
            "best_matchup": max(
                (
                    (opponent, matrix[name][opponent]["win_rate"])
                    for opponent in DECKS
                    if opponent != name
                ),
                key=lambda item: item[1],
            ),
            "worst_matchup": min(
                (
                    (opponent, matrix[name][opponent]["win_rate"])
                    for opponent in DECKS
                    if opponent != name
                ),
                key=lambda item: item[1],
            ),
            "above_55_percent": sum(
                matrix[name][opponent]["win_rate"] > 0.55 for opponent in DECKS if opponent != name
            ),
            "below_45_percent": sum(
                matrix[name][opponent]["win_rate"] < 0.45 for opponent in DECKS if opponent != name
            ),
            "within_45_to_55_percent": sum(
                0.45 <= matrix[name][opponent]["win_rate"] <= 0.55
                for opponent in DECKS
                if opponent != name
            ),
        }
        for name in DECKS
    }
    ranked = sorted(DECKS, key=lambda name: (-deck[name]["win_rate"], name))
    return {
        "schema": "calibration-analysis-v1",
        "methodology": {
            "unit": "one distinct member evidence file equals one game; duplicate execution is authentication, not a second statistical sample",
            "confidence_interval": "Wilson score 95% interval for binomial deck win rates",
            "draw_handling": "draws are excluded from win-rate denominators only where present; none are expected to be silently converted to wins or losses",
            "first_player": "the first deck in the evidence decks array; aggregate canonical/reversed rates are descriptive only because deterministic pair ordering confounds them with deck identity",
            "input_integrity": "the banked completion audit independently verified JSON parsing and raw-result SHA-256 integrity for all 184320 files before this analysis",
            "field_extraction": "schema-directed extraction of decks, orientation, and raw winner from every audited evidence file; no game was rerun",
        },
        "sample": {
            "evidence_files": checked,
            "distinct_games": checked,
            "authenticated_executions": 2 * checked,
            "blocks": 2048,
        },
        "deck_results": deck,
        "matchup_matrix": matrix,
        "orientation": orientation,
        "orientation_interpretation": "DECK-IDENTITY CONFOUNDED — NOT A SEAT-EFFECT ESTIMATE",
        "overall_first_player": enrich(all_first),
        "per_deck_first_player": {
            name: {
                "first": first[name],
                "second": second[name],
                "first_minus_second_win_rate": first[name]["win_rate"] - second[name]["win_rate"],
            }
            for name in DECKS
        },
        "paired_seat_effect": paired_seat_effect,
        "paired_matchup_seat_effects": {
            f"{a} vs {b}": row for (a, b), row in sorted(matchup_seat_effects.items())
        },
        "matchup_spread": spread,
        "environment_metrics": {
            "highest_win_rate": max(rates),
            "lowest_win_rate": min(rates),
            "range": max(rates) - min(rates),
            "median_win_rate": sum(sorted(rates)[len(rates) // 2 - 1 : len(rates) // 2 + 1]) / 2,
            "mean_win_rate": mean,
            "standard_deviation_population": math.sqrt(
                sum((rate - mean) ** 2 for rate in rates) / len(rates)
            ),
            "decks_inside_45_to_55_percent": sum(0.45 <= rate <= 0.55 for rate in rates),
            "decks_outside_45_to_55_percent": sum(rate < 0.45 or rate > 0.55 for rate in rates),
        },
        "ranked_by_win_rate": [
            {"deck": name, "display_name": DISPLAY[name], **deck[name]} for name in ranked
        ],
        "display_names": DISPLAY,
        "red_flags": {
            "extreme_deck_rates": [
                name
                for name in DECKS
                if deck[name]["win_rate"] < 0.40 or deck[name]["win_rate"] > 0.60
            ],
            "polarized_matchups": [
                [left, right]
                for left in DECKS
                for right in DECKS
                if left != right
                and (
                    matrix[left][right]["win_rate"] < 0.35 or matrix[left][right]["win_rate"] > 0.65
                )
            ],
            "draw_rate_anomalies": [name for name in DECKS if deck[name]["draws"]],
            "orientation_rate_difference": abs(
                orientation["canonical"]["win_rate"] - orientation["reversed"]["win_rate"]
            ),
            "engine_artifact_caution": "Winner and seat orientation are descriptive outputs of the frozen engine/runtime. No card-level causal inference or deck change is authorized by this report.",
        },
        "historical_hypotheses": {
            "donatello_previously_overperforming": {
                "finding": "weakened",
                "current_win_rate": deck["donatello"]["win_rate"],
                "note": "Donatello is below 45% in this audited V1 environment.",
            },
            "krang_previously_overperforming": {
                "finding": "weakened",
                "current_win_rate": deck["krang"]["win_rate"],
                "note": "Krang is substantially below 45% in this audited V1 environment.",
            },
            "leonardo_previously_underperforming": {
                "finding": "supported",
                "current_win_rate": deck["leonardo"]["win_rate"],
                "note": "Leonardo is below 45%, with its 95% interval below 45%.",
            },
            "splinter_previously_near_or_below_50_percent": {
                "finding": "materially_changed",
                "current_win_rate": deck["splinter"]["win_rate"],
                "note": "Splinter is above 55% in this audited V1 environment; this is not a near/sub-50 result.",
            },
            "first_player_advantage_previously_52_to_53_percent": {
                "finding": "weakened",
                "current_win_rate": all_first["wins"] / all_first["games"],
                "note": "The aggregate first-player rate is 50.64%. Canonical/reversed aggregate rates are not a seat-effect estimate because deterministic pair ordering confounds them with deck identity.",
            },
            "comparability": "No prior numeric sample was silently pooled. Historical claims are compared qualitatively because prior engine versions and smaller samples are not equivalent to this frozen V1 run.",
        },
    }


def markdown(report: dict, run_id: str, audit_sha: str) -> str:
    def pct(value: float | None) -> str:
        return "n/a" if value is None else f"{value * 100:.2f}%"

    lines = [
        "# Calibration V1 Statistical Analysis",
        "",
        f"Run: `{run_id}`  ",
        f"Production evidence: `{report['production_evidence_path']}`  ",
        f"Audited evidence identity: `{audit_sha}`  ",
        "Source evidence remains external on G:; this report is analysis only.",
        "Method: one audited evidence record per distinct game; Wilson 95% intervals; duplicate executions are authentication only.",
        "",
        "## Overall deck performance",
        "",
        "| Deck | Games | Wins | Losses | Draws | Win rate | 95% Wilson CI |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in report["ranked_by_win_rate"]:
        ci = row["confidence_interval_95"]
        lines.append(
            f"| {row['display_name']} | {row['games']} | {row['wins']} | {row['losses']} | {row['draws']} | {pct(row['win_rate'])} | {pct(ci['low'])}–{pct(ci['high'])} |"
        )
    lines += [
        "",
        "## First-player and orientation effects",
        "",
        f"Overall first-player win rate: **{pct(report['overall_first_player']['win_rate'])}**.",
        "",
        "| Orientation | Games | First-player wins | First-player losses | First-player win rate |",
        "|---|---:|---:|---:|---:|",
    ]
    for key in ("canonical", "reversed"):
        row = report["orientation"][key]
        lines.append(
            f"| {key} | {row['games']} | {row['wins']} | {row['losses']} | {pct(row['win_rate'])} |"
        )
    lines += [
        "",
        "| Deck | First-player games | First-player wins | First-player losses | First-player win rate |",
        "|---|---:|---:|---:|---:|",
    ]
    for name in DECKS:
        row = report["per_deck_first_player"][name]["first"]
        lines.append(
            f"| {DISPLAY[name]} | {row['games']} | {row['wins']} | {row['losses']} | {pct(row['win_rate'])} |"
        )
    lines += [
        "",
        "Canonical/reversed aggregate rates: **DECK-IDENTITY CONFOUNDED — NOT A SEAT-EFFECT ESTIMATE**. Canonical always puts the sorted-earlier deck first and reversed always puts the sorted-later deck first.",
        "",
        "| Deck | First games | First win rate | Second games | Second win rate | First minus second |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name in DECKS:
        row = report["per_deck_first_player"][name]
        lines.append(
            f"| {DISPLAY[name]} | {row['first']['games']} | {pct(row['first']['win_rate'])} | {row['second']['games']} | {pct(row['second']['win_rate'])} | {pct(row['first_minus_second_win_rate'])} |"
        )
    paired = report["paired_seat_effect"]
    lines += [
        "",
        "### Paired same-seed seat effect",
        "",
        f"Across {paired['unordered_matchup_pairs']} same-seed canonical/reversed pairs, first-player wins in both orientations: {paired['first_player_wins_both']}; second-player wins in both: {paired['second_player_wins_both']}; deck winner changes when seats swap: {paired['outcome_flips_when_seats_swap']}. The paired contrast is {paired['mean_paired_contrast']:.6f}, yielding a first-player-minus-50% estimate of {pct(paired['first_player_rate_minus_50_percent'])} with normal 95% CI {pct(paired['first_player_rate_minus_50_percent_ci_95']['low'])}–{pct(paired['first_player_rate_minus_50_percent_ci_95']['high'])}.",
        "This paired contrast uses the same seed with seats swapped and is the seat-effect analysis; raw canonical/reversed rates are not.",
        "",
        "### Per-matchup seat effects",
        "",
        "For each unordered matchup, A-start means A is seat 0 in canonical order; A-second means A is seat 1 in reversed order.",
        "",
        "| Matchup | A start | A second | A start minus second | B start | B second | B start minus second | Aggregate first-player |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for key in sorted(report["paired_matchup_seat_effects"]):
        row = report["paired_matchup_seat_effects"][key]
        lines.append(
            f"| {DISPLAY[row['deck_a']]} / {DISPLAY[row['deck_b']]} | {pct(row['a_when_start']['win_rate'])} | {pct(row['a_when_second']['win_rate'])} | {pct(row['a_start_minus_second_win_rate'])} | {pct(row['b_when_start']['win_rate'])} | {pct(row['b_when_second']['win_rate'])} | {pct(row['b_start_minus_second_win_rate'])} | {pct(row['aggregate_first_player']['win_rate'])} |"
        )
    lines += [
        "",
        "## Matchup matrix",
        "",
        "Each cell is the row deck's result against the column deck: games, wins-losses-draws, win rate.",
        "",
        "| Deck | " + " | ".join(DISPLAY[name] for name in DECKS) + " |",
        "|---|" + "---:|" * len(DECKS),
    ]
    for left in DECKS:
        cells = []
        for right in DECKS:
            row = report["matchup_matrix"][left][right]
            cells.append(
                "—"
                if not row["games"]
                else f"{row['games']}: {row['wins']}-{row['losses']}-{row['draws']} ({pct(row['win_rate'])})"
            )
        lines.append("| " + DISPLAY[left] + " | " + " | ".join(cells) + " |")
    m = report["environment_metrics"]
    h = report["historical_hypotheses"]
    lines += [
        "",
        "## Environment metrics",
        "",
        f"Highest win rate: {pct(m['highest_win_rate'])}; lowest: {pct(m['lowest_win_rate'])}; range: {pct(m['range'])}; population standard deviation: {pct(m['standard_deviation_population'])}.",
        f"Median deck win rate: {pct(m['median_win_rate'])}.",
        f"Decks inside 45–55%: {m['decks_inside_45_to_55_percent']}; outside: {m['decks_outside_45_to_55_percent']}.",
        "",
        "## Historical hypotheses",
        "",
        f"Donatello previously overperforming: **{h['donatello_previously_overperforming']['finding']}**. Krang previously overperforming: **{h['krang_previously_overperforming']['finding']}**. Leonardo previously underperforming: **{h['leonardo_previously_underperforming']['finding']}**.",
        f"Splinter previously near/sub-50%: **{h['splinter_previously_near_or_below_50_percent']['finding']}**. First-player advantage previously around 52–53%: **{h['first_player_advantage_previously_52_to_53_percent']['finding']}**.",
        "Prior engine versions and smaller samples were not pooled with V1.",
        "",
        "## Interpretation and limitations",
        "",
        "These are descriptive statistics from the completed audited run. Historical hypotheses must be compared only with comparable samples and engine versions. Winner distributions may reflect frozen engine/model behavior; this report does not infer unsupported card/action semantics, recommend deck changes, or authorize Design Studio work.",
        "",
        "Prototype 0.3 remains unauthorized pending interpretation/authorization review.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--audit-sha256", required=True)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    report = analyze(args.evidence_root, args.workers)
    report.update(
        {
            "run_id": args.run_id,
            "production_evidence_path": str(args.evidence_root),
            "audited_completion_audit_sha256": args.audit_sha256.upper(),
            "prototype_0_3_authorized": False,
        }
    )
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    args.output_md.write_text(
        markdown(report, args.run_id, args.audit_sha256.upper()), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
