"""Fresh-only, disposable review runner. No live executor or resume is shipped."""

from __future__ import annotations

import copy
import gc
import json
import os
import re
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

from tmnt_design_studio.calibration_integrity import (
    CheckpointAccumulator,
    WriterLock,
    _replace_with_retry,
    note_cleanup,
)
from tmnt_design_studio.fresh900_identity import (
    digest,
    disjoint,
    encoded,
    file_hash,
    plain,
    require,
    verify_plan,
)

MEMORY_GATE = 2_997_492_240
DISK_RESERVE = 20 * 2**30
PROTOCOL = "fresh900-status-v1"


def resources() -> dict[str, int]:
    """Windows physical/commit counters; fail closed on unsupported hosts."""
    require(os.name == "nt", "Windows resource provider required")
    import ctypes
    from ctypes import wintypes

    class Info(ctypes.Structure):
        _fields_ = (
            [("cb", wintypes.DWORD)]
            + [
                (name, ctypes.c_size_t)
                for name in (
                    "CommitTotal",
                    "CommitLimit",
                    "CommitPeak",
                    "PhysicalTotal",
                    "PhysicalAvailable",
                    "SystemCache",
                    "KernelTotal",
                    "KernelPaged",
                    "KernelNonpaged",
                    "PageSize",
                )
            ]
            + [(name, wintypes.DWORD) for name in ("HandleCount", "ProcessCount", "ThreadCount")]
        )

    value = Info()
    value.cb = ctypes.sizeof(value)
    api = ctypes.WinDLL("psapi", use_last_error=True).GetPerformanceInfo
    api.argtypes = [ctypes.POINTER(Info), wintypes.DWORD]
    api.restype = wintypes.BOOL
    if not api(ctypes.byref(value), value.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    return dict(
        physical=value.PhysicalAvailable * value.PageSize,
        commit=(value.CommitLimit - value.CommitTotal) * value.PageSize,
    )


def check_resources(parent: Path, measure: Callable = resources) -> dict:
    import shutil

    sample = measure()
    require(sample["physical"] >= MEMORY_GATE, "physical memory gate")
    require(sample["commit"] >= MEMORY_GATE, "system commit gate")
    disk = shutil.disk_usage(parent).free
    require(disk >= DISK_RESERVE, "insufficient evidence disk reserve")
    return {**sample, "disk_free": disk, "memory_gate": MEMORY_GATE}


def atomic_json(path: Path, value: dict) -> None:
    """Small control/telemetry publication. Failure never affects checkpoint bytes."""
    plain(path)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    failure = None
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(encoded(value))
            stream.flush()
            os.fsync(stream.fileno())
        plain(path)
        _replace_with_retry(temporary, path)
    except BaseException as error:
        failure = error
        raise
    finally:
        try:
            if os.path.exists(temporary):
                os.unlink(temporary)
        except BaseException as cleanup:
            if failure is None:
                raise
            note_cleanup(failure, cleanup, "TEMPORARY_CLEANUP", temporary)


def validate_result(result: dict, row: dict, index: int, plan: dict, plan_hash: str) -> None:
    """Validate redundant identity before adding derived fields, never repair it."""
    require(isinstance(result, dict), "result object required")
    require(result.get("synthetic") is True, "synthetic records required")
    require(result.get("game_id") == row["game_id"], "wrong result ID")
    require(result.get("terminal") is True, "incomplete result")
    require(result.get("winner") in row["seats"], "unexplained/no winner")
    require(type(result.get("turn")) is int and 0 < result["turn"] <= 120, "invalid turn")
    require(result.get("invariant_violations") == [], "invariant failure")
    require(result.get("stop_records") == [], "stopped/unsupported result")
    require(
        all(
            isinstance(result.get(key), list)
            for key in ("events", "stage002_presence", "rules_event_evidence")
        ),
        "detailed evidence missing",
    )
    for event in result["events"]:
        require(isinstance(event, dict), "invalid event evidence")
        require(
            event.get("event", event.get("kind")) != "acceptance_incomplete",
            "incomplete event contradicts terminal result",
        )
    require(
        all(
            isinstance(entry, dict)
            for key in ("stage002_presence", "rules_event_evidence")
            for entry in result[key]
        ),
        "invalid detailed evidence entry",
    )
    authoritative = {
        **row,
        "run_id": plan["run_id"],
        "terminal": True,
        "winner": result["winner"],
        "turn": result["turn"],
        "synthetic": True,
        "participants": row["seats"],
        "schedule_index": index,
        "schedule_position": index + 1,
        "fresh_run_id": plan["run_id"],
        "schedule_row": row,
        "plan_sha256": plan_hash,
        "turns_started": result["turn"],
        "winner_index": row["seats"].index(result["winner"]),
        "loser": next(seat for seat in row["seats"] if seat != result["winner"]),
        "draw": False,
        "terminal_state": "COMPLETE",
        "source_commit": plan["runtime"].get("source_commit"),
        "runtime_sha256": digest(plan["runtime"]),
        "inputs_sha256": digest(plan["inputs"]),
        "completed_games": index + 1,
        "schedule_games": len(plan["schedule"]),
    }
    for key, expected in authoritative.items():
        if key in result:
            require(encoded(result[key]) == encoded(expected), f"conflicting result {key}")
    if "players" in result:
        players = result["players"]
        require(
            isinstance(players, list) and all(isinstance(p, dict) for p in players),
            "invalid participant states",
        )
        require([p.get("name") for p in players] == row["seats"], "conflicting participants")
    for field in ("metadata", "identity"):
        if field in result:
            metadata = result[field]
            require(isinstance(metadata, dict), "invalid identity metadata")
            for key, value in metadata.items():
                require(key in authoritative, f"unclassified identity metadata: {key}")
                require(encoded(value) == encoded(authoritative[key]), f"conflicting {field}.{key}")
    encoded(result)  # Reject non-JSON/NaN/cyclic values before persistence.


def validate_final_checkpoint(
    path: Path,
    schedule: list[dict],
    expected_records: dict[str, str],
    expected_file: str,
) -> dict:
    """Read-back after caller releases its accumulator; bind bytes AND content."""
    from tmnt_design_studio.calibration_integrity import validate_checkpoint

    path = plain(path)
    before = path.stat()
    require(file_hash(path) == expected_file, "final checkpoint byte identity mismatch")
    with path.open(encoding="utf-8") as stream:
        payload = json.load(stream)
    validate_checkpoint(payload, schedule)
    require(payload["completed_games"] == len(schedule), "incomplete final checkpoint")
    ids = [row["game_id"] for row in schedule]
    require(list(expected_records) == ids, "expected record coverage/order mismatch")
    for row, record in zip(schedule, payload["records"], strict=True):
        require(record["game_id"] == row["game_id"], "final schedule order mismatch")
        require(
            digest(record) == expected_records[row["game_id"]],
            "final checkpoint record content mismatch",
        )
    require(file_hash(path) == expected_file, "checkpoint changed during final validation")
    after = plain(path).stat()
    require(
        (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
        == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns),
        "checkpoint object changed during validation",
    )
    return dict(
        completed_games=len(schedule),
        checkpoint_sha256=expected_file,
        checkpoint_bytes=after.st_size,
        synthetic=True,
    )


def run_synthetic(
    plan: dict,
    authorization: dict,
    *,
    expected_authorization_sha256: str,
    executor: Callable[[dict], dict],
    measure: Callable = resources,
) -> dict:
    """Explicit synthetic seam only. Cannot select a live adapter or recover a run.

    The caller's independently pinned approval digest is governance evidence,
    not a same-user tamper-proof cryptographic issuer or a resume capability.
    """
    plan = copy.deepcopy(plan)
    authorization = copy.deepcopy(authorization)
    require(digest(authorization) == expected_authorization_sha256, "approval bytes mismatch")
    require(authorization.get("action") == "synthetic-review", "live execution not implemented")
    require(authorization.get("approved_by"), "explicit external approval required")
    require(authorization.get("plan_sha256") == digest(plan), "wrong approved plan")
    run_id = plan["run_id"]
    require(bool(re.fullmatch(r"FRESH_900_[A-Za-z0-9_-]{8,96}", run_id)), "invalid run ID")
    root = plain(Path(plan["output"]))
    require(root.name == run_id, "run directory differs from ID")
    require(root.parent.is_dir(), "existing output parent required")
    for protected in [plan["runtime"]["source"], *plan["protected"]]:
        require(disjoint(root, plain(Path(protected))), "protected/output overlap")
    require(plan["protected"], "protected roots required")
    require(not root.exists(), "unused run root required; no resume")
    parent_info = root.parent.stat()
    verify_plan(plan)
    initial_resources = check_resources(root.parent, measure)
    require(
        plain(root) == root
        and (root.parent.stat().st_dev, root.parent.stat().st_ino)
        == (parent_info.st_dev, parent_info.st_ino),
        "reservation parent changed",
    )
    # mkdir itself is the exclusive run-ID reservation. Never reuse it on error.
    root.mkdir()
    for directory in (
        "inputs",
        "runtime",
        "control",
        "checkpoints",
        "telemetry",
        "integrity",
        "logs",
        "failures",
        "results",
    ):
        (root / directory).mkdir()
    directories = {p: (p.stat().st_dev, p.stat().st_ino) for p in [root, *root.iterdir()]}

    def guard():
        require(plain(root) == root, "run path changed")
        for protected in [plan["runtime"]["source"], *plan["protected"]]:
            require(disjoint(root, Path(protected)), "protected/output overlap")
        for path, identity in directories.items():
            require(
                (plain(path).stat().st_dev, path.stat().st_ino) == identity,
                "run directory replaced",
            )
        for directory in directories:
            for path in directory.iterdir():
                plain(path)

    checkpoint = root / "checkpoints/checkpoint.json"
    stage = "INITIALIZING"
    committed = 0
    plan_hash = digest(plan)
    expected_records = {}
    expected_file = None
    ownership = WriterLock(checkpoint, run_id)
    try:
        with ownership:
            guard()
            # Materialize immutable, exact approved bytes with their input hashes.
            for index, (name, expected) in enumerate(plan["inputs"].items()):
                source = plain(Path(name))
                require(file_hash(source) == expected, "input changed during reservation")
                destination = root / "inputs" / f"{index:02d}-{source.name}"
                with destination.open("xb") as stream:
                    with source.open("rb") as original:
                        import shutil

                        shutil.copyfileobj(original, stream)
                    stream.flush()
                    os.fsync(stream.fileno())
                require(file_hash(destination) == expected, "input copy mismatch")
            atomic_json(root / "inputs/manifest.json", plan)
            atomic_json(root / "inputs/schedule.json", {"schedule": plan["schedule"]})
            atomic_json(root / "runtime/manifest.json", plan["runtime"])
            atomic_json(root / "control/launch-authorization.json", authorization)
            atomic_json(root / "logs/preflight.json", initial_resources)
            accumulator = CheckpointAccumulator(plan["schedule"], writer_id=run_id)

            def publish(state: str):
                guard()
                require(file_hash(checkpoint) == expected_file, "checkpoint changed before status")
                atomic_json(
                    root / "telemetry/status.json",
                    dict(
                        protocol=PROTOCOL,
                        run_id=run_id,
                        synthetic=True,
                        state=state,
                        committed_games=committed,
                        checkpoint_sha256=expected_file,
                        heartbeat=time.time(),
                        stage=stage,
                    ),
                )

            stage = "INITIAL_CHECKPOINT"
            written = accumulator.write(
                checkpoint,
                writer_id=run_id,
                return_snapshot=False,
                verify_bytes=True,
                before_create=guard,
                before_replace=guard,
            )
            expected_file = written["checkpoint_sha256"]
            publish("RUNNING")
            for index, row in enumerate(plan["schedule"]):
                guard()
                stage = "PREFLIGHT"
                check_resources(root, measure)
                # Full identity verification at every dispatch intentionally trades
                # I/O for review simplicity; measure its cost before deployment.
                verify_plan(plan)
                stage = "EXECUTOR"
                atomic_json(
                    root / "telemetry/heartbeat.json",
                    dict(
                        protocol=PROTOCOL,
                        run_id=run_id,
                        heartbeat=time.time(),
                        committed_games=committed,
                        stage=stage,
                        synthetic=True,
                    ),
                )
                result = executor(copy.deepcopy(row))
                stage = "RESULT_VALIDATION"
                try:
                    validate_result(result, row, index, plan, plan_hash)
                except BaseException as primary:
                    try:
                        guard()
                        atomic_json(
                            root / "failures/rejected-record.json",
                            dict(record=result, error=str(primary), stage=stage),
                        )
                    except BaseException as cleanup:
                        note_cleanup(
                            primary, cleanup, "REJECTED_RECORD_LOG", str(root / "failures")
                        )
                    raise
                result = {
                    **result,
                    "fresh_run_id": run_id,
                    "schedule_row": row,
                    "plan_sha256": plan_hash,
                }
                expected_records[row["game_id"]] = digest(result)
                accumulator.append(result, writer_id=run_id)
                stage = "CHECKPOINT"
                guard()
                written = accumulator.write(
                    checkpoint,
                    writer_id=run_id,
                    return_snapshot=False,
                    verify_bytes=True,
                    before_create=guard,
                    before_replace=guard,
                )
                expected_file = written["checkpoint_sha256"]
                committed += 1
                stage = "INTEGRITY"
                atomic_json(
                    root / "integrity/committed.json",
                    dict(
                        completed_games=committed,
                        checkpoint_sha256=expected_file,
                        plan_sha256=plan_hash,
                        synthetic=True,
                    ),
                )
                stage = "STATUS"
                publish("RUNNING")
            accumulator.assert_complete()
            stage = "FINAL"
            del accumulator, result
            gc.collect()
            guard()
            final = validate_final_checkpoint(
                checkpoint, plan["schedule"], expected_records, expected_file
            )
            final.update(plan_sha256=plan_hash, operation_state="VERIFIED_CHECKPOINT")
        # No COMPLETE publication or successful return until ownership release.
        stage = "FINAL_PUBLICATION"
        guard()
        atomic_json(root / "results/summary.json", final)
        publish("COMPLETE")
        return final
    except BaseException as error:
        # Checkpoint may have advanced immediately before a later publication
        # failed. Never restore old bytes or automatically replay after a stop.
        cleanup_failures = getattr(error, "cleanup_failures", [])
        if any(error is cleanup for cleanup in ownership.cleanup_failures):
            stage = "LOCK_RELEASE"
            if not any(error is cleanup for _, _, cleanup in cleanup_failures):
                note_cleanup(error, error, "LOCK_RELEASE", str(ownership.path))
                cleanup_failures = error.cleanup_failures
        integrity_verified = False
        try:
            guard()
            integrity_verified = (
                expected_file is not None and file_hash(checkpoint) == expected_file
            )
        except BaseException as diagnostic_error:
            note_cleanup(error, diagnostic_error, "CHECKPOINT_DIAGNOSTIC", str(checkpoint))
            cleanup_failures = getattr(error, "cleanup_failures", [])
        failure = dict(
            stage=stage,
            last_observed_committed=committed,
            error_type=type(error).__name__,
            error=str(error),
            errno=getattr(error, "errno", None),
            winerror=getattr(error, "winerror", None),
            synthetic=True,
            recovery="STOPPED_REVIEW_REQUIRED",
            operation_state="STOPPED_REVIEW_REQUIRED",
            checkpoint_integrity_verified=integrity_verified,
            ownership_unresolved=ownership._held,
            resources_unresolved=ownership._held or bool(cleanup_failures),
            cleanup_failures=[
                dict(
                    stage=where,
                    resource=resource,
                    error_type=type(cleanup).__name__,
                    error=str(cleanup),
                    errno=getattr(cleanup, "errno", None),
                    winerror=getattr(cleanup, "winerror", None),
                )
                for where, resource, cleanup in cleanup_failures
            ],
        )
        error.failure_report = failure
        try:
            guard()
            atomic_json(root / "failures/stop.json", failure)
        except BaseException as logging_error:
            failure["cleanup_failures"].append(
                dict(
                    stage="FAILURE_LOG_WRITE",
                    error_type=type(logging_error).__name__,
                    error=str(logging_error),
                    resource=str(root / "failures/stop.json"),
                )
            )
            failure["resources_unresolved"] = True
            try:
                print(json.dumps(failure, sort_keys=True), file=sys.stderr)
            except BaseException as stderr_error:
                note_cleanup(error, stderr_error, "FAILURE_STDERR", "stderr")
        raise
