"""Generic Class level-two creature-departure life trigger and frozen history."""

from dataclasses import replace
from pathlib import Path

import pytest

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import CardFact, Game, TriggerEffect, TurnStep, load_facts

LAND = CardFact("Plains", "", 0, "Basic Land — Plains")
BEAR = CardFact("Example Bear", "{1}{W}", 2, "Creature — Bear", power=2, toughness=2)
EFFECT = (
    "Whenever a creature you control leaves the battlefield, if it had a counter on it, "
    "you gain 2 life."
)
LEVEL = "{2}{W}: Level 2"
CLASS = CardFact(
    "Example Leadership",
    "{1}{W}",
    2,
    "Enchantment — Class",
    "(Gain the next level as a sorcery to add its ability.)\n"
    "Whenever you attack, put a +1/+1 counter on target attacking creature.\n"
    f"{LEVEL}\n{EFFECT}\n{{3}}{{W}}: Level 3\n"
    "Whenever you cast a spell, put a +1/+1 counter on each creature you control.",
)


def drain(game):
    while game.priority_state is not None:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            game.execute_priority_action(
                game.legal_priority_actions(game.priority_state.player_index)[0]
            )


def setup(seed=289, *, mana=3):
    game = Game(([LAND] * 30, [LAND] * 30), seed=seed)
    game.begin_turn()
    for _ in range(mana):
        game.create_permanent(LAND, 0, summoning_sick=False)
    source = game.create_permanent(CLASS, 0)
    return game, source


def level_two(game, source):
    assert game.activate_ability(0, source, LEVEL)
    assert source.class_level == 1
    drain(game)
    assert source.class_level == 2


def test_exact_frozen_oracle_and_complete_level_only():
    catalog = Path(__file__).resolve().parents[1] / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
    frozen = load_facts(
        load_card_data(catalog, catalog.with_suffix(".manifest.json")), {"Leader's Talent"}
    )["Leader's Talent"]
    interpreter = CardInterpreter()
    assert frozen.oracle_text == CLASS.oracle_text
    assert interpreter.countered_creature_left_life(frozen, EFFECT) == 2
    assert interpreter.class_level_child(frozen, 2) == EFFECT
    assert interpreter.activated_ability_semantics(frozen, LEVEL).coverage.fully_supported
    assert not interpreter.activated_ability_semantics(
        frozen, "{3}{W}: Level 3"
    ).coverage.fully_supported
    for changed in (
        replace(CLASS, oracle_text=CLASS.oracle_text.replace(EFFECT, EFFECT + " Draw a card.")),
        replace(CLASS, oracle_text=CLASS.oracle_text.replace(EFFECT, EFFECT + "\nScry 1.")),
        replace(CLASS, oracle_text=CLASS.oracle_text.replace(f"{LEVEL}\n{EFFECT}", EFFECT)),
    ):
        assert interpreter.class_level_child(changed, 2) is None
        assert not interpreter.activated_ability_semantics(changed, LEVEL).coverage.fully_supported
    assert interpreter.class_level_child(replace(CLASS, name="Another Class"), 2) == EFFECT


def test_cost_timing_stack_priority_and_countered_leave():
    game, source = setup()
    creature = game.create_permanent(BEAR, 0)
    game.place_counters(creature, "+1/+1", 1, source_card="Fixture", oracle_fragment="test")
    game.players[0].battlefield[0].tapped = True
    assert game.activation_payment_plan(0, source, LEVEL) is None
    game.players[0].battlefield[0].tapped = False
    level_two(game, source)
    assert game.activation_payment_plan(0, source, LEVEL) is None
    game.move_object(creature, "exile")
    game.check_state_based_actions()
    assert len(game.stack) == 1
    trigger = game.stack[-1]
    assert trigger.effect is TriggerEffect.CONTROLLED_COUNTERED_CREATURE_LEFT_LIFE
    assert trigger.source_id == source.object_id
    assert game.players[0].life == 20
    with pytest.raises(ValueError, match="all players pass"):
        game.resolve_top_of_stack()
    game.move_object(source, "graveyard")
    drain(game)
    assert game.players[0].life == 22
    assert game.players[1].life == 20
    assert any(
        event["event"] == "countered_creature_departure_life_resolved"
        and event["departed_id"] == creature.object_id
        for event in game.events
    )
    game.check_invariants()


def test_no_counter_wrong_controller_suppression_and_active_level():
    game, source = setup(290)
    creature = game.create_permanent(BEAR, 0)
    game.move_object(creature, "hand")
    game.check_state_based_actions()
    assert not game.stack  # level one, and no counter
    level_two(game, source)
    another = game.create_permanent(BEAR, 1, controller=0)
    game.move_object(another, "graveyard")
    game.check_state_based_actions()
    assert not game.stack  # level two, but no counter
    opponent = game.create_permanent(BEAR, 1)
    game.place_counters(opponent, "+1/+1", 1, source_card="Fixture", oracle_fragment="test")
    game.move_object(opponent, "graveyard")
    game.check_state_based_actions()
    assert not game.stack
    suppressed = game.create_permanent(BEAR, 0)
    game.place_counters(suppressed, "stun", 1, source_card="Fixture", oracle_fragment="test")
    source.ability_loss_timestamp = (9999, 9999)
    game.move_object(suppressed, "graveyard")
    game.check_state_based_actions()
    assert not game.stack
    game.check_invariants()


def test_controller_history_source_independence_and_simultaneous_replay():
    def replay():
        game, source = setup(291)
        level_two(game, source)
        first = game.create_permanent(BEAR, 1, controller=0)
        second = game.create_permanent(BEAR, 0)
        for creature in (first, second):
            game.place_counters(creature, "+1/+1", 1, source_card="Fixture", oracle_fragment="test")
        game.put_permanents_into_graveyard((first, second), state_based_action="test")
        game.change_controller(source, 1)
        game.check_state_based_actions()
        assert len(game.stack) == 2
        drain(game)
        game.check_invariants()
        return game.players[0].life, game.events, game.snapshot()

    first = replay()
    assert first == replay()
    assert first[0] == 24


def test_leave_history_rejects_counter_or_event_relink():
    game, source = setup(292)
    level_two(game, source)
    creature = game.create_permanent(BEAR, 0)
    game.place_counters(creature, "+1/+1", 1, source_card="Fixture", oracle_fragment="test")
    game.move_object(creature, "graveyard")
    game.check_state_based_actions()
    trigger = game.stack[-1]
    trigger.source_id = "fabricated"
    with pytest.raises(ValueError, match="invalid event provenance"):
        drain(game)


def test_level_up_is_sorcery_and_uncompleted_level_three_stays_unavailable():
    game, source = setup(293)
    game.advance_to(TurnStep.DECLARE_ATTACKERS)
    assert not game.activate_ability(0, source, LEVEL)
    assert game.activation_payment_plan(0, source, "{3}{W}: Level 3") is None
    game.check_invariants()
