"""Disposable synthetic persistence-only profiling; no executor/game imports.

Run with Python -P -s -B, --parent an existing disposable directory and --records.
Never reads a historical checkpoint. Output is reserved exclusively and retained.
"""

from __future__ import annotations

import argparse
import ctypes
import gc
import json
import os
import sys
import time
from ctypes import wintypes
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tmnt_design_studio.calibration_integrity import (  # noqa: E402
    CheckpointAccumulator,
    WriterLock,
)
from tmnt_design_studio.fresh900 import (  # noqa: E402
    MEMORY_GATE,
    atomic_json,
    check_resources,
    validate_final_checkpoint,
)
from tmnt_design_studio.fresh900_identity import digest, file_hash, plain, require  # noqa: E402


class Counters(ctypes.Structure):
    _fields_ = [("cb", wintypes.DWORD), ("faults", wintypes.DWORD)] + [
        (name, ctypes.c_size_t)
        for name in (
            "peak_working_set",
            "working_set",
            "peak_paged",
            "paged",
            "peak_nonpaged",
            "nonpaged",
            "pagefile",
            "peak_private_commit",
            "private_commit",
        )
    ]


def memory():
    api = ctypes.WinDLL("psapi", use_last_error=True).GetProcessMemoryInfo
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    api.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    api.restype = wintypes.BOOL
    value = Counters()
    value.cb = ctypes.sizeof(value)
    if not api(kernel.GetCurrentProcess(), ctypes.byref(value), value.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    return {
        name: int(getattr(value, name))
        for name in ("working_set", "peak_working_set", "private_commit", "peak_private_commit")
    }


def fixture(index, target):
    # Historical *aggregate* densities only. Unique strings/dicts avoid a
    # misleading shared-template heap. Values carry no historical game content.
    row = dict(
        game_id=f"synthetic-{index}",
        pairing_id="synthetic-cell",
        orientation="candidate_first" if index % 2 == 0 else "opponent_first",
        seed=index,
    )
    record = dict(
        game_id=row["game_id"],
        synthetic=True,
        events=[
            dict(event_id=f"e-{index}-{i}", kind="SYNTHETIC", detail=f"{index}:{i}".ljust(350, "x"))
            for i in range(817)
        ],
        stage002_presence=[
            dict(
                object_id=f"p-{index}-{i}", state="SYNTHETIC", detail=f"{index}:{i}".ljust(200, "x")
            )
            for i in range(255)
        ],
        rules_event_evidence=[
            dict(event_id=f"r-{index}-{i}", kind="SYNTHETIC", detail=f"{index}:{i}".ljust(200, "x"))
            for i in range(58)
        ],
        padding="",
    )
    size = len(json.dumps({"records": [record]}, sort_keys=True, indent=2).encode())
    record["padding"] = "SYNTHETIC-" + "z" * max(0, target - size - 10)
    return row, record


def nested_fixture(index, target):
    """Independent audit's nested topology, no real game telemetry or imports."""
    events = [
        dict(
            id=f"{index}:event:{n}",
            kind="SYNTHETIC",
            context=dict(turn=n // 50, player=n % 2, stage=f"audit-{index}-{n}"),
            detail=f"{index}:{n}:" + "e" * 180,
        )
        for n in range(817)
    ]
    presence = [
        dict(
            object_id=f"{index}:object:{n}",
            metadata=dict(name=f"fixture-{n}", states=[f"{index}-{n}-A", f"{index}-{n}-B"]),
        )
        for n in range(255)
    ]
    rules = [
        dict(
            id=f"{index}:rule:{n}",
            targets=[dict(id=f"{index}-{n}-target", zone="fixture")],
            effect=dict(name="SYNTHETIC", value=n),
        )
        for n in range(58)
    ]
    record = dict(
        game_id=f"audit-{index}",
        synthetic=True,
        events=events,
        stage002_presence=presence,
        rules_event_evidence=rules,
        padding="",
    )
    size = len(json.dumps({"records": [record]}, sort_keys=True, indent=2).encode())
    record["padding"] = "fixture:" + "z" * max(0, target - size - 8)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", type=Path, required=True)
    parser.add_argument("--records", type=int, default=900)
    parser.add_argument("--bytes-per-record", type=int, default=969401)
    parser.add_argument("--shape", choices=("nested", "flat"), default="nested")
    args = parser.parse_args()
    require(os.name == "nt", "Windows profiling only")
    require(
        2 <= args.records <= 900
        and args.records % 2 == 0
        and 600_000 <= args.bytes_per_record <= 3_000_000,
        "bounded synthetic fixture required",
    )
    parent = plain(args.parent)
    before = check_resources(parent)
    root = parent / (
        "FRESH900_SYNTHETIC_" + time.strftime("%Y%m%dT%H%M%S") + "_" + str(os.getpid())
    )
    root.mkdir()
    report = dict(
        synthetic=True,
        games_executed=0,
        production_checkpoint_accessed=False,
        python=sys.version,
        executable=sys.executable,
        resources_before=before,
        records=args.records,
        target_bytes_per_record=args.bytes_per_record,
        shape=args.shape,
        baseline=memory(),
        source_file_sha256=file_hash(Path(__file__)),
        component_sha256={
            name: file_hash(ROOT / name)
            for name in (
                "src/tmnt_design_studio/calibration_integrity.py",
                "src/tmnt_design_studio/fresh900.py",
                "src/tmnt_design_studio/fresh900_identity.py",
            )
        },
    )
    rows = [
        dict(
            game_id=f"audit-{i}" if args.shape == "nested" else f"synthetic-{i}",
            pairing_id="synthetic-cell",
            seed=i,
            orientation="candidate_first" if i % 2 == 0 else "opponent_first",
        )
        for i in range(args.records)
    ]
    acc = CheckpointAccumulator(rows, writer_id="synthetic-profiler")
    expected_records = {}
    samples = []
    checkpoint = root / "synthetic-checkpoint.json"
    ownership = WriterLock(checkpoint, "synthetic-profiler")
    ownership.acquire()
    points = {args.records // 4, args.records // 2, args.records}
    for index in range(args.records):
        if args.shape == "nested":
            record = nested_fixture(index, args.bytes_per_record)
        else:
            _, record = fixture(index, args.bytes_per_record)
        expected_records[record["game_id"]] = digest(record)
        acc.append(record, writer_id="synthetic-profiler")
        if index + 1 in points:
            start = time.perf_counter()
            written = acc.write(
                checkpoint, writer_id="synthetic-profiler", return_snapshot=False, verify_bytes=True
            )
            elapsed = time.perf_counter() - start
            status_start = time.perf_counter()
            require(file_hash(checkpoint) == written["checkpoint_sha256"], "changed before status")
            status_hash_seconds = time.perf_counter() - status_start
            publish_start = time.perf_counter()
            atomic_json(
                root / "profile-status.json",
                dict(
                    synthetic=True,
                    completed_games=index + 1,
                    checkpoint_sha256=written["checkpoint_sha256"],
                ),
            )
            samples.append(
                dict(
                    records=index + 1,
                    write_verified_seconds=elapsed,
                    bytes=written["checkpoint_bytes"],
                    timings=written["timings"],
                    status_hash_seconds=status_hash_seconds,
                    status_publish_seconds=time.perf_counter() - publish_start,
                    memory=memory(),
                )
            )
    del record
    gc.collect()
    report["retained"] = memory()
    report["samples"] = samples
    report["after_write"] = memory()
    report["checkpoint_bytes"] = checkpoint.stat().st_size
    report["checkpoint_sha256"] = written["checkpoint_sha256"]
    del acc
    gc.collect()
    start = time.perf_counter()
    verified = validate_final_checkpoint(
        checkpoint, rows, expected_records, written["checkpoint_sha256"]
    )
    report["final_validation_seconds"] = time.perf_counter() - start
    report["after_final_validation"] = memory()
    release_start = time.perf_counter()
    ownership.release()
    report["release_seconds"] = time.perf_counter() - release_start
    report["resources_after"] = check_resources(parent)
    report["verified_records"] = verified["completed_games"]
    report["checkpoint_hash_unchanged"] = file_hash(checkpoint) == report["checkpoint_sha256"]
    report["after_complete_path"] = memory()
    report["peak_comparison_threshold_bytes"] = MEMORY_GATE
    peak = report["after_complete_path"]
    report["threshold_exceeded"] = (
        peak["peak_private_commit"] > MEMORY_GATE or peak["peak_working_set"] > MEMORY_GATE
    )
    report["recommendation"] = (
        "BLOCKED" if report["threshold_exceeded"] else "WITHIN_MEASURED_THRESHOLD"
    )
    if args.records == 900:
        last = samples[-1]
        report["projected_900_checkpoint_write_bytes"] = last["bytes"] * 901 / 2
        report["projected_900_checkpoint_read_bytes"] = last["bytes"] * 901
        per_write = (
            last["write_verified_seconds"]
            + last["status_hash_seconds"]
            + last["status_publish_seconds"]
        )
        report["projected_persistence_seconds"] = (
            per_write * 901 / 2 + report["final_validation_seconds"]
        )
    report["ownership_unresolved"] = ownership._held
    destination = root / "report.json"
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if report["threshold_exceeded"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
