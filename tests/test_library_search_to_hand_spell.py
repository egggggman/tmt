"""Unrestricted private library search with normal and Sneak casting."""

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
    {"Splinter's Technique"},
)["Splinter's Technique"]
SWAMP = CardFact("Swamp", "", 0, "Basic Land — Swamp")
BEAR = CardFact("Quiet Bear", "{1}{B}", 2, "Creature — Bear", power=2, toughness=2)
RELIC = CardFact("Quiet Relic", "{2}", 2, "Artifact")


def game(*, lands=4, chooser=None, seed=315):
    current = Game(([SWAMP] * 40, [SWAMP] * 40), seed=seed, library_search_chooser=chooser)
    current.begin_turn()
    for _ in range(lands):
        current.create_permanent(SWAMP, 0)
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
                    option
                    for option in current.legal_priority_actions(state.player_index)
                    if option.kind is ActionKind.PASS_PRIORITY
                )
            )


def test_complete_parser_and_sneak_are_name_independent_and_fail_closed():
    interpreter = CardInterpreter()
    for card in (CARD, replace(CARD, name="Anonymous Search")):
        program = interpreter.library_search_to_hand_program(card)
        assert program is not None and program.sneak_fragment is not None
        assert interpreter.cast_program(card).kind is CastKind.LIBRARY_SEARCH_TO_HAND
        assert interpreter.sneak_semantic_coverage(
            card, program.sneak_fragment
        ).coverage.fully_supported
        assert interpreter.unsupported_fragments(card) == ()
    for text in (
        CARD.oracle_text + "\nDraw a card.",
        CARD.oracle_text.replace("then shuffle.", "then scry 1."),
        CARD.oracle_text.replace("a card", "a creature card"),
        CARD.oracle_text.replace("return an unblocked attacker", "sacrifice an attacker"),
    ):
        partial = replace(CARD, oracle_text=text)
        assert interpreter.library_search_to_hand_program(partial) is None
        assert interpreter.cast_program(partial).kind is CastKind.UNSUPPORTED


def test_normal_cast_payment_private_choice_movement_and_shuffle():
    seen = []

    def choose(view, options):
        seen.append((view.player_index, len(view.cards), len(options)))
        return next(option for option in options if view.cards[-1].object_id == option.card_id)

    current, card = game(chooser=choose)
    wanted = current.players[0].library[-1]
    current.players[0].library[-1] = current._create_card_object(RELIC, 0, "library")
    wanted.zone = "former"  # Fixture replaces one private library card before gameplay.
    wanted_id = current.players[0].library[-1].object_id
    before_ids = {item.object_id for item in current.players[0].library}
    action = next(a for a in current.legal_main_actions(0) if a.object_id == card.object_id)
    assert current.execute_main_action(action)
    spell = current.stack[-1]
    assert not seen and card.zone == "former"
    paid = next(e for e in current.events if e["event"] == "cost_paid")
    assert paid["generic"] == 3 and paid["colored"] == ["B"]
    drain(current)
    evidence = next(e for e in current.events if e["event"] == "library_search_to_hand_resolved")
    assert seen == [(0, len(before_ids), len(before_ids))]
    assert evidence["stack_object_id"] == spell.object_id
    assert evidence["selected_id"] == wanted_id
    assert current._objects[evidence["hand_id"]].name == RELIC.name
    assert len(current.players[0].library) == len(before_ids) - 1
    assert set(evidence["post_shuffle_ids"]) == before_ids - {wanted_id}
    assert not any(e["event"] == "card_revealed" for e in current.events)
    current.check_invariants()


def test_empty_library_search_still_resolves_and_shuffles():
    current, card = game()
    for obj in current.players[0].library:
        obj.zone = "former"
    current.players[0].library.clear()
    spell = current.announce_spell(0, card)
    assert spell is not None
    current.resolve_top_of_stack()
    evidence = next(e for e in current.events if e["event"] == "library_search_to_hand_resolved")
    assert evidence["selected_id"] is None and evidence["post_shuffle_ids"] == []
    current.check_invariants()


