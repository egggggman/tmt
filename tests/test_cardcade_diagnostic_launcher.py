from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tools.cardcade_diagnostic_launcher import (
    EvidencePersistenceError,
    OneShotDiagnosticLauncher,
    stage002,
)

ROOT = Path(__file__).resolve().parents[1]


def _launcher(tmp_path: Path) -> OneShotDiagnosticLauncher:
    output_root = ROOT / ".cardcade-diagnostic-runs"
    output_root.mkdir(exist_ok=True)
    output = output_root / f"diagnostic-game-test-{tmp_path.parent.name}-{tmp_path.name}"
    return OneShotDiagnosticLauncher(ROOT, output)


def _synthetic_executor(root, spec, *, diagnostic_capture):
    """Construct and snapshot the specified fixture without entering the game loop."""
    catalog = stage002.load_catalog(root)
    deck_paths = tuple(root / seat.relative_path for seat in spec.seats)
    names = {name for path in deck_paths for _quantity, name in stage002._deck_rows(path)}
    facts = stage002.load_facts(catalog, names)
    game = stage002.Game(
        (
            stage002.load_deck(deck_paths[0], facts),
            stage002.load_deck(deck_paths[1], facts),
        ),
        names=tuple(seat.display_id for seat in spec.seats),
        seed=spec.seed,
    )
    presence = stage002._initial_presence(game)
    diagnostic_capture.bind(game, presence)
    snapshot = game.snapshot()
    stage002._add_created_token_presence(game, presence, snapshot["events"])
    snapshot["stage002_presence"] = stage002._finish_presence(presence, snapshot["events"])
    return snapshot


def test_synthetic_success_serializes_reconciliation_and_integrity_hashes(tmp_path):
    launcher = _launcher(tmp_path)
    calls = []

    def executor(root, spec, *, diagnostic_capture):
        calls.append((root, spec.game_id))
        return _synthetic_executor(root, spec, diagnostic_capture=diagnostic_capture)

    snapshot = launcher.run_once(executor=executor)

    assert len(calls) == 1
    assert calls[0][1] == "april-casey:canonical:7231"
    assert snapshot["stage002_presence"]
    assert launcher._run_game_call_count == 1
    assert launcher._consumed
    assert launcher.output_directory.joinpath("snapshot.json").is_file()
    assert launcher.output_directory.joinpath("events.json").is_file()
    assert launcher.output_directory.joinpath("priority_stack_combat_trace.json").is_file()
    assert launcher.output_directory.joinpath("reconciliation.json").is_file()

    metadata = json.loads(
        launcher.output_directory.joinpath("run_metadata.json").read_text(encoding="utf-8")
    )
    assert metadata["retry_count"] == 0
    assert metadata["additional_seeds"] == 0
    assert metadata["batch_or_calibration"] is False
    status = json.loads(
        launcher.output_directory.joinpath("run_status.json").read_text(encoding="utf-8")
    )
    assert status["run_game_call_count"] == 1
    assert status["reconciliation_completed"] is True

    declared_hashes = json.loads(
        launcher.output_directory.joinpath("artifact_sha256.json").read_text(encoding="utf-8")
    )
    actual_hashes = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in launcher.output_directory.iterdir()
        if path.is_file() and path.name != "artifact_sha256.json"
    }
    assert declared_hashes == actual_hashes


def test_injected_failure_preserves_original_exception_and_bound_snapshot(tmp_path):
    launcher = _launcher(tmp_path)
    original = RuntimeError("synthetic launcher failure")
    calls = 0

    def executor(root, spec, *, diagnostic_capture):
        nonlocal calls
        calls += 1
        _synthetic_executor(root, spec, diagnostic_capture=diagnostic_capture)
        raise original

    with pytest.raises(RuntimeError) as raised:
        launcher.run_once(executor=executor)

    assert raised.value is original
    assert calls == launcher._run_game_call_count == 1
    error = json.loads(
        launcher.output_directory.joinpath("exception.json").read_text(encoding="utf-8")
    )
    assert error["type"] == "RuntimeError"
    assert "synthetic launcher failure" in error["traceback"]
    snapshot = json.loads(
        launcher.output_directory.joinpath("snapshot.json").read_text(encoding="utf-8")
    )
    assert snapshot["stage002_presence"]
    status = json.loads(
        launcher.output_directory.joinpath("run_status.json").read_text(encoding="utf-8")
    )
    assert status["snapshot_captured"] is True
    assert status["retry_count"] == 0


