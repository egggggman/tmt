"""Refresh unchanged Baseline 004 after the generic cycling pilot-policy change.

The preserved Combined 006 source is read-only. This runs all 45 control cells
under one committed semantic identity; it never substitutes a candidate deck.
"""

from __future__ import annotations

import argparse
import gzip
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

import run_objective_balance_lab_round1 as r1  # noqa: E402
import run_objective_balance_lab_round5 as r5  # noqa: E402
from objective_balance_lab_semantic_identity import identity  # noqa: E402

AUTHORITY = OBL / "BASELINE_004_CYCLING_PILOT_READINESS.json"
MANIFEST = OBL / "baselines/OBL_BASELINE_004_MANIFEST.json"
SOURCE = OBL / "COMBINED_006_R7A_EVIDENCE.json.gz"
RESULT = OBL / "BASELINE_004_CYCLING_PILOT_CONTROL.json.gz"
CONTROL_ID = "OBL-BASELINE-004-CYCLING-PILOT-REFRESH-001"
PRIOR_RUNTIME = "f40c4888ef9128d03819fc1be86dde1316b2115fd0d4fb365cd03b288453afa1"
SCHEDULE_SHA = "b5fd8ab57016b15662fca420d508c9aab3633ad14b7f7515d667492b0f8abf27"
REPLAY_PAIRS = (
    ("bebop_rocksteady", "leonardo"),
    ("bebop_rocksteady", "raphael"),
    ("bebop_rocksteady", "krang"),
    ("bebop_rocksteady", "april_oneil"),
    ("krang", "shredder"),
    ("donatello", "michelangelo"),
)


