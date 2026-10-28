"""Independent replacement-head probes. Synthetic records and disposable files only."""

import dataclasses
import importlib.machinery
import json
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

from tmnt_design_studio import calibration_integrity as integrity
from tmnt_design_studio import resume_authorization as auth
from tmnt_design_studio import resume_status as monitor
from tmnt_design_studio.calibration_runner import run_authorized_resume
from tmnt_design_studio.resume_paths import TelemetryGrant, directory_identity

REPO = Path(__file__).resolve().parents[1]


def identity():
    source = {
        p.relative_to(REPO).as_posix(): auth.file_hash(p) for p in (REPO / "src").rglob("*.py")
    }
    for relative in (
        "tools/run_bad_guys_initial_calibration.py",
        "tools/baseline005_provenance.py",
        "tools/validate_baseline005_provenance.py",
        "scripts/durable_status_monitor.py",
    ):
        source[relative] = auth.file_hash(REPO / relative)
    files, origins, interpreter = {}, {}, {}
    for name, module in tuple(sys.modules.items()):
        if name.startswith("tmnt_design_studio") or name in ("__main__", "__mp_main__"):
            continue
        origin = getattr(module, "__file__", None)
        if origin and Path(origin).is_file():
            path = str(Path(origin).resolve())
            if name.split(".")[0] in sys.stdlib_module_names:
                interpreter[path] = auth.file_hash(Path(path))
            else:
                origins[name] = path
                files[path] = auth.file_hash(Path(path))
        elif name.split(".")[0] not in sys.stdlib_module_names:
            origins[name] = "namespace:" + str(
                sorted(str(Path(p).resolve()) for p in getattr(module, "__path__", []))
            )
    for path in (Path(sys._base_executable), *Path(sys.base_prefix).glob("*.dll")):
        interpreter[str(path.resolve())] = auth.file_hash(path)
    return auth.RuntimeIdentity(
        REPO,
        source,
        {"uv.lock": auth.file_hash(REPO / "uv.lock")},
        auth.file_hash(Path(sys.executable)),
        files,
        origins,
        interpreter,
    )


@pytest.fixture
def trial(tmp_path):
    rows = [
        dict(
            game_id=f"reaudit-{i}",
            seed=i,
            pairing_id="reaudit",
            synthetic_review=True,
            orientation="candidate_first" if i < 450 else "opponent_first",
        )
        for i in range(900)
    ]
    raw = auth.encoded(
        dict(
            completed_games=732,
            schedule_games=900,
            schedule_digest=auth.sha256(auth.encoded(rows)),
            records=[dict(game_id=f"reaudit-{i}", evidence=i) for i in range(732)],
        )
    )
    for name in ("reference", "working", "telemetry"):
        (tmp_path / name).mkdir()
    reference = tmp_path / "reference/checkpoint.json"
    reference.write_bytes(raw)
    checkpoint = tmp_path / "working/checkpoint.json"
    checkpoint.write_bytes(raw)
    lease = auth.ReviewLease(
        "new-independent-issuer",
        checkpoint,
        reference,
        tmp_path / "receipts",
        auth.sha256(raw),
        auth.sha256(auth.encoded(rows)),
        identity(),
        b"reaudit-private-test-key-1234567890123",
        telemetry_root=tmp_path / "telemetry",
        telemetry_root_identity=directory_identity(tmp_path / "telemetry"),
    )
    return rows, lease, tmp_path / "telemetry/durable-status.json", raw


def step(trial, executor=None):
    rows, lease, path, _ = trial
    return run_authorized_resume(
        rows,
        executor or (lambda row: dict(game_id=row["game_id"], synthetic_result=True)),
        lease=lease,
        status=path,
        stop_after=1,
    )


@pytest.mark.parametrize("role", ["reference", "working", "nested-reference", "control"])
def test_protected_status_roles_refused_before_writes(trial, role, monkeypatch):
    rows, lease, path, raw = trial
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
    monkeypatch.setattr(
        monitor.tempfile, "mkstemp", lambda **_: pytest.fail("temporary output created")
    )
    with pytest.raises(auth.ResumeRefused):
        step((rows, lease, root / monitor.STATUS_NAME, raw), lambda _: pytest.fail("dispatch"))
    assert lease.reference.read_bytes() == lease.checkpoint.read_bytes() == raw
    assert not Path(str(lease.checkpoint) + ".lock").exists()


def test_original_reference_named_status_is_immutable(trial):
    rows, lease, _, raw = trial
    renamed = lease.reference.with_name(monitor.STATUS_NAME)
    lease.reference.rename(renamed)
    lease = dataclasses.replace(lease, reference=renamed)
    with pytest.raises(auth.ResumeRefused):
        step((rows, lease, renamed, raw))
    assert renamed.read_bytes() == raw


