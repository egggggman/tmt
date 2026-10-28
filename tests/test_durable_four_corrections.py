"""Expanded four-defect acceptance; synthetic files and metadata only."""

from __future__ import annotations

import dataclasses
import importlib.machinery
import multiprocessing
import os
import subprocess
import sys
import threading
import time
import types
from pathlib import Path

import pytest
import typer
from resume_test_support import telemetry_grant
from test_durable_resume_safety import contract as contract
from test_durable_resume_safety import execute

from tmnt_design_studio import resume_status as status
from tmnt_design_studio.resume_authorization import ResumeRefused, encoded, file_hash
from tmnt_design_studio.resume_paths import directory_identity


@pytest.mark.parametrize("role", ["reference", "working", "control", "nested-reference"])
def test_output_roles_rejected_before_any_writer_or_temp(contract, monkeypatch, role):
    rows, lease, _, raw = contract
    if role == "reference":
        root = lease.reference.parent
    elif role == "working":
        root = lease.checkpoint.parent
    elif role == "control":
        root = lease.control
        root.mkdir()
    else:
        root = lease.reference.parent / "nested"
        root.mkdir()
    lease = dataclasses.replace(
        lease, telemetry_root=root, telemetry_root_identity=directory_identity(root)
    )

    def forbidden(*args, **kwargs):
        pytest.fail("writer/temp was reached before path validation")

    monkeypatch.setattr(status.tempfile, "mkstemp", forbidden)
    with pytest.raises(ResumeRefused):
        execute((rows, lease, root / status.STATUS_NAME, raw), executor=forbidden)
    assert lease.reference.read_bytes() == raw
    assert lease.checkpoint.read_bytes() == raw


@pytest.mark.parametrize("role", ["reference", "working"])
def test_control_store_cannot_nest_in_protected_role(contract, role):
    rows, lease, path, raw = contract
    protected = getattr(lease, role if role == "reference" else "checkpoint").parent
    bad = dataclasses.replace(lease, control=protected / "receipts")
    with pytest.raises(ResumeRefused):
        execute((rows, bad, path, raw), executor=lambda _: pytest.fail("dispatch"))
    assert not bad.control.exists() and lease.reference.read_bytes() == raw


def test_telemetry_capability_is_required_for_every_public_operation(tmp_path):
    path = tmp_path / status.STATUS_NAME
    with pytest.raises(ResumeRefused):
        status.publish_status(path, authorization="test", count=733, checkpoint_sha256="a" * 64)
    assert not path.exists()
    assert status.read_status(path, authorization="test") == {"state": "UNKNOWN"}


def test_root_object_replacement_is_rejected(tmp_path):
    root = tmp_path / "telemetry"
    root.mkdir()
    grant = telemetry_grant(root)
    root.rename(tmp_path / "old-root")
    root.mkdir()
    with pytest.raises(ResumeRefused):
        status.publish_status(
            root / status.STATUS_NAME,
            authorization="test",
            count=733,
            checkpoint_sha256="a" * 64,
            grant=grant,
        )
    assert not list(root.iterdir())


@pytest.mark.parametrize("alias", ["hardlink", "symlink", "junction"])
def test_windows_and_posix_aliases_refused(contract, alias):
    _, lease, path, raw = contract
    grant = lease.validate_outputs(path)
    if alias == "hardlink":
        os.link(lease.reference, path)
    elif alias == "symlink":
        try:
            path.symlink_to(lease.reference)
        except OSError as error:
            pytest.skip(f"symlink creation unavailable: {error}")
    else:
        if os.name != "nt":
            pytest.skip("Windows junction test")
        path.parent.rmdir()
        result = subprocess.run(
            ["cmd.exe", "/d", "/c", "mklink", "/J", str(path.parent), str(lease.reference.parent)],
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
            check=False,
        )
        assert result.returncode == 0, result.stderr
    with pytest.raises(ResumeRefused):
        status.publish_status(
            path,
            authorization=lease.authorization_id,
            count=733,
            checkpoint_sha256="a" * 64,
            grant=grant,
        )
    assert status.read_status(path, authorization=lease.authorization_id, grant=grant) == {
        "state": "UNKNOWN"
    }
    assert lease.reference.read_bytes() == raw


