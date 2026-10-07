"""Derive a neutral Baseline 004 runtime-control comparison from complete evidence."""

# Full Markdown rows are retained as report literals.
# ruff: noqa: E501

from __future__ import annotations

import hashlib
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_combined003_runtime_compatible as metrics  # noqa: E402
import run_objective_balance_lab_baseline004_pilot_refresh as run  # noqa: E402

ANALYSIS = run.OBL / "BASELINE_004_CYCLING_PILOT_ANALYSIS.json"
REPORT = run.OBL / "BASELINE_004_CYCLING_PILOT_CONTROL.md"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def distribution(games: list[dict]) -> dict:
    return {
        "ending_turn_histogram": dict(
            sorted(
                Counter(str(game["turn"]) for game in games).items(), key=lambda item: int(item[0])
            )
        ),
        "draws": sum(game["draw"] for game in games),
        "ending_turn_min": min(game["turn"] for game in games),
        "ending_turn_max": max(game["turn"] for game in games),
        "first_player_counts": dict(Counter(game["first_player"] for game in games)),
    }


def cycling(games: list[dict], deck: str, cards: list[str]) -> dict:
    activations = Counter()
    casts = Counter()
    delivered = Counter()
    cycling_games = 0
    for game in games:
        present = False
        source_ids = set()
        for event in game["activation_events"]:
            if (
                event["event"] == "activation_announced"
                and event.get("player") == deck
                and event.get("source") in cards
                and "cycling" in event.get("oracle_fragment", "").lower()
            ):
                activations[event["source"]] += 1
                source_ids.add(event["source_id"])
                present = True
        delivered["land_found"] += sum(
            event["event"] == "landcycling_found" and event.get("source_id") in source_ids
            for event in game["activation_events"]
        )
        delivered["shuffles"] += sum(
            event["event"] == "landcycling_shuffled" and event.get("source_id") in source_ids
            for event in game["activation_events"]
        )
        cycling_games += present
        for card in cards:
            casts[card] += game["signature_casts"].get(f"{deck}:{card}", 0)
    return {
        "cards": cards,
        "games": len(games),
        "cycling_games": cycling_games,
        "activations": dict(activations),
        "casts": dict(casts),
        "land_found": delivered["land_found"],
        "shuffles": delivered["shuffles"],
        "first_creature_by_turn_4": sum(
            game["first"][deck]["creature"] is not None and game["first"][deck]["creature"] <= 4
            for game in games
        ),
        "games_without_creature": sum(game["first"][deck]["creature"] is None for game in games),
        "battlefield_presence": {
            str(turn): round(
                statistics.mean(
                    game["battlefield_presence"].get(deck, {}).get(str(turn), 0) for game in games
                ),
                4,
            )
            for turn in (3, 5, 7)
        },
        "spell_casts": sum(game["casts"].get(deck, 0) for game in games),
    }


