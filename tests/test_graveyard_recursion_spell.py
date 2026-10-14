"""Complete one-or-two targeted graveyard recursion with normal and Sneak costs."""

from dataclasses import replace
from pathlib import Path

import pytest

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter, CastKind
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
CARD = load_facts(
    load_card_data(CATALOG, CATALOG.with_suffix(".manifest.json")),
    {"Leonardo's Technique"},
)["Leonardo's Technique"]
PLAINS = CardFact("Plains", "", 0, "Basic Land — Plains")
ONE = CardFact("Quiet Scout", "{W}", 1, "Creature — Scout", power=1, toughness=1)
THREE = CardFact("Quiet Mentor", "{2}{W}", 3, "Creature — Mentor", power=2, toughness=2)
FOUR = CardFact("Large Mentor", "{3}{W}", 4, "Creature — Mentor", power=4, toughness=4)
ARTIFACT = CardFact("Quiet Relic", "{1}", 1, "Artifact")
ZERO = CardFact("Frail Scout", "{W}", 1, "Creature — Scout", power=0, toughness=0)


def game(*, lands=4, seed=321):
    current = Game(([PLAINS] * 40, [PLAINS] * 40), seed=seed)
    current.begin_turn()
    for _ in range(lands):
        current.create_permanent(PLAINS, 0)
    spell = current.set_hand_for_testing(0, [CARD])[0]
    return current, spell


def grave(current, card, owner=0):
    obj = current._create_card_object(card, owner, "graveyard")
    current.players[owner].graveyard.append(obj)
    return obj


def drain(current):
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


def test_complete_parser_and_sneak_fail_closed_without_names():
    interpreter = CardInterpreter()
    for card in (CARD, replace(CARD, name="Anonymous Recursion")):
        program = interpreter.graveyard_recursion_program(card)
        assert program is not None and program.mana_value_limit == 3
        assert interpreter.cast_program(card).kind is CastKind.GRAVEYARD_RECURSION
        assert interpreter.sneak_semantic_coverage(
            card, program.sneak_fragment
        ).coverage.fully_supported
        assert interpreter.unsupported_fragments(card) == ()
    for text in (
        CARD.oracle_text + "\nDraw a card.",
        CARD.oracle_text.replace("one or two", "up to two"),
        CARD.oracle_text.replace("your graveyard", "a graveyard"),
        CARD.oracle_text.replace("return an unblocked attacker", "sacrifice an attacker"),
    ):
        card = replace(CARD, oracle_text=text)
        assert interpreter.graveyard_recursion_program(card) is None
        assert interpreter.cast_program(card).kind is CastKind.UNSUPPORTED


def test_legal_one_and_two_targets_payment_zone_id_and_stack():
    current, spell = game()
    one, three = grave(current, ONE), grave(current, THREE)
    grave(current, FOUR)
    grave(current, ARTIFACT)
    grave(current, ONE, owner=1)
    options = [a for a in current.legal_main_actions(0) if a.object_id == spell.object_id]
    assert {a.choice_ids for a in options} == {
        (one.object_id,),
        (three.object_id,),
        (one.object_id, three.object_id),
    }
    assert current.execute_main_action(options[-1])
    stacked = current.stack[-1]
    assert stacked.target_ids == (one.object_id, three.object_id)
    paid = next(e for e in current.events if e["event"] == "cost_paid")
    assert paid["generic"] == 3 and paid["colored"] == ["W"]
    drain(current)
    event = next(e for e in current.events if e["event"] == "graveyard_recursion_resolved")
    assert event["stack_object_id"] == stacked.object_id
    assert [item["graveyard_id"] for item in event["entered"]] == list(stacked.target_ids)
    assert all(
        current._objects[item["battlefield_id"]].zone == "battlefield" for item in event["entered"]
    )
    assert one.zone == three.zone == "former"
    current.check_invariants()


