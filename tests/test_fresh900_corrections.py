from __future__ import annotations

import ast
import copy
import errno
import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest
from test_fresh900_independent import execute, record, rows
from test_fresh900_independent import fixture as fixture

from tmnt_design_studio import calibration_integrity as storage
from tmnt_design_studio import fresh900 as runner
from tmnt_design_studio import fresh900_identity as identity

ROOT = Path(__file__).resolve().parents[1]


def test_original_failing_predicates_unchanged():
    raw = ROOT / "tests/evidence/pr369_test_independent.py.txt"
    assert (
        hashlib.sha256(raw.read_bytes()).hexdigest()
        == "f8210adda237543adefb9c8e7f1668cae38384fcae51fcd10ed66488a13b088e"
    )
    original = ast.parse(raw.read_bytes())
    current = ast.parse((ROOT / "tests/test_fresh900_independent.py").read_text())
    for name in (
        "test_extended_namespace_cannot_bypass_protected_overlap",
        "test_conflicting_result_identity_is_not_committed",
        "test_final_checkpoint_content_must_match_accepted_records",
        "test_primary_error_survives_lock_cleanup_error",
    ):
        assert ast.dump(
            next(n for n in original.body if getattr(n, "name", None) == name)
        ) == ast.dump(next(n for n in current.body if getattr(n, "name", None) == name))
    full = ROOT / "tests/evidence/pr369_test_fullplan_boundary.py.txt"
    assert (
        hashlib.sha256(full.read_bytes()).hexdigest()
        == "ad93699112f6b5e9cfd4d5c2217cb25229b264ac0d971df6be09f9d7e3007bb4"
    )


@pytest.mark.parametrize(
    "field,bad",
    [
        ("seats", ["opponent", "candidate"]),
        ("participants", ["foreign", "candidate"]),
        ("schedule_index", 1),
        ("schedule_position", 2),
        ("run_id", "foreign"),
        ("fresh_run_id", "foreign"),
        ("schedule_row", {}),
        ("plan_sha256", "bad"),
        ("winner_index", 1),
        ("loser", "candidate"),
        ("draw", True),
        ("terminal_state", "RUNNING"),
        ("turns_started", 11),
        ("source_commit", "bad"),
        ("runtime_sha256", "bad"),
        ("inputs_sha256", "bad"),
        ("completed_games", 2),
        ("schedule_games", 900),
        ("players", [{"name": "foreign"}, {"name": "candidate"}]),
        ("metadata", {"seed": -1}),
        ("identity", {"winner": "opponent"}),
        ("metadata", {"unapproved_identity": "value"}),
        ("identity", None),
    ],
)
def test_all_redundant_authority_fields_refused_and_preserved(fixture, field, bad):
    failed = {**record(rows()[0]), field: bad}
    with pytest.raises(identity.FreshRefused):
        execute(fixture, lambda _: copy.deepcopy(failed))
    root = Path(fixture["output"])
    assert json.loads((root / "checkpoints/checkpoint.json").read_bytes())["completed_games"] == 0
    saved = json.loads((root / "failures/rejected-record.json").read_bytes())
    assert saved["record"] == failed  # Neither fixed nor normalized into accepted data.


def test_consistent_metadata_is_accepted(fixture):
    plan = fixture
    row = rows()[0]
    value = {
        **record(row),
        **row,
        "participants": row["seats"],
        "schedule_index": 0,
        "schedule_position": 1,
        "fresh_run_id": plan["run_id"],
        "schedule_row": row,
        "plan_sha256": identity.digest(plan),
        "metadata": {"seed": row["seed"], "terminal": True},
    }
    runner.validate_result(value, row, 0, plan, identity.digest(plan))


@pytest.mark.parametrize(
    "field,bad",
    [
        ("events", [None]),
        ("events", [{"event": "acceptance_incomplete", "reason": "turn_limit"}]),
        ("stage002_presence", ["not evidence"]),
        ("rules_event_evidence", [None]),
    ],
)
def test_inconsistent_detailed_evidence_refused(fixture, field, bad):
    with pytest.raises(identity.FreshRefused):
        execute(fixture, lambda row: {**record(row), field: bad})


