from __future__ import annotations

import copy
import errno
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from tmnt_design_studio import calibration_integrity as persistence
from tmnt_design_studio import fresh900 as runner
from tmnt_design_studio import fresh900_identity as identity
from tmnt_design_studio.fresh900_identity import FreshRefused, digest, file_hash
from tmnt_design_studio.fresh900_monitor import MonitorLocation, read_status

ROOT = Path(__file__).resolve().parents[1]
GIT = "C:/Program Files/Git/cmd/git.exe" if os.name == "nt" else "git"


def schedule():
    # AST-extracted schedule is independent of the production constructor.
    import ast

    node = next(
        n
        for n in ast.parse((ROOT / "tools/run_bad_guys_initial_calibration.py").read_text()).body
        if isinstance(n, ast.FunctionDef) and n.name == "build_schedule"
    )
    namespace = dict(
        Path=Path,
        ROOT=ROOT,
        json=json,
        MANIFEST_PATH="docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json",
        GAMES_PER_MATCHUP=100,
        EXPECTED_GAMES=900,
        EXPECTED_MATCHUPS=9,
        validate_schedule=persistence.validate_schedule,
    )
    exec(compile(ast.Module(body=[node], type_ignores=[]), "<schedule-only>", "exec"), namespace)
    return namespace["build_schedule"]()


def result(row):
    return dict(
        game_id=row["game_id"],
        synthetic=True,
        terminal=True,
        winner=row["seats"][0],
        turn=12,
        invariant_violations=[],
        stop_records=[],
        events=[{"kind": "synthetic", "detail": "preserve me"}],
        stage002_presence=[],
        rules_event_evidence=[],
    )


@pytest.fixture
def contract(tmp_path, monkeypatch):
    # Runner/persistence fixtures do not pretend to attest the test interpreter.
    # Real runtime/import checks are separately exercised below without this seam.
    monkeypatch.setattr(identity, "verify_runtime", lambda runtime: None)
    source = tmp_path / "source"
    source.mkdir()
    sample = source / "input.txt"
    sample.write_bytes(b"frozen synthetic input\n")
    monkeypatch.setattr(identity, "FROZEN_INPUTS", {"input.txt": file_hash(sample)})
    plan = dict(
        protocol="fresh900-plan-v1",
        games=900,
        run_id="FRESH_900_synthetic_test",
        output=str(tmp_path / "FRESH_900_synthetic_test"),
        protected=[str(tmp_path / "historical")],
        runtime={"source": str(source)},
        inputs={str(sample): file_hash(sample)},
        schedule=schedule(),
    )
    approval = dict(action="synthetic-review", approved_by="fixture-only", plan_sha256=digest(plan))
    return plan, approval


def run(contract, executor=result):
    plan, approval = contract
    return runner.run_synthetic(
        plan,
        approval,
        expected_authorization_sha256=digest(approval),
        executor=executor,
        measure=lambda: dict(physical=10 * 2**30, commit=10 * 2**30),
    )


def test_full_900_complete_no_replay(contract):
    calls = []

    def execute(row):
        assert row["game_id"] not in calls
        calls.append(row["game_id"])
        return result(row)

    summary = run(contract, execute)
    assert summary["completed_games"] == 900 and len(calls) == 900
    root = Path(contract[0]["output"])
    saved = json.loads((root / "checkpoints/checkpoint.json").read_bytes())
    assert [r["game_id"] for r in saved["records"]] == [r["game_id"] for r in schedule()]
    assert saved["records"][0]["events"][0]["detail"] == "preserve me"
    with pytest.raises(FreshRefused, match="unused"):
        run(contract, lambda row: pytest.fail("replay"))


@pytest.mark.parametrize("mode", ["missing", "live", "wrong-plan", "wrong-pin"])
def test_approval_before_any_output(contract, mode):
    plan, approval = contract
    pin = digest(approval)
    if mode == "missing":
        approval.pop("approved_by")
    elif mode == "live":
        approval["action"] = "fresh-start"
    elif mode == "wrong-plan":
        approval["plan_sha256"] = "0" * 64
    else:
        pin = "0" * 64
    if mode != "wrong-pin":
        pin = digest(approval)
    with pytest.raises(FreshRefused):
        runner.run_synthetic(
            plan,
            approval,
            expected_authorization_sha256=pin,
            executor=lambda row: pytest.fail("dispatch"),
        )
    assert not Path(plan["output"]).exists()