def build() -> dict:
    authority, manifest, schedule, _ = run.preflight()
    control = run.read(run.RESULT)
    run.verify(control, run.template(authority, manifest, schedule), schedule, complete=True)
    old = run.read(run.SOURCE)
    assert old["environment_id"] == "OBL-COMBINED-006"
    assert old["semantic_runtime_sha256"] == run.PRIOR_RUNTIME
    assert old["schedule_sha256"] == run.SCHEDULE_SHA
    before = old["combined_games"]
    after = control["games"]
    assert [game["schedule"] for game in before] == [game["schedule"] for game in after] == schedule
    assert len(before) == len(after) == 4500
    old_rows = metrics.matchup_rows(before)
    new_rows = metrics.matchup_rows(after)
    old_summary = run.r1.aggregate(before, run.r1.DECKS)
    new_summary = run.r1.aggregate(after, run.r1.DECKS)
    old_global = metrics.summary_metrics(old_summary, old_rows, before)
    new_global = metrics.summary_metrics(new_summary, new_rows, after)
    per_deck_old = metrics.per_deck(old_summary, old_rows)
    per_deck_new = metrics.per_deck(new_summary, new_rows)
    paired = {
        "changed_outcomes": sum(
            (a["winner"], a["draw"]) != (b["winner"], b["draw"])
            for a, b in zip(before, after, strict=True)
        ),
        "changed_ending_turns": sum(
            a["turn"] != b["turn"] for a, b in zip(before, after, strict=True)
        ),
    }
    matchup_deltas = []
    for prior, current in zip(old_rows, new_rows, strict=True):
        assert prior["decks"] == current["decks"]
        pair = current["decks"]
        deck = pair[0]
        matchup_deltas.append(
            {
                "decks": pair,
                "prior_first_deck_win_rate": prior["win_rates"][deck],
                "new_first_deck_win_rate": current["win_rates"][deck],
                "first_deck_delta": round(current["win_rates"][deck] - prior["win_rates"][deck], 6),
            }
        )
    named = {}
    for deck, rows in authority["cycling_inventory"].items():
        cards = [row["card"] for row in rows]
        named[deck] = {
            "prior": cycling([game for game in before if deck in game["seats"]], deck, cards),
            "new": cycling([game for game in after if deck in game["seats"]], deck, cards),
        }
    return {
        "schema": "obl-baseline004-cycling-pilot-control-analysis-v1",
        "status": "CONTROL_VALIDATED_RETURN_TO_HQ_DESIGN_STUDIO",
        "environment_id": "OBL-BASELINE-004",
        "control_id": run.CONTROL_ID,
        "prior_semantic_runtime_sha256": run.PRIOR_RUNTIME,
        "new_semantic_runtime_sha256": authority["semantic_runtime_sha256"],
        "baseline_manifest_sha256": sha(run.MANIFEST),
        "readiness_sha256": sha(run.AUTHORITY),
        "source_combined_sha256": sha(run.SOURCE),
        "control_evidence_sha256": sha(run.RESULT),
        "schedule_sha256": run.SCHEDULE_SHA,
        "validation": {
            "games": 4500,
            "matchups": 45,
            "balanced_starts_each_cell": [50, 50],
            "deterministic_replay_samples_matched": 6,
            "runtime_errors": 0,
            "decks_changed": 0,
            "new_candidate_games": 0,
        },
        "paired": paired,
        "prior_global_metrics": old_global,
        "new_global_metrics": new_global,
        "global_delta": {
            key: round(new_global[key] - old_global[key], 6)
            for key in old_global
            if isinstance(old_global[key], (int, float))
        },
        "prior_deck_summary": old_summary,
        "new_deck_summary": new_summary,
        "prior_per_deck": per_deck_old,
        "new_per_deck": per_deck_new,
        "matchup_deltas": matchup_deltas,
        "distribution": {"prior": distribution(before), "new": distribution(after)},
        "cycling_decks": named,
        "combined_validation_run": False,
        "promotion_authorized": False,
        "deck_design_decision": "DEFER_TO_HQ_DESIGN_STUDIO",
    }


