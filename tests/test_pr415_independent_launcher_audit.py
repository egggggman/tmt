from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.cardcade_diagnostic_launcher import OneShotDiagnosticLauncher, stage002

ROOT = Path(__file__).resolve().parents[1]
PRE_TEST_DESCENDANT = "5cf4a0c6cd631ddeac9dbf8123a4197c25bac66f"
ACCEPTED_MAIN = "10d2ac80ef5b81b3a209a3133eb0a84633a1f944"


def _launcher(tmp_path: Path, suffix: str) -> OneShotDiagnosticLauncher:
    output_root = ROOT / ".cardcade-diagnostic-runs"
    output_root.mkdir(exist_ok=True)
    return OneShotDiagnosticLauncher(
        ROOT,
        output_root / f"diagnostic-game-audit-{tmp_path.parent.name}-{suffix}",
    )


def _synthetic_executor(root, spec, *, diagnostic_capture):
    catalog = stage002.load_catalog(root)
    paths = tuple(root / seat.relative_path for seat in spec.seats)
    names = {name for path in paths for _count, name in stage002._deck_rows(path)}
    facts = stage002.load_facts(catalog, names)
    game = stage002.Game(
        (stage002.load_deck(paths[0], facts), stage002.load_deck(paths[1], facts)),
        names=tuple(seat.display_id for seat in spec.seats),
        seed=spec.seed,
    )
    presence = stage002._initial_presence(game)
    diagnostic_capture.bind(game, presence)
    snapshot = game.snapshot()
    stage002._add_created_token_presence(game, presence, snapshot["events"])
    snapshot["stage002_presence"] = stage002._finish_presence(presence, snapshot["events"])
    return snapshot


def test_audit_preflight_accepts_unapproved_pretest_descendant(monkeypatch, tmp_path):
    launcher = _launcher(tmp_path, "unapproved-source")

    def synthetic_git(_root, *args):
        if args == ("rev-parse", "HEAD"):
            return PRE_TEST_DESCENDANT
        if args == ("branch", "--show-current"):
            return ""
        if args == ("status", "--porcelain=v1"):
            return ""
        if args == ("rev-parse", "refs/remotes/origin/main"):
            return ACCEPTED_MAIN
        return launcher._git(launcher.root, *args)

    monkeypatch.setattr(launcher, "_git", synthetic_git)
    identity = launcher._verify_source()

    assert identity["head"] == PRE_TEST_DESCENDANT
    assert identity["accepted_main"] == ACCEPTED_MAIN


def test_audit_success_path_returns_normally_when_reconciliation_fails(monkeypatch, tmp_path):
    launcher = _launcher(tmp_path, "reconcile-failure")
    monkeypatch.setattr(
        stage002,
        "reconcile_snapshot",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("injected reconcile failure")),
    )

    result = launcher.run_once(executor=_synthetic_executor)

    assert result["terminal"] is False
    status = json.loads(
        launcher.output_directory.joinpath("run_status.json").read_text(encoding="utf-8")
    )
    assert status["run_returned_normally"] is True
    assert status["reconciliation_completed"] is False
    error = json.loads(
        launcher.output_directory.joinpath("reconciliation_error.json").read_text(encoding="utf-8")
    )
    assert error["type"] == "ValueError"


def test_audit_new_launcher_instances_can_each_invoke_executor(tmp_path):
    calls = 0

    def executor(*args, **kwargs):
        nonlocal calls
        calls += 1
        return _synthetic_executor(*args, **kwargs)

    first = _launcher(tmp_path, "repeat-one")
    second = _launcher(tmp_path, "repeat-two")
    first.run_once(executor=executor)
    second.run_once(executor=executor)

    assert calls == 2
    assert first._run_game_call_count == second._run_game_call_count == 1


def test_audit_original_exception_survives_failure_to_persist_exception_record(
    monkeypatch, tmp_path
):
    launcher = _launcher(tmp_path, "exception-persist-failure")
    original = RuntimeError("synthetic execution fault")
    calls = 0
    original_write = launcher._write_json

    def failing_write(directory, filename, value):
        if filename == "exception.json":
            raise OSError("injected exception-record storage failure")
        return original_write(directory, filename, value)

    monkeypatch.setattr(launcher, "_write_json", failing_write)

    def executor(_root, _spec, *, diagnostic_capture):
        nonlocal calls
        calls += 1
        raise original

    with pytest.raises(RuntimeError) as raised:
        launcher.run_once(executor=executor)

    assert raised.value is original
    assert calls == launcher._run_game_call_count == 1
    assert any("evidence persistence failed" in note for note in raised.value.__notes__)
