"""Package the new-runtime Baseline 003 control without changing historical authority."""

# Generated Markdown rows and evidence paths are deliberately kept as literal lines.
# ruff: noqa: E501

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
sys.path.insert(0, str(ROOT / "tools"))

import build_combined003_runtime_compatible as metrics  # noqa: E402
import run_objective_balance_lab_baseline003_runtime_refresh as run  # noqa: E402
import run_objective_balance_lab_round1 as r1  # noqa: E402
import run_objective_balance_lab_round5 as r5  # noqa: E402

EVIDENCE = OBL / "BASELINE_003_RUNTIME_REFRESH_EVIDENCE.json"
REPORT = OBL / "BASELINE_003_RUNTIME_REFRESH.md"
REPLAY_PAIRS = (
    ("krang", "shredder"),
    ("krang", "raphael"),
    ("april_oneil", "krang"),
    ("leonardo", "shredder"),
    ("april_oneil", "raphael"),
    ("bebop_rocksteady", "donatello"),
)


def by_schedule(games: list[dict]) -> dict[str, dict]:
    result = {r5.digest(game["schedule"]): game for game in games}
    assert len(result) == len(games)
    return result


def compare_cells(old_games: list[dict], new_games: list[dict]) -> list[dict]:
    old_map = by_schedule(old_games)
    new_map = by_schedule(new_games)
    assert old_map.keys() == new_map.keys()
    old_cells = metrics.matchup_rows(old_games)
    new_cells = metrics.matchup_rows(new_games)
    old_by_pair = {tuple(row["decks"]): row for row in old_cells}
    new_by_pair = {tuple(row["decks"]): row for row in new_cells}
    by_pair: dict[tuple[str, str], list[str]] = defaultdict(list)
    for key, game in new_map.items():
        by_pair[tuple(sorted(game["schedule"]["pair"]))].append(key)
    result = []
    for pair in sorted(by_pair):
        prior, current = old_by_pair[pair], new_by_pair[pair]
        old_wld = {
            "wins": {
                deck: sum(old_map[key]["winner"] == deck for key in by_pair[pair]) for deck in pair
            },
            "draws": sum(bool(old_map[key]["draw"]) for key in by_pair[pair]),
        }
        new_wld = {
            "wins": {
                deck: sum(new_map[key]["winner"] == deck for key in by_pair[pair]) for deck in pair
            },
            "draws": sum(bool(new_map[key]["draw"]) for key in by_pair[pair]),
        }
        old_wld["losses"] = {deck: 100 - old_wld["wins"][deck] - old_wld["draws"] for deck in pair}
        new_wld["losses"] = {deck: 100 - new_wld["wins"][deck] - new_wld["draws"] for deck in pair}
        outcome_changes = sum(
            (old_map[key]["winner"], old_map[key]["draw"])
            != (new_map[key]["winner"], new_map[key]["draw"])
            for key in by_pair[pair]
        )
        turn_changes = sum(old_map[key]["turn"] != new_map[key]["turn"] for key in by_pair[pair])
        result.append(
            {
                "decks": list(pair),
                "historical_win_rates": prior["win_rates"],
                "refreshed_win_rates": current["win_rates"],
                "historical_wld": old_wld,
                "refreshed_wld": new_wld,
                "win_rate_delta": {
                    deck: round(current["win_rates"][deck] - prior["win_rates"][deck], 6)
                    for deck in pair
                },
                "historical_deviation": prior["deviation"],
                "refreshed_deviation": current["deviation"],
                "outcome_changed_games": outcome_changes,
                "ending_turn_changed_games": turn_changes,
                "cell_result_changed": old_wld != new_wld,
            }
        )
    assert len(result) == 45
    return result


