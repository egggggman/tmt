"""Independent acceptance predicates; synthetic boundary fixtures, no game calls."""

import errno
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from tmnt_design_studio import calibration_integrity as storage
from tmnt_design_studio import fresh900 as runner
from tmnt_design_studio import fresh900_identity as identity
from tmnt_design_studio.fresh900_monitor import MonitorLocation, read_status


class FixtureStop(RuntimeError):
    pass


def rows():
    return [
        dict(
            game_id=f"audit-{i}",
            pairing_id="audit-pair",
            orientation="candidate_first" if i == 0 else "opponent_first",
            seed=700 + i,
            seats=["candidate", "opponent"],
        )
        for i in range(2)
    ]


def record(row):
    return dict(
        game_id=row["game_id"],
        synthetic=True,
        terminal=True,
        winner="candidate",
        turn=10,
        invariant_violations=[],
        stop_records=[],
        events=[{"kind": "synthetic", "value": 17}],
        stage002_presence=[],
        rules_event_evidence=[],
    )


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    # Isolate runner boundary behavior from independent real environment checks.
    # Two rows shorten fault injection; the real 900-row identity is tested separately.
    source = tmp_path / "source"
    source.mkdir()
    input_file = source / "fixture.txt"
    input_file.write_bytes(b"approved synthetic input\n")
    plan = dict(
        protocol="fresh900-plan-v1",
        games=900,
        run_id="FRESH_900_independent_fixture",
        output=str(tmp_path / "FRESH_900_independent_fixture"),
        protected=[str(tmp_path / "history")],
        runtime={"source": str(source)},
        inputs={str(input_file): identity.file_hash(input_file)},
        schedule=rows(),
    )

    def verify(p):
        assert p["schedule"] == rows()
        identity.verify_inventory(p["inputs"])

    monkeypatch.setattr(runner, "verify_plan", verify)
    import shutil
    import types

    monkeypatch.setattr(shutil, "disk_usage", lambda _: types.SimpleNamespace(free=40 * 2**30))
    return plan


def execute(plan, callback=record, approval_change=None, pin_change=False):
    approval = dict(
        action="synthetic-review",
        approved_by="independent fixture",
        plan_sha256=identity.digest(plan),
    )
    if approval_change:
        approval.update(approval_change)
    pin = identity.digest(approval) if not pin_change else "f" * 64
    return runner.run_synthetic(
        plan,
        approval,
        expected_authorization_sha256=pin,
        executor=callback,
        measure=lambda: dict(physical=8 * 2**30, commit=8 * 2**30),
    )


def checkpoint(plan):
    return Path(plan["output"]) / "checkpoints/checkpoint.json"


def test_positive_boundary_preserves_details(fixture):
    answer = execute(fixture)
    assert answer["completed_games"] == 2
    saved = json.loads(checkpoint(fixture).read_bytes())
    assert saved["records"][0]["events"] == [{"kind": "synthetic", "value": 17}]
    with pytest.raises(identity.FreshRefused):
        execute(fixture)


@pytest.mark.parametrize(
    "change,pin",
    [
        (dict(action="fresh-start"), False),
        (dict(approved_by=""), False),
        (dict(plan_sha256="0" * 64), False),
        ({}, True),
    ],
)
def test_approval_refusal_before_writes(fixture, change, pin):
    with pytest.raises(identity.FreshRefused):
        execute(fixture, approval_change=change, pin_change=pin)
    assert not Path(fixture["output"]).exists()


def test_direct_historical_path_refused(fixture, tmp_path):
    prior = tmp_path / "history/checkpoint.json"
    prior.parent.mkdir()
    prior.write_bytes(b"preserved reference")
    fixture["output"] = str(prior)
    with pytest.raises(identity.FreshRefused):
        execute(fixture)
    assert prior.read_bytes() == b"preserved reference"


def test_normal_protected_overlap_refused(fixture, tmp_path):
    protected = tmp_path / "history"
    protected.mkdir()
    fixture["output"] = str(protected / fixture["run_id"])
    with pytest.raises(identity.FreshRefused):
        execute(fixture)
    assert list(protected.iterdir()) == []


@pytest.mark.skipif(os.name != "nt", reason="Windows extended namespace")
def test_extended_namespace_cannot_bypass_protected_overlap(fixture, tmp_path):
    protected = tmp_path / "history"
    protected.mkdir()
    fixture["output"] = "\\\\?\\" + str(protected / fixture["run_id"])
    assert os.path.samefile(Path(fixture["output"]).parent, protected)
    try:  # noqa: SIM105 -- preserve the original independent predicate AST
        execute(fixture, lambda row: (_ for _ in ()).throw(FixtureStop("dispatch reached")))
    except (identity.FreshRefused, FixtureStop):
        pass
    assert not Path(fixture["output"]).exists(), "protected-root alias was written before refusal"


