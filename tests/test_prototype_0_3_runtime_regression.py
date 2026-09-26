from pathlib import Path

import pytest

from tmnt_design_studio.smoke01 import run_smoke_game
from tmnt_design_studio.stage002 import DeckSpec, GameSpec

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("game_id", "pairing", "seed", "starting", "opposing"),
    (
        (
            "shredder-vs-raphael-3007",
            "shredder/raphael",
            3007,
            "shredder",
            "raphael",
        ),
        (
            "raphael-vs-casey_jones-3001",
            "raphael/casey_jones",
            3001,
            "raphael",
            "casey_jones",
        ),
    ),
)
def test_prototype_0_3_runtime_failures_complete_and_replay_deterministically(
    game_id, pairing, seed, starting, opposing
):
    spec = GameSpec(
        game_id,
        pairing,
        seed,
        "other",
        (
            DeckSpec(f"{starting}-p0.3", f"decks/{starting}/PROTOTYPE_0.3.txt"),
            DeckSpec(f"{opposing}-p0.3", f"decks/{opposing}/PROTOTYPE_0.3.txt"),
        ),
    )

    first = run_smoke_game(ROOT, spec)
    second = run_smoke_game(ROOT, spec)

    assert first["winner"] is not None
    assert first == second