@pytest.mark.parametrize("mode", ["seed", "duplicate", "reorder", "input"])
def test_frozen_inputs_and_schedule(contract, mode):
    plan, approval = contract
    if mode == "seed":
        plan["schedule"][0]["seed"] += 1
    elif mode == "duplicate":
        plan["schedule"][1] = copy.deepcopy(plan["schedule"][0])
    elif mode == "reorder":
        plan["schedule"].reverse()
    else:
        next(iter(plan["inputs"]))
        Path(next(iter(plan["inputs"]))).write_bytes(b"tampered")
    approval["plan_sha256"] = digest(plan)
    with pytest.raises(FreshRefused):
        run(contract)
    assert not Path(plan["output"]).exists()


@pytest.mark.parametrize(
    "field,value",
    [
        ("terminal", False),
        ("winner", None),
        ("game_id", "wrong"),
        ("invariant_violations", ["bad"]),
        ("stop_records", ["turn_limit"]),
        ("events", None),
        ("synthetic", False),
        ("turn", 121),
    ],
)
def test_invalid_result_stops_without_credit(contract, field, value):
    calls = []

    def execute(row):
        calls.append(row)
        return {**result(row), field: value}

    with pytest.raises(FreshRefused):
        run(contract, execute)
    root = Path(contract[0]["output"])
    assert len(calls) == 1
    assert json.loads((root / "checkpoints/checkpoint.json").read_bytes())["completed_games"] == 0
    assert (
        json.loads((root / "failures/stop.json").read_bytes())["recovery"]
        == "STOPPED_REVIEW_REQUIRED"
    )


def test_executor_exception_never_retried(contract):
    calls = []

    def fail(row):
        calls.append(row)
        raise RuntimeError("interrupted synthetic fixture")

    with pytest.raises(RuntimeError):
        run(contract, fail)
    assert len(calls) == 1


def test_ambiguous_status_failure_retains_advanced_checkpoint(contract, monkeypatch):
    real = runner.atomic_json

    def fail(path, value):
        if path.name == "status.json" and value["committed_games"] == 1:
            raise PermissionError(13, "held synthetic status reader")
        real(path, value)

    monkeypatch.setattr(runner, "atomic_json", fail)
    with pytest.raises(PermissionError):
        run(contract)
    root = Path(contract[0]["output"])
    assert json.loads((root / "checkpoints/checkpoint.json").read_bytes())["completed_games"] == 1
    assert json.loads((root / "failures/stop.json").read_bytes())["stage"] == "STATUS"
    with pytest.raises(FreshRefused):
        run(contract)


def test_replace_exhaustion_preserves_original(tmp_path):
    path = tmp_path / "checkpoint.json"
    acc = persistence.CheckpointAccumulator(schedule(), writer_id="test")
    acc.write(path, writer_id="test", return_snapshot=False)
    before = path.read_bytes()
    acc.append(result(schedule()[0]), writer_id="test")
    error = PermissionError(errno.EACCES, "synthetic denied")
    with (
        patch.object(persistence.os, "replace", side_effect=error) as replace,
        patch.object(persistence.time, "sleep") as sleep,
        pytest.raises(PermissionError) as caught,
    ):
        acc.write(path, writer_id="test", return_snapshot=False)
    assert caught.value is error
    assert replace.call_count == 8 and sleep.call_count == 7
    assert path.read_bytes() == before


def test_transient_replace_retries_same_flushed_file(tmp_path):
    path = tmp_path / "checkpoint.json"
    real = persistence.os.replace
    sources = []

    def replace(source, destination):
        sources.append(source)
        assert Path(source).read_bytes().endswith(b"\n")
        if len(sources) < 3:
            raise PermissionError(errno.EACCES, "transient")
        real(source, destination)

    acc = persistence.CheckpointAccumulator(schedule(), writer_id="test")
    with (
        patch.object(persistence.os, "replace", side_effect=replace),
        patch.object(persistence.time, "sleep"),
    ):
        acc.write(path, writer_id="test", return_snapshot=False)
    assert len(sources) == 3 and len(set(sources)) == 1


