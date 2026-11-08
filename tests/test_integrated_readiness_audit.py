"""Reviewer-only synthetic composition checks for the accumulated source chain."""

from pathlib import Path

import pytest

from tmnt_design_studio.engine07 import (
    ActionKind,
    Game,
    TriggeredAbilityObject,
    TriggerEffect,
    load_facts,
)
from tmnt_design_studio.mana_ledger07 import ManaSpendingContext
from tmnt_design_studio.stage002 import load_catalog

ROOT = Path(__file__).resolve().parents[1]
CATALOG = load_catalog(ROOT)
FACTS = load_facts(
    CATALOG,
    {"Purple Dragon Punks", "Ravenous Robots", "Spicy Oatmeal Pizza", "Mountain"},
)
PUNKS = FACTS["Purple Dragon Punks"]
ROBOTS = FACTS["Ravenous Robots"]
PIZZA = FACTS["Spicy Oatmeal Pizza"]
MOUNTAIN = FACTS["Mountain"]


def make_game():
    game = Game(
        ([MOUNTAIN] * 20, [MOUNTAIN] * 20),
        seed=40138601,
        damage_target_chooser=lambda _controller, _source, offered: (
            "player:1" if "player:1" in offered else None
        ),
    )
    game.begin_turn()
    punks = game.create_permanent(PUNKS, 0, summoning_sick=False)
    robots = game.create_permanent(ROBOTS, 0, summoning_sick=False)
    lands = [game.create_permanent(MOUNTAIN, 0, summoning_sick=False) for _ in range(2)]
    pizza_card = game.set_hand_for_testing(0, [PIZZA])[0]
    return game, punks, robots, lands, pizza_card


def produce_punks_mana(game, punks, pizza_card):
    option = next(
        option
        for option in game.legal_main_actions(0)
        if option.kind is ActionKind.ACTIVATE_ABILITY and option.object_id == punks.object_id
    )
    assert f"cast:{pizza_card.object_id}" in option.mana_followups
    assert game.execute_main_action(option)
    return next(
        item for item in game.floating_mana.productions(0) if item.source_id == punks.object_id
    )


def assert_composed_resolution(game, punks, robots, lands, pizza_card, production):
    pizza_spell = next(item for item in game.stack if item.card is PIZZA)
    cast_event = next(
        event
        for event in game._rules_events.values()
        if event.kind.value == "spell_cast" and event.source_id == pizza_spell.object_id
    )
    robot_triggers = [
        item
        for item in game.stack
        if isinstance(item, TriggeredAbilityObject)
        and item.effect is TriggerEffect.CREATE_TOKEN
        and item.source_id == robots.object_id
    ]
    assert len(robot_triggers) == 1
    assert robot_triggers[0].event is cast_event
    assert cast_event.card_oracle_id == PIZZA.oracle_id
    assert (
        len(
            [
                event
                for event in game._rules_events.values()
                if event.kind.value == "spell_cast" and event.source_id == pizza_spell.object_id
            ]
        )
        == 1
    )
    allocation = next(
        item
        for item in game.floating_mana.consumptions(0)
        if item.source_event_id == production.event_id
    )
    assert allocation.payment_id == pizza_card.object_id
    assert allocation.spending_context is ManaSpendingContext.ARTIFACT_SPELL
    assert all(land.tapped for land in lands)

    for _ in range(16):
        if not game.stack:
            break
        if game.priority_state is None:
            game._begin_priority_window()
        state = game.priority_state
        assert state is not None
        if state.resolution_pending:
            game.process_priority_resolution()
            continue
        option = next(
            option
            for option in game.legal_priority_actions(state.player_index)
            if option.kind is ActionKind.PASS_PRIORITY
        )
        assert game.execute_priority_action(option)
    assert not game.stack
    assert game.priority_state is None

    robot_tokens = [
        item for item in game.players[0].battlefield if item.is_token and item.card.name == "Robot"
    ]
    pizza_permanent = next(
        item
        for item in game.players[0].battlefield
        if getattr(item.card, "oracle_id", None) == PIZZA.oracle_id
    )
    pizza_triggers = [
        event
        for event in game.events
        if event.get("event") == "trigger_stacked" and event.get("source") == PIZZA.name
    ]
    damage = [event for event in game.events if event.get("event") == "damage_dealt"]
    assert len(robot_tokens) == 1
    assert robot_tokens[0].power == robot_tokens[0].toughness == 1
    assert len(pizza_triggers) == 1
    assert [event["amount"] for event in damage] == [4, 3]
    assert [game.players[1].life, game.players[0].life] == [16, 17]
    assert all(event["source_id"] == pizza_permanent.object_id for event in damage)
    assert (
        len(
            [
                event
                for event in game.events
                if event.get("event") == "floating_mana_produced"
                and event.get("source_id") == punks.object_id
            ]
        )
        == 1
    )
    game.check_invariants()


def test_announce_spell_composes_punks_payment_robot_trigger_and_pizza_etb():
    game, punks, robots, lands, pizza_card = make_game()
    production = produce_punks_mana(game, punks, pizza_card)
    pizza_spell = game.announce_spell(0, pizza_card)
    assert pizza_spell is not None
    assert_composed_resolution(game, punks, robots, lands, pizza_card, production)


def test_main_cast_wrapper_raises_on_pending_artifact_cast_trigger():
    game, punks, robots, lands, pizza_card = make_game()
    production = produce_punks_mana(game, punks, pizza_card)
    cast_option = next(
        option
        for option in game.legal_main_actions(0)
        if option.kind is ActionKind.CAST and option.object_id == pizza_card.object_id
    )
    with pytest.raises(
        ValueError, match="artifact-cast token trigger requires Priority resolution"
    ):
        game.execute_main_action(cast_option)

    pizza_spell = next(item for item in game.stack if item.card is PIZZA)
    cast_event = next(
        event
        for event in game._rules_events.values()
        if event.kind.value == "spell_cast" and event.source_id == pizza_spell.object_id
    )
    assert pizza_card.zone == "former"
    assert game.priority_state is None
    assert len(game.stack) == 2 and game.stack[-1].source_id == robots.object_id
    assert cast_event.card_oracle_id == PIZZA.oracle_id
    allocation = next(
        item
        for item in game.floating_mana.consumptions(0)
        if item.source_event_id == production.event_id
    )
    assert allocation.payment_id == pizza_card.object_id
    assert allocation.spending_context is ManaSpendingContext.ARTIFACT_SPELL
    assert all(land.tapped for land in lands)
    assert all(
        event.get("event") != "trigger_stacked" or event.get("source") != PIZZA.name
        for event in game.events
    )
    game.check_invariants()
