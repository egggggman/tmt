"""Authenticate reusable Combined 004 cells and run only three novel pairings."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
sys.path.insert(0, str(ROOT / "tools"))

import run_objective_balance_lab_round1 as r1  # noqa: E402
import run_objective_balance_lab_round5 as r5  # noqa: E402
from objective_balance_lab_semantic_identity import (  # noqa: E402
    assert_pre_chrome_evidence_runtime,
    identity,
)
from validate_objective_balance_lab_round5_results import validate as validate_r5  # noqa: E402

EXPECTED_MAIN = "0a09e2a17e14826d6a0dd37902b9b2ba4be9d495"
RUNTIME = "78bcce5b5f635f11c67247df91f90fef2bf0dbf948973c5c1ac38419f28b0e25"
SELECTION = {
    "shredder": "OBL-R5-SHREDDER-B",
    "april_oneil": "OBL-R5-APRIL_ONEIL-A",
    "krang": "OBL-R5-KRANG-B",
}
NOVEL_PAIRS = {
    ("shredder", "april_oneil"),
    ("shredder", "krang"),
    ("april_oneil", "krang"),
}
BASELINE_PATH = OBL / "baselines/OBL_BASELINE_002_MANIFEST.json"
BASELINE_EVIDENCE = OBL / "COMBINED_003_RUNTIME_COMPATIBLE_EVIDENCE.json"
ROUND5_PATH = OBL / "ROUND_5_EVIDENCE.json"
NEW_CHECKPOINT = OBL / "COMBINED_004_NEW_PAIRS.checkpoint.json"
NEW_PAIRS = OBL / "COMBINED_004_NEW_PAIRS.json"


def fingerprint(games: list[dict]) -> str:
    canonical = json.dumps(games, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def pair_key(pair: list[str] | tuple[str, str]) -> tuple[str, str]:
    return tuple(sorted(pair))


def grouped(games: list[dict]) -> dict[tuple[str, str], list[dict]]:
    cells: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for game in games:
        cells[pair_key(game["schedule"]["pair"])].append(game)
    return dict(cells)


def schedules_by_pair(schedule: list[dict]) -> dict[tuple[str, str], list[dict]]:
    rows: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for item in schedule:
        rows[pair_key(item["pair"])].append(item)
    return dict(rows)


def verify_cell(games: list[dict], expected: list[dict], label: str) -> str:
    assert len(games) == len(expected) == 100, label
    actual_schedule = {r5.digest(game["schedule"]): game["schedule"] for game in games}
    expected_schedule = {r5.digest(row): row for row in expected}
    assert len(actual_schedule) == len(expected_schedule) == 100, label
    assert actual_schedule == expected_schedule, label
    assert all(game["seats"] == game["schedule"]["decks"] for game in games), label
    assert Counter(game["schedule"]["orientation"] for game in games) == {
        "canonical": 50,
        "reversed": 50,
    }, label
    assert all(game["runtime_fingerprint"] and not game["runtime_error"] for game in games), label
    return fingerprint(games)


def _head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def verify_deck_bytes(relative: str, recorded_sha: str) -> dict[str, str]:
    """Retain the historical raw-checkout SHA and canonical Git-byte identity."""
    local = (ROOT / relative).read_bytes()
    committed = subprocess.check_output(["git", "show", f"HEAD:{relative}"], cwd=ROOT)
    local_sha = hashlib.sha256(local).hexdigest()
    committed_sha = hashlib.sha256(committed).hexdigest()
    canonical = committed.replace(b"\r\n", b"\n")
    checkout_crlf_sha = hashlib.sha256(canonical.replace(b"\n", b"\r\n")).hexdigest()
    assert recorded_sha in {local_sha, committed_sha, checkout_crlf_sha}, relative
    assert local.replace(b"\r\n", b"\n") == canonical, relative
    return {
        "recorded_sha256": recorded_sha,
        "worktree_sha256": local_sha,
        "git_sha256": committed_sha,
    }


def preflight() -> tuple[dict, dict, dict, dict, dict, dict, list[dict]]:
    assert not subprocess.run(
        ["git", "merge-base", "--is-ancestor", EXPECTED_MAIN, _head()],
        cwd=ROOT,
        check=False,
    ).returncode, "unexpected simulation-source lineage"
    validate_r5(replay=False)
    baseline_manifest = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    baseline = json.loads(BASELINE_EVIDENCE.read_text(encoding="utf-8"))
    round5 = json.loads(ROUND5_PATH.read_text(encoding="utf-8"))
    plan = json.loads(r5.PLAN.read_text(encoding="utf-8"))
    schedule = r1.schedule()
    schedule_hash = r5.digest(schedule)
    assert_pre_chrome_evidence_runtime(RUNTIME)
    assert baseline_manifest["environment_id"] == "OBL-BASELINE-002"
    assert baseline["environment_id"] == "OBL-COMBINED-003"
    assert baseline["combined_global_metrics"] == baseline_manifest["environment_metrics"]
    assert round5["environment_id"] == "OBL-BASELINE-002"
    assert (
        baseline_manifest["semantic_runtime_sha256"]
        == baseline["semantic_runtime_sha256"]
        == round5["semantic_runtime_sha256"]
        == plan["semantic_runtime_sha256"]
        == RUNTIME
    )
    assert (
        baseline_manifest["schedule_identity"]
        == baseline["schedule_sha256"]
        == round5["schedule_sha256"]
        == plan["schedule_identity"]
        == schedule_hash
    )
    assert round5["parent_evidence_git_blob_sha256"] == r5.git_blob_sha(
        BASELINE_EVIDENCE.relative_to(ROOT).as_posix()
    )
    assert round5["parent_manifest_sha256"] == r5.git_blob_sha(
        BASELINE_PATH.relative_to(ROOT).as_posix()
    )
    assert len(schedule) == 4500 and round5["counts"]["completed_games"] == 4500
    assert round5["counts"]["runtime_errors"] == 0
    assert len(baseline["combined_games"]) == 4500 and baseline["runtime_errors"] == 0

    decks = {row["deck_key"]: row for row in baseline_manifest["decks"]}
    assert set(decks) == set(r1.DECKS)
    candidates = round5["candidate_manifests"]
    planned = {row["experiment_id"]: row for row in plan["candidates"]}
    paths = {deck: row["source_path"] for deck, row in decks.items()}
    selected_hashes = {deck: row["sha256"] for deck, row in decks.items()}
    cards = r1.catalog()
    for row in decks.values():
        verify_deck_bytes(row["source_path"], row["sha256"])
        assert sum(r1.validate_deck(ROOT / row["source_path"], cards)["cards"].values()) == 60
    for deck, experiment_id in SELECTION.items():
        assert experiment_id in planned and experiment_id in candidates
        candidate = candidates[experiment_id]
        assert candidate["deck_key"] == planned[experiment_id]["deck_key"] == deck
        assert candidate["candidate_sha256"] == planned[experiment_id]["candidate_sha256"]
        assert candidate["parent_sha256"] == decks[deck]["sha256"]
        assert candidate["parent_path"] == decks[deck]["source_path"]
        verify_deck_bytes(candidate["candidate_path"], candidate["candidate_sha256"])
        assert (
            sum(r1.validate_deck(ROOT / candidate["candidate_path"], cards)["cards"].values()) == 60
        )
        assert round5["reports"][experiment_id]["verdict"] == "ACCEPT_FOR_COMBINED_MATRIX"
        paths[deck] = candidate["candidate_path"]
        selected_hashes[deck] = candidate["candidate_sha256"]
    assert not subprocess.check_output(
        ["git", "diff", "--name-only", "HEAD", "--", *paths.values()], cwd=ROOT, text=True
    ).strip()

    source_schedule = schedules_by_pair(schedule)
    baseline_cells = grouped(baseline["combined_games"])
    round5_cells = {
        deck: grouped(round5["candidate_results"][experiment_id])
        for deck, experiment_id in SELECTION.items()
    }
    assert len(source_schedule) == len(baseline_cells) == 45
    assert all(len(cells) == 9 for cells in round5_cells.values())
    baseline_provenance = {pair_key(row["decks"]): row for row in baseline["provenance"]}
    assert len(baseline_provenance) == 45
    for pair in sorted(source_schedule):
        if not set(pair) & SELECTION.keys():
            games = baseline_cells[pair]
            source_fingerprint = verify_cell(games, source_schedule[pair], f"baseline:{pair}")
            assert baseline_provenance[pair]["fingerprint"] == source_fingerprint
            assert baseline_provenance[pair]["semantic_runtime_sha256"] == RUNTIME
            assert baseline_provenance[pair]["schedule_sha256"] == schedule_hash
            assert baseline_provenance[pair]["deck_hashes"] == {
                deck: selected_hashes[deck] for deck in pair
            }
        elif len(set(pair) & SELECTION.keys()) == 1:
            candidate_deck = next(deck for deck in pair if deck in SELECTION)
            verify_cell(
                round5_cells[candidate_deck][pair],
                source_schedule[pair],
                f"round5:{SELECTION[candidate_deck]}:{pair}",
            )
    return baseline_manifest, baseline, round5, decks, paths, selected_hashes, schedule


def expected_checkpoint(schedule_hash: str, selected_hashes: dict[str, str]) -> dict:
    return {
        "schema": "obl-combined-004-new-pairs-v1",
        "environment_id": "OBL-COMBINED-004",
        "source_repository_sha": EXPECTED_MAIN,
        "semantic_runtime_sha256": RUNTIME,
        "schedule_sha256": schedule_hash,
        "selected_deck_sha256": selected_hashes,
        "completed_pairs": {},
    }


def verify_checkpoint(checkpoint: dict, expected: dict, schedule: list[dict]) -> None:
    for key, value in expected.items():
        if key != "completed_pairs":
            assert checkpoint[key] == value, key
    schedules = schedules_by_pair(schedule)
    novel = {pair_key(pair) for pair in NOVEL_PAIRS}
    assert set(checkpoint["completed_pairs"]) <= {"|".join(pair) for pair in novel}
    for label, games in checkpoint["completed_pairs"].items():
        pair = tuple(label.split("|"))
        verify_cell(games, schedules[pair], label)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-new", action="store_true")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    _manifest, _baseline, _round5, _decks, paths, hashes, schedule = preflight()
    expected = expected_checkpoint(r5.digest(schedule), hashes)
    if not args.run_new:
        print(json.dumps({"status": "PREFLIGHT_PASS", "reused_cells": 42, "new_games": 300}))
        return 0
    assert identity()["aggregate_semantic_runtime_sha256"] == RUNTIME, (
        "Cannot execute historical Combined 004 cells under a changed semantic runtime"
    )
    checkpoint = (
        json.loads(NEW_CHECKPOINT.read_text(encoding="utf-8"))
        if NEW_CHECKPOINT.exists()
        else expected
    )
    verify_checkpoint(checkpoint, expected, schedule)
    schedules = schedules_by_pair(schedule)
    cards = r1.catalog()
    for pair in sorted(pair_key(pair) for pair in NOVEL_PAIRS):
        label = "|".join(pair)
        if label in checkpoint["completed_pairs"]:
            continue
        print(f"starting {label}: 100 frozen games", flush=True)
        games = r1.run_set(paths, schedules[pair], cards, args.workers)
        verify_cell(games, schedules[pair], label)
        checkpoint["completed_pairs"][label] = games
        r5.write_json_atomic(NEW_CHECKPOINT, checkpoint)
        print(json.dumps({"completed_pairs": len(checkpoint["completed_pairs"])}), flush=True)
    assert len(checkpoint["completed_pairs"]) == 3
    r5.write_json_atomic(NEW_PAIRS, checkpoint)
    print(json.dumps({"status": "COMPLETE", "new_games": 300, "runtime_errors": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
