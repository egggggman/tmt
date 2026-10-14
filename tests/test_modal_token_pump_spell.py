"""A complete two-mode instant through ordinary cast, stack, and combat rules."""

from dataclasses import replace
from pathlib import Path

import pytest

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter, CastKind, StrikeKeyword
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
MODAL = load_facts(
    load_card_data(CATALOG, CATALOG.with_suffix(".manifest.json")), {"Mouser Attack!"}
)["Mouser Attack!"]
MOUNTAIN = CardFact("Mountain", "", 0, "Basic Land — Mountain")
BEAR = CardFact("Bear", "{1}", 1, "Creature — Bear", power=2, toughness=2)
HEXPROOF = replace(BEAR, name="Protected", keywords=("Hexproof",))
TOKEN_MODE, PUMP_MODE = CardInterpreter.fragments(MODAL)[1:]


def game(seed=310):
    current = Game(([MOUNTAIN] * 40, [MOUNTAIN] * 40), seed=seed)
    current.begin_turn()
    current.create_permanent(MOUNTAIN, 0)
    current.create_permanent(MOUNTAIN, 0)
    return current


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


def test_frozen_oracle_and_renamed_fixture_require_both_complete_modes():
    interpreter = CardInterpreter()
    for source in (MODAL, replace(MODAL, name="Anonymous Instant")):
        program = interpreter.modal_token_or_creature_pump_program(source)
        assert program is not None and program.token.executable
        assert program.power == 3 and program.toughness == 0
        assert interpreter.cast_program(source).kind is CastKind.MODAL_TOKEN_OR_CREATURE_PUMP
        assert interpreter.token_semantic_coverage(source, TOKEN_MODE).fully_supported
        assert interpreter.strike_semantic_coverage(source, PUMP_MODE).coverage.fully_supported
        assert interpreter.unsupported_fragments(source) == ()
    for text in (
        MODAL.oracle_text + "\nDraw a card.",
        MODAL.oracle_text.replace("first strike", "flying"),
        MODAL.oracle_text.replace("artifact creature", "artifact"),
        MODAL.oracle_text.replace("Choose one", "Choose two"),
    ):
        incomplete = replace(MODAL, oracle_text=text)
        assert interpreter.modal_token_or_creature_pump_program(incomplete) is None
        assert interpreter.cast_program(incomplete).kind is CastKind.UNSUPPORTED


def test_token_mode_offered_without_targets_locks_choice_and_uses_paid_stack():
    current = game()
    card = current.set_hand_for_testing(0, [MODAL])[0]
    options = [
        option for option in current.legal_main_actions(0) if option.object_id == card.object_id
    ]
    assert len(options) == 1 and options[0].oracle_fragment == TOKEN_MODE
    assert current.announce_spell(0, card) is None
    assert current.announce_spell(0, card, mode_fragment="• Create a Food token.") is None
    assert not any(e["event"] == "cost_paid" for e in current.events)
    assert current.execute_main_action(options[0])
    spell = current.stack[-1]
    assert spell.mode_fragment == TOKEN_MODE and spell.target_id is None
    assert (
        current.priority_state is not None
        and sum(p.tapped for p in current.players[0].battlefield) == 2
    )
    assert not [p for p in current.players[0].battlefield if p.is_token]
    drain(current)
    tokens = [p for p in current.players[0].battlefield if p.is_token]
    assert len(tokens) == 1 and (tokens[0].power, tokens[0].toughness) == (1, 1)
    assert tokens[0].type_line == "Artifact Creature — Robot"
    created = next(e for e in current.events if e["event"] == "tokens_created")
    assert created["source_id"] == spell.object_id and created["oracle_fragment"] == TOKEN_MODE
    assert [e["mode_fragment"] for e in current.events if e["event"] == "modal_spell_resolved"] == [
        TOKEN_MODE
    ]
    current.check_invariants()


def test_targeted_mode_protection_payment_effects_and_cleanup():
    current = game()
    own = current.create_permanent(BEAR, 0, summoning_sick=False)
    enemy = current.create_permanent(BEAR, 1)
    protected = current.create_permanent(HEXPROOF, 1)
    card = current.set_hand_for_testing(0, [MODAL])[0]
    options = [
        option for option in current.legal_main_actions(0) if option.object_id == card.object_id
    ]
    assert {(a.oracle_fragment, a.target_id) for a in options} == {
        (TOKEN_MODE, None),
        (PUMP_MODE, own.object_id),
        (PUMP_MODE, enemy.object_id),
    }
    assert current.announce_spell(0, card, protected, mode_fragment=PUMP_MODE) is None
    assert current.announce_spell(0, card, enemy, mode_fragment=TOKEN_MODE) is None
    assert not any(p.tapped for p in current.players[0].battlefield)
    pump = next(a for a in options if a.target_id == own.object_id)
    current.execute_main_action(pump)
    spell = current.stack[-1]
    assert own.power == 2 and spell.target_id == own.object_id
    drain(current)
    assert (own.power, own.toughness) == (5, 2)
    assert current.evaluated_strike_keywords(own) == {StrikeKeyword.FIRST_STRIKE}
    resolved = next(e for e in current.events if e["event"] == "modal_spell_resolved")
    assert resolved["stack_object_id"] == spell.object_id and resolved["target_id"] == own.object_id
    current.end_turn()
    assert own.power == 2 and not current.evaluated_strike_keywords(own)
    current.check_invariants()


