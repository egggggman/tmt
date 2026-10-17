"""Controlled countered-artifact departure transfers its frozen counters."""

import copy
from pathlib import Path

import pytest

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import ActionKind, CardFact, Game, TriggerEffect, load_facts

FRAGMENT = (
    "Whenever an artifact you control is put into a graveyard from the battlefield, "
    "if it had counters on it, put those counters on up to one target artifact or creature "
    "you control."
)
SOURCE = CardFact("Anonymous Watcher", "{3}{U}", 4, "Creature — Artificer", FRAGMENT, 2, 2)
ARTIFACT = CardFact("Countered Relic", "{2}", 2, "Artifact Creature — Robot", "", 2, 2)
TARGET = CardFact("Receiving Relic", "{2}", 2, "Artifact", "")
LAND = CardFact("Island", "", 0, "Basic Land — Island")


def setup(*, chooser=None):
    game = Game(([LAND] * 60, [LAND] * 60), seed=933, counter_target_chooser=chooser)
    game.begin_turn()
    watcher = game.create_permanent(SOURCE, 0)
    departed = game.create_permanent(ARTIFACT, 0)
    target = game.create_permanent(TARGET, 0)
    departed.counters.update({"+1/+1": 2, "charge": 3})
    return game, watcher, departed, target


def resolve(game):
    while game.priority_state is not None:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            options = game.legal_priority_actions(game.priority_state.player_index)
            game.execute_priority_action(
                next(o for o in options if o.kind is ActionKind.PASS_PRIORITY)
            )


def test_complete_generic_parser_and_frozen_clause():
    interpreter = CardInterpreter()
    assert interpreter.controlled_artifact_counter_transfer(SOURCE, FRAGMENT)
    assert (FRAGMENT, "oracle_ability_not_implemented") not in interpreter.unsupported_fragments(
        SOURCE
    )
    assert not interpreter.controlled_artifact_counter_transfer(
        CardFact("Spell", "{2}", 2, "Instant", FRAGMENT), FRAGMENT
    )
    assert not interpreter.controlled_artifact_counter_transfer(
        CardFact("Partial", "{2}", 2, "Artifact", FRAGMENT + " Draw a card."),
        FRAGMENT + " Draw a card.",
    )


def test_snapshot_optional_target_priority_source_departure_and_replay():
    def run():
        game, watcher, departed, target = setup(
            chooser=lambda _controller, _source, offered: next(
                item for item in offered if item == target.object_id
            )
        )
        game.move_object(departed, "graveyard", reason="sacrifice")
        game.check_state_based_actions()
        assert game.stack[-1].effect is TriggerEffect.CONTROLLED_ARTIFACT_COUNTER_TRANSFER
        assert game.stack[-1].target_id == target.object_id
        game.move_object(watcher, "graveyard", reason="response")
        assert target.counters == {}
        resolve(game)
        assert target.counters == {"+1/+1": 2, "charge": 3}
        records = [e for e in game.events if e["event"] == "artifact_counter_transfer_resolved"]
        assert len(records) == 1 and records[0]["counter_snapshot"] == [["+1/+1", 2], ["charge", 3]]
        game.check_invariants()
        return game.events

    # Closure target is assigned after setup; explicitly exercise the same sequence twice.
    assert run() == copy.deepcopy(run())


@pytest.mark.parametrize("response", ["removed", "control", "type", "declined"])
def test_optional_or_illegal_target_resolves_without_moving_counters(response):
    def choose(_controller, _source, offered):
        return None if response == "declined" else target.object_id

    game, _watcher, departed, target = setup(chooser=choose)
    game.move_object(departed, "graveyard")
    game.check_state_based_actions()
    if response == "removed":
        game.move_object(target, "graveyard")
    elif response == "control":
        game.change_controller(target, 1)
    elif response == "type":
        target.type_line_override = "Land"
    resolve(game)
    assert target.counters == {}
    assert [e for e in game.events if e["event"] == "artifact_counter_transfer_resolved"][-1][
        "target_legal"
    ] is False
    game.check_invariants()


def test_chooser_cannot_select_a_protected_artifact():
    game, _watcher, departed, _target = setup(
        chooser=lambda _controller, _source, _offered: protected.object_id
    )
    protected = game.create_permanent(CardFact("Hidden Relic", "{2}", 2, "Artifact", "Shroud"), 0)
    game.move_object(departed, "graveyard")
    with pytest.raises(ValueError, match="illegal target"):
        game.check_state_based_actions()


def test_no_trigger_without_counters_graveyard_or_controlled_artifact():
    for change in ("no_counters", "exile", "enemy", "nonartifact"):
        game, _watcher, departed, _target = setup()
        if change == "no_counters":
            departed.counters.clear()
        elif change == "enemy":
            game.change_controller(departed, 1)
        elif change == "nonartifact":
            departed.type_line_override = "Creature — Robot"
        game.move_object(departed, "exile" if change == "exile" else "graveyard")
        game.check_state_based_actions()
        assert not any(
            e["event"] == "trigger_pending" and e["oracle_fragment"] == FRAGMENT
            for e in game.events
        )
        game.check_invariants()


def test_self_departure_and_suppression_use_pre_exit_ability_state():
    artifact_watcher = CardFact("Artifact Watcher", "{2}", 2, "Artifact", FRAGMENT)
    for suppressed in (False, True):
        game = Game(([LAND] * 60, [LAND] * 60), seed=934)
        game.begin_turn()
        watcher = game.create_permanent(artifact_watcher, 0)
        receiver = game.create_permanent(TARGET, 0)
        watcher.counters["charge"] = 2
        if suppressed:
            watcher.ability_loss_timestamp = (game.turn, 1)
        game.move_object(watcher, "graveyard")
        game.check_state_based_actions()
        if suppressed:
            assert not game.stack
            assert receiver.counters == {}
        else:
            resolve(game)
            assert receiver.counters == {"charge": 2}
        game.check_invariants()


def test_frozen_departure_counter_provenance_rejects_tampering():
    game, _watcher, departed, _target = setup()
    game.move_object(departed, "graveyard")
    game.check_state_based_actions()
    departed.counters["charge"] = 7
    with pytest.raises(AssertionError, match="invalid event provenance"):
        game.check_invariants()


def test_frozen_oracle_card_executes_through_same_generic_trigger():
    catalog = Path(__file__).resolve().parents[1] / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
    card = load_facts(
        load_card_data(catalog, catalog.with_suffix(".manifest.json")),
        {"Donatello, Mutant Mechanic"},
    )["Donatello, Mutant Mechanic"]
    assert FRAGMENT in CardInterpreter().fragments(card)
    game = Game(([LAND] * 60, [LAND] * 60), seed=935)
    game.begin_turn()
    watcher = game.create_permanent(card, 0)
    artifact = game.create_permanent(ARTIFACT, 0)
    artifact.counters["+1/+1"] = 3
    game.move_object(artifact, "graveyard")
    game.check_state_based_actions()
    assert game.stack[-1].source_id == watcher.object_id
    resolve(game)
    assert watcher.counters["+1/+1"] == 3
    game.check_invariants()
