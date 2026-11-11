"""Synthetic rule checks for Spicy Oatmeal Pizza's authenticated ETB damage."""

import pytest

from tmnt_design_studio.card_interpreter07 import CardInterpreter, DamageTargetKind
from tmnt_design_studio.conformance07 import semantic_key
from tmnt_design_studio.engine07 import (
    ActionKind,
    ActionOption,
    CardFact,
    Game,
    TriggeredAbilityObject,
    TriggerEffect,
    TurnStep,
)
from tmnt_design_studio.stage002 import (
    DeckSpec,
    GameSpec,
    _authoritative_execution_index,
    reconcile_snapshot,
)

LAND = CardFact("Mountain", "", 0, "Basic Land — Mountain")
PIZZA_FRAGMENT = "When this artifact enters, it deals 4 damage to any target and 3 damage to you."
PIZZA = CardFact(
    "Spicy Oatmeal Pizza",
    "{2}{R}",
    3,
    "Artifact — Food",
    PIZZA_FRAGMENT + "\n{2}, {T}, Sacrifice this artifact: You gain 3 life.",
    oracle_id="9665f940-c0a4-4d3e-b889-8049cf549a4f",
)
BEAR = CardFact("Bear", "{1}{G}", 2, "Creature — Bear", power=2, toughness=2)


def make_game(*, damage_target_chooser=None):
    game = Game(
        ([LAND] * 20, [LAND] * 20),
        seed=9387,
        damage_target_chooser=damage_target_chooser,
    )
    game.begin_turn()
    return game


def resolve_priority(game):
    while game.priority_state is not None and not game.terminal:
        state = game.priority_state
        if state.resolution_pending:
            game.process_priority_resolution()
        else:
            option = next(
                item
                for item in game.legal_priority_actions(state.player_index)
                if item.kind is ActionKind.PASS_PRIORITY
            )
            game.execute_priority_action(option)


def enter_pizza(game):
    source = game.create_permanent(PIZZA, 0, summoning_sick=False)
    game._process_creature_entered_triggers(source)
    return source


def cast_pizza_through_main_action(game):
    for _ in range(3):
        game.create_permanent(LAND, 0, summoning_sick=False)
    pizza_card = game.set_hand_for_testing(0, [PIZZA])[0]
    action = next(
        option
        for option in game.legal_main_actions(0)
        if option.kind is ActionKind.CAST and option.object_id == pizza_card.object_id
    )
    assert game.execute_main_action(action)
    source = next(permanent for permanent in game.players[0].battlefield if permanent.card is PIZZA)
    triggers = [
        item
        for item in game.stack
        if isinstance(item, TriggeredAbilityObject) and item.effect is TriggerEffect.DEAL_DAMAGE
    ]
    assert len(triggers) == 1
    return source, triggers[0]


def pizza_reconciliation(game, source):
    snapshot = game.snapshot()
    key = semantic_key(source.card.oracle_id, 0, 0, PIZZA_FRAGMENT)
    assert any(
        reference["semantic_key"] == key
        and reference["source_id"] == source.object_id
        and reference["oracle_fragment"] == PIZZA_FRAGMENT
        for reference in snapshot["conformance"]["executed_references"]
    )
    snapshot["stage002_presence"] = [
        {
            "semantic_key": key,
            "oracle_fragment": PIZZA_FRAGMENT,
            "origin": "deck_card",
            "object_ids": [source.object_id],
            "is_token": False,
        }
    ]
    return reconcile_snapshot(
        GameSpec(
            "synthetic-pizza-terminal" if game.terminal else "synthetic-pizza-cast",
            "synthetic",
            9387,
            "canonical",
            (DeckSpec("A", ""), DeckSpec("B", "")),
        ),
        snapshot,
        {
            "decks": [
                {
                    "cards": [
                        {"fragments": [{"semantic_key": key, "oracle_fragment": PIZZA_FRAGMENT}]}
                    ]
                }
            ]
        },
    )


