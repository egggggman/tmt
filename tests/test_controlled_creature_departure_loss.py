"""Complete shared creature-departure life-loss trigger at Class level one."""

from dataclasses import replace

import pytest

from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import CardFact, Game, TriggeredAbilityObject, TriggerEffect

LAND = CardFact("Swamp", "", 0, "Basic Land — Swamp")
BEAR = CardFact("Bear", "{1}{B}", 2, "Creature — Bear", power=2, toughness=2)
CLAUSE = "Whenever a creature you control leaves the battlefield, each opponent loses 1 life."
CLASS = CardFact("Test Class", "{2}{B}", 3, "Enchantment — Class", CLAUSE)


def setup():
    game = Game(([LAND] * 20, [LAND] * 20), seed=321)
    game.begin_turn()
    source = game.create_permanent(CLASS, 0)
    return game, source


def pass_priority(game):
    while game.priority_state is not None:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            game.execute_priority_action(
                game.legal_priority_actions(game.priority_state.player_index)[0]
            )


def test_renamed_generic_clause_and_complete_fragment_rejection():
    interpreter = CardInterpreter()
    assert interpreter.unsupported_fragments(CLASS) == ()
    assert interpreter.unsupported_fragments(replace(CLASS, name="Another Class")) == ()
    extra = replace(CLASS, oracle_text=CLAUSE + " Draw a card.")
    assert interpreter.unsupported_fragments(extra)


@pytest.mark.parametrize("destination", ["graveyard", "hand", "exile"])
def test_controlled_creature_departure_uses_priority_and_preserves_event_provenance(destination):
    game, source = setup()
    creature = game.create_permanent(BEAR, 1, controller=0)
    game.move_object(creature, destination)
    game.check_state_based_actions()
    assert len(game.stack) == 1
    trigger = game.stack[-1]
    assert isinstance(trigger, TriggeredAbilityObject)
    assert trigger.effect is TriggerEffect.CONTROLLED_CREATURE_LEFT_OPPONENT_LOSS
    assert trigger.source_id == source.object_id
    with pytest.raises(ValueError, match="all players pass"):
        game.resolve_top_of_stack()
    assert game.players[1].life == 20
    pass_priority(game)
    assert game.players[1].life == 19
    assert game.players[0].life == 20
    assert any(
        event["event"] == "controlled_creature_departure_life_loss"
        and event["departed_id"] == creature.object_id
        for event in game.events
    )
    game.check_invariants()


def test_wrong_controller_and_noncreature_leave_do_not_trigger():
    game, _ = setup()
    game.move_object(game.create_permanent(BEAR, 1), "graveyard")
    game.move_object(game.create_permanent(LAND, 0), "graveyard")
    game.check_state_based_actions()
    assert not game.stack
    assert game.players[1].life == 20


def test_self_departure_still_triggers_for_a_creature_source():
    creature_source = CardFact(
        "Creature Watcher", "{1}{B}", 2, "Creature — Mutant", CLAUSE, power=2, toughness=2
    )
    game = Game(([LAND] * 20, [LAND] * 20), seed=18)
    game.begin_turn()
    source = game.create_permanent(creature_source, 0)
    game.move_object(source, "graveyard")
    game.check_state_based_actions()
    assert len(game.stack) == 1
    pass_priority(game)
    assert game.players[1].life == 19
    game.check_invariants()


def test_source_departs_after_trigger_and_simultaneous_lethal_are_deterministic():
    def replay():
        game, source = setup()
        first = game.create_permanent(BEAR, 0)
        second = game.create_permanent(BEAR, 0)
        game.put_permanents_into_graveyard((first, second), state_based_action="test")
        game.move_object(source, "graveyard")
        game.check_state_based_actions()
        assert len(game.stack) == 2
        pass_priority(game)
        game.check_invariants()
        return game.players[1].life, game.events

    assert replay() == replay()
    assert replay()[0] == 18