def test_failure_before_binding_is_persisted_without_fabricated_snapshot(tmp_path):
    launcher = _launcher(tmp_path)
    original = LookupError("synthetic pre-binding failure")
    calls = 0

    def executor(_root, _spec, *, diagnostic_capture):
        nonlocal calls
        calls += 1
        raise original

    with pytest.raises(LookupError) as raised:
        launcher.run_once(executor=executor)

    assert raised.value is original
    assert calls == 1
    error = json.loads(
        launcher.output_directory.joinpath("exception.json").read_text(encoding="utf-8")
    )
    assert "snapshot" not in error
    assert "not bound" in error["capture_error"]
    assert not launcher.output_directory.joinpath("snapshot.json").exists()


def test_launcher_instance_cannot_be_reused_for_second_invocation(tmp_path):
    launcher = _launcher(tmp_path)
    calls = 0

    def executor(root, spec, *, diagnostic_capture):
        nonlocal calls
        calls += 1
        return _synthetic_executor(root, spec, diagnostic_capture=diagnostic_capture)

    launcher.run_once(executor=executor)
    with pytest.raises(RuntimeError, match="already been consumed"):
        launcher.run_once(executor=executor)
    assert calls == launcher._run_game_call_count == 1


def test_existing_output_directory_is_rejected_before_executor_call(tmp_path):
    launcher = _launcher(tmp_path)
    launcher.output_directory.mkdir(parents=True)
    calls = 0

    def executor(_root, _spec, *, diagnostic_capture):
        nonlocal calls
        calls += 1
        raise AssertionError("executor must not be called")

    with pytest.raises(FileExistsError):
        launcher.run_once(executor=executor)
    assert calls == launcher._run_game_call_count == 0


def test_persistence_failure_after_synthetic_execution_is_never_retried(tmp_path, monkeypatch):
    launcher = _launcher(tmp_path)
    calls = 0
    original_write = launcher._write_json

    def failing_write(directory, filename, value):
        if filename == "snapshot.json":
            raise OSError("injected evidence storage failure")
        return original_write(directory, filename, value)

    monkeypatch.setattr(launcher, "_write_json", failing_write)

    def executor(root, spec, *, diagnostic_capture):
        nonlocal calls
        calls += 1
        return _synthetic_executor(root, spec, diagnostic_capture=diagnostic_capture)

    with pytest.raises(EvidencePersistenceError, match="do not retry"):
        launcher.run_once(executor=executor)
    assert calls == launcher._run_game_call_count == 1


def test_committed_match_configuration_is_exact():
    spec = OneShotDiagnosticLauncher(ROOT, ROOT / "unused")._match_spec()
    assert (spec.game_id, spec.pairing_id, spec.orientation, spec.seed) == (
        "april-casey:canonical:7231",
        "april-casey",
        "canonical",
        7231,
    )
    assert tuple(seat.display_id for seat in spec.seats) == (
        "april-oneil-p0.1",
        "casey-jones-p0.1",
    )


def test_output_directory_cannot_escape_isolated_diagnostic_root(tmp_path):
    outside = tmp_path / "diagnostic-game-outside"
    launcher = OneShotDiagnosticLauncher(ROOT, outside)
    with pytest.raises(RuntimeError, match="inside .cardcade-diagnostic-runs"):
        launcher._prepare_output()
    assert not outside.exists()
