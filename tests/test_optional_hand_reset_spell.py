"""Complete optional hand reset through normal and fixed Sneak casting."""

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
    {"Raphael's Technique"},
)["Raphael's Technique"]
MOUNTAIN = CardFact("Mountain", "", 0, "Basic Land — Mountain")
BEAR = CardFact("Quiet Bear", "{1}{R}", 2, "Creature — Bear", power=2, toughness=2)


def game(*, lands=6, chooser=None, seed=319):
    current = Game(([MOUNTAIN] * 40, [MOUNTAIN] * 40), seed=seed, hand_reset_chooser=chooser)
    current.begin_turn()
    for _ in range(lands):
        current.create_permanent(MOUNTAIN, 0)
    spell = current.set_hand_for_testing(0, [CARD, BEAR])[0]
    current.set_hand_for_testing(1, [BEAR, BEAR])
    return current, spell


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


def test_complete_oracle_parser_and_sneak_fail_closed_without_names():
    interpreter = CardInterpreter()
    for card in (CARD, replace(CARD, name="Anonymous Reset")):
        program = interpreter.optional_hand_reset_program(card)
        assert program is not None and program.draw_quantity == 7
        assert interpreter.cast_program(card).kind is CastKind.OPTIONAL_HAND_RESET
        assert interpreter.sneak_semantic_coverage(
            card, program.sneak_fragment
        ).coverage.fully_supported
        assert interpreter.unsupported_fragments(card) == ()
    for text in (
        CARD.oracle_text + "\nCreate a token.",
        CARD.oracle_text.replace("may discard", "must discard"),
        CARD.oracle_text.replace("draw seven cards.", "draw seven cards, then scry 1."),
        CARD.oracle_text.replace("return an unblocked attacker", "sacrifice an attacker"),
    ):
        card = replace(CARD, oracle_text=text)
        assert interpreter.optional_hand_reset_program(card) is None
        assert interpreter.cast_program(card).kind is CastKind.UNSUPPORTED


def test_normal_payment_and_independent_decline_preserves_hand():
    seen = []

    def choose(index, cards, context):
        seen.append((index, tuple(c.name for c in cards), context.own_hand))
        return index == 0

    current, spell = game(chooser=choose)
    opponent_hand = tuple(current.players[1].hand)
    action = next(a for a in current.legal_main_actions(0) if a.object_id == spell.object_id)
    assert current.execute_main_action(action)
    assert not seen
    paid = next(e for e in current.events if e["event"] == "cost_paid")
    assert paid["generic"] == 4 and paid["colored"] == ["R", "R"]
    drain(current)
    event = next(e for e in current.events if e["event"] == "optional_hand_reset_resolved")
    assert [x["discard_and_draw"] for x in event["choices"]] == [True, False]
    assert len(event["discarded"][0]["zone_ids"]) == 1
    assert event["discarded"][1]["zone_ids"] == []
    assert len(event["drawn"][0]["hand_ids"]) == 7
    assert event["drawn"][1]["hand_ids"] == []
    assert tuple(current.players[1].hand) == opponent_hand
    assert [x[0] for x in seen] == [0, 1]
    current.check_invariants()


def test_apnap_choices_precede_all_discards_and_draws():
    seen = []

    def choose(index, cards, _context):
        seen.append((index, len(cards)))
        return True

    current, spell = game(chooser=choose)
    assert current.announce_spell(0, spell) is not None
    old_hands = [tuple(card.object_id for card in player.hand) for player in current.players]
    current.resolve_top_of_stack()
    event = next(e for e in current.events if e["event"] == "optional_hand_reset_resolved")
    assert seen == [(0, 1), (1, 2)]
    for index in (0, 1):
        assert [pair[0] for pair in event["discarded"][index]["zone_ids"]] == list(old_hands[index])
        assert len(event["drawn"][index]["hand_ids"]) == 7
    cast_event = next(
        i
        for i, e in enumerate(current.events)
        if e["event"] == "zone_changed" and e.get("reason") == "spell_cast"
    )
    transitions = [
        (i, e["reason"])
        for i, e in enumerate(current.events)
        if i > cast_event
        and e["event"] == "zone_changed"
        and e.get("reason") in {"optional_hand_reset_discard", "draw"}
    ]
    assert max(i for i, reason in transitions if reason == "optional_hand_reset_discard") < min(
        i for i, reason in transitions if reason == "draw"
    )
    current.check_invariants()


