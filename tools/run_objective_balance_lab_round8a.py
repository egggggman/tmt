"""Fail-closed R8-A: refresh unchanged Baseline 004, then isolate its frozen candidate."""

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

import run_objective_balance_lab_baseline004_pilot_refresh as old  # noqa: E402
import run_objective_balance_lab_round1 as r1  # noqa: E402
import run_objective_balance_lab_round5 as r5  # noqa: E402
from objective_balance_lab_semantic_identity import identity  # noqa: E402

AUTHORITY = OBL / "ROUND_8_A_SEMANTIC_READINESS.json"
MANIFEST = OBL / "baselines/OBL_BASELINE_004_MANIFEST.json"
SOURCE = OBL / "BASELINE_004_CYCLING_PILOT_CONTROL.json.gz"
REGISTRY = OBL / "ENVIRONMENT_REGISTRY.json"
CANDIDATE = OBL / "candidates/BEBOP_ROCKSTEADY_OBL_R8_A.txt"
RESULT = OBL / "BASELINE_004_R8A_ETB_RUNTIME_CONTROL.json.gz"
CANDIDATE_RESULT = OBL / "ROUND_8_A_EVIDENCE.json.gz"
CONTROL_ID = "OBL-BASELINE-004-R8A-ETB-RUNTIME-REFRESH-001"
CANDIDATE_ID = "OBL-R8-BEBOP-A"
PRIOR_RUNTIME = "24ce312cdac00d914606d1f4c111813826ca615768d631532e995faf1c8d57fa"
SCHEDULE_SHA = "b5fd8ab57016b15662fca420d508c9aab3633ad14b7f7515d667492b0f8abf27"
REPLAY_PAIRS = (
    ("bebop_rocksteady", "leonardo"),
    ("bebop_rocksteady", "raphael"),
    ("bebop_rocksteady", "krang"),
    ("bebop_rocksteady", "april_oneil"),
    ("krang", "shredder"),
    ("donatello", "michelangelo"),
)
SELECTED_REPLAY_PAIRS = tuple(
    ("bebop_rocksteady", deck) for deck in r1.DECKS if deck != "bebop_rocksteady"
)


