"""Exercise bounded checkpoint replacement on disposable Windows files."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from tmnt_design_studio.calibration_integrity import _replace_with_retry


def hold_reader(
    path: Path, ready: Path, milliseconds: int, *, share_mode: str = "Read"
) -> subprocess.Popen:
    assert share_mode in ("Read", "None")
    script = (
        f"$p='{path}'; $r='{ready}'; "
        "$f=[System.IO.FileStream]::new($p,[System.IO.FileMode]::Open,"
        f"[System.IO.FileAccess]::Read,[System.IO.FileShare]::{share_mode}); "
        "try { [System.IO.File]::WriteAllText($r,'ready'); "
        f"Start-Sleep -Milliseconds {milliseconds} }} "
        "finally { $f.Dispose() }"
    )
    reader = subprocess.Popen(["powershell", "-NoProfile", "-Command", script])
    deadline = time.monotonic() + 8
    while not ready.exists():
        if reader.poll() is not None or time.monotonic() >= deadline:
            raise RuntimeError("disposable reader did not open")
        time.sleep(0.02)
    return reader


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.probe_root.resolve()
    assert root.is_dir()
    directory = Path(tempfile.mkdtemp(prefix="durable001-replace-", dir=root)).resolve()
    assert directory.is_relative_to(root) and directory != root
    try:
        destination = directory / "checkpoint.json"
        source = directory / ".checkpoint.json.new"
        destination.write_bytes(b"old")
        source.write_bytes(b"new")
        reader = hold_reader(destination, directory / "reader1.ready", 900)
        _replace_with_retry(str(source), destination)
        assert reader.wait(timeout=8) == 0
        assert destination.read_bytes() == b"new"

        source.write_bytes(b"newer")
        reader = hold_reader(destination, directory / "reader2.ready", 6000)
        first_error = None
        try:
            _replace_with_retry(str(source), destination)
        except PermissionError as exc:
            first_error = exc
        assert first_error is not None, "persistent sharing denial did not fail closed"
        assert destination.read_bytes() == b"new" and source.read_bytes() == b"newer"
        assert reader.wait(timeout=8) == 0

        monitor_target = directory / "monitor_checkpoint.json"
        monitor_replacement = directory / "monitor_replacement.json"
        monitor_payload = {
            "completed_games": 732,
            "records": [{"blob": "x" * 300}],
            "schedule_digest": "4da440bc83b9790876d1020ae83cf2147c4e60a67feba8bb7181421e196b303e",
            "schedule_games": 900,
        }
        monitor_target.write_text(json.dumps(monitor_payload, indent=2), encoding="utf-8")
        monitor_payload["completed_games"] = 733
        monitor_replacement.write_text(json.dumps(monitor_payload, indent=2), encoding="utf-8")
        monitor = (
            Path(__file__).resolve().parents[1] / "scripts/calibration_durable_status_safe.ps1"
        )
        reader = subprocess.Popen(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(monitor),
                "-Checkpoint",
                str(monitor_target),
                "-HoldOpenMilliseconds",
                "2500",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        assert reader.stdout is not None
        assert reader.stdout.readline().strip() == "MONITOR_READ_HANDLE_OPEN"
        _replace_with_retry(str(monitor_replacement), monitor_target)
        output, errors = reader.communicate(timeout=8)
        assert reader.returncode == 0, errors
        assert "ReportedCompletedGames : 732" in output
        assert json.loads(monitor_target.read_text())["completed_games"] == 733

        locked = hold_reader(monitor_target, directory / "reader3.ready", 2500, share_mode="None")
        unavailable = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(monitor),
                "-Checkpoint",
                str(monitor_target),
            ],
            capture_output=True,
            text=True,
            timeout=8,
            check=True,
        )
        assert "IdentityCheck" in unavailable.stdout
        assert "UNAVAILABLE:" in unavailable.stdout
        assert locked.wait(timeout=8) == 0
        print(
            json.dumps(
                {
                    "status": "WINDOWS_REPLACE_PROBE_PASSED",
                    "transient_denial_retried": True,
                    "persistent_denial_failed_closed": True,
                    "original_error": str(first_error),
                    "checkpoint_unchanged_after_failure": True,
                    "replacement_succeeded_with_safe_monitor_open": True,
                    "monitor_reports_temporary_unavailability": True,
                    "probe_root": str(root),
                },
                sort_keys=True,
            )
        )
    finally:
        assert directory.is_relative_to(root) and directory.name.startswith("durable001-replace-")
        shutil.rmtree(directory)


if __name__ == "__main__":
    main()