@pytest.mark.parametrize(
    "field,bad", [("seed", 999999), ("orientation", "wrong"), ("pairing_id", "foreign")]
)
def test_conflicting_result_identity_is_not_committed(fixture, field, bad):
    def callback(row):
        if row["game_id"] == rows()[1]["game_id"]:
            raise FixtureStop("after first result")
        return {**record(row), field: bad}

    try:  # noqa: SIM105 -- preserve the original independent predicate AST
        execute(fixture, callback)
    except (identity.FreshRefused, FixtureStop):
        pass
    saved = json.loads(checkpoint(fixture).read_bytes())
    assert saved["completed_games"] == 0, f"conflicting {field} was accepted and committed"


@pytest.mark.parametrize(
    "field,bad",
    [
        ("terminal", False),
        ("winner", None),
        ("turn", 121),
        ("game_id", "foreign"),
        ("events", None),
    ],
)
def test_incomplete_record_is_not_committed(fixture, field, bad):
    with pytest.raises(identity.FreshRefused):
        execute(fixture, lambda row: {**record(row), field: bad})
    assert json.loads(checkpoint(fixture).read_bytes())["completed_games"] == 0


def test_final_checkpoint_content_must_match_accepted_records(fixture, monkeypatch):
    original = storage.os.replace

    def corrupt(source, destination):
        original(source, destination)
        if Path(destination).name == "checkpoint.json":
            data = json.loads(Path(destination).read_bytes())
            if data["records"]:
                data["records"][0]["events"][0]["value"] = 999
                Path(destination).write_text(json.dumps(data))

    monkeypatch.setattr(storage.os, "replace", corrupt)
    with pytest.raises((identity.FreshRefused, storage.CheckpointIntegrityError)):
        execute(fixture)


def test_primary_error_survives_lock_cleanup_error(fixture, monkeypatch):
    original = storage.os.unlink
    primary = RuntimeError("PRIMARY_EXECUTOR_FAILURE")

    def unlink(path, *args, **kwargs):
        if str(path).endswith(".lock"):
            raise PermissionError(errno.EACCES, "SECONDARY_LOCK_CLEANUP_FAILURE")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(storage.os, "unlink", unlink)
    caught = None
    try:
        execute(fixture, lambda row: (_ for _ in ()).throw(primary))
    except BaseException as error:
        caught = error
    failure = json.loads((Path(fixture["output"]) / "failures/stop.json").read_bytes())
    assert caught is primary and "PRIMARY_EXECUTOR_FAILURE" in json.dumps(failure), (
        f"caller received {type(caught).__name__}; failure record loses primary error: {failure}"
    )


def test_replacement_denial_preserves_original_bytes_and_error(tmp_path, monkeypatch):
    target = tmp_path / "checkpoint.json"
    acc = storage.CheckpointAccumulator(rows(), writer_id="audit")
    acc.write(target, writer_id="audit", return_snapshot=False)
    before = target.read_bytes()
    acc.append(record(rows()[0]), writer_id="audit")
    failure = PermissionError(errno.EACCES, "original replacement failure")
    with (
        patch.object(storage.os, "replace", side_effect=failure) as replace,
        patch.object(storage.time, "sleep"),
        pytest.raises(PermissionError) as error,
    ):
        acc.write(target, writer_id="audit", return_snapshot=False)
    assert error.value is failure and replace.call_count == 8
    assert target.read_bytes() == before


def test_cooperative_second_writer_rejected(tmp_path):
    path = tmp_path / "checkpoint.json"
    with storage.WriterLock(path, "one"), pytest.raises(storage.CheckpointIntegrityError):
        storage.WriterLock(path, "two").acquire()


def test_monitor_alias_and_protocol_refused(tmp_path):
    root = tmp_path / "FRESH_900_independent_monitor"
    telemetry = root / "telemetry"
    telemetry.mkdir(parents=True)
    protected = root / "checkpoints"
    protected.mkdir()
    info = telemetry.stat()
    loc = MonitorLocation(telemetry, (info.st_dev, info.st_ino), root.name, (protected,))
    target = protected / "checkpoint.json"
    target.write_text(
        json.dumps(
            dict(
                protocol=runner.PROTOCOL,
                run_id=root.name,
                synthetic=True,
                state="RUNNING",
                committed_games=1,
                heartbeat=time.time(),
            )
        )
    )
    os.link(target, telemetry / "status.json")
    assert read_status(loc) == {"state": "UNKNOWN"}


def test_same_version_file_substitution_rejected(tmp_path):
    path = tmp_path / "dependency.py"
    path.write_text('__version__="1.0"\nvalue=1\n')
    seal = {str(path): identity.file_hash(path)}
    path.write_text('__version__="1.0"\nvalue=2\n')
    with pytest.raises(identity.FreshRefused):
        identity.verify_inventory(seal)


