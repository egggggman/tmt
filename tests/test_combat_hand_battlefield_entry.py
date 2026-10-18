"""Generic combat-damage hand-to-battlefield trigger semantics."""

from dataclasses import replace
from pathlib import Path

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import (
    CardFact,
    Game,
    RulesEventKind,
    TriggerEffect,
    load_facts,
)

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
CARD = load_facts(
    load_card_data(CATALOG, CATALOG.with_suffix(".manifest.json")),
    {"Michelangelo, Improviser"},
)["Michelangelo, Improviser"]
FRAGMENT = CARD.oracle_text.splitlines()[1]
LAND = CardFact("Plains", "", 0, "Basic Land — Plains")
CREATURE = CardFact("Quiet Bear", "{1}{G}", 2, "Creature — Bear", power=2, toughness=2)


def game(choice=None):
    current = Game(
        ([LAND] * 20, [LAND] * 20),
        seed=733,
        hand_battlefield_entry_chooser=choice,
    )
    current.begin_turn()
    source = current.create_permanent(CARD, 0, summoning_sick=False)
    hand = current.set_hand_for_testing(0, [CREATURE, LAND])
    return current, source, hand


def resolve_trigger(current):
    current._put_pending_triggers_on_stack()
    current._begin_priority_window()
    while current.priority_state is not None:
        if current.priority_state.resolution_pending:
            current.process_priority_resolution()
        else:
            current.execute_priority_action(
                next(
                    action
                    for action in current.legal_priority_actions(
                        current.priority_state.player_index
                    )
                    if action.kind.value == "pass_priority"
                )
            )


def trigger(current, source):
    event = current._new_rules_event(
        RulesEventKind.COMBAT_DAMAGE_TO_PLAYER,
        0,
        (source.object_id,),
        source_id=source.object_id,
        target_player=1,
        amount=2,
        battlefield_authority=current._battlefield_authority_snapshot(),
    )
    current._enqueue_trigger(event, source, FRAGMENT, TriggerEffect.COMBAT_DAMAGE_HAND_BATTLEFIELD)


def test_parser_is_generic_and_complete():
    interpreter = CardInterpreter()
    renamed = replace(CARD, name="Renamed Improviser")
    generic_fragment = FRAGMENT.replace("Michelangelo", "this creature")
    assert interpreter.combat_damage_hand_battlefield(renamed, generic_fragment)
    assert not any(
        reason == "oracle_ability_not_implemented"
        for _fragment, reason in interpreter.unsupported_fragments(
            replace(renamed, oracle_text=generic_fragment)
        )
    )
    assert not interpreter.combat_damage_hand_battlefield(
        renamed, FRAGMENT.replace("to a player", "to a creature")
    )


def test_optional_creature_and_land_selection_enters_both_without_casting():
    selected = {}

    def choose(view, options):
        selected["view"] = view
        return next(option for option in options if option.creature_id and option.land_id)

    current, source, hand = game(choose)
    hand_ids = tuple(item.object_id for item in hand)
    trigger(current, source)
    resolve_trigger(current)
    assert {permanent.card.name for permanent in current.players[0].battlefield} >= {
        CARD.name,
        CREATURE.name,
        LAND.name,
    }
    assert all(item.zone == "former" for item in hand)
    assert tuple(item[0] for item in selected["view"].cards) == hand_ids
    assert any(
        event["event"] == "combat_hand_battlefield_entry_resolved" for event in current.events
    )
    current.check_invariants()


def test_decline_is_legal_and_source_departure_does_not_cancel_trigger():
    current, source, hand = game(lambda _view, options: options[0])
    trigger(current, source)
    current._put_pending_triggers_on_stack()
    current._begin_priority_window()
    current.move_object(source, "graveyard", reason="source_departed")
    while current.priority_state is not None:
        if current.priority_state.resolution_pending:
            current.process_priority_resolution()
        else:
            current.execute_priority_action(
                next(
                    action
                    for action in current.legal_priority_actions(
                        current.priority_state.player_index
                    )
                    if action.kind.value == "pass_priority"
                )
            )
    assert all(item.zone == "hand" for item in hand)
    assert not any(
        event["event"] == "zone_changed" and event.get("reason") == "combat_hand_entry"
        for event in current.events
    )
