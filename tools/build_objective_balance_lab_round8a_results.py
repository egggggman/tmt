"""Derive the R8-A isolated handoff from authenticated control and candidate games."""

# Report prose is kept as complete Markdown lines.
# ruff: noqa: E501

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_baseline003_runtime_refresh_report as refresh  # noqa: E402
import build_combined003_runtime_compatible as global_metrics  # noqa: E402
import build_objective_balance_lab_round5_results as normal  # noqa: E402
import run_objective_balance_lab_round8a as run  # noqa: E402

ANALYSIS = run.OBL / "ROUND_8_A_ANALYSIS.json"
REPORT = run.OBL / "ROUND_8_A_RESULTS.md"
CONTROL_REPORT = run.OBL / "BASELINE_004_R8A_ETB_RUNTIME_CONTROL.md"
DECK = "bebop_rocksteady"
ORDER = (
    "raphael",
    "shredder",
    "splinter",
    "casey_jones",
    "donatello",
    "leonardo",
    "krang",
    "april_oneil",
    "michelangelo",
)
DIAGNOSTICS = ORDER[:4]
SENTINELS = ORDER[4:7]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def distribution(games: list[dict]) -> dict:
    return {
        "ending_turn_histogram": dict(
            sorted(Counter(str(g["turn"]) for g in games).items(), key=lambda item: int(item[0]))
        ),
        "first_player_counts": dict(Counter(g["first_player"] for g in games)),
        "draws": sum(g["draw"] for g in games),
        "ending_turn_min": min(g["turn"] for g in games),
        "ending_turn_max": max(g["turn"] for g in games),
    }


def paired(control: list[dict], candidate: list[dict]) -> dict:
    old = {run.digest(g["schedule"]): g for g in control}
    new = {run.digest(g["schedule"]): g for g in candidate}
    assert len(old) == len(new) == len(control) == len(candidate)
    assert old.keys() == new.keys()
    return {
        "outcome_changed_games": sum(
            (old[k]["winner"], old[k]["draw"]) != (new[k]["winner"], new[k]["draw"]) for k in old
        ),
        "ending_turn_changed_games": sum(old[k]["turn"] != new[k]["turn"] for k in old),
        "loss_to_win": sum(old[k]["winner"] != DECK and new[k]["winner"] == DECK for k in old),
        "win_to_loss": sum(old[k]["winner"] == DECK and new[k]["winner"] != DECK for k in old),
    }


def mechanism(games: list[dict]) -> dict:
    resolved = [
        event
        for game in games
        for event in game["etb_life_gain_events"]
        if event["source_card"] == "Primordial Pachyderm" and event["controller"] == DECK
    ]
    assert all(e["amount"] == 2 and e["life_after"] - e["life_before"] == 2 for e in resolved)
    return {
        "pachyderm_casts": sum(
            g["signature_casts"].get(f"{DECK}:Primordial Pachyderm", 0) for g in games
        ),
        "pachyderm_etb_life_gain_resolutions": len(resolved),
        "pachyderm_life_gained": sum(e["amount"] for e in resolved),
        "pachyderm_etb_games": sum(
            any(
                e["source_card"] == "Primordial Pachyderm" and e["controller"] == DECK
                for e in g["etb_life_gain_events"]
            )
            for g in games
        ),
        "all_etb_life_gain_events": sum(len(g["etb_life_gain_events"]) for g in games),
    }


