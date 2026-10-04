"""Derive the Aura-runtime control and isolated R6-C handoff; never run games."""

# Report literals deliberately keep complete Markdown rows and prose together.
# ruff: noqa: E501
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_baseline003_runtime_refresh_report as refresh  # noqa: E402
import build_combined003_runtime_compatible as metrics  # noqa: E402
import build_objective_balance_lab_round5_results as normal  # noqa: E402
import run_objective_balance_lab_round6c as run  # noqa: E402

ANALYSIS = run.OBL / "ROUND_6_C_ANALYSIS.json"
REPORT = run.OBL / "ROUND_6_C_RESULTS.md"
CONTROL_REPORT = run.OBL / "BASELINE_003_AURA_RUNTIME_CONTROL.md"
DIAGNOSTICS = ("raphael", "shredder", "april_oneil")
ORDER = (
    *DIAGNOSTICS,
    "splinter",
    "casey_jones",
    "michelangelo",
    "donatello",
    "bebop_rocksteady",
    "leonardo",
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def distribution(games):
    return {
        "ending_turn_histogram": dict(
            sorted(Counter(str(g["turn"]) for g in games).items(), key=lambda x: int(x[0]))
        ),
        "first_player_counts": dict(Counter(g["first_player"] for g in games)),
        "draws": sum(g["draw"] for g in games),
        "ending_turn_min": min(g["turn"] for g in games),
        "ending_turn_max": max(g["turn"] for g in games),
    }


def aura_telemetry(games):
    result = Counter()
    targets = Counter()
    turns = []
    cast_games = []
    resolved_games = []
    resolved_pt = Counter()
    first_cast_turns = []
    for game in games:
        seat = game["seats"].index("krang")
        events = game["aura_events"]
        casts = [
            e
            for e in events
            if e["event"] == "spell_cast"
            and e.get("player") == "krang"
            and e.get("card") == "Retro-Mutation"
        ]
        resolved = [
            e
            for e in events
            if e["event"] == "aura_resolved"
            and e.get("controller") == seat
            and e.get("card") == "Retro-Mutation"
        ]
        cast_by_id = {e["stack_object_id"]: e for e in casts}
        attachments = {
            e["source_id"]: e
            for e in events
            if e["event"] == "aura_attached" and e.get("controller") == seat
        }
        owned_sources = {e["source_id"] for e in resolved}
        owned_targets = {e["target_id"] for e in resolved}
        for event in resolved:
            cast = cast_by_id[event["stack_object_id"]]
            attachment = attachments[event["source_id"]]
            assert cast["target_id"] == event["target_id"] == attachment["target_id"]
            assert attachment["abilities_removed"] and attachment["cant_attack"]
            targets[event["target"]] += 1
            turns.append(event["turn"])
            resolved_pt[f"{event['power']}/{event['toughness']}"] += 1
        failed = [
            e for e in events if e["event"] == "aura_failed" and e.get("source_id") in cast_by_id
        ]
        countered = [
            e
            for e in events
            if e["event"] == "spell_countered" and e.get("target_spell_id") in cast_by_id
        ]
        assert len(casts) == len(resolved) + len(failed) + len(countered)
        recalculations = [
            e
            for e in events
            if e["event"] == "aura_effects_recalculated"
            and (owned_sources.intersection(e["source_ids"]) or e["target_id"] in owned_targets)
        ]
        result.update(
            {
                "casts": len(casts),
                "resolutions": len(resolved),
                "failed_illegal_target": len(failed),
                "countered": len(countered),
                "attachments_verified": len(resolved),
                "recalculation_events": len(recalculations),
                "restoration_events": sum(
                    not e["abilities_removed"] and not e["cant_attack"] for e in recalculations
                ),
            }
        )
        if casts:
            cast_games.append(game)
            first_cast_turns.append(min(e["turn"] for e in casts))
        if resolved:
            resolved_games.append(game)
    assert result["casts"] == sum(
        g["signature_casts"].get("krang:Retro-Mutation", 0) for g in games
    )
    return {
        **dict(result),
        "games": len(games),
        "games_with_cast": len(cast_games),
        "games_with_resolution": len(resolved_games),
        "win_rate_in_games_with_cast_descriptive_only": normal._rate(cast_games, "krang")
        if cast_games
        else None,
        "mean_first_cast_turn_if_observed": round(statistics.mean(first_cast_turns), 4)
        if first_cast_turns
        else None,
        "resolution_turn_histogram": dict(
            sorted(Counter(str(t) for t in turns).items(), key=lambda x: int(x[0]))
        ),
        "resolved_effective_pt_counts": dict(sorted(resolved_pt.items())),
        "targets": dict(sorted(targets.items(), key=lambda x: (-x[1], x[0]))),
    }


def paired(control, candidate):
    old = {run.digest(g["schedule"]): g for g in control}
    new = {run.digest(g["schedule"]): g for g in candidate}
    assert old.keys() == new.keys()
    return {
        "outcome_changed_games": sum(
            (old[k]["winner"], old[k]["draw"]) != (new[k]["winner"], new[k]["draw"]) for k in old
        ),
        "ending_turn_changed_games": sum(old[k]["turn"] != new[k]["turn"] for k in old),
        "krang_loss_to_win": sum(
            old[k]["winner"] != "krang" and new[k]["winner"] == "krang" for k in old
        ),
        "krang_win_to_loss": sum(
            old[k]["winner"] == "krang" and new[k]["winner"] != "krang" for k in old
        ),
    }


def build():
    authority, manifest, full_schedule, _ = run.preflight()
    control = run.read(run.CONTROL)
    run.verify(
        control, run.template(authority, manifest, full_schedule), full_schedule, complete=True
    )
    schedule = [r for r in full_schedule if "krang" in r["pair"]]
    candidate = run.read(run.RESULT)
    run.verify(
        candidate,
        run.template(authority, manifest, schedule, candidate=True),
        schedule,
        complete=True,
    )
    historical_path = run.OBL / "BASELINE_003_RUNTIME_REFRESH_EVIDENCE.json"
    historical = json.loads(historical_path.read_text())
    assert historical["semantic_runtime_sha256"] == authority["historical_runtime_sha256"]
    cells = refresh.compare_cells(historical["games"], control["games"])
    controls = [g for g in control["games"] if "krang" in g["seats"]]
    games = candidate["games"]
    prior_attempt = run.OBL / "audit/R6_C_SUPERSEDED_RUNTIME_002"
    prior_control = run.read(prior_attempt / run.CONTROL.name)
    prior_candidate = run.read(prior_attempt / run.RESULT.name)
    assert len(prior_control["games"]) == 4500 and len(prior_candidate["games"]) == 400
    assert control["games"] == prior_control["games"]
    assert games[:400] == prior_candidate["games"]
    old_summary = run.r1.aggregate(historical["games"], run.r1.DECKS)
    new_summary = run.r1.aggregate(control["games"], run.r1.DECKS)
    comparison = normal.comparison(
        normal.summarize(controls, "krang"), normal.summarize(games, "krang")
    )
    opponents = {}
    for opponent in ORDER:
        parent_cell = [g for g in controls if opponent in g["seats"]]
        candidate_cell = [g for g in games if opponent in g["seats"]]
        opponents[opponent] = {
            "control": {**distribution(parent_cell), "aura": aura_telemetry(parent_cell)},
            "candidate": {**distribution(candidate_cell), "aura": aura_telemetry(candidate_cell)},
            "paired": paired(parent_cell, candidate_cell),
        }
    result = {
        "schema": "obl-r6c-derived-analysis-v1",
        "experiment_id": "OBL-R6-KRANG-C",
        "verdict": "RETURN_TO_DESIGN_STUDIO",
        "hypothesis": "Threat suppression instead of additional board value",
        "primary": "raphael",
        "secondary": "shredder",
        "sentinel": "april_oneil",
        "mechanism_status": "EXECUTED_AND_TELEMETRY_VERIFIED",
        "candidate_path": run.CANDIDATE,
        "candidate_sha256": run.CANDIDATE_SHA,
        "candidate_git_blob": hashlib.sha1(
            f"blob {(ROOT / run.CANDIDATE).stat().st_size}\0".encode()
            + (ROOT / run.CANDIDATE).read_bytes()
        ).hexdigest(),
        "semantic_runtime_sha256": authority["semantic_runtime_sha256"],
        "runtime_repository_sha": authority["runtime_repository_sha"],
        "readiness_sha256": sha(run.AUTHORITY),
        "schedule_sha256": run.old.SCHEDULE_SHA,
        "control_id": run.CONTROL_ID,
        "control_sha256": sha(run.CONTROL),
        "candidate_evidence_sha256": sha(run.RESULT),
        "historical_control_sha256": sha(historical_path),
        "baseline_manifest_sha256": sha(run.old.MANIFEST),
        "comparison": comparison,
        "distribution_observations": {
            "aggregate_win_rate_improved": comparison["aggregate_win_rate_delta"] > 0,
            "mean_matchup_balance_error_improved": comparison["balance_delta"] < 0,
            "primary_delta": comparison["matchup_deltas"]["raphael"],
            "secondary_delta": comparison["matchup_deltas"]["shredder"],
            "sentinel_delta": comparison["matchup_deltas"]["april_oneil"],
            "new_over_60_40_opponents": [
                d
                for d, rate in comparison["candidate"]["matchup_win_rates"].items()
                if abs(rate - 0.5) > 0.1
                and abs(comparison["parent"]["matchup_win_rates"][d] - 0.5) <= 0.1
            ],
            "new_over_70_30_opponents": [
                d
                for d, rate in comparison["candidate"]["matchup_win_rates"].items()
                if abs(rate - 0.5) > 0.2
                and abs(comparison["parent"]["matchup_win_rates"][d] - 0.5) <= 0.2
            ],
            "interpretation_owner": "Design Studio",
        },
        "paired": paired(controls, games),
        "distributions": {"control": distribution(controls), "candidate": distribution(games)},
        "aura": {"control": aura_telemetry(controls), "candidate": aura_telemetry(games)},
        "opponents": opponents,
        "block_enumeration_regression": {
            "ordered_legal_surface_tests": 9,
            "complete_control_records_identical_before_and_after": 4500,
            "completed_candidate_prefix_records_identical_before_and_after": 400,
            "no_old_records_reused_in_final_runs": True,
            "prior_runtime_sha256": prior_control["semantic_runtime_sha256"],
            "prior_control_sha256": sha(prior_attempt / run.CONTROL.name),
            "prior_candidate_prefix_sha256": sha(prior_attempt / run.RESULT.name),
        },
        "control_refresh": {
            "runtime_equivalence_claimed": False,
            "historical_runtime_sha256": authority["historical_runtime_sha256"],
            "historical_global_metrics": metrics.summary_metrics(
                old_summary, metrics.matchup_rows(historical["games"]), historical["games"]
            ),
            "refreshed_global_metrics": metrics.summary_metrics(
                new_summary, metrics.matchup_rows(control["games"]), control["games"]
            ),
            "baseline_deck_summaries": {
                d: normal.summarize(control["games"], d) for d in run.r1.DECKS
            },
            "matchup_comparisons": cells,
            "changed_cell_count": sum(c["cell_result_changed"] for c in cells),
            "outcome_changed_games": sum(c["outcome_changed_games"] for c in cells),
            "ending_turn_changed_games": sum(c["ending_turn_changed_games"] for c in cells),
        },
        "validation": {
            "control_games": 4500,
            "candidate_games": 900,
            "control_replay_samples_matched": 6,
            "candidate_replays_matched": 900,
            "runtime_errors": 0,
            "balanced_starts_each_cell": [50, 50],
            "semantic_and_regression_validation": authority["validation"],
        },
        "redesign": False,
        "combined_validation_run": False,
        "promotion_authorized": False,
        "limits": authority["limits"]
        + [
            "Both control and candidate now execute Retro-Mutation (two versus three copies); cast telemetry cannot identify the marginal physical copy.",
            "Historical interaction and first-interaction proxies exclude Aura suppression; Aura execution is reported separately.",
            "Cast-conditioned win rates are descriptive selection-biased subsets, not causal estimates.",
            "Effective P/T after resolution can exceed 0/1 because counters and other modifiers apply after base P/T setting.",
            "Full saved-record replay hashes include Aura events. The older runtime_fingerprint field alone does not encode every continuous characteristic.",
            "Suppression and attachment are observed; counterfactual prevented attacks or damage are not quantified.",
        ],
    }
    return result


def pct(value):
    return f"{value:.2%}"


def pp(value):
    return f"{value * 100:+.2f} pp"


def control_report(a):
    c = a["control_refresh"]
    lines = [
        "# Baseline 003 Aura-runtime control refresh",
        "",
        f"Control: `{a['control_id']}`. Runtime: `{a['semantic_runtime_sha256']}`. Source commit: `{a['runtime_repository_sha']}`.",
        "",
        "The ten unchanged decks were authenticated against the [frozen Baseline 003 manifest](baselines/OBL_BASELINE_003_MANIFEST.json). All 4,500 games completed using the established 45-cell schedule, 100 games per cell, 50 starts each way. Zero runtime errors; all six sampled full-record deterministic replays matched. This is a control refresh, not a combined candidate validation or baseline promotion.",
        "",
        f"No runtime-equivalence claim is made. Against the previous runtime control, {c['changed_cell_count']}/45 cells changed their aggregate result; {c['outcome_changed_games']}/4,500 individual outcomes and {c['ending_turn_changed_games']}/4,500 ending turns changed. The new semantics and generic pilot policy make previously inert Aura slots executable, including the two Retro-Mutations already in unchanged Krang. The candidate was run only after this control completed and passed identity/schedule checks.",
        "",
        "[Raw control](BASELINE_003_AURA_RUNTIME_CONTROL.json.gz), [derived metrics](ROUND_6_C_ANALYSIS.json), [prior control](BASELINE_003_RUNTIME_REFRESH_EVIDENCE.json), and [semantic authority](ROUND_6_C_SEMANTIC_READINESS.json). The final runtime also prunes impossible combat block assignments. Its entire 4,500-game control record equals the pre-pruning Aura control record, while all games were freshly rerun under the final identity.",
        "",
        "| Global metric | Previous runtime | Aura runtime |",
        "|---|---:|---:|",
    ]
    for key in (
        "mean_matchup_balance_error",
        "median_matchup_deviation",
        "over_60_40",
        "over_70_30",
        "aggregate_win_rate_spread",
        "aggregate_win_rate_stddev",
        "mean_first_player_result_rate",
        "mean_ending_turn",
        "median_ending_turn",
    ):
        before, after = c["historical_global_metrics"][key], c["refreshed_global_metrics"][key]
        rate = any(s in key for s in ("error", "deviation", "spread", "stddev", "rate"))
        lines.append(
            f"| {key} | {pct(before) if rate else before} | {pct(after) if rate else after} |"
        )
    lines += [
        "",
        "All 45 cells below use the first named deck's win rate. Exact per-deck metrics, wins/losses/draws and outcome-change counts are in the analysis JSON.",
        "",
        "| Pair | Previous | Aura runtime | Delta | Changed outcomes |",
        "|---|---:|---:|---:|---:|",
    ]
    for cell in c["matchup_comparisons"]:
        first, second = cell["decks"]
        lines.append(
            f"| {run.r1.DISPLAY[first]} / {run.r1.DISPLAY[second]} | {pct(cell['historical_win_rates'][first])} | {pct(cell['refreshed_win_rates'][first])} | {pp(cell['win_rate_delta'][first])} | {cell['outcome_changed_games']} |"
        )
    return "\n".join(lines) + "\n"


def report(a):
    c = a["comparison"]
    parent, candidate = c["parent"], c["candidate"]
    lines = [
        "# Round 6 C — threat suppression",
        "",
        "Handoff: **RETURN_TO_DESIGN_STUDIO**. Gameplay mechanism: **EXECUTED_AND_TELEMETRY_VERIFIED**. No redesign, combined candidate validation, or promotion occurred.",
        "",
        f"On the frozen schedule, aggregate win rate moved {pct(parent['win_rate'])} → {pct(candidate['win_rate'])}; mean matchup balance error moved {pct(parent['mean_matchup_balance_error'])} → {pct(candidate['mean_matchup_balance_error'])}. Raphael changed {pp(c['matchup_deltas']['raphael'])}, Shredder {pp(c['matchup_deltas']['shredder'])}, and April {pp(c['matchup_deltas']['april_oneil'])}. Strict >60/40 matchups moved {parent['over_60_40']} → {candidate['over_60_40']}; strict >70/30 moved {parent['over_70_30']} → {candidate['over_70_30']}. April is a new >60/40 matchup and Leonardo a new >70/30 matchup. The suppression mechanism executed, but the tested list did not produce a smoother matchup distribution. Design Studio owns the interpretation and any subsequent design decision.",
        "",
        f"Frozen `OBL-R6-KRANG-C`: **−1 Negate / +1 Retro-Mutation**, 60 cards, SHA-256 `{a['candidate_sha256']}`. The nine opponents are the exact authenticated Baseline 003 decks in the raw evidence's opponent manifest. Raphael is the primary diagnostic, Shredder secondary, April the anti-polarization sentinel.",
        "",
        f"Runtime `{a['semantic_runtime_sha256']}` at source commit `{a['runtime_repository_sha']}`. The [new control](BASELINE_003_AURA_RUNTIME_CONTROL.md) completed before candidate execution; the older control is not used for candidate deltas. All **900 candidate games and 900 full-record deterministic replays** completed, with **zero runtime errors** and **50 starts each way per opponent**. Schedule SHA-256: `{a['schedule_sha256']}`.",
        "",
        "[Machine analysis](ROUND_6_C_ANALYSIS.json) · [raw candidate events and games](ROUND_6_C_EVIDENCE.json.gz) · [raw control](BASELINE_003_AURA_RUNTIME_CONTROL.json.gz) · [semantic readiness](ROUND_6_C_SEMANTIC_READINESS.json) · [frozen candidate](candidates/KRANG_OBL_R6_C.txt).",
        "",
        "| Opponent | Control | R6-C | Delta |",
        "|---|---:|---:|---:|",
    ]
    for opponent in ORDER:
        role = {
            "raphael": " — primary",
            "shredder": " — secondary",
            "april_oneil": " — sentinel",
        }.get(opponent, "")
        lines.append(
            f"| {run.r1.DISPLAY[opponent]}{role} | {pct(parent['matchup_win_rates'][opponent])} | {pct(candidate['matchup_win_rates'][opponent])} | {pp(c['matchup_deltas'][opponent])} |"
        )
    lines += ["", "| Distribution metric | Control | R6-C |", "|---|---:|---:|"]
    for key in (
        "wins",
        "losses",
        "draws",
        "win_rate",
        "mean_matchup_balance_error",
        "median_matchup_deviation",
        "over_60_40",
        "over_70_30",
        "first_player_result_rate",
        "mean_ending_turn",
        "median_ending_turn",
    ):
        before, after = parent[key], candidate[key]
        rate = key.endswith("rate") or key in {
            "mean_matchup_balance_error",
            "median_matchup_deviation",
        }
        lines.append(
            f"| {key} | {pct(before) if rate else before} | {pct(after) if rate else after} |"
        )
    lines += [
        "",
        "Strict >60/40 and >70/30 thresholds use the established metric definitions. Ending-turn histograms, per-cell starts, paired outcome shifts, first-land-miss/creature/blocker/interaction timing, battlefield presence, and all signature casts are retained in the machine analysis.",
        "",
        "| Timing / board proxy | Control | R6-C |",
        "|---|---:|---:|",
    ]
    for event in ("land_miss", "creature", "blocker", "interaction"):
        values = [s["first_play"][event] for s in (parent, candidate)]
        lines.append(
            f"| First {event}: mean turn (observed games) | {values[0]['mean_turn_if_observed']} ({values[0]['observed_games']}) | {values[1]['mean_turn_if_observed']} ({values[1]['observed_games']}) |"
        )
    for turn in ("3", "5", "7"):
        values = [s["battlefield_presence"][turn] for s in (parent, candidate)]
        lines.append(
            f"| Turn {turn} creatures: mean (observed games) | {values[0]['mean_creatures_if_observed']} ({values[0]['observed_games']}) | {values[1]['mean_creatures_if_observed']} ({values[1]['observed_games']}) |"
        )
    lines += [
        "",
        "Retro-Mutation is excluded from the historical interaction proxy; its execution is counted separately below. Printed creature counts are unchanged by the candidate substitution.",
        "",
        "| Retro-Mutation execution | Control | R6-C |",
        "|---|---:|---:|",
    ]
    for key in (
        "casts",
        "resolutions",
        "failed_illegal_target",
        "countered",
        "games_with_cast",
        "games_with_resolution",
        "attachments_verified",
        "recalculation_events",
        "restoration_events",
        "mean_first_cast_turn_if_observed",
    ):
        lines.append(f"| {key} | {a['aura']['control'][key]} | {a['aura']['candidate'][key]} |")
    lines += [
        "",
        "Every recorded resolution links back to its cast and locked target ID and an attachment reporting ability removal and an attack restriction. Targets, object IDs, turns, phase/step, effective P/T and source IDs are in the raw game records. Final P/T may exceed 0/1 after counters or later modifiers; the base-setting layer is separately tested.",
        "",
        "| Diagnostic | Control casts / resolves | R6-C casts / resolves | Control / R6-C games with resolution |",
        "|---|---:|---:|---:|",
    ]
    for opponent in DIAGNOSTICS:
        old, new = [a["opponents"][opponent][side]["aura"] for side in ("control", "candidate")]
        lines.append(
            f"| {run.r1.DISPLAY[opponent]} | {old['casts']} / {old['resolutions']} | {new['casts']} / {new['resolutions']} | {old['games_with_resolution']} / {new['games_with_resolution']} |"
        )
    lines += ["", "| Resolved target | Control | R6-C |", "|---|---:|---:|"]
    for target in sorted(
        set(a["aura"]["control"]["targets"]) | set(a["aura"]["candidate"]["targets"])
    ):
        lines.append(
            f"| {target} | {a['aura']['control']['targets'].get(target, 0)} | {a['aura']['candidate']['targets'].get(target, 0)} |"
        )
    lines += [
        "",
        "The implementation recognizes a bounded Oracle-text Aura template with variable creature type and base P/T. It does not dispatch on experiment IDs, opponent identities or target names. Tests cover legal targeting, attachment, layer 7b versus counters/modifiers, layer-6 keyword order, static/trigger/activated ability suppression, retained already-stacked abilities, Flash priority, retargeting, source removal, incarnation changes, simultaneous departures, state-based actions and deterministic execution.",
        "",
        "Validation before freezing the final runtime: 1,604 passed and 2 skipped in one invocation, including 17 Aura tests and nine combat-enumeration equivalence tests. Final evidence authentication and tamper checks are additionally covered by `tests/test_objective_balance_lab_round6c.py`. Ruff check/format and diff checks passed.",
        "",
        "Limits:",
        "",
    ]
    lines.extend(f"- {limit}" for limit in a["limits"])
    lines += [
        "",
        "Two attempts are preserved for audit: [the invalid-target logging fix](audit/R6_C_SUPERSEDED_RUNTIME_001/AUDIT.json) and [the combat enumeration bottleneck](audit/R6_C_SUPERSEDED_RUNTIME_002/AUDIT.json). Each contains a superseded control and 400 completed candidate games; none are included in final metrics. The latter identified scheduled game 424 against Splinter as the slow case. Pruning impossible block assignments preserved the full ordered legal action surface and reduced that diagnostic game to under one second. All 4,500 final control records and the first 400 final candidate records exactly match the pre-pruning records, but were freshly executed under the final runtime. The complete 900-game final test uses this same runtime throughout.",
        "",
        "Reproduce without mixing runtimes:",
        "",
        "```sh",
        "uv sync --locked --dev",
        "uv run python tools/run_objective_balance_lab_round6c.py",
        "uv run python tools/run_objective_balance_lab_round6c.py --control --workers 8",
        "uv run python tools/run_objective_balance_lab_round6c.py --candidate --workers 8",
        "uv run python tools/build_objective_balance_lab_round6c_results.py --check",
        "```",
        "",
        "The runner verifies completed checkpoints and resumes only missing work; it does not rerun a completed cell. For fresh execution, use a separate checkout and move the two final `.json.gz` files aside there before running. Keep the published evidence intact.",
    ]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    a = build()
    products = {
        ANALYSIS: json.dumps(a, indent=2, ensure_ascii=False) + "\n",
        REPORT: report(a),
        CONTROL_REPORT: control_report(a),
    }
    for path, content in products.items():
        if args.check:
            assert path.read_text() == content, path
        else:
            path.write_text(content, encoding="utf-8")
    print("R6_C_ANALYSIS_VERIFIED" if args.check else "R6_C_ANALYSIS_WRITTEN")


if __name__ == "__main__":
    main()
