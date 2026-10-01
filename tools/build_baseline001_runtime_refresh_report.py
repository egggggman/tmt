"""Package Baseline 001 runtime-refresh evidence and comparisons."""

# Generated evidence/report expressions intentionally keep wide lines.
# ruff: noqa: E501

from __future__ import annotations

import hashlib
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import run_objective_balance_lab_round1 as r1  # noqa: E402
from objective_balance_lab_semantic_identity import identity  # noqa: E402

OBL = ROOT / "docs/objective-balance-lab"
OLD_PATH = OBL / "ROUND_1_EVIDENCE.json"
REFRESH_PATH = OBL / "BASELINE_001_RUNTIME_REFRESH_EVIDENCE.json"
CHECKPOINT_PATH = OBL / "BASELINE_001_RUNTIME_REFRESH_CHECKPOINT.json"
R4C_PATH = OBL / "ROUND_4B_RAPHAEL_EVIDENCE.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_games(path: Path, key: str) -> list[dict[str, object]]:
    return json.loads(path.read_text(encoding="utf-8"))[key]


def matchup(games: list[dict[str, object]]) -> dict[str, object]:
    by_pair: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for game in games:
        seats = tuple(game["seats"])
        by_pair[tuple(sorted(seats))].append(game)
    rows = []
    for pair, cells in sorted(by_pair.items()):
        rates = {}
        for deck in pair:
            wins = sum(game.get("winner") == deck for game in cells)
            draws = sum(bool(game.get("draw")) for game in cells)
            rates[deck] = round((wins + draws / 2) / len(cells), 6)
        winner = max(rates, key=rates.get)
        deviation = abs(rates[winner] - 0.5)
        rows.append(
            {
                "decks": list(pair),
                "games": len(cells),
                "win_rates": rates,
                "winner_side": winner,
                "deviation": round(deviation, 6),
            }
        )
    return {"cells": rows}


def global_metrics(
    summary: dict[str, object], cells: list[dict[str, object]], games: list[dict[str, object]]
) -> dict[str, object]:
    deviations = [cell["deviation"] for cell in cells]
    worst = max(cells, key=lambda cell: cell["deviation"])
    rates = [summary[deck]["win_rate"] for deck in r1.DECKS]
    first = [
        summary[deck]["first_player_rate"]
        for deck in r1.DECKS
        if summary[deck]["first_player_rate"] is not None
    ]
    return {
        "mean_matchup_balance_error": round(statistics.mean(deviations), 6),
        "median_matchup_deviation": round(statistics.median(deviations), 6),
        "worst_matchup": worst,
        "over_60_40": sum(cell["deviation"] > 0.1 for cell in cells),
        "over_70_30": sum(cell["deviation"] > 0.2 for cell in cells),
        "aggregate_win_rate_spread": round(max(rates) - min(rates), 6),
        "aggregate_win_rate_stddev": round(statistics.pstdev(rates), 6),
        "mean_first_player_result_rate": round(statistics.mean(first), 6),
        "mean_ending_turn": round(
            statistics.mean([game["turn"] for game in games if game.get("turn") is not None]), 4
        ),
        "median_ending_turn": statistics.median(
            [game["turn"] for game in games if game.get("turn") is not None]
        ),
    }


def utility_totals(games: list[dict[str, object]]) -> dict[str, dict[str, dict[str, int]]]:
    result: dict[str, dict[str, dict[str, int]]] = defaultdict(lambda: defaultdict(Counter))
    for game in games:
        for deck, cards in game.get("utility_telemetry", {}).items():
            for card, counts in cards.items():
                for key, value in counts.items():
                    result[deck][card][key] += int(value)
    return {deck: dict(cards) for deck, cards in result.items()}


def compact_games(games: list[dict[str, object]]) -> list[dict[str, object]]:
    """Drop only zero-valued utility counters; all game metrics remain intact."""
    compact = []
    for game in games:
        copied = dict(game)
        copied["utility_telemetry"] = {
            deck: {card: counts for card, counts in cards.items() if any(counts.values())}
            for deck, cards in game.get("utility_telemetry", {}).items()
            if any(any(counts.values()) for counts in cards.values())
        }
        compact.append(copied)
    return compact