def digest(value: object) -> str:
    canonical = json.loads(json.dumps(value, ensure_ascii=False))
    return hashlib.sha256(
        json.dumps(canonical, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def raw_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    assert authority["status"] == "ETB_SEMANTICS_VALIDATED_CONTROL_REQUIRED"
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
    assert raw_sha(SOURCE) == authority["source_control_sha256"]
    assert (
        subprocess.check_output(
            ["git", "hash-object", SOURCE.relative_to(ROOT).as_posix()], cwd=ROOT, text=True
        ).strip()
        == authority["source_control_git_blob_sha1"]
    )
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["environment_id"] == "OBL-BASELINE-004"
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert manifest["environment_id"] == registry["environment_id"]
    assert registry["semantic_runtime_sha256"] == PRIOR_RUNTIME
    assert (
        registry["current_simulation_control"]["git_blob_sha1"]
        == authority["source_control_git_blob_sha1"]
    )
    assert registry["current_simulation_control"]["sha256"] == raw_sha(SOURCE)
    assert file_sha(REGISTRY) == authority["registry_sha256"]
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
    assert file_sha(CANDIDATE) == authority["candidate_sha256"]
    assert CANDIDATE.read_bytes() == subprocess.check_output(
        ["git", "show", f"HEAD:{CANDIDATE.relative_to(ROOT).as_posix()}"], cwd=ROOT
    )
    candidate = r1.validate_deck(CANDIDATE, cards)["cards"]
    parent = r1.validate_deck(ROOT / paths["bebop_rocksteady"], cards)["cards"]
    assert {
        card: parent[card] - candidate.get(card, 0)
        for card in parent
        if parent[card] > candidate.get(card, 0)
    } == {"Illegitimate Business": 2}
    assert {
        card: candidate[card] - parent.get(card, 0)
        for card in candidate
        if candidate[card] > parent.get(card, 0)
    } == {"Primordial Pachyderm": 2}
    assert authority["candidate_id"] == CANDIDATE_ID
    source = read(SOURCE)
    old.verify(source, source, schedule, complete=True)
    assert source["semantic_runtime_sha256"] == PRIOR_RUNTIME
    assert source["evidence_id"] == registry["current_simulation_control"]["control_id"]
    return authority, manifest, schedule, paths


def template(
    authority: dict, manifest: dict, schedule: list[dict], *, candidate: bool = False
) -> dict:
    return {
        "schema": "obl-round8a-isolated-v1" if candidate else "obl-baseline004-r8a-etb-control-v1",
        "environment_id": "OBL-BASELINE-004",
        "evidence_id": CANDIDATE_ID if candidate else CONTROL_ID,
        "baseline_manifest_sha256": file_sha(MANIFEST),
        "baseline_decks": manifest["decks"],
        "source_control_sha256": raw_sha(SOURCE),
        "semantic_runtime_sha256": authority["semantic_runtime_sha256"],
        "prior_semantic_runtime_sha256": PRIOR_RUNTIME,
        "readiness_sha256": file_sha(AUTHORITY),
        "schedule_sha256": SCHEDULE_SHA,
        "selected_schedule_sha256": digest(schedule),
        "required_games": len(schedule),
        "candidate_deck_sha256": authority["candidate_sha256"] if candidate else None,
        "runtime_control_sha256": raw_sha(RESULT) if candidate else None,
        "games": [],
        "cell_hashes": {},
        "replays": {},
        "status": "IN_PROGRESS",
        "runtime_errors": 0,
        "new_candidate_games": 0,
        "combined_validation_run": False,
        "promotion_authorized": False,
    }


def verify(
    payload: dict,
    expected: dict,
    schedule: list[dict],
    *,
    complete: bool = False,
    replay_pairs: tuple[tuple[str, str], ...] = REPLAY_PAIRS,
) -> None:
    for key, value in expected.items():
        if key not in {"games", "cell_hashes", "replays", "status", "failure"}:
            assert payload[key] == value, key
    games = payload["games"]
    assert len(games) <= len(schedule) and len(games) % 100 == 0
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
            assert payload["replays"][key] == digest(
                cell if expected["candidate_deck_sha256"] else cell[0]
            )
    if complete:
        assert payload["status"] == "COMPLETE" and len(games) == len(schedule)
        assert len(payload["cell_hashes"]) == len(schedule) // 100
        assert len(payload["replays"]) == len(replay_pairs)
        assert {key for key in payload["replays"]} == {
            "|".join(row["pair"])
            for row in schedule
            if any(set(row["pair"]) == set(pair) for pair in replay_pairs)
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


def run(*, workers: int, candidate: bool) -> None:
    authority, manifest, schedule, paths = preflight()
    selected = [row for row in schedule if "bebop_rocksteady" in row["pair"]]
    assert len(selected) == 900 and len(schedule) == 4500
    if candidate:
        assert RESULT.exists(), "complete refreshed control required"
        control = read(RESULT)
        verify(control, template(authority, manifest, schedule), schedule, complete=True)
        assert control["status"] == "COMPLETE"
        paths = {**paths, "bebop_rocksteady": CANDIDATE.relative_to(ROOT).as_posix()}
    rows_to_run = selected if candidate else schedule
    replay_pairs = SELECTED_REPLAY_PAIRS if candidate else REPLAY_PAIRS
    expected = template(authority, manifest, rows_to_run, candidate=candidate)
    destination = CANDIDATE_RESULT if candidate else RESULT
    payload = read(destination) if destination.exists() else expected
    assert payload["status"] != "FAIL_CLOSED", "preserved failure needs investigation"
    verify(payload, expected, rows_to_run, replay_pairs=replay_pairs)
    with ProcessPoolExecutor(
        max_workers=workers, initializer=r1._init_worker, initargs=(r1.catalog(),)
    ) as pool:
        for offset in range(0, len(rows_to_run), 100):
            rows = rows_to_run[offset : offset + 100]
            key = "|".join(rows[0]["pair"])
            if offset >= len(payload["games"]):
                try:
                    cell = execute(pool, rows, paths, offset)
                except Exception as error:
                    payload["status"] = "FAIL_CLOSED"
                    payload["failure"] = str(error)
                    save(destination, payload)
                    raise
                payload["games"].extend(cell)
                payload["cell_hashes"][key] = digest(cell)
                verify(payload, expected, rows_to_run, replay_pairs=replay_pairs)
                save(destination, payload)
                print(
                    json.dumps(
                        {
                            "phase": "candidate" if candidate else "control",
                            "pair": key,
                            "games": len(payload["games"]),
                        }
                    ),
                    flush=True,
                )
            if (
                any(set(rows[0]["pair"]) == set(pair) for pair in replay_pairs)
                and key not in payload["replays"]
            ):
                try:
                    replay = execute(pool, rows if candidate else rows[:1], paths, offset)
                    original = payload["games"][offset : offset + (100 if candidate else 1)]
                    assert digest(replay) == digest(original)
                except Exception as error:
                    payload["status"] = "FAIL_CLOSED"
                    payload["failure"] = f"replay {key}: {error}"
                    save(destination, payload)
                    raise
                payload["replays"][key] = digest(replay if candidate else replay[0])
                save(destination, payload)
        payload["status"] = "COMPLETE"
        verify(payload, expected, rows_to_run, complete=True, replay_pairs=replay_pairs)
        save(destination, payload)
    print(
        json.dumps(
            {
                "status": "COMPLETE",
                "games": len(rows_to_run),
                "replay_games": 900 if candidate else 6,
            }
        ),
        flush=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--control", action="store_true")
    parser.add_argument("--candidate", action="store_true")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    assert 1 <= args.workers <= 16
    assert not (args.control and args.candidate)
    if args.control or args.candidate:
        run(workers=args.workers, candidate=args.candidate)
    else:
        authority, manifest, schedule, _ = preflight()
        if RESULT.exists():
            verify(read(RESULT), template(authority, manifest, schedule), schedule)
        print("ROUND_8_A_SEMANTIC_PREFLIGHT_PASS_CONTROL_REQUIRED")


if __name__ == "__main__":
    main()
