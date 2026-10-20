"""Regression coverage for combat SBA LTB Mutagen departure provenance."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from tmnt_design_studio.engine07 import Game
from tmnt_design_studio.pilot07 import AcceptancePilot
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, run_game

ROOT = Path(__file__).resolve().parents[1]
SEEDS = (
    52602875548163369144134008259635487845293317286481406726252498296187974632476,
    106006273492101665316000105358704653692902405446975804566779680826804429635677,
    96991309514714145862924378877563814471441266842137307947311233243287635527631,
)


def _spec(seed: int, index: int) -> GameSpec:
    manifest = json.loads(
        (ROOT / "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json").read_text()
    )
    paths = {row["deck_key"]: row["source_path"] for row in manifest["decks"]}
    return GameSpec(
        f"attempt8-ltb-mutagen-{index}",
        "michelangelo-vs-splinter",
        seed,
        "canonical",
        (
            DeckSpec("michelangelo", paths["michelangelo"]),
            DeckSpec("splinter", paths["splinter"]),
        ),
    )


@pytest.mark.parametrize("index,seed", enumerate(SEEDS, 1))
def test_preserved_ltb_mutagen_failures_replay_deterministically(index: int, seed: int):
    first = run_game(ROOT, _spec(seed, index), AcceptancePilot())
    second = run_game(ROOT, _spec(seed, index), AcceptancePilot())
    assert first.get("runtime_error") is None
    assert second.get("runtime_error") is None
    assert json.dumps(first, sort_keys=True, separators=(",", ":")) == json.dumps(
        second, sort_keys=True, separators=(",", ":")
    )
    assert any(event.get("event") == "ltb_mutagen_resolved" for event in first["events"])


def test_forged_ltb_mutagen_departure_evidence_still_fails_closed():
    snapshot = run_game(ROOT, _spec(SEEDS[0], 99), AcceptancePilot())
    forged = copy.deepcopy(snapshot)
    source_id = next(
        event["source_id"]
        for event in forged["events"]
        if event.get("event") == "ltb_mutagen_resolved"
    )
    resolved = next(
        event
        for event in forged["events"]
        if event.get("event") == "ltb_mutagen_resolved" and event.get("source_id") == source_id
    )
    leave = next(
        event
        for event in forged["events"]
        if event.get("event") == "rules_event" and event.get("event_id") == resolved["event_id"]
    )
    leave["subject_ids"] = ["object-forged"]
    with pytest.raises(ValueError, match="LTB Mutagen evidence does not reconstruct"):
        Game.validate_ltb_mutagen_snapshot_evidence(forged)