@pytest.mark.parametrize("kind", ["hardlink", "junction", "symlink"])
def test_actual_aliases_are_refused(trial, kind):
    _, lease, path, raw = trial
    grant = lease.validate_outputs(path)
    if kind == "hardlink":
        os.link(lease.reference, path)
    elif kind == "symlink":
        try:
            path.symlink_to(lease.reference)
        except OSError as e:
            pytest.skip(f"Windows symlink privilege unavailable: {e}")
    else:
        if os.name != "nt":
            pytest.skip("native Windows junction")
        path.parent.rename(path.parent.with_name("former-root"))
        created = subprocess.run(
            ["cmd.exe", "/d", "/c", "mklink", "/J", str(path.parent), str(lease.reference.parent)],
            capture_output=True,
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        assert created.returncode == 0, created.stderr
    with pytest.raises(auth.ResumeRefused):
        monitor._read_shared(str(path), grant)
    with pytest.raises(auth.ResumeRefused):
        monitor.publish_status(
            path,
            authorization=lease.authorization_id,
            count=733,
            checkpoint_sha256="a" * 64,
            grant=grant,
        )
    assert lease.reference.read_bytes() == raw


def test_disguised_checkpoint_is_not_monitor_target(trial, monkeypatch):
    rows, lease, path, raw = trial
    disguised = lease.checkpoint.with_name(monitor.STATUS_NAME)
    lease.checkpoint.rename(disguised)
    lease = dataclasses.replace(lease, checkpoint=disguised)
    assert step((rows, lease, path, raw))["completed_games"] == 733
    grant = lease.validate_outputs(path)
    monkeypatch.setattr(
        multiprocessing, "get_context", lambda _: pytest.fail("monitor spawned for checkpoint")
    )
    assert monitor.read_status(disguised, authorization=lease.authorization_id, grant=grant) == {
        "state": "UNKNOWN"
    }


@pytest.mark.parametrize("attack", ["same-version-origin", "same-version-payload", "loader-origin"])
def test_loaded_dependency_substitution_rejected(trial, tmp_path, monkeypatch, attack):
    expected = trial[1].identity
    fake = types.ModuleType("typer")
    fake.__version__ = typer.__version__
    if attack == "same-version-origin":
        path = tmp_path / "foreign.py"
        path.write_bytes(Path(typer.__file__).read_bytes())
        fake.__file__ = str(path)
    elif attack == "loader-origin":
        fake.__file__ = typer.__file__
        fake.__spec__ = importlib.machinery.ModuleSpec(
            "typer", None, origin=str(tmp_path / "other.py")
        )
    else:
        path = tmp_path / "approved-then-altered.py"
        path.write_text('VERSION="same"')
        files = dict(expected.dependency_files)
        files[str(path.resolve())] = auth.file_hash(path)
        origins = dict(expected.dependency_origins)
        origins["typer"] = str(path.resolve())
        expected = dataclasses.replace(expected, dependency_files=files, dependency_origins=origins)
        path.write_text('VERSION="same"; substituted=True')
        fake.__file__ = str(path)
    monkeypatch.setitem(sys.modules, "typer", fake)
    with pytest.raises(auth.ResumeRefused, match="dependency"):
        expected.verify()


def test_continuation_and_completed_prefix(trial):
    rows, lease, path, raw = trial
    calls = []

    def callback(row):
        calls.append(row["game_id"])
        return dict(game_id=row["game_id"])

    one = step(trial, callback)
    fresh = dataclasses.replace(lease, expected_tip=one["receipt_tip"])
    two = step((rows, fresh, path, raw), callback)
    assert (one["completed_games"], two["completed_games"]) == (733, 734)
    assert calls == ["reaudit-732", "reaudit-733"] and lease.reference.read_bytes() == raw


@pytest.mark.parametrize("attack", ["hash", "count", "prefix", "schedule"])
def test_initial_boundary_rejects_mismatch(trial, attack):
    rows, lease, path, raw = trial
    if attack == "hash":
        lease = dataclasses.replace(lease, initial_sha256="0" * 64)
    elif attack == "schedule":
        rows = [dict(r, seed=99999) for r in rows]
    else:
        value = json.loads(raw)
        if attack == "count":
            value["completed_games"] = 731
        else:
            value["records"][-1]["game_id"] = "reaudit-899"
        raw = auth.encoded(value)
        lease.reference.write_bytes(raw)
        lease.checkpoint.write_bytes(raw)
        lease = dataclasses.replace(lease, initial_sha256=auth.sha256(raw))
    with pytest.raises(auth.ResumeRefused):
        step((rows, lease, path, raw), lambda _: pytest.fail("dispatch"))


@pytest.mark.parametrize("phase", ["start", "prepare", "commit"])
def test_interrupted_receipt_does_not_authorize_recovery(trial, monkeypatch, phase):
    rows, lease, path, raw = trial
    append = auth.Receipts.append

    def interrupted(self, name, **fields):
        if name == phase:
            # Model a partial durable event rather than merely an unwritten intent.
            self.lease.control.mkdir(exist_ok=True)
            (self.lease.control / f"{len(self.events):06d}.json").write_bytes(b'{"partial":')
            raise OSError("synthetic interruption")
        return append(self, name, **fields)

    monkeypatch.setattr(auth.Receipts, "append", interrupted)
    with pytest.raises(OSError):
        step(trial)
    monkeypatch.undo()
    with pytest.raises((ValueError, auth.ResumeRefused)):
        step((rows, dataclasses.replace(lease), path, raw), lambda _: pytest.fail("replay"))
    assert lease.reference.read_bytes() == raw


@pytest.mark.parametrize("attack", ["stale", "forged", "missing", "rollback"])
def test_trusted_tip_and_receipt_bindings(trial, attack):
    rows, lease, path, raw = trial
    first = step(trial)
    renewed = dataclasses.replace(lease, expected_tip=first["receipt_tip"])
    receipt = lease.control / "000002.json"
    if attack == "stale":
        renewed = dataclasses.replace(lease)
    elif attack == "missing":
        receipt.unlink()
    elif attack == "rollback":
        lease.checkpoint.write_bytes(raw)
    else:
        value = json.loads(receipt.read_bytes())
        value["checkpoint_sha256"] = "0" * 64
        receipt.write_bytes(auth.encoded(value))
    with pytest.raises(auth.ResumeRefused):
        step((rows, renewed, path, raw), lambda _: pytest.fail("replay"))


def test_competing_writer(trial):
    with (
        integrity.WriterLock(trial[1].checkpoint, "reaudit-competitor", hold_handle=True),
        pytest.raises(integrity.CheckpointIntegrityError),
    ):
        step(trial, lambda _: pytest.fail("dispatch"))


class Backend:
    def __init__(self, mode, args):
        self.mode, self.args = mode, args
        self.pid = None
        self.exitcode = None
        self.alive = False
        self.closed = threading.Event()
        self.terminated = threading.Event()
        self.exited = threading.Event()

    def start(self):
        if self.mode in ("late-exit", "startup"):
            time.sleep(0.12)
        self.pid = 4242
        self.alive = True
        if self.mode == "send":
            self.args[-1][:4] = (200).to_bytes(4, "little")

    def join(self, timeout):
        assert 0 <= timeout <= 0.25
        if self.alive:
            self.exited.wait(timeout)

    def is_alive(self):
        return self.alive

    def terminate(self):
        self.terminated.set()
        if self.mode == "termination-error":
            raise PermissionError("injected termination denial")
        if self.mode == "termination-delay":
            time.sleep(0.35)
        if self.mode == "late-exit":

            def exit_later():
                self.alive = False
                self.exitcode = -1
                self.exited.set()

            timer = threading.Timer(0.06, exit_later)
            timer.daemon = True
            timer.start()
            return
        self.alive = False
        self.exitcode = -1
        self.exited.set()

    def close(self):
        self.closed.set()


@pytest.mark.parametrize(
    "mode", ["startup", "read", "send", "termination-delay", "late-exit", "termination-error"]
)
def test_entire_deadline_and_cleanup(tmp_path, monkeypatch, mode):
    workers = []

    class Context:
        def RawArray(self, _, size):
            return bytearray(size)

        def Process(self, args, **_):
            worker = Backend(mode, args)
            workers.append(worker)
            return worker

    grant = TelemetryGrant(
        tmp_path, directory_identity(tmp_path), (tmp_path.parent / "protected-role",), "reaudit"
    )
    monkeypatch.setattr(multiprocessing, "get_context", lambda _: Context())
    began = time.monotonic()
    observed = monitor.read_status(
        tmp_path / monitor.STATUS_NAME, authorization="reaudit", grant=grant, timeout=0.05
    )
    elapsed = time.monotonic() - began
    assert observed == {"state": "UNKNOWN"}
    assert elapsed < 0.15, f"{mode}: {elapsed:.3f}s exceeded the 50ms supervisory budget"
    assert workers[0].closed.wait(0.45), f"{mode}: child/handle was never closed after cleanup"
    assert not workers[0].is_alive(), f"{mode}: child remains alive"


@pytest.fixture(autouse=True)
def release_disposable_backend_after_assertions():
    # Test-only external exit after assertions: do not leak a synthetic backend
    # into another test. Never force-clear ownership of an actual OS process.
    yield
    import tmnt_design_studio.monitor_cleanup as lifecycle
    from tmnt_design_studio.monitor_cleanup import cleanup_status

    owner = lifecycle._OWNER
    if owner and owner.worker is not None and isinstance(owner.worker, Backend):
        owner.worker.alive = False
        owner.worker.exited.set()
        cleanup_status(refresh=True)
        assert owner.closed.wait(1), "fixture cleanup failed"
