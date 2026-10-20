"""Run the single HQ-authorized Baseline 005 calibration control."""

from __future__ import annotations

import argparse
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
from artifact_integrity import (  # noqa: E402
    assert_new_control_classification,
    write_validated_artifact,
)
from objective_balance_lab_semantic_identity import identity  # noqa: E402

MANIFEST = OBL / "baselines/OBL_BASELINE_005_MANIFEST.json"
READINESS = ROOT / "docs/cardcade/ISSUE_289_MICHELANGELO_IMPROVISER_CALIBRATION_READINESS.json"
COUNTER_REPAIR = (
    ROOT / "docs/objective-balance-lab/BASELINE_005_COUNTER_ACTIVATION_PROVENANCE_REPAIR_001.json"
)
REPAIR = ROOT / "docs/objective-balance-lab/BASELINE_005_PLAYER_INDEX_REPAIR_001.json"
LTB_REPAIR = ROOT / "docs/objective-balance-lab/BASELINE_005_LTB_MUTAGEN_DEPARTURE_REPAIR_001.json"
RECOVERY = OBL / "BASELINE_005_ARTIFACT_RECOVERY_001.json"
LEDGER = ROOT / "docs/cardcade/ISSUE_289_COVERAGE_LEDGER.csv"
RESULT = OBL / "BASELINE_005_LTB_REPAIR_CONTROL_ATTEMPT_009.json.gz"
CONTROL_ID = "OBL-BASELINE-005-LTB-REPAIR-CONTROL-ATTEMPT-009"
RUNTIME = "defefdce8a716ceef6dcedad1a6f50e2abc367bd3cb772a369853506d2f5398d"
SCHEDULE_SHA = "b5fd8ab57016b15662fca420d508c9aab3633ad14b7f7515d667492b0f8abf27"
PRIOR_FAILED_CONTROL_SHA = "1f2442ad5c3f716913c4ee9c5dad84137b75232b15664745e2b722d8bef7a352"
PRIOR_REPAIRED_CONTROL_SHA = "45c4cdcd95708bb5974620b543fb50ee4dfb43b2a0d09c288e01ceb9dfeb15d7"
PRIOR_FOOD_SEARCH_CONTROL_SHA = "93ad17ed91bf5b7c1f0dd1c32414767f2a5a8ffe2806466ebb811fc06c1ab5e7"
PRIOR_ATTEMPT6_CONTROL_SHA = "6f950648b1edd20052bb30c0982faf9bb82a1a979fd69271d2b6a97b8eac169a"
PRIOR_ATTEMPT8_CONTROL_SHA = "3ac2dacfea88bddb0152ec90b394ac52157522f4149d7cf44c92cadef7b584e7"
REGISTRY = OBL / "BASELINE_005_HISTORICAL_FAILURE_REGISTRY_001.json"
STABILITY_GATE = OBL / "BASELINE_005_HISTORICAL_REGRESSION_STABILITY_GATE_001.json"


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()


def schedule_digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path: Path, payload: dict, expected_manifest: dict | None = None) -> None:
    assert_new_control_classification(payload)
    write_validated_artifact(
        path,
        payload,
        expected_manifest=expected_manifest
        or {
            key: payload[key]
            for key in ("schema", "evidence_id", "semantic_runtime_sha256", "schedule_sha256")
            if key in payload
        },
    )


def replay_historical_failures(
    paths: dict[str, str], cards: dict[str, dict[str, object]], registry: dict
) -> list[dict]:
    """Replay every preserved failure seed before permitting a new control."""
    r1._init_worker(cards)
    results = []
    for index, row in enumerate(registry["entries"], 1):
        item = {
            "pair": row["seats"],
            "decks": row["seats"],
            "orientation": row["orientation"],
            "block": index,
            "seed": int(row["seed"]),
            "pair_index": index,
        }
        first = r1._run_one((100000 + index, paths, item))
        replay = r1._run_one((200000 + index, paths, item))
        if first.get("runtime_error") or replay.get("runtime_error"):
            raise RuntimeError(f"historical replay failed for seed {row['seed']}")
        first_digest = digest(first)
        replay_digest = digest(replay)
        if first_digest != replay_digest:
            raise RuntimeError(f"historical replay mismatch for seed {row['seed']}")
        # Historical digests were produced under predecessor repair runtimes.  The
        # gate requires deterministic completion under the current runtime; it does
        # not pretend a semantic repair preserves predecessor byte-for-byte output.
        results.append({"seed": row["seed"], "deterministic": True, "digest": first_digest})
    return results


