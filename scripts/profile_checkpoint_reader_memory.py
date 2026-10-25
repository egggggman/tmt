"""Compare current and streaming restore on disposable Durable 001 copies."""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIVE = Path(r"G:\cardcade\calibration-runs\BAD_GUYS_CRONIES_0_2_DURABLE_001\checkpoint.json")
EXPECTED_SHA = "ab1ecf83c6acbaf084ee142e5d2d84c0407c4ab82f63d2cbded9c5e4858c7c7a"
REPAIR_COMMIT = "01ee617683bbc50f38098923c56102738eec9f37"


class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.wintypes.DWORD),
        ("PageFaultCount", ctypes.wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
        ("PrivateUsage", ctypes.c_size_t),
    ]


class PERFORMANCE_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.wintypes.DWORD),
        ("CommitTotal", ctypes.c_size_t),
        ("CommitLimit", ctypes.c_size_t),
        ("CommitPeak", ctypes.c_size_t),
        ("PhysicalTotal", ctypes.c_size_t),
        ("PhysicalAvailable", ctypes.c_size_t),
        ("SystemCache", ctypes.c_size_t),
        ("KernelTotal", ctypes.c_size_t),
        ("KernelPaged", ctypes.c_size_t),
        ("KernelNonpaged", ctypes.c_size_t),
        ("PageSize", ctypes.c_size_t),
        ("HandleCount", ctypes.wintypes.DWORD),
        ("ProcessCount", ctypes.wintypes.DWORD),
        ("ThreadCount", ctypes.wintypes.DWORD),
    ]