def replay_sample(games: list[dict], paths: dict[str, str], schedule: list[dict]) -> list[dict]:
    by_pair = {}
    for index, item in enumerate(schedule, 1):
        pair = tuple(sorted(item["pair"]))
        by_pair.setdefault(pair, index)
    r1._init_worker(r1.catalog())
    samples = []
    for pair in REPLAY_PAIRS:
        index = by_pair[pair]
        original = games[index - 1]
        replay = r1._run_one((index, paths, schedule[index - 1]))
        assert replay["runtime_error"] is None
        assert replay["schedule"] == original["schedule"]
        assert replay["runtime_fingerprint"] == original["runtime_fingerprint"]
        assert (replay["winner"], replay["draw"], replay["turn"]) == (
            original["winner"],
            original["draw"],
            original["turn"],
        )
        samples.append(
            {
                "decks": list(pair),
                "schedule": original["schedule"],
                "runtime_fingerprint": original["runtime_fingerprint"],
                "result": {
                    "winner": original["winner"],
                    "draw": original["draw"],
                    "turn": original["turn"],
                },
                "status": "REPLAY_MATCHED",
            }
        )
    return samples


def build() -> dict:
    manifest, schedule, paths, runtime = run.preflight()
    checkpoint = json.loads(run.CHECKPOINT.read_text(encoding="utf-8"))
    expected = run.checkpoint_template(manifest, runtime)
    run.verify_checkpoint(checkpoint, expected, schedule)
    games = checkpoint["results"]
    assert len(games) == 4500
    old = json.loads(run.HISTORICAL.read_text(encoding="utf-8"))
    old_games = old["combined_games"]
    assert len(old_games) == 4500
    old_rows = metrics.matchup_rows(old_games)
    new_rows = metrics.matchup_rows(games)
    old_summary = r1.aggregate(old_games, r1.DECKS)
    new_summary = r1.aggregate(games, r1.DECKS)
    old_metrics = metrics.summary_metrics(old_summary, old_rows, old_games)
    new_metrics = metrics.summary_metrics(new_summary, new_rows, games)
    assert old_metrics == old["combined_005_global_metrics"]
    old_decks = metrics.per_deck(old_summary, old_rows)
    new_decks = metrics.per_deck(new_summary, new_rows)
    comparisons = compare_cells(old_games, games)
    changed = [row for row in comparisons if row["cell_result_changed"]]
    replay = replay_sample(games, paths, schedule)
    krang = {**new_decks["krang"], **new_summary["krang"]}
    deltas = {
        key: round(new_metrics[key] - old_metrics[key], 6)
        for key in new_metrics
        if key != "worst_matchup"
    }
    evidence = {
        "schema": "obl-baseline-003-runtime-refresh-v1",
        "environment_id": "OBL-BASELINE-003",
        "evidence_id": run.EVIDENCE_ID,
        "state": "BASELINE_EVIDENCE_REFRESH",
        "repository_sha": run.BASE,
        "semantic_runtime_sha256": run.RUNTIME,
        "old_semantic_runtime_sha256": run.OLD_RUNTIME,
        "semantic_runtime_identity": runtime,
        "baseline_manifest_path": run.MANIFEST.relative_to(ROOT).as_posix(),
        "baseline_manifest_sha256": run.file_sha(run.MANIFEST),
        "historical_evidence_path": run.HISTORICAL.relative_to(ROOT).as_posix(),
        "historical_evidence_sha256": run.file_sha(run.HISTORICAL),
        "checkpoint_path": run.CHECKPOINT.relative_to(ROOT).as_posix(),
        "schedule_sha256": run.SCHEDULE_SHA,
        "deck_manifest": manifest["decks"],
        "logical_matchups": 45,
        "executed_games": len(games),
        "orientation_counts": dict(Counter(game["schedule"]["orientation"] for game in games)),
        "runtime_errors": 0,
        "cell_fingerprints": checkpoint["cell_fingerprints"],
        "games": games,
        "historical_global_metrics": old_metrics,
        "refreshed_global_metrics": new_metrics,
        "global_delta": deltas,
        "historical_deck_summary": old_decks,
        "refreshed_deck_summary": new_decks,
        "refreshed_aggregate_telemetry": new_summary,
        "per_deck_delta": {
            deck: {
                "win_rate": round(new_decks[deck]["win_rate"] - old_decks[deck]["win_rate"], 6),
                "mean_matchup_balance_error": round(
                    new_decks[deck]["mean_matchup_balance_error"]
                    - old_decks[deck]["mean_matchup_balance_error"],
                    6,
                ),
            }
            for deck in r1.DECKS
        },
        "matchups": new_rows,
        "matchup_comparisons": comparisons,
        "changed_matchup_cells": changed,
        "changed_cell_count": len(changed),
        "unchanged_cell_count": 45 - len(changed),
        "max_cell_win_rate_movement": max(
            abs(delta) for row in comparisons for delta in row["win_rate_delta"].values()
        ),
        "outcome_changed_games": sum(row["outcome_changed_games"] for row in comparisons),
        "ending_turn_changed_games": sum(row["ending_turn_changed_games"] for row in comparisons),
        "worst_matchup_changed": old_metrics["worst_matchup"]["decks"]
        != new_metrics["worst_matchup"]["decks"],
        "replay_samples": replay,
        "krang_control": krang,
        "r6_b_control_status": "R6_B_CONTROL_READY",
        "promotion_authorized": False,
    }
    EVIDENCE.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report(evidence)
    return evidence