def location(tmp_path):
    root = tmp_path / "FRESH_900_monitor_test"
    telemetry = root / "telemetry"
    telemetry.mkdir(parents=True)
    checkpoints = root / "checkpoints"
    checkpoints.mkdir()
    info = telemetry.stat()
    loc = MonitorLocation(telemetry, (info.st_dev, info.st_ino), root.name, (checkpoints,))
    runner.atomic_json(
        telemetry / "status.json",
        dict(
            protocol=runner.PROTOCOL,
            run_id=root.name,
            synthetic=True,
            state="RUNNING",
            committed_games=1,
            heartbeat=time.time(),
        ),
    )
    return loc


def test_monitor_status_only_readonly(tmp_path):
    loc = location(tmp_path)
    path = loc.root / "status.json"
    before = path.read_bytes()
    assert read_status(loc)["state"] == "REPORTED_ONLY"
    assert path.read_bytes() == before
    checkpoint = loc.root.parent / "checkpoints/status.json"
    checkpoint.write_bytes(before)
    info = checkpoint.parent.stat()
    wrong = MonitorLocation(
        checkpoint.parent, (info.st_dev, info.st_ino), loc.run_id, loc.protected
    )
    assert read_status(wrong) == {"state": "UNKNOWN"}


def test_disguised_checkpoint_hardlink_rejected(tmp_path):
    loc = location(tmp_path)
    path = loc.root / "status.json"
    checkpoint = loc.root.parent / "checkpoints/checkpoint.json"
    path.replace(checkpoint)
    os.link(checkpoint, path)
    assert read_status(loc) == {"state": "UNKNOWN"}
    assert checkpoint.read_bytes() == path.read_bytes()


@pytest.mark.parametrize(
    "field,value",
    [("protocol", "wrong"), ("run_id", "foreign"), ("heartbeat", 0), ("committed_games", 901)],
)
def test_invalid_status_unknown(tmp_path, field, value):
    loc = location(tmp_path)
    path = loc.root / "status.json"
    data = json.loads(path.read_bytes())
    data[field] = value
    runner.atomic_json(path, data)
    assert read_status(loc) == {"state": "UNKNOWN"}


@pytest.mark.parametrize("field", ["physical", "commit"])
def test_unchanged_resource_gate(tmp_path, field):
    sample = dict(physical=runner.MEMORY_GATE, commit=runner.MEMORY_GATE)
    sample[field] -= 1
    with pytest.raises(FreshRefused):
        runner.check_resources(tmp_path, lambda: sample)
    assert runner.MEMORY_GATE == 2_997_492_240


def test_same_version_payload_substitution(tmp_path):
    file = tmp_path / "package.py"
    file.write_text('__version__="1.0"\nvalue="approved"\n')
    approved = {str(file): file_hash(file)}
    identity.verify_inventory(approved)
    file.write_text('__version__="1.0"\nvalue="substituted"\n')
    with pytest.raises(FreshRefused, match="payload mismatch"):
        identity.verify_inventory(approved)


def test_cross_process_writer_and_stale_lock(tmp_path):
    path = tmp_path / "checkpoint.json"
    code = (
        "import sys; from pathlib import Path; "
        "from tmnt_design_studio.calibration_integrity import WriterLock; "
        "WriterLock(Path(sys.argv[1]),'child').acquire(); print('CLAIMED',flush=True); "
        "sys.stdin.read()"
    )
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src"), "PYTHONDONTWRITEBYTECODE": "1"}
    proc = subprocess.Popen(
        [sys.executable, "-B", "-c", code, str(path)],
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=0x08000000 if os.name == "nt" else 0,
    )
    try:
        assert proc.stdout.readline().strip() == b"CLAIMED"
        with pytest.raises(persistence.CheckpointIntegrityError):
            persistence.WriterLock(path, "other").acquire()
        proc.kill()
        proc.wait(timeout=5)
        with pytest.raises(persistence.CheckpointIntegrityError):
            persistence.WriterLock(path, "other").acquire()
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)
        for handle in (proc.stdin, proc.stdout, proc.stderr):
            handle.close()


