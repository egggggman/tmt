"""Run Design Studio's immutable Krang R6-A diagnostic, one frozen cell at a time."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
sys.path.insert(0, str(ROOT / "tools"))

import run_objective_balance_lab_round1 as r1  # noqa: E402
from objective_balance_lab_semantic_identity import (  # noqa: E402
    assert_pre_chrome_evidence_runtime,
    identity,
)

from tmnt_design_studio.pilot07 import AcceptancePilot  # noqa: E402
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, run_game  # noqa: E402

EXPERIMENT = "OBL-R6-KRANG-A"
CANDIDATE = "docs/objective-balance-lab/candidates/KRANG_OBL_R6_A.txt"
CANDIDATE_SHA = "f7d5734781c06349d33dc3396614ec8f7e448ada4ceb8d468db84d1f268a38fa"
CANDIDATE_GIT_SHA = "15d218c5395eb66e1e36bdd66758051287ed383fb09d803f0eec465284e8d3f6"
MANIFEST = "docs/objective-balance-lab/baselines/OBL_BASELINE_003_MANIFEST.json"
BASELINE_EVIDENCE = "docs/objective-balance-lab/COMBINED_005_EVIDENCE.json"
CHECKPOINT = OBL / "ROUND_6_A_CHECKPOINT.json"
EVIDENCE = OBL / "ROUND_6_A_EVIDENCE.json"
RUNTIME = "78bcce5b5f635f11c67247df91f90fef2bf0dbf948973c5c1ac38419f28b0e25"
PARENT_SHA = "5a52bc59b5de1034721ba17d1c1d4f12c493ec70681c1a910c8230808e4e4f96"
STAGE1 = ("shredder", "raphael")


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def git_sha(path: str) -> str:
    return hashlib.sha256(git_bytes(path)).hexdigest()


def git_bytes(path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"HEAD:{path}"], cwd=ROOT)


def verify_preserved_file(path: str, recorded_sha: str) -> None:
    working = (ROOT / path).read_bytes()
    canonical = git_bytes(path)
    assert working.replace(b"\r\n", b"\n") == canonical.replace(b"\r\n", b"\n")
    crlf = canonical.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    assert recorded_sha in {
        hashlib.sha256(working).hexdigest(),
        hashlib.sha256(canonical).hexdigest(),
        hashlib.sha256(crlf).hexdigest(),
    }, path


def atomic_json(path: Path, value: dict) -> None:
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="\n", dir=path.parent, delete=False
    ) as stream:
        temporary = Path(stream.name)
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    os.replace(temporary, path)


def preflight() -> tuple[dict, list[dict], dict[str, str], list[dict]]:
    manifest = json.loads((ROOT / MANIFEST).read_text(encoding="utf-8"))
    source = json.loads((ROOT / BASELINE_EVIDENCE).read_text(encoding="utf-8"))
    schedule = r1.schedule()
    assert len(schedule) == 4500
    assert digest(schedule) == manifest["schedule_identity"] == source["schedule_sha256"]
    assert manifest["semantic_runtime_sha256"] == source["semantic_runtime_sha256"] == RUNTIME
    assert_pre_chrome_evidence_runtime(RUNTIME)
    assert len(source["combined_games"]) == 4500
    assert not source["runtime_errors"]
    verify_preserved_file(CANDIDATE, CANDIDATE_SHA)
    assert git_sha(CANDIDATE) == CANDIDATE_GIT_SHA
    paths = {row["deck_key"]: row["source_path"] for row in manifest["decks"]}
    hashes = {row["deck_key"]: row["sha256"] for row in manifest["decks"]}
    assert len(paths) == len(hashes) == 10
    assert hashes["krang"] == PARENT_SHA
    for deck, path in paths.items():
        # Historical prototype manifests used checked-out CRLF bytes, while
        # promoted artifacts used Git LF bytes. Verify content and either form.
        verify_preserved_file(path, hashes[deck])
    cards = r1.catalog()
    parent = r1.validate_deck(ROOT / paths["krang"], cards)
    candidate = r1.validate_deck(ROOT / CANDIDATE, cards)
    assert parent["cards"]["Negate"] == 3
    assert candidate["cards"]["Negate"] == 2
    assert candidate["cards"]["Donatello, Turtle Techie"] == 1
    assert r1.diff(parent["cards"], candidate["cards"]) == {
        "Donatello, Turtle Techie": {"parent": 0, "candidate": 1},
        "Negate": {"parent": 3, "candidate": 2},
    }
    assert candidate["color_identity"] == "U"
    bank = {digest(game["schedule"]): game for game in source["combined_games"]}
    assert len(bank) == 4500
    for row in schedule:
        game = bank[digest(row)]
        assert game["schedule"] == row and game["seats"] == row["decks"]
        assert game["runtime_fingerprint"] and not game["runtime_error"]
    return manifest, schedule, paths, source["combined_games"]


_CARDS: dict = {}


def _init(cards: dict) -> None:
    r1._init_worker(cards)
    global _CARDS
    _CARDS = cards


def _one(item: tuple[int, dict[str, str], dict]) -> dict:
    index, paths, row = item
    a, b = row["decks"]
    try:
        spec = GameSpec(
            f"obl-r1-{index:05d}",
            f"{a}-vs-{b}",
            row["seed"],
            row["orientation"],
            (DeckSpec(a, paths[a]), DeckSpec(b, paths[b])),
        )
        snapshot = run_game(ROOT, spec, AcceptancePilot())
        result = r1.game_metrics(snapshot, (a, b), _CARDS)
        effect_events = [
            event
            for event in snapshot.get("events", [])
            if event.get("event") == "etb_artifact_draw_resolved"
            and event.get("source") == "Donatello, Turtle Techie"
            and event.get("controller") == [a, b].index("krang")
        ]
        result.update(
            {
                "schedule": row,
                "seats": [a, b],
                "runtime_error": None,
                "turtle_techie_effects": {
                    "resolved": len(effect_events),
                    "condition_met": sum(
                        bool(event.get("condition_met")) for event in effect_events
                    ),
                    "cards_drawn": sum(
                        bool(event.get("draw_succeeded")) for event in effect_events
                    ),
                },
            }
        )
        return result
    except Exception as error:
        return {
            "schedule": row,
            "seats": [a, b],
            "runtime_error": f"{type(error).__name__}: {error}",
        }


def run_cell(paths: dict[str, str], rows: list[dict], workers: int) -> list[dict]:
    # Match the index assigned by the established 900-game isolated runner.
    positions = {
        digest(row): index
        for index, row in enumerate((r for r in r1.schedule() if "krang" in r["pair"]), 1)
    }
    with ProcessPoolExecutor(
        max_workers=workers, initializer=_init, initargs=(r1.catalog(),)
    ) as pool:
        return list(pool.map(_one, [(positions[digest(row)], paths, row) for row in rows]))


def verify(payload: dict, schedule: list[dict]) -> None:
    assert payload["experiment_id"] == EXPERIMENT
    assert payload["candidate_sha256"] == CANDIDATE_SHA
    assert payload["parent_sha256"] == PARENT_SHA
    assert payload["semantic_runtime_sha256"] == RUNTIME
    assert payload["schedule_sha256"] == digest(schedule)
    for opponent, games in payload["cells"].items():
        assert opponent in r1.DECKS and opponent != "krang"
        expected = [row for row in schedule if set(row["pair"]) == {"krang", opponent}]
        assert len(games) == len(expected) == 100
        assert [game["schedule"] for game in games] == expected
        assert sum(game["first_player"] == "krang" for game in games) == 50
        assert all(game["runtime_fingerprint"] and not game["runtime_error"] for game in games)
        assert all(game["seats"] == game["schedule"]["decks"] for game in games)
    assert len(payload["cells"]) in (0, 1, 2, 9) or 2 < len(payload["cells"]) < 9
    assert payload["completed_games"] == sum(map(len, payload["cells"].values()))


def cell_rate(games: list[dict]) -> float:
    return (
        sum(game["winner"] == "krang" for game in games) + sum(game["draw"] for game in games) / 2
    ) / len(games)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--enrich-replay", action="store_true")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    _manifest, schedule, paths, _baseline = preflight()
    if args.run or args.enrich_replay:
        assert identity()["aggregate_semantic_runtime_sha256"] == RUNTIME, (
            "historical Round 6-A games cannot run under a changed semantic runtime"
        )
    if args.enrich_replay:
        payload = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        verify(payload, schedule)
        paths["krang"] = CANDIDATE
        for opponent, original in payload["cells"].items():
            rows = [row for row in schedule if set(row["pair"]) == {"krang", opponent}]
            replay = run_cell(paths, rows, args.workers)
            for old, new in zip(original, replay, strict=True):
                for key in (
                    "schedule",
                    "seats",
                    "winner",
                    "draw",
                    "turn",
                    "runtime_fingerprint",
                    "signature_casts",
                ):
                    assert old[key] == new[key], (opponent, key)
                assert not new["runtime_error"]
                old["turtle_techie_effects"] = new["turtle_techie_effects"]
            payload["effect_replay_verified_games"] = payload.get(
                "effect_replay_verified_games", 0
            ) + len(replay)
            atomic_json(CHECKPOINT, payload)
            print(
                json.dumps(
                    {"replayed_cell": opponent, "verified": payload["effect_replay_verified_games"]}
                ),
                flush=True,
            )
        assert payload["effect_replay_verified_games"] == payload["completed_games"]
        atomic_json(EVIDENCE, payload)
        return 0
    if not args.run:
        print(json.dumps({"status": "PREFLIGHT_PASS", "candidate_sha256": CANDIDATE_SHA}))
        return 0
    payload = (
        json.loads(CHECKPOINT.read_text(encoding="utf-8"))
        if CHECKPOINT.exists()
        else {
            "schema": "objective-balance-lab-round6a-v1",
            "experiment_id": EXPERIMENT,
            "candidate_path": CANDIDATE,
            "candidate_sha256": CANDIDATE_SHA,
            "candidate_git_blob_sha256": CANDIDATE_GIT_SHA,
            "parent_manifest_path": MANIFEST,
            "parent_sha256": PARENT_SHA,
            "baseline_evidence_path": BASELINE_EVIDENCE,
            "semantic_runtime_sha256": RUNTIME,
            "schedule_sha256": digest(schedule),
            "stage1_rule": (
                "Continue only if at least one severe diagnostic improves and both do not worsen; "
                "stop on any runtime or semantic blocker."
            ),
            "stage1_decision": None,
            "cells": {},
            "completed_games": 0,
        }
    )
    verify(payload, schedule)
    paths["krang"] = CANDIDATE
    for opponent in STAGE1:
        if opponent in payload["cells"]:
            continue
        rows = [row for row in schedule if set(row["pair"]) == {"krang", opponent}]
        games = run_cell(paths, rows, args.workers)
        assert all(not game.get("runtime_error") for game in games), games[:1]
        payload["cells"][opponent] = games
        payload["completed_games"] += 100
        verify(payload, schedule)
        atomic_json(CHECKPOINT, payload)
        print(
            json.dumps({"opponent": opponent, "krang_rate": cell_rate(games), "games": 100}),
            flush=True,
        )
    shredder = cell_rate(payload["cells"]["shredder"])
    raphael = cell_rate(payload["cells"]["raphael"])
    # Frozen before observing Stage 1: a positive severe-cell signal is needed,
    # and a double regression cannot qualify. No post-hoc percentage threshold.
    continue_stage2 = (shredder > 0.12 or raphael > 0.13) and not (
        shredder < 0.12 and raphael < 0.13
    )
    payload["stage1_decision"] = "CONTINUE" if continue_stage2 else "STOP"
    atomic_json(CHECKPOINT, payload)
    print(
        json.dumps(
            {
                "stage1_decision": payload["stage1_decision"],
                "shredder": shredder,
                "raphael": raphael,
            }
        ),
        flush=True,
    )
    if continue_stage2:
        for opponent in r1.DECKS:
            if opponent == "krang" or opponent in payload["cells"]:
                continue
            rows = [row for row in schedule if set(row["pair"]) == {"krang", opponent}]
            games = run_cell(paths, rows, args.workers)
            assert all(not game.get("runtime_error") for game in games), games[:1]
            payload["cells"][opponent] = games
            payload["completed_games"] += 100
            verify(payload, schedule)
            atomic_json(CHECKPOINT, payload)
            print(
                json.dumps(
                    {
                        "opponent": opponent,
                        "krang_rate": cell_rate(games),
                        "completed_games": payload["completed_games"],
                    }
                ),
                flush=True,
            )
    atomic_json(EVIDENCE, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
