"""Measurable caller/ownership contract; never pretend denied termination succeeded."""

import errno
import importlib.util
import json
import multiprocessing
import sys
import threading
import time
from pathlib import Path

import pytest
from resume_test_support import telemetry_grant

from tmnt_design_studio import monitor_cleanup as lifecycle
from tmnt_design_studio import resume_status as status
from tmnt_design_studio.resume_authorization import encoded


class Backend:
    def __init__(self, args, mode):
        self.args, self.mode = args, mode
        self.pid = None
        self.exitcode = None
        self.alive = False
        self.exited = threading.Event()
        self.closed = threading.Event()
        self.start_release = threading.Event()
        self.error = PermissionError(errno.EACCES, "original cleanup denial")
        self.error.winerror = 5
        self.calls = []
        self.close_fails = mode == "close-error"

    def finish(self):
        self.alive = False
        self.exitcode = 0
        self.exited.set()

    def start(self):
        if self.mode == "late-exit":
            time.sleep(0.12)
        if self.mode == "stuck-start":
            self.start_release.wait(2)
        self.pid = 123
        self.alive = True
        if self.mode in (
            "complete",
            "close-delay",
            "close-error",
            "join-error",
            "cleanup-join-error",
        ):
            data = encoded(
                dict(
                    protocol=status.PROTOCOL,
                    authorization="test",
                    committed_games=733,
                    checkpoint_sha256="a" * 64,
                    heartbeat=time.time(),
                )
            )
            self.args[-1][4 : 4 + len(data)] = data
            self.args[-1][:4] = len(data).to_bytes(4, "little")
            self.finish()

    def is_alive(self):
        return self.alive

    def join(self, timeout):
        assert 0 <= timeout <= 0.25
        self.calls.append(("join", timeout))
        if self.mode == "join-error":
            raise self.error
        if self.mode == "cleanup-join-error" and len(self.calls) > 1:
            raise self.error
        if self.alive:
            self.exited.wait(timeout)

    def terminate(self):
        self.calls.append(("terminate", None))
        if self.mode == "termination-delay":
            time.sleep(0.35)
        if self.mode in ("termination-error", "denial-then-exit"):
            if self.mode == "denial-then-exit":
                timer = threading.Timer(0.06, self.finish)
                timer.daemon = True
                timer.start()
            raise self.error
        if self.mode == "late-exit":
            timer = threading.Timer(0.06, self.finish)
            timer.daemon = True
            timer.start()
        else:
            self.finish()

    def close(self):
        assert not self.alive, "cannot close a live worker as if exit were confirmed"
        if self.mode == "close-delay":
            time.sleep(0.3)
        if self.close_fails:
            raise self.error
        self.closed.set()


@pytest.fixture
def backend(monkeypatch):
    workers = []

    def install(mode):
        class Context:
            def RawArray(self, _, size):
                return bytearray(size)

            def Process(self, args, **_):
                worker = Backend(args, mode)
                workers.append(worker)
                return worker

        monkeypatch.setattr(multiprocessing, "get_context", lambda _: Context())
        return workers

    yield install
    # External resolution of only these disposable backends, after assertions.
    for worker in workers:
        worker.start_release.set()
        worker.close_fails = False
        worker.finish()
    lifecycle.cleanup_status(refresh=True)
    owner = lifecycle._OWNER
    if owner and owner.worker in workers:
        assert owner.closed.wait(1), "disposable backend did not release ownership"


def sample(tmp_path):
    return status.read_status(
        tmp_path / status.STATUS_NAME,
        authorization="test",
        timeout=0.05,
        grant=telemetry_grant(tmp_path),
    )


@pytest.mark.parametrize("mode", ["termination-delay", "late-exit", "close-delay"])
def test_timeout_never_waits_for_os_control_or_becomes_success(tmp_path, backend, mode):
    workers = backend(mode)
    started = time.monotonic()
    result = sample(tmp_path)
    assert time.monotonic() - started < 0.15
    assert result == {"state": "UNKNOWN"} and result.outcome == "TIMEOUT"
    assert workers[0].closed.wait(0.6)
    assert result.report()["cleanup"]["state"] == "CLOSED"
    assert result.report()["cleanup"]["process_state"] == "EXIT_CONFIRMED"
    assert result.report()["outcome"] == "TIMEOUT" and result["state"] == "UNKNOWN"