def test_actual_900_frozen_schedule_and_inputs():
    import subprocess

    git = "C:/Program Files/Git/cmd/git.exe" if os.name == "nt" else "git"
    repo = Path(__file__).resolve().parents[1]
    sha = "45311dadd1c14e0c183c86085b47e8d3dd670b6f"
    for name, expected in identity.FROZEN_INPUTS.items():
        data = subprocess.check_output(
            [git, "-c", f"safe.directory={repo.as_posix()}", "show", f"{sha}:{name}"], cwd=repo
        )
        assert hashlib.sha256(data).hexdigest() == expected
    # Invoke only the plan's schedule comparison with a frozen-input/runtime seam.
    source = repo
    manifest = json.loads(
        subprocess.check_output(
            [
                git,
                "-c",
                f"safe.directory={repo.as_posix()}",
                "show",
                sha + ":docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json",
            ],
            cwd=repo,
        )
    )
    schedule = []
    for index, opponent in enumerate(
        sorted(r["deck_key"] for r in manifest["decks"] if r["deck_key"] != "bebop_rocksteady")
    ):
        for j in range(100):
            seed = 1000000 + index * 100 + j
            orientation = "candidate_first" if j < 50 else "opponent_first"
            schedule.append(
                dict(
                    game_id=f"bad_guys_cronies_sandbox_0_2--{opponent}:{orientation}:{seed}",
                    pairing_id=f"bebop_rocksteady--{opponent}",
                    opponent=opponent,
                    orientation=orientation,
                    seed=seed,
                    seats=["bad_guys_cronies_sandbox_0_2", opponent]
                    if j < 50
                    else [opponent, "bad_guys_cronies_sandbox_0_2"],
                )
            )
    plan = dict(
        protocol="fresh900-plan-v1",
        games=900,
        runtime={"source": str(source)},
        inputs={str(source / p): h for p, h in identity.FROZEN_INPUTS.items()},
        schedule=schedule,
    )
    with patch.object(identity, "verify_runtime"), patch.object(identity, "verify_inventory"):
        identity.verify_plan(plan)
        plan["schedule"][0]["seed"] += 1
        with pytest.raises(identity.FreshRefused):
            identity.verify_plan(plan)
    assert len(schedule) == 900


@pytest.mark.skipif(os.name != "nt", reason="native Windows handle semantics")
@pytest.mark.parametrize("held_role", ["status", "checkpoint"])
def test_native_windows_held_reader_behavior(tmp_path, held_role):
    import ctypes
    from ctypes import wintypes

    parent = tmp_path / "FRESH_900_native_audit"
    telemetry = parent / "telemetry"
    telemetry.mkdir(parents=True)
    control = parent / "checkpoints"
    control.mkdir()
    path = control / "checkpoint.json"
    acc = storage.CheckpointAccumulator(rows(), writer_id="audit")
    acc.write(path, writer_id="audit", return_snapshot=False)
    old = path.read_bytes()
    status = telemetry / "status.json"
    status.write_text(
        json.dumps(
            dict(
                protocol=runner.PROTOCOL,
                run_id=parent.name,
                state="RUNNING",
                synthetic=True,
                committed_games=0,
                heartbeat=time.time(),
            )
        )
    )
    target = status if held_role == "status" else path
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.CreateFileW(str(target), 0x80000000, 3, None, 3, 0, None)
    assert handle != wintypes.HANDLE(-1).value
    acc.append(record(rows()[0]), writer_id="audit")
    try:
        if held_role == "checkpoint":
            with pytest.raises(PermissionError) as caught:
                acc.write(path, writer_id="audit", return_snapshot=False)
            assert caught.value.winerror in (5, 32) and path.read_bytes() == old
        else:
            acc.write(path, writer_id="audit", return_snapshot=False)
            assert json.loads(path.read_bytes())["completed_games"] == 1
            info = control.stat()
            bad = MonitorLocation(control, (info.st_dev, info.st_ino), parent.name, (control,))
            with patch.object(Path, "open", side_effect=AssertionError("monitor attempted open")):
                assert read_status(bad) == {"state": "UNKNOWN"}
    finally:
        kernel.CloseHandle(handle)
    if held_role == "checkpoint":
        acc.write(path, writer_id="audit", return_snapshot=False)
        assert json.loads(path.read_bytes())["completed_games"] == 1


def test_independent_process_ownership_and_interrupted_lock(tmp_path):
    import subprocess

    repo = Path(__file__).resolve().parents[1]
    target = tmp_path / "checkpoint.json"
    ready = tmp_path / "child-ready"
    code = """
import sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from tmnt_design_studio.calibration_integrity import WriterLock
WriterLock(Path(sys.argv[2]),'independent-child').acquire()
Path(sys.argv[3]).write_text('owned')
sys.stdin.read()
"""
    child = subprocess.Popen(
        [sys.executable, "-B", "-c", code, str(repo / "src"), str(target), str(ready)],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=0x08000000 if os.name == "nt" else 0,
    )
    try:
        deadline = time.monotonic() + 5
        while not ready.exists() and child.poll() is None and time.monotonic() < deadline:
            time.sleep(0.02)
        assert ready.exists()
        with pytest.raises(storage.CheckpointIntegrityError):
            storage.WriterLock(target, "competitor").acquire()
        child.kill()
        child.wait(timeout=5)
        with pytest.raises(storage.CheckpointIntegrityError):
            storage.WriterLock(target, "competitor").acquire()
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=5)
        child.stdin.close()