def test_target_zone_or_type_change_fizzles_without_switching_modes():
    for change in ("zone", "type", "hexproof"):
        current = game()
        target = current.create_permanent(BEAR, 1)
        card = current.set_hand_for_testing(0, [MODAL])[0]
        spell = current.announce_spell(0, card, target, mode_fragment=PUMP_MODE)
        assert spell is not None
        if change == "zone":
            current.move_object(target, "graveyard", reason="target_left")
            current.create_permanent(BEAR, 1)
        elif change == "type":
            target.type_line_override = "Artifact"
        else:
            target.card = HEXPROOF
        current.resolve_top_of_stack()
        assert not any(e["event"] == "modal_spell_resolved" for e in current.events)
        assert any(e["event"] == "spell_resolved_no_effect" for e in current.events)
        assert not any(p.is_token for p in current.players[0].battlefield)
        current.check_invariants()


def test_priority_mode_choice_is_locked_and_countered_source_has_no_effect():
    current = game()
    target = current.create_permanent(BEAR, 0)
    card = current.set_hand_for_testing(0, [MODAL])[0]
    current._begin_priority_window(allow_empty=True, priority_player=0)
    offered = [
        option for option in current.legal_priority_actions(0) if option.object_id == card.object_id
    ]
    assert {(a.oracle_fragment, a.target_id) for a in offered} == {
        (TOKEN_MODE, None),
        (PUMP_MODE, target.object_id),
    }
    forged = replace(offered[0], oracle_fragment="• Draw a card.")
    with pytest.raises(ValueError, match="not currently legal"):
        current.execute_priority_action(forged)
    assert current.execute_priority_action(offered[0])
    spell = current.stack[-1]
    assert spell.mode_fragment == TOKEN_MODE and current.priority_state is not None
    assert not [p for p in current.players[0].battlefield if p.is_token]
    current.move_object(spell, "graveyard", reason="countered_response")
    current.priority_state = None
    assert not [p for p in current.players[0].battlefield if p.is_token]
    assert not any(e["event"] == "modal_spell_resolved" for e in current.events)
    current.check_invariants()


def test_payment_revalidated_before_targeted_mode_commit():
    current = game()
    target = current.create_permanent(BEAR, 0)
    card = current.set_hand_for_testing(0, [MODAL])[0]
    offered = next(
        action
        for action in current.legal_main_actions(0)
        if action.object_id == card.object_id and action.oracle_fragment == PUMP_MODE
    )
    current.players[0].battlefield[0].tapped = True
    with pytest.raises(ValueError, match="not currently legal"):
        current.execute_main_action(offered)
    assert card.zone == "hand" and target.power == 2 and not current.stack
    assert not any(e["event"] == "cost_paid" for e in current.events)
    current.check_invariants()


def test_priority_response_combat_first_strike_and_deterministic_replay():
    def run():
        current = game()
        attacker = current.create_permanent(BEAR, 0, summoning_sick=False)
        blocker = current.create_permanent(BEAR, 1)
        # Main-phase cast opens normal priority, then the resolved grant informs combat.
        card = current.set_hand_for_testing(0, [MODAL])[0]
        response = next(
            action
            for action in current.legal_main_actions(0)
            if action.object_id == card.object_id
            and action.oracle_fragment == PUMP_MODE
            and action.target_id == attacker.object_id
        )
        current.execute_main_action(response)
        drain(current)
        current.advance_to(TurnStep.DECLARE_ATTACKERS)
        attack = next(
            action
            for action in current.legal_attack_options(0)
            if action.attacker_ids == (attacker.object_id,)
        )
        current.execute_attack_action(attack)
        current.execute_block_action(
            ActionOption(
                ActionKind.DECLARE_BLOCKERS, 1, blocks=((attacker.object_id, blocker.object_id),)
            )
        )
        assert attacker.power == 5 and current.evaluated_strike_keywords(attacker) == {
            StrikeKeyword.FIRST_STRIKE
        }
        first = current.resolve_combat_damage()
        assert first.removed_before_next_step == (blocker.object_id,)
        current.resolve_combat_damage()
        current.check_invariants()
        return current.snapshot()

    assert run() == run()
