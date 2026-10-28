"""Synthetic 732-record contracts only; no game engine or production files."""

from __future__ import annotations

import dataclasses
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from resume_test_support import current_identity

from tmnt_design_studio import calibration_integrity as integrity
from tmnt_design_studio.calibration_runner import run_authorized_resume
from tmnt_design_studio.resume_authorization import (
    ResumeRefused,
    ReviewLease,
    encoded,
    sha256,
    strict_json,
)

ROOT = Path(__file__).parents[1]


@pytest.fixture
def contract(tmp_path):
    schedule = [
        dict(
            game_id=f"synthetic-{i}",
            pairing_id="synthetic",
            seed=i,
            orientation="candidate_first" if i < 450 else "opponent_first",
            synthetic_review=True,
        )
        for i in range(900)
    ]
    records = [dict(game_id=row["game_id"], fixture=i) for i, row in enumerate(schedule[:732])]
    initial = encoded(
        dict(
            schedule_digest=sha256(encoded(schedule)),
            schedule_games=900,
            completed_games=732,
            records=records,
        )
    )
    for directory in ("reference", "working", "telemetry"):
        (tmp_path / directory).mkdir()
    reference = tmp_path / "reference/checkpoint.json"
    checkpoint = tmp_path / "working/checkpoint.json"
    reference.write_bytes(initial)
    checkpoint.write_bytes(initial)
    identity = current_identity(ROOT)
    lease = ReviewLease(
        "synthetic-authority",
        checkpoint,
        reference,
        tmp_path / "control",
        sha256(initial),
        sha256(encoded(schedule)),
        identity,
        b"test-key-" * 8,
        telemetry_root=tmp_path / "telemetry",
        telemetry_root_identity=(
            (tmp_path / "telemetry").stat().st_dev,
            (tmp_path / "telemetry").stat().st_ino,
        ),
    )
    return schedule, lease, tmp_path / "telemetry/durable-status.json", initial


def execute(contract, *, stop_after=1, executor=None):
    schedule, lease, status, _ = contract
    return run_authorized_resume(
        schedule,
        executor or (lambda row: dict(game_id=row["game_id"], fixture="new")),
        lease=lease,
        status=status,
        stop_after=stop_after,
    )


def test_valid_732_to_733_to_734_no_replay(contract):
    schedule, lease, status, initial = contract
    called = []

    def mock(row):
        called.append(row["game_id"])
        return dict(game_id=row["game_id"])

    first = execute(contract, executor=mock)
    assert first["completed_games"] == 733
    lease2 = dataclasses.replace(lease, expected_tip=first["receipt_tip"])
    second = execute((schedule, lease2, status, initial), executor=mock)
    assert second["completed_games"] == 734
    assert called == ["synthetic-732", "synthetic-733"]
    assert lease.reference.read_bytes() == initial
    assert (
        strict_json(lease.checkpoint.read_bytes())["records"][:732]
        == strict_json(initial)["records"]
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("action", "new-run"),
        ("initial_count", 731),
        ("schedule_sha256", "0" * 64),
        ("monitor_protocol", "legacy-reader"),
        ("synthetic_review", False),
        ("receipt_key", b""),
        ("initial_sha256", "0" * 64),
    ],
)
def test_wrong_authority_never_dispatches(contract, field, value):
    schedule, lease, status, initial = contract
    bad = dataclasses.replace(lease, **{field: value})
    with pytest.raises(ResumeRefused):
        execute((schedule, bad, status, initial), executor=lambda _: pytest.fail("dispatch"))
    assert lease.checkpoint.read_bytes() == initial


def test_missing_authority(contract):
    schedule, _, status, _ = contract
    with pytest.raises(ResumeRefused):
        run_authorized_resume(
            schedule, lambda _: pytest.fail("dispatch"), lease=None, status=status
        )


