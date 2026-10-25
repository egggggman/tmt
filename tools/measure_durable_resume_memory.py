"""Measure one mock-only resume write from a disposable copy of Durable 001."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from tmnt_design_studio.calibration_runner import run_checkpointed_schedule
from tools.run_bad_guys_initial_calibration import build_schedule

EXPECTED_SHA256 = "ab1ecf83c6acbaf084ee142e5d2d84c0407c4ab82f63d2cbded9c5e4858c7c7a"


class ProcessMemoryCounters(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_ulong),
        ("page_fault_count", ctypes.c_ulong),
        ("peak_working_set_size", ctypes.c_size_t),
        ("working_set_size", ctypes.c_size_t),
        ("quota_peak_paged_pool_usage", ctypes.c_size_t),
        ("quota_paged_pool_usage", ctypes.c_size_t),
        ("quota_peak_nonpaged_pool_usage", ctypes.c_size_t),
        ("quota_nonpaged_pool_usage", ctypes.c_size_t),
        ("pagefile_usage", ctypes.c_size_t),
        ("peak_pagefile_usage", ctypes.c_size_t),
    ]


def peak_working_set() -> int:
    counters = ProcessMemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    current_process = ctypes.windll.kernel32.GetCurrentProcess
    current_process.restype = ctypes.c_void_p
    get_memory = ctypes.windll.psapi.GetProcessMemoryInfo
    get_memory.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ProcessMemoryCounters),
        ctypes.c_ulong,
    ]
    if not get_memory(current_process(), ctypes.byref(counters), counters.cb):
        raise OSError("GetProcessMemoryInfo failed")
    return counters.peak_working_set_size


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--probe-root", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    source = args.source.resolve()
    root = args.probe_root.resolve()
    assert root.is_dir() and source.is_file()
    assert source != root and not source.is_relative_to(root)
    fixture_dir = Path(tempfile.mkdtemp(prefix="durable001-mock-", dir=root)).resolve()
    assert fixture_dir.is_relative_to(root) and fixture_dir != root
    fixture = fixture_dir / "checkpoint.json"
    try:
        shutil.copy2(source, fixture)
        assert sha(fixture) == sha(source), "fixture copy differs from preserved checkpoint"
        print("MOCK_FIXTURE_COPIED", flush=True)
        schedule = build_schedule(args.repository_root)
        first_missing = schedule[732]["game_id"]
        calls: list[str] = []

        def mock_executor(row: dict) -> dict:
            calls.append(row["game_id"])
            if len(calls) > 1:
                raise RuntimeError("MOCK_STOP_AFTER_ONE_WRITE")
            return {"game_id": row["game_id"], "winner": "MOCK_ONLY"}

        try:
            run_checkpointed_schedule(
                schedule,
                fixture,
                mock_executor,
                writer_id="durable-001-mock-memory-probe",
                expected_matchups=9,
                games_per_matchup=100,
            )
        except RuntimeError as exc:
            assert str(exc) == "MOCK_STOP_AFTER_ONE_WRITE"
        else:
            raise AssertionError("mock stop did not occur")
        assert calls == [first_missing, schedule[733]["game_id"]]
        with fixture.open("rb") as handle:
            header = handle.read(256)
        assert b'"completed_games": 733' in header
        assert not Path(f"{fixture}.lock").exists()
        print(
            json.dumps(
                {
                    "status": "MOCK_RESUME_ONE_WRITE_PASSED",
                    "source_sha256": sha(source),
                    "fixture_bytes_after_mock": fixture.stat().st_size,
                    "first_missing_id": first_missing,
                    "mock_executor_calls": calls,
                    "peak_working_set_bytes": peak_working_set(),
                    "preserved_source_unchanged": sha(source) == EXPECTED_SHA256,
                },
                sort_keys=True,
            ),
            flush=True,
        )
    finally:
        assert fixture_dir.is_relative_to(root) and fixture_dir.name.startswith("durable001-mock-")
        shutil.rmtree(fixture_dir)


if __name__ == "__main__":
    main()
