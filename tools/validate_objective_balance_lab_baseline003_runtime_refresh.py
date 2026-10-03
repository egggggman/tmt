"""Fail-closed authentication of the new-runtime Baseline 003 control matrix."""

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

import build_baseline003_runtime_refresh_report as report  # noqa: E402
import build_combined003_runtime_compatible as metrics  # noqa: E402
import run_objective_balance_lab_baseline003_runtime_refresh as run  # noqa: E402
import run_objective_balance_lab_round1 as r1  # noqa: E402


def validate(*, replay: bool = True) -> dict:
    manifest, schedule, paths, runtime = run.preflight()
    checkpoint = json.loads(run.CHECKPOINT.read_text(encoding="utf-8"))
    run.verify_checkpoint(checkpoint, run.checkpoint_template(manifest, runtime), schedule)
    evidence = json.loads(report.EVIDENCE.read_text(encoding="utf-8"))
    old = json.loads(run.HISTORICAL.read_text(encoding="utf-8"))
    games = evidence["games"]
    assert len(games) == len(checkpoint["results"]) == len(schedule) == 4500
    assert games == checkpoint["results"]
    assert evidence["schema"] == "obl-baseline-003-runtime-refresh-v1"
    assert evidence["environment_id"] == "OBL-BASELINE-003"
    assert evidence["evidence_id"] == run.EVIDENCE_ID
    assert evidence["state"] == "BASELINE_EVIDENCE_REFRESH"
    assert evidence["repository_sha"] == run.BASE
    assert evidence["semantic_runtime_sha256"] == run.RUNTIME
    assert evidence["old_semantic_runtime_sha256"] == run.OLD_RUNTIME
    assert evidence["semantic_runtime_identity"] == runtime
    assert evidence["schedule_sha256"] == run.SCHEDULE_SHA
    assert evidence["baseline_manifest_sha256"] == run.file_sha(run.MANIFEST)
    assert evidence["historical_evidence_sha256"] == run.file_sha(run.HISTORICAL)
    assert evidence["deck_manifest"] == manifest["decks"]
    assert evidence["cell_fingerprints"] == checkpoint["cell_fingerprints"]
    assert evidence["logical_matchups"] == 45 and evidence["executed_games"] == 4500
    assert evidence["runtime_errors"] == 0
    assert evidence["orientation_counts"] == {"canonical": 2250, "reversed": 2250}
    assert all(row["runtime_error"] is None and row["runtime_fingerprint"] for row in games)
    cells = Counter(tuple(sorted(game["schedule"]["pair"])) for game in games)
    assert len(cells) == 45 and set(cells.values()) == {100}
    for pair in cells:
        orientations = Counter(
            game["schedule"]["orientation"]
            for game in games
            if tuple(sorted(game["schedule"]["pair"])) == pair
        )
        assert orientations == {"canonical": 50, "reversed": 50}, pair
    assert set(paths) == set(r1.DECKS)
    assert all("R6_B" not in path.upper() for path in paths.values())
    old_games = old["combined_games"]
    assert len(old_games) == 4500
    old_rows, new_rows = metrics.matchup_rows(old_games), metrics.matchup_rows(games)
    old_summary, new_summary = r1.aggregate(old_games, r1.DECKS), r1.aggregate(games, r1.DECKS)
    old_metrics = metrics.summary_metrics(old_summary, old_rows, old_games)
    new_metrics = metrics.summary_metrics(new_summary, new_rows, games)
    assert old_metrics == old["combined_005_global_metrics"]
    assert evidence["historical_global_metrics"] == old_metrics
    assert evidence["refreshed_global_metrics"] == new_metrics
    assert evidence["historical_deck_summary"] == metrics.per_deck(old_summary, old_rows)
    assert evidence["refreshed_deck_summary"] == metrics.per_deck(new_summary, new_rows)
    assert evidence["refreshed_aggregate_telemetry"] == new_summary
    assert evidence["matchups"] == new_rows
    comparisons = report.compare_cells(old_games, games)
    assert evidence["matchup_comparisons"] == comparisons
    changed = [row for row in comparisons if row["cell_result_changed"]]
    assert evidence["changed_matchup_cells"] == changed
    assert evidence["changed_cell_count"] == len(changed)
    assert evidence["unchanged_cell_count"] == 45 - len(changed)
    assert evidence["max_cell_win_rate_movement"] == max(
        abs(delta) for row in comparisons for delta in row["win_rate_delta"].values()
    )
    assert evidence["outcome_changed_games"] == sum(
        row["outcome_changed_games"] for row in comparisons
    )
    assert evidence["ending_turn_changed_games"] == sum(
        row["ending_turn_changed_games"] for row in comparisons
    )
    assert evidence["worst_matchup_changed"] == (
        old_metrics["worst_matchup"]["decks"] != new_metrics["worst_matchup"]["decks"]
    )
    assert evidence["global_delta"] == {
        key: round(new_metrics[key] - old_metrics[key], 6)
        for key in new_metrics
        if key != "worst_matchup"
    }
    assert evidence["krang_control"] == {
        **evidence["refreshed_deck_summary"]["krang"],
        **new_summary["krang"],
    }
    assert len(evidence["krang_control"]["matchup_win_rates"]) == 9
    assert len(evidence["replay_samples"]) == 6
    assert {tuple(row["decks"]) for row in evidence["replay_samples"]} == set(report.REPLAY_PAIRS)
    assert all(row["status"] == "REPLAY_MATCHED" for row in evidence["replay_samples"])
    if replay:
        assert report.replay_sample(games, paths, schedule) == evidence["replay_samples"]
    assert evidence["r6_b_control_status"] == "R6_B_CONTROL_READY"
    assert evidence["promotion_authorized"] is False
    registry = json.loads((OBL / "ENVIRONMENT_REGISTRY.json").read_text(encoding="utf-8"))
    assert registry["environment_id"] == "OBL-BASELINE-003"
    assert registry["status"] == "OFFICIAL_BASELINE"
    preserved = [
        "docs/objective-balance-lab/baselines/OBL_BASELINE_003_MANIFEST.json",
        "docs/objective-balance-lab/COMBINED_005_EVIDENCE.json",
        "docs/objective-balance-lab/COMBINED_005_RESULTS.md",
        "docs/objective-balance-lab/PROMOTION_HISTORY.md",
        *paths.values(),
    ]
    assert (
        subprocess.run(
            ["git", "diff", "--quiet", run.BASE, "--", *preserved], cwd=ROOT, check=False
        ).returncode
        == 0
    )
    return {
        "status": "PASS",
        "evidence_id": run.EVIDENCE_ID,
        "games": 4500,
        "matchups": 45,
        "runtime_errors": 0,
        "replay_samples": 6 if replay else "recorded-only",
        "control_status": evidence["r6_b_control_status"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-replay", action="store_true")
    args = parser.parse_args()
    print(json.dumps(validate(replay=not args.no_replay), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