@pytest.mark.parametrize(
    "kind", ["content", "duplicate", "reordered", "count", "digest", "missing"]
)
def test_checkpoint_negative(contract, kind):
    _, lease, _, initial = contract
    payload = strict_json(initial)
    if kind == "content":
        payload["records"][0]["fixture"] = "changed"
    elif kind == "duplicate":
        payload["records"][1] = payload["records"][0]
    elif kind == "reordered":
        payload["records"].reverse()
    elif kind == "count":
        payload["completed_games"] = 731
    elif kind == "digest":
        payload["schedule_digest"] = "0" * 64
    if kind == "missing":
        lease.checkpoint.unlink()
    else:
        lease.checkpoint.write_bytes(encoded(payload))
    with pytest.raises((ResumeRefused, OSError)):
        execute(contract, executor=lambda _: pytest.fail("dispatch"))
    if kind == "missing":
        assert not lease.checkpoint.exists()


@pytest.mark.parametrize("kind", ["source", "input", "executable"])
def test_identity_mismatch(contract, kind):
    schedule, lease, status, initial = contract
    identity = lease.identity
    if kind == "source":
        files = dict(identity.source_files)
        files[next(iter(files))] = "0" * 64
        identity = dataclasses.replace(identity, source_files=files)
    elif kind == "input":
        identity = dataclasses.replace(identity, input_files={"pyproject.toml": "0" * 64})
    else:
        identity = dataclasses.replace(identity, executable_sha256="0" * 64)
    with pytest.raises(ResumeRefused):
        execute(
            (schedule, dataclasses.replace(lease, identity=identity), status, initial),
            executor=lambda _: pytest.fail("dispatch"),
        )


@pytest.mark.parametrize("lock_target", ["checkpoint", "control"])
def test_competing_writer(contract, lock_target):
    _, lease, _, _ = contract
    with (
        integrity.WriterLock(getattr(lease, lock_target), "other"),
        pytest.raises(integrity.CheckpointIntegrityError),
    ):
        execute(contract, executor=lambda _: pytest.fail("dispatch"))


@pytest.mark.parametrize("fault", ["executor", "prepare", "replace", "commit"])
def test_interruption_is_not_auto_recovered(contract, monkeypatch, fault):
    import tmnt_design_studio.resume_authorization as authorization

    _, lease, _, initial = contract
    append = authorization.Receipts.append

    def fail_append(self, phase, **fields):
        if phase == fault:
            raise OSError("injected receipt failure")
        return append(self, phase, **fields)

    if fault in ("prepare", "commit"):
        monkeypatch.setattr(authorization.Receipts, "append", fail_append)
    if fault == "replace":

        def deny(*_):
            raise PermissionError("denied")

        monkeypatch.setattr(integrity, "_replace_with_retry", deny)

    def mock(row):
        if fault == "executor":
            raise RuntimeError("interrupted")
        return dict(game_id=row["game_id"])

    with pytest.raises((OSError, RuntimeError)):
        execute(contract, executor=mock)
    if fault != "commit":
        assert lease.checkpoint.read_bytes() == initial
    assert lease.reference.read_bytes() == initial
    monkeypatch.undo()
    with pytest.raises(ResumeRefused):
        execute(
            (contract[0], dataclasses.replace(lease), contract[2], initial),
            executor=lambda _: pytest.fail("replay"),
        )


@pytest.mark.parametrize("fault", ["missing", "forged", "stale-head", "rollback", "reused-lease"])
def test_continuation_evidence(contract, fault):
    schedule, lease, status, initial = contract
    result = execute(contract)
    next_lease = dataclasses.replace(lease, expected_tip=result["receipt_tip"])
    if fault == "missing":
        (lease.control / "000002.json").unlink()
    elif fault == "forged":
        path = lease.control / "000002.json"
        value = json.loads(path.read_bytes())
        value["count"] = 734
        path.write_bytes(encoded(value))
    elif fault == "stale-head":
        next_lease = dataclasses.replace(lease)
    elif fault == "rollback":
        lease.checkpoint.write_bytes(initial)
    else:
        next_lease = lease
    with pytest.raises(ResumeRefused):
        execute((schedule, next_lease, status, initial), executor=lambda _: pytest.fail("replay"))


