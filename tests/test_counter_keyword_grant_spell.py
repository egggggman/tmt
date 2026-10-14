"""Complete Oracle-derived counter plus temporary keyword spell execution."""

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
    TemporaryKeyword,
    TurnStep,
    load_facts,
)

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
SHELL = load_facts(
    load_card_data(CATALOG, CATALOG.with_suffix(".manifest.json")), {"Saved by the Shell"}
)["Saved by the Shell"]
FOREST = CardFact("Forest", "", 0, "Basic Land — Forest")
TURTLE = CardFact("Quiet Turtle", "{1}{G}", 2, "Creature — Turtle", power=2, toughness=2)
BEAR = CardFact("Quiet Bear", "{1}{G}", 2, "Creature — Bear", power=2, toughness=2)
BLOCKER = replace(BEAR, name="Small Blocker", power=1, toughness=1)
FRAGMENT = CardInterpreter.fragments(SHELL)[1]


def game(*, lands=2, turtle=True, seed=311):
    current = Game(([FOREST] * 40, [FOREST] * 40), seed=seed)
    current.begin_turn()
    for _ in range(lands):
        current.create_permanent(FOREST, 0)
    target = current.create_permanent(TURTLE if turtle else BEAR, 0, summoning_sick=False)
    card = current.set_hand_for_testing(0, [SHELL])[0]
    return current, card, target


def drain(current):
    while current.priority_state is not None:
        state = current.priority_state
        if state.resolution_pending:
            current.process_priority_resolution()
        else:
            current.execute_priority_action(
                next(
                    action
                    for action in current.legal_priority_actions(state.player_index)
                    if action.kind is ActionKind.PASS_PRIORITY
                )
            )


def test_frozen_and_renamed_oracle_accept_whole_spell_only():
    interpreter = CardInterpreter()
    for source in (SHELL, replace(SHELL, name="Unnamed Rescue")):
        program = interpreter.targeted_counter_keyword_grant_program(source)
        assert program is not None
        assert program.counter_type == "+1/+1" and program.quantity == 1
        assert program.keywords == ("trample", "hexproof", "indestructible")
        assert program.cost_reduction is not None and program.cost_reduction.quality == "Turtle"
        assert interpreter.cast_program(source).kind is CastKind.TARGETED_COUNTER_KEYWORD_GRANT
        assert interpreter.trample_semantic_coverage(source, FRAGMENT).coverage.fully_supported
        assert interpreter.unsupported_fragments(source) == ()
    for text in (
        SHELL.oracle_text + "\nDraw a card.",
        SHELL.oracle_text.replace("indestructible", "flying"),
        SHELL.oracle_text.replace("if you control a Turtle", "if you control three Turtles"),
        SHELL.oracle_text.replace("target creature you control", "target creature"),
        SHELL.oracle_text.replace("until end of turn", "forever"),
    ):
        partial = replace(SHELL, oracle_text=text)
        assert interpreter.targeted_counter_keyword_grant_program(partial) is None
        assert interpreter.cast_program(partial).kind is CastKind.UNSUPPORTED


def test_cost_reduction_target_generation_and_no_partial_announcement():
    current, card, own = game(lands=1)
    other = current.create_permanent(BEAR, 1)
    assert current.casting_requirement(0, card).generic == 0
    offered = [a for a in current.legal_main_actions(0) if a.object_id == card.object_id]
    assert [(a.target_id, a.oracle_fragment) for a in offered] == [(own.object_id, FRAGMENT)]
    assert current.announce_spell(0, card, other) is None
    assert current.announce_spell(0, card) is None
    assert not any(e["event"] == "cost_paid" for e in current.events)
    assert current.execute_main_action(offered[0])
    spell = current.stack[-1]
    assert spell.target_id == own.object_id and own.counters == {}
    paid = next(e for e in current.events if e["event"] == "cost_paid")
    assert paid["generic"] == 0 and paid["colored"] == ["G"]
    drain(current)
    assert own.counters["+1/+1"] == 1 and (own.power, own.toughness) == (3, 3)
    resolved = next(e for e in current.events if e["event"] == "counter_keyword_grant_resolved")
    assert resolved["stack_object_id"] == spell.object_id
    assert resolved["target_id"] == own.object_id
    assert [effect.source_id for effect in own.temporary_keyword_effects] == [spell.object_id] * 3
    current.check_invariants()


def test_no_discount_uses_full_cost_and_stale_payment_is_rejected():
    current, card, own = game(turtle=False)
    assert current.casting_requirement(0, card).generic == 1
    offered = next(a for a in current.legal_main_actions(0) if a.object_id == card.object_id)
    current.players[0].battlefield[0].tapped = True
    with pytest.raises(ValueError, match="not currently legal"):
        current.execute_main_action(offered)
    assert card.zone == "hand" and own.counters == {}
    assert not any(e["event"] == "cost_paid" for e in current.events)
    current.players[0].battlefield[0].tapped = False
    spell = current.announce_spell(0, card, own)
    assert spell is not None
    assert next(e for e in current.events if e["event"] == "cost_paid")["generic"] == 1
    current.resolve_top_of_stack()
    current.check_invariants()


