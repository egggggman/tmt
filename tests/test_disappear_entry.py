"""Shared departure history and complete conditional creature-entry effects."""

from dataclasses import replace

import pytest

from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import CardFact, Game, TriggeredAbilityObject, TurnStep

LAND = CardFact("Swamp", "", 0, "Basic Land — Swamp")
TOKEN_TEXT = (
    "Disappear — When this creature enters, if a permanent left the battlefield "
    "under your control this turn, create a 1/1 black Ninja creature token."
)
COUNTER_TEXT = (
    "Disappear — This creature enters with two +1/+1 counters on it if a permanent "
    "left the battlefield under your control this turn."
)
TOKEN_SOURCE = CardFact(
    "Test Mystic", "{3}{B}", 4, "Creature — Human Ninja", TOKEN_TEXT, power=2, toughness=4
)
COUNTER_SOURCE = CardFact(
    "Test Pals", "{2}{B}", 3, "Creature — Mutant", COUNTER_TEXT, power=1, toughness=1
)


def game():
    result = Game(([LAND] * 20, [LAND] * 20), seed=1449)
    result.begin_turn()
    return result


def enter(result, card, controller=0, *, defer=False):
    hand = result.set_hand_for_testing(controller, [card])[0]
    permanent = result.move_object(hand, "battlefield", controller=controller)
    result._process_creature_entered_triggers(permanent, defer_triggers=defer)
    return permanent


def pass_priority(result):
    while result.priority_state is not None:
        if result.priority_state.resolution_pending:
            result.process_priority_resolution()
        else:
            result.execute_priority_action(
                result.legal_priority_actions(result.priority_state.player_index)[0]
            )


def test_generic_interpreter_accepts_complete_effects_but_not_extra_followup():
    interpreter = CardInterpreter()
    renamed = replace(TOKEN_SOURCE, name="Any Ninja")
    fragment = interpreter.fragments(renamed)[0]
    assert interpreter.token_semantic_coverage(renamed, fragment).fully_supported
    assert not interpreter.unsupported_fragments(renamed)
    assert not interpreter.unsupported_fragments(COUNTER_SOURCE)
    extra = replace(TOKEN_SOURCE, oracle_text=TOKEN_TEXT + " Draw a card.")
    assert not interpreter.token_semantic_coverage(
        extra, interpreter.fragments(extra)[0]
    ).fully_supported


def test_controller_at_departure_even_when_owner_differs_and_source_arrives_later():
    result = game()
    stolen = result.create_permanent(LAND, 1, controller=0)
    result.move_object(stolen, "graveyard")
    departure = [e for e in result.events if e["event"] == "permanent_departed"]
    assert len(departure) == 1 and departure[0]["controller"] == 0
    assert result._left_under_control_this_turn(0)
    assert not result._left_under_control_this_turn(1)
    source = enter(result, TOKEN_SOURCE)
    assert any(e["event"] == "trigger_stacked" for e in result.events)
    assert len(result.stack) == 1 and isinstance(result.stack[-1], TriggeredAbilityObject)
    assert not any(p.card.name == "Ninja" for p in result.players[0].battlefield)
    with pytest.raises(ValueError, match="all players pass"):
        result.resolve_top_of_stack()
    pass_priority(result)
    assert source.zone == "battlefield"
    assert sum(p.card.name == "Ninja" for p in result.players[0].battlefield) == 1
    result.check_invariants()


def test_intervening_if_absent_at_entry_does_not_trigger_and_entry_counters_apply_immediately():
    result = game()
    enter(result, TOKEN_SOURCE)
    assert not result.stack
    assert not any(p.card.name == "Ninja" for p in result.players[0].battlefield)
    vanilla = enter(result, COUNTER_SOURCE)
    assert vanilla.counters.get("+1/+1", 0) == 0
    result.move_object(result.create_permanent(LAND, 0), "hand")
    boosted = enter(result, COUNTER_SOURCE)
    assert boosted.counters["+1/+1"] == 2
    assert boosted.power == 3
    result.check_invariants()


def test_control_change_is_not_a_departure_but_later_hand_return_records_last_controller():
    result = game()
    foreign = result.create_permanent(LAND, 1)
    result.change_controller(foreign, 0)
    assert not result._left_under_control_this_turn(0)
    result.move_object(foreign, "hand")
    assert result._left_under_control_this_turn(0)
    assert not result._left_under_control_this_turn(1)
    result.check_invariants()


def test_departure_provenance_rejects_mutated_controller_history():
    result = game()
    result.move_object(result.create_permanent(LAND, 0), "exile")
    record = next(e for e in result.events if e["event"] == "permanent_departed")
    record["controller"] = 1
    try:
        result.check_invariants()
    except AssertionError as error:
        assert "departure history" in str(error)
    else:
        raise AssertionError("forged departure controller passed invariants")


def test_departure_history_expires_at_next_turn_and_trigger_survives_source_departure():
    result = game()
    result.move_object(result.create_permanent(LAND, 0), "graveyard")
    source = enter(result, TOKEN_SOURCE, defer=True)
    result.move_object(source, "graveyard")
    result._begin_priority_window()
    pass_priority(result)
    assert sum(p.card.name == "Ninja" for p in result.players[0].battlefield) == 1
    result.advance_to(TurnStep.COMBAT_DAMAGE)
    result.resolve_combat_damage()
    result.advance_to(TurnStep.CLEANUP)
    result.begin_turn()
    assert not result._left_under_control_this_turn(0)
    plain = enter(result, COUNTER_SOURCE)
    assert plain.counters.get("+1/+1", 0) == 0
    result.check_invariants()


def test_replay_is_deterministic():
    def replay():
        result = game()
        result.move_object(result.create_permanent(LAND, 0), "exile")
        enter(result, TOKEN_SOURCE)
        pass_priority(result)
        result.check_invariants()
        return result.events

    assert replay() == replay()
