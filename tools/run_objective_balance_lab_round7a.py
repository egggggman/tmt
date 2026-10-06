"""Fail-closed new-runtime control refresh followed by frozen isolated R7-A.

Never composes candidate decks. Historical control and evidence are read-only.
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

import run_objective_balance_lab_baseline003_runtime_refresh as old  # noqa: E402
import run_objective_balance_lab_round1 as r1  # noqa: E402
import run_objective_balance_lab_round5 as r5  # noqa: E402
from objective_balance_lab_semantic_identity import identity  # noqa: E402

AUTHORITY = OBL / "ROUND_7_A_SEMANTIC_READINESS.json"
CANDIDATE = "docs/objective-balance-lab/candidates/KRANG_OBL_R7_A.txt"
CANDIDATE_SHA = "2d598af2d05212ffb0f19fe5f315b7bf8f85501975155f394448b0a48fa81ab1"
CONTROL = OBL / "BASELINE_003_R7A_SEMANTIC_CONTROL.json.gz"
RESULT = OBL / "ROUND_7_A_EVIDENCE.json.gz"
CONTROL_ID = "OBL-BASELINE-003-R7A-SEMANTIC-REFRESH-001"
REPLAY_PAIRS = (
    ("krang", "raphael"),
    ("krang", "shredder"),
    ("krang", "april_oneil"),
    ("leonardo", "shredder"),
    ("april_oneil", "raphael"),
    ("bebop_rocksteady", "donatello"),
)


def digest(value):
    # Normalize JSON object keys before hashing both in-memory and loaded records.
    normalized = json.loads(json.dumps(value, ensure_ascii=False))
    return hashlib.sha256(
        json.dumps(normalized, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()


def read(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def save(path, payload):
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(gzip.compress(data, mtime=0))
    temporary.replace(path)


def preflight():
    authority = json.loads(AUTHORITY.read_text())
    assert AUTHORITY.read_bytes() == subprocess.check_output(
        ["git", "show", f"HEAD:{AUTHORITY.relative_to(ROOT).as_posix()}"], cwd=ROOT
    )
    assert old.file_sha(Path(__file__)) == authority["execution_driver_sha256"]
    runtime = identity()
    assert runtime["aggregate_semantic_runtime_sha256"] == authority["semantic_runtime_sha256"]
    assert (
        identity("HEAD")["aggregate_semantic_runtime_sha256"]
        == authority["semantic_runtime_sha256"]
    ), "runtime must be committed and unchanged"
    assert (
        runtime["aggregate_semantic_runtime_sha256"]
        != (json.loads((OBL / "ROUND_7_A_READINESS.json").read_text())["semantic_runtime_sha256"])
    )
    assert (
        identity(authority["runtime_repository_sha"])["aggregate_semantic_runtime_sha256"]
        == (authority["semantic_runtime_sha256"])
    )
    manifest = json.loads(old.MANIFEST.read_text())
    assert old.file_sha(old.MANIFEST) == authority["baseline_manifest_sha256"]
    paths = {}
    for row in manifest["decks"]:
        old.verify_deck(row)
        r1.validate_deck(ROOT / row["source_path"], r1.catalog())
        paths[row["deck_key"]] = row["source_path"]
    assert set(paths) == set(r1.DECKS)
    candidate = (ROOT / CANDIDATE).read_bytes()
    assert hashlib.sha256(candidate).hexdigest() == CANDIDATE_SHA
    assert candidate == subprocess.check_output(["git", "show", f"HEAD:{CANDIDATE}"], cwd=ROOT)
    assert r1.diff(
        r1.validate_deck(ROOT / paths["krang"], r1.catalog())["cards"],
        r1.validate_deck(ROOT / CANDIDATE, r1.catalog())["cards"],
    ) == {
        "Does Machines": {"parent": 2, "candidate": 1},
        "Negate": {"parent": 3, "candidate": 2},
        "Ray Fillet, Man Ray": {"parent": 3, "candidate": 4},
        "Stockman, Mad Fly-entist": {"parent": 2, "candidate": 3},
    }
    schedule = r1.schedule()
    assert r5.digest(schedule) == old.SCHEDULE_SHA
    assert len(schedule) == 4500
    from tmnt_design_studio.card_interpreter07 import CardInterpreter, TokenDefinition
    from tmnt_design_studio.engine07 import load_facts
    from tmnt_design_studio.stage002 import _semantic_coverage, load_catalog

    interpreter = CardInterpreter()
    facts = load_facts(load_catalog(ROOT), {"Ray Fillet, Man Ray", "Stockman, Mad Fly-entist"})
    for card in facts.values():
        assert all(
            _semantic_coverage(interpreter, card, fragment, ())["fully_supported"]
            for fragment in interpreter.fragments(card)
        )
    mutagen = interpreter.PREDEFINED_TOKENS["mutagen"]
    assert isinstance(mutagen, TokenDefinition)
    assert interpreter.activated_ability_semantics(
        mutagen, mutagen.oracle_text
    ).coverage.fully_supported
    return authority, manifest, schedule, paths


def template(authority, manifest, schedule, *, candidate=False):
    result = {
        "schema": "obl-r7a-semantic-runtime-v1",
        "environment_id": "OBL-BASELINE-003",
        "evidence_id": "OBL-R7-KRANG-A" if candidate else CONTROL_ID,
        "semantic_runtime_sha256": authority["semantic_runtime_sha256"],
        "readiness_sha256": old.file_sha(AUTHORITY),
        "runtime_repository_sha": authority["runtime_repository_sha"],
        "baseline_manifest_sha256": old.file_sha(old.MANIFEST),
        "baseline_decks": manifest["decks"],
        "schedule_sha256": old.SCHEDULE_SHA,
        "selected_schedule_sha256": digest(schedule),
        "required_games": len(schedule),
        "games": [],
        "cell_hashes": {},
        "replays": {},
        "status": "IN_PROGRESS",
        "runtime_errors": 0,
        "combined_validation_run": False,
        "promotion_authorized": False,
    }
    if candidate:
        result.update(
            {
                "candidate_path": CANDIDATE,
                "candidate_sha256": CANDIDATE_SHA,
                "control_id": CONTROL_ID,
                "control_sha256": hashlib.sha256(CONTROL.read_bytes()).hexdigest(),
                "primary": ["raphael", "shredder"],
                "anti_polarization_sentinels": ["april_oneil", "leonardo"],
                "opponent_manifest": [d for d in manifest["decks"] if d["deck_key"] != "krang"],
            }
        )
    return result


def verify(payload, expected, schedule, *, complete=False):
    mutable = {"games", "cell_hashes", "replays", "status", "failure"}
    for key, value in expected.items():
        if key not in mutable:
            assert payload[key] == value, key
    games = payload["games"]
    assert len(games) % 100 == 0 and len(games) <= len(schedule)
    assert len(payload["cell_hashes"]) == len(games) // 100
    assert [g["schedule"] for g in games] == schedule[: len(games)]
    for index in range(0, len(games), 100):
        cell = games[index : index + 100]
        pair = cell[0]["schedule"]["pair"]
        key = "|".join(pair)
        assert payload["cell_hashes"][key] == digest(cell)
        assert Counter(g["first_player"] for g in cell) == {p: 50 for p in pair}
        assert all(g["seats"] == g["schedule"]["decks"] for g in cell)
        assert all(g["runtime_error"] is None and g["runtime_fingerprint"] for g in cell)
        if key in payload["replays"] and payload["evidence_id"] == "OBL-R7-KRANG-A":
            assert payload["replays"][key] == digest(cell)
    if complete:
        assert payload["status"] == "COMPLETE" and len(games) == len(schedule)
        if payload["evidence_id"] == "OBL-R7-KRANG-A":
            assert set(payload["replays"]) == set(payload["cell_hashes"])
        else:
            assert len(payload["replays"]) == len(REPLAY_PAIRS)
            for key, recorded in payload["replays"].items():
                original = next(g for g in games if "|".join(g["schedule"]["pair"]) == key)
                assert recorded == digest(original)


def execute(pool, rows, paths, offset):
    games = list(
        pool.map(
            r1._run_one, [(offset + i + 1, paths, row) for i, row in enumerate(rows)], chunksize=1
        )
    )
    failures = [g for g in games if g.get("runtime_error")]
    if failures:
        raise RuntimeError(json.dumps(failures))
    return games


def run(candidate, workers):
    authority, manifest, full_schedule, paths = preflight()
    schedule = [r for r in full_schedule if "krang" in r["pair"]] if candidate else full_schedule
    assert len(schedule) == (900 if candidate else 4500)
    if candidate:
        control = read(CONTROL)
        control_expected = template(authority, manifest, full_schedule)
        verify(control, control_expected, full_schedule, complete=True)
    expected = template(authority, manifest, schedule, candidate=candidate)
    destination = RESULT if candidate else CONTROL
    payload = read(destination) if destination.exists() else expected
    assert payload["status"] != "FAIL_CLOSED", "preserved failure requires investigation"
    verify(payload, expected, schedule)
    if candidate:
        paths = {**paths, "krang": CANDIDATE}
    with ProcessPoolExecutor(
        max_workers=workers, initializer=r1._init_worker, initargs=(r1.catalog(),)
    ) as pool:
        for offset in range(0, len(schedule), 100):
            rows = schedule[offset : offset + 100]
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
                verify(payload, expected, schedule)
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
            replay_required = candidate or any(set(rows[0]["pair"]) == set(p) for p in REPLAY_PAIRS)
            if replay_required and key not in payload["replays"]:
                original = payload["games"][offset : offset + (100 if candidate else 1)]
                replay = execute(pool, rows if candidate else rows[:1], paths, offset)
                assert digest(replay) == digest(original), key
                payload["replays"][key] = digest(replay) if candidate else digest(replay[0])
                save(destination, payload)
        payload["status"] = "COMPLETE"
        verify(payload, expected, schedule, complete=True)
        save(destination, payload)
    print(
        json.dumps(
            {
                "status": "COMPLETE",
                "evidence": destination.name,
                "games": len(payload["games"]),
                "replay_cells": len(payload["replays"]),
            }
        ),
        flush=True,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--control", action="store_true")
    parser.add_argument("--candidate", action="store_true")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    assert 1 <= args.workers <= 16
    assert not (args.control and args.candidate)
    if not (args.control or args.candidate):
        preflight()
        print("PREFLIGHT_PASS")
        return
    run(args.candidate, args.workers)


if __name__ == "__main__":
    main()
