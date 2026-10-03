"""Compose the two-candidate Combined 005 matrix without executing games."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
sys.path.insert(0, str(ROOT / "tools"))

import build_combined003_runtime_compatible as b3  # noqa: E402
import build_combined_004_reports as b4  # noqa: E402
import run_combined_004 as c4  # noqa: E402
import run_objective_balance_lab_round1 as r1  # noqa: E402
import run_objective_balance_lab_round5 as r5  # noqa: E402
from objective_balance_lab_semantic_identity import (  # noqa: E402
    assert_pre_chrome_evidence_runtime,
)
from validate_combined_004 import validate as validate_c4  # noqa: E402

EXPECTED_MAIN = "d25b47e26c685018210acfec3b2e8e0ed3c83849"
SELECTION = {
    "shredder": "OBL-R5-SHREDDER-B",
    "april_oneil": "OBL-R5-APRIL_ONEIL-A",
}
EVIDENCE = OBL / "COMBINED_005_EVIDENCE.json"
MANIFEST = OBL / "combined/OBL_COMBINED_005_MANIFEST.json"
SELECTION_DOC = OBL / "COMBINED_005_SELECTION.md"
RESULTS_DOC = OBL / "COMBINED_005_RESULTS.md"

DECISIONS: dict[str, dict[str, str]] = {
    "OBL-R5-SHREDDER-B": {
        "combined_verdict": "COMBINED_VALIDATION_PASSED",
        "promotion_eligibility": "PROMOTION_ELIGIBLE",
        "rationale": (
            "Shredder is 71.67% versus 75.00% in Baseline 002; its balance error "
            "improves 3.33 pp and >70/30 falls 6→5 without more >60/40 cells. "
            "The effect is 0.67 pp weaker than in Combined 004 but still stronger "
            "than its 2.56 pp isolated reduction. Villain-minion pressure remains intact. "
            "The 88/12 Krang pairing is an important residual extreme, not hidden."
        ),
    },
    "OBL-R5-APRIL_ONEIL-A": {
        "combined_verdict": "COMBINED_VALIDATION_PASSED",
        "promotion_eligibility": "PROMOTION_ELIGIBLE",
        "rationale": (
            "April rises 25.78%→29.89% and improves balance error 4.11 pp; >60/40 "
            "falls 7→5 while >70/30 stays at 5. Its gain is stronger than both the "
            "4.00 pp isolated result and the 3.00 pp Combined 004 result, so it does "
            "not depend on Krang B. Reporter/Utrom preserve adaptive identity; no "
            "unsupported combat-draw is credited."
        ),
    },
}
ENVIRONMENT_DECISION = "COMBINED_ENVIRONMENT_IMPROVED"
RECOMMENDED_SUBSET = ["OBL-R5-SHREDDER-B", "OBL-R5-APRIL_ONEIL-A"]
PROMOTION_RATIONALE = (
    "Both candidates pass together in the exact Combined 005 subset and are "
    "recommended for a separate explicit promotion to OBL-BASELINE-003. Against "
    "Baseline 002, the environment improves mean balance error by 1.29 pp, cuts "
    ">60/40 cells 34→32 and >70/30 cells 18→17, and narrows WR spread. "
    "Compared with Combined 004, removing Krang B reduces >60/40 cells 34→32 but "
    "raises mean balance error 17.22%→17.67% and worsens the worst split 14/86→12/88. "
    "Krang remains an unresolved underperformer; this tradeoff and the still-high "
    "Shredder strength must be recorded in the promotion decision. No promotion is "
    "performed in this experiment."
)


def _check_lineage() -> None:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    assert not subprocess.run(
        ["git", "merge-base", "--is-ancestor", EXPECTED_MAIN, head],
        cwd=ROOT,
        check=False,
    ).returncode


def _source_sha(path: Path) -> str:
    return r5.git_blob_sha(path.relative_to(ROOT).as_posix())


def _metric_delta(source: dict, target: dict) -> dict:
    keys = (
        "mean_matchup_balance_error",
        "median_matchup_deviation",
        "over_60_40",
        "over_70_30",
        "aggregate_win_rate_spread",
        "aggregate_win_rate_stddev",
        "mean_first_player_result_rate",
        "mean_ending_turn",
        "median_ending_turn",
    )
    return {key: round(target[key] - source[key], 6) for key in keys}


def build() -> tuple[dict, dict]:
    _check_lineage()
    validate_c4(replay=False)
    assert_pre_chrome_evidence_runtime(c4.RUNTIME)
    baseline_manifest = json.loads(c4.BASELINE_PATH.read_text(encoding="utf-8"))
    baseline = json.loads(c4.BASELINE_EVIDENCE.read_text(encoding="utf-8"))
    round5 = json.loads(c4.ROUND5_PATH.read_text(encoding="utf-8"))
    combined004 = json.loads(b4.EVIDENCE.read_text(encoding="utf-8"))
    schedule = r1.schedule()
    schedule_sha = r5.digest(schedule)
    assert (
        baseline_manifest["semantic_runtime_sha256"]
        == baseline["semantic_runtime_sha256"]
        == round5["semantic_runtime_sha256"]
        == combined004["semantic_runtime_sha256"]
        == c4.RUNTIME
    )
    assert (
        baseline_manifest["schedule_identity"]
        == baseline["schedule_sha256"]
        == round5["schedule_sha256"]
        == combined004["schedule_sha256"]
        == schedule_sha
    )
    assert combined004["environment_id"] == "OBL-COMBINED-004"
    assert len(baseline["combined_games"]) == len(combined004["combined_games"]) == 4500
    assert len(schedule) == 4500 and combined004["runtime_errors"] == 0
    parent_decks = {row["deck_key"]: row for row in baseline_manifest["decks"]}
    selected_hashes = {deck: row["sha256"] for deck, row in parent_decks.items()}
    selected_paths = {deck: row["source_path"] for deck, row in parent_decks.items()}
    for deck, experiment_id in SELECTION.items():
        row = round5["candidate_manifests"][experiment_id]
        prior = combined004["candidate_decisions"][experiment_id]
        assert prior["combined_verdict"] == "COMBINED_VALIDATION_PASSED"
        assert prior["promotion_eligibility"] == "PROMOTION_ELIGIBLE"
        assert row["deck_key"] == deck
        assert row["parent_sha256"] == parent_decks[deck]["sha256"]
        selected_hashes[deck] = row["candidate_sha256"]
        selected_paths[deck] = row["candidate_path"]
    assert set(selected_hashes) == set(r1.DECKS)
    for deck in r1.DECKS:
        c4.verify_deck_bytes(selected_paths[deck], selected_hashes[deck])
        assert (
            sum(r1.validate_deck(ROOT / selected_paths[deck], r1.catalog())["cards"].values()) == 60
        )

    baseline_cells = c4.grouped(baseline["combined_games"])
    candidate_cells = {
        deck: c4.grouped(round5["candidate_results"][experiment_id])
        for deck, experiment_id in SELECTION.items()
    }
    combined004_cells = c4.grouped(combined004["combined_games"])
    prior_provenance = {tuple(row["decks"]): row for row in combined004["provenance"]}
    expected_schedule = c4.schedules_by_pair(schedule)
    assert len(expected_schedule) == len(baseline_cells) == len(combined004_cells) == 45
    assert len(prior_provenance) == 45
    shared_pair = c4.pair_key(tuple(SELECTION))
    assert prior_provenance[shared_pair]["provenance"] == "COMBINED_004_NEW_PAIRING"
    assert prior_provenance[shared_pair]["deck_sha256"] == {
        deck: selected_hashes[deck] for deck in shared_pair
    }
    source_paths = {
        "BASELINE_002_REUSED": c4.BASELINE_EVIDENCE.relative_to(ROOT).as_posix(),
        "ROUND_5_REUSED": c4.ROUND5_PATH.relative_to(ROOT).as_posix(),
        "COMBINED_004_REUSED": b4.EVIDENCE.relative_to(ROOT).as_posix(),
    }
    source_hashes = {
        "BASELINE_002_REUSED": _source_sha(c4.BASELINE_EVIDENCE),
        "ROUND_5_REUSED": _source_sha(c4.ROUND5_PATH),
        "COMBINED_004_REUSED": _source_sha(b4.EVIDENCE),
    }
    provenance = []
    composed_games = []
    provenance_counts: Counter[str] = Counter()
    for pair in sorted(expected_schedule):
        candidate_decks = sorted(set(pair) & SELECTION.keys())
        if not candidate_decks:
            source_type = "BASELINE_002_REUSED"
            source_id = None
            games = baseline_cells[pair]
        elif len(candidate_decks) == 1:
            source_type = "ROUND_5_REUSED"
            source_id = SELECTION[candidate_decks[0]]
            games = candidate_cells[candidate_decks[0]][pair]
        else:
            assert pair == shared_pair
            source_type = "COMBINED_004_REUSED"
            source_id = None
            games = combined004_cells[pair]
            assert c4.fingerprint(games) == prior_provenance[pair]["matchup_fingerprint"]
        cell_fingerprint = c4.verify_cell(games, expected_schedule[pair], str(pair))
        provenance_counts[source_type] += 1
        composed_games.extend(games)
        provenance.append(
            {
                "decks": list(pair),
                "provenance": source_type,
                "source_artifact": source_paths[source_type],
                "source_artifact_sha256": source_hashes[source_type],
                "source_experiment_id": source_id,
                "semantic_runtime_sha256": c4.RUNTIME,
                "schedule_sha256": schedule_sha,
                "deck_sha256": {deck: selected_hashes[deck] for deck in pair},
                "game_count": 100,
                "orientation_counts": dict(
                    Counter(game["schedule"]["orientation"] for game in games)
                ),
                "matchup_fingerprint": cell_fingerprint,
            }
        )
    assert provenance_counts == {
        "BASELINE_002_REUSED": 28,
        "ROUND_5_REUSED": 16,
        "COMBINED_004_REUSED": 1,
    }
    assert len(provenance) == 45 and len(composed_games) == 4500
    assert len(c4.grouped(composed_games)) == 45

    rows = b3.matchup_rows(composed_games)
    deck_summary = r1.aggregate(composed_games, r1.DECKS)
    metrics = b3.summary_metrics(deck_summary, rows, composed_games)
    baseline_metrics = baseline_manifest["environment_metrics"]
    assert baseline_metrics == baseline["combined_global_metrics"]
    combined004_metrics = combined004["combined_global_metrics"]
    baseline_decks = b3.per_deck(
        baseline["combined_deck_summary"], b3.matchup_rows(baseline["combined_games"])
    )
    combined_decks = b3.per_deck(deck_summary, rows)
    combined004_decks = b3.per_deck(combined004["combined_deck_summary"], combined004["matchups"])
    per_deck = {}
    for deck in r1.DECKS:
        before, after, previous = (
            baseline_decks[deck],
            combined_decks[deck],
            combined004_decks[deck],
        )
        per_deck[deck] = {
            "baseline": {**before, "most_extreme_matchup": b4._most_extreme(before)},
            "combined_004": {**previous, "most_extreme_matchup": b4._most_extreme(previous)},
            "combined_005": {**after, "most_extreme_matchup": b4._most_extreme(after)},
            "win_rate_delta_from_baseline": round(after["win_rate"] - before["win_rate"], 6),
            "balance_error_delta_from_baseline": round(
                after["mean_matchup_balance_error"] - before["mean_matchup_balance_error"],
                6,
            ),
            "win_rate_delta_from_004": round(after["win_rate"] - previous["win_rate"], 6),
            "balance_error_delta_from_004": round(
                after["mean_matchup_balance_error"] - previous["mean_matchup_balance_error"],
                6,
            ),
        }
    combined004_rows = {tuple(row["decks"]): row for row in combined004["matchups"]}
    matchup_changes = []
    for row in rows:
        pair = tuple(row["decks"])
        previous = combined004_rows[pair]
        changed = c4.fingerprint(c4.grouped(composed_games)[pair]) != c4.fingerprint(
            combined004_cells[pair]
        )
        delta = round(row["deviation"] - previous["deviation"], 6)
        matchup_changes.append(
            {
                "decks": list(pair),
                "changed_source_cell": changed,
                "combined_004_rates": previous["win_rates"],
                "combined_005_rates": row["win_rates"],
                "combined_004_deviation": previous["deviation"],
                "combined_005_deviation": row["deviation"],
                "deviation_delta": delta,
                "balance_direction": (
                    "IMPROVED" if delta < 0 else "WORSENED" if delta > 0 else "UNCHANGED"
                ),
            }
        )
    assert sum(row["changed_source_cell"] for row in matchup_changes) == 9
    assert all(row["changed_source_cell"] == ("krang" in row["decks"]) for row in matchup_changes)
    interaction = {}
    for deck, experiment_id in SELECTION.items():
        isolated = round5["reports"][experiment_id]
        assert isolated["parent"]["win_rate"] == per_deck[deck]["baseline"]["win_rate"]
        isolated_delta = isolated["aggregate_win_rate_delta"]
        combined004_delta = combined004["isolated_to_combined"][deck]["combined_wr_delta"]
        combined005_delta = per_deck[deck]["win_rate_delta_from_baseline"]
        interaction[deck] = {
            "experiment_id": experiment_id,
            "isolated_candidate_wr": isolated["candidate"]["win_rate"],
            "isolated_wr_delta": isolated_delta,
            "combined_004_wr": per_deck[deck]["combined_004"]["win_rate"],
            "combined_004_wr_delta": combined004_delta,
            "combined_005_wr": per_deck[deck]["combined_005"]["win_rate"],
            "combined_005_wr_delta": combined005_delta,
            "combined_004_to_005_wr_delta": per_deck[deck]["win_rate_delta_from_004"],
            "classification": b4._delta_class(isolated_delta, combined005_delta),
            "isolated_balance_delta": isolated["balance_delta"],
            "combined_004_balance_delta": round(
                per_deck[deck]["combined_004"]["mean_matchup_balance_error"]
                - per_deck[deck]["baseline"]["mean_matchup_balance_error"],
                6,
            ),
            "combined_005_balance_delta": per_deck[deck]["balance_error_delta_from_baseline"],
        }
    roster = []
    for deck in r1.DECKS:
        experiment_id = SELECTION.get(deck)
        source = round5["candidate_manifests"][experiment_id] if experiment_id else None
        bytes_identity = c4.verify_deck_bytes(selected_paths[deck], selected_hashes[deck])
        roster.append(
            {
                "deck": r1.DISPLAY[deck],
                "deck_key": deck,
                "selection": experiment_id or "OBL-BASELINE-002",
                "source_path": selected_paths[deck],
                "sha256": selected_hashes[deck],
                "canonical_git_sha256": bytes_identity["git_sha256"],
                "parent_baseline_sha256": parent_decks[deck]["sha256"],
                "exact_diff": {
                    "removals": source["removals"] if source else {},
                    "additions": source["additions"] if source else {},
                },
            }
        )
    manifest = {
        "schema": "objective-balance-lab-combined-environment-v1",
        "environment_id": "OBL-COMBINED-005",
        "state": "EXPERIMENTAL_COMBINED_ENVIRONMENT",
        "source_repository_sha": EXPECTED_MAIN,
        "parent_environment": "OBL-BASELINE-002",
        "semantic_runtime_sha256": c4.RUNTIME,
        "schedule_sha256": schedule_sha,
        "selected_experiments": list(SELECTION.values()),
        "decks": roster,
        "logical_matchups": 45,
        "logical_games": 4500,
        "reused_games": 4500,
        "newly_executed_games": 0,
        "source_artifacts": source_paths,
    }
    evidence = {
        "schema": "objective-balance-lab-combined-environment-v1",
        "environment_id": "OBL-COMBINED-005",
        "state": "EXPERIMENTAL_COMBINED_ENVIRONMENT",
        "source_repository_sha": EXPECTED_MAIN,
        "parent_environment": "OBL-BASELINE-002",
        "manifest_path": MANIFEST.relative_to(ROOT).as_posix(),
        "manifest_content_sha256": r5.digest(manifest),
        "semantic_runtime_sha256": c4.RUNTIME,
        "schedule_sha256": schedule_sha,
        "logical_matchups": 45,
        "logical_games": 4500,
        "reused_games": 4500,
        "newly_executed_games": 0,
        "runtime_errors": 0,
        "provenance_counts": dict(provenance_counts),
        "provenance": provenance,
        "source_artifact_sha256": source_hashes,
        "combined_games": composed_games,
        "matchups": rows,
        "baseline_global_metrics": baseline_metrics,
        "combined_004_global_metrics": combined004_metrics,
        "combined_005_global_metrics": metrics,
        "baseline_to_005_global_delta": _metric_delta(baseline_metrics, metrics),
        "combined_004_to_005_global_delta": _metric_delta(combined004_metrics, metrics),
        "baseline_deck_summary": baseline["combined_deck_summary"],
        "combined_005_deck_summary": deck_summary,
        "per_deck_comparison": per_deck,
        "combined_004_to_005_matchup_changes": matchup_changes,
        "candidate_interactions": interaction,
        "candidate_decisions": DECISIONS,
        "environment_decision": ENVIRONMENT_DECISION,
        "recommended_promotion_subset": RECOMMENDED_SUBSET,
        "promotion_rationale": PROMOTION_RATIONALE,
    }
    return manifest, evidence


def render_selection(manifest: dict) -> str:
    lines = [
        "# Objective Balance Lab Combined Environment 005 — selection",
        "",
        "`OBL-COMBINED-005` is an experimental combined environment, not a promoted "
        "baseline. It selects only the two candidates marked promotion-eligible by "
        "[Combined 004](COMBINED_004_RESULTS.md), restoring Krang to exact Baseline 002.",
        "",
        "| Deck | Build | Source path | Recorded SHA-256 | Parent baseline SHA-256 |",
        "|---|---|---|---|---|",
    ]
    for row in manifest["decks"]:
        lines.append(
            f"| {row['deck']} | `{row['selection']}` | `{row['source_path']}` "
            f"| `{row['sha256']}` | `{row['parent_baseline_sha256']}` |"
        )
    lines += [
        "",
        "Shredder B: −1 Dream Beavers; −1 Shark Shredder, Killer Clone; +2 Tunnel Rats. "
        "April A (`OBL-R5-APRIL_ONEIL-A`, alias `OBL-R5-APRIL-A`): −2 Negate; "
        "+1 April, Reporter of the Weird; +1 Utrom Scientists. The other eight decks "
        "have no Round 5 diff in this environment.",
        "",
        "## Zero-new-game composition",
        "",
        "The matrix reuses 28 unchanged [Baseline 002](baselines/OBL_BASELINE_002_MANIFEST.json) "
        "cells, 16 [Round 5](ROUND_5_EVIDENCE.json) candidate-vs-baseline cells, "
        "and the exact Shredder B–April A cell from [Combined 004](COMBINED_004_EVIDENCE.json). "
        "All 45 cells have the same semantic runtime, frozen schedule, deck identities, "
        "100 games, 50/50 starts, and authenticated fingerprints. No game was rerun.",
        "",
        "Historical Baseline 002 SHA values can describe CRLF Windows checkout bytes; "
        "candidate SHA values identify canonical Git bytes. The verifier checks the "
        "recorded hash and exact card content across newline forms without treating "
        "different line endings as different deck lists.",
        "",
        f"Semantic runtime: `{manifest['semantic_runtime_sha256']}`. "
        f"Schedule: `{manifest['schedule_sha256']}`.",
        "",
        "[Combined 005 manifest](combined/OBL_COMBINED_005_MANIFEST.json) · "
        "[machine evidence](COMBINED_005_EVIDENCE.json).",
        "",
    ]
    return "\n".join(lines)


def render_results(evidence: dict) -> str:
    baseline = evidence["baseline_global_metrics"]
    combined004 = evidence["combined_004_global_metrics"]
    combined005 = evidence["combined_005_global_metrics"]

    def worst_split(metrics: dict) -> str:
        matchup = metrics["worst_matchup"]
        return " / ".join(
            f"{r1.DISPLAY[deck]} {b4._pct(matchup['win_rates'][deck])}" for deck in matchup["decks"]
        )

    lines = [
        "# Objective Balance Lab Combined Environment 005 — results",
        "",
        "The full 45-cell matrix is **4,500 logical games, 4,500 authenticated reused "
        "games, and zero newly executed games**: 28 Baseline 002, 16 Round 5, and one "
        "Combined 004 cell. Runtime errors: **0**. No deck or Cardcade semantics changed; "
        "no promotion occurred.",
        "",
        "[Selection](COMBINED_005_SELECTION.md) · [machine evidence](COMBINED_005_EVIDENCE.json).",
        "",
        "## Global comparison",
        "",
        "| Metric | Baseline 002 | Combined 004 | Combined 005 | 004→005 |",
        "|---|---:|---:|---:|---:|",
    ]
    for key, label, percent in (
        ("mean_matchup_balance_error", "Mean matchup balance error", True),
        ("median_matchup_deviation", "Median matchup deviation", True),
        ("over_60_40", ">60/40 cells", False),
        ("over_70_30", ">70/30 cells", False),
        ("aggregate_win_rate_spread", "Deck WR spread", True),
        ("aggregate_win_rate_stddev", "Deck WR standard deviation", True),
        ("mean_first_player_result_rate", "First-player result rate", True),
        ("mean_ending_turn", "Mean ending turn", False),
        ("median_ending_turn", "Median ending turn", False),
    ):
        old, prior, current = baseline[key], combined004[key], combined005[key]
        if percent:
            values = (b4._pct(old), b4._pct(prior), b4._pct(current), b4._pp(current - prior))
        elif key in {"over_60_40", "over_70_30"}:
            values = (str(old), str(prior), str(current), f"{current - prior:+d}")
        else:
            values = (str(old), str(prior), str(current), f"{current - prior:+.4f}")
        lines.append(f"| {label} | {values[0]} | {values[1]} | {values[2]} | {values[3]} |")
    lines += [
        "",
        f"Worst matchup: Baseline 002 {worst_split(baseline)}; "
        f"Combined 004 {worst_split(combined004)}; "
        f"Combined 005 {worst_split(combined005)}.",
        "",
        "## All ten decks versus Baseline 002",
        "",
        "| Deck | WR Baseline → 005 (Δ) | Mean error Baseline → 005 (Δ) "
        "| >60/40 | >70/30 | Most lopsided matchup Baseline → 005 |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for deck in r1.DECKS:
        row = evidence["per_deck_comparison"][deck]
        before, after = row["baseline"], row["combined_005"]
        old_worst = before["most_extreme_matchup"]
        new_worst = after["most_extreme_matchup"]
        lines.append(
            f"| {r1.DISPLAY[deck]} | {b4._pct(before['win_rate'])} → "
            f"{b4._pct(after['win_rate'])} ({b4._pp(row['win_rate_delta_from_baseline'])}) "
            f"| {b4._pct(before['mean_matchup_balance_error'])} → "
            f"{b4._pct(after['mean_matchup_balance_error'])} "
            f"({b4._pp(row['balance_error_delta_from_baseline'])}) "
            f"| {before['over_60_40']}→{after['over_60_40']} "
            f"| {before['over_70_30']}→{after['over_70_30']} "
            f"| {old_worst['opponent']} {b4._pct(old_worst['win_rate'])} → "
            f"{new_worst['opponent']} {b4._pct(new_worst['win_rate'])} |"
        )
    lines += [
        "",
        "## Removing Krang B: the nine changed matchup cells",
        "",
        "| Matchup | Combined 004 | Combined 005 | Deviation Δ | Balance direction |",
        "|---|---|---|---:|---|",
    ]
    changed = [
        row for row in evidence["combined_004_to_005_matchup_changes"] if row["changed_source_cell"]
    ]
    for row in changed:
        pair = row["decks"]
        lines.append(
            f"| {' / '.join(pair)} | "
            + " / ".join(f"{deck} {b4._pct(row['combined_004_rates'][deck])}" for deck in pair)
            + " | "
            + " / ".join(f"{deck} {b4._pct(row['combined_005_rates'][deck])}" for deck in pair)
            + f" | {b4._pp(row['deviation_delta'])} | {row['balance_direction']} |"
        )
    counts = Counter(row["balance_direction"] for row in changed)
    lines += [
        "",
        f"Restoring baseline Krang changes exactly nine cells: {counts['IMPROVED']} "
        f"less lopsided, {counts['WORSENED']} more lopsided, and "
        f"{counts['UNCHANGED']} unchanged in absolute 50% deviation. The other "
        "36 cell results remain byte-identical to Combined 004.",
        "",
        "## Candidate interactions and decisions",
        "",
        "| Candidate | Isolated WR / Δ | Combined 004 WR / Δ | Combined 005 WR / Δ "
        "| Classification | Combined 005 verdict | Eligibility |",
        "|---|---:|---:|---:|---|---|---|",
    ]
    for row in evidence["candidate_interactions"].values():
        decision = evidence["candidate_decisions"][row["experiment_id"]]
        lines.append(
            f"| `{row['experiment_id']}` | {b4._pct(row['isolated_candidate_wr'])} "
            f"({b4._pp(row['isolated_wr_delta'])}) | "
            f"{b4._pct(row['combined_004_wr'])} "
            f"({b4._pp(row['combined_004_wr_delta'])}) | "
            f"{b4._pct(row['combined_005_wr'])} "
            f"({b4._pp(row['combined_005_wr_delta'])}) | {row['classification']} "
            f"| {decision['combined_verdict']} | {decision['promotion_eligibility']} |"
        )
    lines += ["", "## Verdict and promotion gate", ""]
    for experiment_id, decision in evidence["candidate_decisions"].items():
        lines.append(f"- `{experiment_id}`: {decision['rationale']}")
    lines += [
        "",
        f"Environment decision: **{evidence['environment_decision']}**. "
        "Recommended subset for a separate, explicit promotion decision: "
        + (
            ", ".join(f"`{item}`" for item in evidence["recommended_promotion_subset"])
            if evidence["recommended_promotion_subset"]
            else "none"
        )
        + ". No promotion or Baseline 003 creation occurs here.",
        "",
        evidence["promotion_rationale"],
        "",
        "Mean balance error is the mean over 45 cells of |((wins + draws/2)/100) − "
        "50%|; threshold counts are strict. Reporter combat-draw and other unavailable "
        "effect-use telemetry are not credited.",
        "",
    ]
    return "\n".join(lines)


def publish(manifest: dict, evidence: dict) -> None:
    assert set(DECISIONS) == set(SELECTION.values())
    assert ENVIRONMENT_DECISION in {
        "COMBINED_ENVIRONMENT_IMPROVED",
        "COMBINED_ENVIRONMENT_MIXED",
        "COMBINED_ENVIRONMENT_REGRESSED",
        "COMBINED_ENVIRONMENT_INCONCLUSIVE",
    }
    assert set(RECOMMENDED_SUBSET) <= {
        experiment_id
        for experiment_id, decision in DECISIONS.items()
        if decision["promotion_eligibility"] == "PROMOTION_ELIGIBLE"
    }
    assert PROMOTION_RATIONALE
    r5.write_json_atomic(MANIFEST, manifest)
    r5.write_json_atomic(EVIDENCE, evidence)
    SELECTION_DOC.write_text(render_selection(manifest), encoding="utf-8")
    RESULTS_DOC.write_text(render_results(evidence), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    manifest, evidence = build()
    if args.write:
        publish(manifest, evidence)
        print(json.dumps({"status": "PUBLISHED", "logical_games": 4500, "new_games": 0}))
    else:
        print(
            json.dumps(
                {
                    "baseline": evidence["baseline_global_metrics"],
                    "combined_004": evidence["combined_004_global_metrics"],
                    "combined_005": evidence["combined_005_global_metrics"],
                    "per_deck": {
                        deck: {
                            "baseline_wr": row["baseline"]["win_rate"],
                            "combined_004_wr": row["combined_004"]["win_rate"],
                            "combined_005_wr": row["combined_005"]["win_rate"],
                            "balance_delta_from_baseline": row["balance_error_delta_from_baseline"],
                            "extremes_60": (
                                row["baseline"]["over_60_40"],
                                row["combined_005"]["over_60_40"],
                            ),
                            "extremes_70": (
                                row["baseline"]["over_70_30"],
                                row["combined_005"]["over_70_30"],
                            ),
                        }
                        for deck, row in evidence["per_deck_comparison"].items()
                    },
                    "changed_matchups": [
                        row
                        for row in evidence["combined_004_to_005_matchup_changes"]
                        if row["changed_source_cell"]
                    ],
                    "interactions": evidence["candidate_interactions"],
                },
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
