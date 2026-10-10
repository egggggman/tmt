"""Pure Oracle counterspell clauses use legal priority, targets, and stack zones."""

from dataclasses import replace
from pathlib import Path

import pytest

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter, CastKind
from tmnt_design_studio.engine07 import ActionKind, CardFact, Game, StackObject, load_facts
from tmnt_design_studio.pilot07 import AcceptancePilot

ROOT = Path(__file__).resolve().parents[1]
LAND = CardFact("Island", "", 0, "Basic Land — Island")
COUNTER = CardFact("Quiet Refusal", "{1}{U}", 2, "Instant", "Counter target noncreature spell.")
DRAW = CardFact("Insight", "{1}{U}", 2, "Sorcery", "Draw one card.")
BEAR = CardFact("Bear", "{1}", 1, "Creature", power=2, toughness=2)


def game(seed=2893):
    current = Game(([LAND] * 30, [LAND] * 30), seed=seed)
    current.begin_turn()
    for player in (0, 1):
        for _ in range(2):
            current.create_permanent(LAND, player, summoning_sick=False)
    return current


def stack_spell(current, card=DRAW, controller=0):
    kind = current.interpreter.cast_program(card).kind
    target = StackObject(current._allocate_object_id(), card, controller, controller, kind)
    current._register(target)
    current.stack.append(target)
    current._begin_priority_window()
    return target


def pass_all(current):
    while current.priority_state is not None:
        state = current.priority_state
        if state.resolution_pending:
            current.process_priority_resolution()
        else:
            current.execute_priority_action(
                next(
                    option
                    for option in current.legal_priority_actions(state.player_index)
                    if option.kind is ActionKind.PASS_PRIORITY
                )
            )


def test_frozen_negate_and_renamed_counter_derive_exact_grammar():
    catalog = load_card_data(
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json",
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json",
    )
    frozen = load_facts(catalog, {"Negate"})["Negate"]
    interpreter = CardInterpreter()
    for card in (frozen, COUNTER, replace(COUNTER, name="Yet Another Refusal")):
        assert interpreter.cast_program(card).kind is CastKind.COUNTER_TARGET_SPELL
        assert interpreter.counter_spell_semantic_coverage(card, card.oracle_text).fully_supported
        assert not interpreter.unsupported_fragments(card)
    for text in ("Counter target spell. Draw a card.", "Counter target creature spell."):
        altered = replace(COUNTER, oracle_text=text)
        assert interpreter.cast_program(altered).kind is CastKind.UNSUPPORTED


def test_response_pays_real_mana_and_counters_noncreature_before_resolution():
    current = game()
    target = stack_spell(current)
    hand = current.set_hand_for_testing(1, [COUNTER])[0]
    current.execute_priority_action(current.legal_priority_actions(0)[0])
    choices = current.legal_priority_actions(1)
    selected = AcceptancePilot().choose_priority(current.priority_view(1), choices)
    assert selected.kind is ActionKind.CAST and selected.target_id == target.object_id
    assert current.execute_priority_action(selected)
    assert hand.zone == "former"
    assert sum(source.tapped for source in current.players[1].battlefield) == 2
    pass_all(current)
    assert target.zone == "former"
    assert not any(event["event"] == "draw_spell_resolved" for event in current.events)
    assert any(
        event["event"] == "spell_countered" and event["target_spell_id"] == target.object_id
        for event in current.events
    )
    current.check_invariants()


def test_noncreature_filter_and_insufficient_mana_offer_no_response():
    current = game()
    target = stack_spell(current, BEAR)
    current.set_hand_for_testing(1, [COUNTER])
    current.execute_priority_action(current.legal_priority_actions(0)[0])
    assert not any(option.kind is ActionKind.CAST for option in current.legal_priority_actions(1))
    assert current.announce_spell(1, current.players[1].hand[0], target) is None

    current = game()
    stack_spell(current)
    current.set_hand_for_testing(1, [COUNTER])
    current.players[1].battlefield[0].tapped = True
    current.execute_priority_action(current.legal_priority_actions(0)[0])
    assert not any(option.kind is ActionKind.CAST for option in current.legal_priority_actions(1))


