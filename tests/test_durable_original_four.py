"""Original four failing audit predicates; fixtures supply the new explicit capabilities."""

import dataclasses
import multiprocessing
import sys
import time
import types
from pathlib import Path

import pytest
from test_durable_resume_safety import contract as contract

from tmnt_design_studio import calibration_integrity as integrity
from tmnt_design_studio import resume_authorization as auth
from tmnt_design_studio import resume_status as monitor
from tmnt_design_studio.calibration_runner import run_authorized_resume


@pytest.fixture
def sample(contract):
    return contract


def step(sample, executor=None):
    rows, lease, status, _ = sample
    return run_authorized_resume(
        rows,
        executor or (lambda row: {"game_id": row["game_id"], "synthetic": "audit"}),
        lease=lease,
        status=status,
        stop_after=1,
    )


def test_defect_status_must_not_overwrite_reference(sample):
    rows, lease, _, raw = sample
    destination = lease.reference.with_name("durable-status.json")
    lease.reference.rename(destination)
    lease = dataclasses.replace(lease, reference=destination)
    try:  # noqa: SIM105 -- preserve the original independent audit predicate
        step((rows, lease, destination, raw))
    except auth.ResumeRefused:
        pass
    assert destination.read_bytes() == raw, (
        "status publication replaced the immutable audit reference"
    )


def test_defect_dependency_mismatch_must_be_rejected(sample, tmp_path, monkeypatch):
    dependency = tmp_path / "tampered_typer.py"
    dependency.write_text("synthetic changed dependency")
    module = types.ModuleType("typer")
    module.__file__ = str(dependency)
    monkeypatch.setitem(sys.modules, "typer", module)
    with pytest.raises(auth.ResumeRefused, match="dependency|identity|import"):
        sample[1].identity.verify()


class Pipe:
    def __init__(self, shared):
        self.shared = shared

    def send_bytes(self, data):
        self.shared["data"] = data

    def close(self):
        pass

    def poll(self, _timeout):
        return True

    def recv_bytes(self, _maximum):
        if self.shared.get("delay"):
            time.sleep(self.shared["delay"])
        return self.shared.get("data", b"")


class ImmediateProcess:
    pid = 123

    def __init__(self, target, args):
        self.target = target
        self.args = args

    def start(self):
        self.target(*self.args)

    def is_alive(self):
        return False

    def join(self):
        pass


class ImmediateContext:
    def __init__(self, shared):
        self.shared = shared

    def Pipe(self, **_):
        return Pipe(self.shared), Pipe(self.shared)

    def Process(self, target, args, **_):
        return ImmediateProcess(target, args)


def test_defect_supported_monitor_must_not_read_active_checkpoint(sample, monkeypatch):
    rows, lease, telemetry, raw = sample
    checkpoint = lease.checkpoint.with_name("durable-status.json")
    lease.checkpoint.rename(checkpoint)
    lease = dataclasses.replace(lease, checkpoint=checkpoint)
    assert step((rows, lease, telemetry, raw))["completed_games"] == 733
    before = checkpoint.read_bytes()
    opened = []
    read = monitor._read_shared

    def observe(path):
        opened.append(Path(path))
        return read(path)

    monkeypatch.setattr(monitor, "_read_shared", observe)
    monkeypatch.setattr(multiprocessing, "get_context", lambda _: ImmediateContext({}))
    with integrity.WriterLock(checkpoint, "active-owner", hold_handle=True):
        monitor.read_status(checkpoint, authorization=lease.authorization_id)
    assert not opened, "supported status API opened an active checkpoint with the allowed basename"
    assert checkpoint.read_bytes() == before


def test_defect_receive_phase_must_respect_monitor_deadline(tmp_path, monkeypatch):
    shared = {"delay": 0.35, "data": b""}

    # Simulate a ready IPC header with an incomplete frame body / suspended sender.
    class Process(ImmediateProcess):
        def start(self):
            pass

    class Context(ImmediateContext):
        def Process(self, target, args, **_):
            return Process(target, args)

    monkeypatch.setattr(multiprocessing, "get_context", lambda _: Context(shared))
    start = time.monotonic()
    result = monitor.read_status(
        tmp_path / "durable-status.json", authorization="audit", timeout=0.02
    )
    elapsed = time.monotonic() - start
    assert result == {"state": "UNKNOWN"}
    assert elapsed < 0.25, f"IPC receive exceeded 20ms budget: {elapsed:.3f}s"