def test_final_record_binding_rejects_even_rehashed_substitution(tmp_path):
    path = tmp_path / "checkpoint.json"
    acc = storage.CheckpointAccumulator(rows(), writer_id="fixture")
    expected = {}
    for row in rows():
        value = record(row)
        expected[row["game_id"]] = identity.digest(value)
        acc.append(value, writer_id="fixture")
    acc.write(path, writer_id="fixture", return_snapshot=False, verify_bytes=True)
    bad = json.loads(path.read_bytes())
    bad["records"][0]["events"][0]["value"] = 12345
    path.write_text(json.dumps(bad))
    with pytest.raises(identity.FreshRefused, match="record content"):
        runner.validate_final_checkpoint(path, rows(), expected, identity.file_hash(path))


def test_final_requires_complete_ordered_expected_records(tmp_path):
    path = tmp_path / "checkpoint.json"
    acc = storage.CheckpointAccumulator(rows(), writer_id="fixture")
    one = record(rows()[0])
    acc.append(one, writer_id="fixture")
    out = acc.write(path, writer_id="fixture", return_snapshot=False, verify_bytes=True)
    with pytest.raises(identity.FreshRefused, match="incomplete final"):
        runner.validate_final_checkpoint(
            path, rows(), {rows()[0]["game_id"]: identity.digest(one)}, out["checkpoint_sha256"]
        )


def test_pre_replace_corruption_cannot_mint_expected_hash(tmp_path):
    path = tmp_path / "checkpoint.json"
    acc = storage.CheckpointAccumulator(rows(), writer_id="fixture")

    def corrupt():
        for temporary in tmp_path.glob(".checkpoint.json.*"):
            temporary.write_text('{"valid_but_unexpected":true}')

    with pytest.raises(storage.CheckpointIntegrityError, match="expected bytes"):
        acc.write(
            path,
            writer_id="fixture",
            return_snapshot=False,
            verify_bytes=True,
            before_replace=corrupt,
        )


def test_primary_and_cleanup_are_structured_separately(fixture, monkeypatch):
    original = storage.os.unlink
    primary = RuntimeError("primary failure")

    def unlink(path, *args, **kwargs):
        if str(path).endswith(".lock"):
            raise PermissionError(errno.EACCES, "cleanup failure")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(storage.os, "unlink", unlink)
    with pytest.raises(RuntimeError) as caught:
        execute(fixture, lambda _: (_ for _ in ()).throw(primary))
    assert caught.value is primary
    log = json.loads((Path(fixture["output"]) / "failures/stop.json").read_bytes())
    assert log["error_type"] == "RuntimeError" and log["stage"] == "EXECUTOR"
    assert log["cleanup_failures"][0]["stage"] == "LOCK_RELEASE"
    assert log["cleanup_failures"][0]["error_type"] == "PermissionError"
    assert log["checkpoint_integrity_verified"] is True
    assert log["ownership_unresolved"] is True and log["resources_unresolved"] is True
    assert log["operation_state"] == "STOPPED_REVIEW_REQUIRED"


def test_release_only_failure_never_publishes_complete(fixture, monkeypatch):
    def failed_release(self):
        raise PermissionError(errno.EACCES, "release-only failure")

    monkeypatch.setattr(storage.WriterLock, "release", failed_release)
    with pytest.raises(PermissionError):
        execute(fixture)
    root = Path(fixture["output"])
    assert not (root / "results/summary.json").exists()
    assert json.loads((root / "telemetry/status.json").read_bytes())["state"] != "COMPLETE"
    log = json.loads((root / "failures/stop.json").read_bytes())
    assert log["stage"] == "LOCK_RELEASE" and log["ownership_unresolved"]
    assert log["checkpoint_integrity_verified"]


def test_temporary_cleanup_does_not_mask_serialization_error(tmp_path, monkeypatch):
    path = tmp_path / "checkpoint.json"
    acc = storage.CheckpointAccumulator(rows(), writer_id="fixture")
    value = record(rows()[0])
    value["unserializable"] = object()
    acc.append(value, writer_id="fixture")
    monkeypatch.setattr(
        storage.os,
        "unlink",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            PermissionError("temporary cleanup denied")
        ),
    )
    with pytest.raises(TypeError) as caught:
        acc.write(path, writer_id="fixture", return_snapshot=False, verify_bytes=True)
    assert caught.value.cleanup_failures[0][0] == "TEMPORARY_CLEANUP"