def metrics() -> dict[str, int]:
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GetCurrentProcess.restype = ctypes.wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = [
        ctypes.wintypes.HANDLE,
        ctypes.POINTER(PROCESS_MEMORY_COUNTERS_EX),
        ctypes.wintypes.DWORD,
    ]
    psapi.GetProcessMemoryInfo.restype = ctypes.wintypes.BOOL
    psapi.GetPerformanceInfo.argtypes = [
        ctypes.POINTER(PERFORMANCE_INFORMATION),
        ctypes.wintypes.DWORD,
    ]
    psapi.GetPerformanceInfo.restype = ctypes.wintypes.BOOL
    process = PROCESS_MEMORY_COUNTERS_EX()
    process.cb = ctypes.sizeof(process)
    if not psapi.GetProcessMemoryInfo(
        kernel32.GetCurrentProcess(), ctypes.byref(process), process.cb
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    system = PERFORMANCE_INFORMATION()
    system.cb = ctypes.sizeof(system)
    if not psapi.GetPerformanceInfo(ctypes.byref(system), system.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    return {
        "working_set_bytes": int(process.WorkingSetSize),
        "peak_working_set_bytes": int(process.PeakWorkingSetSize),
        "private_commit_bytes": int(process.PrivateUsage),
        "peak_private_commit_bytes": int(process.PeakPagefileUsage),
        "process_page_fault_count": int(process.PageFaultCount),
        "system_commit_bytes": int(system.CommitTotal * system.PageSize),
        "system_commit_limit_bytes": int(system.CommitLimit * system.PageSize),
        "system_available_physical_bytes": int(system.PhysicalAvailable * system.PageSize),
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(8 * 1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def same_bytes(left: Path, right: Path) -> bool:
    with left.open("rb") as first, right.open("rb") as second:
        while True:
            a, b = first.read(1024 * 1024), second.read(1024 * 1024)
            if a != b:
                return False
            if not a:
                return True


def worker(mode: str, checkpoint: Path, output: Path | None, marker: Path | None = None) -> dict:
    before_imports = metrics()
    sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
    from tmnt_design_studio.calibration_integrity import (
        CheckpointAccumulator,
        validate_checkpoint,
        validate_schedule,
    )
    from tools.run_bad_guys_initial_calibration import build_schedule

    schedule = build_schedule(ROOT)
    contract = validate_schedule(
        schedule, expected_games=900, expected_matchups=9, games_per_matchup=100
    )
    accumulator = CheckpointAccumulator(schedule, writer_id=f"memory-profile-{mode}")
    after_imports = metrics()
    stop = threading.Event()
    maxima = dict(after_imports)
    minimum_available = after_imports["system_available_physical_bytes"]

    def sample() -> None:
        nonlocal minimum_available
        while not stop.wait(0.025):
            value = metrics()
            for key, current in value.items():
                if key == "process_page_fault_count":
                    continue
                maxima[key] = max(maxima.get(key, current), current)
            minimum_available = min(minimum_available, value["system_available_physical_bytes"])

    sampler = threading.Thread(target=sample, daemon=True)
    sampler.start()
    started = time.perf_counter()
    if marker is not None:
        marker.write_text("restore", encoding="ascii")
    if mode == "whole_file":
        payload = json.loads(checkpoint.read_text(encoding="utf-8"))
        validate_checkpoint(payload, schedule)
        if payload.get("schedule_digest") != contract["schedule_digest"]:
            raise AssertionError("whole-file baseline schedule digest mismatch")
        accumulator.restore(payload, take_ownership=True)
        del payload
    elif mode in {"stream", "stream_engine"}:
        accumulator.restore_stream(checkpoint)
    else:
        raise ValueError(mode)
    restored_at = metrics()
    restore_finished = time.perf_counter()
    game_summary = None
    game_elapsed = None
    if mode == "stream_engine":
        # One non-calibration diagnostic game; return data is discarded and no
        # checkpoint or statistical evidence is written.
        from tmnt_design_studio.smoke01 import run_smoke_game
        from tmnt_design_studio.stage002 import DeckSpec, GameSpec

        spec = GameSpec(
            "memory-diagnostic-discarded",
            "non-calibration-memory-probe",
            3000,
            "diagnostic",
            (
                DeckSpec("shredder-p0.3", "decks/shredder/PROTOTYPE_0.3.txt"),
                DeckSpec("donatello-p0.3a", "decks/donatello/PROTOTYPE_0.3a.txt"),
            ),
        )
        if marker is not None:
            marker.write_text("engine", encoding="ascii")
        game_started = time.perf_counter()
        result = run_smoke_game(ROOT, spec)
        game_elapsed = round(time.perf_counter() - game_started, 3)
        game_summary = {
            "terminal": result.get("winner") is not None,
            "error_present": result.get("error") is not None,
            "event_count": len(result.get("events", [])),
        }
        del result
    write_started = time.perf_counter()
    if output is not None:
        if marker is not None:
            marker.write_text("serialization", encoding="ascii")
        accumulator.write(output, writer_id=f"memory-profile-{mode}", return_snapshot=False)
    write_elapsed = round(time.perf_counter() - write_started, 3)
    stop.set()
    sampler.join()
    finished = metrics()
    for key, current in finished.items():
        if key != "process_page_fault_count":
            maxima[key] = max(maxima.get(key, current), current)
    if marker is not None:
        marker.unlink(missing_ok=True)
    return {
        "mode": mode,
        "before_imports": before_imports,
        "after_imports": after_imports,
        "after_restore": restored_at,
        "finished": finished,
        "maxima": maxima,
        "minimum_system_available_physical_bytes": minimum_available,
        "restore_elapsed_seconds": round(restore_finished - started, 3),
        "game_elapsed_seconds": game_elapsed,
        "write_elapsed_seconds": write_elapsed,
        "restored_record_count": len(accumulator.completed_ids),
        "schedule_digest": accumulator.schedule_digest,
        "game_diagnostic": game_summary,
        "output_sha256": sha256(output) if output else None,
        "output_bytes": output.stat().st_size if output else None,
    }


def single_profile(mode: str, marker: Path | None = None) -> None:
    env = {
        **os.environ,
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "safe.directory",
        "GIT_CONFIG_VALUE_0": str(ROOT).replace("\\", "/"),
    }
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, env=env
    ).strip()
    assert commit == REPAIR_COMMIT, commit
    temp_root = Path(tempfile.mkdtemp(prefix=f"durable001_{mode}_", dir=ROOT))
    try:
        checkpoint = temp_root / "checkpoint.json"
        with LIVE.open("rb") as source, checkpoint.open("xb") as target:
            shutil.copyfileobj(source, target, length=8 * 1024 * 1024)
        assert sha256(checkpoint) == EXPECTED_SHA
        output = temp_root / "restored-output.json" if mode != "stream_engine" else None
        if marker is not None:
            marker.write_text("startup", encoding="ascii")
        try:
            raw_result = subprocess.check_output(
                [
                    sys.executable,
                    "-B",
                    str(Path(__file__).resolve()),
                    "--worker",
                    mode,
                    str(checkpoint),
                    str(output) if output else "-",
                    str(marker) if marker else "-",
                ],
                cwd=ROOT,
                text=True,
                env=env,
            )
        finally:
            if marker is not None:
                marker.unlink(missing_ok=True)
        result = json.loads(raw_result)
        assert result["restored_record_count"] == 732
        if output:
            assert result["output_sha256"] == EXPECTED_SHA
        print(
            json.dumps(
                {
                    "status": "SINGLE_READER_PROFILE_COMPLETE",
                    "created_utc": datetime.now(UTC).isoformat(),
                    "repair_commit": commit,
                    "input_checkpoint_sha256": EXPECTED_SHA,
                    "input_checkpoint_bytes": LIVE.stat().st_size,
                    "profile": result,
                },
                sort_keys=True,
            )
        )
    finally:
        shutil.rmtree(temp_root)


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--single":
        single_profile(sys.argv[2], Path(sys.argv[3]) if len(sys.argv) > 3 else None)
        return
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        result = worker(
            sys.argv[2],
            Path(sys.argv[3]),
            Path(sys.argv[4]) if sys.argv[4] != "-" else None,
            Path(sys.argv[5]) if len(sys.argv) > 5 and sys.argv[5] != "-" else None,
        )
        print(json.dumps(result, sort_keys=True))
        return

    env = {
        **os.environ,
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "safe.directory",
        "GIT_CONFIG_VALUE_0": str(ROOT).replace("\\", "/"),
    }
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, env=env
    ).strip()
    assert commit == REPAIR_COMMIT, commit
    temp_root = Path(tempfile.mkdtemp(prefix="durable001_reader_profile_", dir=ROOT))
    try:
        whole_input, stream_input = temp_root / "whole.json", temp_root / "stream.json"
        whole_output, stream_output = (
            temp_root / "whole-output.json",
            temp_root / "stream-output.json",
        )
        for destination in (whole_input, stream_input):
            with LIVE.open("rb") as source, destination.open("xb") as target:
                shutil.copyfileobj(source, target, length=8 * 1024 * 1024)
        assert sha256(whole_input) == sha256(stream_input) == EXPECTED_SHA
        whole = json.loads(
            subprocess.check_output(
                [
                    sys.executable,
                    "-B",
                    str(Path(__file__).resolve()),
                    "--worker",
                    "whole_file",
                    str(whole_input),
                    str(whole_output),
                ],
                cwd=ROOT,
                text=True,
                env=env,
            )
        )
        streamed = json.loads(
            subprocess.check_output(
                [
                    sys.executable,
                    "-B",
                    str(Path(__file__).resolve()),
                    "--worker",
                    "stream",
                    str(stream_input),
                    str(stream_output),
                ],
                cwd=ROOT,
                text=True,
                env=env,
            )
        )
        engine = json.loads(
            subprocess.check_output(
                [
                    sys.executable,
                    "-B",
                    str(Path(__file__).resolve()),
                    "--worker",
                    "stream_engine",
                    str(stream_input),
                    "-",
                ],
                cwd=ROOT,
                text=True,
                env=env,
            )
        )
        assert whole["restored_record_count"] == streamed["restored_record_count"] == 732
        assert whole["schedule_digest"] == streamed["schedule_digest"]
        assert whole["output_sha256"] == streamed["output_sha256"] == EXPECTED_SHA
        assert same_bytes(whole_output, stream_output)
        report = {
            "status": "STREAMING_READER_PROFILE_COMPLETE",
            "created_utc": datetime.now(UTC).isoformat(),
            "repair_commit": commit,
            "input_checkpoint_sha256": EXPECTED_SHA,
            "input_checkpoint_bytes": LIVE.stat().st_size,
            "current_whole_file_reader": whole,
            "streaming_reader": streamed,
            "streaming_reader_with_engine_diagnostic": engine,
            "engine_diagnostic_note": (
                "One non-calibration smoke game with test decks; result discarded, "
                "no checkpoint/evidence written."
            ),
            "hard_paging_note": (
                "PROCESS_MEMORY_COUNTERS_EX page-fault count is total faults; system "
                "Pages Input/sec and Page Reads/sec are sampled by the outer "
                "PowerShell process when available."
            ),
        }
        print(json.dumps(report, indent=2, sort_keys=True))
    finally:
        shutil.rmtree(temp_root)


if __name__ == "__main__":
    main()
