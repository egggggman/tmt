import hashlib
import inspect
import json
from dataclasses import replace
from pathlib import Path

import pytest

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import (
    ActionKind,
    ActionOption,
    CardFact,
    CardObject,
    Game,
    Permanent,
    TurnStep,
)

ROOT = Path(__file__).resolve().parents[1]
PLAINS = CardFact("Plains", "", 0, "Basic Land — Plains")
BEAR = CardFact("Bear", "{1}{W}", 2, "Creature — Bear", power=2, toughness=2)
SNEAK_FRAGMENT = (
    "Sneak {W} (You may cast this spell for {W} if you also return an unblocked attacker "
    "you control to hand during the declare blockers step. It enters tapped and attacking.)"
)
SNEAK_CREATURE = CardFact(
    "Anonymous Sneak",
    "{3}{W}",
    4,
    "Creature — Ninja",
    SNEAK_FRAGMENT,
    power=4,
    toughness=4,
    keywords=("Sneak",),
)


def catalog():
    return load_card_data(
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json",
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json",
    )


def coverage_sets():
    interpreter = CardInterpreter()
    recognized, executable, full = [], [], []
    seen = set()
    for card in sorted(catalog().cards, key=lambda value: (value.name, value.oracle_id)):
        if card.oracle_id in seen:
            continue
        seen.add(card.oracle_id)
        for fragment in interpreter.fragments(card):
            semantics = interpreter.sneak_semantic_coverage(card, fragment)
            if semantics is None:
                continue
            member = (card.oracle_id, card.name, fragment)
            recognized.append(member)
            if semantics.coverage.payload_executable:
                executable.append(member)
            if semantics.coverage.fully_supported:
                full.append(member)
    return recognized, executable, full


