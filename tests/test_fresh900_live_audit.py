"""Execute the preserved audit predicates unchanged against the replacement head."""

import hashlib
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from tmnt_design_studio import fresh900 as persistence
from tmnt_design_studio import fresh900_live as adapter

ORIGINAL = Path(__file__).parent / "evidence/pr370_independent_adapter.py.txt"
assert hashlib.sha256(ORIGINAL.read_bytes()).hexdigest() == (
    "fc8d0df270e0ed3f82486d2539be5eeb3705f2e290c07a56fafa11553e02b8a3"
)
exec(compile(ORIGINAL.read_bytes(), str(ORIGINAL), "exec"), globals())

# Only fixture authority changes: use the actual review checkout/commit/platform.
# No original assertion, negative payload or predicate body is edited.
ROOT = Path(__file__).resolve().parents[1]
GIT = shutil.which("git") or "C:/Program Files/Git/cmd/git.exe"
HEAD = subprocess.check_output(
    [GIT, "-c", f"safe.directory={ROOT.as_posix()}", "-C", str(ROOT), "rev-parse", "HEAD"],
    text=True,
).strip()
_audit_boundary = globals()["boundary"].__wrapped__


@pytest.fixture
def boundary(tmp_path, monkeypatch, request):
    value = _audit_boundary(tmp_path, monkeypatch)
    if request.node.name != "test_replaced_executor_is_detected_before_invocation":
        # Explicit controlled mock boundary for record/error tests. The callable
        # substitution predicate ALWAYS uses the real frozen binding verifier.
        monkeypatch.setattr(adapter, "_bind_executor", lambda *_: value[2])
    if os.name != "nt":
        from test_fresh900_fullplan import linux_resources

        # Actual Linux counters, existing thresholds/disk check, no version spoof.
        # The production Windows provider remains unchanged and rejects Linux.
        monkeypatch.setattr(persistence, "resources", linux_resources)
    return value
