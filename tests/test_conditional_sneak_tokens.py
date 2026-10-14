"""Complete token spell entry, Sneak timing and combat participation."""

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
    {"The Last Ronin's Technique"},
)["The Last Ronin's Technique"]
PLAINS = CardFact("Plains", "", 0, "Basic Land — Plains")
ATTACKER = CardFact("Quiet Attacker", "{W}", 1, "Creature — Scout", power=2, toughness=2)


def game(*, lands=4, seed=321):
    current = Game(([PLAINS] * 40, [PLAINS] * 40), seed=seed)
    current.begin_turn()
    for _ in range(lands):
        current.create_permanent(PLAINS, 0)
    card = current.set_hand_for_testing(0, [CARD])[0]
    return current, card


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


def test_interpreter_requires_complete_generic_spell_and_rejects_partial_variants():
    interpreter = CardInterpreter()
    for card in (CARD, replace(CARD, name="Anonymous Token Spell")):
        program = interpreter.conditional_sneak_tokens_program(card)
        assert program is not None
        assert program.token.quantity == 3 and program.token.definition.power == 1
        assert interpreter.cast_program(card).kind is CastKind.CONDITIONAL_SNEAK_TOKENS
        assert interpreter.sneak_semantic_coverage(
            card, program.sneak_fragment
        ).coverage.fully_supported
        assert interpreter.unsupported_fragments(card) == ()
    for text in (
        CARD.oracle_text + "\nDraw a card.",
        CARD.oracle_text.replace("three", "that many"),
        CARD.oracle_text.replace("this spell's sneak cost", "another spell's sneak cost"),
        CARD.oracle_text.replace("tapped and attacking", "attacking"),
        CARD.oracle_text.replace("return an unblocked attacker", "sacrifice an attacker"),
    ):
        assert interpreter.conditional_sneak_tokens_program(replace(CARD, oracle_text=text)) is None


def test_normal_payment_creates_untapped_nonattacking_tokens_with_entry_provenance():
    current, card = game()
    action = next(a for a in current.legal_main_actions(0) if a.object_id == card.object_id)
    assert current.execute_main_action(action)
    drain(current)
    event = next(e for e in current.events if e["event"] == "conditional_tokens_resolved")
    assert not event["sneak_cost_paid"] and not event["tapped"]
    assert event["attacking_defender"] is None
    tokens = [current._objects[item] for item in event["token_ids"]]
    assert len(tokens) == 3 and all(t.is_token and t.power == t.toughness == 1 for t in tokens)
    assert all(not t.tapped and t.controller == 0 for t in tokens)
    creation = next(e for e in current.events if e["event"] == "tokens_created")
    assert creation["object_ids"] == event["token_ids"]
    assert current._combat_attackers == ()
    assert any(e["event"] == "cost_paid" and e["generic"] == 3 for e in current.events)
    current.check_invariants()


def test_sneak_enters_tapped_attacking_after_blockers_and_deals_combat_damage():
    def run():
        current, card = game(lands=2, seed=322)
        attacker = current.create_permanent(ATTACKER, 0, summoning_sick=False)
        current.advance_to(TurnStep.DECLARE_ATTACKERS)
        current.execute_attack_action(
            ActionOption(ActionKind.DECLARE_ATTACKERS, 0, attacker_ids=(attacker.object_id,))
        )
        current.execute_block_action(ActionOption(ActionKind.DECLARE_BLOCKERS, 1))
        action = next(a for a in current.legal_sneak_actions(0) if a.object_id == card.object_id)
        current.execute_sneak_action(action)
        assert attacker.zone == "former" and not current._combat_attackers
        stacked = current.stack[-1]
        with pytest.raises(ValueError, match="before all players pass"):
            current.resolve_top_of_stack()
        drain(current)
        event = next(e for e in current.events if e["event"] == "conditional_tokens_resolved")
        assert event["stack_object_id"] == stacked.object_id
        assert event["sneak_cost_paid"] and event["attacking_defender"] == 1
        assert tuple(event["token_ids"]) == current._combat_attackers
        assert all(current._objects[item].tapped for item in event["token_ids"])
        assert all(current._objects[item].zone == "battlefield" for item in event["token_ids"])
        assert current._combat_blocks == ()
        assert len([e for e in current.events if e["event"] == "sneak_cost_paid"]) == 1
        assert not any(
            e["event"] == "attackers_declared" and e["attackers"] == event["token_ids"]
            for e in current.events
        )
        current.transition_to(TurnStep.COMBAT_DAMAGE)
        current.resolve_combat_damage()
        assert current.players[1].life == 17
        current.check_invariants()
        return current.snapshot()

    assert run() == run()


def test_illegal_sneak_or_countered_spell_does_not_create_tokens():
    current, card = game(lands=1)
    assert not any(a.object_id == card.object_id for a in current.legal_main_actions(0))
    assert not current.legal_sneak_actions(0)
    assert current.announce_spell(0, card) is None
    other, card = game(seed=323)
    stacked = other.announce_spell(0, card)
    assert stacked is not None
    other.move_object(stacked, "graveyard", reason="countered")
    assert not any(e["event"] == "tokens_created" for e in other.events)
    other.check_invariants()
