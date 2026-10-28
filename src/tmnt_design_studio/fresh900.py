"""Fresh-only, disposable review runner. No live executor or resume is shipped."""

from __future__ import annotations

import copy
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
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(encoded(value))
            stream.flush()
            os.fsync(stream.fileno())
        plain(path)
        _replace_with_retry(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


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
    verify_plan(plan)
    initial_resources = check_resources(root.parent, measure)
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
    try:
        with WriterLock(checkpoint, run_id):
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
                atomic_json(
                    root / "telemetry/status.json",
                    dict(
                        protocol=PROTOCOL,
                        run_id=run_id,
                        synthetic=True,
                        state=state,
                        committed_games=committed,
                        checkpoint_sha256=file_hash(checkpoint),
                        heartbeat=time.time(),
                        stage=stage,
                    ),
                )

            stage = "INITIAL_CHECKPOINT"
            accumulator.write(checkpoint, writer_id=run_id, return_snapshot=False)
            publish("RUNNING")
            for row in plan["schedule"]:
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
                require(result.get("synthetic") is True, "synthetic records required")
                require(result.get("game_id") == row["game_id"], "wrong result ID")
                require(result.get("terminal") is True, "incomplete result")
                require(result.get("winner") in row["seats"], "unexplained/no winner")
                require(
                    type(result.get("turn")) is int and 0 < result["turn"] <= 120, "invalid turn"
                )
                require(result.get("invariant_violations") == [], "invariant failure")
                require(result.get("stop_records") == [], "stopped/unsupported result")
                require(
                    all(
                        isinstance(result.get(key), list)
                        for key in ("events", "stage002_presence", "rules_event_evidence")
                    ),
                    "detailed evidence missing",
                )
                result = {
                    **result,
                    "fresh_run_id": run_id,
                    "schedule_row": row,
                    "plan_sha256": digest(plan),
                }
                accumulator.append(result, writer_id=run_id)
                stage = "CHECKPOINT"
                guard()
                accumulator.write(checkpoint, writer_id=run_id, return_snapshot=False)
                committed += 1
                stage = "INTEGRITY"
                atomic_json(
                    root / "integrity/committed.json",
                    dict(
                        completed_games=committed,
                        checkpoint_sha256=file_hash(checkpoint),
                        plan_sha256=digest(plan),
                        synthetic=True,
                    ),
                )
                stage = "STATUS"
                publish("RUNNING")
            accumulator.assert_complete()
            stage = "FINAL"
            # Verify the final persisted envelope, not only the in-memory count.
            from tmnt_design_studio.calibration_integrity import validate_checkpoint

            with checkpoint.open(encoding="utf-8") as stream:
                validate_checkpoint(json.load(stream), plan["schedule"])
            final = dict(
                completed_games=committed,
                checkpoint_sha256=file_hash(checkpoint),
                plan_sha256=digest(plan),
                synthetic=True,
            )
            atomic_json(root / "results/summary.json", final)
            publish("COMPLETE")
            return final
    except BaseException as error:
        # Checkpoint may have advanced immediately before a later publication
        # failed. Never restore old bytes or automatically replay after a stop.
        failure = dict(
            stage=stage,
            last_observed_committed=committed,
            error_type=type(error).__name__,
            error=str(error),
            errno=getattr(error, "errno", None),
            winerror=getattr(error, "winerror", None),
            synthetic=True,
            recovery="STOPPED_REVIEW_REQUIRED",
        )
        try:
            guard()
            atomic_json(root / "failures/stop.json", failure)
        except BaseException as logging_error:
            print(f"Fresh900 stop: {failure!r}; logging failed: {logging_error!r}", file=sys.stderr)
        raise
