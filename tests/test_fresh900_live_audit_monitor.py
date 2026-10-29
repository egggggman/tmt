"""Unchanged independent Windows handle predicates; skips are not Linux proof."""

import hashlib
import os
from pathlib import Path

import pytest

source = Path(__file__).parent / "evidence/pr370_monitor_independent.py.txt"
assert hashlib.sha256(source.read_bytes()).hexdigest() == (
    "77c5689cb5c67224f947889cdd346074f5d8e7f67e0214d3888e195360728cd1"
)
exec(compile(source.read_bytes(), str(source), "exec"), globals())
pytestmark = pytest.mark.skipif(os.name != "nt", reason="Native Windows file-sharing APIs required")