def digest(members):
    encoded = json.dumps(members, ensure_ascii=False, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def setup_sneak(*, card=SNEAK_CREATURE, attacker_owner=0, mana=1):
    current = Game(([PLAINS] * 20, [PLAINS] * 20), seed=311)
    current.begin_turn()
    current.set_hand_for_testing(0, [card])
    for _ in range(mana):
        current.create_permanent(PLAINS, 0, summoning_sick=False)
    attacker = current.create_permanent(BEAR, attacker_owner, controller=0, summoning_sick=False)
    current.advance_to(TurnStep.DECLARE_ATTACKERS)
    attack = ActionOption(ActionKind.DECLARE_ATTACKERS, 0, attacker_ids=(attacker.object_id,))
    current.execute_attack_action(attack)
    blocks = ActionOption(ActionKind.DECLARE_BLOCKERS, 1)
    current.execute_block_action(blocks)
    if mana:
        assert current.step is TurnStep.DECLARE_BLOCKERS
    return current, attacker


def resolve_priority(current):
    while current.priority_state is not None:
        if current.priority_state.resolution_pending:
            current.process_priority_resolution()
        else:
            current.execute_priority_action(
                current.legal_priority_actions(current.priority_state.player_index)[0]
            )


def cast_option(current):
    return next(
        option for option in current.legal_sneak_actions(0) if option.kind is ActionKind.CAST
    )


def test_sneak_is_oracle_derived_and_card_name_independent():
    interpreter = CardInterpreter()
    first = interpreter.sneak_semantic_coverage(SNEAK_CREATURE, SNEAK_FRAGMENT)
    renamed = replace(SNEAK_CREATURE, name="Entirely Different Name")
    second = interpreter.sneak_semantic_coverage(renamed, SNEAK_FRAGMENT)

    assert first == second
    assert first is not None and first.coverage.fully_supported
    source = inspect.getsource(CardInterpreter.sneak_semantic_coverage)
    assert "Leonardo" not in source and "Raphael" not in source


def test_bounded_sneak_announcement_stack_priority_and_resolution():
    current, attacker = setup_sneak()
    original_hand_id = current.players[0].hand[0].object_id
    option = cast_option(current)

    current.execute_sneak_action(option)

    assert attacker.zone == "former"
    assert current.players[0].hand[0].object_id != attacker.object_id
    assert current.stack[-1].object_id == current.sneak_evidence[-1].stack_object_id
    assert current.priority_state is not None
    with pytest.raises(ValueError, match="before all players pass"):
        current.resolve_top_of_stack()

    resolve_priority(current)
    evidence = current.sneak_evidence[-1]
    permanent = current._objects[evidence.resolved_object_id]
    assert isinstance(permanent, Permanent)
    assert permanent.tapped and permanent.summoning_sick
    assert permanent.object_id in current._combat_attackers
    assert evidence.hand_object_id == original_hand_id
    assert evidence.entered_tapped and evidence.entered_attacking
    current.check_invariants()


def test_return_cost_uses_owner_hand_not_controller_hand():
    current, attacker = setup_sneak(attacker_owner=1)
    current.execute_sneak_action(cast_option(current))
    evidence = current.sneak_evidence[-1]

    assert any(card.object_id == evidence.returned_hand_id for card in current.players[1].hand)
    assert all(card.object_id != evidence.returned_hand_id for card in current.players[0].hand)
    assert attacker.zone == "former"


def test_token_attacker_pays_return_cost_then_ceases_at_sba_boundary():
    current, attacker = setup_sneak()
    attacker.is_token = True
    current.execute_sneak_action(cast_option(current))
    evidence = current.sneak_evidence[-1]
    returned = current._objects[evidence.returned_hand_id]

    assert returned.zone == "former"
    assert all(card.object_id != returned.object_id for card in current.players[0].hand)
    assert any(
        event["event"] == "token_ceased" and event["object_id"] == returned.object_id
        for event in current.events
    )


def test_sneak_paid_etb_condition_uses_its_own_stack_priority_boundary():
    fragment = (
        "When Anonymous Leader enters, if its sneak cost was paid, creatures you control get "
        "+2/+0 until end of turn."
    )
    leader = replace(
        SNEAK_CREATURE, name="Anonymous Leader", oracle_text=SNEAK_FRAGMENT + "\n" + fragment
    )
    current, _attacker = setup_sneak(card=leader)
    ally = current.create_permanent(BEAR, 0, summoning_sick=False)
    power_before = ally.power

    current.execute_sneak_action(cast_option(current))
    current.execute_priority_action(current.legal_priority_actions(0)[0])
    current.execute_priority_action(current.legal_priority_actions(1)[0])
    current.process_priority_resolution()

    assert current.priority_state is not None
    assert current.stack and current.stack[-1].source_card.name == leader.name
    assert ally.power == power_before
    resolve_priority(current)
    assert ally.power == power_before + 2


def test_sneak_payment_and_zone_changes_are_new_objects():
    current, attacker = setup_sneak()
    card = current.players[0].hand[0]
    current.execute_sneak_action(cast_option(current))
    evidence = current.sneak_evidence[-1]

    assert (
        len(
            {
                attacker.object_id,
                evidence.returned_hand_id,
                card.object_id,
                evidence.stack_object_id,
            }
        )
        == 4
    )
    assert attacker.zone == card.zone == "former"


@pytest.mark.parametrize("effective_mana", [0])
def test_insufficient_mana_generates_no_sneak_cast(effective_mana):
    current, _attacker = setup_sneak(mana=effective_mana)
    before = current.snapshot()
    assert all(option.kind is not ActionKind.CAST for option in current.legal_sneak_actions(0))
    assert current.snapshot() == before


def test_illegal_timing_wrong_zone_and_fabricated_options_fail_without_mutation():
    current = Game(([PLAINS] * 20, [PLAINS] * 20), seed=312)
    current.begin_turn()
    card = current.set_hand_for_testing(0, [SNEAK_CREATURE])[0]
    attacker = current.create_permanent(BEAR, 0, summoning_sick=False)
    assert current.sneak_payment_plan(0, card, attacker) is None

    before = current.snapshot()
    fake = ActionOption(
        ActionKind.CAST,
        0,
        object_id=card.object_id,
        cost_object_id="fabricated",
        oracle_fragment=SNEAK_FRAGMENT,
    )
    with pytest.raises(ValueError, match="not currently legal"):
        current.execute_sneak_action(fake)
    assert current.snapshot() == before


def test_wrong_zone_equal_valued_and_unsupported_target_choices_are_rejected():
    current, attacker = setup_sneak()
    card = current.players[0].hand[0]
    fabricated = CardObject("fabricated", card.card, card.owner, card.controller, "hand")
    assert current.sneak_payment_plan(0, fabricated, attacker) is None

    valid = cast_option(current)
    forged = replace(valid, target_id=attacker.object_id)
    before = current.snapshot()
    with pytest.raises(ValueError, match="not currently legal"):
        current.execute_sneak_action(forged)
    assert current.snapshot() == before

    moved = current.move_object(card, "graveyard", reason="test_wrong_zone")
    assert current.sneak_payment_plan(0, moved, attacker) is None  # type: ignore[arg-type]


def test_stale_option_and_stale_attacker_fail_before_partial_payment():
    current, attacker = setup_sneak()
    option = cast_option(current)
    land = next(permanent for permanent in current.players[0].battlefield if permanent.card.is_land)
    land.tapped = True
    before = current.snapshot()

    with pytest.raises(ValueError, match="not currently legal"):
        current.execute_sneak_action(option)
    assert current.snapshot() == before
    assert current.is_authoritative(attacker, "battlefield")
    assert current.is_authoritative(current.players[0].hand[0], "hand")


def test_blocked_attacker_is_not_a_legal_return_cost():
    current = Game(([PLAINS] * 20, [PLAINS] * 20), seed=313)
    current.begin_turn()
    current.set_hand_for_testing(0, [SNEAK_CREATURE])
    current.create_permanent(PLAINS, 0, summoning_sick=False)
    attacker = current.create_permanent(BEAR, 0, summoning_sick=False)
    blocker = current.create_permanent(BEAR, 1, summoning_sick=False)
    current.advance_to(TurnStep.DECLARE_ATTACKERS)
    attack = ActionOption(ActionKind.DECLARE_ATTACKERS, 0, attacker_ids=(attacker.object_id,))
    current.execute_attack_action(attack)
    current.execute_block_action(
        ActionOption(
            ActionKind.DECLARE_BLOCKERS,
            1,
            blocks=((attacker.object_id, blocker.object_id),),
        )
    )

    assert current.step is TurnStep.COMBAT_DAMAGE
    assert not current.legal_sneak_actions(0)


def test_keyword_only_sneak_is_recognized_and_executable_generically():
    keyword_only = replace(SNEAK_CREATURE, oracle_text="Sneak {2}{W}{W}")
    semantics = CardInterpreter().sneak_semantic_coverage(keyword_only, keyword_only.oracle_text)
    assert semantics is not None and semantics.coverage.fully_supported


def test_hybrid_and_noncreature_sneak_remain_explicitly_unsupported():
    hybrid = replace(SNEAK_CREATURE, oracle_text="Sneak {3}{W/B}")
    noncreature = replace(
        SNEAK_CREATURE,
        type_line="Sorcery",
        power=None,
        toughness=None,
        oracle_text="Sneak {W}",
    )
    hybrid_result = CardInterpreter().sneak_semantic_coverage(hybrid, hybrid.oracle_text)
    noncreature_result = CardInterpreter().sneak_semantic_coverage(
        noncreature, noncreature.oracle_text
    )

    assert hybrid_result is not None and not hybrid_result.coverage.payload_executable
    assert hybrid_result.limitations == ("sneak_cost_shape_not_implemented",)
    assert noncreature_result is not None and not noncreature_result.coverage.payload_executable
    assert noncreature_result.limitations == ("sneak_noncreature_spell_not_implemented",)


def test_sneak_reference_does_not_become_an_executable_parent():
    fragment = "When this creature enters, if its sneak cost was paid, draw a card."
    card = replace(SNEAK_CREATURE, oracle_text=fragment)
    semantics = CardInterpreter().sneak_semantic_coverage(card, fragment)

    assert semantics is not None
    assert semantics.coverage.payload_executable is False
    assert semantics.coverage.parent_executable is False
    assert semantics.coverage.fully_supported is False
    assert semantics.limitations == ("sneak_reference_or_granted_ability_not_implemented",)


def test_sneak_creature_is_unblocked_after_blockers_and_does_not_retrigger_attack():
    current, _attacker = setup_sneak()
    attacks_before = sum(event["event"] == "attackers_declared" for event in current.events)
    current.execute_sneak_action(cast_option(current))
    resolve_priority(current)

    assert sum(event["event"] == "attackers_declared" for event in current.events) == attacks_before
    assert not any(
        attacker_id == current.sneak_evidence[-1].resolved_object_id
        for attacker_id, _blocker_id in current._combat_blocks
    )


def test_sneak_evidence_is_reconstructive_and_snapshot_deterministic():
    first, _ = setup_sneak()
    first.execute_sneak_action(cast_option(first))
    resolve_priority(first)
    first_snapshot = first.snapshot()

    second, _ = setup_sneak()
    second.execute_sneak_action(cast_option(second))
    resolve_priority(second)
    second_snapshot = second.snapshot()

    assert first_snapshot == second_snapshot
    evidence = first_snapshot["sneak"][0]
    assert evidence == {
        "card": "Anonymous Sneak",
        "hand_object_id": evidence["hand_object_id"],
        "controller": 0,
        "turn": 1,
        "step": "declare_blockers",
        "oracle_fragment": SNEAK_FRAGMENT,
        "mana_requirement": {"generic": 0, "colored": ["W"]},
        "mana_source_ids": evidence["mana_source_ids"],
        "returned_attacker_id": evidence["returned_attacker_id"],
        "returned_hand_id": evidence["returned_hand_id"],
        "defending_player": 1,
        "stack_object_id": evidence["stack_object_id"],
        "priority_epoch": 1,
        "resolved_object_id": evidence["resolved_object_id"],
        "entered_tapped": True,
        "entered_attacking": True,
    }


def test_corpus_memberships_and_digests_are_exact():
    recognized, executable, full = coverage_sets()

    assert (len({row[0] for row in recognized}), len(recognized)) == (27, 32)
    assert (len({row[0] for row in executable}), len(executable)) == (14, 14)
    assert (len({row[0] for row in full}), len(full)) == (14, 14)
    assert digest(recognized) == "af93d6edb678df9768372cfc215f2e4fabab455d0eeff2422d05f5a87934b320"
    assert digest(executable) == "8f49420ba3fd4e31bc9746f2e3b50f70fa9ec7add295840925a4610606bba924"
    assert digest(full) == "8f49420ba3fd4e31bc9746f2e3b50f70fa9ec7add295840925a4610606bba924"
