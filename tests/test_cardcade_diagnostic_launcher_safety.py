from __future__ import annotations

from pathlib import Path

import pytest

from tools.cardcade_diagnostic_launcher import (
    DiagnosticLauncherError,
    OneShotDiagnosticLauncher,
    stage002,
)

ROOT = Path(__file__).resolve().parents[1]
PRE_TEST_DESCENDANT = "5cf4a0c6cd631ddeac9dbf8123a4197c25bac66f"
ACCEPTED_MAIN = "10d2ac80ef5b81b3a209a3133eb0a84633a1f944"


def _launcher(tmp_path: Path, label: str) -> OneShotDiagnosticLauncher:
    output_root = ROOT / ".cardcade-diagnostic-runs"
    output_root.mkdir(exist_ok=True)
    return OneShotDiagnosticLauncher(
        ROOT,
        output_root / f"diagnostic-game-safety-{tmp_path.parent.name}-{label}",
    )


def _synthetic_executor(root, spec, *, diagnostic_capture):
    """Create initial engine state and snapshot it without running gameplay."""
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


def test_source_preflight_rejects_descendant_not_exactly_approved(monkeypatch, tmp_path):
    launcher = _launcher(tmp_path, "wrong-source")

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
    with pytest.raises(DiagnosticLauncherError, match="exact approved implementation"):
        launcher._verify_source()


def test_failed_reconciliation_makes_successful_execution_blocked(monkeypatch, tmp_path):
    launcher = _launcher(tmp_path, "reconcile-failure")
    monkeypatch.setattr(
        stage002,
        "reconcile_snapshot",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            ValueError("injected reconciliation error")
        ),
    )

    with pytest.raises(DiagnosticLauncherError, match="reconciliation did not complete"):
        launcher.run_once(executor=_synthetic_executor)

    assert (launcher.output_directory / "reconciliation_error.json").is_file()
    assert (launcher.output_directory / "snapshot.json").is_file()


def test_authorization_is_consumed_across_fresh_launcher_instances(tmp_path):
    calls = 0

    def executor(*args, **kwargs):
        nonlocal calls
        calls += 1
        return _synthetic_executor(*args, **kwargs)

    first = _launcher(tmp_path, "repeat-one")
    second = _launcher(tmp_path, "repeat-two")
    first.run_once(executor=executor)
    with pytest.raises(DiagnosticLauncherError, match="authorization already consumed"):
        second.run_once(executor=executor)

    assert calls == 1