def test_announcement_rejects_zero_duplicate_foreign_expensive_or_noncreature_targets():
    current, spell = game()
    one = grave(current, ONE)
    foreign = grave(current, ONE, owner=1)
    four = grave(current, FOUR)
    artifact = grave(current, ARTIFACT)
    for targets in ((), (one, one), (foreign,), (four,), (artifact,), (one, foreign)):
        assert current.announce_spell(0, spell, recursion_targets=targets) is None
    assert (
        current.announce_spell(
            0, spell, target=current.create_permanent(ONE, 1), recursion_targets=(one,)
        )
        is None
    )
    assert spell.zone == "hand" and not any(e["event"] == "cost_paid" for e in current.events)
    current.check_invariants()


def test_partial_invalid_target_still_returns_legal_one_and_all_illegal_fizzles():
    current, spell = game()
    one, three = grave(current, ONE), grave(current, THREE)
    stacked = current.announce_spell(0, spell, recursion_targets=(one, three))
    assert stacked is not None
    current.move_object(one, "exile", reason="opponent_response")
    current.resolve_top_of_stack()
    event = next(e for e in current.events if e["event"] == "graveyard_recursion_resolved")
    assert event["invalid_target_ids"] == [one.object_id]
    assert [entry["graveyard_id"] for entry in event["entered"]] == [three.object_id]
    current.check_invariants()

    other, spell = game(seed=322)
    target = grave(other, ONE)
    other.announce_spell(0, spell, recursion_targets=(target,))
    other.move_object(target, "exile", reason="opponent_response")
    other.resolve_top_of_stack()
    assert any(
        e["event"] == "spell_resolved_no_effect" and e["target_source_ids"] == [target.object_id]
        for e in other.events
    )
    assert not any(e["event"] == "graveyard_recursion_resolved" for e in other.events)
    other.check_invariants()


def test_sneak_timing_target_choice_priority_source_independence_and_replay():
    def run():
        current, spell = game(lands=2, seed=323)
        target = grave(current, THREE)
        attacker = current.create_permanent(ONE, 0, summoning_sick=False)
        current.advance_to(TurnStep.DECLARE_ATTACKERS)
        current.execute_attack_action(
            ActionOption(ActionKind.DECLARE_ATTACKERS, 0, attacker_ids=(attacker.object_id,))
        )
        current.execute_block_action(ActionOption(ActionKind.DECLARE_BLOCKERS, 1))
        action = next(a for a in current.legal_sneak_actions(0) if a.object_id == spell.object_id)
        assert action.choice_ids == (target.object_id,)
        current.execute_sneak_action(action)
        stacked = current.stack[-1]
        assert attacker.zone == "former" and stacked.target_ids == (target.object_id,)
        with pytest.raises(ValueError, match="before all players pass"):
            current.resolve_top_of_stack()
        drain(current)
        assert any(e["event"] == "sneak_cost_paid" for e in current.events)
        assert any(
            e["event"] == "graveyard_recursion_resolved"
            and e["stack_object_id"] == stacked.object_id
            for e in current.events
        )
        current.check_invariants()
        return current.snapshot()

    assert run() == run()


def test_state_based_actions_and_countered_spell():
    current, spell = game()
    target = grave(current, ZERO)
    current.announce_spell(0, spell, recursion_targets=(target,))
    current.resolve_top_of_stack()
    event = next(e for e in current.events if e["event"] == "graveyard_recursion_resolved")
    returned = current._objects[event["entered"][0]["battlefield_id"]]
    assert returned.zone == "former"
    assert any(
        e["event"] == "zone_changed"
        and e["source_object_id"] == returned.object_id
        and e["destination_zone"] == "graveyard"
        for e in current.events
    )
    current.check_invariants()

    other, spell = game(seed=324)
    target = grave(other, ONE)
    stacked = other.announce_spell(0, spell, recursion_targets=(target,))
    other.move_object(stacked, "graveyard", reason="countered")
    assert target.zone == "graveyard"
    assert not any(e["event"] == "graveyard_recursion_resolved" for e in other.events)
    other.check_invariants()
