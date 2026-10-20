"""Regression fixtures for the preserved Baseline 005 Food-search failures."""

import json
from pathlib import Path

import pytest

from tmnt_design_studio.pilot07 import AcceptancePilot
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, run_game

ROOT = Path(__file__).parents[1]
DECKS = {
    "raphael": "docs/objective-balance-lab/baselines/RAPHAEL_OBL_BASELINE_002.txt",
    "michelangelo": "decks/michelangelo/PROTOTYPE_0.1.txt",
}


@pytest.mark.parametrize(
    ("orientation", "seed", "first", "second"),
    [
        (
            "reversed",
            70854356032484108629752045553328311296264080222857296236996711926358961833742,
            "raphael",
            "michelangelo",
        ),
        (
            "canonical",
            61283485696731598188099450771387457581219000296206197647983307541613500950207,
            "michelangelo",
            "raphael",
        ),
    ],
)
def test_preserved_etb_food_search_failures_replay_and_reconstruct(
    orientation, seed, first, second
):
    spec = GameSpec(
        f"food-search-regression-{orientation}",
        f"{first}-vs-{second}",
        seed,
        orientation,
        (
            DeckSpec(first, DECKS[first]),
            DeckSpec(second, DECKS[second]),
        ),
    )
    first_run = run_game(ROOT, spec, AcceptancePilot())
    second_run = run_game(ROOT, spec, AcceptancePilot())
    assert json.dumps(first_run, sort_keys=True) == json.dumps(second_run, sort_keys=True)
    assert any(event["event"] == "etb_food_search_committed" for event in first_run["events"])
