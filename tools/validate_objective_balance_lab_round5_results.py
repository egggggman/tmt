"""Validate Round 5 results, preserved candidates, and deterministic replay."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
sys.path.insert(0, str(ROOT / "tools"))

import build_objective_balance_lab_round5_results as builder  # noqa: E402
import run_objective_balance_lab_round1 as r1  # noqa: E402
import run_objective_balance_lab_round5 as r5  # noqa: E402


def validate(*, replay: bool = True) -> dict[str, object]:
    plan, baseline, schedule, parent_paths = r5.preflight()
    evidence = json.loads(r5.OUTPUT.read_text(encoding="utf-8"))
    checkpoint = json.loads(r5.CHECKPOINT.read_text(encoding="utf-8"))
    assert evidence["schema"] == checkpoint["schema"] == "objective-balance-lab-round5-results-v1"
    assert evidence["environment_id"] == checkpoint["environment_id"] == "OBL-BASELINE-002"
    assert evidence["semantic_runtime_sha256"] == baseline["semantic_runtime_sha256"]
    assert evidence["schedule_sha256"] == plan["schedule_identity"]
    assert evidence["candidate_manifests"] == checkpoint["candidate_manifests"]
    assert evidence["candidate_results"] == checkpoint["candidate_results"]
    assert (
        evidence["counts"]
        == checkpoint["counts"]
        == {
            "expected_candidates": 5,
            "expected_games": 4500,
            "completed_candidates": 5,
            "completed_games": 4500,
            "runtime_errors": 0,
        }
    )
    assert set(evidence["candidate_results"]) == {
        row["experiment_id"] for row in plan["candidates"]
    }
    r5.verify_completed(evidence, schedule)
    assert evidence["parent_manifest_sha256"] == r5.git_blob_sha(plan["parent_manifest"])
    assert evidence["parent_evidence_git_blob_sha256"] == r5.git_blob_sha(
        plan["reference_evidence"]
    )
    assert evidence["design_plan_sha256"] == r5.git_blob_sha(r5.PLAN.relative_to(ROOT).as_posix())
    assert evidence["snapshot_sha256"] == r5.git_blob_sha(plan["card_snapshot"])
    assert evidence["baseline_global_metrics"] == baseline["environment_metrics"]
    assert evidence["metric_audit_path"] == plan["metric_audit"]
    assert evidence["metric_audit_git_blob_sha256"] == r5.git_blob_sha(plan["metric_audit"])
    assert evidence["experiment_aliases"] == {"OBL-R5-APRIL-A": "OBL-R5-APRIL_ONEIL-A"}

    _, recomputed = builder.build()
    assert evidence["reports"].keys() == recomputed.keys()
    allowed_hypotheses = {
        "SUPPORTED",
        "PARTIALLY_SUPPORTED",
        "FALSIFIED",
        "SEMANTICALLY_UNRESOLVED",
    }
    allowed_verdicts = {
        "ACCEPT_FOR_COMBINED_MATRIX",
        "PROMISING_NEEDS_VARIANT",
        "REJECT_BALANCE_REGRESSION",
        "REJECT_IDENTITY_REGRESSION",
        "REJECT_SEMANTIC_CONFIDENCE",
        "INCONCLUSIVE",
    }
    for experiment_id, expected in recomputed.items():
        observed = evidence["reports"][experiment_id]
        assert all(observed[key] == value for key, value in expected.items()), experiment_id
        assert observed["hypothesis_result"] in allowed_hypotheses
        assert observed["verdict"] in allowed_verdicts
        assert observed["identity_classification"] in {
            "IDENTITY_STRENGTHENED",
            "IDENTITY_PRESERVED",
            "IDENTITY_DILUTED",
        }
        assert observed["rationale"]

    pool = evidence["provisional_combined_004_pool"]
    assert set(pool) <= {"shredder", "april_oneil", "krang"}
    assert all(
        evidence["candidate_manifests"][experiment_id]["deck_key"] == deck
        and evidence["reports"][experiment_id]["verdict"]
        in {"ACCEPT_FOR_COMBINED_MATRIX", "PROMISING_NEEDS_VARIANT"}
        for deck, experiment_id in pool.items()
    )

    ledger = json.loads((OBL / "EXPERIMENT_LEDGER.json").read_text(encoding="utf-8"))
    ids = [row["experiment_id"] for row in ledger["experiments"]]
    assert len(ids) == len(set(ids))
    for planned in plan["candidates"]:
        experiment_id = planned["experiment_id"]
        record = next(row for row in ledger["experiments"] if row["experiment_id"] == experiment_id)
        assert record["candidate"]["sha256"] == planned["candidate_sha256"]
        assert record["parent"]["sha256"] == planned["parent_sha256"]
        assert record["parent"]["environment_id"] == "OBL-BASELINE-002"
        assert record["schedule_identity"] == plan["schedule_identity"]
        assert record["verdict"] == evidence["reports"][experiment_id]["verdict"]
        assert record["promotion_status"] == "EXPERIMENTAL"
        assert record["source_evidence"] == r5.OUTPUT.relative_to(ROOT).as_posix()
    role = json.loads((OBL / "CARD_ROLE_EVIDENCE.json").read_text(encoding="utf-8"))
    for planned in plan["candidates"]:
        experiment_id = planned["experiment_id"]
        rows = [row for row in role["records"] if row.get("experiment_id") == experiment_id]
        assert len(rows) == len(planned["removals"]) + len(planned["additions"])
        assert {row["card"] for row in rows} == set(planned["removals"]) | set(planned["additions"])
        assert all(row["causality_note"] for row in rows)
    assert "ROUND_5_EVIDENCE.json" in (OBL / "EXPERIMENT_LEDGER.md").read_text(encoding="utf-8")
    report_text = (OBL / "ROUND_5_RESULTS.md").read_text(encoding="utf-8")
    assert all(experiment_id in report_text for experiment_id in recomputed)
    for markdown in (OBL / "ROUND_5_RESULTS.md", OBL / "EXPERIMENT_LEDGER.md"):
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", markdown.read_text(encoding="utf-8")):
            if "://" not in target and not target.startswith("#"):
                assert (markdown.parent / target.split("#", 1)[0].strip("<>")).is_file(), (
                    markdown,
                    target,
                )

    protected = [row["source_path"] for row in baseline["decks"]]
    protected.extend(row["candidate_path"] for row in plan["candidates"])
    protected.extend(
        [
            "docs/objective-balance-lab/ROUND_5_DIAGNOSTIC.md",
            "docs/objective-balance-lab/ROUND_5_CANDIDATE_PLAN.md",
            "docs/objective-balance-lab/ROUND_5_CANDIDATE_PLAN.json",
            "docs/objective-balance-lab/PROMOTION_HISTORY.md",
        ]
    )
    assert not subprocess.check_output(
        ["git", "diff", "--name-only", "HEAD", "--", *protected], cwd=ROOT, text=True
    ).strip()

    replayed = 0
    if replay:
        r1._init_worker(r1.catalog())
        for planned in plan["candidates"]:
            experiment_id = planned["experiment_id"]
            deck = planned["deck_key"]
            rows = evidence["candidate_results"][experiment_id]
            paths = dict(parent_paths)
            paths[deck] = planned["candidate_path"]
            for orientation in ("canonical", "reversed"):
                index, original = next(
                    (index, row)
                    for index, row in enumerate(rows, 1)
                    if row["schedule"]["orientation"] == orientation
                )
                result = r1._run_one((index, paths, original["schedule"]))
                assert result["runtime_error"] is None
                assert result["runtime_fingerprint"] == original["runtime_fingerprint"]
                replayed += 1
    return {
        "status": "PASS",
        "candidates": 5,
        "games": 4500,
        "runtime_errors": 0,
        "replayed_fingerprints": replayed,
    }


def main() -> int:
    print(json.dumps(validate(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