def pct(value: float) -> str:
    return f"{value:.2%}"


def report(evidence: dict) -> None:
    old = evidence["historical_global_metrics"]
    new = evidence["refreshed_global_metrics"]
    lines = [
        "# Baseline 003 New-Runtime Control Refresh",
        "",
        f"Evidence identity: `{run.EVIDENCE_ID}`. This is a runtime evidence revision of the same ten-deck `OBL-BASELINE-003`, not a new baseline or promotion.",
        "",
        f"The historical [Baseline 003 manifest](baselines/OBL_BASELINE_003_MANIFEST.json) and [Combined 005 evidence](COMBINED_005_EVIDENCE.json) remain unchanged. Old runtime: `{run.OLD_RUNTIME}`. Refreshed runtime: `{run.RUNTIME}`. Their game evidence is not semantically composable.",
        "",
        f"[Machine evidence](BASELINE_003_RUNTIME_REFRESH_EVIDENCE.json) and [checkpoint](BASELINE_003_RUNTIME_REFRESH_CHECKPOINT.json) contain 45 complete cells, 4,500 new control games, 50 starts each way per cell, zero runtime errors, six matched deterministic replays, and frozen schedule `{run.SCHEDULE_SHA}`. No R6-B candidate was played.",
        "",
        "## Global metrics",
        "",
        "| Metric | Historical | Refreshed | Delta |",
        "|---|---:|---:|---:|",
    ]
    for key, label in (
        ("mean_matchup_balance_error", "Mean matchup balance error"),
        ("median_matchup_deviation", "Median deviation"),
        ("over_60_40", ">60/40 cells"),
        ("over_70_30", ">70/30 cells"),
        ("aggregate_win_rate_spread", "WR spread"),
        ("aggregate_win_rate_stddev", "WR standard deviation"),
        ("mean_first_player_result_rate", "First-player result rate"),
        ("mean_ending_turn", "Mean ending turn"),
        ("median_ending_turn", "Median ending turn"),
    ):
        lines.append(f"| {label} | {old[key]} | {new[key]} | {evidence['global_delta'][key]:+} |")
    worst_old = old["worst_matchup"]
    worst_new = new["worst_matchup"]
    old_first = worst_old["decks"][0]
    new_first = worst_new["decks"][0]
    lines.extend(
        [
            f"| Worst matchup | {r1.DISPLAY[old_first]} {pct(worst_old['win_rates'][old_first])} vs {r1.DISPLAY[worst_old['decks'][1]]} | {r1.DISPLAY[new_first]} {pct(worst_new['win_rates'][new_first])} vs {r1.DISPLAY[worst_new['decks'][1]]} | {'changed' if evidence['worst_matchup_changed'] else 'same pair'} |",
            "",
            "## Deck outcomes",
            "",
            "| Deck | Historical WR | Refreshed WR | WR delta | Historical balance error | Refreshed balance error | Error delta |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for deck in r1.DECKS:
        before = evidence["historical_deck_summary"][deck]
        after = evidence["refreshed_deck_summary"][deck]
        delta = evidence["per_deck_delta"][deck]
        lines.append(
            f"| {r1.DISPLAY[deck]} | {pct(before['win_rate'])} | {pct(after['win_rate'])} | {pct(delta['win_rate'])} | {pct(before['mean_matchup_balance_error'])} | {pct(after['mean_matchup_balance_error'])} | {pct(delta['mean_matchup_balance_error'])} |"
        )
    interpretation = (
        "The zero delta is observed game-result equivalence, not permission to compose "
        "evidence across different semantic runtimes."
        if evidence["outcome_changed_games"] == evidence["ending_turn_changed_games"] == 0
        else "These are observed runtime differences, not proof of a single-card cause."
    )
    lines.extend(
        [
            "",
            "## Matchup-result audit",
            "",
            f"Changed cells: {evidence['changed_cell_count']}; unchanged cells: {evidence['unchanged_cell_count']}; maximum cell WR movement: {pct(evidence['max_cell_win_rate_movement'])}. Paired game outcomes changed in {evidence['outcome_changed_games']} seeds; ending turns changed in {evidence['ending_turn_changed_games']}. {interpretation}",
            "",
            "| Matchup | Historical WR (first deck) | Refreshed WR | Delta | Paired outcomes changed |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in evidence["changed_matchup_cells"]:
        first = row["decks"][0]
        lines.append(
            f"| {r1.DISPLAY[first]} vs {r1.DISPLAY[row['decks'][1]]} | {pct(row['historical_win_rates'][first])} | {pct(row['refreshed_win_rates'][first])} | {pct(row['win_rate_delta'][first])} | {row['outcome_changed_games']} |"
        )
    if not evidence["changed_matchup_cells"]:
        lines.append("| None | — | — | — | 0 |")
    krang = evidence["krang_control"]
    lines.extend(
        [
            "",
            "## Krang control handoff",
            "",
            f"Krang: aggregate WR {pct(krang['win_rate'])}; mean matchup balance error {pct(krang['mean_matchup_balance_error'])}; >60/40 {krang['over_60_40']}; >70/30 {krang['over_70_30']}; first-player result rate {pct(krang['first_player_rate'])}; mean/median ending turn {krang['average_turn']}/{krang['median_turn']}.",
            "",
            "| Opponent | Refreshed Krang WR |",
            "|---|---:|",
        ]
    )
    for opponent, rate in sorted(krang["matchup_win_rates"].items()):
        lines.append(f"| {r1.DISPLAY[opponent]} | {pct(rate)} |")
    lines.extend(
        [
            "",
            f"Supported early-board/interaction telemetry: {krang['first_play']}; battlefield presence t3/t5/t7: {krang['battlefield_presence']}; interaction casts: {krang['interaction_casts']}. Unavailable metrics are not imputed as zero.",
            "",
            "**R6_B_CONTROL_READY.** All nine new-runtime Krang cells are complete. This evidence may serve as the parent/control for a later R6-B isolated experiment; it does not itself authorize R6-B games or promotion.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    result = build()
    print(
        json.dumps(
            {
                "status": result["r6_b_control_status"],
                "games": result["executed_games"],
                "changed_cells": result["changed_cell_count"],
                "replays": len(result["replay_samples"]),
            }
        )
    )