def test_priority_response_target_control_and_zone_rechecks():
    current, card, own = game(lands=1)
    current._begin_priority_window(allow_empty=True, priority_player=0)
    response = next(a for a in current.legal_priority_actions(0) if a.object_id == card.object_id)
    current.execute_priority_action(response)
    spell = current.stack[-1]
    assert spell.target_id == own.object_id
    own.controller = 1
    current.players[0].battlefield.remove(own)
    current.players[1].battlefield.append(own)
    drain(current)
    assert own.counters == {} and not own.temporary_keyword_effects
    assert any(e["event"] == "spell_resolved_no_effect" for e in current.events)
    assert not any(e["event"] == "counter_keyword_grant_resolved" for e in current.events)
    current.check_invariants()

    current, card, own = game(lands=1)
    spell = current.announce_spell(0, card, own)
    current.move_object(own, "graveyard", reason="target_departed")
    replacement = current.create_permanent(TURTLE, 0)
    current.resolve_top_of_stack()
    assert spell.zone == "former" and replacement.counters == {}
    assert not replacement.temporary_keyword_effects
    current.check_invariants()


def test_temporary_hexproof_restricts_opponents_but_allows_own_targeting():
    current, card, own = game(lands=1)
    current.announce_spell(0, card, own)
    current.resolve_top_of_stack()
    assert current.has_temporary_keyword(own, TemporaryKeyword.HEXPROOF)
    assert current._legal_targeting_protection(own, 0)
    assert not current._legal_targeting_protection(own, 1)
    assert not current._legal_damage_target(own, 1)
    assert not current._legal_modal_creature_target(own, 1)
    current.end_turn()
    assert own.counters["+1/+1"] == 1
    assert not current.has_temporary_keyword(own, TemporaryKeyword.HEXPROOF)
    assert current._legal_targeting_protection(own, 1)
    current.check_invariants()


def test_indestructible_prevents_destroy_and_lethal_damage_but_not_zero_toughness():
    current, card, own = game(lands=1)
    current.announce_spell(0, card, own)
    current.resolve_top_of_stack()
    current.destroy(own)
    assert own.zone == "battlefield"
    own.damage = 4
    current.check_state_based_actions()
    assert own.zone == "battlefield" and own.damage == 4
    assert any(e["event"] == "destruction_prevented" for e in current.events)
    current.end_turn()
    assert own.damage == 0 and own.zone == "battlefield"
    current.check_invariants()

    current, card, own = game(lands=1)
    current.announce_spell(0, card, own)
    current.resolve_top_of_stack()
    current.apply_pt_modifier(
        own,
        0,
        -4,
        duration="until_end_of_turn",
        source_card="Test effect",
        oracle_fragment="Target creature gets -0/-4 until end of turn.",
    )
    current.check_state_based_actions()
    assert own.zone == "former"  # Indestructible cannot save toughness at or below zero.
    current.check_invariants()


def test_trample_changes_combat_assignment_and_keyword_cleanup():
    current, card, own = game(lands=1)
    blocker = current.create_permanent(BLOCKER, 1, summoning_sick=False)
    current.announce_spell(0, card, own)
    current.resolve_top_of_stack()
    assert current.evaluated_trample(own)
    current.advance_to(TurnStep.DECLARE_ATTACKERS)
    attack = next(a for a in current.legal_attack_options(0) if a.attacker_ids == (own.object_id,))
    current.execute_attack_action(attack)
    current.execute_block_action(
        ActionOption(ActionKind.DECLARE_BLOCKERS, 1, blocks=((own.object_id, blocker.object_id),))
    )
    result = current.resolve_combat_damage()
    assert result.trample_results and current.players[1].life == 18
    assert own.zone == "battlefield" and blocker.zone == "former"
    current.end_turn()
    assert not current.evaluated_trample(own)
    current.check_invariants()


def test_countered_spell_does_not_apply_partial_effect_and_replay_matches():
    def run():
        current, card, own = game(lands=1)
        option = next(a for a in current.legal_main_actions(0) if a.object_id == card.object_id)
        current.execute_main_action(option)
        spell = current.stack[-1]
        current.move_object(spell, "graveyard", reason="countered")
        current.priority_state = None
        assert own.counters == {} and not own.temporary_keyword_effects
        current.check_invariants()
        return current.snapshot()

    assert run() == run()


def test_resolved_source_leaves_but_effects_remain_on_target_until_cleanup():
    current, card, own = game(lands=1)
    spell = current.announce_spell(0, card, own)
    current.resolve_top_of_stack()
    assert spell.zone == "former" and own.zone == "battlefield"
    assert current.evaluated_trample(own) and current._has_keyword(own, "Indestructible")
    current.end_turn()
    assert not current._has_keyword(own, "Indestructible")
    assert own.counters["+1/+1"] == 1
    current.check_invariants()