@pytest.mark.parametrize("change", ["origin", "payload", "loader", "missing-manifest"])
def test_dependency_same_version_substitution_is_refused(contract, tmp_path, monkeypatch, change):
    identity = contract[1].identity
    if change == "missing-manifest":
        with pytest.raises(ResumeRefused):
            dataclasses.replace(identity, dependency_files=None).verify()
        return
    original = typer.__file__
    module = types.ModuleType("typer")
    module.__version__ = typer.__version__
    if change == "origin":
        path = tmp_path / "same-version.py"
        path.write_bytes(Path(original).read_bytes())
        module.__file__ = str(path)
    elif change == "loader":
        module.__file__ = original
        module.__spec__ = importlib.machinery.ModuleSpec(
            "typer", None, origin=str(tmp_path / "foreign.py")
        )
    else:
        path = tmp_path / "pinned-dependency.py"
        path.write_text("VERSION='same'")
        files = dict(identity.dependency_files)
        files[str(path.resolve())] = file_hash(path)
        origins = dict(identity.dependency_origins)
        origins["typer"] = str(path.resolve())
        identity = dataclasses.replace(identity, dependency_files=files, dependency_origins=origins)
        path.write_text("VERSION='same'; SUBSTITUTED=True")
        module.__file__ = str(path)
    monkeypatch.setitem(sys.modules, "typer", module)
    with pytest.raises(ResumeRefused, match="dependency"):
        identity.verify()


def test_base_interpreter_payload_is_required(contract):
    identity = contract[1].identity
    files = dict(identity.interpreter_files)
    files[str(Path(sys._base_executable).resolve())] = "0" * 64
    with pytest.raises(ResumeRefused, match="interpreter"):
        dataclasses.replace(identity, interpreter_files=files).verify()


class Worker:
    def __init__(self, target, args, mode):
        self.target, self.args, self.mode = target, args, mode
        self.pid = None
        self.exitcode = None
        self.alive = False
        self.closed = threading.Event()
        self.joins = []

    def start(self):
        if self.mode == "slow-start":
            time.sleep(0.15)
        self.pid = 123
        self.alive = True
        if self.mode == "complete":
            data = encoded(
                dict(
                    protocol=status.PROTOCOL,
                    authorization="test",
                    committed_games=733,
                    checkpoint_sha256="a" * 64,
                    heartbeat=time.time(),
                )
            )
            buffer = self.args[-1]
            buffer[4 : 4 + len(data)] = data
            buffer[:4] = len(data).to_bytes(4, "little")
            self.alive = False
            self.exitcode = 0
        elif self.mode == "partial":
            self.args[-1][:4] = (200).to_bytes(4, "little")
        elif self.mode == "empty":
            self.alive = False
            self.exitcode = 0

    def join(self, timeout):
        assert 0 <= timeout <= 0.25
        self.joins.append(timeout)
        if self.alive:
            time.sleep(timeout)

    def is_alive(self):
        return self.alive

    def terminate(self):
        self.alive = False
        self.exitcode = -1

    def close(self):
        self.closed.set()


@pytest.mark.parametrize(
    "mode", ["complete", "partial", "empty", "stalled", "slow-start", "slow-setup"]
)
def test_single_deadline_including_start_and_cleanup(tmp_path, monkeypatch, mode):
    workers = []

    class Context:
        def RawArray(self, _, size):
            if mode == "slow-setup":
                time.sleep(0.15)
            return bytearray(size)

        def Pipe(self, **_):
            pytest.fail("framed IPC must not be used")

        def Process(self, target, args, **_):
            worker = Worker(target, args, mode)
            workers.append(worker)
            return worker

    monkeypatch.setattr(multiprocessing, "get_context", lambda _: Context())
    start = time.monotonic()
    result = status.read_status(
        tmp_path / status.STATUS_NAME,
        authorization="test",
        timeout=0.05,
        grant=telemetry_grant(tmp_path),
    )
    elapsed = time.monotonic() - start
    assert elapsed < 0.12, elapsed
    assert result["state"] == ("REPORTED_ONLY" if mode == "complete" else "UNKNOWN")
    if mode == "slow-setup":
        time.sleep(0.2)
        assert not workers  # Cancelled setup must never create a child afterward.
    else:
        assert workers[0].closed.wait(0.5)
        assert workers[0].joins


def test_actual_worker_lifecycle_and_fixed_buffer(tmp_path):
    grant = telemetry_grant(tmp_path)
    path = tmp_path / status.STATUS_NAME
    status.publish_status(
        path, authorization="test", count=733, checkpoint_sha256="a" * 64, grant=grant
    )
    context = multiprocessing.get_context("spawn")
    buffer = context.RawArray("B", status.MAX_BYTES + 4)
    status._worker(str(path), grant, buffer)
    size = int.from_bytes(bytes(buffer[:4]), "little")
    assert (
        status.parse_status(bytes(buffer[4 : 4 + size]), authorization="test")["committed_games"]
        == 733
    )
    baseline = {child.pid for child in multiprocessing.active_children()}
    started = time.monotonic()
    observed = status.read_status(path, authorization="test", grant=grant)
    assert time.monotonic() - started < 0.4
    assert observed["state"] in ("REPORTED_ONLY", "UNKNOWN")
    deadline = time.monotonic() + 0.5
    while time.monotonic() < deadline:
        if not ({child.pid for child in multiprocessing.active_children()} - baseline):
            break
        time.sleep(0.01)
    assert not ({child.pid for child in multiprocessing.active_children()} - baseline)
