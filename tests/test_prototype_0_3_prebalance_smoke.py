from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from tools.run_prototype_0_3_prebalance_smoke import (
    AUTHORIZED_BASE_COMMIT,
    DECKS,
    MATCHUPS,
    REQUIRED_GAME_COUNT,
    SEEDS,
    PreflightError,
    build_schedule,
    execute_smoke,
)

ROOT = Path(__file__).resolve().parents[1]


def test_schedule_is_exact_and_deterministic() -> None:
    first = build_schedule(ROOT, AUTHORIZED_BASE_COMMIT)
    second = build_schedule(ROOT, AUTHORIZED_BASE_COMMIT)
    assert first == second
    assert len(first) == REQUIRED_GAME_COUNT == 240
    for left, right in MATCHUPS:
        games = [item for item in first if item.matchup == f"{left}/{right}"]
        assert len(games) == 40
        assert [item.seed for item in games] == list(SEEDS)
        assert sum(item.starting_deck == left for item in games) == 20
        assert sum(item.starting_deck == right for item in games) == 20


def test_schedule_uses_only_prototype_0_3_paths() -> None:
    schedule = build_schedule(ROOT, AUTHORIZED_BASE_COMMIT)
    for item in schedule:
        assert DECKS[item.starting_deck][1].endswith("PROTOTYPE_0.3.txt")
        assert DECKS[item.opposing_deck][1].endswith("PROTOTYPE_0.3.txt")


def test_preflight_hash_failure_runs_no_game(monkeypatch: pytest.MonkeyPatch) -> None:
    broken_decks = dict(DECKS)
    broken_decks["shredder"] = (DECKS["shredder"][0], DECKS["shredder"][1], "0" * 64)
    monkeypatch.setattr("tools.run_prototype_0_3_prebalance_smoke.DECKS", broken_decks)
    called = False

    def should_not_run(*_args: object, **_kwargs: object) -> dict[str, object]:
        nonlocal called
        called = True
        raise AssertionError("game runner called after failed preflight")

    module = importlib.import_module("tools.run_prototype_0_3_prebalance_smoke")
    monkeypatch.setattr(module, "run_smoke_game", should_not_run)
    with pytest.raises(PreflightError):
        execute_smoke(ROOT, ROOT / "smoke-test-must-not-be-created.json", AUTHORIZED_BASE_COMMIT)
    assert not called


def test_historical_smoke_contract_remains_frozen() -> None:
    historical = importlib.import_module("tmnt_design_studio.smoke01")
    assert historical.REQUIRED_GAME_COUNT == 180
    assert historical.smoke_games()[0].seed == 8001