def runtime_contract():
    import importlib.util

    files = {}
    for module in tuple(sys.modules.values()):
        name = getattr(module, "__file__", None)
        if name:
            path = Path(name).absolute()
            if path.suffix == ".pyc":
                path = Path(importlib.util.source_from_cache(str(path)))
            files[str(path)] = file_hash(path)
        cached = getattr(module, "__cached__", None)
        if cached and Path(cached).exists():
            files[str(Path(cached).absolute())] = file_hash(Path(cached))
    for path in (sys.executable, sys._base_executable):
        files[path] = file_hash(Path(path))
    commit = subprocess.check_output(
        [GIT, "-c", f"safe.directory={ROOT.as_posix()}", "-C", str(ROOT), "rev-parse", "HEAD"],
        text=True,
    ).strip()
    return dict(
        version=sys.version,
        executable=sys.executable,
        base_executable=sys._base_executable,
        source=str(ROOT),
        source_commit=commit,
        git_executable=GIT,
        files=files,
    )


@pytest.mark.skipif(os.name != "nt", reason="Windows interpreter/import seal")
def test_actual_loaded_imports_are_verified():
    identity.verify_runtime(runtime_contract())


@pytest.mark.skipif(os.name != "nt", reason="Windows interpreter/import seal")
def test_actual_loaded_same_version_substitution_rejected(tmp_path, monkeypatch):
    import types

    path = tmp_path / "substituted.py"
    path.write_text('__version__="1.0"\nvalue="approved"\n')
    module = types.ModuleType("synthetic_dependency")
    module.__file__ = str(path)
    module.__version__ = "1.0"
    monkeypatch.setitem(sys.modules, "synthetic_dependency", module)
    runtime = runtime_contract()
    path.write_text('__version__="1.0"\nvalue="changed"\n')
    with pytest.raises(FreshRefused, match="payload mismatch"):
        identity.verify_runtime(runtime)


@pytest.mark.skipif(os.name != "nt", reason="Windows interpreter/import seal")
def test_project_import_outside_source_rejected(tmp_path, monkeypatch):
    import types

    path = tmp_path / "main_substitute.py"
    path.write_text("pass\n")
    module = types.ModuleType("tmnt_design_studio.substitute")
    module.__file__ = str(path)
    monkeypatch.setitem(sys.modules, "tmnt_design_studio.substitute", module)
    with pytest.raises(FreshRefused, match="outside approved source"):
        identity.verify_runtime(runtime_contract())


@pytest.mark.parametrize("phase", ["before-flush", "after-flush", "after-replace", "after-write"])
def test_actual_process_interruption_preserves_valid_old_or_new(tmp_path, phase):
    path = tmp_path / "checkpoint.json"
    acc = persistence.CheckpointAccumulator(schedule(), writer_id="parent")
    acc.write(path, writer_id="parent", return_snapshot=False)
    rows = tmp_path / "schedule.json"
    rows.write_text(json.dumps(schedule()))
    code = """
import json,sys
from pathlib import Path
import tmnt_design_studio.calibration_integrity as c
path, rows, phase = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
def pause():
    print('BOUNDARY',flush=True)
    sys.stdin.read()
schedule=json.loads(rows.read_bytes())
acc=c.CheckpointAccumulator(schedule,writer_id='child')
acc.append(dict(game_id=schedule[0]['game_id'],synthetic=True),writer_id='child')
real_replace=c.os.replace
real_dump=c.json.dump
def replace(source,destination):
    if phase=='after-flush': pause()
    real_replace(source,destination)
    if phase=='after-replace': pause()
def dump(*args,**kwargs):
    if phase=='before-flush': pause()
    return real_dump(*args,**kwargs)
c.os.replace=replace
c.json.dump=dump
acc.write(path,writer_id='child',return_snapshot=False)
pause()
"""
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src"), "PYTHONDONTWRITEBYTECODE": "1"}
    proc = subprocess.Popen(
        [sys.executable, "-B", "-c", code, str(path), str(rows), phase],
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=0x08000000 if os.name == "nt" else 0,
    )
    try:
        assert proc.stdout.readline().strip() == b"BOUNDARY"
        proc.kill()
        proc.wait(timeout=5)
        saved = json.loads(path.read_bytes())
        persistence.validate_checkpoint(saved, schedule())
        assert saved["completed_games"] == (1 if phase in ("after-replace", "after-write") else 0)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)
        for handle in (proc.stdin, proc.stdout, proc.stderr):
            handle.close()