def report(data: dict) -> str:
    old = data["prior_global_metrics"]
    new = data["new_global_metrics"]
    lines = [
        "# Baseline 004 cycling-pilot runtime control",
        "",
        f"Evidence `{data['control_id']}`. The ten official Baseline 004 lists are unchanged. The new semantic runtime is `{data['new_semantic_runtime_sha256']}`; prior Combined 006 used `{data['prior_semantic_runtime_sha256']}`.",
        "",
        "**Control validated:** 45 cells × 100 games, 50 starts per side, 4,500 games, six matching full-record deterministic replay samples, zero runtime errors. No new candidate, combined validation, or promotion.",
        "",
        f"Paired games with changed outcomes: **{data['paired']['changed_outcomes']}/4,500**. Ending turn changed: **{data['paired']['changed_ending_turns']}/4,500**. Runtime identities differ; the new control replaces the former balance reference for future interpretation rather than being composed with it.",
        "",
        "## Global distribution",
        "",
        "| Metric | Prior Combined 006 | New unchanged Baseline 004 control | Delta |",
        "|---|---:|---:|---:|",
    ]
    labels = {
        "mean_matchup_balance_error": "Mean matchup balance error",
        "median_matchup_deviation": "Median matchup deviation",
        "over_60_40": ">60/40 cells",
        "over_70_30": ">70/30 cells",
        "aggregate_win_rate_spread": "Deck win-rate spread",
        "aggregate_win_rate_stddev": "Deck win-rate standard deviation",
        "mean_first_player_result_rate": "Mean first-player result rate",
        "mean_ending_turn": "Mean ending turn",
        "median_ending_turn": "Median ending turn",
    }
    for key, label in labels.items():
        lines.append(f"| {label} | {old[key]} | {new[key]} | {data['global_delta'][key]:+g} |")
    lines += [
        "",
        "## Deck summaries",
        "",
        "| Deck | Prior WR | New WR | Delta | Prior balance error | New balance error |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for deck in run.r1.DECKS:
        before, after = data["prior_per_deck"][deck], data["new_per_deck"][deck]
        lines.append(
            f"| {run.r1.DISPLAY[deck]} | {before['win_rate']:.2%} | {after['win_rate']:.2%} | {after['win_rate'] - before['win_rate']:+.2%} | {before['mean_matchup_balance_error']:.2%} | {after['mean_matchup_balance_error']:.2%} |"
        )
    lines += [
        "",
        "## All 45 paired matchup cells",
        "",
        "First listed deck's result rate; both deck rates and all 4,500 game records are preserved in the machine evidence.",
        "",
        "| Matchup | Prior | New | Delta |",
        "|---|---:|---:|---:|",
    ]
    for row in data["matchup_deltas"]:
        left, right = row["decks"]
        lines.append(
            f"| {run.r1.DISPLAY[left]} vs {run.r1.DISPLAY[right]} | {row['prior_first_deck_win_rate']:.0%} | {row['new_first_deck_win_rate']:.0%} | {row['first_deck_delta']:+.0%} |"
        )
    lines += ["", "## Cycling execution", ""]
    for deck, rows in data["cycling_decks"].items():
        prior = rows["prior"]
        current = rows["new"]
        lines.append(f"### {run.r1.DISPLAY[deck]}")
        lines.append("")
        lines.append(
            f"Cycling in {prior['cycling_games']} → {current['cycling_games']} of 900 games; lands found {prior['land_found']} → {current['land_found']}; shuffles {prior['shuffles']} → {current['shuffles']}. First creature by turn 4: {prior['first_creature_by_turn_4']} → {current['first_creature_by_turn_4']}; games with none: {prior['games_without_creature']} → {current['games_without_creature']}. Creature presence at turns 3/5/7: {prior['battlefield_presence']} → {current['battlefield_presence']}."
        )
        lines.append("")
        lines.append("| Cycling creature | Prior casts | New casts | Prior cycling | New cycling |")
        lines.append("|---|---:|---:|---:|---:|")
        for card in current["cards"]:
            lines.append(
                f"| {card} | {prior['casts'][card]} | {current['casts'][card]} | {prior['activations'].get(card, 0)} | {current['activations'].get(card, 0)} |"
            )
        lines.append("")
    lines += [
        "## Handoff",
        "",
        "This is a full unchanged Baseline 004 runtime-control refresh, not a Round 8 deck test. The prior and new runtime are compared descriptively; no deck weakness, redesign, combined result, or promotion is inferred automatically. 🏢 HQ and 🧪 Design Studio own the environment reassessment and any Round 8 deck-work decision.",
        "",
        "[Raw control](BASELINE_004_CYCLING_PILOT_CONTROL.json.gz) · [analysis](BASELINE_004_CYCLING_PILOT_ANALYSIS.json) · [readiness authority](BASELINE_004_CYCLING_PILOT_READINESS.json).",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    data = build()
    ANALYSIS.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT.write_text(report(data), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": data["status"],
                "paired": data["paired"],
                "global_delta": data["global_delta"],
                "cycling": data["cycling_decks"],
            }
        )
    )


if __name__ == "__main__":
    main()
