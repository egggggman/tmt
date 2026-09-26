from __future__ import annotations

import hashlib
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
    _authenticate_decks,
    build_schedule,
    execute_smoke,
)

ROOT = Path(__file__).resolve().parents[1]


def test_schedule_is_exact_and_deterministic() -> None:
    first = build_schedule(ROOT, AUTHORIZED_BASE_COMMIT)
    second = build_schedule(ROOT, AUTHORIZED_BASE_COMMIT)
    assert first == second
    assert len(first) == REQUIRED_GAME_COUNT == 240
    expected_topology = tuple(
        (
            f"{left}-vs-{right}-{seed}",
            f"{left}/{right}",
            seed,
            "alphabetical-earlier" if seed % 2 == 0 else "other",
            (
                sorted((left, right), key=lambda key: DECKS[key][0].casefold())[0]
                if seed % 2 == 0
                else sorted((left, right), key=lambda key: DECKS[key][0].casefold())[1]
            ),
            (
                sorted((left, right), key=lambda key: DECKS[key][0].casefold())[1]
                if seed % 2 == 0
                else sorted((left, right), key=lambda key: DECKS[key][0].casefold())[0]
            ),
        )
        for left, right in MATCHUPS
        for seed in SEEDS
    )
    assert (
        tuple(
            (
                item.game_id,
                item.matchup,
                item.seed,
                item.orientation,
                item.starting_deck,
                item.opposing_deck,
            )
            for item in first
        )
        == expected_topology
    )
    for left, right in MATCHUPS:
        games = [item for item in first if item.matchup == f"{left}/{right}"]
        assert len(games) == 40
        assert [item.seed for item in games] == list(SEEDS)
        assert sum(item.starting_deck == left for item in games) == 20
        assert sum(item.starting_deck == right for item in games) == 20


def test_schedule_uses_the_authorized_deck_paths() -> None:
    schedule = build_schedule(ROOT, AUTHORIZED_BASE_COMMIT)
    for item in schedule:
        for deck_key in (item.starting_deck, item.opposing_deck):
            expected_suffix = (
                "PROTOTYPE_0.3a.txt" if deck_key == "donatello" else "PROTOTYPE_0.3.txt"
            )
            assert DECKS[deck_key][1].endswith(expected_suffix)


def test_p0_3a_is_required_and_old_donatello_input_fails_authentication(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert DECKS["donatello"][1] == "decks/donatello/PROTOTYPE_0.3a.txt"
    assert (
        DECKS["donatello"][2] == "25812e2d7f0ac64ae2476c0d62298db35196d1719c9376b5369d5080faa6aad1"
    )
    old_input = {
        key: (
            display,
            relative_path,
            hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest(),
        )
        for key, (display, relative_path, _expected_hash) in DECKS.items()
    }
    old_input["donatello"] = (
        DECKS["donatello"][0],
        "decks/donatello/PROTOTYPE_0.3.txt",
        DECKS["donatello"][2],
    )
    monkeypatch.setattr("tools.run_prototype_0_3_prebalance_smoke.DECKS", old_input)
    with pytest.raises(
        PreflightError,
        match=r"deck hash mismatch: decks/donatello/PROTOTYPE_0\.3\.txt",
    ):
        _authenticate_decks(ROOT)


def test_other_authenticated_deck_hashes_remain_unchanged() -> None:
    assert (
        DECKS["shredder"][2] == "818e9a847fcdf8521f53ab9b49c0f054ddd6f9bce95e9fd57c89cb6c94da2ed2"
    )
    assert DECKS["raphael"][2] == "220ea90ccc579e09bef38ce972ba84f661c2382b92c7a4559667d24a5eec6f51"
    assert (
        DECKS["casey_jones"][2]
        == "f18d2dd6591520e495a0c723e1d15f5d3f4f6ce8a2693e4f93be0cd6660e838f"
    )


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