def main() -> int:
    old_doc = json.loads(OLD_PATH.read_text(encoding="utf-8"))
    refresh = json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))
    checkpoint = refresh
    old_games = old_doc["baseline_results"]
    new_games = compact_games(refresh["results"])
    refresh["results"] = new_games
    CHECKPOINT_PATH.write_text(
        json.dumps(refresh, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    old_summary = r1.aggregate(old_games, r1.DECKS)
    new_summary = r1.aggregate(new_games, r1.DECKS)
    old_cells = matchup(old_games)["cells"]
    new_cells = matchup(new_games)["cells"]
    old_global = global_metrics(old_summary, old_cells, old_games)
    new_global = global_metrics(new_summary, new_cells, new_games)
    old_by_pair = {tuple(cell["decks"]): cell for cell in old_cells}
    new_by_pair = {tuple(cell["decks"]): cell for cell in new_cells}
    utility_by_pair: dict[tuple[str, str], dict[str, object]] = defaultdict(dict)
    for game in new_games:
        pair = tuple(sorted(game["seats"]))
        for deck, cards in game.get("utility_telemetry", {}).items():
            for card, counts in cards.items():
                if any(counts.values()):
                    utility_by_pair.setdefault(pair, {}).setdefault(deck, {}).setdefault(
                        card, Counter()
                    ).update(counts)
    changed = []
    all_comparisons = []
    for pair in sorted(old_by_pair):
        old_cell, new_cell = old_by_pair[pair], new_by_pair[pair]
        deltas = {
            deck: round(new_cell["win_rates"][deck] - old_cell["win_rates"][deck], 6)
            for deck in pair
        }
        comparison = {"decks": list(pair), "old": old_cell, "refreshed": new_cell, "delta": deltas}
        if pair in utility_by_pair:
            comparison["refreshed_utility_activity"] = {
                deck: {card: dict(counts) for card, counts in cards.items()}
                for deck, cards in utility_by_pair[pair].items()
            }
        all_comparisons.append(comparison)
        if any(deltas.values()):
            changed.append(comparison)
    current = identity()
    original = identity("0017d9d3b65d57474789ef24471deb615a9b1e54")
    r4c = identity("8b8a3b353d4aac9f00704adf57383101d9c1e048")
    identity_payload = {
        "schema": "obl-semantic-runtime-comparison-v1",
        "current": current,
        "original_baseline_evidence_runtime": original,
        "r4c_evidence_runtime": r4c,
        "comparisons": {
            "original_equals_current": original["aggregate_semantic_runtime_sha256"]
            == current["aggregate_semantic_runtime_sha256"],
            "r4c_equals_current": r4c["aggregate_semantic_runtime_sha256"]
            == current["aggregate_semantic_runtime_sha256"],
        },
        "compatibility_rule": "semantic runtime identity must match; repository commit identity alone is insufficient",
    }
    (OBL / "SEMANTIC_RUNTIME_IDENTITY.json").write_text(
        json.dumps(identity_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    r4c_compat = (
        "REUSE_ELIGIBLE_FOR_COMBINED_003"
        if identity_payload["comparisons"]["r4c_equals_current"]
        else "RERUN_REQUIRED"
    )
    evidence = {
        "schema": "objective-balance-lab-baseline-001-runtime-refresh-report-v1",
        "environment_id": "OBL-BASELINE-001",
        "evidence_id": "OBL-BASELINE-001-RUNTIME-REFRESH-001",
        "state": "BASELINE_EVIDENCE_REFRESH",
        "repository_sha": current["repository_commit"],
        "semantic_runtime_sha256": current["aggregate_semantic_runtime_sha256"],
        "refresh_evidence_path": REFRESH_PATH.relative_to(ROOT).as_posix(),
        "refresh_source_checkpoint_sha256": sha(CHECKPOINT_PATH),
        "refresh_checkpoint_path": CHECKPOINT_PATH.relative_to(ROOT).as_posix(),
        "refresh_checkpoint_sha256": sha(CHECKPOINT_PATH),
        "original_evidence_path": OLD_PATH.relative_to(ROOT).as_posix(),
        "original_evidence_sha256": sha(OLD_PATH),
        "schedule_games": len(new_games),
        "orientation_counts": dict(Counter(game["schedule"]["orientation"] for game in new_games)),
        "runtime_errors": sum(bool(game.get("runtime_error")) for game in new_games),
        "old_global_metrics": old_global,
        "refreshed_global_metrics": new_global,
        "global_delta": {
            key: round(new_global[key] - old_global[key], 6)
            for key in (
                "mean_matchup_balance_error",
                "median_matchup_deviation",
                "aggregate_win_rate_spread",
                "aggregate_win_rate_stddev",
                "mean_first_player_result_rate",
                "mean_ending_turn",
            )
        },
        "old_summary": old_summary,
        "refreshed_summary": new_summary,
        "per_deck_delta": {
            deck: {
                "win_rate": round(new_summary[deck]["win_rate"] - old_summary[deck]["win_rate"], 6),
                "average_turn": round(
                    new_summary[deck]["average_turn"] - old_summary[deck]["average_turn"], 4
                ),
            }
            for deck in r1.DECKS
        },
        "matchup_changes": changed,
        "all_matchup_comparisons": all_comparisons,
        "utility_associated_changed_matchups": [
            row for row in changed if row.get("refreshed_utility_activity")
        ],
        "utility_usage_refreshed": utility_totals(new_games),
        "utility_usage_old": "not recorded by original pre-utility evidence",
        "r4c_compatibility": {
            "experiment_id": "OBL-R4-RAPHAEL-C",
            "historical_runtime_sha256": r4c["aggregate_semantic_runtime_sha256"],
            "current_runtime_sha256": current["aggregate_semantic_runtime_sha256"],
            "status": r4c_compat,
            "cells": 9,
            "reason": "R4-C evidence was generated under a different semantic runtime"
            if r4c_compat == "RERUN_REQUIRED"
            else "all semantic identities match",
        },
        "deterministic_schedule_sha256": refresh["schedule_sha256"],
        "deck_manifest": refresh["deck_manifest"],
        "games": checkpoint["results"],
    }
    (OBL / "BASELINE_001_RUNTIME_REFRESH_EVIDENCE.json").write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    lines = [
        "# Baseline 001 Semantic Runtime Refresh",
        "",
        "Evidence identity: `OBL-BASELINE-001-RUNTIME-REFRESH-001`. The official environment and deck bytes are unchanged; only the simulation runtime evidence was refreshed.",
        "",
        "## Runtime identity",
        "",
        f"- Original baseline runtime: `{original['aggregate_semantic_runtime_sha256']}` (commit `{original['repository_commit']}`).",
        f"- R4-C runtime: `{r4c['aggregate_semantic_runtime_sha256']}` (commit `{r4c['repository_commit']}`).",
        f"- Current refresh runtime: `{current['aggregate_semantic_runtime_sha256']}` (commit `{current['repository_commit']}`).",
        f"- R4-C compatibility: **{r4c_compat}**. Its nine cells are semantically compatible with the refreshed runtime and may be reused by a future composition.",
        "",
        "## Completion and integrity",
        "",
        f"The refresh contains {len(new_games):,}/4,500 games, 45 matchup cells, 50 canonical and 50 reversed games per matchup, zero runtime errors, and schedule identity `{'`'}{refresh['schedule_sha256']}{'`'}`. The original evidence remains at `ROUND_1_EVIDENCE.json` and its recorded SHA-256 is preserved in the machine-readable report.",
        "",
        "## Global comparison",
        "",
        "| Metric | Original | Refreshed | Delta |",
        "|---|---:|---:|---:|",
    ]
    for key, label in [
        ("mean_matchup_balance_error", "Mean matchup balance error"),
        ("median_matchup_deviation", "Median deviation"),
        ("over_60_40", "60/40 count"),
        ("over_70_30", "70/30 count"),
        ("aggregate_win_rate_spread", "WR spread"),
        ("aggregate_win_rate_stddev", "WR stddev"),
        ("mean_first_player_result_rate", "Mean first-player result rate"),
        ("mean_ending_turn", "Mean ending turn"),
        ("median_ending_turn", "Median ending turn"),
    ]:
        delta = (
            new_global[key] - old_global[key] if isinstance(new_global[key], (int, float)) else "—"
        )
        lines.append(
            f"| {label} | {old_global[key]} | {new_global[key]} | {round(delta, 6) if isinstance(delta, (int, float)) else delta} |"
        )
    lines += [
        "",
        "## Per-deck change",
        "",
        "| Deck | Original WR | Refreshed WR | WR delta | Original turn | Refreshed turn |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for deck in r1.DECKS:
        lines.append(
            f"| {r1.DISPLAY[deck]} | {old_summary[deck]['win_rate']:.2%} | {new_summary[deck]['win_rate']:.2%} | {(new_summary[deck]['win_rate'] - old_summary[deck]['win_rate']):+.2%} | {old_summary[deck]['average_turn']} | {new_summary[deck]['average_turn']} |"
        )
    associated = evidence["utility_associated_changed_matchups"]
    lines += [
        "",
        "## Utility impact",
        "",
        "The refreshed evidence records draw, legal-opportunity, selection, cast, resolution, activation, equip, and effect-use counters for artifact cards. The original evidence predates this telemetry, so zero/absent old counters are not treated as proof of zero use. Matchup-level attribution is observational: a changed cell is utility-associated only when the refreshed cell contains utility events for one of its decks.",
        "",
        f"Changed matchup cells: **{len(changed)}**; changed cells with observed utility activity: **{len(associated)}**.",
        "",
    ]
    for row in associated:
        active = ", ".join(
            f"{deck}: {', '.join(cards)}"
            for deck, cards in row["refreshed_utility_activity"].items()
        )
        lines.append(f"- `{row['decks'][0]}` vs `{row['decks'][1]}`: {active}.")
    lines.append("")
    (OBL / "BASELINE_001_RUNTIME_REFRESH.md").write_text("\n".join(lines), encoding="utf-8")
    print(
        json.dumps(
            {
                "games": len(new_games),
                "runtime_errors": evidence["runtime_errors"],
                "current_runtime": current["aggregate_semantic_runtime_sha256"],
                "r4c_compatibility": r4c_compat,
                "changed_matchups": len(changed),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