def build() -> dict:
    authority, manifest, schedule, _ = run.preflight()
    control = run.read(run.RESULT)
    run.verify(control, run.template(authority, manifest, schedule), schedule, complete=True)
    selected = [row for row in schedule if DECK in row["pair"]]
    candidate = run.read(run.CANDIDATE_RESULT)
    run.verify(
        candidate,
        run.template(authority, manifest, selected, candidate=True),
        selected,
        complete=True,
        replay_pairs=run.SELECTED_REPLAY_PAIRS,
    )
    controls = [g for g in control["games"] if DECK in g["seats"]]
    games = candidate["games"]
    assert len(controls) == len(games) == 900
    assert candidate["runtime_control_sha256"] == sha(run.RESULT)
    comparison = normal.comparison(normal.summarize(controls, DECK), normal.summarize(games, DECK))
    opponents = {}
    for name in ORDER:
        old = [g for g in controls if name in g["seats"]]
        new = [g for g in games if name in g["seats"]]
        assert len(old) == len(new) == 100
        opponents[name] = {
            "control": {"distribution": distribution(old), "mechanism": mechanism(old)},
            "candidate": {"distribution": distribution(new), "mechanism": mechanism(new)},
            "paired": paired(old, new),
        }
    previous = run.read(run.SOURCE)
    assert previous["semantic_runtime_sha256"] == run.PRIOR_RUNTIME
    assert [game["schedule"] for game in previous["games"]] == schedule
    unchanged_fingerprints = sum(
        old["runtime_fingerprint"] == new["runtime_fingerprint"]
        for old, new in zip(previous["games"], control["games"], strict=True)
    )
    assert unchanged_fingerprints == 4500
    cell_comparison = refresh.compare_cells(previous["games"], control["games"])
    assert len(cell_comparison) == 45
    return {
        "schema": "obl-r8a-derived-analysis-v1",
        "experiment_id": run.CANDIDATE_ID,
        "handoff": "RETURN_TO_DESIGN_STUDIO_FOR_INTERPRETATION",
        "primary_diagnostics": list(DIAGNOSTICS),
        "anti_polarization_sentinels": list(SENTINELS),
        "candidate_path": str(run.CANDIDATE.relative_to(ROOT)),
        "candidate_sha256": authority["candidate_sha256"],
        "semantic_runtime_sha256": authority["semantic_runtime_sha256"],
        "readiness_sha256": sha(run.AUTHORITY),
        "baseline_manifest_sha256": sha(run.MANIFEST),
        "schedule_sha256": run.SCHEDULE_SHA,
        "control_id": run.CONTROL_ID,
        "control_sha256": sha(run.RESULT),
        "candidate_evidence_sha256": sha(run.CANDIDATE_RESULT),
        "prior_control_sha256": sha(run.SOURCE),
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
            "prior_runtime_sha256": run.PRIOR_RUNTIME,
            "old_global_metrics": global_metrics.summary_metrics(
                run.r1.aggregate(previous["games"], run.r1.DECKS),
                global_metrics.matchup_rows(previous["games"]),
                previous["games"],
            ),
            "new_global_metrics": global_metrics.summary_metrics(
                run.r1.aggregate(control["games"], run.r1.DECKS),
                global_metrics.matchup_rows(control["games"]),
                control["games"],
            ),
            "prior_baseline_deck_summaries": {
                deck: normal.summarize(previous["games"], deck) for deck in run.r1.DECKS
            },
            "baseline_deck_summaries": {
                deck: normal.summarize(control["games"], deck) for deck in run.r1.DECKS
            },
            "matchup_comparisons": cell_comparison,
            "changed_cell_count": sum(row["cell_result_changed"] for row in cell_comparison),
            "outcome_changed_games": sum(row["outcome_changed_games"] for row in cell_comparison),
            "matching_state_fingerprints": unchanged_fingerprints,
            "ending_turn_changed_games": sum(
                row["ending_turn_changed_games"] for row in cell_comparison
            ),
            "new_control_etb_life_gain_events": sum(
                len(game["etb_life_gain_events"]) for game in control["games"]
            ),
        },
        "redesign": False,
        "combined_validation_run": False,
        "promotion_authorized": False,
    }


def pct(value: float) -> str:
    return f"{value:.2%}"


