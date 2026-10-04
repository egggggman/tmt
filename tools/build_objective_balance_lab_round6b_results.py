"""Package Krang R6-B's authenticated new-runtime isolated comparison."""

# Generated Markdown prose and tables are intentionally kept as literal lines.
# ruff: noqa: E501

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
sys.path.insert(0, str(ROOT / "tools"))

import build_objective_balance_lab_round5_results as summarize  # noqa: E402
import run_objective_balance_lab_round6b as r6b  # noqa: E402

HYPOTHESIS = "PARTIALLY_SUPPORTED"
VERDICT = "RETURN_TO_DESIGN_STUDIO_REJECT_POLARIZATION"
IDENTITY = "IDENTITY_STRENGTHENED"
REPORT = OBL / "ROUND_6_B_RESULTS.md"


def pct(rate: float) -> str:
    return f"{rate:.2%}"


def pp(delta: float) -> str:
    return f"{delta * 100:+.2f} pp"


def chrome_telemetry(games: list[dict]) -> dict:
    names = Counter()
    per_opponent: dict[str, dict[str, int]] = {}
    casts = entries = exits = applications = removals = updates = 0
    games_with_cast = games_with_impact = casts_without_impact = 0
    positive_power = removed_power = distinct_targets = 0
    max_qualifying = 0
    for opponent in (deck for deck in summarize.r1.DECKS if deck != "krang"):
        own = [game for game in games if opponent in game["seats"]]
        own_casts = own_impacts = 0
        for game in own:
            count = game["signature_casts"].get("krang:Chrome Dome", 0)
            changes = [
                event
                for event in game.get("static_modifier_changes", [])
                if event["source"] == "Chrome Dome"
            ]
            zones = [
                event
                for event in game.get("static_source_zone_changes", [])
                if event["card"] == "Chrome Dome"
            ]
            applied = [event for event in changes if event["action"] == "applied"]
            removed = [event for event in changes if event["action"] == "removed"]
            changed = [event for event in changes if event["action"] == "updated"]
            assert all(
                event["power_delta"] == 1 and event["toughness_delta"] == 0 for event in applied
            )
            assert all(
                event["power_delta"] == -1 and event["toughness_delta"] == 0 for event in removed
            )
            casts += count
            applications += len(applied)
            removals += len(removed)
            updates += len(changed)
            positive_power += sum(event["power_delta"] for event in applied)
            removed_power += sum(event["power_delta"] for event in removed)
            names.update(event["target"] for event in applied)
            distinct_targets += len({event["target_object_id"] for event in applied})
            if changes:
                max_qualifying = max(
                    max_qualifying,
                    *(event["qualifying_targets"] for event in changes),
                )
            entries += sum(
                event["destination_zone"] == "battlefield" and event["source_zone"] != "battlefield"
                for event in zones
            )
            exits += sum(
                event["source_zone"] == "battlefield" and event["destination_zone"] != "battlefield"
                for event in zones
            )
            games_with_cast += count > 0
            games_with_impact += bool(applied)
            casts_without_impact += count > 0 and not applied
            own_casts += count
            own_impacts += bool(applied)
        per_opponent[opponent] = {
            "casts": own_casts,
            "games_with_modifier_impact": own_impacts,
        }
    return {
        "casts": casts,
        "games_with_cast": games_with_cast,
        "battlefield_entries": entries,
        "battlefield_exits": exits,
        "modifier_change_events": applications + removals + updates,
        "modifier_applications": applications,
        "modifier_removals": removals,
        "modifier_updates": updates,
        "qualifying_target_applications": applications,
        "distinct_affected_permanents_across_games": distinct_targets,
        "max_simultaneous_qualifying_targets_observed": max_qualifying,
        "affected_artifact_creature_names": dict(sorted(names.items())),
        "positive_power_contributions": positive_power,
        "removed_power_contributions": removed_power,
        "toughness_contribution": 0,
        "games_with_modifier_impact": games_with_impact,
        "games_with_cast_but_no_modifier_impact": casts_without_impact,
        "per_opponent": per_opponent,
        "activated_copy_ability": "UNSUPPORTED_NOT_CREDITED",
    }


