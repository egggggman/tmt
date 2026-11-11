"""Reviewer-only synthetic composition checks for the accumulated source chain."""

from pathlib import Path

from tmnt_design_studio.conformance07 import semantic_key
from tmnt_design_studio.engine07 import (
    ActionKind,
    CardFact,
    Game,
    TriggeredAbilityObject,
    TriggerEffect,
    load_facts,
)
from tmnt_design_studio.mana_ledger07 import ManaSpendingContext
from tmnt_design_studio.stage002 import (
    DeckSpec,
    GameSpec,
    _authoritative_execution_index,
    load_catalog,
    reconcile_snapshot,
)

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

    priority_passes = {}
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
        priority_passes.setdefault(state.epoch, []).append(state.player_index)
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
    robot_resolution_index = next(
        index
        for index, event in enumerate(game.events)
        if event.get("event") == "trigger_resolved"
        and event.get("source_id") == robots.object_id
        and event.get("effect") == TriggerEffect.CREATE_TOKEN.value
    )
    pizza_trigger_stacked_index = next(
        index
        for index, event in enumerate(game.events)
        if event.get("event") == "trigger_stacked" and event.get("source") == PIZZA.name
    )
    pizza_trigger_resolution_index = next(
        index
        for index, event in enumerate(game.events)
        if event.get("event") == "trigger_resolved"
        and event.get("source_id") == pizza_permanent.object_id
        and event.get("effect") == TriggerEffect.DEAL_DAMAGE.value
    )
    damage = [event for event in game.events if event.get("event") == "damage_dealt"]
    assert len(robot_tokens) == 1
    assert robot_tokens[0].power == robot_tokens[0].toughness == 1
    assert len(pizza_triggers) == 1
    assert robot_resolution_index < pizza_trigger_stacked_index < pizza_trigger_resolution_index
    assert [event["amount"] for event in damage] == [4, 3]
    assert [game.players[1].life, game.players[0].life] == [16, 17]
    assert all(event["source_id"] == pizza_permanent.object_id for event in damage)
    assert game.floating_mana.snapshot(0) == {}
    assert len(priority_passes) >= 3
    assert all(players == [0, 1] for players in priority_passes.values())
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

    snapshot = game.snapshot()
    index = _authoritative_execution_index(snapshot)
    for event in damage:
        assert index[("damage_dealt", event["event_id"])] == [
            {
                "source_id": pizza_permanent.object_id,
                "oracle_fragment": PIZZA.oracle_text.splitlines()[0],
            }
        ]
    assert not snapshot["conformance"]["stop_records"]

    robot_key = semantic_key(ROBOTS.oracle_id, 0, 0, ROBOTS.oracle_text.splitlines()[0])
    pizza_key = semantic_key(PIZZA.oracle_id, 0, 0, PIZZA.oracle_text.splitlines()[0])
    punks_fragment = PUNKS.oracle_text.splitlines()[0]
    punks_key = semantic_key(PUNKS.oracle_id, 0, 0, punks_fragment)
    snapshot["stage002_presence"] = [
        {
            "semantic_key": punks_key,
            "oracle_fragment": punks_fragment,
            "origin": "deck_card",
            "object_ids": [punks.object_id],
            "is_token": False,
        },
        {
            "semantic_key": robot_key,
            "oracle_fragment": ROBOTS.oracle_text.splitlines()[0],
            "origin": "deck_card",
            "object_ids": [robots.object_id],
            "is_token": False,
        },
        {
            "semantic_key": pizza_key,
            "oracle_fragment": PIZZA.oracle_text.splitlines()[0],
            "origin": "deck_card",
            "object_ids": [pizza_permanent.object_id],
            "is_token": False,
        },
    ]
    manifest = {
        "decks": [
            {
                "cards": [
                    {
                        "fragments": [
                            {
                                "semantic_key": robot_key,
                                "oracle_fragment": ROBOTS.oracle_text.splitlines()[0],
                            },
                            {
                                "semantic_key": pizza_key,
                                "oracle_fragment": PIZZA.oracle_text.splitlines()[0],
                            },
                            {"semantic_key": punks_key, "oracle_fragment": punks_fragment},
                        ]
                    }
                ]
            }
        ]
    }
    report = reconcile_snapshot(
        GameSpec(
            "integrated-punks-pizza-robots",
            "synthetic",
            40138601,
            "canonical",
            (DeckSpec("A", ""), DeckSpec("B", "")),
        ),
        snapshot,
        manifest,
    )
    assert not report["stop_records"]


def test_announce_spell_composes_punks_payment_robot_trigger_and_pizza_etb():
    game, punks, robots, lands, pizza_card = make_game()
    production = produce_punks_mana(game, punks, pizza_card)
    pizza_spell = game.announce_spell(0, pizza_card)
    assert pizza_spell is not None
    assert_composed_resolution(game, punks, robots, lands, pizza_card, production)


def test_main_cast_action_composes_punks_followup_robot_trigger_and_pizza_etb():
    game, punks, robots, lands, pizza_card = make_game()
    production = produce_punks_mana(game, punks, pizza_card)
    cast_option = next(
        option
        for option in game.legal_main_actions(0)
        if option.kind is ActionKind.CAST and option.object_id == pizza_card.object_id
    )
    assert game.execute_main_action(cast_option)
    assert game.priority_state is not None
    assert game.priority_state.player_index == 0
    assert game.stack[-1].source_id == robots.object_id
    first_window = next(
        event for event in game.events if event.get("event") == "response_window_opened"
    )
    assert first_window["stack_object_id"] == game.stack[-1].object_id
    assert first_window["priority_epoch"] == game.priority_state.epoch
    assert_composed_resolution(game, punks, robots, lands, pizza_card, production)


def test_trigger_free_main_cast_still_resolves_with_legacy_compatibility():
    game = Game(([MOUNTAIN] * 20, [MOUNTAIN] * 20), seed=40138602)
    game.begin_turn()
    game.create_permanent(MOUNTAIN, 0, summoning_sick=False)
    card = game.set_hand_for_testing(
        0, [CardFact("Legacy Synthetic Creature", "{R}", 1, "Creature", "", 1, 1)]
    )[0]
    option = next(
        option
        for option in game.legal_main_actions(0)
        if option.kind is ActionKind.CAST and option.object_id == card.object_id
    )

    assert game.execute_main_action(option)
    assert any(
        item.card.name == "Legacy Synthetic Creature" for item in game.players[0].battlefield
    )
    assert not game.stack and game.priority_state is None


def test_game_cast_direct_caller_keeps_immediate_resolution_contract():
    game = Game(([MOUNTAIN] * 20, [MOUNTAIN] * 20), seed=40138603)
    game.begin_turn()
    game.create_permanent(MOUNTAIN, 0, summoning_sick=False)
    card = game.set_hand_for_testing(
        0, [CardFact("Legacy Direct Creature", "{R}", 1, "Creature", "", 1, 1)]
    )[0]

    assert game.cast(0, card)
    assert any(item.card.name == "Legacy Direct Creature" for item in game.players[0].battlefield)
    assert not game.stack and game.priority_state is None