def test_pizza_etb_target_damage_then_controller_damage_has_authenticated_priority():
    game = make_game(
        damage_target_chooser=lambda _player, _source, offered: next(
            item for item in offered if not item.startswith("player:")
        )
    )
    target = game.create_permanent(BEAR, 1, summoning_sick=False)
    source = enter_pizza(game)

    trigger = next(item for item in game.stack if item.effect is TriggerEffect.DEAL_DAMAGE)
    assert trigger.source_id == source.object_id
    assert trigger.event.kind.value == "permanent_entered"
    assert trigger.oracle_fragment == PIZZA_FRAGMENT
    assert trigger.target_id == target.object_id
    assert game.snapshot()["stack"][-1]["target_id"] == target.object_id
    assert game.priority_state is not None
    assert game.players[1].life == 20 and target.damage == 0

    priority_players = []
    while game.priority_state is not None and game.winner is None:
        state = game.priority_state
        priority_players.append(state.player_index)
        if state.resolution_pending:
            game.process_priority_resolution()
        else:
            option = next(
                item
                for item in game.legal_priority_actions(state.player_index)
                if item.kind is ActionKind.PASS_PRIORITY
            )
            game.execute_priority_action(option)

    assert target.damage == 4
    assert game.players[0].life == 17
    damage = [event for event in game.events if event["event"] == "damage_dealt"]
    assert [(event["source_id"], event["target_id"], event["amount"]) for event in damage] == [
        (source.object_id, target.object_id, 4),
        (source.object_id, None, 3),
    ]
    assert len([event for event in game.events if event.get("event") == "trigger_resolved"]) == 1
    assert not game.stack
    assert set(priority_players) == {0, 1}
    snapshot = game.snapshot()
    execution = _authoritative_execution_index(snapshot)
    assert len(damage) == 2
    for event in damage:
        assert execution[("damage_dealt", event["event_id"])] == [
            {"source_id": source.object_id, "oracle_fragment": PIZZA_FRAGMENT}
        ]
    assert snapshot["conformance"]["stop_records"] == []
    executed_reference = next(
        item
        for item in snapshot["conformance"]["executed_references"]
        if item["source_id"] == source.object_id and item["oracle_fragment"] == PIZZA_FRAGMENT
    )
    key = semantic_key(source.card.oracle_id, 0, 0, PIZZA_FRAGMENT)
    assert executed_reference["semantic_key"] == key
    snapshot["stage002_presence"] = [
        {
            "semantic_key": key,
            "oracle_fragment": PIZZA_FRAGMENT,
            "origin": "deck_card",
            "object_ids": [source.object_id],
            "is_token": False,
        }
    ]
    report = reconcile_snapshot(
        GameSpec(
            "synthetic-pizza",
            "synthetic",
            9387,
            "canonical",
            (DeckSpec("A", ""), DeckSpec("B", "")),
        ),
        snapshot,
        {
            "decks": [
                {
                    "cards": [
                        {"fragments": [{"semantic_key": key, "oracle_fragment": PIZZA_FRAGMENT}]}
                    ]
                }
            ]
        },
    )
    assert report["stop_records"] == []
    assert report["presence"][0]["classification"] == "executed"
    assert len(report["authenticated_executed_references"]) >= 2


def test_pizza_trigger_resolves_after_source_leaves_and_simultaneous_lethal_effects():
    game = make_game()
    game.players[0].life = 3
    game.players[1].life = 4
    source, trigger = cast_pizza_through_main_action(game)
    assert trigger.source_id == source.object_id
    game.put_into_graveyard(source)

    resolve_priority(game)

    assert game.players[1].life == 0
    assert game.players[0].life == 0
    assert game.winner is None
    assert game.terminal
    assert all(player.lost for player in game.players)
    assert game.priority_state is None
    damage = [event for event in game.events if event["event"] == "damage_dealt"]
    assert [event["amount"] for event in damage] == [4, 3]
    assert all(event["source_id"] == source.object_id for event in damage)
    snapshot = game.snapshot()
    assert snapshot["terminal"] is True and snapshot["winner"] is None
    assert not any(event["event"] == "acceptance_incomplete" for event in game.events)
    report = pizza_reconciliation(game, source)
    assert report["terminal"] is True and report["winner"] is None
    assert report["stop_records"] == []
    before = game.authoritative_state_fingerprint()
    with pytest.raises(ValueError, match="terminal game"):
        game.advance_step()
    with pytest.raises(ValueError, match="terminal game"):
        game.advance_to(TurnStep.CLEANUP)
    assert game.authoritative_state_fingerprint() == before
    assert game.legal_main_actions(0) == ()
    assert game.legal_priority_actions(0) == ()
    assert game.legal_attack_options(0) == ()
    assert game.legal_block_options(ActionOption(ActionKind.DECLARE_ATTACKERS, 0), 1) == ()
    assert game.legal_sneak_actions(0) == ()
    with pytest.raises(ValueError, match="terminal game"):
        game._begin_priority_window(allow_empty=True)


def test_ordinary_life_loss_remains_a_terminal_win():
    game = make_game()
    game.players[1].life = 0
    game._begin_priority_window(allow_empty=True)

    game.check_life()

    assert game.players[1].lost
    assert not game.players[0].lost
    assert game.winner == 0
    assert game.terminal
    assert game.priority_state is None
    snapshot = game.snapshot()
    assert snapshot["terminal"] is True
    assert snapshot["winner"] == game.players[0].name