def build() -> dict:
    manifest, isolated, _paths, control = r6b.preflight()
    checkpoint = json.loads(r6b.CHECKPOINT.read_text(encoding="utf-8"))
    r6b.verify(checkpoint, r6b.template(manifest, isolated), isolated)
    assert checkpoint["completed_games"] == checkpoint["replayed_games"] == 900
    assert len(checkpoint["cells"]) == len(checkpoint["replay_fingerprints"]) == 9
    games = [
        game
        for opponent in summarize.r1.DECKS
        if opponent in checkpoint["cells"]
        for game in checkpoint["cells"][opponent]
    ]
    parent = summarize.summarize(control["games"], "krang")
    candidate = summarize.summarize(games, "krang")
    comparison = summarize.comparison(parent, candidate)
    telemetry = chrome_telemetry(games)
    assert telemetry["casts"] == candidate["signature_casts"].get("Chrome Dome", 0)
    assert telemetry["casts"] > 0 and telemetry["modifier_applications"] > 0
    assert parent["win_rate"] == control["krang_control"]["win_rate"]
    assert (
        parent["mean_matchup_balance_error"]
        == control["krang_control"]["mean_matchup_balance_error"]
    )
    assert parent["matchup_win_rates"] == control["krang_control"]["matchup_win_rates"]
    near_even_new_extremes = [
        opponent
        for opponent, rate in parent["matchup_win_rates"].items()
        if abs(rate - 0.5) <= 0.1 and abs(candidate["matchup_win_rates"][opponent] - 0.5) > 0.1
    ]
    assert near_even_new_extremes == ["april_oneil"]
    assert candidate["matchup_win_rates"]["shredder"] == 0.15
    assert candidate["matchup_win_rates"]["raphael"] == 0.13
    assert candidate["matchup_win_rates"]["april_oneil"] == 0.62
    assert comparison["balance_delta"] > 0 and comparison["over_60_40_delta"] > 0
    assert comparison["over_70_30_delta"] < 0
    prior = json.loads((OBL / "ROUND_6_A_EVIDENCE.json").read_text(encoding="utf-8"))
    prior_result = prior["results"]["comparison"]["candidate"]
    results = {
        "hypothesis_result": HYPOTHESIS,
        "cardcade_verdict": VERDICT,
        "identity_classification": IDENTITY,
        "comparison": comparison,
        "chrome_dome_telemetry": telemetry,
        "new_extremes_from_near_even": near_even_new_extremes,
        "r6_a_historical_context": {
            "semantic_runtime_sha256": prior["semantic_runtime_sha256"],
            "win_rate": prior_result["win_rate"],
            "mean_matchup_balance_error": prior_result["mean_matchup_balance_error"],
            "over_60_40": prior_result["over_60_40"],
            "over_70_30": prior_result["over_70_30"],
            "matchup_win_rates": prior_result["matchup_win_rates"],
            "warning": "Historical design context only; not the runtime-compatible paired control.",
        },
        "runtime_errors": 0,
        "replay_verified_games": checkpoint["replayed_games"],
        "promotion_authorized": False,
    }
    checkpoint["results"] = results
    r6b.save(checkpoint)
    r6b.EVIDENCE.write_text(
        json.dumps(checkpoint, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    render(results)
    return results


def render(results: dict) -> None:
    comparison = results["comparison"]
    parent = comparison["parent"]
    candidate = comparison["candidate"]
    telemetry = results["chrome_dome_telemetry"]
    lines = [
        "# Krang Round 6-B — isolated Chrome Dome validation",
        "",
        f"Immutable Design Studio candidate `{r6b.EXPERIMENT}`: -1 Negate, +1 Chrome Dome; canonical LF SHA-256 `{r6b.CANDIDATE_SHA}`, Git blob `{r6b.CANDIDATE_BLOB}`. Its 60-card list was not changed.",
        "",
        f"The paired control is [Baseline 003 Runtime Refresh 001](BASELINE_003_RUNTIME_REFRESH_EVIDENCE.json) under semantic runtime `{r6b.RUNTIME}` and frozen schedule `{r6b.SCHEDULE_SHA}`. Historical R6-A used another runtime and is context only. [Machine evidence](ROUND_6_B_EVIDENCE.json) and [checkpoint](ROUND_6_B_CHECKPOINT.json) retain nine 100-game cells and all 900 matching deterministic replays. No parent games were rerun.",
        "",
        "Mean Matchup Balance Error = mean of absolute matchup WR distance from 50%. The >60/40 and >70/30 counts use strict thresholds. Negative Balance Δ is improvement.",
        "",
        "| Metric | Refreshed control | R6-B | Delta |",
        "|---|---:|---:|---:|",
        f"| Aggregate WR | {pct(parent['win_rate'])} | {pct(candidate['win_rate'])} | {pp(comparison['aggregate_win_rate_delta'])} |",
        f"| Mean balance error | {pct(parent['mean_matchup_balance_error'])} | {pct(candidate['mean_matchup_balance_error'])} | {pp(comparison['balance_delta'])} |",
        f"| >60/40 | {parent['over_60_40']} | {candidate['over_60_40']} | {comparison['over_60_40_delta']:+} |",
        f"| >70/30 | {parent['over_70_30']} | {candidate['over_70_30']} | {comparison['over_70_30_delta']:+} |",
        f"| Worst matchup | {parent['worst_matchup']['opponent']} {pct(parent['worst_matchup']['win_rate'])} | {candidate['worst_matchup']['opponent']} {pct(candidate['worst_matchup']['win_rate'])} | — |",
        f"| Krang-first result | {pct(parent['first_player_result_rate'])} | {pct(candidate['first_player_result_rate'])} | — |",
        f"| Mean / median ending turn | {parent['mean_ending_turn']} / {parent['median_ending_turn']} | {candidate['mean_ending_turn']} / {candidate['median_ending_turn']} | — |",
        "",
        "| Opponent | Control WR | R6-B WR | Delta |",
        "|---|---:|---:|---:|",
    ]
    for opponent, rate in parent["matchup_win_rates"].items():
        lines.append(
            f"| {summarize.r1.DISPLAY[opponent]} | {pct(rate)} | {pct(candidate['matchup_win_rates'][opponent])} | {pp(comparison['matchup_deltas'][opponent])} |"
        )
    lines.extend(
        [
            "",
            "## Development and mechanism",
            "",
            f"First creature (conditional mean when observed): {parent['first_play']['creature']['mean_turn_if_observed']} → {candidate['first_play']['creature']['mean_turn_if_observed']}; first meaningful blocker proxy: {parent['first_play']['blocker']['mean_turn_if_observed']} → {candidate['first_play']['blocker']['mean_turn_if_observed']}; first interaction proxy: {parent['first_play']['interaction']['mean_turn_if_observed']} → {candidate['first_play']['interaction']['mean_turn_if_observed']}. Unobserved is not zero.",
            "",
            "| Turn | Control observed games / mean creatures | R6-B observed games / mean creatures | Delta in conditional mean |",
            "|---|---:|---:|---:|",
        ]
    )
    for turn in ("3", "5", "7"):
        before = parent["battlefield_presence"][turn]
        after = candidate["battlefield_presence"][turn]
        lines.append(
            f"| {turn} | {before['observed_games']} / {before['mean_creatures_if_observed']} | {after['observed_games']} / {after['mean_creatures_if_observed']} | {comparison['battlefield_presence_mean_deltas'][turn]:+.4f} |"
        )
    lines.extend(
        [
            "",
            f"Interaction casts: {parent['interaction_casts_total']} → {candidate['interaction_casts_total']}; Chrome Dome casts: **{telemetry['casts']}** in {telemetry['games_with_cast']} games; battlefield entries/exits recorded: {telemetry['battlefield_entries']}/{telemetry['battlefield_exits']}.",
            "",
            f"The generic `pt_static_team_modifier_changed` stream records {telemetry['modifier_change_events']} changes: {telemetry['modifier_applications']} applications, {telemetry['modifier_removals']} removals, {telemetry['modifier_updates']} updates. It applied +1/+0 to qualifying targets {telemetry['positive_power_contributions']} times (maximum simultaneous qualifying targets observed: {telemetry['max_simultaneous_qualifying_targets_observed']}). Affected artifact-creature names and counts: {telemetry['affected_artifact_creature_names']}. It affected another artifact creature in **{telemetry['games_with_modifier_impact']} games**; {telemetry['games_with_cast_but_no_modifier_impact']} games had a cast without a recorded modifier application. Casts alone are not counted as modifier impact, and neither observation proves win causality. Chrome Dome's {{5}} copy activation remains unsupported and is not credited.",
            "",
            "## Distribution audit",
            "",
            "1. Shredder improved 12% → 15%; Raphael held at 13%.",
            "2. April moved 53% → 62%, creating a new >60/40 extreme from a near-even cell.",
            "3. Casey improved 23% → 31% and is not excessively Krang-favored; Leonardo moved 68% → 70% but did not exceed the strict >70/30 threshold.",
            "4. Mean balance error worsened 19.5556% → 19.7778%; >60/40 increased 6 → 7, while >70/30 decreased 4 → 3.",
            "5. Early battlefield-presence proxies rose modestly, but first-creature timing did not improve. The supported continuous modifier was exercised in actual game states.",
            "6. Replacing Negate with an artifact body and team artifact modifier strengthens Krang's technology-engine identity, without relying on the unsupported copy activation.",
            "",
            "R6-A historical context: its one-copy Turtle Techie reached 40.11% WR, Shredder 17%, Raphael 14%, April 67%, mean error 19.89%, >60/40 7 and >70/30 4. R6-B is less severe on April and >70/30, but still worsens its own runtime-compatible control's mean balance and >60/40 distribution. R6-A is not used as statistical control.",
            "",
            f"Hypothesis: **{HYPOTHESIS}**. Cardcade handoff: **{VERDICT}**. Identity: **{IDENTITY}**. The primary Shredder cell and artifact mechanism show a real signal, but Raphael does not move and April becomes a new extreme. Return evidence to Design Studio; this is not a promotion decision and Cardcade does not design R6-C.",
            "",
            "Nine complete cells, 900/900 unique candidate games, 450 Krang-first and 450 opponent-first starts, 900/900 matching replay fingerprints, no adaptive/replacement seeds, zero runtime errors, and no candidate-vs-candidate games.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    result = build()
    print(
        json.dumps(
            {
                "games": 900,
                "verdict": result["cardcade_verdict"],
                "chrome_casts": result["chrome_dome_telemetry"]["casts"],
                "modifier_applications": result["chrome_dome_telemetry"]["modifier_applications"],
            }
        )
    )
