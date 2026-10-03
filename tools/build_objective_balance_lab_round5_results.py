"""Derive Round 5 metrics from authenticated games and publish durable reports."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
sys.path.insert(0, str(ROOT / "tools"))

import run_objective_balance_lab_round1 as r1  # noqa: E402
import run_objective_balance_lab_round5 as r5  # noqa: E402

DECISIONS: dict[str, dict[str, str]] = {
    "OBL-R5-SHREDDER-A": {
        "hypothesis_result": "PARTIALLY_SUPPORTED",
        "identity_classification": "IDENTITY_PRESERVED",
        "verdict": "PROMISING_NEEDS_VARIANT",
        "rationale": (
            "The first-creature proxy is 0.27 turns later and turn-3/5 board proxies fall, "
            "so the early-pressure lever is observable. Power falls only 0.44 pp, however, "
            "and >60/40 matchups rise 7 to 9 despite one fewer >70/30 matchup. "
            "The Foot/minion pressure identity remains; this is informative but not the "
            "preferred combined-matrix build."
        ),
    },
    "OBL-R5-SHREDDER-B": {
        "hypothesis_result": "PARTIALLY_SUPPORTED",
        "identity_classification": "IDENTITY_PRESERVED",
        "verdict": "ACCEPT_FOR_COMBINED_MATRIX",
        "rationale": (
            "Splitting the cut between a one-drop and Shark Shredder lowers WR by 2.56 pp "
            "and mean balance error by 2.56 pp; >70/30 falls 6 to 5 without adding "
            ">60/40 pairings. Turn-3/5 board proxies do not fall, so this supports a "
            "conversion/opportunity-cost effect, not the predicted early-board dilution. "
            "The remaining villain shell preserves identity."
        ),
    },
    "OBL-R5-APRIL_ONEIL-A": {
        "hypothesis_result": "PARTIALLY_SUPPORTED",
        "identity_classification": "IDENTITY_STRENGTHENED",
        "verdict": "ACCEPT_FOR_COMBINED_MATRIX",
        "rationale": (
            "Moving two Negates into Reporter/Utrom bodies raises WR 4.00 pp and lowers "
            "balance error 4.00 pp; >60/40 falls 7 to 5. First-creature proxy is "
            "0.26 turns earlier and turn-5/7 presence rises slightly, but turn-3 presence "
            "and >70/30 count do not improve. Reporter and adaptive Utrom tempo strengthen "
            "identity. Baseline Negate had zero casts, so this converts dormant slots "
            "rather than measuring the cost of lost permission. Reporter combat-draw "
            "is not credited as simulated value."
        ),
    },
    "OBL-R5-KRANG-A": {
        "hypothesis_result": "PARTIALLY_SUPPORTED",
        "identity_classification": "IDENTITY_STRENGTHENED",
        "verdict": "REJECT_BALANCE_REGRESSION",
        "rationale": (
            "Mouser casts and turn-3/5/7 presence show a real artifact-linked board lever; "
            "WR rises 4.89 pp. Yet balance error worsens 1.78 pp, >60/40 rises 6 to 8, "
            "and >70/30 rises 4 to 5. The matchup spread, not its aggregate WR, rejects "
            "this otherwise thematic candidate. Baseline Negate had zero casts, so the "
            "observed change is active artifact bodies replacing dormant slots."
        ),
    },
    "OBL-R5-KRANG-B": {
        "hypothesis_result": "PARTIALLY_SUPPORTED",
        "identity_classification": "IDENTITY_PRESERVED",
        "verdict": "ACCEPT_FOR_COMBINED_MATRIX",
        "rationale": (
            "Artifact-linked Turtle Techie bodies raise WR 7.89 pp, improve balance error "
            "1.67 pp, and modestly increase turn-5/7 presence. However, >60/40 rises "
            "6 to 8 while >70/30 stays at 4; the conditional ETB draw lacks a direct "
            "effect-use counter here. Two Donatello cameos remain technology support "
            "rather than a new deck identity. Baseline Negate had zero casts; this is "
            "an active-body substitution, not an observed interaction tradeoff. "
            "Combined validation must test the extra "
            "extremes and identity risk before any promotion."
        ),
    },
}

RECOMMENDATIONS = {
    "shredder": "OBL-R5-SHREDDER-B",
    "april_oneil": "OBL-R5-APRIL_ONEIL-A",
    "krang": "OBL-R5-KRANG-B",
}


@lru_cache(maxsize=1)
def interaction_names() -> frozenset[str]:
    """Use the same Oracle-text name filter as the frozen game-metrics runner."""
    return frozenset(
        name
        for name, card in r1.catalog().items()
        if any(
            word in (card.get("oracle_text") or "").lower()
            for word in ("counter target", "destroy target", "exile target", "return target")
        )
    )


def _rate(games: list[dict], deck: str) -> float:
    return (
        sum(game["winner"] == deck for game in games) + sum(game["draw"] for game in games) / 2
    ) / len(games)


def summarize(games: list[dict], deck: str) -> dict:
    own = [game for game in games if deck in game["seats"]]
    assert len(own) == 900
    assert all(not game.get("runtime_error") for game in own)
    matchups = {}
    for opponent in r1.DECKS:
        if opponent == deck:
            continue
        subset = [game for game in own if opponent in game["seats"]]
        assert len(subset) == 100
        matchups[opponent] = round(_rate(subset, deck), 6)
    deviations = {opponent: abs(rate - 0.5) for opponent, rate in matchups.items()}
    worst = max(matchups, key=lambda opponent: deviations[opponent])
    weakest = min(matchups, key=matchups.get)
    starts = [game for game in own if game["first_player"] == deck]
    assert len(starts) == 450
    first = {}
    for event in ("land_miss", "creature", "blocker", "interaction"):
        observed = [
            game["first"][deck][event]
            for game in own
            if game["first"].get(deck, {}).get(event) is not None
        ]
        first[event] = {
            "observed_games": len(observed),
            "mean_turn_if_observed": round(statistics.mean(observed), 4) if observed else None,
            "median_turn_if_observed": statistics.median(observed) if observed else None,
        }
    presence = {}
    for turn in (3, 5, 7):
        observed = [
            game["battlefield_presence"][deck][str(turn)]
            for game in own
            if str(turn) in game["battlefield_presence"].get(deck, {})
        ]
        presence[str(turn)] = {
            "observed_games": len(observed),
            "mean_creatures_if_observed": round(statistics.mean(observed), 4) if observed else None,
            "positive_games": sum(value > 0 for value in observed),
        }
    signature = Counter()
    utility: dict[str, Counter] = {}
    for game in own:
        for key, value in game["signature_casts"].items():
            if key.startswith(f"{deck}:"):
                signature[key.split(":", 1)[1]] += value
        for card, counters in game.get("utility_telemetry", {}).get(deck, {}).items():
            utility.setdefault(card, Counter()).update(counters)
    interaction_total = sum(
        count for name, count in signature.items() if name in interaction_names()
    )
    source_interaction_proxy = sum(game["interaction_casts"].get(deck, 0) for game in own)
    turns = [game["turn"] for game in own]
    return {
        "games": 900,
        "wins": sum(game["winner"] == deck for game in own),
        "draws": sum(game["draw"] for game in own),
        "losses": sum(game["winner"] not in {deck, None} for game in own),
        "win_rate": round(_rate(own, deck), 6),
        "matchup_win_rates": matchups,
        "mean_matchup_balance_error": round(statistics.mean(deviations.values()), 6),
        "median_matchup_deviation": round(statistics.median(deviations.values()), 6),
        "over_60_40": sum(value > 0.1 for value in deviations.values()),
        "over_70_30": sum(value > 0.2 for value in deviations.values()),
        "worst_matchup": {"opponent": worst, "win_rate": matchups[worst]},
        "weakest_matchup": {"opponent": weakest, "win_rate": matchups[weakest]},
        "first_player_result_rate": round(_rate(starts, deck), 6),
        "mean_ending_turn": round(statistics.mean(turns), 4),
        "median_ending_turn": statistics.median(turns),
        "first_play": first,
        "battlefield_presence": presence,
        "interaction_casts_total": interaction_total,
        "interaction_casts_per_game": round(interaction_total / 900, 4),
        "source_distinct_cast_names_proxy_total": source_interaction_proxy,
        "source_distinct_cast_names_proxy_per_game": round(source_interaction_proxy / 900, 4),
        "signature_casts": dict(sorted(signature.items())),
        "utility_telemetry": {
            card: dict(sorted(counts.items())) for card, counts in sorted(utility.items())
        },
        "runtime_errors": 0,
    }


def comparison(parent: dict, candidate: dict) -> dict:
    return {
        "parent": parent,
        "candidate": candidate,
        "aggregate_win_rate_delta": round(candidate["win_rate"] - parent["win_rate"], 6),
        "balance_delta": round(
            candidate["mean_matchup_balance_error"] - parent["mean_matchup_balance_error"], 6
        ),
        "matchup_deltas": {
            opponent: round(candidate["matchup_win_rates"][opponent] - rate, 6)
            for opponent, rate in parent["matchup_win_rates"].items()
        },
        "over_60_40_delta": candidate["over_60_40"] - parent["over_60_40"],
        "over_70_30_delta": candidate["over_70_30"] - parent["over_70_30"],
        "first_creature_mean_delta": round(
            candidate["first_play"]["creature"]["mean_turn_if_observed"]
            - parent["first_play"]["creature"]["mean_turn_if_observed"],
            4,
        ),
        "battlefield_presence_mean_deltas": {
            turn: round(
                candidate["battlefield_presence"][turn]["mean_creatures_if_observed"]
                - parent["battlefield_presence"][turn]["mean_creatures_if_observed"],
                4,
            )
            for turn in ("3", "5", "7")
        },
        "interaction_casts_per_game_delta": round(
            candidate["interaction_casts_per_game"] - parent["interaction_casts_per_game"], 4
        ),
    }


def build() -> tuple[dict, dict]:
    plan, _manifest, schedule, _paths = r5.preflight()
    evidence = json.loads(r5.OUTPUT.read_text(encoding="utf-8"))
    checkpoint = json.loads(r5.CHECKPOINT.read_text(encoding="utf-8"))
    r5.verify_completed(evidence, schedule)
    r5.verify_completed(checkpoint, schedule)
    assert evidence["candidate_results"] == checkpoint["candidate_results"]
    assert evidence["counts"]["completed_games"] == 4500
    baseline = json.loads((ROOT / plan["reference_evidence"]).read_text(encoding="utf-8"))
    baseline_games = baseline["combined_games"]
    parent_summaries = {
        deck: summarize(baseline_games, deck) for deck in ("shredder", "april_oneil", "krang")
    }
    for deck, summary in parent_summaries.items():
        assert summary["win_rate"] == baseline["combined_deck_summary"][deck]["win_rate"]
    reports = {}
    for planned in plan["candidates"]:
        experiment_id = planned["experiment_id"]
        deck = planned["deck_key"]
        candidate = summarize(evidence["candidate_results"][experiment_id], deck)
        reports[experiment_id] = comparison(parent_summaries[deck], candidate)
    return evidence, reports


def _pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def render_report(evidence: dict, reports: dict) -> str:
    global_reference = evidence["baseline_global_metrics"]
    planned_by_id = {
        row["experiment_id"]: row
        for row in json.loads(r5.PLAN.read_text(encoding="utf-8"))["candidates"]
    }
    lines = [
        "# Objective Balance Lab Round 5 — isolated candidate results",
        "",
        "The execution request's `OBL-R5-APRIL-A` denotes the approved plan's stable "
        "`OBL-R5-APRIL_ONEIL-A`; this is an alias, not a second candidate.",
        "",
        "Five preserved candidates played the nine exact OBL-BASELINE-002 opponents each: "
        "4,500/4,500 games, 100 per pairing, 50 starts per seat, no adaptive/replacement seeds, "
        "no candidate-vs-candidate games, and zero runtime errors. No baseline was regenerated. "
        "The semantic runtime matches the audited Baseline 002 authority. "
        "[Raw evidence](ROUND_5_EVIDENCE.json); [checkpoint](ROUND_5_CHECKPOINT.json).",
        "The immutable card diffs and SHA-256 values remain in the "
        "[approved design plan](ROUND_5_CANDIDATE_PLAN.md).",
        "Per-card signature casts are recorded, but these Round 5 game rows do not carry "
        "draw, activation, attack-gate, or effect-use counters for artifacts. Their absence "
        "means unavailable, not zero. The same limitation applies to a direct Reporter "
        "combat-draw or Turtle Techie ETB-draw counter.",
        "",
        "Mean Matchup Balance Error is the mean of |(wins + draws/2)/100 − 50%| "
        "across the deck's nine opponents. Negative Balance Δ is improvement. "
        "Counts above 60/40 and 70/30 use strict thresholds.",
        "",
        "The audited Baseline 002 environment remains the comparison authority: "
        f"global balance error {_pct(global_reference['mean_matchup_balance_error'])}, "
        f"median deviation {_pct(global_reference['median_matchup_deviation'])}, "
        f">60/40 {global_reference['over_60_40']}, "
        f">70/30 {global_reference['over_70_30']}, "
        f"WR spread {_pct(global_reference['aggregate_win_rate_spread'])}, "
        f"first-player result {_pct(global_reference['mean_first_player_result_rate'])}, "
        f"mean/median ending turn {global_reference['mean_ending_turn']}/"
        f"{global_reference['median_ending_turn']}. This isolated round does not claim a new "
        "combined-environment metric.",
        "",
        "| Candidate | Parent WR → candidate WR | Balance error parent → candidate (Δ) "
        "| >60/40 | >70/30 | Most extreme matchup | Hypothesis | Identity | Verdict |",
        "|---|---:|---:|---:|---:|---|---|---|---|",
    ]
    for experiment_id, result in reports.items():
        parent, candidate = result["parent"], result["candidate"]
        decision = DECISIONS[experiment_id]
        worst = candidate["worst_matchup"]
        lines.append(
            f"| `{experiment_id}` | {_pct(parent['win_rate'])} → {_pct(candidate['win_rate'])} "
            f"| {_pct(parent['mean_matchup_balance_error'])} → "
            f"{_pct(candidate['mean_matchup_balance_error'])} "
            f"({result['balance_delta'] * 100:+.2f} pp) "
            f"| {parent['over_60_40']} → {candidate['over_60_40']} "
            f"| {parent['over_70_30']} → {candidate['over_70_30']} "
            f"| {worst['opponent']} {_pct(worst['win_rate'])} "
            f"| {decision['hypothesis_result']} | {decision['identity_classification']} "
            f"| {decision['verdict']} |"
        )
    lines += ["", "## Matchup and functional telemetry", ""]
    for experiment_id, result in reports.items():
        candidate = result["candidate"]
        parent = result["parent"]
        decision = DECISIONS[experiment_id]
        lines += [
            f"### {experiment_id}",
            "",
            decision["rationale"],
            "",
            "| Opponent | Parent | Candidate | Δ |",
            "|---|---:|---:|---:|",
        ]
        for opponent, rate in candidate["matchup_win_rates"].items():
            lines.append(
                f"| {opponent} | {_pct(parent['matchup_win_rates'][opponent])} "
                f"| {_pct(rate)} | {result['matchup_deltas'][opponent] * 100:+.2f} pp |"
            )
        lines += [
            "",
            f"First-player result: {_pct(parent['first_player_result_rate'])} → "
            f"{_pct(candidate['first_player_result_rate'])}; mean/median ending turn: "
            f"{parent['mean_ending_turn']}/{parent['median_ending_turn']} → "
            f"{candidate['mean_ending_turn']}/{candidate['median_ending_turn']}. "
            f"First-creature proxy (observed games, conditional mean turn): "
            f"{parent['first_play']['creature']['observed_games']}, "
            f"{parent['first_play']['creature']['mean_turn_if_observed']} → "
            f"{candidate['first_play']['creature']['observed_games']}, "
            f"{candidate['first_play']['creature']['mean_turn_if_observed']}.",
            "",
            "Battlefield-presence proxy through turn 3/5/7 "
            "(observed games; conditional mean): "
            + "; ".join(
                f"t{turn} {parent['battlefield_presence'][turn]['observed_games']};"
                f"{parent['battlefield_presence'][turn]['mean_creatures_if_observed']} → "
                f"{candidate['battlefield_presence'][turn]['observed_games']};"
                f"{candidate['battlefield_presence'][turn]['mean_creatures_if_observed']}"
                for turn in ("3", "5", "7")
            )
            + ". Missing snapshots are not zeroes.",
            "",
            f"Oracle-text-matched interaction casts per game: "
            f"{parent['interaction_casts_per_game']} → {candidate['interaction_casts_per_game']}. "
            "Full per-card cast counts are in machine evidence; artifact activation counters "
            "are only present if emitted by the source runtime.",
            "",
        ]
        changed_cards = set(planned_by_id[experiment_id]["removals"]) | set(
            planned_by_id[experiment_id]["additions"]
        )
        lines += [
            "Changed-card signature casts: "
            + "; ".join(
                f"{card} {parent['signature_casts'].get(card, 0)} → "
                f"{candidate['signature_casts'].get(card, 0)}"
                for card in sorted(changed_cards)
            )
            + ".",
            "",
        ]
        observed_utility = {
            card: candidate["utility_telemetry"][card]
            for card in planned_by_id[experiment_id]["additions"]
            if card in candidate["utility_telemetry"]
        }
        if observed_utility:
            lines += [
                "Added-card utility telemetry (drawn / cast / activated / effect used): "
                + "; ".join(
                    f"{card} {data.get('drawn', 0)} / {data.get('casts', 0)} / "
                    f"{data.get('activations', 0)} / {data.get('effect_used', 0)}"
                    for card, data in observed_utility.items()
                )
                + ". Counts are recorded events, not unique games.",
                "",
            ]
        else:
            lines += [
                "Added-card draw/activation telemetry is unavailable; do not infer zero use.",
                "",
            ]
    lines += [
        "## Preserved candidate identities",
        "",
        "| Candidate | Exact diff from Baseline 002 | Candidate SHA-256 |",
        "|---|---|---|",
    ]
    for experiment_id, planned in planned_by_id.items():
        exact_diff = "; ".join(
            [f"-{copies} {card}" for card, copies in planned["removals"].items()]
            + [f"+{copies} {card}" for card, copies in planned["additions"].items()]
        )
        lines.append(f"| `{experiment_id}` | {exact_diff} | `{planned['candidate_sha256']}` |")
    lines += [
        "",
        "## Interpretation and next gate",
        "",
        "Compared with [Round 3](ROUND_3_DELTA_RESULTS.md), Shredder's earlier single-card "
        "substitutions did not supply a viable balance correction; the R5-B split across "
        "opening and closing slots is a distinct, measurable lever. April R3-A's small "
        "isolated value-density gain and R3-B's reactive failure motivated this proactive "
        "board experiment. Krang R3-A's setup-oriented mixed result and R3-B's high-end "
        "regression motivated the two conversion tests here. These are different semantic "
        "runtime baselines, so historical percentages are context, not paired deltas.",
        "",
        "Negate registers zero signature casts in the exact April and Krang Baseline 002 "
        "parent samples, and remains zero in their candidate samples. These experiments "
        "therefore test whether making two dormant slots into castable bodies changes "
        "outcomes. They do not measure an actual loss of reactive-spell use. This is the "
        "strongest shared card-role signal; it is a deck-level association, not proof "
        "that a particular drawn Negate caused a loss.",
        "",
        "April Reporter's combat-draw trigger and Tunnel Rats' graveyard return are not credited "
        "without runtime evidence. Mouser's other-artifact attack condition and Turtle Techie's "
        "conditional ETB draw are considered only to the extent the current engine executes them. "
        "The historical `interaction_casts` source field counts distinct cast card names, not "
        "interaction spells; this report independently filters signature-cast counts by the "
        "runner's Oracle-text interaction-name rule. Both values remain in machine evidence. "
        "No hand-size, flood/screw, unused-mana, stabilization, or loss-cause values are invented.",
        "",
        "Provisional Combined 004 pool: "
        + json.dumps(evidence["provisional_combined_004_pool"], sort_keys=True)
        + ". This is a recommendation only; no combined matrix or promotion occurred.",
        "",
    ]
    return "\n".join(lines)


def publish(evidence: dict, reports: dict) -> None:
    assert set(DECISIONS) == set(reports)
    for experiment_id, report in reports.items():
        report.update(DECISIONS[experiment_id])
    evidence["reports"] = reports
    evidence["experiment_aliases"] = {"OBL-R5-APRIL-A": "OBL-R5-APRIL_ONEIL-A"}
    evidence["telemetry_limitations"] = {
        "utility_draws": "UNAVAILABLE",
        "utility_activations": "UNAVAILABLE",
        "utility_effect_use": "UNAVAILABLE",
        "conditional_effect_attribution": "UNAVAILABLE",
        "per_card_signature_casts": "AVAILABLE",
    }
    baseline_manifest = json.loads(
        (OBL / "baselines/OBL_BASELINE_002_MANIFEST.json").read_text(encoding="utf-8")
    )
    evidence["baseline_global_metrics"] = baseline_manifest["environment_metrics"]
    evidence["metric_audit_path"] = "docs/objective-balance-lab/BASELINE_002_METRIC_AUDIT.json"
    evidence["metric_audit_git_blob_sha256"] = r5.git_blob_sha(evidence["metric_audit_path"])
    evidence["provisional_combined_004_pool"] = {
        key: value for key, value in RECOMMENDATIONS.items() if value
    }
    r5.write_json_atomic(r5.OUTPUT, evidence)
    (OBL / "ROUND_5_RESULTS.md").write_text(render_report(evidence, reports), encoding="utf-8")
    plan = json.loads(r5.PLAN.read_text(encoding="utf-8"))
    catalog = r1.catalog()
    ledger_path = OBL / "EXPERIMENT_LEDGER.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["experiments"] = [
        row for row in ledger["experiments"] if row["experiment_id"] not in reports
    ]
    for planned in plan["candidates"]:
        experiment_id = planned["experiment_id"]
        result = reports[experiment_id]
        ledger["experiments"].append(
            {
                "experiment_id": experiment_id,
                "round": "R5",
                "deck": r1.DISPLAY[planned["deck_key"]],
                "deck_key": planned["deck_key"],
                "parent": {
                    "environment_id": "OBL-BASELINE-002",
                    "path": planned["parent_path"],
                    "sha256": planned["parent_sha256"],
                },
                "candidate": {
                    "path": planned["candidate_path"],
                    "sha256": planned["candidate_sha256"],
                    "label": experiment_id.rsplit("-", 1)[-1],
                },
                "exact_additions": planned["additions"],
                "exact_removals": planned["removals"],
                "hypothesis": planned["hypothesis"],
                "schedule_identity": evidence["schedule_sha256"],
                "semantic_runtime_sha256": evidence["semantic_runtime_sha256"],
                "source_evidence": "docs/objective-balance-lab/ROUND_5_EVIDENCE.json",
                "result_metrics": {
                    "candidate_win_rate": result["candidate"]["win_rate"],
                    "parent_win_rate": result["parent"]["win_rate"],
                    "balance_delta": result["balance_delta"],
                    "extremes": {
                        name: result["candidate"][name]
                        for name in ("worst_matchup", "over_60_40", "over_70_30")
                    },
                    "matchup_deltas": result["matchup_deltas"],
                },
                "identity_classification": result["identity_classification"],
                "hypothesis_result": result["hypothesis_result"],
                "verdict": result["verdict"],
                "promotion_status": "EXPERIMENTAL",
                "promotion": None,
            }
        )
    r5.write_json_atomic(ledger_path, ledger)
    ledger_md = OBL / "EXPERIMENT_LEDGER.md"
    old_md = ledger_md.read_text(encoding="utf-8")
    old_md = old_md.split("\n## Round 5 isolated experiments", 1)[0].rstrip()
    md_rows = [
        "",
        "## Round 5 isolated experiments",
        "",
        "No Round 5 candidate is promoted; all five are preserved as isolated evidence.",
        "",
        "| Experiment | Deck | Parent SHA-256 | Candidate SHA-256 | Verdict | Promotion |",
        "|---|---|---|---|---|---|",
    ]
    for planned in plan["candidates"]:
        experiment_id = planned["experiment_id"]
        md_rows.append(
            f"| `{experiment_id}` | {r1.DISPLAY[planned['deck_key']]} "
            f"| `{planned['parent_sha256']}` | `{planned['candidate_sha256']}` "
            f"| {reports[experiment_id]['verdict']} | EXPERIMENTAL |"
        )
    md_rows += ["", "Results: [Round 5 evidence](ROUND_5_EVIDENCE.json).", ""]
    ledger_md.write_text(old_md + "\n" + "\n".join(md_rows), encoding="utf-8")
    role_path = OBL / "CARD_ROLE_EVIDENCE.json"
    role = json.loads(role_path.read_text(encoding="utf-8"))
    role["records"] = [row for row in role["records"] if row.get("experiment_id") not in reports]
    role["round5_evidence_path"] = "docs/objective-balance-lab/ROUND_5_EVIDENCE.json"
    for planned in plan["candidates"]:
        experiment_id = planned["experiment_id"]
        result = reports[experiment_id]
        changes = {
            **{name: -amount for name, amount in planned["removals"].items()},
            **planned["additions"],
        }
        for card, copies in changes.items():
            role["records"].append(
                {
                    "experiment_id": experiment_id,
                    "round": "R5",
                    "deck": r1.DISPLAY[planned["deck_key"]],
                    "candidate": experiment_id,
                    "card": card,
                    "copies_changed": copies,
                    "replacement_relationship": {
                        "removals": planned["removals"],
                        "additions": planned["additions"],
                    },
                    "mana_value": catalog[card]["mana_value"],
                    "card_type": catalog[card]["type_line"],
                    "rules_text": catalog[card]["oracle_text"],
                    "semantic_support": planned["semantic_support"],
                    "aggregate_win_rate_delta": result["aggregate_win_rate_delta"],
                    "matchup_deltas": result["matchup_deltas"],
                    "balance_error_delta": result["balance_delta"],
                    "early_board_delta": result["battlefield_presence_mean_deltas"],
                    "interaction_delta": result["interaction_casts_per_game_delta"],
                    "signature_delta": result["candidate"]["signature_casts"].get(card, 0)
                    - result["parent"]["signature_casts"].get(card, 0),
                    "utility_telemetry": result["candidate"]["utility_telemetry"].get(card),
                    "identity_result": result["identity_classification"],
                    "hypothesis_result": result["hypothesis_result"],
                    "causality_note": "Paired deck-level association, not drawn-card causality.",
                }
            )
    r5.write_json_atomic(role_path, role)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    evidence, reports = build()
    if not args.write:
        print(
            json.dumps(
                {
                    experiment_id: {
                        "parent_wr": report["parent"]["win_rate"],
                        "candidate_wr": report["candidate"]["win_rate"],
                        "balance_delta": report["balance_delta"],
                        "parent_60": report["parent"]["over_60_40"],
                        "candidate_60": report["candidate"]["over_60_40"],
                        "parent_70": report["parent"]["over_70_30"],
                        "candidate_70": report["candidate"]["over_70_30"],
                        "parent_worst": report["parent"]["worst_matchup"],
                        "candidate_worst": report["candidate"]["worst_matchup"],
                        "matchup_deltas": report["matchup_deltas"],
                        "first_creature_mean_delta": report["first_creature_mean_delta"],
                        "battlefield_presence_mean_deltas": report[
                            "battlefield_presence_mean_deltas"
                        ],
                        "interaction_casts_per_game_delta": report[
                            "interaction_casts_per_game_delta"
                        ],
                        "candidate_signature_casts": report["candidate"]["signature_casts"],
                    }
                    for experiment_id, report in reports.items()
                },
                indent=2,
            )
        )
        return 0
    publish(evidence, reports)
    print(json.dumps({"status": "PUBLISHED", "candidates": len(reports)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
