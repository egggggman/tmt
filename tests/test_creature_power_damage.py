"""Oracle-derived two-target damage, with the chosen creature as the damage source."""

from pathlib import Path

import pytest

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter, CastKind
from tmnt_design_studio.engine07 import ActionKind, CardFact, Game

ROOT = Path(__file__).resolve().parents[1]
TEXT = (
    "Target creature you control deals damage equal to its power to "
    "target creature an opponent controls."
)
SPELL = CardFact("Renamed Instant", "{1}{G}", 2, "Instant", TEXT)
SORCERY = CardFact("Renamed Sorcery", "{1}{G}", 2, "Sorcery", TEXT)
FOREST = CardFact("Forest", "", 0, "Basic Land — Forest")
PLAINS = CardFact("Plains", "", 0, "Basic Land — Plains")
BEAR = CardFact("Renamed Creature", "{1}{G}", 2, "Creature — Bear", power=2, toughness=2)
BIG = CardFact("Large Creature", "{4}{G}", 5, "Creature — Beast", power=4, toughness=5)


def setup(*, spell=SPELL, source=BEAR, recipient=BIG, mana=True):
    game = Game(([PLAINS] * 60, [PLAINS] * 60), seed=73)
    game.begin_turn()
    if mana:
        game.create_permanent(FOREST, 0, summoning_sick=False)
        game.create_permanent(PLAINS, 0, summoning_sick=False)
    card = game.set_hand_for_testing(0, [spell])[0]
    own = game.create_permanent(source, 0, summoning_sick=False)
    other = game.create_permanent(recipient, 1, summoning_sick=False)
    return game, card, own, other


def test_frozen_oracle_and_renamed_spell_share_exact_program():
    catalog = load_card_data(
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json",
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json",
    )
    frozen = next(card for card in catalog.cards if card.name == "Tenderize")
    interpreter = CardInterpreter()
    assert frozen.oracle_text == TEXT
    assert interpreter.cast_program(frozen).kind is CastKind.CREATURE_POWER_DAMAGE
    assert interpreter.cast_program(SPELL).kind is CastKind.CREATURE_POWER_DAMAGE
    assert interpreter.creature_power_damage_program(SPELL, TEXT).amount_source == "source_power"
    assert interpreter.damage_semantic_coverage(SPELL, TEXT).coverage.fully_supported
    invalid = CardFact("Renamed Creature", "{1}{G}", 2, "Creature", TEXT)
    assert interpreter.creature_power_damage_program(invalid, TEXT) is None
    assert not interpreter.damage_semantic_coverage(invalid, TEXT).coverage.fully_supported


def test_pair_targeting_cost_and_no_partial_mutation_on_illegal_announcement():
    game, card, own, other = setup(mana=False)
    original = game.snapshot()
    assert game.announce_spell(0, card, other, source_target=own) is None
    assert game.snapshot() == original
    game.create_permanent(FOREST, 0, summoning_sick=False)
    game.create_permanent(PLAINS, 0, summoning_sick=False)
    assert game.announce_spell(0, card, own, source_target=own) is None
    assert game.announce_spell(0, card, other, source_target=other) is None
    assert game.announce_spell(0, card, other) is None
    assert card.zone == "hand" and other.damage == 0
    options = [
        option
        for option in game.legal_main_actions(0)
        if option.kind is ActionKind.CAST and option.object_id == card.object_id
    ]
    assert {(option.source_target_id, option.target_id) for option in options} == {
        (own.object_id, other.object_id)
    }
    spell = game.announce_spell(0, card, other, source_target=own)
    assert spell is not None and spell.source_target_id == own.object_id
    assert card.zone != "hand" and spell.zone == "stack"
    assert len([permanent for permanent in game.players[0].battlefield if permanent.tapped]) == 2


def test_power_at_resolution_damage_source_and_state_based_death():
    game, card, own, other = setup()
    spell = game.announce_spell(0, card, other, source_target=own)
    own.counters["+1/+1"] = 3
    game.resolve_top_of_stack()
    damage = [event for event in game.events if event["event"] == "damage_dealt"]
    assert len(damage) == 1 and damage[0]["source_id"] == own.object_id
    assert damage[0]["target_id"] == other.object_id and damage[0]["amount"] == 5
    assert other.zone == "former" and spell.zone != "stack"
    assert any(card.card.name == other.card.name for card in game.players[1].graveyard)
    assert [
        event["amount"]
        for event in game.events
        if event["event"] == "creature_power_damage_resolved"
    ] == [5]


@pytest.mark.parametrize("departing", ["source", "recipient", "both"])
def test_zone_departure_rechecks_targets_and_never_uses_last_known_power(departing):
    game, card, own, other = setup()
    game.announce_spell(0, card, other, source_target=own)
    if departing in {"source", "both"}:
        game.move_object(own, "graveyard", reason="test_removal")
    if departing in {"recipient", "both"}:
        game.move_object(other, "graveyard", reason="test_removal")
    game.resolve_top_of_stack()
    assert not any(event["event"] == "damage_dealt" for event in game.events)
    outcome = (
        "spell_resolved_no_effect"
        if departing == "both"
        else "creature_power_damage_resolved_no_damage"
    )
    assert any(event["event"] == outcome for event in game.events)


def test_zero_power_has_no_damage_and_sorcery_is_excluded_from_priority_options():
    zero = CardFact("Zero", "{G}", 1, "Creature", power=0, toughness=3)
    game, card, own, other = setup(source=zero)
    game.announce_spell(0, card, other, source_target=own)
    game.resolve_top_of_stack()
    assert other.damage == 0
    assert any(
        event["event"] == "creature_power_damage_resolved_no_damage" for event in game.events
    )
    game, card, own, other = setup(spell=SORCERY)
    game._begin_priority_window(allow_empty=True, priority_player=0)
    assert not any(option.object_id == card.object_id for option in game.legal_priority_actions(0))
    game, card, own, other = setup()
    game._begin_priority_window(allow_empty=True, priority_player=0)
    options = game.legal_priority_actions(0)
    assert any(
        option.object_id == card.object_id
        and option.source_target_id == own.object_id
        and option.target_id == other.object_id
        for option in options
    )


def test_replay_including_action_and_damage_provenance_is_deterministic():
    def run():
        game, card, own, other = setup()
        option = next(
            option for option in game.legal_main_actions(0) if option.object_id == card.object_id
        )
        game.execute_main_action(option)
        game.priority_state = None
        game.resolve_top_of_stack()
        game.check_invariants()
        return game.snapshot(), game.events

    assert run() == run()
