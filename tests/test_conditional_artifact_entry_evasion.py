"""Conditional evasion reads entry provenance and the creature's live abilities."""

from dataclasses import replace
from pathlib import Path

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import (
    CardInterpreter,
    TokenCreationProgram,
    TokenDefinition,
)
from tmnt_design_studio.engine07 import CardFact, Game, load_facts

ROOT = Path(__file__).resolve().parents[1]
CLAUSE = (
    "This creature can't be blocked if an artifact entered the battlefield "
    "under your control this turn."
)
LAND = CardFact("Island", "", 0, "Basic Land — Island")
ATTACKER = CardFact("Anonymous Droid", "{2}", 2, "Creature — Robot", CLAUSE, 2, 2)
BLOCKER = CardFact("Anonymous Guardian", "{2}", 2, "Creature — Turtle", power=2, toughness=2)
ARTIFACT = CardFact("Anonymous Device", "{1}", 1, "Artifact")
NONARTIFACT = CardFact("Anonymous Charm", "{1}", 1, "Enchantment")


def setup(seed=2896):
    current = Game(([LAND] * 30, [LAND] * 30), seed=seed)
    current.begin_turn()
    attacker = current.create_permanent(ATTACKER, 0, summoning_sick=False)
    blocker = current.create_permanent(BLOCKER, 1, summoning_sick=False)
    return current, attacker, blocker


def test_frozen_and_renamed_card_use_same_oracle_block_rule():
    catalog = load_card_data(
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json",
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json",
    )
    frozen = load_facts(catalog, {"Fugitive Droid"})["Fugitive Droid"]
    for card in (frozen, ATTACKER, replace(ATTACKER, name="Another Droid")):
        assert CLAUSE in CardInterpreter.fragments(card)
        assert CardInterpreter().supports_blocking_fragment(CLAUSE)
        assert (
            CLAUSE,
            "oracle_ability_not_implemented",
        ) not in CardInterpreter().unsupported_fragments(card)


def test_artifact_entry_enables_evasion_after_artifact_leaves():
    current, attacker, blocker = setup()
    assert current.can_block(attacker, blocker, 1)
    current.create_permanent(NONARTIFACT, 0)
    current.create_permanent(ARTIFACT, 1)
    assert current.can_block(attacker, blocker, 1)
    source = current.create_permanent(ARTIFACT, 0)
    assert not current.can_block(attacker, blocker, 1)
    current.move_object(source, "graveyard", reason="test_artifact_left")
    assert not current.can_block(attacker, blocker, 1)
    current.check_invariants()


def test_control_change_does_not_rewrite_entry_controller_and_turn_resets():
    current, attacker, blocker = setup()
    source = current.create_permanent(ARTIFACT, 1)
    current.change_controller(source, 0)
    assert current.can_block(attacker, blocker, 1)
    current.create_permanent(ARTIFACT, 0)
    assert not current.can_block(attacker, blocker, 1)
    current._turn += 1
    assert current.can_block(attacker, blocker, 1)


def test_artifact_token_entry_qualifies_and_ability_loss_restores_block():
    current, attacker, blocker = setup()
    current.create_tokens(
        0,
        TokenCreationProgram(TokenDefinition("Anonymous Relic", "Artifact"), 1),
        source_card="Anonymous Source",
        oracle_fragment="Create an artifact token.",
    )
    assert not current.can_block(attacker, blocker, 1)
    attacker.ability_loss_timestamp = (999, 999)
    assert current.can_block(attacker, blocker, 1)
    attacker.ability_loss_timestamp = None
    assert not current.can_block(attacker, blocker, 1)
    current.check_invariants()


def test_conditional_block_choices_replay_exactly():
    def run():
        current, attacker, blocker = setup()
        source = current.create_permanent(ARTIFACT, 0)
        current.move_object(source, "graveyard", reason="test_artifact_left")
        restriction = current.blocking_restriction(attacker, blocker)
        current.check_invariants()
        return restriction, current.snapshot(), current.events

    assert run() == run()