@pytest.mark.parametrize("raw", [b'{"a":1,"a":2}', b'{"a":NaN}'])
def test_ambiguous_json_refused(raw):
    with pytest.raises(ResumeRefused):
        strict_json(raw)


@pytest.mark.parametrize("kind", ["duplicate", "reordered", "count", "digest", "bool-count"])
def test_structural_validation_after_valid_outer_hash(contract, kind):
    schedule, lease, status, initial = contract
    payload = strict_json(initial)
    if kind == "duplicate":
        payload["records"][1] = payload["records"][0]
    elif kind == "reordered":
        payload["records"].reverse()
    elif kind == "count":
        payload["completed_games"] = 731
    elif kind == "digest":
        payload["schedule_digest"] = "0" * 64
    else:
        payload["completed_games"] = True
    raw = encoded(payload)
    # Test-only authority explicitly pins malformed bytes to reach inner checks.
    lease.reference.write_bytes(raw)
    lease.checkpoint.write_bytes(raw)
    bad = dataclasses.replace(lease, initial_sha256=sha256(raw))
    with pytest.raises(ResumeRefused):
        execute((schedule, bad, status, raw), executor=lambda _: pytest.fail("dispatch"))


def test_truncated_all_receipts_cannot_reuse_latest_head(contract):
    schedule, lease, status, initial = contract
    result = execute(contract)
    next_lease = dataclasses.replace(lease, expected_tip=result["receipt_tip"])
    for path in lease.control.iterdir():
        path.unlink()
    lease.checkpoint.write_bytes(initial)
    with pytest.raises(ResumeRefused):
        execute((schedule, next_lease, status, initial), executor=lambda _: pytest.fail("replay"))


def test_actual_second_process_writer_is_refused(tmp_path):
    target = tmp_path / "checkpoint.json"
    code = (
        "import sys; from pathlib import Path; "
        "from tmnt_design_studio.calibration_integrity import WriterLock,CheckpointIntegrityError\n"
        "try: WriterLock(Path(sys.argv[1]),'second',hold_handle=True).acquire()\n"
        "except CheckpointIntegrityError: sys.exit(0)\n"
        "sys.exit(1)\n"
    )
    with integrity.WriterLock(target, "first", hold_handle=True):
        completed = subprocess.run(
            [sys.executable, "-B", "-c", code, str(target)],
            check=False,
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        assert completed.returncode == 0, completed.stderr


@pytest.mark.skipif(os.name != "nt", reason="Windows held marker semantics")
def test_owned_marker_cannot_be_deleted(tmp_path):
    target = tmp_path / "checkpoint.json"
    with (
        integrity.WriterLock(target, "first", hold_handle=True) as owner,
        pytest.raises(PermissionError),
    ):
        owner.path.unlink()


@pytest.mark.skipif(os.name != "nt", reason="Windows sharing API")
def test_status_handle_cannot_block_checkpoint(contract):
    import ctypes
    import ctypes.wintypes as w

    _, lease, status, _ = contract
    status.write_bytes(b"old telemetry")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [
        w.LPCWSTR,
        w.DWORD,
        w.DWORD,
        w.LPVOID,
        w.DWORD,
        w.DWORD,
        w.HANDLE,
    ]
    kernel.CreateFileW.restype = w.HANDLE
    kernel.CloseHandle.argtypes = [w.HANDLE]
    handle = kernel.CreateFileW(str(status), 0x80000000, 1, None, 3, 0x80, None)
    assert handle != w.HANDLE(-1).value
    try:
        with pytest.raises(ResumeRefused, match="telemetry"):
            execute(contract)
        assert strict_json(lease.checkpoint.read_bytes())["completed_games"] == 733
        assert len(list(lease.control.glob("*.json"))) == 3
    finally:
        kernel.CloseHandle(handle)
