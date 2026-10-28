"""Explicit no-game suite bootstrap for a resolved (non-symlink) CI interpreter."""

import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(root / "src"), str(root), str(root / "tests"), sys.argv[1]]

import pytest  # noqa: E402

raise SystemExit(
    pytest.main(
        [
            "-q",
            "tests/test_fresh900.py",
            "tests/test_fresh900_independent.py",
            "tests/test_fresh900_fullplan.py",
            "tests/test_fresh900_corrections.py",
            "tests/test_calibration_integrity.py",
            "tests/test_bad_guys_calibration_entrypoint.py",
            "tests/test_fresh900_live.py",
            "tests/test_fresh900_live_audit.py",
            "tests/test_fresh900_native.py",
        "tests/test_fresh900_live_audit_paths.py",
        "tests/test_fresh900_live_audit_monitor.py",
        ]
    )
)
