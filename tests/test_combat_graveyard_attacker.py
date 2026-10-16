"""A self combat-damage trigger returns an opponent's creature tapped and attacking."""

from dataclasses import replace
from pathlib import Path

import pytest

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import (
    ActionKind,
    ActionOption,
    CardFact,
    Game,
    TurnStep,
    load_facts,
)

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
SHARK = load_facts(
    load_card_data(CATALOG, CATALOG.with_suffix(".manifest.json")), {"Shark Shredder, Killer Clone"}
)["Shark Shredder, Killer Clone"]
LAND = CardFact("Forest", "", 0, "Basic Land — Forest")
BEAR = CardFact("Risen Bear", "{1}{G}", 2, "Creature — Bear", power=2, toughness=2)
FIRST = CardFact(
    "Risen First", "{W}", 1, "Creature — Soldier", "First strike", 2, 2, ("First strike",)
)
DOUBLE = CardFact(
    "Risen Double", "{W}", 1, "Creature — Soldier", "Double strike", 2, 2, ("Double strike",)
)


def game(seed=40, source=SHARK, *, blocker=None, grave_card=BEAR):
    current = Game(([LAND] * 40, [LAND] * 40), seed=seed)
    current.begin_turn()
    attacker = current.create_permanent(source, 0, summoning_sick=False)
    target = None
    if grave_card is not None:
        target = current._create_card_object(grave_card, 1, "graveyard")
        current.players[1].graveyard.append(target)
    current.advance_to(TurnStep.DECLARE_ATTACKERS)
    attack = next(
        option
        for option in current.legal_attack_options(0)
        if option.attacker_ids == (attacker.object_id,)
    )
    current.execute_attack_action(attack)
    blocked = current.create_permanent(blocker, 1) if blocker else None
    current.execute_block_action(
        ActionOption(
            ActionKind.DECLARE_BLOCKERS,
            1,
            blocks=((attacker.object_id, blocked.object_id),) if blocked else (),
        )
    )
    return current, attacker, target


def drain(current):
    while current.priority_state is not None:
        if current.priority_state.resolution_pending:
            current.process_priority_resolution()
        else:
            options = current.legal_priority_actions(current.priority_state.player_index)
            current.execute_priority_action(
                next(option for option in options if option.kind is ActionKind.PASS_PRIORITY)
            )


def test_parser_requires_complete_clause_and_accepts_renamed_fixture():
    interpreter = CardInterpreter()
    fragment = interpreter.fragments(SHARK)[-1]
    assert interpreter.combat_damage_graveyard_attacker(SHARK, fragment)
    renamed = replace(
        SHARK,
        name="Undersea Raider",
        oracle_text=SHARK.oracle_text.replace("Shark Shredder", "Undersea Raider"),
    )
    assert interpreter.combat_damage_graveyard_attacker(renamed, interpreter.fragments(renamed)[-1])
    assert not interpreter.combat_damage_graveyard_attacker(
        SHARK, fragment.replace("tapped and attacking", "tapped")
    )


@pytest.mark.parametrize("grave_card", [BEAR, FIRST, DOUBLE])
def test_first_strike_damage_returns_attacker_and_late_entrant_deals_regular_damage(grave_card):
    current, attacker, target = game(grave_card=grave_card)
    first = current.resolve_combat_damage()
    assert len(first.assignments) == 1
    assert current.stack[-1].target_id == target.object_id
    assert current.step is TurnStep.COMBAT_DAMAGE
    assert current.priority_state is not None
    drain(current)
    entry = next(e for e in current.events if e["event"] == "combat_graveyard_attacker_resolved")
    returned = current._objects[entry["permanent_id"]]
    assert returned.owner == 1 and returned.controller == 0 and returned.tapped
    assert returned.object_id in current._combat_attackers
    assert target.zone == "former"
    regular = current.resolve_combat_damage()
    assert [assignment.source_id for assignment in regular.assignments] == [returned.object_id]
    assert current.players[1].life == 20 - attacker.power - returned.power
    current.check_invariants()


def test_blocked_damage_to_creature_does_not_trigger():
    current, _, target = game(blocker=BEAR)
    current.resolve_combat_damage()
    assert not any(e["event"] == "combat_graveyard_target_selected" for e in current.events)
    assert current.is_authoritative(target, "graveyard")
    current.check_invariants()


def test_target_fixed_at_stack_placement_and_illegal_target_fizzles():
    current, _, target = game()
    current.resolve_combat_damage()
    assert current.stack[-1].target_id == target.object_id
    moved = current.move_object(target, "hand", reason="priority_response")
    drain(current)
    resolved = [e for e in current.events if e["event"] == "combat_graveyard_attacker_resolved"]
    assert resolved[0]["legal_target"] is False
    assert current.is_authoritative(moved, "hand")
    current.check_invariants()


def test_source_departure_and_empty_graveyard_preserve_optional_trigger():
    for grave_card in (BEAR, None):
        current, source, _ = game(grave_card=grave_card)
        current.resolve_combat_damage()
        assert current.priority_state is not None
        current.put_into_graveyard(source, state_based_action="priority_response")
        drain(current)
        resolved = [e for e in current.events if e["event"] == "combat_graveyard_attacker_resolved"]
        assert len(resolved) == 1
        assert resolved[0]["legal_target"] is (grave_card is not None)
        current.check_invariants()


def test_returned_zero_toughness_creature_dies_to_state_based_actions():
    frail = CardFact("Frail", "{W}", 1, "Creature", power=0, toughness=0)
    current, _, _ = game(grave_card=frail)
    current.resolve_combat_damage()
    drain(current)
    entry = next(e for e in current.events if e["event"] == "combat_graveyard_attacker_resolved")
    assert not current.is_authoritative(current._objects[entry["permanent_id"]], "battlefield")
    current.check_invariants()


def test_regular_step_returned_attacker_cannot_deal_damage_this_combat():
    regular_source = replace(
        SHARK,
        oracle_text=SHARK.oracle_text.replace("First strike\n", ""),
        keywords=(),
    )
    current, _, _ = game(source=regular_source)
    current.resolve_combat_damage()
    drain(current)
    assert current.step is TurnStep.END_OF_COMBAT
    assert current.players[1].life == 20 - SHARK.power
    current.check_invariants()


def test_stack_target_tamper_fails_provenance_before_resolution():
    current, _, _ = game()
    another = current._create_card_object(FIRST, 1, "graveyard")
    current.players[1].graveyard.append(another)
    current.resolve_combat_damage()
    current.stack[-1].target_id = another.object_id
    with pytest.raises(AssertionError, match="selection provenance"):
        current.check_invariants()


def test_replay_deterministic():
    def trace():
        current, _, _ = game(seed=777)
        current.resolve_combat_damage()
        drain(current)
        current.resolve_combat_damage()
        current.check_invariants()
        return current.events

    assert trace() == trace()
