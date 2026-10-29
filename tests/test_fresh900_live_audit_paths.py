"""Unchanged independent path/persistence predicates with a complete mock record."""

import hashlib
import sys
from pathlib import Path

import pytest
import test_fresh900_live_audit as audit
from fresh900_native_fixtures import native_snapshot

source = Path(__file__).parent / "evidence/pr370_authorization_paths.py.txt"
assert hashlib.sha256(source.read_bytes()).hexdigest() == (
    "15ae761716d7606b0c02bdf5d709061be78fefd4968bc3af9016e1170ce2c25a"
)
previous = sys.modules.get("test_independent_adapter")
sys.modules["test_independent_adapter"] = audit
try:
    exec(compile(source.read_bytes(), str(source), "exec"), globals())
finally:
    if previous is None:
        del sys.modules["test_independent_adapter"]
    else:
        sys.modules["test_independent_adapter"] = previous


@pytest.fixture
def boundary(tmp_path, monkeypatch, request):
    value = audit.boundary.__wrapped__(tmp_path, monkeypatch, request)
    # The persistence-positive probe needs a now-complete valid result in order
    # to reach its original replacement-denial injection. Assertions are intact.
    value[2].side_effect = lambda root, spec: native_snapshot(spec)
    return value