def test_priority_response_and_illegal_target_or_payment():
    current, spell = game(lands=5)
    assert current.announce_spell(0, spell) is None
    assert all(a.object_id != spell.object_id for a in current.legal_main_actions(0))
    current.create_permanent(MOUNTAIN, 0)
    target = current.create_permanent(BEAR, 1)
    assert current.announce_spell(0, spell, target) is None
    current.advance_to(TurnStep.DECLARE_ATTACKERS)
    assert current.announce_spell(0, spell) is None
    current._begin_priority_window(allow_empty=True, priority_player=0)
    option = next(a for a in current.legal_priority_actions(0) if a.object_id == spell.object_id)
    assert current.execute_priority_action(option)
    drain(current)
    assert any(e["event"] == "optional_hand_reset_resolved" for e in current.events)
    current.check_invariants()


def test_sneak_payment_source_departure_priority_and_deterministic_replay():
    def run():
        current, spell = game(lands=3, seed=320)
        attacker = current.create_permanent(BEAR, 0, summoning_sick=False)
        current.advance_to(TurnStep.DECLARE_ATTACKERS)
        current.execute_attack_action(
            ActionOption(ActionKind.DECLARE_ATTACKERS, 0, attacker_ids=(attacker.object_id,))
        )
        current.execute_block_action(ActionOption(ActionKind.DECLARE_BLOCKERS, 1))
        option = next(a for a in current.legal_sneak_actions(0) if a.object_id == spell.object_id)
        current.execute_sneak_action(option)
        stacked = current.stack[-1]
        assert attacker.zone == "former"
        with pytest.raises(ValueError, match="before all players pass"):
            current.resolve_top_of_stack()
        drain(current)
        event = next(e for e in current.events if e["event"] == "optional_hand_reset_resolved")
        assert event["stack_object_id"] == stacked.object_id
        assert any(e["event"] == "sneak_cost_paid" for e in current.events)
        assert len(event["drawn"][0]["hand_ids"]) == 7
        current.check_invariants()
        return current.snapshot()

    assert run() == run()


def test_invalid_or_impure_choices_commit_no_discard_or_draw():
    for chooser in (lambda *_: None, lambda *_: 1):
        current, spell = game(chooser=chooser)
        current.announce_spell(0, spell)
        hands = tuple(tuple(player.hand) for player in current.players)
        with pytest.raises(ValueError, match="choice must be a boolean"):
            current.resolve_top_of_stack()
        assert tuple(tuple(player.hand) for player in current.players) == hands
        assert not any(e["event"] == "optional_hand_reset_resolved" for e in current.events)
    current, spell = game()
    victim = current.players[1].hand[0]
    current.hand_reset_chooser = lambda *_: current.move_object(victim, "graveyard")
    current.announce_spell(0, spell)
    with pytest.raises(ValueError, match="chooser cannot move"):
        current.resolve_top_of_stack()
    assert victim.zone == "hand"


def test_countered_spell_has_no_choices_or_hand_movement():
    called = []
    current, spell = game(chooser=lambda *args: called.append(args) or True)
    stacked = current.announce_spell(0, spell)
    assert stacked is not None
    hands = tuple(tuple(player.hand) for player in current.players)
    current.move_object(stacked, "graveyard", reason="countered")
    assert not called
    assert tuple(tuple(player.hand) for player in current.players) == hands
    current.check_invariants()