def report(a: dict) -> str:
    comparison = a["comparison"]
    old, new = comparison["parent"], comparison["candidate"]
    lines = [
        "# Round 8 A — frozen Bebop & Rocksteady board-development hypothesis",
        "",
        "Handoff: **RETURN_TO_DESIGN_STUDIO_FOR_INTERPRETATION**. Cardcade reports execution and distribution evidence. Design Studio owns the hypothesis verdict; aggregate win-rate gain alone is insufficient.",
        "",
        "Frozen candidate: **−2 Illegitimate Business / +2 Primordial Pachyderm** against unchanged Baseline 004. No redesign, combined validation, promotion, Baseline 005, or merge occurred.",
        "",
        f"Candidate SHA-256 `{a['candidate_sha256']}`. Semantic runtime `{a['semantic_runtime_sha256']}`. The refreshed 4,500-game unchanged control and six deterministic replay samples validated before the 900-game isolated candidate and all 900 deterministic replays. Zero runtime errors; each cell has 50 starts each way.",
        "",
        f"Aggregate B&R win rate {pct(old['win_rate'])} → {pct(new['win_rate'])}; mean matchup balance error {pct(old['mean_matchup_balance_error'])} → {pct(new['mean_matchup_balance_error'])}. Strict >60/40 cells {old['over_60_40']} → {new['over_60_40']}; >70/30 cells {old['over_70_30']} → {new['over_70_30']}.",
        "",
        "| Opponent | Control | R8-A | Delta | Role |",
        "|---|---:|---:|---:|---|",
    ]
    for name in ORDER:
        role = "primary" if name in DIAGNOSTICS else "sentinel" if name in SENTINELS else ""
        lines.append(
            f"| {run.r1.DISPLAY[name]} | {pct(old['matchup_win_rates'][name])} | {pct(new['matchup_win_rates'][name])} | {comparison['matchup_deltas'][name] * 100:+.2f} pp | {role} |"
        )
    lines += ["", "| Distribution metric | Control | R8-A |", "|---|---:|---:|"]
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
            f"| {key} | {pct(old[key]) if percentage else old[key]} | {pct(new[key]) if percentage else new[key]} |"
        )
    mechanism_old, mechanism_new = a["mechanism"]["control"], a["mechanism"]["candidate"]
    lines += ["", "| Mechanism observation | Control | R8-A |", "|---|---:|---:|"]
    for key in (
        "pachyderm_casts",
        "pachyderm_etb_life_gain_resolutions",
        "pachyderm_life_gained",
        "pachyderm_etb_games",
        "all_etb_life_gain_events",
    ):
        lines.append(f"| {key} | {mechanism_old[key]} | {mechanism_new[key]} |")
    lines += [
        "",
        "The raw ETB events preserve source, controller, trigger and stack IDs, amount, and life totals before and after each resolution. Machine analysis includes per-cell paired outcomes, first-creature timing, battlefield presence, ending-turn histograms, cast signatures, and all distribution metrics. Both lists contain 20 basic lands (10 Forest and 10 Swamp). Illegitimate Business is also a Land in the frozen catalog; cutting two copies changes total lands from 24 to 22. This experiment measures the whole substitution rather than isolating life gain from that resource change.",
        "",
        f"The refreshed unchanged Baseline 004 control has {a['control_refresh']['changed_cell_count']}/45 changed cell results, {a['control_refresh']['outcome_changed_games']}/4,500 changed outcomes, {a['control_refresh']['matching_state_fingerprints']}/4,500 matching state fingerprints, and {a['control_refresh']['new_control_etb_life_gain_events']} new ETB life-gain events versus the prior control. The runtime identity changed, so the complete new control is the comparison anchor. No combined candidate validation occurred. A superseded partial 600-game checkpoint is preserved in [audit](audit/R8_A_SUPERSEDED_TELEMETRY_CONTROL_001/README.md) and was excluded from all comparisons.",
        "",
        "[Machine analysis](ROUND_8_A_ANALYSIS.json) · [raw candidate](ROUND_8_A_EVIDENCE.json.gz) · [control report](BASELINE_004_R8A_ETB_RUNTIME_CONTROL.md) · [raw control](BASELINE_004_R8A_ETB_RUNTIME_CONTROL.json.gz) · [semantic readiness](ROUND_8_A_SEMANTIC_READINESS.json).",
        "",
    ]
    return "\n".join(lines)


def control_report(a: dict) -> str:
    c = a["control_refresh"]
    lines = [
        "# Baseline 004 — R8-A ETB semantic runtime control",
        "",
        f"Control `{a['control_id']}` under runtime `{a['semantic_runtime_sha256']}`. Ten unchanged decks, 45 cells, 4,500 games, balanced 50 starts per cell, six matching deterministic replay samples, zero runtime errors. Completed before the R8-A candidate. No equivalence claim, combined candidate test, or promotion.",
        "",
        f"Prior control SHA-256 `{a['prior_control_sha256']}`; new control SHA-256 `{a['control_sha256']}`. Changed cell results: {c['changed_cell_count']}/45. Paired outcomes changed: {c['outcome_changed_games']}/4,500. State fingerprints matched: {c['matching_state_fingerprints']}/4,500. Ending turns changed: {c['ending_turn_changed_games']}/4,500. New ETB life-gain events on unchanged decks: {c['new_control_etb_life_gain_events']}.",
        "",
        "| Deck | Prior WR | Refreshed WR |",
        "|---|---:|---:|",
    ]
    for deck in run.r1.DECKS:
        before = c["prior_baseline_deck_summaries"][deck]
        lines.append(
            f"| {run.r1.DISPLAY[deck]} | {pct(before['win_rate'])} | {pct(c['baseline_deck_summaries'][deck]['win_rate'])} |"
        )
    lines += [
        "",
        "The 45 unchanged cell comparisons, paired outcome changes, global distribution, and full baseline deck summaries are in [machine analysis](ROUND_8_A_ANALYSIS.json). [Raw control](BASELINE_004_R8A_ETB_RUNTIME_CONTROL.json.gz).",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    a = build()
    ANALYSIS.write_text(json.dumps(a, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT.write_text(report(a), encoding="utf-8")
    CONTROL_REPORT.write_text(control_report(a), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": a["handoff"],
                "control_games": 4500,
                "candidate_games": 900,
                "win_rate": [a["comparison"][side]["win_rate"] for side in ("parent", "candidate")],
            }
        )
    )


if __name__ == "__main__":
    main()
