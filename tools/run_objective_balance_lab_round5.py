"""Run only the five approved Round 5 candidate slices against Baseline 002."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
PLAN = OBL / "ROUND_5_CANDIDATE_PLAN.json"
CHECKPOINT = OBL / "ROUND_5_CHECKPOINT.json"
OUTPUT = OBL / "ROUND_5_EVIDENCE.json"
sys.path.insert(0, str(ROOT / "tools"))

import run_objective_balance_lab_round1 as r1  # noqa: E402
from objective_balance_lab_semantic_identity import identity  # noqa: E402
from validate_objective_balance_lab_round5_design import validate as validate_design  # noqa: E402


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode("utf-8")).hexdigest()


def git_blob_sha(relative: str) -> str:
    content = subprocess.check_output(["git", "show", f"HEAD:{relative}"], cwd=ROOT)
    return hashlib.sha256(content).hexdigest()


def write_json_atomic(path: Path, payload: dict[str, object]) -> None:
    rendered = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="\n", dir=path.parent, delete=False
    ) as stream:
        temp_path = Path(stream.name)
        stream.write(rendered)
    os.replace(temp_path, path)


def preflight() -> tuple[dict, dict, list[dict], dict[str, str]]:
    validate_design(allow_results=OUTPUT.exists())
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    baseline = json.loads((ROOT / plan["parent_manifest"]).read_text(encoding="utf-8"))
    evidence_path = ROOT / plan["reference_evidence"]
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    schedule = r1.schedule()
    assert len(schedule) == 4500
    assert digest(schedule) == plan["schedule_identity"] == baseline["schedule_identity"]
    assert (
        evidence["semantic_runtime_sha256"]
        == baseline["semantic_runtime_sha256"]
        == plan["semantic_runtime_sha256"]
        == identity()["aggregate_semantic_runtime_sha256"]
    )
    assert evidence["environment_id"] == "OBL-COMBINED-003"
    assert evidence["newly_executed_games"] == 0
    assert len(evidence["combined_games"]) == len(schedule)
    banked = {digest(game["schedule"]): game for game in evidence["combined_games"]}
    assert len(banked) == 4500
    for row in schedule:
        game = banked[digest(row)]
        assert game["schedule"] == row
        assert game["seats"] == row["decks"]
        assert not game.get("runtime_error")
    assert not evidence["runtime_errors"]
    paths = {row["deck_key"]: row["source_path"] for row in baseline["decks"]}
    assert len(paths) == 10
    for candidate in plan["candidates"]:
        assert git_blob_sha(candidate["candidate_path"]) == candidate["candidate_sha256"]
    return plan, baseline, schedule, paths


def expected_payload(plan: dict, baseline: dict, schedule: list[dict]) -> dict:
    return {
        "schema": "objective-balance-lab-round5-results-v1",
        "environment_id": "OBL-BASELINE-002",
        "repository_sha": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "semantic_runtime_sha256": plan["semantic_runtime_sha256"],
        "snapshot_path": plan["card_snapshot"],
        "snapshot_sha256": git_blob_sha(plan["card_snapshot"]),
        "schedule_sha256": digest(schedule),
        "schedule_games": len(schedule),
        "parent_manifest_path": plan["parent_manifest"],
        "parent_manifest_sha256": git_blob_sha(plan["parent_manifest"]),
        "parent_evidence_path": plan["reference_evidence"],
        "parent_evidence_git_blob_sha256": git_blob_sha(plan["reference_evidence"]),
        "parent_evidence_recorded_sha256": baseline["source_combined_evidence"]["sha256"],
        "design_plan_path": PLAN.relative_to(ROOT).as_posix(),
        "design_plan_sha256": git_blob_sha(PLAN.relative_to(ROOT).as_posix()),
        "candidate_manifests": {
            row["experiment_id"]: {
                key: row[key]
                for key in (
                    "experiment_id",
                    "deck_key",
                    "candidate_path",
                    "candidate_sha256",
                    "parent_path",
                    "parent_sha256",
                    "removals",
                    "additions",
                    "hypothesis",
                    "semantic_support",
                )
            }
            for row in plan["candidates"]
        },
        "candidate_results": {},
        "counts": {
            "expected_candidates": 5,
            "expected_games": 4500,
            "completed_candidates": 0,
            "completed_games": 0,
            "runtime_errors": 0,
        },
    }


def verify_completed(payload: dict, schedule: list[dict]) -> None:
    expected = {digest(row): row for row in schedule}
    assert len(expected) == 4500
    for experiment_id, games in payload["candidate_results"].items():
        manifest = payload["candidate_manifests"][experiment_id]
        deck = manifest["deck_key"]
        selected = {key: value for key, value in expected.items() if deck in value["pair"]}
        assert len(games) == len(selected) == 900
        assert len({digest(game["schedule"]) for game in games}) == 900
        assert {digest(game["schedule"]) for game in games} == set(selected)
        assert all(game["seats"] == game["schedule"]["decks"] for game in games)
        assert all(game["runtime_fingerprint"] and not game["runtime_error"] for game in games)
        for opponent in r1.DECKS:
            if opponent == deck:
                continue
            subset = [game for game in games if opponent in game["seats"]]
            assert len(subset) == 100
            assert sum(game["schedule"]["orientation"] == "canonical" for game in subset) == 50
            assert sum(game["schedule"]["orientation"] == "reversed" for game in subset) == 50
    assert payload["counts"]["completed_candidates"] == len(payload["candidate_results"])
    assert payload["counts"]["completed_games"] == sum(
        len(games) for games in payload["candidate_results"].values()
    )
    assert payload["counts"]["runtime_errors"] == 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true", help="execute the approved candidate slices")
    parser.add_argument("--workers", type=int, default=10)
    args = parser.parse_args()
    plan, baseline, schedule, paths = preflight()
    expected = expected_payload(plan, baseline, schedule)
    if not args.run:
        print(json.dumps({"status": "PREFLIGHT_PASS", "candidate_games": 4500}))
        return 0
    if OUTPUT.exists():
        completed = json.loads(OUTPUT.read_text(encoding="utf-8"))
        assert len(completed["candidate_results"]) == 5
        verify_completed(completed, schedule)
        print(json.dumps({"status": "COMPLETE_REUSED", **completed["counts"]}))
        return 0
    payload = (
        json.loads(CHECKPOINT.read_text(encoding="utf-8")) if CHECKPOINT.exists() else expected
    )
    for key in expected:
        if key not in {"candidate_results", "counts"}:
            assert payload[key] == expected[key], key
    verify_completed(payload, schedule)
    cards = r1.catalog()
    for candidate in plan["candidates"]:
        experiment_id = candidate["experiment_id"]
        if experiment_id in payload["candidate_results"]:
            continue
        deck = candidate["deck_key"]
        games = [row for row in schedule if deck in row["pair"]]
        assert len(games) == 900
        candidate_paths = dict(paths)
        candidate_paths[deck] = candidate["candidate_path"]
        print(f"starting {experiment_id}: 900 frozen games", flush=True)
        results = r1.run_set(candidate_paths, games, cards, args.workers)
        assert len(results) == 900
        payload["candidate_results"][experiment_id] = results
        payload["counts"]["completed_candidates"] += 1
        payload["counts"]["completed_games"] += len(results)
        payload["counts"]["runtime_errors"] += sum(
            bool(game.get("runtime_error")) for game in results
        )
        verify_completed(payload, schedule)
        write_json_atomic(CHECKPOINT, payload)
        print(json.dumps(payload["counts"]), flush=True)
    assert payload["counts"]["completed_games"] == 4500
    write_json_atomic(OUTPUT, payload)
    print(json.dumps({"status": "COMPLETE", **payload["counts"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
