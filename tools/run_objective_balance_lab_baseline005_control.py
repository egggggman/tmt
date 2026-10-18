"""Run the single HQ-authorized Baseline 005 calibration control."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
sys.path.insert(0, str(ROOT / "tools"))
import run_objective_balance_lab_round1 as r1  # noqa: E402
from objective_balance_lab_semantic_identity import identity  # noqa: E402

MANIFEST = OBL / "baselines/OBL_BASELINE_005_MANIFEST.json"
READINESS = ROOT / "docs/cardcade/ISSUE_289_MICHELANGELO_IMPROVISER_CALIBRATION_READINESS.json"
LEDGER = ROOT / "docs/cardcade/ISSUE_289_COVERAGE_LEDGER.csv"
RESULT = OBL / "BASELINE_005_ISSUE289_FINAL_CONTROL.json.gz"
RUNTIME = "69d09aa4e63bdbc05dc0d7c4ecc212b4739c088034d273548880838bcd5ab130"
SCHEDULE_SHA = "b5fd8ab57016b15662fca420d508c9aab3633ad14b7f7515d667492b0f8abf27"


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()


def schedule_digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path: Path, payload: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(
        gzip.compress(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode(), mtime=0
        )
    )
    tmp.replace(path)


def preflight() -> tuple[dict, list[dict], dict[str, str]]:
    assert not RESULT.exists(), f"refusing to overwrite existing control: {RESULT}"
    manifest = json.loads(MANIFEST.read_text())
    readiness = json.loads(READINESS.read_text())
    assert identity()["aggregate_semantic_runtime_sha256"] == RUNTIME
    assert readiness["semantic_runtime_sha256"] == RUNTIME
    assert readiness["calibration_readiness"] == "READY"
    assert readiness["critical_remaining"] == readiness["important_remaining"] == 0
    assert readiness["unbounded_residual_important"] == 0
    assert len(list(__import__("csv").DictReader(LEDGER.open()))) == 172
    assert manifest["environment_id"] == "OBL-BASELINE-005"
    # The promoted Baseline 005 manifest records its historical promotion runtime;
    # this control intentionally replays the unchanged decks under final Issue #289.
    assert manifest["semantic_runtime_sha256"] != RUNTIME
    cards = r1.catalog()
    paths: dict[str, str] = {}
    for row in manifest["decks"]:
        path = ROOT / row["source_path"]
        # Historical deck hashes use CRLF canonicalization; LF/CRLF are content-equivalent.
        current = path.read_bytes()
        canonical = current.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        assert row["sha256"] in {sha(path), hashlib.sha256(canonical).hexdigest()}
        assert sum(r1.validate_deck(path, cards)["cards"].values()) == 60
        paths[row["deck_key"]] = row["source_path"]
    schedule = r1.schedule()
    assert len(schedule) == 4500
    assert schedule_digest(schedule) == SCHEDULE_SHA == manifest["schedule_identity"]
    assert Counter(row["orientation"] for row in schedule) == {"canonical": 2250, "reversed": 2250}
    assert len({tuple(row["pair"]) for row in schedule}) == 45
    return manifest, schedule, paths


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    manifest, schedule, paths = preflight()
    if not args.run:
        print(
            json.dumps({"status": "PREFLIGHT_PASS", "games": 4500, "cells": 45, "runtime": RUNTIME})
        )
        return 0
    expected = {
        "schema": "obl-baseline005-final-control-v1",
        "environment_id": "OBL-BASELINE-005",
        "evidence_id": "OBL-BASELINE-005-FINAL-CONTROL-001",
        "baseline_manifest_sha256": sha(MANIFEST),
        "baseline_decks": manifest["decks"],
        "semantic_runtime_sha256": RUNTIME,
        "manifest_semantic_runtime_sha256": manifest["semantic_runtime_sha256"],
        "schedule_sha256": SCHEDULE_SHA,
        "required_games": 4500,
        "games": [],
        "cell_hashes": {},
        "replays": {},
        "runtime_errors": 0,
        "status": "IN_PROGRESS",
        "promotion_authorized": False,
    }
    cards = r1.catalog()
    replay_pairs = (
        ("leonardo", "raphael"),
        ("bebop_rocksteady", "raphael"),
        ("donatello", "michelangelo"),
        ("april_oneil", "casey_jones"),
        ("krang", "shredder"),
        ("splinter", "shredder"),
    )
    with ProcessPoolExecutor(
        max_workers=args.workers, initializer=r1._init_worker, initargs=(cards,)
    ) as pool:
        for offset in range(0, len(schedule), 100):
            cell_rows = schedule[offset : offset + 100]
            results = list(
                pool.map(
                    r1._run_one,
                    [(offset + i + 1, paths, row) for i, row in enumerate(cell_rows)],
                    chunksize=1,
                )
            )
            failures = [g for g in results if g.get("runtime_error")]
            if failures:
                expected["status"] = "FAIL_CLOSED"
                expected["failure"] = failures
                save(RESULT, expected)
                raise RuntimeError(f"runtime failure in cell {cell_rows[0]['pair']}")
            expected["games"].extend(results)
            key = "|".join(cell_rows[0]["pair"])
            expected["cell_hashes"][key] = digest(results)
            if any(set(cell_rows[0]["pair"]) == set(pair) for pair in replay_pairs):
                replay = list(
                    pool.map(r1._run_one, [(offset + 1, paths, cell_rows[0])], chunksize=1)
                )
                assert digest(replay) == digest(results[:1])
                expected["replays"][key] = digest(replay[0])
            save(RESULT, expected)
            print(
                json.dumps({"phase": "control", "pair": key, "games": len(expected["games"])}),
                flush=True,
            )
    assert (
        len(expected["games"]) == 4500
        and len(expected["cell_hashes"]) == 45
        and len(expected["replays"]) == 6
    )
    assert all(g["runtime_error"] is None and g["runtime_fingerprint"] for g in expected["games"])
    expected["status"] = "COMPLETE"
    save(RESULT, expected)
    print(json.dumps({"status": "COMPLETE", "games": 4500, "replay_cells": 6}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())