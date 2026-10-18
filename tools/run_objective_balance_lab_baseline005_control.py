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
REPAIR = ROOT / "docs/cardcade/ISSUE_289_DAMAGE_MANA_PROVENANCE_REPAIR.json"
PILOT_REPAIR = ROOT / "docs/cardcade/ISSUE_289_PILOT_NONE_T_REPAIR.json"
LEDGER = ROOT / "docs/cardcade/ISSUE_289_COVERAGE_LEDGER.csv"
RESULT = OBL / "BASELINE_005_ISSUE289_REPAIRED_PILOT_CONTROL.json.gz"
CONTROL_ID = "OBL-BASELINE-005-REPAIRED-PILOT-CONTROL-001"
RUNTIME = "dc80bc679e2c0d118f543d12ae4a95661033039058b1525f32e8d076dae8d308"
SCHEDULE_SHA = "b5fd8ab57016b15662fca420d508c9aab3633ad14b7f7515d667492b0f8abf27"
PRIOR_FAILED_CONTROL_SHA = "1f2442ad5c3f716913c4ee9c5dad84137b75232b15664745e2b722d8bef7a352"
PRIOR_REPAIRED_CONTROL_SHA = "45c4cdcd95708bb5974620b543fb50ee4dfb43b2a0d09c288e01ceb9dfeb15d7"


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
    repair = json.loads(REPAIR.read_text())
    pilot_repair = json.loads(PILOT_REPAIR.read_text())
    assert identity()["aggregate_semantic_runtime_sha256"] == RUNTIME
    # The final coverage/readiness ledger predates the provenance repair.  Its
    # zero-gap result is retained as semantic evidence, while the repair report
    # authenticates the runtime actually used by this control.
    assert readiness["semantic_runtime_sha256"] != RUNTIME
    assert readiness["calibration_readiness"] == "READY"
    assert readiness["critical_remaining"] == readiness["important_remaining"] == 0
    assert readiness["unbounded_residual_important"] == 0
    assert repair["status"] == "READY_REPAIR_BLOCKED_CALIBRATION"
    assert repair["repaired_runtime_sha256"] == "a86708257c54495cb3d3a71c578b86f41931184542542bbe676dacb924b1d401"
    assert repair["previous_control_id"] == "OBL-BASELINE-005-FINAL-CONTROL-001"
    assert repair["previous_control_artifact_sha256"] == PRIOR_FAILED_CONTROL_SHA
    failed = OBL / "BASELINE_005_ISSUE289_FINAL_CONTROL.json.gz"
    assert sha(failed) == PRIOR_FAILED_CONTROL_SHA
    assert pilot_repair["status"] == "READY_REPAIR_BLOCKED_CALIBRATION"
    assert pilot_repair["repaired_runtime_sha256"] == RUNTIME
    assert pilot_repair["previous_control_id"] == "OBL-BASELINE-005-REPAIRED-CONTROL-001"
    assert pilot_repair["previous_control_artifact_sha256"] == PRIOR_REPAIRED_CONTROL_SHA
    previous_repaired = OBL / "BASELINE_005_ISSUE289_REPAIRED_CONTROL.json.gz"
    assert sha(previous_repaired) == PRIOR_REPAIRED_CONTROL_SHA
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
        "schema": "obl-baseline005-repaired-pilot-control-v1",
        "environment_id": "OBL-BASELINE-005",
        "evidence_id": CONTROL_ID,
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
        "prior_failed_control_id": "OBL-BASELINE-005-FINAL-CONTROL-001",
        "prior_failed_control_sha256": PRIOR_FAILED_CONTROL_SHA,
        "prior_repaired_control_id": "OBL-BASELINE-005-REPAIRED-CONTROL-001",
        "prior_repaired_control_sha256": PRIOR_REPAIRED_CONTROL_SHA,
        "repair_diagnostics_excluded": True,
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
