"""Run the immutable Krang R6-B candidate against nine new-runtime controls."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
sys.path.insert(0, str(ROOT / "tools"))

import run_objective_balance_lab_baseline003_runtime_refresh as refresh  # noqa: E402
import run_objective_balance_lab_round1 as r1  # noqa: E402
import run_objective_balance_lab_round5 as r5  # noqa: E402
from objective_balance_lab_semantic_identity import identity  # noqa: E402
from validate_chrome_dome_r6b_readiness import validate as validate_chrome  # noqa: E402
from validate_objective_balance_lab_baseline003_runtime_refresh import (  # noqa: E402
    validate as validate_control,
)

BASE = "3438284afeb1db2e74dd137ca244ad52e015bbaf"
EXPERIMENT = "OBL-R6-KRANG-B"
CANDIDATE = "docs/objective-balance-lab/candidates/KRANG_OBL_R6_B.txt"
CANDIDATE_SHA = "5460b9d1288d193db3f8db7a78076dfeb38f734c79acdd1ddbe898da030b3bdf"
CANDIDATE_BLOB = "53af73af05c475832bd3e8a08c67264a0ff8fd44"
PARENT_SHA = "5a52bc59b5de1034721ba17d1c1d4f12c493ec70681c1a910c8230808e4e4f96"
CHECKPOINT = OBL / "ROUND_6_B_CHECKPOINT.json"
EVIDENCE = OBL / "ROUND_6_B_EVIDENCE.json"
RUNTIME = refresh.RUNTIME
SCHEDULE_SHA = refresh.SCHEDULE_SHA


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def preflight() -> tuple[dict, list[dict], dict[str, str], dict]:
    assert (
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", BASE, "HEAD"], cwd=ROOT, check=False
        ).returncode
        == 0
    )
    manifest, schedule, paths, _runtime = refresh.preflight()
    assert identity()["aggregate_semantic_runtime_sha256"] == RUNTIME
    assert validate_chrome()["status"] == "PASS"
    assert validate_control(replay=False)["control_status"] == "R6_B_CONTROL_READY"
    control = json.loads(
        refresh.OBL.joinpath("BASELINE_003_RUNTIME_REFRESH_EVIDENCE.json").read_text(
            encoding="utf-8"
        )
    )
    assert control["semantic_runtime_sha256"] == RUNTIME
    assert control["schedule_sha256"] == SCHEDULE_SHA
    assert control["deck_manifest"] == manifest["decks"]
    assert control["executed_games"] == 4500 and control["runtime_errors"] == 0
    assert len(control["games"]) == 4500
    committed = subprocess.check_output(["git", "show", f"HEAD:{CANDIDATE}"], cwd=ROOT)
    local = (ROOT / CANDIDATE).read_bytes()
    assert local.replace(b"\r\n", b"\n") == committed
    assert sha(committed) == CANDIDATE_SHA
    assert (
        subprocess.check_output(
            ["git", "rev-parse", f"HEAD:{CANDIDATE}"], cwd=ROOT, text=True
        ).strip()
        == CANDIDATE_BLOB
    )
    cards = r1.catalog()
    parent = r1.validate_deck(ROOT / paths["krang"], cards)
    candidate = r1.validate_deck(ROOT / CANDIDATE, cards)
    assert candidate["color_identity"] == "U"
    assert r1.diff(parent["cards"], candidate["cards"]) == {
        "Chrome Dome": {"parent": 0, "candidate": 1},
        "Negate": {"parent": 3, "candidate": 2},
    }
    assert (
        next(row["sha256"] for row in manifest["decks"] if row["deck_key"] == "krang") == PARENT_SHA
    )
    isolated = [row for row in schedule if "krang" in row["pair"]]
    assert len(isolated) == 900
    assert Counter(row["orientation"] for row in isolated) == {
        "canonical": 450,
        "reversed": 450,
    }
    return manifest, isolated, paths, control


def template(manifest: dict, isolated: list[dict]) -> dict:
    return {
        "schema": "obl-round-6-b-isolated-v1",
        "experiment_id": EXPERIMENT,
        "repository_sha": BASE,
        "candidate_path": CANDIDATE,
        "candidate_sha256": CANDIDATE_SHA,
        "candidate_git_blob_sha1": CANDIDATE_BLOB,
        "parent_environment": "OBL-BASELINE-003",
        "parent_deck_sha256": next(
            row["sha256"] for row in manifest["decks"] if row["deck_key"] == "krang"
        ),
        "parent_manifest_path": refresh.MANIFEST.relative_to(ROOT).as_posix(),
        "parent_manifest_sha256": refresh.file_sha(refresh.MANIFEST),
        "control_evidence_id": refresh.EVIDENCE_ID,
        "control_evidence_path": (OBL / "BASELINE_003_RUNTIME_REFRESH_EVIDENCE.json")
        .relative_to(ROOT)
        .as_posix(),
        "control_evidence_sha256": refresh.file_sha(
            OBL / "BASELINE_003_RUNTIME_REFRESH_EVIDENCE.json"
        ),
        "semantic_runtime_sha256": RUNTIME,
        "schedule_sha256": SCHEDULE_SHA,
        "isolated_schedule_sha256": r5.digest(isolated),
        "opponent_manifest": [row for row in manifest["decks"] if row["deck_key"] != "krang"],
        "cells": {},
        "cell_fingerprints": {},
        "replay_fingerprints": {},
        "completed_games": 0,
        "replayed_games": 0,
        "runtime_errors": 0,
    }


def verify(checkpoint: dict, expected: dict, isolated: list[dict]) -> None:
    for key, value in expected.items():
        if key not in {
            "cells",
            "cell_fingerprints",
            "replay_fingerprints",
            "completed_games",
            "replayed_games",
            "runtime_errors",
        }:
            assert checkpoint[key] == value, key
    schedules = {
        opponent: [row for row in isolated if set(row["pair"]) == {"krang", opponent}]
        for opponent in r1.DECKS
        if opponent != "krang"
    }
    assert set(checkpoint["cells"]) <= set(schedules)
    assert set(checkpoint["cell_fingerprints"]) == set(checkpoint["cells"])
    assert set(checkpoint["replay_fingerprints"]) <= set(checkpoint["cells"])
    assert checkpoint["completed_games"] == len(checkpoint["cells"]) * 100
    assert checkpoint["replayed_games"] == len(checkpoint["replay_fingerprints"]) * 100
    assert checkpoint["runtime_errors"] == 0
    for opponent, games in checkpoint["cells"].items():
        assert len(games) == 100
        assert [game["schedule"] for game in games] == schedules[opponent]
        assert all(game["seats"] == game["schedule"]["decks"] for game in games)
        assert all(game["runtime_error"] is None and game["runtime_fingerprint"] for game in games)
        assert sum(game["first_player"] == "krang" for game in games) == 50
        assert checkpoint["cell_fingerprints"][opponent] == refresh.original_cell_fingerprint(games)
        if opponent in checkpoint["replay_fingerprints"]:
            assert (
                checkpoint["replay_fingerprints"][opponent]
                == checkpoint["cell_fingerprints"][opponent]
            )


def save(checkpoint: dict) -> None:
    temporary = CHECKPOINT.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(checkpoint, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(CHECKPOINT)


def execute(
    pool: ProcessPoolExecutor, rows: list[dict], positions: dict[str, int], paths: dict[str, str]
) -> list[dict]:
    payloads = [(positions[r5.digest(row)], paths, row) for row in rows]
    games = list(pool.map(r1._run_one, payloads, chunksize=1))
    assert all(game["runtime_error"] is None and game["runtime_fingerprint"] for game in games), [
        game.get("runtime_error") for game in games if game.get("runtime_error")
    ]
    return games


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--replay", action="store_true")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    manifest, isolated, paths, _control = preflight()
    expected = template(manifest, isolated)
    checkpoint = (
        json.loads(CHECKPOINT.read_text(encoding="utf-8")) if CHECKPOINT.exists() else expected
    )
    verify(checkpoint, expected, isolated)
    if not (args.run or args.replay):
        print(
            json.dumps(
                {"status": "PREFLIGHT_PASS", "completed_games": checkpoint["completed_games"]}
            )
        )
        return 0
    assert 1 <= args.workers <= 16
    paths = {**paths, "krang": CANDIDATE}
    positions = {r5.digest(row): index for index, row in enumerate(isolated, 1)}
    cards = r1.catalog()
    with ProcessPoolExecutor(
        max_workers=args.workers, initializer=r1._init_worker, initargs=(cards,)
    ) as pool:
        for opponent in r1.DECKS:
            if opponent == "krang":
                continue
            rows = [row for row in isolated if set(row["pair"]) == {"krang", opponent}]
            if args.run and opponent not in checkpoint["cells"]:
                games = execute(pool, rows, positions, paths)
                checkpoint["cells"][opponent] = games
                checkpoint["cell_fingerprints"][opponent] = refresh.original_cell_fingerprint(games)
                checkpoint["completed_games"] += 100
                verify(checkpoint, expected, isolated)
                save(checkpoint)
                print(
                    json.dumps(
                        {"opponent": opponent, "completed_games": checkpoint["completed_games"]}
                    ),
                    flush=True,
                )
            if (
                args.replay
                and opponent in checkpoint["cells"]
                and opponent not in checkpoint["replay_fingerprints"]
            ):
                replay = execute(pool, rows, positions, paths)
                original = checkpoint["cells"][opponent]
                assert [game["runtime_fingerprint"] for game in replay] == [
                    game["runtime_fingerprint"] for game in original
                ]
                assert [(game["winner"], game["draw"], game["turn"]) for game in replay] == [
                    (game["winner"], game["draw"], game["turn"]) for game in original
                ]
                assert (
                    refresh.original_cell_fingerprint(replay)
                    == checkpoint["cell_fingerprints"][opponent]
                )
                checkpoint["replay_fingerprints"][opponent] = checkpoint["cell_fingerprints"][
                    opponent
                ]
                checkpoint["replayed_games"] += 100
                verify(checkpoint, expected, isolated)
                save(checkpoint)
                print(
                    json.dumps(
                        {"replayed": opponent, "verified_games": checkpoint["replayed_games"]}
                    ),
                    flush=True,
                )
    verify(checkpoint, expected, isolated)
    if checkpoint["completed_games"] == 900 and checkpoint["replayed_games"] == 900:
        EVIDENCE.write_text(
            json.dumps(checkpoint, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
