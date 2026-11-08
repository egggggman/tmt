"""Independent adversarial checks for PR #404 cast dispatch."""

from pathlib import Path

import pytest

from tmnt_design_studio.engine07 import (
    ActionKind,
    CardFact,
    Game,
    TriggeredAbilityObject,
    TriggerEffect,
    load_facts,
)
from tmnt_design_studio.stage002 import load_catalog

ROOT = Path(__file__).resolve().parents[1]
CATALOG = load_catalog(ROOT)
FACTS = load_facts(CATALOG, {"Ravenous Robots", "Spicy Oatmeal Pizza", "Ooze Spill"})
ROBOTS = FACTS["Ravenous Robots"]
PIZZA = FACTS["Spicy Oatmeal Pizza"]
OOZE_SPILL = FACTS["Ooze Spill"]
MOUNTAIN = CardFact("Mountain", "", 0, "Basic Land Ã¢â‚¬â€ Mountain")
ISLAND = CardFact("Island", "", 0, "Basic Land Ã¢â‚¬â€ Island")


def resolve_one_priority_cycle(game):
    if game.priority_state is None:
        game._begin_priority_window()
    for _ in range(2):
        state = game.priority_state
        assert state is not None and not state.resolution_pending
        pass_option = next(
            option
            for option in game.legal_priority_actions(state.player_index)
            if option.kind is ActionKind.PASS_PRIORITY
        )
        assert game.execute_priority_action(pass_option)
    assert game.priority_state is not None and game.priority_state.resolution_pending
    assert game.process_priority_resolution()


def test_execute_main_action_dispatches_all_authenticated_cast_triggers_to_active_player_priority():
    game = Game(([MOUNTAIN] * 20, [MOUNTAIN] * 20), seed=404001)
    game.begin_turn()
    game._active_player = 1
    robots = [game.create_permanent(ROBOTS, 1, summoning_sick=False) for _ in range(2)]
    game.create_permanent(MOUNTAIN, 1, summoning_sick=False)
    card = CardFact("Synthetic Artifact", "{1}", 1, "Artifact", "")
    artifact = game.set_hand_for_testing(1, [card])[0]
    cast_option = next(
        option
        for option in game.legal_main_actions(1)
        if option.kind is ActionKind.CAST and option.object_id == artifact.object_id
    )

    assert game.execute_main_action(cast_option)

    spell = next(item for item in game.stack if getattr(item, "card", None) is card)
    cast_events = [
        event
        for event in game._rules_events.values()
        if event.kind.value == "spell_cast" and event.source_id == spell.object_id
    ]
    assert len(cast_events) == 1
    cast_event = cast_events[0]
    triggers = [
        item
        for item in game.stack
        if isinstance(item, TriggeredAbilityObject)
        and item.effect is TriggerEffect.CREATE_TOKEN
        and item.event is cast_event
    ]
    assert len(triggers) == 2
    assert {trigger.source_id for trigger in triggers} == {source.object_id for source in robots}
    assert game.priority_state is not None
    assert game.priority_state.player_index == 1
    first_window = next(
        event for event in game.events if event.get("event") == "response_window_opened"
    )
    assert first_window["stack_object_id"] == game.stack[-1].object_id
    assert first_window["priority_epoch"] == game.priority_state.epoch

    passes = {}
    for _ in range(16):
        if not game.stack:
            break
        state = game.priority_state
        assert state is not None
        if state.resolution_pending:
            assert game.process_priority_resolution()
            continue
        pass_option = next(
            option
            for option in game.legal_priority_actions(state.player_index)
            if option.kind is ActionKind.PASS_PRIORITY
        )
        passes.setdefault(state.epoch, []).append(state.player_index)
        assert game.execute_priority_action(pass_option)

    assert not game.stack
    assert game.priority_state is None
    assert passes and all(players == [1, 0] for players in passes.values())
    assert (
        sum(
            permanent.is_token and permanent.card.name == "Robot"
            for permanent in game.players[1].battlefield
        )
        == 2
    )
    game.check_invariants()


def test_main_action_artifact_cast_can_be_countered_after_its_cast_trigger_resolves():
    game = Game(([MOUNTAIN] * 20, [ISLAND] * 20), seed=404002)
    game.begin_turn()
    game.create_permanent(ROBOTS, 0, summoning_sick=False)
    for _ in range(3):
        game.create_permanent(MOUNTAIN, 0, summoning_sick=False)
        game.create_permanent(ISLAND, 1, summoning_sick=False)
    pizza = game.set_hand_for_testing(0, [PIZZA])[0]
    counter = game.set_hand_for_testing(1, [OOZE_SPILL])[0]
    cast_option = next(
        option
        for option in game.legal_main_actions(0)
        if option.kind is ActionKind.CAST and option.object_id == pizza.object_id
    )

    assert game.execute_main_action(cast_option)
    cast_event = next(
        event
        for event in game._rules_events.values()
        if event.kind.value == "spell_cast" and event.source_id == game.stack[0].object_id
    )
    resolve_one_priority_cycle(game)
    assert (
        sum(
            permanent.is_token and permanent.card.name == "Robot"
            for permanent in game.players[0].battlefield
        )
        == 1
    )
    if game.priority_state is None:
        game._begin_priority_window()
    if game.priority_state.player_index != 1:
        pass_option = next(
            option
            for option in game.legal_priority_actions(game.priority_state.player_index)
            if option.kind is ActionKind.PASS_PRIORITY
        )
        assert game.execute_priority_action(pass_option)
    counter_option = next(
        option
        for option in game.legal_priority_actions(1)
        if option.kind is ActionKind.CAST and option.object_id == counter.object_id
    )
    assert game.execute_priority_action(counter_option)
    resolve_one_priority_cycle(game)

    assert pizza.zone == "former"
    assert cast_event.card_oracle_id == PIZZA.oracle_id
    assert (
        sum(
            event.get("event") == "trigger_stacked" and event.get("source") == PIZZA.name
            for event in game.events
        )
        == 0
    )
    assert (
        sum(
            permanent.is_token and permanent.card.name == "Robot"
            for permanent in game.players[0].battlefield
        )
        == 1
    )
    assert not game.stack
    game.check_invariants()


def test_stale_engine_cast_option_rejection_does_not_mutate_state_or_emit_cast_event():
    game = Game(([MOUNTAIN] * 20, [MOUNTAIN] * 20), seed=404003)
    game.begin_turn()
    game.create_permanent(MOUNTAIN, 0, summoning_sick=False)
    card = CardFact("Stale Synthetic Artifact", "{1}", 1, "Artifact", "")
    stale_card = game.set_hand_for_testing(0, [card])[0]
    stale_option = next(
        option
        for option in game.legal_main_actions(0)
        if option.kind is ActionKind.CAST and option.object_id == stale_card.object_id
    )
    game.move_object(stale_card, "graveyard", reason="independent_stale_action_fixture")
    before = game.snapshot()
    before_events = tuple(game.events)

    with pytest.raises(ValueError, match="not currently legal"):
        game.execute_main_action(stale_option)

    assert game.snapshot() == before
    assert tuple(game.events) == before_events
    assert not any(
        event.kind.value == "spell_cast" and event.source_id == stale_card.object_id
        for event in game._rules_events.values()
    )
    game.check_invariants()
