"""Regression fixture for the preserved Attempt 6 counter-provenance failure."""

import json
from pathlib import Path

from tmnt_design_studio.pilot07 import AcceptancePilot
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, run_game

ROOT = Path(__file__).resolve().parents[1]
SEED = 12506277166433065153407346632076121278501225696392466898823914761107207299783


def _spec() -> GameSpec:
    manifest = json.loads(
        (ROOT / "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json").read_text()
    )
    paths = {row["deck_key"]: row["source_path"] for row in manifest["decks"]}
    return GameSpec(
        "attempt6-counter-provenance-regression",
        "donatello-vs-bebop_rocksteady",
        SEED,
        "canonical",
        (
            DeckSpec("bebop_rocksteady", paths["bebop_rocksteady"]),
            DeckSpec("donatello", paths["donatello"]),
        ),
    )


def test_preserved_counter_activation_failure_replays_deterministically():
    first = run_game(ROOT, _spec(), AcceptancePilot())
    second = run_game(ROOT, _spec(), AcceptancePilot())

    assert first.get("runtime_error") is None
    assert second.get("runtime_error") is None
    assert json.dumps(first, sort_keys=True, separators=(",", ":")) == json.dumps(
        second, sort_keys=True, separators=(",", ":")
    )
    assert first["winner"] in {"donatello", "bebop_rocksteady"}
    assert any(
        event["event"] == "activated_ability_resolved" and event.get("delivered")
        for event in first["events"]
    )