def test_logging_failure_keeps_primary_and_structured_fallback(fixture, monkeypatch, capsys):
    original = runner.atomic_json

    def fail(path, value):
        if path.name == "stop.json":
            raise PermissionError("failure log denied")
        original(path, value)

    monkeypatch.setattr(runner, "atomic_json", fail)
    primary = RuntimeError("initiating failure")
    with pytest.raises(RuntimeError) as caught:
        execute(fixture, lambda _: (_ for _ in ()).throw(primary))
    assert caught.value is primary
    report = json.loads(capsys.readouterr().err)
    assert report["error"] == "initiating failure"
    assert report["cleanup_failures"][-1]["stage"] == "FAILURE_LOG_WRITE"


@pytest.mark.parametrize("substitution", ["junction", "directory"])
def test_directory_substitution_after_dispatch_fails_closed(fixture, tmp_path, substitution):
    root = Path(fixture["output"])
    outside = tmp_path / "outside"
    outside.mkdir()
    old = root / "old-checkpoints"
    captured = {}

    def substitute(_row):
        directory = root / "checkpoints"
        assert directory.resolve().is_relative_to(tmp_path.resolve())
        assert old.resolve().is_relative_to(tmp_path.resolve()) and not old.exists()
        captured["before"] = (directory / "checkpoint.json").read_bytes()
        directory.rename(old)
        if substitution == "directory":
            directory.mkdir()
        elif os.name == "nt":
            subprocess.run(
                ["cmd.exe", "/d", "/c", "mklink", "/J", str(directory), str(outside)],
                check=True,
                capture_output=True,
                creationflags=0x08000000,
            )
        else:
            directory.symlink_to(outside, target_is_directory=True)
        return record(_row)

    with pytest.raises(identity.FreshRefused):
        execute(fixture, substitute)
    assert (old / "checkpoint.json").read_bytes() == captured["before"]
    assert list(outside.iterdir()) == []
    if substitution == "directory":
        assert list((root / "checkpoints").iterdir()) == []


def test_reservation_parent_substitution_before_mkdir_refused(fixture, tmp_path, monkeypatch):
    parent = tmp_path / "parent"
    parent.mkdir()
    old = tmp_path / "old-parent"
    fixture["output"] = str(parent / fixture["run_id"])
    original = runner.check_resources

    def substitute(path, measure):
        sample = original(path, measure)
        assert parent.resolve().is_relative_to(tmp_path.resolve())
        assert old.resolve().is_relative_to(tmp_path.resolve()) and not old.exists()
        parent.rename(old)
        parent.mkdir()
        return sample

    monkeypatch.setattr(runner, "check_resources", substitute)
    with pytest.raises(identity.FreshRefused, match="parent changed"):
        execute(fixture)
    assert list(parent.iterdir()) == []


def test_silent_release_does_not_authorize_success(fixture, monkeypatch):
    monkeypatch.setattr(storage.WriterLock, "release", lambda self: None)
    with pytest.raises(storage.CheckpointIntegrityError, match="unresolved"):
        execute(fixture)
    root = Path(fixture["output"])
    assert not (root / "results/summary.json").exists()
    assert json.loads((root / "telemetry/status.json").read_bytes())["state"] != "COMPLETE"


@pytest.mark.skipif(os.name != "nt", reason="Windows path namespace policy")
@pytest.mark.parametrize("form", ["extended", "device", "unc", "trailing-dot", "alternate-stream"])
def test_ambiguous_path_spellings_refused_before_output(tmp_path, form):
    name = str(tmp_path / "safe")
    variants = {
        "extended": "\\\\?\\" + name,
        "device": "\\\\.\\" + name,
        "unc": "\\\\localhost\\C$\\fixture",
        "trailing-dot": name + ".",
        "alternate-stream": name + ":payload",
    }
    with pytest.raises(identity.FreshRefused):
        identity.plain(Path(variants[form]))
    assert not (tmp_path / "safe").exists()