def test_denial_preserves_error_and_blocks_worker_accumulation(tmp_path, backend):
    workers = backend("termination-error")
    started = time.monotonic()
    result = sample(tmp_path)
    assert time.monotonic() - started < 0.15
    assert isinstance(result, lifecycle.MonitorFailure)
    owner = result.owner
    assert owner.finished.wait(0.8)
    assert result.cleanup_error is workers[0].error
    report = result.report()
    assert report["state"] == "UNKNOWN" and report["cleanup"]["state"] == "UNRESOLVED"
    assert report["cleanup"]["errors"][-1]["winerror"] == 5
    assert workers[0].is_alive() and not workers[0].closed.is_set()
    again = sample(tmp_path)
    assert again.outcome == "OWNERSHIP_UNRESOLVED" and len(workers) == 1
    # OS/operator later confirms exit; refresh closes the retained handle.
    workers[0].finish()
    lifecycle.cleanup_status(refresh=True)
    assert owner.closed.wait(0.8)
    assert result.cleanup_error is workers[0].error


def test_termination_error_still_rechecks_for_natural_exit(tmp_path, backend):
    workers = backend("denial-then-exit")
    result = sample(tmp_path)
    assert workers[0].closed.wait(0.6)
    assert result.cleanup_error is workers[0].error
    assert result.report()["cleanup"]["process_state"] == "EXIT_CONFIRMED"


def test_close_failure_does_not_claim_child_is_live_or_report_success(tmp_path, backend):
    workers = backend("close-error")
    result = sample(tmp_path)
    assert result == {"state": "UNKNOWN"} and result.outcome == "OWNERSHIP_UNRESOLVED"
    assert result.cleanup_error is workers[0].error
    assert result.report()["cleanup"]["process_state"] == "EXIT_CONFIRMED"
    assert result.report()["cleanup"]["state"] == "UNRESOLVED"
    assert not workers[0].is_alive()


def test_join_error_preserved_while_confirmed_exited_handle_closes(tmp_path, backend):
    workers = backend("join-error")
    result = sample(tmp_path)
    assert result == {"state": "UNKNOWN"}
    assert workers[0].closed.wait(0.5)
    assert result.cleanup_error is workers[0].error


def test_stalled_start_is_retained_and_late_child_cancelled(tmp_path, backend):
    workers = backend("stuck-start")
    started = time.monotonic()
    result = sample(tmp_path)
    assert time.monotonic() - started < 0.15 and result.outcome == "TIMEOUT"
    again = sample(tmp_path)
    assert again.outcome == "OWNERSHIP_UNRESOLVED" and len(workers) == 1
    workers[0].start_release.set()
    assert workers[0].closed.wait(0.6)


def test_success_requires_confirmed_close_inside_budget(tmp_path, backend):
    workers = backend("complete")
    result = sample(tmp_path)
    assert result["state"] == "REPORTED_ONLY"
    assert workers[0].closed.is_set()
    assert lifecycle.cleanup_status()["state"] == "CLOSED"


def test_cleanup_error_cannot_hide_behind_a_valid_sample(tmp_path, backend):
    workers = backend("cleanup-join-error")
    result = sample(tmp_path)
    assert isinstance(result, lifecycle.MonitorFailure)
    assert result.cleanup_error is workers[0].error
    assert result.report()["state"] == "UNKNOWN"
    assert result.report()["cleanup"]["state"] == "CLOSED"


def test_cli_serializes_original_cleanup_error(tmp_path, backend, monkeypatch, capsys):
    backend("close-error")
    result = sample(tmp_path)
    path = Path(__file__).parents[1] / "scripts/durable_status_monitor.py"
    spec = importlib.util.spec_from_file_location("cleanup_monitor_cli", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "read_status", lambda *args, **kwargs: result)
    monkeypatch.setattr(
        sys,
        "argv",
        ["monitor", "--status", str(tmp_path / status.STATUS_NAME), "--authorization", "test"],
    )
    assert module.main() == 0
    observed = json.loads(capsys.readouterr().out)
    assert observed["state"] == "UNKNOWN" and observed["outcome"] == "OWNERSHIP_UNRESOLVED"
    assert observed["cleanup"]["errors"][0]["message"].endswith("original cleanup denial")