def digest(value: object) -> str:
    canonical = json.loads(json.dumps(value, ensure_ascii=False))
    return hashlib.sha256(
        json.dumps(canonical, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def read(path: Path) -> dict:
    return json.loads(gzip.decompress(path.read_bytes()))


def save(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(
        gzip.compress(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode(), mtime=0
        )
    )
    temporary.replace(path)


def preflight() -> tuple[dict, dict, list[dict], dict[str, str]]:
    authority_bytes = AUTHORITY.read_bytes()
    assert authority_bytes == subprocess.check_output(
        ["git", "show", f"HEAD:{AUTHORITY.relative_to(ROOT).as_posix()}"], cwd=ROOT
    )
    authority = json.loads(authority_bytes)
    runtime = identity()
    assert authority["status"] == "READY_FOR_UNCHANGED_BASELINE004_CONTROL"
    assert runtime["aggregate_semantic_runtime_sha256"] == authority["semantic_runtime_sha256"]
    assert (
        identity("HEAD")["aggregate_semantic_runtime_sha256"]
        == authority["semantic_runtime_sha256"]
    ), "new pilot policy must be committed and unchanged"
    assert [(row["path"], row["sha256"]) for row in runtime["files"]] == [
        (row["path"], row["sha256"]) for row in authority["semantic_runtime_identity"]["files"]
    ]
    assert file_sha(Path(__file__)) == authority["execution_driver_sha256"]
    assert file_sha(MANIFEST) == authority["baseline_manifest_sha256"]
    assert file_sha(SOURCE) == authority["source_combined_sha256"]
    assert (
        subprocess.check_output(
            ["git", "hash-object", SOURCE.relative_to(ROOT).as_posix()], cwd=ROOT, text=True
        ).strip()
        == authority["source_combined_git_blob_sha1"]
    )
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["environment_id"] == "OBL-BASELINE-004"
    assert manifest["semantic_runtime_sha256"] == PRIOR_RUNTIME
    assert manifest["source_combined_environment"] == "OBL-COMBINED-006"
    assert (
        manifest["source_combined_evidence"]["git_blob_sha1"]
        == authority["source_combined_git_blob_sha1"]
    )
    assert {row["deck_key"] for row in manifest["decks"]} == set(r1.DECKS)
    cards = r1.catalog()
    paths = {}
    for row in manifest["decks"]:
        relative = row["source_path"]
        committed = subprocess.check_output(["git", "show", f"HEAD:{relative}"], cwd=ROOT)
        local = (ROOT / relative).read_bytes()
        assert local.replace(b"\r\n", b"\n") == committed.replace(b"\r\n", b"\n")
        assert row["sha256"] in {
            hashlib.sha256(value).hexdigest()
            for value in (
                local,
                committed,
                committed.replace(b"\r\n", b"\n"),
                committed.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"),
            )
        }, relative
        assert sum(r1.validate_deck(ROOT / relative, cards)["cards"].values()) == 60
        paths[row["deck_key"]] = relative
    schedule = r1.schedule()
    assert len(schedule) == 4500 and r5.digest(schedule) == SCHEDULE_SHA
    assert Counter(row["orientation"] for row in schedule) == {
        "canonical": 2250,
        "reversed": 2250,
    }
    assert authority["schedule_sha256"] == SCHEDULE_SHA
    assert authority["prior_semantic_runtime_sha256"] == PRIOR_RUNTIME
    assert authority["baseline_deck_hashes"] == {
        row["deck_key"]: row["sha256"] for row in manifest["decks"]
    }
    return authority, manifest, schedule, paths


def template(authority: dict, manifest: dict, schedule: list[dict]) -> dict:
    return {
        "schema": "obl-baseline004-cycling-pilot-control-v1",
        "environment_id": "OBL-BASELINE-004",
        "evidence_id": CONTROL_ID,
        "baseline_manifest_sha256": file_sha(MANIFEST),
        "baseline_decks": manifest["decks"],
        "source_combined_sha256": file_sha(SOURCE),
        "semantic_runtime_sha256": authority["semantic_runtime_sha256"],
        "prior_semantic_runtime_sha256": PRIOR_RUNTIME,
        "readiness_sha256": file_sha(AUTHORITY),
        "schedule_sha256": SCHEDULE_SHA,
        "selected_schedule_sha256": digest(schedule),
        "required_games": 4500,
        "games": [],
        "cell_hashes": {},
        "replays": {},
        "status": "IN_PROGRESS",
        "runtime_errors": 0,
        "new_candidate_games": 0,
        "combined_validation_run": False,
        "promotion_authorized": False,
    }


def verify(payload: dict, expected: dict, schedule: list[dict], *, complete: bool = False) -> None:
    for key, value in expected.items():
        if key not in {"games", "cell_hashes", "replays", "status", "failure"}:
            assert payload[key] == value, key
    games = payload["games"]
    assert len(games) <= 4500 and len(games) % 100 == 0
    assert [game["schedule"] for game in games] == schedule[: len(games)]
    assert len(payload["cell_hashes"]) == len(games) // 100
    for offset in range(0, len(games), 100):
        cell = games[offset : offset + 100]
        pair = schedule[offset]["pair"]
        key = "|".join(pair)
        assert payload["cell_hashes"][key] == digest(cell)
        assert Counter(game["first_player"] for game in cell) == {deck: 50 for deck in pair}
        assert all(game["seats"] == game["schedule"]["decks"] for game in cell)
        assert all(game["runtime_error"] is None and game["runtime_fingerprint"] for game in cell)
        if key in payload["replays"]:
            assert payload["replays"][key] == digest(cell[0])
    if complete:
        assert payload["status"] == "COMPLETE" and len(games) == 4500
        assert len(payload["cell_hashes"]) == 45
        assert len(payload["replays"]) == len(REPLAY_PAIRS)
        assert {key for key in payload["replays"]} == {
            "|".join(row["pair"])
            for row in schedule
            if any(set(row["pair"]) == set(pair) for pair in REPLAY_PAIRS)
        }


def execute(pool: ProcessPoolExecutor, rows: list[dict], paths: dict, offset: int) -> list[dict]:
    result = list(
        pool.map(
            r1._run_one,
            [(offset + index + 1, paths, row) for index, row in enumerate(rows)],
            chunksize=1,
        )
    )
    failures = [game for game in result if game.get("runtime_error")]
    if failures:
        raise RuntimeError(json.dumps(failures))
    return result


def run(*, workers: int) -> None:
    authority, manifest, schedule, paths = preflight()
    expected = template(authority, manifest, schedule)
    payload = read(RESULT) if RESULT.exists() else expected
    assert payload["status"] != "FAIL_CLOSED", "preserved failure needs investigation"
    verify(payload, expected, schedule)
    with ProcessPoolExecutor(
        max_workers=workers, initializer=r1._init_worker, initargs=(r1.catalog(),)
    ) as pool:
        for offset in range(0, 4500, 100):
            rows = schedule[offset : offset + 100]
            key = "|".join(rows[0]["pair"])
            if offset >= len(payload["games"]):
                try:
                    cell = execute(pool, rows, paths, offset)
                except Exception as error:
                    payload["status"] = "FAIL_CLOSED"
                    payload["failure"] = str(error)
                    save(RESULT, payload)
                    raise
                payload["games"].extend(cell)
                payload["cell_hashes"][key] = digest(cell)
                verify(payload, expected, schedule)
                save(RESULT, payload)
                print(json.dumps({"pair": key, "games": len(payload["games"])}), flush=True)
            if (
                any(set(rows[0]["pair"]) == set(pair) for pair in REPLAY_PAIRS)
                and key not in payload["replays"]
            ):
                try:
                    replay = execute(pool, rows[:1], paths, offset)[0]
                    assert digest(replay) == digest(payload["games"][offset])
                except Exception as error:
                    payload["status"] = "FAIL_CLOSED"
                    payload["failure"] = f"replay {key}: {error}"
                    save(RESULT, payload)
                    raise
                payload["replays"][key] = digest(replay)
                save(RESULT, payload)
        payload["status"] = "COMPLETE"
        verify(payload, expected, schedule, complete=True)
        save(RESULT, payload)
    print(json.dumps({"status": "COMPLETE", "games": 4500, "replay_samples": 6}), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    assert 1 <= args.workers <= 16
    if args.run:
        run(workers=args.workers)
    else:
        authority, manifest, schedule, _ = preflight()
        if RESULT.exists():
            verify(read(RESULT), template(authority, manifest, schedule), schedule)
        print("BASELINE_004_PILOT_CONTROL_PREFLIGHT_PASS")


if __name__ == "__main__":
    main()
