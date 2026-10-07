"""Compose the R8-A Combined Environment from accepted, runtime-compatible cells."""

# Evidence prose and cross-artifact assertions retain complete lines.
# ruff: noqa: E501

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_combined003_runtime_compatible as metrics  # noqa: E402
import build_objective_balance_lab_round8a_results as isolated  # noqa: E402
import run_objective_balance_lab_round8a as run  # noqa: E402

OUT = run.OBL / "combined"
MANIFEST = OUT / "OBL_COMBINED_007_MANIFEST.json"
EVIDENCE = run.OBL / "COMBINED_007_R8A_EVIDENCE.json.gz"
REPORT = run.OBL / "COMBINED_007_R8A_RESULTS.md"
ENVIRONMENT = "OBL-COMBINED-007"
ACCEPTED_PR = "https://github.com/egggggman/tmt/pull/275"
ACCEPTED_MERGE = "75133aecde12f0dc979424e324debc465021c788"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build() -> dict:
    authority, baseline_manifest, schedule, _ = run.preflight()
    control = run.read(run.RESULT)
    candidate = run.read(run.CANDIDATE_RESULT)
    selected = [row for row in schedule if "bebop_rocksteady" in row["pair"]]
    run.verify(
        control, run.template(authority, baseline_manifest, schedule), schedule, complete=True
    )
    run.verify(
        candidate,
        run.template(authority, baseline_manifest, selected, candidate=True),
        selected,
        complete=True,
        replay_pairs=run.SELECTED_REPLAY_PAIRS,
    )
    analysis = isolated.build()
    assert analysis == json.loads(isolated.ANALYSIS.read_text())
    assert control["semantic_runtime_sha256"] == candidate["semantic_runtime_sha256"]
    assert control["schedule_sha256"] == candidate["schedule_sha256"]
    assert candidate["runtime_control_sha256"] == sha(run.RESULT)
    assert candidate["candidate_deck_sha256"] == authority["candidate_sha256"]
    assert control["runtime_errors"] == candidate["runtime_errors"] == 0

    control_by_schedule = {run.digest(game["schedule"]): game for game in control["games"]}
    candidate_by_schedule = {run.digest(game["schedule"]): game for game in candidate["games"]}
    assert len(control_by_schedule) == 4500 and len(candidate_by_schedule) == 900
    assert set(candidate_by_schedule).issubset(control_by_schedule)
    games = [
        candidate_by_schedule.get(run.digest(row), control_by_schedule[run.digest(row)])
        for row in schedule
    ]
    assert len(games) == 4500
    assert [game["schedule"] for game in games] == schedule
    assert all(game["runtime_error"] is None for game in games)

    deck_rows = []
    for row in baseline_manifest["decks"]:
        if row["deck_key"] == "bebop_rocksteady":
            deck_rows.append(
                {
                    "deck": row["deck"],
                    "deck_key": "bebop_rocksteady",
                    "selection": "OBL-R8-BEBOP-A",
                    "source_path": run.CANDIDATE.relative_to(ROOT).as_posix(),
                    "sha256": authority["candidate_sha256"],
                    "parent_baseline_sha256": row["sha256"],
                    "exact_diff": {
                        "removals": {"Illegitimate Business": 2},
                        "additions": {"Primordial Pachyderm": 2},
                    },
                }
            )
        else:
            deck_rows.append(
                {
                    "deck": row["deck"],
                    "deck_key": row["deck_key"],
                    "selection": "OBL-BASELINE-004",
                    "source_path": row["source_path"],
                    "sha256": row["sha256"],
                    "parent_baseline_sha256": row["sha256"],
                    "exact_diff": {"removals": {}, "additions": {}},
                }
            )
    manifest = {
        "schema": "objective-balance-lab-combined-environment-v1",
        "environment_id": ENVIRONMENT,
        "state": "EXPERIMENTAL_COMBINED_ENVIRONMENT",
        "parent_environment": "OBL-BASELINE-004",
        "selected_experiments": ["OBL-R8-BEBOP-A"],
        "semantic_runtime_sha256": authority["semantic_runtime_sha256"],
        "schedule_sha256": control["schedule_sha256"],
        "baseline_manifest_sha256": sha(run.MANIFEST),
        "candidate_sha256": authority["candidate_sha256"],
        "accepted_isolated_record": {"pull_request": ACCEPTED_PR, "merge_commit": ACCEPTED_MERGE},
        "source_artifacts": {
            "BASELINE_004_REUSED": run.RESULT.relative_to(ROOT).as_posix(),
            "ROUND_8_A_REUSED": run.CANDIDATE_RESULT.relative_to(ROOT).as_posix(),
        },
        "source_artifact_sha256": {
            "BASELINE_004_REUSED": sha(run.RESULT),
            "ROUND_8_A_REUSED": sha(run.CANDIDATE_RESULT),
        },
        "decks": deck_rows,
        "logical_matchups": 45,
        "logical_games": 4500,
        "reused_games": 4500,
        "newly_executed_games": 0,
        "promotion_authorized": False,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    write_json(MANIFEST, manifest)
    provenance = []
    for offset in range(0, len(schedule), 100):
        cell = games[offset : offset + 100]
        pair = cell[0]["schedule"]["pair"]
        key = "|".join(pair)
        source = "ROUND_8_A_REUSED" if "bebop_rocksteady" in pair else "BASELINE_004_REUSED"
        source_payload = candidate if source == "ROUND_8_A_REUSED" else control
        assert len(cell) == 100
        assert Counter(game["first_player"] for game in cell) == {deck: 50 for deck in pair}
        assert run.digest(cell) == source_payload["cell_hashes"][key]
        assert all(game["seats"] == game["schedule"]["decks"] for game in cell)
        provenance.append(
            {
                "decks": pair,
                "source": source,
                "source_artifact": manifest["source_artifacts"][source],
                "source_artifact_sha256": manifest["source_artifact_sha256"][source],
                "source_experiment": "OBL-R8-BEBOP-A" if source == "ROUND_8_A_REUSED" else None,
                "semantic_runtime_sha256": manifest["semantic_runtime_sha256"],
                "schedule_sha256": manifest["schedule_sha256"],
                "deck_sha256": {
                    deck: next(row["sha256"] for row in deck_rows if row["deck_key"] == deck)
                    for deck in pair
                },
                "orientation_counts": dict(
                    Counter(game["schedule"]["orientation"] for game in cell)
                ),
                "game_count": 100,
                "cell_sha256": run.digest(cell),
            }
        )
    assert len(provenance) == 45
    assert Counter(row["source"] for row in provenance) == {
        "BASELINE_004_REUSED": 36,
        "ROUND_8_A_REUSED": 9,
    }
    baseline_rows = metrics.matchup_rows(control["games"])
    combined_rows = metrics.matchup_rows(games)
    baseline_summary = run.r1.aggregate(control["games"], run.r1.DECKS)
    combined_summary = run.r1.aggregate(games, run.r1.DECKS)
    baseline_global = metrics.summary_metrics(baseline_summary, baseline_rows, control["games"])
    combined_global = metrics.summary_metrics(combined_summary, combined_rows, games)
    baseline_decks = metrics.per_deck(baseline_summary, baseline_rows)
    combined_decks = metrics.per_deck(combined_summary, combined_rows)
    deltas = {
        key: round(combined_global[key] - baseline_global[key], 6)
        for key in baseline_global
        if isinstance(baseline_global[key], (int, float))
    }
    evidence = {
        "schema": "objective-balance-lab-combined-environment-v1",
        "environment_id": ENVIRONMENT,
        "state": "EXPERIMENTAL_COMBINED_ENVIRONMENT",
        "parent_environment": "OBL-BASELINE-004",
        "candidate_experiment": "OBL-R8-BEBOP-A",
        "manifest_path": MANIFEST.relative_to(ROOT).as_posix(),
        "manifest_sha256": sha(MANIFEST),
        "semantic_runtime_sha256": manifest["semantic_runtime_sha256"],
        "schedule_sha256": manifest["schedule_sha256"],
        "source_artifact_sha256": manifest["source_artifact_sha256"],
        "accepted_isolated_record": manifest["accepted_isolated_record"],
        "logical_matchups": 45,
        "logical_games": 4500,
        "reused_games": 4500,
        "newly_executed_games": 0,
        "provenance_counts": dict(Counter(row["source"] for row in provenance)),
        "provenance": provenance,
        "baseline_global_metrics": baseline_global,
        "combined_global_metrics": combined_global,
        "global_delta": deltas,
        "baseline_deck_summary": baseline_summary,
        "combined_deck_summary": combined_summary,
        "baseline_per_deck": baseline_decks,
        "combined_per_deck": combined_decks,
        "baseline_matchups": baseline_rows,
        "combined_matchups": combined_rows,
        "ending_turn_distribution": {
            "baseline": isolated.distribution(control["games"]),
            "combined": isolated.distribution(games),
        },
        "paired_bebop_rocksteady_changes": isolated.paired(
            [game for game in control["games"] if "bebop_rocksteady" in game["seats"]],
            candidate["games"],
        ),
        "combined_games": games,
        "runtime_errors": 0,
        "promotion_authorized": False,
        "handoff": "RETURN_TO_DESIGN_STUDIO_HQ_FOR_PROMOTION_DECISION",
    }
    run.save(EVIDENCE, evidence)
    lines = [
        "# Combined 007: Frozen R8-A in Baseline 004",
        "",
        "Experimental Combined Environment validation. No promotion or baseline change is made here.",
        "",
        f"- Candidate: `OBL-R8-BEBOP-A`, SHA-256 `{authority['candidate_sha256']}`.",
        f"- Semantic runtime: `{manifest['semantic_runtime_sha256']}`.",
        f"- Sources: refreshed Baseline 004 `{sha(run.RESULT)}` and accepted R8-A `{sha(run.CANDIDATE_RESULT)}`.",
        f"- Accepted isolated record: [PR #275]({ACCEPTED_PR}), merged as `{ACCEPTED_MERGE}`.",
        "- Exact schedule: 45 matchups × 100 games, 50 starts per side; 36 unchanged control cells and nine frozen R8-A cells.",
        "- Logical games: **4,500**; source games reused: **4,500**; new executions: **0**; runtime errors: **0**.",
        "- Source deterministic checks: 900/900 R8-A replays and six control cell replay samples matched in isolated evidence.",
        "",
        "## Global distribution",
        "",
        "| Metric | Runtime-compatible Baseline 004 | Combined 007 | Delta |",
        "|---|---:|---:|---:|",
    ]
    labels = {
        "mean_matchup_balance_error": "Mean matchup balance error",
        "median_matchup_deviation": "Median matchup deviation",
        "over_60_40": ">60/40 cells",
        "over_70_30": ">70/30 cells",
        "aggregate_win_rate_spread": "Deck WR spread",
        "aggregate_win_rate_stddev": "Deck WR standard deviation",
        "mean_first_player_result_rate": "Mean first-player result rate",
        "mean_ending_turn": "Mean ending turn",
        "median_ending_turn": "Median ending turn",
    }
    for key, label in labels.items():
        lines.append(
            f"| {label} | {baseline_global[key]} | {combined_global[key]} | {deltas[key]:+g} |"
        )
    old_cells = {tuple(row["decks"]): row for row in baseline_rows}
    new_cells = {tuple(row["decks"]): row for row in combined_rows}
    lines += [
        "",
        "## R8-A diagnostics and polarization sentinels",
        "",
        "The B&R result rate is shown in each cell. Both lists contain 20 basic lands (10 Forest and 10 Swamp). Illegitimate Business is a Land, so the exact frozen swap reduces total lands from 24 to 22; these are outcomes for the whole substitution.",
        "",
        "| Opponent | Role | Baseline B&R WR | Combined B&R WR | Delta |",
        "|---|---|---:|---:|---:|",
    ]
    diagnostic_order = (
        ("raphael", "primary"),
        ("shredder", "primary"),
        ("splinter", "primary"),
        ("casey_jones", "primary"),
        ("donatello", "sentinel"),
        ("leonardo", "sentinel"),
        ("krang", "sentinel"),
        ("april_oneil", "sentinel"),
    )
    for opponent, role in diagnostic_order:
        pair = tuple(sorted(("bebop_rocksteady", opponent)))
        old = old_cells[pair]["win_rates"]["bebop_rocksteady"]
        new = new_cells[pair]["win_rates"]["bebop_rocksteady"]
        lines.append(
            f"| {run.r1.DISPLAY[opponent]} | {role} | {old:.0%} | {new:.0%} | {new - old:+.0%} |"
        )
    lines += [
        "",
        "All four primary cells improve, although B&R remains below 30% in each. Krang, Donatello, and April finish at 54%, 54%, and 55% for B&R, respectively; none crosses 60/40 in the candidate's favor. Krang's 27-point swing is the largest sentinel movement and remains a design review point.",
        "",
        "The aggregate standings table below shows the effect on Raphael, Shredder, Splinter, and Casey across all nine opponents. Only their B&R cell changes in this composed environment.",
    ]
    lines += [
        "",
        "## Ten deck summaries",
        "",
        "| Deck | Baseline WR | Combined WR | Delta | Baseline balance error | Combined balance error |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for deck in run.r1.DECKS:
        old, new = baseline_decks[deck], combined_decks[deck]
        lines.append(
            f"| {run.r1.DISPLAY[deck]} | {old['win_rate']:.2%} | {new['win_rate']:.2%} | {new['win_rate'] - old['win_rate']:+.2%} | {old['mean_matchup_balance_error']:.2%} | {new['mean_matchup_balance_error']:.2%} |"
        )
    old_rows = old_cells
    lines += [
        "",
        "## All 45 matchup cells",
        "",
        "The first listed deck's result rate is shown; the other deck has the complementary rate. Full game records and both rates are in the machine evidence.",
        "",
        "| Matchup | Baseline | Combined | Delta | Source |",
        "|---|---:|---:|---:|---|",
    ]
    for row in combined_rows:
        pair = tuple(row["decks"])
        deck = pair[0]
        old = old_rows[pair]["win_rates"][deck]
        new = row["win_rates"][deck]
        source = "R8-A" if "bebop_rocksteady" in pair else "Baseline 004"
        lines.append(
            f"| {run.r1.DISPLAY[pair[0]]} vs {run.r1.DISPLAY[pair[1]]} | {old:.0%} | {new:.0%} | {new - old:+.0%} | {source} |"
        )
    lines += [
        "",
        "## Handoff",
        "",
        "This is a measured experimental environment. 🧪 Design Studio/HQ makes the promotion decision; Cardcade has not promoted the candidate or changed Baseline 004.",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    return evidence


def main() -> int:
    result = build()
    print(
        json.dumps(
            {
                "environment_id": ENVIRONMENT,
                "logical_games": result["logical_games"],
                "provenance_counts": result["provenance_counts"],
                "global_delta": result["global_delta"],
                "bebop_rocksteady_win_rate": result["combined_deck_summary"]["bebop_rocksteady"][
                    "win_rate"
                ],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
