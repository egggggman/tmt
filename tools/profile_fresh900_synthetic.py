"""Disposable synthetic persistence-only profiling; no executor/game imports.

Run with Python -I -B, --parent an existing disposable directory and --records.
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
    validate_checkpoint,
)
from tmnt_design_studio.fresh900 import check_resources  # noqa: E402
from tmnt_design_studio.fresh900_identity import file_hash, plain, require  # noqa: E402


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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", type=Path, required=True)
    parser.add_argument("--records", type=int, default=900)
    parser.add_argument("--bytes-per-record", type=int, default=969401)
    args = parser.parse_args()
    require(os.name == "nt", "Windows profiling only")
    require(
        1 <= args.records <= 900 and 600_000 <= args.bytes_per_record <= 3_000_000,
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
        baseline=memory(),
        source_file_sha256=file_hash(Path(__file__)),
    )
    rows = [fixture(i, args.bytes_per_record)[0] for i in range(args.records)]
    acc = CheckpointAccumulator(rows, writer_id="synthetic-profiler")
    for index in range(args.records):
        _, record = fixture(index, args.bytes_per_record)
        acc.append(record, writer_id="synthetic-profiler")
    del record
    gc.collect()
    report["retained"] = memory()
    checkpoint = root / "synthetic-checkpoint.json"
    start = time.monotonic()
    acc.write(checkpoint, writer_id="synthetic-profiler", return_snapshot=False)
    report["write_seconds"] = time.monotonic() - start
    report["after_write"] = memory()
    report["checkpoint_bytes"] = checkpoint.stat().st_size
    report["checkpoint_sha256"] = file_hash(checkpoint)
    del acc
    gc.collect()
    start = time.monotonic()
    with checkpoint.open(encoding="utf-8") as stream:
        payload = json.load(stream)
    validate_checkpoint(payload, rows)
    restored = CheckpointAccumulator(rows, writer_id="synthetic-profiler")
    restored.restore(payload, take_ownership=True)
    del payload
    gc.collect()
    report["restore_seconds"] = time.monotonic() - start
    report["after_restore"] = memory()
    report["resources_after"] = check_resources(parent)
    report["verified_records"] = len(restored.completed_ids)
    report["checkpoint_hash_unchanged"] = file_hash(checkpoint) == report["checkpoint_sha256"]
    destination = root / "report.json"
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