@pytest.mark.parametrize("target_kind", ("self", "opponent", "creature"))
def test_normal_pizza_cast_auto_stacks_and_resolves_one_authenticated_trigger(target_kind):
    target = None
    selected = {"value": None}

    def choose_target(_controller, _source_id, offered):
        assert selected["value"] in offered
        return selected["value"]

    game = make_game(damage_target_chooser=choose_target)
    if target_kind == "creature":
        target = game.create_permanent(BEAR, 1, summoning_sick=False)
        selected["value"] = target.object_id
    else:
        selected["value"] = f"player:{0 if target_kind == 'self' else 1}"

    source, trigger = cast_pizza_through_main_action(game)

    assert trigger.source_id == source.object_id
    assert trigger.source_card is source.card is PIZZA
    assert trigger.oracle_fragment == PIZZA_FRAGMENT
    assert trigger.event.subject_ids == (source.object_id,)
    assert trigger.event.kind.value == "permanent_entered"
    assert game._rules_events[trigger.event.event_id] is trigger.event
    assert (
        sum(
            event.get("event") == "trigger_stacked"
            and event.get("source") == source.card.name
            and event.get("stack_object_id") == trigger.object_id
            and event.get("trigger_id") == trigger.trigger_id
            for event in game.events
        )
        == 1
    )
    assert game.priority_state is not None
    priority_epoch = game.priority_state.epoch
    assert game.players[0].life == 20 and game.players[1].life == 20
    assert target is None or target.damage == 0

    passed_by = []
    while game.priority_state is not None:
        state = game.priority_state
        assert not state.resolution_pending
        assert game.stack[-1] is trigger
        passed_by.append((state.player_index, state.epoch))
        option = next(
            option
            for option in game.legal_priority_actions(state.player_index)
            if option.kind is ActionKind.PASS_PRIORITY
        )
        game.execute_priority_action(option)
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()

    assert passed_by == [(0, priority_epoch), (1, priority_epoch)]
    damage = [event for event in game.events if event["event"] == "damage_dealt"]
    assert len(damage) == 2
    assert [event["amount"] for event in damage] == [4, 3]
    assert all(event["source_id"] == source.object_id for event in damage)
    if target_kind == "creature":
        assert target is not None and target.zone == "former"
        assert damage[0]["target_id"] == target.object_id
        lethal_move = next(
            index
            for index, event in enumerate(game.events)
            if event.get("event") == "zone_changed"
            and event.get("source_object_id") == target.object_id
            and event.get("reason") == "lethal_damage"
        )
        damage_positions = [game.events.index(event) for event in damage]
        assert damage_positions[0] < damage_positions[1] < lethal_move
    else:
        expected_target_player = 0 if target_kind == "self" else 1
        assert damage[0]["target_player"] == game.players[expected_target_player].name
        assert damage[1]["target_player"] == game.players[0].name
        assert game.players[0].life == (13 if target_kind == "self" else 17)
        assert game.players[1].life == (20 if target_kind == "self" else 16)

    snapshot = game.snapshot()
    execution = _authoritative_execution_index(snapshot)
    for event in damage:
        assert execution[("damage_dealt", event["event_id"])] == [
            {"source_id": source.object_id, "oracle_fragment": PIZZA_FRAGMENT}
        ]
    report = pizza_reconciliation(game, source)
    assert report["terminal"] is False
    assert report["stop_records"] == []
    assert report["presence"][0]["classification"] == "executed"
    assert len(report["authenticated_executed_references"]) >= 2


def test_pizza_trigger_with_illegal_target_does_not_deal_either_damage():
    selected = {}

    def choose_target(_player, _source_id, offered):
        selected["target"] = next(item for item in offered if not item.startswith("player:"))
        return selected["target"]

    game = make_game(damage_target_chooser=choose_target)
    target = game.create_permanent(BEAR, 1, summoning_sick=False)
    selected_id = target.object_id
    source, trigger = cast_pizza_through_main_action(game)
    assert selected["target"] == selected_id
    assert trigger.source_id == source.object_id
    game.put_into_graveyard(target)

    resolve_priority(game)

    assert game.players[0].life == 20
    assert not any(event["event"] == "damage_dealt" for event in game.events)
    skipped = [event for event in game.events if event.get("reason") == "all_targets_illegal"]
    assert skipped and skipped[-1]["source_id"] == source.object_id


def test_pizza_damage_semantics_are_card_name_independent_and_fully_supported():
    renamed = CardFact(
        "Renamed Artifact",
        "{2}{R}",
        3,
        "Artifact — Food",
        PIZZA_FRAGMENT,
    )
    coverage = CardInterpreter().damage_semantic_coverage(renamed, renamed.oracle_text)
    assert coverage is not None and coverage.coverage.fully_supported
    assert coverage.program.target_kind is DamageTargetKind.ANY
    assert coverage.program.followup_amount == 3
