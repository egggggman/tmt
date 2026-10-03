"""Validate Combined 005 as a zero-new-game, source-authenticated composition."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
sys.path.insert(0, str(ROOT / "tools"))

import build_combined003_runtime_compatible as b3  # noqa: E402
import build_combined_004_reports as b4  # noqa: E402
import build_combined_005_reports as builder  # noqa: E402
import run_combined_004 as c4  # noqa: E402
import run_objective_balance_lab_round1 as r1  # noqa: E402
import run_objective_balance_lab_round5 as r5  # noqa: E402


def validate() -> dict:
    manifest = json.loads(builder.MANIFEST.read_text(encoding="utf-8"))
    evidence = json.loads(builder.EVIDENCE.read_text(encoding="utf-8"))
    baseline_manifest = json.loads(c4.BASELINE_PATH.read_text(encoding="utf-8"))
    baseline = json.loads(c4.BASELINE_EVIDENCE.read_text(encoding="utf-8"))
    round5 = json.loads(c4.ROUND5_PATH.read_text(encoding="utf-8"))
    combined004 = json.loads((OBL / "COMBINED_004_EVIDENCE.json").read_text(encoding="utf-8"))
    schedule = r1.schedule()
    assert manifest["environment_id"] == evidence["environment_id"] == "OBL-COMBINED-005"
    assert manifest["state"] == evidence["state"] == "EXPERIMENTAL_COMBINED_ENVIRONMENT"
    assert manifest["parent_environment"] == evidence["parent_environment"] == "OBL-BASELINE-002"
    assert (
        manifest["source_repository_sha"]
        == evidence["source_repository_sha"]
        == builder.EXPECTED_MAIN
    )
    assert manifest["semantic_runtime_sha256"] == evidence["semantic_runtime_sha256"] == c4.RUNTIME
    assert manifest["schedule_sha256"] == evidence["schedule_sha256"] == r5.digest(schedule)
    assert evidence["manifest_path"] == builder.MANIFEST.relative_to(ROOT).as_posix()
    assert evidence["manifest_content_sha256"] == r5.digest(manifest)
    assert manifest["logical_matchups"] == evidence["logical_matchups"] == 45
    assert manifest["logical_games"] == evidence["logical_games"] == 4500
    assert manifest["reused_games"] == evidence["reused_games"] == 4500
    assert manifest["newly_executed_games"] == evidence["newly_executed_games"] == 0
    assert evidence["runtime_errors"] == 0
    assert evidence["provenance_counts"] == {
        "BASELINE_002_REUSED": 28,
        "ROUND_5_REUSED": 16,
        "COMBINED_004_REUSED": 1,
    }
    assert len(manifest["decks"]) == 10
    assert {row["deck_key"] for row in manifest["decks"]} == set(r1.DECKS)
    assert set(manifest["selected_experiments"]) == set(builder.SELECTION.values())
    parent_decks = {row["deck_key"]: row for row in baseline_manifest["decks"]}
    selected_hashes = {}
    for row in manifest["decks"]:
        deck = row["deck_key"]
        experiment_id = builder.SELECTION.get(deck)
        assert row["selection"] == (experiment_id or "OBL-BASELINE-002")
        assert row["parent_baseline_sha256"] == parent_decks[deck]["sha256"]
        if experiment_id:
            source = round5["candidate_manifests"][experiment_id]
            assert row["source_path"] == source["candidate_path"]
            assert row["sha256"] == source["candidate_sha256"]
            assert row["exact_diff"] == {
                "removals": source["removals"],
                "additions": source["additions"],
            }
            assert (
                combined004["candidate_decisions"][experiment_id]["promotion_eligibility"]
                == "PROMOTION_ELIGIBLE"
            )
        else:
            assert row["source_path"] == parent_decks[deck]["source_path"]
            assert row["sha256"] == parent_decks[deck]["sha256"]
            assert row["exact_diff"] == {"removals": {}, "additions": {}}
        byte_identity = c4.verify_deck_bytes(row["source_path"], row["sha256"])
        assert row["canonical_git_sha256"] == byte_identity["git_sha256"]
        selected_hashes[deck] = row["sha256"]

    expected_schedules = c4.schedules_by_pair(schedule)
    baseline_cells = c4.grouped(baseline["combined_games"])
    candidate_cells = {
        deck: c4.grouped(round5["candidate_results"][experiment_id])
        for deck, experiment_id in builder.SELECTION.items()
    }
    combined004_cells = c4.grouped(combined004["combined_games"])
    prior_provenance = {tuple(row["decks"]): row for row in combined004["provenance"]}
    composed_cells = c4.grouped(evidence["combined_games"])
    provenance = {tuple(row["decks"]): row for row in evidence["provenance"]}
    assert len(evidence["combined_games"]) == 4500
    assert len(expected_schedules) == len(provenance) == len(composed_cells) == 45
    assert set(expected_schedules) == set(provenance) == set(composed_cells)
    assert (
        Counter(row["provenance"] for row in provenance.values()) == evidence["provenance_counts"]
    )
    reused_fingerprints = 0
    for pair in sorted(expected_schedules):
        row = provenance[pair]
        candidate_decks = sorted(set(pair) & builder.SELECTION.keys())
        if not candidate_decks:
            source_type = "BASELINE_002_REUSED"
            source_id = None
            source = baseline_cells[pair]
        elif len(candidate_decks) == 1:
            source_type = "ROUND_5_REUSED"
            source_id = builder.SELECTION[candidate_decks[0]]
            source = candidate_cells[candidate_decks[0]][pair]
        else:
            assert pair == c4.pair_key(tuple(builder.SELECTION))
            source_type = "COMBINED_004_REUSED"
            source_id = None
            source = combined004_cells[pair]
            assert prior_provenance[pair]["provenance"] == "COMBINED_004_NEW_PAIRING"
            assert prior_provenance[pair]["matchup_fingerprint"] == c4.fingerprint(source)
        assert row["provenance"] == source_type
        assert row["source_experiment_id"] == source_id
        assert row["source_artifact"] == manifest["source_artifacts"][source_type]
        assert row["source_artifact_sha256"] == r5.git_blob_sha(row["source_artifact"])
        assert row["source_artifact_sha256"] == evidence["source_artifact_sha256"][source_type]
        assert row["semantic_runtime_sha256"] == c4.RUNTIME
        assert row["schedule_sha256"] == r5.digest(schedule)
        assert row["deck_sha256"] == {deck: selected_hashes[deck] for deck in pair}
        assert row["game_count"] == 100
        assert row["orientation_counts"] == {"canonical": 50, "reversed": 50}
        assert row["matchup_fingerprint"] == c4.verify_cell(
            source, expected_schedules[pair], str(pair)
        )
        assert composed_cells[pair] == source
        assert c4.fingerprint(composed_cells[pair]) == row["matchup_fingerprint"]
        reused_fingerprints += 1
    assert reused_fingerprints == 45
    assert all(not game["runtime_error"] for game in evidence["combined_games"])

    matchup_rows = b3.matchup_rows(evidence["combined_games"])
    assert evidence["matchups"] == matchup_rows
    summary = r1.aggregate(evidence["combined_games"], r1.DECKS)
    assert evidence["combined_005_deck_summary"] == summary
    assert evidence["combined_005_global_metrics"] == b3.summary_metrics(
        summary, matchup_rows, evidence["combined_games"]
    )
    assert evidence["baseline_global_metrics"] == baseline_manifest["environment_metrics"]
    assert evidence["combined_004_global_metrics"] == combined004["combined_global_metrics"]
    baseline_decks = b3.per_deck(
        baseline["combined_deck_summary"], b3.matchup_rows(baseline["combined_games"])
    )
    current_decks = b3.per_deck(summary, matchup_rows)
    for deck in r1.DECKS:
        row = evidence["per_deck_comparison"][deck]
        assert row["baseline"]["win_rate"] == baseline_decks[deck]["win_rate"]
        assert row["combined_005"]["win_rate"] == current_decks[deck]["win_rate"]
        assert (
            row["combined_005"]["mean_matchup_balance_error"]
            == current_decks[deck]["mean_matchup_balance_error"]
        )
        assert row["combined_005"]["over_60_40"] == current_decks[deck]["over_60_40"]
        assert row["combined_005"]["over_70_30"] == current_decks[deck]["over_70_30"]
        assert row["win_rate_delta_from_baseline"] == round(
            current_decks[deck]["win_rate"] - baseline_decks[deck]["win_rate"], 6
        )
    assert (
        sum(row["changed_source_cell"] for row in evidence["combined_004_to_005_matchup_changes"])
        == 9
    )
    assert all(
        row["changed_source_cell"] == ("krang" in row["decks"])
        for row in evidence["combined_004_to_005_matchup_changes"]
    )
    assert set(evidence["candidate_decisions"]) == set(builder.SELECTION.values())
    assert set(evidence["candidate_interactions"]) == set(builder.SELECTION)
    for deck, experiment_id in builder.SELECTION.items():
        interaction = evidence["candidate_interactions"][deck]
        decision = evidence["candidate_decisions"][experiment_id]
        assert interaction["experiment_id"] == experiment_id
        assert interaction["classification"] == b4._delta_class(
            interaction["isolated_wr_delta"], interaction["combined_005_wr_delta"]
        )
        assert decision["combined_verdict"] in {
            "COMBINED_VALIDATION_PASSED",
            "COMBINED_VALIDATION_MIXED",
            "COMBINED_VALIDATION_FAILED",
        }
        assert decision["promotion_eligibility"] in {
            "PROMOTION_ELIGIBLE",
            "NOT_PROMOTION_ELIGIBLE",
        }
        assert decision["rationale"]
    assert set(evidence["recommended_promotion_subset"]) <= {
        experiment_id
        for experiment_id, decision in evidence["candidate_decisions"].items()
        if decision["promotion_eligibility"] == "PROMOTION_ELIGIBLE"
    }
    assert evidence["environment_decision"] in {
        "COMBINED_ENVIRONMENT_IMPROVED",
        "COMBINED_ENVIRONMENT_MIXED",
        "COMBINED_ENVIRONMENT_REGRESSED",
        "COMBINED_ENVIRONMENT_INCONCLUSIVE",
    }
    assert evidence["promotion_rationale"]
    expected_manifest, expected_evidence = builder.build()
    assert manifest == expected_manifest
    assert evidence == expected_evidence
    for markdown in (builder.SELECTION_DOC, builder.RESULTS_DOC):
        content = markdown.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", content):
            if "://" not in target and not target.startswith("#"):
                assert (markdown.parent / target.split("#", 1)[0].strip("<>")).is_file(), target
    assert not subprocess.check_output(
        [
            "git",
            "status",
            "--porcelain",
            "--",
            "decks",
            "docs/objective-balance-lab/candidates",
            "docs/objective-balance-lab/baselines",
            "docs/objective-balance-lab/PROMOTION_HISTORY.md",
        ],
        cwd=ROOT,
        text=True,
    ).strip()
    return {
        "status": "PASS",
        "matchups": 45,
        "logical_games": 4500,
        "reused_games": 4500,
        "new_games": 0,
        "provenance_fingerprints": reused_fingerprints,
        "runtime_errors": 0,
    }


def main() -> int:
    print(json.dumps(validate(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
