import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MONITOR = ROOT / "scripts" / "calibration_status_monitor.ps1"


def test_monitor_declares_delete_and_readwrite_sharing_without_seed_access():
    source = MONITOR.read_text(encoding="utf-8")

    assert "[System.IO.FileShare]::ReadWrite" in source
    assert "[System.IO.FileShare]::Delete" in source
    assert "FileAccess]::Read" in source
    assert "CALIBRATION_SEED_TABLE" not in source
    assert "Start-Process" not in source
    assert "Stop-Process" not in source


@pytest.mark.skipif(
    sys.platform != "win32", reason="PowerShell sharing semantics are Windows-specific"
)
def test_monitor_read_handle_does_not_block_atomic_replace(tmp_path):
    heartbeat = tmp_path / "RUN_HEARTBEAT.json"
    heartbeat.write_text('{"completed_member_count": 0}\n', encoding="utf-8")
    process = subprocess.Popen(
        [
            "powershell.exe",
            "-NoProfile",
            "-File",
            str(MONITOR),
            "-RunDirectory",
            str(tmp_path),
            "-Once",
            "-HoldOpenMilliseconds",
            "1000",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    replacement = tmp_path / "replacement.json"
    replacement.write_text('{"completed_member_count": 1}\n', encoding="utf-8")
    try:
        os.replace(replacement, heartbeat)
    finally:
        stdout, stderr = process.communicate(timeout=5)
    assert process.returncode == 0, stderr
    assert json.loads(heartbeat.read_text(encoding="utf-8"))["completed_member_count"] == 1