@pytest.mark.skipif(os.name != "nt", reason="native Windows held reader")
def test_windows_held_status_handle_does_not_block_checkpoint(tmp_path):
    import ctypes
    from ctypes import wintypes

    loc = location(tmp_path)
    api = ctypes.WinDLL("kernel32", use_last_error=True)
    api.CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    api.CreateFileW.restype = wintypes.HANDLE
    api.CloseHandle.argtypes = [wintypes.HANDLE]
    # Intentionally deny FILE_SHARE_DELETE: status replacement may fail, while
    # checkpoint replacement must succeed with this handle held throughout.
    handle = api.CreateFileW(str(loc.root / "status.json"), 0x80000000, 3, None, 3, 0, None)
    assert handle != wintypes.HANDLE(-1).value
    try:
        path = loc.root.parent / "checkpoints/checkpoint.json"
        acc = persistence.CheckpointAccumulator(schedule(), writer_id="test")
        for row in schedule()[:5]:
            acc.append(result(row), writer_id="test")
            acc.write(path, writer_id="test", return_snapshot=False)
        assert json.loads(path.read_bytes())["completed_games"] == 5
    finally:
        api.CloseHandle(handle)


def test_symlink_output_rejected_before_output(contract):
    plan, approval = contract
    destination = Path(plan["output"])
    target = destination.parent / "separate"
    target.mkdir()
    try:
        destination.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("native symlink creation privilege unavailable")
    with pytest.raises(FreshRefused):
        run(contract)
    assert list(target.iterdir()) == []


def test_protected_overlap_before_writes(contract):
    plan, approval = contract
    plan["protected"] = [str(Path(plan["output"]).parent)]
    approval["plan_sha256"] = digest(plan)
    with pytest.raises(FreshRefused, match="overlap"):
        run(contract)
    assert not Path(plan["output"]).exists()


def test_telemetry_transient_replacement_is_bounded(tmp_path):
    path = tmp_path / "status.json"
    runner.atomic_json(path, {"old": True})
    real = persistence.os.replace
    calls = []

    def replace(source, destination):
        calls.append(source)
        if len(calls) < 3:
            raise PermissionError(errno.EACCES, "transient status contention")
        real(source, destination)

    with (
        patch.object(persistence.os, "replace", side_effect=replace),
        patch.object(persistence.time, "sleep"),
    ):
        runner.atomic_json(path, {"new": True})
    assert len(calls) == 3 and len(set(calls)) == 1
    assert json.loads(path.read_bytes()) == {"new": True}


def test_disk_reserve_failure_before_reservation(contract, monkeypatch):
    import shutil
    import types

    monkeypatch.setattr(shutil, "disk_usage", lambda _: types.SimpleNamespace(free=1))
    with pytest.raises(FreshRefused, match="disk reserve"):
        run(contract)
    assert not Path(contract[0]["output"]).exists()


def test_input_changed_after_first_dispatch_stops_before_second(contract):
    calls = []

    def execute(row):
        calls.append(row)
        Path(next(iter(contract[0]["inputs"]))).write_bytes(b"changed after first dispatch")
        return result(row)

    with pytest.raises(FreshRefused, match="payload mismatch"):
        run(contract, execute)
    assert len(calls) == 1
    root = Path(contract[0]["output"])
    assert json.loads((root / "checkpoints/checkpoint.json").read_bytes())["completed_games"] == 1


def test_serialization_failure_preserves_old_checkpoint(tmp_path):
    path = tmp_path / "checkpoint.json"
    acc = persistence.CheckpointAccumulator(schedule(), writer_id="test")
    acc.write(path, writer_id="test", return_snapshot=False)
    before = path.read_bytes()
    record = result(schedule()[0])
    record["unserializable"] = object()
    acc.append(record, writer_id="test")
    with pytest.raises(TypeError):
        acc.write(path, writer_id="test", return_snapshot=False)
    assert path.read_bytes() == before


