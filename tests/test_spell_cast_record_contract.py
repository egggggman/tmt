"""Regression coverage for the common spell-cast telemetry contract."""

import json
from pathlib import Path

import pytest

from tmnt_design_studio.engine07 import Game
from tmnt_design_studio.pilot07 import AcceptancePilot
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, run_game

ROOT = Path(__file__).resolve().parents[1]
SEED = 90856440471641210079667413299657723063525178810879778610267403494681052196929


def _spec() -> GameSpec:
    manifest = json.loads(
        (ROOT / "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json").read_text()
    )
    paths = {row["deck_key"]: row["source_path"] for row in manifest["decks"]}
    return GameSpec(
        "attempt7-player-index-regression",
        "april_oneil-vs-donatello",
        SEED,
        "canonical",
        (
            DeckSpec("april_oneil", paths["april_oneil"]),
            DeckSpec("donatello", paths["donatello"]),
        ),
    )


def test_attempt7_seed_replays_and_spell_cast_records_are_complete():
    first = run_game(ROOT, _spec(), AcceptancePilot())
    second = run_game(ROOT, _spec(), AcceptancePilot())
    assert first.get("runtime_error") is None
    assert second.get("runtime_error") is None
    assert json.dumps(first, sort_keys=True, separators=(",", ":")) == json.dumps(
        second, sort_keys=True, separators=(",", ":")
    )
    records = [event for event in first["events"] if event.get("event") == "spell_cast"]
    assert records
    assert all(isinstance(event.get("player_index"), int) for event in records)
    assert all(isinstance(event.get("card_types"), (list, tuple)) for event in records)


@pytest.mark.parametrize(
    "record",
    [
        {"event": "spell_cast", "card_types": ("Instant",)},
        {"event": "spell_cast", "player_index": 0},
    ],
)
def test_malformed_spell_cast_record_fails_closed(record):
    with pytest.raises(ValueError, match="spell_cast record lacks"):
        Game._validate_spell_cast_record(record)