def test_payment_timing_and_illegal_target_reject_without_mutation():
    current, card = game(lands=3)
    assert not any(a.object_id == card.object_id for a in current.legal_main_actions(0))
    assert current.announce_spell(0, card) is None
    current.create_permanent(SWAMP, 0)
    target = current.create_permanent(BEAR, 1)
    assert current.announce_spell(0, card, target) is None
    current.advance_to(TurnStep.DECLARE_ATTACKERS)
    assert current.announce_spell(0, card) is None
    assert card.zone == "hand" and not any(e["event"] == "cost_paid" for e in current.events)


def test_bad_or_mutating_private_choice_rejects_before_card_movement():
    for chooser in (
        lambda _view, _options: object(),
        lambda _view, _options: None,
    ):
        current, card = game(chooser=chooser)
        current.announce_spell(0, card)
        before = tuple(current.players[0].library)
        with pytest.raises(ValueError, match="select one offered"):
            current.resolve_top_of_stack()
        assert tuple(current.players[0].library) == before
    current, card = game()
    victim = current.players[0].library[-1]
    current.library_search_chooser = lambda _view, _options: current.move_object(
        victim, "hand", reason="impure_choice"
    )
    current.announce_spell(0, card)
    with pytest.raises(ValueError, match="chooser cannot move"):
        current.resolve_top_of_stack()
    assert victim.zone == "library"


def test_sneak_alternative_cost_priority_source_independence_and_replay():
    def run():
        current, card = game(lands=2, seed=316)
        attacker = current.create_permanent(BEAR, 0, summoning_sick=False)
        current.advance_to(TurnStep.DECLARE_ATTACKERS)
        current.execute_attack_action(
            ActionOption(ActionKind.DECLARE_ATTACKERS, 0, attacker_ids=(attacker.object_id,))
        )
        current.execute_block_action(ActionOption(ActionKind.DECLARE_BLOCKERS, 1))
        option = next(a for a in current.legal_sneak_actions(0) if a.object_id == card.object_id)
        current.execute_sneak_action(option)
        spell = current.stack[-1]
        assert spell.cast_kind is CastKind.LIBRARY_SEARCH_TO_HAND
        assert attacker.zone == "former" and current.priority_state is not None
        with pytest.raises(ValueError, match="before all players pass"):
            current.resolve_top_of_stack()
        drain(current)
        assert any(
            e["event"] == "library_search_to_hand_resolved"
            and e["stack_object_id"] == spell.object_id
            for e in current.events
        )
        assert any(
            e["event"] == "sneak_cost_paid" and len(e["mana_source_ids"]) == 2
            for e in current.events
        )
        current.check_invariants()
        return current.snapshot()

    assert run() == run()


def test_generic_private_selection_prefers_needed_land_then_castable_nonland():
    def run(lands):
        current = Game(([SWAMP] * 39 + [RELIC], [SWAMP] * 40), seed=317)
        current.begin_turn()
        current.set_hand_for_testing(0, [])
        for _ in range(lands):
            current.create_permanent(SWAMP, 0)
        # Test the private choice policy directly; spell payment is covered above.
        from tmnt_design_studio.engine07 import TopCardSelectionOption
        from tmnt_design_studio.pilot_input_v2 import (
            TopCardSelectionViewV2,
            decision_context,
            describe_card,
        )

        library = current.players[0].library
        options = tuple(TopCardSelectionOption(obj.object_id) for obj in library)
        view = TopCardSelectionViewV2(
            0,
            tuple(describe_card(obj.object_id, obj.card) for obj in library),
            decision_context(current, 0),
        )
        chosen = current._default_library_search_choice(view, options)
        return current._objects[chosen.card_id].card.is_land

    assert run(2) is True
    assert run(4) is False


def test_countered_spell_has_no_private_choice_or_shuffle():
    called = []
    current, card = game(chooser=lambda view, options: called.append(view) or options[0])
    spell = current.announce_spell(0, card)
    assert spell is not None
    library_ids = tuple(obj.object_id for obj in current.players[0].library)
    current.move_object(spell, "graveyard", reason="countered")
    assert not called
    assert tuple(obj.object_id for obj in current.players[0].library) == library_ids
    assert not any(e["event"] == "library_search_to_hand_resolved" for e in current.events)
    current.check_invariants()
