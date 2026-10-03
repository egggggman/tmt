"""Compose authenticated Combined 004 cells and publish comparison evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
sys.path.insert(0, str(ROOT / "tools"))

import build_combined003_runtime_compatible as b3  # noqa: E402
import run_combined_004 as c4  # noqa: E402
import run_objective_balance_lab_round1 as r1  # noqa: E402
import run_objective_balance_lab_round5 as r5  # noqa: E402

MANIFEST = OBL / "combined/OBL_COMBINED_004_MANIFEST.json"
EVIDENCE = OBL / "COMBINED_004_EVIDENCE.json"
SELECTION_DOC = OBL / "COMBINED_004_SELECTION.md"
RESULTS_DOC = OBL / "COMBINED_004_RESULTS.md"

DECISIONS: dict[str, dict[str, str]] = {
    "OBL-R5-SHREDDER-B": {
        "combined_verdict": "COMBINED_VALIDATION_PASSED",
        "promotion_eligibility": "PROMOTION_ELIGIBLE",
        "rationale": (
            "Shredder falls 75.00%→71.00%, improves its nine-matchup balance error "
            "4.00 pp, and reduces >70/30 pairings 6→5 without adding >60/40 cells. "
            "The isolated downward effect strengthens in combination. It remains a "
            "strong villain deck, but its Foot/minion pressure identity is preserved."
        ),
    },
    "OBL-R5-APRIL_ONEIL-A": {
        "combined_verdict": "COMBINED_VALIDATION_PASSED",
        "promotion_eligibility": "PROMOTION_ELIGIBLE",
        "rationale": (
            "April rises 25.78%→28.78% and improves balance error 3.00 pp; >60/40 "
            "falls 7→6 and the 9% baseline worst split improves to 14% against "
            "Casey. Her isolated gain weakens by 1.00 pp, yet remains meaningful "
            "against a tougher combined meta. Reporter/Utrom reinforce adaptive "
            "development without crediting unsupported combat-draw."
        ),
    },
    "OBL-R5-KRANG-B": {
        "combined_verdict": "COMBINED_VALIDATION_MIXED",
        "promotion_eligibility": "NOT_PROMOTION_ELIGIBLE",
        "rationale": (
            "Krang rises 35.11%→43.33% and improves balance error 2.22 pp, so the "
            "isolated gain strengthens. But his >60/40 count remains 6→8, exactly "
            "the distribution risk flagged at selection; >70/30 is unchanged at 4. "
            "The 18% result against Shredder B remains severe. Two artifact-linked "
            "Donatello cameos preserve technology identity, but this unresolved "
            "extremity prevents a promotion recommendation."
        ),
    },
}
ENVIRONMENT_DECISION = "COMBINED_ENVIRONMENT_IMPROVED"
RECOMMENDED_SUBSET = ["OBL-R5-SHREDDER-B", "OBL-R5-APRIL_ONEIL-A"]
SUBSET_RATIONALE = (
    "Recommend only Shredder B and April A for a separate promotion gate, after "
    "recomposing and validating the exact two-candidate matrix with baseline Krang. "
    "Replace Combined 004's Krang B cells with seven Baseline 002 Krang-vs-unchanged "
    "cells, Shredder B vs baseline Krang and April A vs baseline Krang from Round 5; "
    "retain the authenticated Shredder B vs April A new cell. All those cells already "
    "exist at the same runtime, so no new simulations appear necessary, but the subset "
    "must be validated as its own combined environment before any promotion."
)


def _rate(games: list[dict], deck: str) -> float:
    return (
        sum(game["winner"] == deck for game in games) + sum(game["draw"] for game in games) / 2
    ) / len(games)


def _pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _pp(value: float) -> str:
    return f"{value * 100:+.2f} pp"


def _source_sha(relative: str) -> str:
    return r5.git_blob_sha(relative)


def _new_pair_summary(pair: tuple[str, str], games: list[dict]) -> dict:
    rates = {deck: round(_rate(games, deck), 6) for deck in pair}
    starts = {deck: [game for game in games if game["first_player"] == deck] for deck in pair}
    assert all(len(rows) == 50 for rows in starts.values())
    return {
        "decks": list(pair),
        "games": 100,
        "win_rates": rates,
        "wins": {deck: sum(game["winner"] == deck for game in games) for deck in pair},
        "draws": sum(game["draw"] for game in games),
        "starting_seat_games": {deck: 50 for deck in pair},
        "starting_seat_win_rates": {deck: round(_rate(starts[deck], deck), 6) for deck in pair},
        "mean_ending_turn": round(statistics.mean(game["turn"] for game in games), 4),
        "median_ending_turn": statistics.median(game["turn"] for game in games),
        "over_60_40": max(abs(rate - 0.5) for rate in rates.values()) > 0.1,
        "over_70_30": max(abs(rate - 0.5) for rate in rates.values()) > 0.2,
    }


def _most_extreme(deck_row: dict) -> dict:
    opponent = max(
        deck_row["matchup_win_rates"],
        key=lambda name: abs(deck_row["matchup_win_rates"][name] - 0.5),
    )
    return {"opponent": opponent, "win_rate": deck_row["matchup_win_rates"][opponent]}


def _delta_class(isolated: float, combined: float) -> str:
    if isolated * combined < 0:
        return "DELTA_REVERSES"
    if abs(combined) < abs(isolated) - 0.000001:
        return "DELTA_WEAKENS"
    if abs(combined) > abs(isolated) + 0.000001:
        return "DELTA_STRENGTHENS"
    return "DELTA_PERSISTS"


def build() -> tuple[dict, dict, dict]:
    baseline_manifest, baseline, round5, parent_decks, paths, selected_hashes, schedule = (
        c4.preflight()
    )
    checkpoint = json.loads(c4.NEW_CHECKPOINT.read_text(encoding="utf-8"))
    new_pairs = json.loads(c4.NEW_PAIRS.read_text(encoding="utf-8"))
    expected_checkpoint = c4.expected_checkpoint(r5.digest(schedule), selected_hashes)
    c4.verify_checkpoint(checkpoint, expected_checkpoint, schedule)
    c4.verify_checkpoint(new_pairs, expected_checkpoint, schedule)
    assert checkpoint == new_pairs
    assert len(new_pairs["completed_pairs"]) == 3
    source_schedule = c4.schedules_by_pair(schedule)
    baseline_cells = c4.grouped(baseline["combined_games"])
    candidate_cells = {
        deck: c4.grouped(round5["candidate_results"][experiment_id])
        for deck, experiment_id in c4.SELECTION.items()
    }
    source_paths = {
        "BASELINE_002_REUSED": c4.BASELINE_EVIDENCE.relative_to(ROOT).as_posix(),
        "ROUND_5_REUSED": c4.ROUND5_PATH.relative_to(ROOT).as_posix(),
        "COMBINED_004_NEW_PAIRING": c4.NEW_PAIRS.relative_to(ROOT).as_posix(),
    }
    source_sha = {
        "BASELINE_002_REUSED": _source_sha(source_paths["BASELINE_002_REUSED"]),
        "ROUND_5_REUSED": _source_sha(source_paths["ROUND_5_REUSED"]),
        "COMBINED_004_NEW_PAIRING": hashlib.sha256(
            c4.NEW_PAIRS.read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest(),
    }
    provenance = []
    composed_games = []
    provenance_counts: Counter[str] = Counter()
    for pair in sorted(source_schedule):
        candidate_decks = sorted(set(pair) & c4.SELECTION.keys())
        if not candidate_decks:
            label = "BASELINE_002_REUSED"
            source_id = None
            games = baseline_cells[pair]
        elif len(candidate_decks) == 1:
            label = "ROUND_5_REUSED"
            source_id = c4.SELECTION[candidate_decks[0]]
            games = candidate_cells[candidate_decks[0]][pair]
        else:
            label = "COMBINED_004_NEW_PAIRING"
            source_id = None
            games = new_pairs["completed_pairs"]["|".join(pair)]
        source_fingerprint = c4.verify_cell(games, source_schedule[pair], str(pair))
        provenance_counts[label] += 1
        composed_games.extend(games)
        provenance.append(
            {
                "decks": list(pair),
                "provenance": label,
                "source_artifact": source_paths[label],
                "source_artifact_sha256": source_sha[label],
                "source_experiment_id": source_id,
                "semantic_runtime_sha256": c4.RUNTIME,
                "schedule_sha256": r5.digest(schedule),
                "deck_sha256": {deck: selected_hashes[deck] for deck in pair},
                "game_count": 100,
                "orientation_counts": dict(
                    Counter(game["schedule"]["orientation"] for game in games)
                ),
                "matchup_fingerprint": source_fingerprint,
            }
        )
    assert len(composed_games) == 4500 and len(provenance) == 45
    assert provenance_counts == {
        "BASELINE_002_REUSED": 21,
        "ROUND_5_REUSED": 21,
        "COMBINED_004_NEW_PAIRING": 3,
    }
    assert len(c4.grouped(composed_games)) == 45
    rows = b3.matchup_rows(composed_games)
    combined_summary = r1.aggregate(composed_games, r1.DECKS)
    combined_metrics = b3.summary_metrics(combined_summary, rows, composed_games)
    baseline_metrics = baseline_manifest["environment_metrics"]
    baseline_recomputed = b3.summary_metrics(
        baseline["combined_deck_summary"],
        b3.matchup_rows(baseline["combined_games"]),
        baseline["combined_games"],
    )
    assert baseline_recomputed == baseline_metrics
    baseline_decks = b3.per_deck(
        baseline["combined_deck_summary"], b3.matchup_rows(baseline["combined_games"])
    )
    combined_decks = b3.per_deck(combined_summary, rows)
    per_deck = {}
    for deck in r1.DECKS:
        before, after = baseline_decks[deck], combined_decks[deck]
        per_deck[deck] = {
            "baseline": {**before, "most_extreme_matchup": _most_extreme(before)},
            "combined": {**after, "most_extreme_matchup": _most_extreme(after)},
            "win_rate_delta": round(after["win_rate"] - before["win_rate"], 6),
            "balance_error_delta": round(
                after["mean_matchup_balance_error"] - before["mean_matchup_balance_error"],
                6,
            ),
        }
    new_summaries = {
        label: _new_pair_summary(tuple(label.split("|")), games)
        for label, games in new_pairs["completed_pairs"].items()
    }
    isolated_to_combined = {}
    for deck, experiment_id in c4.SELECTION.items():
        isolated = round5["reports"][experiment_id]
        assert isolated["parent"]["win_rate"] == per_deck[deck]["baseline"]["win_rate"]
        combined_delta = per_deck[deck]["win_rate_delta"]
        isolated_delta = isolated["aggregate_win_rate_delta"]
        isolated_to_combined[deck] = {
            "experiment_id": experiment_id,
            "isolated_parent_wr": isolated["parent"]["win_rate"],
            "isolated_candidate_wr": isolated["candidate"]["win_rate"],
            "isolated_wr_delta": isolated_delta,
            "isolated_balance_delta": isolated["balance_delta"],
            "combined_candidate_wr": per_deck[deck]["combined"]["win_rate"],
            "combined_wr_delta": combined_delta,
            "combined_balance_delta": per_deck[deck]["balance_error_delta"],
            "classification": _delta_class(isolated_delta, combined_delta),
        }
    assert len(isolated_to_combined) == 3

    roster = []
    for deck in r1.DECKS:
        experiment_id = c4.SELECTION.get(deck)
        parent_row = parent_decks[deck]
        selected_path = paths[deck]
        selected_sha = selected_hashes[deck]
        byte_identity = c4.verify_deck_bytes(selected_path, selected_sha)
        changed = round5["candidate_manifests"][experiment_id] if experiment_id else None
        roster.append(
            {
                "deck": r1.DISPLAY[deck],
                "deck_key": deck,
                "selection": experiment_id or "OBL-BASELINE-002",
                "source_path": selected_path,
                "sha256": selected_sha,
                "canonical_git_sha256": byte_identity["git_sha256"],
                "parent_baseline_sha256": parent_row["sha256"],
                "exact_diff": {
                    "removals": changed["removals"] if changed else {},
                    "additions": changed["additions"] if changed else {},
                },
            }
        )
    manifest = {
        "schema": "objective-balance-lab-combined-environment-v1",
        "environment_id": "OBL-COMBINED-004",
        "state": "EXPERIMENTAL_COMBINED_ENVIRONMENT",
        "source_repository_sha": c4.EXPECTED_MAIN,
        "parent_environment": "OBL-BASELINE-002",
        "parent_manifest_path": c4.BASELINE_PATH.relative_to(ROOT).as_posix(),
        "parent_manifest_git_sha256": _source_sha(c4.BASELINE_PATH.relative_to(ROOT).as_posix()),
        "semantic_runtime_sha256": c4.RUNTIME,
        "schedule_sha256": r5.digest(schedule),
        "selected_experiments": list(c4.SELECTION.values()),
        "decks": roster,
        "logical_matchups": 45,
        "logical_games": 4500,
        "reused_games": 4200,
        "newly_executed_games": 300,
        "source_artifacts": source_paths,
    }
    evidence = {
        "schema": "objective-balance-lab-combined-environment-v1",
        "environment_id": "OBL-COMBINED-004",
        "state": "EXPERIMENTAL_COMBINED_ENVIRONMENT",
        "source_repository_sha": c4.EXPECTED_MAIN,
        "parent_environment": "OBL-BASELINE-002",
        "manifest_path": MANIFEST.relative_to(ROOT).as_posix(),
        "manifest_content_sha256": r5.digest(manifest),
        "semantic_runtime_sha256": c4.RUNTIME,
        "schedule_sha256": r5.digest(schedule),
        "logical_matchups": 45,
        "logical_games": 4500,
        "reused_games": 4200,
        "newly_executed_games": 300,
        "runtime_errors": 0,
        "provenance_counts": dict(provenance_counts),
        "provenance": provenance,
        "source_artifact_sha256": source_sha,
        "combined_games": composed_games,
        "matchups": rows,
        "baseline_global_metrics": baseline_metrics,
        "combined_global_metrics": combined_metrics,
        "global_balance_delta": round(
            combined_metrics["mean_matchup_balance_error"]
            - baseline_metrics["mean_matchup_balance_error"],
            6,
        ),
        "baseline_deck_summary": baseline["combined_deck_summary"],
        "combined_deck_summary": combined_summary,
        "per_deck_comparison": per_deck,
        "novel_matchups": new_summaries,
        "isolated_to_combined": isolated_to_combined,
        "candidate_decisions": DECISIONS,
        "environment_decision": ENVIRONMENT_DECISION,
        "recommended_promotion_subset": RECOMMENDED_SUBSET,
        "subset_rationale": SUBSET_RATIONALE,
    }
    return manifest, evidence, round5


def render_selection(manifest: dict, round5: dict) -> str:
    lines = [
        "# Objective Balance Lab Combined Environment 004 — selection",
        "",
        "`OBL-COMBINED-004` is an experimental combined environment, not a baseline. "
        "No deck list, official prototype, Cardcade semantics, or promotion history changed.",
        "",
        "The three selected candidates were already `ACCEPT_FOR_COMBINED_MATRIX` in "
        "[Round 5](ROUND_5_RESULTS.md). The other seven decks are exact "
        "[Baseline 002](baselines/OBL_BASELINE_002_MANIFEST.json) builds.",
        "",
        "| Deck | Build | Exact source | Recorded SHA-256 | Baseline parent SHA-256 |",
        "|---|---|---|---|---|",
    ]
    for row in manifest["decks"]:
        lines.append(
            f"| {row['deck']} | `{row['selection']}` | `{row['source_path']}` "
            f"| `{row['sha256']}` | `{row['parent_baseline_sha256']}` |"
        )
    lines += [
        "",
        "## Selection rationale",
        "",
        "- Shredder B tests a split reduction in early and closing pressure; its isolated "
        "balance error improved 2.56 pp without adding >60/40 cells.",
        "- April A tests proactive development from two Negate slots; isolated balance "
        "error improved 4.00 pp and >60/40 fell 7→5. Reporter combat-draw is not "
        "credited as a simulated effect.",
        "- Krang B tests an artifact-linked midgame body. Its isolated balance error "
        "improved 1.67 pp, but >60/40 rose 6→8; this is the specific combined-risk gate.",
        "",
        "The Round 5 parent Negates recorded zero casts. Thus April and Krang are "
        "testing active bodies replacing dormant simulation slots, not the cost of "
        "counterspells actually used.",
        "",
        "## Composition contract",
        "",
        "Reuse 21 unchanged Baseline 002 cells and 21 Round 5 candidate-vs-baseline "
        "cells; execute only the three candidate-vs-candidate cells (300 games). "
        "Every cell retains source artifact, source fingerprint, exact frozen schedule, "
        "50/50 orientation, deck hashes, and semantic runtime identity.",
        "",
        "Some historical Baseline 002 deck SHA-256 values were recorded from CRLF "
        "Windows checkout bytes, while candidate SHA-256 values identify canonical LF "
        "Git bytes. The manifest records the authoritative historical SHA and canonical "
        "Git SHA; the verifier independently calculates checkout SHA. Composition "
        "verifies exact recorded hashes and "
        "byte equality after newline normalization; no card content is normalized away.",
        "",
        f"Semantic runtime: `{manifest['semantic_runtime_sha256']}`. "
        f"Frozen schedule: `{manifest['schedule_sha256']}`.",
        "",
        "[Combined manifest](combined/OBL_COMBINED_004_MANIFEST.json) · "
        "[Machine evidence](COMBINED_004_EVIDENCE.json).",
        "",
    ]
    assert set(round5["provisional_combined_004_pool"].values()) == set(
        manifest["selected_experiments"]
    )
    return "\n".join(lines)


def render_results(evidence: dict) -> str:
    baseline = evidence["baseline_global_metrics"]
    combined = evidence["combined_global_metrics"]
    lines = [
        "# Objective Balance Lab Combined Environment 004 — results",
        "",
        "The 45-cell logical matrix contains **4,500 games**: **4,200 authenticated "
        "reused** games and **300 newly executed** games. Provenance is 21 Baseline "
        "002 cells, 21 Round 5 cells, and three new candidate-vs-candidate cells. "
        "Runtime errors: **0**. No promotion occurred.",
        "",
        "[Selection](COMBINED_004_SELECTION.md) · "
        "[Machine evidence](COMBINED_004_EVIDENCE.json) · "
        "[New-pair checkpoint](COMBINED_004_NEW_PAIRS.checkpoint.json).",
        "",
        "## Environment balance",
        "",
        "| Metric | Baseline 002 | Combined 004 | Change |",
        "|---|---:|---:|---:|",
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
        before, after = baseline[key], combined[key]
        if percent:
            cells = (_pct(before), _pct(after), _pp(after - before))
        else:
            cells = (str(before), str(after), f"{after - before:+.4f}")
        lines.append(f"| {label} | {cells[0]} | {cells[1]} | {cells[2]} |")
    before_worst, after_worst = baseline["worst_matchup"], combined["worst_matchup"]
    lines += [
        "",
        "Most lopsided matchup: "
        f"{before_worst['decks']} {before_worst['win_rates']} → "
        f"{after_worst['decks']} {after_worst['win_rates']}.",
        "",
        "## All ten decks",
        "",
        "| Deck | WR Baseline → combined (Δ) | Mean error Baseline → combined (Δ) "
        "| >60/40 | >70/30 | Most lopsided matchup Baseline → combined |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for deck in r1.DECKS:
        row = evidence["per_deck_comparison"][deck]
        before, after = row["baseline"], row["combined"]
        worst_before, worst_after = before["most_extreme_matchup"], after["most_extreme_matchup"]
        lines.append(
            f"| {r1.DISPLAY[deck]} | {_pct(before['win_rate'])} → "
            f"{_pct(after['win_rate'])} ({_pp(row['win_rate_delta'])}) "
            f"| {_pct(before['mean_matchup_balance_error'])} → "
            f"{_pct(after['mean_matchup_balance_error'])} "
            f"({_pp(row['balance_error_delta'])}) "
            f"| {before['over_60_40']}→{after['over_60_40']} "
            f"| {before['over_70_30']}→{after['over_70_30']} "
            f"| {worst_before['opponent']} {_pct(worst_before['win_rate'])} → "
            f"{worst_after['opponent']} {_pct(worst_after['win_rate'])} |"
        )
    lines += [
        "",
        "## Three novel interactions",
        "",
        "| Matchup | Exact WR split | On-play WR by deck (50 starts each) "
        "| Mean / median ending turn | >60/40 | >70/30 |",
        "|---|---|---|---:|---|---|",
    ]
    for label, row in sorted(evidence["novel_matchups"].items()):
        lines.append(
            f"| {label} | "
            + " / ".join(f"{deck} {_pct(row['win_rates'][deck])}" for deck in row["decks"])
            + " | "
            + " / ".join(
                f"{deck} {_pct(row['starting_seat_win_rates'][deck])}" for deck in row["decks"]
            )
            + f" | {row['mean_ending_turn']} / {row['median_ending_turn']} "
            + f"| {row['over_60_40']} | {row['over_70_30']} |"
        )
    lines += [
        "",
        "## Isolated-to-combined effects",
        "",
        "| Candidate | Isolated WR and Δ | Combined WR and Δ | Isolated balance Δ "
        "| Combined balance Δ | Classification | Combined verdict | Eligibility |",
        "|---|---:|---:|---:|---:|---|---|---|",
    ]
    for row in evidence["isolated_to_combined"].values():
        decision = evidence["candidate_decisions"][row["experiment_id"]]
        lines.append(
            f"| `{row['experiment_id']}` | {_pct(row['isolated_candidate_wr'])} "
            f"({_pp(row['isolated_wr_delta'])}) | {_pct(row['combined_candidate_wr'])} "
            f"({_pp(row['combined_wr_delta'])}) | {_pp(row['isolated_balance_delta'])} "
            f"| {_pp(row['combined_balance_delta'])} | {row['classification']} "
            f"| {decision['combined_verdict']} | {decision['promotion_eligibility']} |"
        )
    lines += ["", "## Decision", ""]
    for experiment_id, decision in evidence["candidate_decisions"].items():
        lines.append(f"- `{experiment_id}`: {decision['rationale']}")
    lines += [
        "",
        f"Environment: **{evidence['environment_decision']}**. "
        f"Global Balance Δ **{_pp(evidence['global_balance_delta'])}**.",
        "",
        "Recommended promotion subset (recommendation only; no promotion here): "
        + (
            ", ".join(f"`{item}`" for item in evidence["recommended_promotion_subset"])
            if evidence["recommended_promotion_subset"]
            else "Recommended promotion subset: **none**. No promotion here."
        ),
        "",
        evidence["subset_rationale"],
        "",
        "Mean balance error is the mean across 45 cells of "
        "|((wins + draws/2)/100) − 50%|. Threshold counts use strict >60/40 and "
        ">70/30. A baseline opponent replaced by another candidate is an interaction "
        "effect, not a fresh isolated test. No unsupported Reporter combat-draw or "
        "unavailable artifact activation telemetry is credited.",
        "",
    ]
    return "\n".join(lines)


def publish(manifest: dict, evidence: dict, round5: dict) -> None:
    assert set(DECISIONS) == set(c4.SELECTION.values())
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
    assert SUBSET_RATIONALE
    r5.write_json_atomic(MANIFEST, manifest)
    r5.write_json_atomic(EVIDENCE, evidence)
    SELECTION_DOC.write_text(render_selection(manifest, round5), encoding="utf-8")
    RESULTS_DOC.write_text(render_results(evidence), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    manifest, evidence, round5 = build()
    if args.write:
        publish(manifest, evidence, round5)
        print(json.dumps({"status": "PUBLISHED", "logical_games": 4500, "new_games": 300}))
    else:
        print(
            json.dumps(
                {
                    "baseline": evidence["baseline_global_metrics"],
                    "combined": evidence["combined_global_metrics"],
                    "new_matchups": evidence["novel_matchups"],
                    "per_deck": {
                        deck: {
                            "baseline_wr": row["baseline"]["win_rate"],
                            "combined_wr": row["combined"]["win_rate"],
                            "balance_delta": row["balance_error_delta"],
                            "over_60": (
                                row["baseline"]["over_60_40"],
                                row["combined"]["over_60_40"],
                            ),
                            "over_70": (
                                row["baseline"]["over_70_30"],
                                row["combined"]["over_70_30"],
                            ),
                        }
                        for deck, row in evidence["per_deck_comparison"].items()
                    },
                    "effects": evidence["isolated_to_combined"],
                },
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