def test_frozen_17_input_git_blobs_unchanged():
    import hashlib

    for name, expected in identity.FROZEN_INPUTS.items():
        raw = subprocess.check_output(
            [
                GIT,
                "-c",
                f"safe.directory={ROOT.as_posix()}",
                "-C",
                str(ROOT),
                "show",
                f"HEAD:{name}",
            ]
        )
        assert hashlib.sha256(raw).hexdigest() == expected


@pytest.mark.skipif(os.name != "nt", reason="Windows interpreter/import seal")
def test_wrong_source_commit_rejected():
    runtime = runtime_contract()
    runtime["source_commit"] = "0" * 40
    with pytest.raises(FreshRefused, match="source commit"):
        identity.verify_runtime(runtime)


def test_wrong_startup_hashseed_rejected(monkeypatch):
    runtime = runtime_contract()
    monkeypatch.setenv("PYTHONHASHSEED", "123")
    with pytest.raises(FreshRefused, match="hash seed"):
        identity.verify_runtime(runtime)


@pytest.mark.skipif(os.name != "nt", reason="native Windows junction")
def test_windows_junction_output_refused(contract):
    destination = Path(contract[0]["output"])
    target = destination.parent / "junction-target"
    target.mkdir()
    subprocess.run(
        ["cmd.exe", "/d", "/c", "mklink", "/J", str(destination), str(target)],
        check=True,
        capture_output=True,
        creationflags=0x08000000,
    )
    with pytest.raises(FreshRefused, match="reparse"):
        run(contract)
    assert list(target.iterdir()) == []


@pytest.mark.skipif(os.name != "nt", reason="Windows wheel installation layout")
@pytest.mark.parametrize("mode", ["valid", "same-version-payload", "wheel-bytes", "version"])
def test_locked_wheel_payload_authentication(tmp_path, monkeypatch, mode):
    import hashlib
    import zipfile

    site = tmp_path / "venv/Lib/site-packages"
    site.mkdir(parents=True)
    wheels = tmp_path / "wheels"
    wheels.mkdir()
    wheel = wheels / "fixture_pkg-1.0-py3-none-any.whl"
    contents = {
        "fixture_pkg/__init__.py": b'__version__="1.0"\n',
        "fixture_pkg-1.0.dist-info/METADATA": (
            b"Metadata-Version: 2.1\nName: fixture-pkg\nVersion: 1.0\n"
        ),
    }
    with zipfile.ZipFile(wheel, "w") as archive:
        for name, data in contents.items():
            archive.writestr(name, data)
            target = site / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    lock = tmp_path / "uv.lock"
    lock.write_text(
        '[[package]]\nname = "fixture-pkg"\nversion = "1.0"\nwheels = [{hash = "sha256:'
        + hashlib.sha256(wheel.read_bytes()).hexdigest()
        + '"}]\n'
    )
    monkeypatch.setitem(identity.FROZEN_INPUTS, "uv.lock", file_hash(lock))
    if mode == "same-version-payload":
        (site / "fixture_pkg/__init__.py").write_bytes(b'__version__="1.0"\n# substituted\n')
    elif mode == "wheel-bytes":
        with wheel.open("ab") as stream:
            stream.write(b"changed")
    elif mode == "version":
        (site / "fixture_pkg-1.0.dist-info/METADATA").write_text(
            "Name: fixture-pkg\nVersion: 2.0\n"
        )
    if mode == "valid":
        assert identity.verify_locked_wheels(lock, wheels, tmp_path / "venv")["payloads"] == 2
    else:
        with pytest.raises(FreshRefused):
            identity.verify_locked_wheels(lock, wheels, tmp_path / "venv")


@pytest.mark.skipif(os.name != "nt", reason="Windows interpreter/import seal")
def test_unsealed_loaded_bytecode_rejected(tmp_path, monkeypatch):
    import types

    path = tmp_path / "fixture.py"
    path.write_text("pass\n")
    cached = tmp_path / "fixture.pyc"
    module = types.ModuleType("synthetic_cached_dependency")
    module.__file__ = str(path)
    module.__cached__ = str(cached)
    monkeypatch.setitem(sys.modules, module.__name__, module)
    runtime = runtime_contract()
    cached.write_bytes(b"unsealed compiled payload")
    with pytest.raises(FreshRefused, match="unsealed import bytecode"):
        identity.verify_runtime(runtime)