def test_generic_counter_target_spell_accepts_creature_and_deeper_stack_target():
    current = game()
    creature = stack_spell(current, BEAR)
    target = replace(COUNTER, oracle_text="Counter target spell.")
    current.set_hand_for_testing(1, [target])
    current.execute_priority_action(current.legal_priority_actions(0)[0])
    option = next(
        action for action in current.legal_priority_actions(1) if action.kind is ActionKind.CAST
    )
    assert option.target_id == creature.object_id
    current.execute_priority_action(option)
    pass_all(current)
    assert creature.zone == "former"
    assert not any(event["event"] == "creature_resolved" for event in current.events)

    current = game()
    first = stack_spell(current, controller=1)
    stack_spell(current, controller=0)
    latest = stack_spell(current, controller=1)
    current.set_hand_for_testing(0, [target])
    choices = [
        option for option in current.legal_priority_actions(0) if option.kind is ActionKind.CAST
    ]
    assert {option.target_id for option in choices} == {
        first.object_id,
        latest.object_id,
    }
    assert AcceptancePilot().choose_priority(
        current.priority_view(0), tuple(choices)
    ).target_id == (latest.object_id)
    current.execute_priority_action(
        next(option for option in choices if option.target_id == first.object_id)
    )
    pass_all(current)
    assert first.zone == "former"
    current.check_invariants()


def test_nested_counter_war_preserves_original_spell_and_priority():
    current = game()
    original = stack_spell(current)
    current.set_hand_for_testing(0, [COUNTER])
    current.set_hand_for_testing(1, [COUNTER])
    current.execute_priority_action(current.legal_priority_actions(0)[0])
    first = next(
        option for option in current.legal_priority_actions(1) if option.kind is ActionKind.CAST
    )
    current.execute_priority_action(first)
    current.execute_priority_action(
        next(
            option
            for option in current.legal_priority_actions(1)
            if option.kind is ActionKind.PASS_PRIORITY
        )
    )
    second = next(
        option for option in current.legal_priority_actions(0) if option.kind is ActionKind.CAST
    )
    assert second.target_id == current.stack[-1].object_id
    current.execute_priority_action(second)
    pass_all(current)
    counters = [event for event in current.events if event["event"] == "spell_countered"]
    assert len(counters) == 1 and counters[0]["target_card"] == COUNTER.name
    assert original.zone == "former"
    assert any(event["event"] == "draw_spell_resolved" for event in current.events)
    current.check_invariants()


def test_target_departure_makes_counter_spell_resolve_without_effect():
    current = game()
    target = stack_spell(current)
    current.set_hand_for_testing(1, [COUNTER])
    current.execute_priority_action(current.legal_priority_actions(0)[0])
    option = next(
        choice for choice in current.legal_priority_actions(1) if choice.kind is ActionKind.CAST
    )
    current.execute_priority_action(option)
    current.move_object(target, "graveyard", reason="test_prior_counter")
    pass_all(current)
    assert any(
        event["event"] == "spell_resolved_no_effect"
        and event.get("reason") == "all_targets_illegal"
        for event in current.events
    )
    assert not any(event["event"] == "spell_countered" for event in current.events)


@pytest.mark.parametrize("seed", (2894, 2895))
def test_counter_response_replays_exactly(seed):
    def run():
        current = game(seed)
        stack_spell(current)
        current.set_hand_for_testing(1, [COUNTER])
        current.execute_priority_action(current.legal_priority_actions(0)[0])
        selected = AcceptancePilot().choose_priority(
            current.priority_view(1), current.legal_priority_actions(1)
        )
        current.execute_priority_action(selected)
        pass_all(current)
        return current.snapshot(), current.events

    assert run() == run()
