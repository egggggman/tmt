"""Fail-closed provenance, metric, governance, and replay checks for Combined 004."""

from __future__ import annotations

import hashlib
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
import build_combined_004_reports as builder  # noqa: E402
import run_combined_004 as c4  # noqa: E402
import run_objective_balance_lab_round1 as r1  # noqa: E402
import run_objective_balance_lab_round5 as r5  # noqa: E402


def _artifact_sha(relative: str) -> str:
    path = ROOT / relative
    if path == c4.NEW_PAIRS:
        return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    return r5.git_blob_sha(relative)


def validate(*, replay: bool = True) -> dict:
    baseline_manifest, baseline, round5, parent_decks, paths, hashes, schedule = c4.preflight()
    manifest = json.loads(builder.MANIFEST.read_text(encoding="utf-8"))
    evidence = json.loads(builder.EVIDENCE.read_text(encoding="utf-8"))
    new_pairs = json.loads(c4.NEW_PAIRS.read_text(encoding="utf-8"))
    checkpoint = json.loads(c4.NEW_CHECKPOINT.read_text(encoding="utf-8"))
    assert new_pairs == checkpoint
    c4.verify_checkpoint(new_pairs, c4.expected_checkpoint(r5.digest(schedule), hashes), schedule)
    assert len(new_pairs["completed_pairs"]) == 3
    assert manifest["environment_id"] == evidence["environment_id"] == "OBL-COMBINED-004"
    assert manifest["state"] == evidence["state"] == "EXPERIMENTAL_COMBINED_ENVIRONMENT"
    assert manifest["parent_environment"] == evidence["parent_environment"] == "OBL-BASELINE-002"
    assert (
        manifest["source_repository_sha"] == evidence["source_repository_sha"] == c4.EXPECTED_MAIN
    )
    assert manifest["semantic_runtime_sha256"] == evidence["semantic_runtime_sha256"] == c4.RUNTIME
    assert manifest["schedule_sha256"] == evidence["schedule_sha256"] == r5.digest(schedule)
    assert evidence["manifest_content_sha256"] == r5.digest(manifest)
    assert evidence["manifest_path"] == builder.MANIFEST.relative_to(ROOT).as_posix()
    assert manifest["logical_matchups"] == evidence["logical_matchups"] == 45
    assert manifest["logical_games"] == evidence["logical_games"] == 4500
    assert manifest["reused_games"] == evidence["reused_games"] == 4200
    assert manifest["newly_executed_games"] == evidence["newly_executed_games"] == 300
    assert evidence["runtime_errors"] == 0
    assert evidence["provenance_counts"] == {
        "BASELINE_002_REUSED": 21,
        "ROUND_5_REUSED": 21,
        "COMBINED_004_NEW_PAIRING": 3,
    }
    assert len(manifest["decks"]) == 10
    assert {row["deck_key"] for row in manifest["decks"]} == set(r1.DECKS)
    assert set(manifest["selected_experiments"]) == set(c4.SELECTION.values())
    assert len(manifest["selected_experiments"]) == 3
    for row in manifest["decks"]:
        deck = row["deck_key"]
        assert row["selection"] == c4.SELECTION.get(deck, "OBL-BASELINE-002")
        assert row["source_path"] == paths[deck]
        assert row["sha256"] == hashes[deck]
        assert row["parent_baseline_sha256"] == parent_decks[deck]["sha256"]
        byte_identity = c4.verify_deck_bytes(row["source_path"], row["sha256"])
        assert row["canonical_git_sha256"] == byte_identity["git_sha256"]
        if deck in c4.SELECTION:
            source = round5["candidate_manifests"][c4.SELECTION[deck]]
            assert row["exact_diff"] == {
                "removals": source["removals"],
                "additions": source["additions"],
            }
        else:
            assert row["exact_diff"] == {"removals": {}, "additions": {}}

    source_schedules = c4.schedules_by_pair(schedule)
    baseline_cells = c4.grouped(baseline["combined_games"])
    candidate_cells = {
        deck: c4.grouped(round5["candidate_results"][experiment_id])
        for deck, experiment_id in c4.SELECTION.items()
    }
    composed = c4.grouped(evidence["combined_games"])
    provenance = {tuple(row["decks"]): row for row in evidence["provenance"]}
    assert len(evidence["combined_games"]) == 4500
    assert len(composed) == len(provenance) == 45
    assert set(composed) == set(source_schedules) == set(provenance)
    assert (
        Counter(row["provenance"] for row in provenance.values()) == evidence["provenance_counts"]
    )
    for pair in sorted(source_schedules):
        row = provenance[pair]
        candidate_decks = sorted(set(pair) & c4.SELECTION.keys())
        if not candidate_decks:
            expected_label = "BASELINE_002_REUSED"
            source = baseline_cells[pair]
            source_id = None
        elif len(candidate_decks) == 1:
            expected_label = "ROUND_5_REUSED"
            source = candidate_cells[candidate_decks[0]][pair]
            source_id = c4.SELECTION[candidate_decks[0]]
        else:
            expected_label = "COMBINED_004_NEW_PAIRING"
            source = new_pairs["completed_pairs"]["|".join(pair)]
            source_id = None
        assert row["provenance"] == expected_label, pair
        assert row["source_experiment_id"] == source_id, pair
        assert row["semantic_runtime_sha256"] == c4.RUNTIME
        assert row["schedule_sha256"] == r5.digest(schedule)
        assert row["deck_sha256"] == {deck: hashes[deck] for deck in pair}
        assert row["game_count"] == 100
        assert row["orientation_counts"] == {"canonical": 50, "reversed": 50}
        assert row["source_artifact"] == manifest["source_artifacts"][expected_label]
        assert row["source_artifact_sha256"] == _artifact_sha(row["source_artifact"])
        assert row["source_artifact_sha256"] == evidence["source_artifact_sha256"][expected_label]
        assert (
            c4.verify_cell(source, source_schedules[pair], str(pair)) == row["matchup_fingerprint"]
        )
        assert composed[pair] == source, pair
        assert c4.fingerprint(composed[pair]) == row["matchup_fingerprint"]
    assert all(not game["runtime_error"] for game in evidence["combined_games"])
    assert evidence["baseline_global_metrics"] == baseline_manifest["environment_metrics"]
    rows = b3.matchup_rows(evidence["combined_games"])
    assert evidence["matchups"] == rows
    summary = r1.aggregate(evidence["combined_games"], r1.DECKS)
    assert evidence["combined_deck_summary"] == summary
    metrics = b3.summary_metrics(summary, rows, evidence["combined_games"])
    assert evidence["combined_global_metrics"] == metrics
    recomputed_decks = b3.per_deck(summary, rows)
    baseline_decks = b3.per_deck(
        baseline["combined_deck_summary"], b3.matchup_rows(baseline["combined_games"])
    )
    for deck in r1.DECKS:
        observed = evidence["per_deck_comparison"][deck]
        assert observed["baseline"]["win_rate"] == baseline_decks[deck]["win_rate"]
        assert observed["combined"]["win_rate"] == recomputed_decks[deck]["win_rate"]
        assert (
            observed["combined"]["mean_matchup_balance_error"]
            == recomputed_decks[deck]["mean_matchup_balance_error"]
        )
        assert observed["combined"]["over_60_40"] == recomputed_decks[deck]["over_60_40"]
        assert observed["combined"]["over_70_30"] == recomputed_decks[deck]["over_70_30"]
        assert observed["win_rate_delta"] == round(
            recomputed_decks[deck]["win_rate"] - baseline_decks[deck]["win_rate"], 6
        )
    assert evidence["global_balance_delta"] == round(
        metrics["mean_matchup_balance_error"]
        - evidence["baseline_global_metrics"]["mean_matchup_balance_error"],
        6,
    )
    assert evidence["environment_decision"] in {
        "COMBINED_ENVIRONMENT_IMPROVED",
        "COMBINED_ENVIRONMENT_MIXED",
        "COMBINED_ENVIRONMENT_REGRESSED",
        "COMBINED_ENVIRONMENT_INCONCLUSIVE",
    }
    assert set(evidence["candidate_decisions"]) == set(c4.SELECTION.values())
    assert set(evidence["isolated_to_combined"]) == set(c4.SELECTION)
    for deck, experiment_id in c4.SELECTION.items():
        decision = evidence["candidate_decisions"][experiment_id]
        assert decision["combined_verdict"] in {
            "COMBINED_VALIDATION_PASSED",
            "COMBINED_VALIDATION_MIXED",
            "COMBINED_VALIDATION_FAILED",
        }
        assert decision["promotion_eligibility"] in {
            "PROMOTION_ELIGIBLE",
            "NOT_PROMOTION_ELIGIBLE",
        }
        effect = evidence["isolated_to_combined"][deck]
        assert effect["experiment_id"] == experiment_id
        assert effect["classification"] == builder._delta_class(
            effect["isolated_wr_delta"], effect["combined_wr_delta"]
        )
    assert set(evidence["recommended_promotion_subset"]) <= {
        experiment_id
        for experiment_id, decision in evidence["candidate_decisions"].items()
        if decision["promotion_eligibility"] == "PROMOTION_ELIGIBLE"
    }
    assert evidence["subset_rationale"]
    assert set(evidence["novel_matchups"]) == set(new_pairs["completed_pairs"])
    for label, source in new_pairs["completed_pairs"].items():
        assert evidence["novel_matchups"][label] == builder._new_pair_summary(
            tuple(label.split("|")), source
        )
    expected_manifest, expected_evidence, _ = builder.build()
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

    replayed = 0
    if replay:
        r1._init_worker(r1.catalog())
        for source in new_pairs["completed_pairs"].values():
            for orientation in ("canonical", "reversed"):
                original = next(
                    game for game in source if game["schedule"]["orientation"] == orientation
                )
                result = r1._run_one((0, paths, original["schedule"]))
                assert result["runtime_error"] is None
                assert result["runtime_fingerprint"] == original["runtime_fingerprint"]
                replayed += 1
    return {
        "status": "PASS",
        "logical_matchups": 45,
        "logical_games": 4500,
        "reused_games": 4200,
        "new_games": 300,
        "runtime_errors": 0,
        "replayed_fingerprints": replayed,
    }


def main() -> int:
    print(json.dumps(validate(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