def preflight() -> tuple[dict, list[dict], dict[str, str], dict]:
    assert not RESULT.exists(), f"refusing to overwrite existing control: {RESULT}"
    manifest = json.loads(MANIFEST.read_text())
    readiness = json.loads(READINESS.read_text())
    repair = json.loads(REPAIR.read_text())
    counter_repair = json.loads(COUNTER_REPAIR.read_text())
    ltb_repair = json.loads(LTB_REPAIR.read_text())
    recovery = json.loads(RECOVERY.read_text())
    assert identity()["aggregate_semantic_runtime_sha256"] == RUNTIME
    # The final coverage/readiness ledger predates the provenance repair.  Its
    # zero-gap result is retained as semantic evidence, while the repair report
    # authenticates the runtime actually used by this control.
    assert readiness["semantic_runtime_sha256"] != RUNTIME
    assert readiness["calibration_readiness"] == "READY"
    assert readiness["critical_remaining"] == readiness["important_remaining"] == 0
    assert readiness["unbounded_residual_important"] == 0
    assert repair["status"] == "READY_REPAIR_BLOCKED_CALIBRATION"
    assert ltb_repair["runtime_after_sha256"] == RUNTIME
    assert ltb_repair["preservation"]["coverage_ledger_rows"] == 172
    assert counter_repair["attempt6_artifact_sha256"] == PRIOR_ATTEMPT6_CONTROL_SHA
    assert (
        sha(OBL / "BASELINE_005_ISSUE289_FOOD_SEARCH_CONTROL_ATTEMPT_005.json.gz")
        == PRIOR_FOOD_SEARCH_CONTROL_SHA
    )
    assert (
        sha(OBL / "BASELINE_005_ISSUE289_DAMAGE_TARGET_CONTROL_ATTEMPT_006.json.gz")
        == PRIOR_ATTEMPT6_CONTROL_SHA
    )
    registry = json.loads(REGISTRY.read_text())
    assert registry["runtime"] == RUNTIME and len(registry["entries"]) == 11
    gate = json.loads(STABILITY_GATE.read_text())
    assert gate["status"] == "READY_STABILITY_BLOCKED_CALIBRATION"
    assert gate["registry"]["entries"] == 7 and gate["registry"]["exceptions"] == 0
    assert (
        sha(OBL / "BASELINE_005_TELEMETRY_CONTROL_ATTEMPT_008.json.gz")
        == PRIOR_ATTEMPT8_CONTROL_SHA
    )
    assert recovery["hq_governance_decision"]["classification"] == "HISTORICAL_CORRUPT_EXCLUDED"
    failed = OBL / "BASELINE_005_ISSUE289_FINAL_CONTROL.json.gz"
    assert sha(failed) == PRIOR_FAILED_CONTROL_SHA
    excluded = {row["control_id"]: row for row in recovery["artifacts"]}
    assert set(excluded) == {
        "OBL-BASELINE-005-REPAIRED-CONTROL-001",
        "OBL-BASELINE-005-REPAIRED-PILOT-CONTROL-001",
    }
    for row in excluded.values():
        path = ROOT / row["path"]
        assert row["historical_classification"] == "HISTORICAL_CORRUPT_EXCLUDED"
        assert sha(path) == row["current_sha256"]
        assert row["current_sha256"] != row["recorded_sha256"]
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
    historical_replays = replay_historical_failures(paths, cards, registry)
    return manifest, schedule, paths, recovery, historical_replays


def main() -> int:
    global RESULT, CONTROL_ID
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--output", help="new control artifact filename under the OBL directory")
    parser.add_argument("--control-id", help="new unique control evidence ID")
    args = parser.parse_args()
    if args.output:
        output = Path(args.output)
        assert not output.is_absolute() and output.name == args.output
        RESULT = OBL / output
    if args.control_id:
        CONTROL_ID = args.control_id
    manifest, schedule, paths, recovery, historical_replays = preflight()
    if not args.run:
        print(
            json.dumps({"status": "PREFLIGHT_PASS", "games": 4500, "cells": 45, "runtime": RUNTIME})
        )
        return 0
    expected = {
        "schema": "obl-baseline005-historical-stability-control-attempt-v1",
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
        "prior_food_search_control_id": "OBL-BASELINE-005-FOOD-SEARCH-CONTROL-ATTEMPT-005",
        "prior_food_search_control_sha256": PRIOR_FOOD_SEARCH_CONTROL_SHA,
        "prior_attempt6_control_id": "OBL-BASELINE-005-DAMAGE-TARGET-CONTROL-ATTEMPT-006",
        "prior_attempt6_control_sha256": PRIOR_ATTEMPT6_CONTROL_SHA,
        "prior_attempt8_control_id": "OBL-BASELINE-005-TELEMETRY-CONTROL-ATTEMPT-008",
        "prior_attempt8_control_sha256": PRIOR_ATTEMPT8_CONTROL_SHA,
        "prior_repaired_pilot_control_id": "OBL-BASELINE-005-REPAIRED-PILOT-CONTROL-001",
        "prior_repaired_pilot_control_sha256": recovery["artifacts"][1]["recorded_sha256"],
        "historical_corrupt_excluded": [
            "OBL-BASELINE-005-REPAIRED-CONTROL-001",
            "OBL-BASELINE-005-REPAIRED-PILOT-CONTROL-001",
        ],
        "repair_diagnostics_excluded": True,
        "historical_failure_replays": historical_replays,
    }
    artifact_manifest = {
        "schema": expected["schema"],
        "evidence_id": CONTROL_ID,
        "semantic_runtime_sha256": RUNTIME,
        "schedule_sha256": SCHEDULE_SHA,
        "required_games": 4500,
        "baseline_manifest_sha256": sha(MANIFEST),
        "baseline_decks": manifest["decks"],
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
                save(RESULT, expected, artifact_manifest)
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
            save(RESULT, expected, artifact_manifest)
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
    save(RESULT, expected, artifact_manifest)
    print(json.dumps({"status": "COMPLETE", "games": 4500, "replay_cells": 6}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
