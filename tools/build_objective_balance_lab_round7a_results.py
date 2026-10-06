"""Derive the frozen R7-A isolated handoff from authenticated raw evidence."""

# Report prose is kept as complete Markdown lines.
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
import run_objective_balance_lab_round7a as run  # noqa: E402

ANALYSIS = run.OBL / "ROUND_7_A_ANALYSIS.json"
REPORT = run.OBL / "ROUND_7_A_RESULTS.md"
CONTROL_REPORT = run.OBL / "BASELINE_003_R7A_SEMANTIC_CONTROL.md"
ORDER = (
    "raphael",
    "shredder",
    "april_oneil",
    "leonardo",
    "splinter",
    "casey_jones",
    "michelangelo",
    "donatello",
    "bebop_rocksteady",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def distribution(games: list[dict]) -> dict:
    return {
        "ending_turn_histogram": dict(
            sorted(
                Counter(str(game["turn"]) for game in games).items(),
                key=lambda row: int(row[0]),
            )
        ),
        "first_player_counts": dict(Counter(game["first_player"] for game in games)),
        "draws": sum(game["draw"] for game in games),
        "ending_turn_min": min(game["turn"] for game in games),
        "ending_turn_max": max(game["turn"] for game in games),
    }


def paired(control: list[dict], candidate: list[dict]) -> dict:
    old = {run.digest(game["schedule"]): game for game in control}
    new = {run.digest(game["schedule"]): game for game in candidate}
    assert old.keys() == new.keys()
    return {
        "outcome_changed_games": sum(
            (old[key]["winner"], old[key]["draw"]) != (new[key]["winner"], new[key]["draw"])
            for key in old
        ),
        "ending_turn_changed_games": sum(old[key]["turn"] != new[key]["turn"] for key in old),
        "krang_loss_to_win": sum(
            old[key]["winner"] != "krang" and new[key]["winner"] == "krang" for key in old
        ),
        "krang_win_to_loss": sum(
            old[key]["winner"] == "krang" and new[key]["winner"] != "krang" for key in old
        ),
    }


def mechanism(games: list[dict]) -> dict:
    counts = Counter()
    target_ids = Counter()
    resolved_games = Counter()
    activation_turns = {"Mutagen": [], "Stockman, Mad Fly-entist": []}
    for game in games:
        events = game["activation_events"]
        created = [
            event
            for event in events
            if event["event"] == "tokens_created"
            and event["token"] == "Mutagen"
            and event["controller"] == "krang"
        ]
        counts["mutagen_tokens_created"] += sum(event["quantity"] for event in created)
        announcements = {
            event["stack_object_id"]: event
            for event in events
            if event["event"] == "activation_announced"
            and event.get("player") == "krang"
            and event.get("source") in activation_turns
        }
        payments = {
            event["stack_object_id"]: event
            for event in events
            if event["event"] == "activation_cost_paid"
        }
        resolutions = {
            event["stack_object_id"]: event
            for event in events
            if event["event"] == "activated_ability_resolved"
        }
        for stack_id, event in announcements.items():
            name = event["source"]
            label = "mutagen" if name == "Mutagen" else "islandcycling"
            counts[f"{label}_announcements"] += 1
            assert stack_id in payments, (game["schedule"], stack_id)
            counts[f"{label}_paid_costs"] += 1
            if stack_id in resolutions:
                counts[f"{label}_resolutions"] += 1
                if resolutions[stack_id]["delivered"]:
                    counts[f"{label}_delivered"] += 1
                    resolved_games[label] += 1
            activation_turns[name].append(event["turn"])
        own_sources = {event["source_id"] for event in announcements.values()}
        for event in events:
            if event["event"] == "mutagen_counter_placed" and event["source_id"] in own_sources:
                counts["mutagen_counters_placed"] += 1
                target_ids[event["target_id"]] += 1
            elif (
                event["event"] == "mutagen_counter_failed_closed"
                and event["source_id"] in own_sources
            ):
                counts["mutagen_illegal_targets_at_resolution"] += 1
            elif event["event"] == "landcycling_revealed" and event["source_id"] in own_sources:
                counts["islandcycling_reveals"] += 1
            elif event["event"] == "landcycling_found" and event["source_id"] in own_sources:
                counts["islandcycling_found"] += 1
            elif event["event"] == "landcycling_shuffled" and event["source_id"] in own_sources:
                counts["islandcycling_shuffles"] += 1
        counts["ray_casts"] += game["signature_casts"].get("krang:Ray Fillet, Man Ray", 0)
        counts["stockman_casts"] += game["signature_casts"].get("krang:Stockman, Mad Fly-entist", 0)
    return {
        **dict(counts),
        "games": len(games),
        "resolved_games": dict(resolved_games),
        "counter_target_object_ids": dict(target_ids),
        "mean_activation_turn_if_observed": {
            name: round(statistics.mean(turns), 4) if turns else None
            for name, turns in activation_turns.items()
        },
    }


def build() -> dict:
    authority, manifest, schedule, _paths = run.preflight()
    control = run.read(run.CONTROL)
    run.verify(control, run.template(authority, manifest, schedule), schedule, complete=True)
    selected = [row for row in schedule if "krang" in row["pair"]]
    candidate = run.read(run.RESULT)
    run.verify(
        candidate,
        run.template(authority, manifest, selected, candidate=True),
        selected,
        complete=True,
    )
    old_control = run.OBL / "BASELINE_003_AURA_RUNTIME_CONTROL.json.gz"
    previous = run.read(old_control)
    assert previous["semantic_runtime_sha256"] == authority["prior_aura_runtime_sha256"]
    control_cells = refresh.compare_cells(previous["games"], control["games"])
    controls = [game for game in control["games"] if "krang" in game["seats"]]
    games = candidate["games"]
    comparison = normal.comparison(
        normal.summarize(controls, "krang"), normal.summarize(games, "krang")
    )
    opponents = {}
    for name in ORDER:
        old = [game for game in controls if name in game["seats"]]
        new = [game for game in games if name in game["seats"]]
        assert len(old) == len(new) == 100
        opponents[name] = {
            "control": {"distribution": distribution(old), "mechanism": mechanism(old)},
            "candidate": {"distribution": distribution(new), "mechanism": mechanism(new)},
            "paired": paired(old, new),
        }
    before = run.r1.aggregate(previous["games"], run.r1.DECKS)
    after = run.r1.aggregate(control["games"], run.r1.DECKS)
    return {
        "schema": "obl-r7a-derived-analysis-v1",
        "experiment_id": "OBL-R7-KRANG-A",
        "handoff": "RETURN_TO_DESIGN_STUDIO_FOR_INTERPRETATION",
        "primary_diagnostics": ["raphael", "shredder"],
        "anti_polarization_sentinels": ["april_oneil", "leonardo"],
        "candidate_path": run.CANDIDATE,
        "candidate_sha256": run.CANDIDATE_SHA,
        "semantic_runtime_sha256": authority["semantic_runtime_sha256"],
        "runtime_repository_sha": authority["runtime_repository_sha"],
        "readiness_sha256": sha(run.AUTHORITY),
        "baseline_manifest_sha256": sha(run.old.MANIFEST),
        "schedule_sha256": run.old.SCHEDULE_SHA,
        "control_id": run.CONTROL_ID,
        "control_sha256": sha(run.CONTROL),
        "candidate_evidence_sha256": sha(run.RESULT),
        "previous_control_sha256": sha(old_control),
        "validation": {
            "control_games": 4500,
            "candidate_games": 900,
            "control_replay_samples_matched": 6,
            "candidate_replays_matched": 900,
            "runtime_errors": 0,
            "balanced_starts_each_cell": [50, 50],
        },
        "comparison": comparison,
        "paired": paired(controls, games),
        "distributions": {"control": distribution(controls), "candidate": distribution(games)},
        "mechanism": {"control": mechanism(controls), "candidate": mechanism(games)},
        "opponents": opponents,
        "control_refresh": {
            "runtime_equivalence_claimed": False,
            "prior_aura_runtime_sha256": authority["prior_aura_runtime_sha256"],
            "old_global_metrics": metrics.summary_metrics(
                before, metrics.matchup_rows(previous["games"]), previous["games"]
            ),
            "new_global_metrics": metrics.summary_metrics(
                after, metrics.matchup_rows(control["games"]), control["games"]
            ),
            "baseline_deck_summaries": {
                deck: normal.summarize(control["games"], deck) for deck in run.r1.DECKS
            },
            "matchup_comparisons": control_cells,
            "changed_cell_count": sum(row["cell_result_changed"] for row in control_cells),
            "outcome_changed_games": sum(row["outcome_changed_games"] for row in control_cells),
        },
        "superseded_failed_control": authority["superseded_failed_control"],
        "redesign": False,
        "combined_validation_run": False,
        "promotion_authorized": False,
    }


def pct(value: float) -> str:
    return f"{value:.2%}"


def pp(value: float) -> str:
    return f"{value * 100:+.2f} pp"


def report(a: dict) -> str:
    comparison = a["comparison"]
    old, new = comparison["parent"], comparison["candidate"]
    lines = [
        "# Round 7 A — frozen Krang conversion hypothesis",
        "",
        "Handoff: **RETURN_TO_DESIGN_STUDIO_FOR_INTERPRETATION**. Cardcade reports execution and distribution evidence; Design Studio owns the design verdict.",
        "",
        "Frozen candidate: **−1 Does Machines, −1 Negate, +1 Ray Fillet, Man Ray, +1 Stockman, Mad Fly-entist**. No deck redesign, combined validation, promotion, or merge occurred.",
        "",
        f"Candidate SHA-256 `{a['candidate_sha256']}`. Semantic runtime `{a['semantic_runtime_sha256']}` from `{a['runtime_repository_sha']}`. All 4,500 unchanged Baseline 003 control games and six sampled replays validated before 900 isolated candidate games and all 900 deterministic replays. Zero runtime errors. The nine cells have 50 starts each way.",
        "",
        f"Aggregate Krang win rate {pct(old['win_rate'])} → {pct(new['win_rate'])}; mean matchup balance error {pct(old['mean_matchup_balance_error'])} → {pct(new['mean_matchup_balance_error'])}. Strict >60/40 cells {old['over_60_40']} → {new['over_60_40']}; >70/30 cells {old['over_70_30']} → {new['over_70_30']}.",
        "",
        "| Opponent | Control | R7-A | Delta | Role |",
        "|---|---:|---:|---:|---|",
    ]
    for name in ORDER:
        role = (
            "primary"
            if name in a["primary_diagnostics"]
            else "sentinel"
            if name in a["anti_polarization_sentinels"]
            else ""
        )
        lines.append(
            f"| {run.r1.DISPLAY[name]} | {pct(old['matchup_win_rates'][name])} | "
            f"{pct(new['matchup_win_rates'][name])} | "
            f"{pp(comparison['matchup_deltas'][name])} | {role} |"
        )
    lines += [
        "",
        "| Distribution metric | Control | R7-A |",
        "|---|---:|---:|",
    ]
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
        percentage = key.endswith("rate") or key in {
            "mean_matchup_balance_error",
            "median_matchup_deviation",
        }
        lines.append(
            f"| {key} | {pct(old[key]) if percentage else old[key]} | "
            f"{pct(new[key]) if percentage else new[key]} |"
        )
    lines += [
        "",
        "| Mechanism observation | Control | R7-A |",
        "|---|---:|---:|",
    ]
    for key in (
        "ray_casts",
        "stockman_casts",
        "mutagen_tokens_created",
        "mutagen_announcements",
        "mutagen_paid_costs",
        "mutagen_resolutions",
        "mutagen_delivered",
        "mutagen_counters_placed",
        "mutagen_illegal_targets_at_resolution",
        "islandcycling_announcements",
        "islandcycling_paid_costs",
        "islandcycling_resolutions",
        "islandcycling_reveals",
        "islandcycling_found",
        "islandcycling_shuffles",
    ):
        lines.append(
            f"| {key} | {a['mechanism']['control'].get(key, 0)} | "
            f"{a['mechanism']['candidate'].get(key, 0)} |"
        )
    lines += [
        "",
        "The raw activation events retain paid mana source IDs, discarded and sacrificed object IDs, target IDs, reveal and shuffle events, resolution status, and turns. The machine analysis contains cell-specific distributions, first-play timing, battlefield presence, paired outcome changes, target IDs, cast signatures, and complete control refresh comparisons. These observations do not by themselves authorize a design decision.",
        "",
        f"The new semantic runtime changed {a['control_refresh']['changed_cell_count']}/45 Baseline cells versus the preserved Aura runtime; {a['control_refresh']['outcome_changed_games']}/4,500 outcomes changed. No runtime equivalence is claimed. A prior 500-game failed control checkpoint was preserved in [audit]({a['superseded_failed_control']}); none of its games were reused.",
        "",
        "[Machine analysis](ROUND_7_A_ANALYSIS.json) · [raw candidate](ROUND_7_A_EVIDENCE.json.gz) · [control report](BASELINE_003_R7A_SEMANTIC_CONTROL.md) · [raw control](BASELINE_003_R7A_SEMANTIC_CONTROL.json.gz) · [semantic readiness](ROUND_7_A_SEMANTIC_READINESS.json).",
        "",
    ]
    return "\n".join(lines)


def control_report(a: dict) -> str:
    c = a["control_refresh"]
    lines = [
        "# Baseline 003 — R7-A semantic runtime control",
        "",
        f"Control `{a['control_id']}` under runtime `{a['semantic_runtime_sha256']}`. Ten unchanged decks, 45 cells, 4,500 games, 50 starts each way, six matching deterministic replay samples, zero runtime errors. Completed before the R7-A candidate. No equivalence claim, combined test, or promotion.",
        "",
        f"Against the preserved Aura runtime, {c['changed_cell_count']}/45 cells changed aggregate result and {c['outcome_changed_games']}/4,500 individual outcomes changed. The full Baseline 003 distribution and every cell comparison are retained in [analysis](ROUND_7_A_ANALYSIS.json).",
        "",
        "| Global metric | Preserved Aura runtime | New runtime |",
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
        prior, new = c["old_global_metrics"][key], c["new_global_metrics"][key]
        rate = any(word in key for word in ("error", "deviation", "spread", "stddev", "rate"))
        lines.append(f"| {key} | {pct(prior) if rate else prior} | {pct(new) if rate else new} |")
    lines += [
        "",
        "[Raw control](BASELINE_003_R7A_SEMANTIC_CONTROL.json.gz) · "
        "[prior control](BASELINE_003_AURA_RUNTIME_CONTROL.json.gz) · "
        "[semantic authority](ROUND_7_A_SEMANTIC_READINESS.json).",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = build()
    products = {
        ANALYSIS: json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        REPORT: report(result),
        CONTROL_REPORT: control_report(result),
    }
    for path, content in products.items():
        if args.write:
            path.write_text(content, encoding="utf-8")
        else:
            assert path.read_text(encoding="utf-8") == content, path
    print("R7_A_ISOLATED_EVIDENCE_VALIDATED")


if __name__ == "__main__":
    main()
