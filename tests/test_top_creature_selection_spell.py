"""Bounded private top-library creature selection with normal and Sneak casting."""

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
    TopCreatureSelectionOption,
    TurnStep,
    load_facts,
)

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
CARD = load_facts(
    load_card_data(CATALOG, CATALOG.with_suffix(".manifest.json")),
    {"Michelangelo's Technique"},
)["Michelangelo's Technique"]
FOREST = CardFact("Forest", "", 0, "Basic Land — Forest")
ONE = CardFact("Small Friend", "{G}", 1, "Creature — Turtle", power=1, toughness=1)
TWO = CardFact("Medium Friend", "{1}{G}", 2, "Creature — Turtle", power=2, toughness=2)
FOUR = CardFact("Big Friend", "{3}{G}", 4, "Creature — Turtle", power=4, toughness=4)
FIVE = CardFact("Large Friend", "{4}{G}", 5, "Creature — Turtle", power=5, toughness=5)
SEVEN = CardFact("Huge Friend", "{6}{G}", 7, "Creature — Turtle", power=7, toughness=7)
ZERO = CardFact("Frail Friend", "{G}", 1, "Creature — Turtle", power=0, toughness=0)
ARTIFACT = CardFact("Quiet Relic", "{1}", 1, "Artifact")


def game(*, lands=5, seed=318, chooser=None, inspected=(), counter_chooser=None):
    current = Game(
        ([FOREST] * 40, [FOREST] * 40),
        seed=seed,
        top_creature_selection_chooser=chooser,
        counter_target_chooser=counter_chooser,
    )
    current.begin_turn()
    for _ in range(lands):
        current.create_permanent(FOREST, 0)
    originals = []
    for fact in inspected:
        obj = current._create_card_object(fact, 0, "library")
        current.players[0].library.append(obj)
        originals.append(obj)
    spell = current.set_hand_for_testing(0, [CARD])[0]
    return current, spell, originals


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


def test_complete_oracle_grammar_is_generic_and_rejects_partial_effects():
    interpreter = CardInterpreter()
    for card in (CARD, replace(CARD, name="Anonymous Selection")):
        program = interpreter.top_creature_selection_program(card)
        assert program is not None
        assert (program.count, program.maximum_creatures, program.maximum_total_mana_value) == (
            8,
            2,
            6,
        )
        assert interpreter.cast_program(card).kind is CastKind.TOP_CREATURE_SELECTION
        assert interpreter.sneak_semantic_coverage(
            card, program.sneak_fragment
        ).coverage.fully_supported
        assert interpreter.unsupported_fragments(card) == ()
    for text in (
        CARD.oracle_text + "\nDraw a card.",
        CARD.oracle_text.replace("total mana value 6", "mana value 6"),
        CARD.oracle_text.replace("in a random order", "in any order"),
        CARD.oracle_text.replace("return an unblocked attacker", "sacrifice an attacker"),
        CARD.oracle_text.replace("creature cards", "permanent cards"),
    ):
        assert interpreter.top_creature_selection_program(replace(CARD, oracle_text=text)) is None
        assert (
            interpreter.cast_program(replace(CARD, oracle_text=text)).kind is CastKind.UNSUPPORTED
        )


def test_private_legal_pair_selection_entry_identities_and_bottom_randomization():
    offered = []

    def choose(view, options):
        offered.append((view, options))
        wanted = {card.object_id for card in view.cards if card.name in {TWO.name, FOUR.name}}
        return next(option for option in options if set(option.card_ids) == wanted)

    inspected = (ONE, TWO, FOUR, FIVE, SEVEN, ARTIFACT, FOREST, ONE)
    current, spell, originals = game(chooser=choose, inspected=inspected)
    assert not offered  # Inspection happens on resolution, not cast or legal-action generation.
    action = next(a for a in current.legal_main_actions(0) if a.object_id == spell.object_id)
    assert not offered and action.choice_ids == ()
    assert current.execute_main_action(action)
    assert not offered and current.stack[-1].cast_kind is CastKind.TOP_CREATURE_SELECTION
    drain(current)
    view, options = offered[0]
    assert len(view.cards) == 8 and view.player_index == 0
    assert {card.object_id for card in view.cards} == {card.object_id for card in originals}
    assert TopCreatureSelectionOption(()) in options
    assert all(len(o.card_ids) <= 2 for o in options)
    by_id = {card.object_id: card for card in view.cards}
    assert all(sum(by_id[item].mana_value for item in o.card_ids) <= 6 for o in options)
    assert not any(SEVEN.name in {by_id[item].name for item in o.card_ids} for o in options)
    assert not any(ARTIFACT.name in {by_id[item].name for item in o.card_ids} for o in options)
    event = next(e for e in current.events if e["event"] == "top_creature_selection_resolved")
    assert [entry["library_id"] for entry in event["selected"]] == [
        originals[2].object_id,
        originals[1].object_id,
    ]  # Inspected top-to-bottom order is authoritative.
    assert len(event["bottom_ids"]) == 6
    assert [obj.object_id for obj in current.players[0].library[:6]] == event["bottom_ids"]
    assert {entry["battlefield_id"] for entry in event["selected"]} <= {
        permanent.object_id for permanent in current.players[0].battlefield
    }
    assert all(original.zone == "former" for original in originals[1:3])
    assert (
        len(
            [
                e
                for e in current.events
                if e["event"] == "zone_changed"
                and e.get("reason") == "top_creature_selection_entry"
            ]
        )
        == 2
    )
    current.check_invariants()


@pytest.mark.parametrize("selected_names", [(), (ONE.name,), (ONE.name, FOUR.name)])
def test_zero_one_or_two_choices_and_empty_library_are_legal(selected_names):
    def choose(view, options):
        wanted = set(selected_names)
        return next(
            option
            for option in options
            if {card.name for card in view.cards if card.object_id in option.card_ids} == wanted
        )

    current, spell, _ = game(chooser=choose, inspected=(ONE, FOUR, ARTIFACT))
    assert current.announce_spell(0, spell) is not None
    current.resolve_top_of_stack()
    event = next(e for e in current.events if e["event"] == "top_creature_selection_resolved")
    assert len(event["inspected_ids"]) == 8  # The pre-existing library supplies the rest.
    assert len(event["selected"]) == len(selected_names)
    current.check_invariants()


def test_invalid_or_mutating_private_choice_leaves_stack_and_zones_unchanged():
    for chooser in (
        lambda _view, _options: TopCreatureSelectionOption(("fabricated",)),
        lambda view, _options: TopCreatureSelectionOption((view.cards[0].object_id,) * 2),
        lambda view, _options: TopCreatureSelectionOption(
            (view.cards[0].object_id, view.cards[1].object_id)
        ),
    ):
        current, spell, _ = game(chooser=chooser, inspected=(FIVE, FOUR))
        assert current.announce_spell(0, spell)
        before = current.snapshot()
        with pytest.raises(ValueError, match="legal combined-value choice"):
            current.resolve_top_of_stack()
        assert current.snapshot() == before

    current, spell, _ = game(inspected=(ONE,))
    current.top_creature_selection_chooser = lambda view, _options: current.move_object(
        current.players[0].library[-1], "hand", reason="illegal_chooser_move"
    )
    assert current.announce_spell(0, spell)
    before = current.snapshot()
    with pytest.raises(ValueError, match="chooser cannot move"):
        current.resolve_top_of_stack()
    assert current.snapshot() == before


def test_sneak_cost_priority_zone_transitions_sba_and_exact_replay():
    def run():
        current, spell, originals = game(lands=4, seed=320, inspected=(ZERO, FOUR, TWO))
        attacker = current.create_permanent(ONE, 0, summoning_sick=False)
        current.advance_to(TurnStep.DECLARE_ATTACKERS)
        current.execute_attack_action(
            ActionOption(ActionKind.DECLARE_ATTACKERS, 0, attacker_ids=(attacker.object_id,))
        )
        current.execute_block_action(ActionOption(ActionKind.DECLARE_BLOCKERS, 1))
        action = next(a for a in current.legal_sneak_actions(0) if a.object_id == spell.object_id)
        current.execute_sneak_action(action)
        stacked = current.stack[-1]
        assert (
            attacker.zone == "former" and stacked.sneak_returned_attacker_id == attacker.object_id
        )
        with pytest.raises(ValueError, match="before all players pass"):
            current.resolve_top_of_stack()
        drain(current)
        event = next(e for e in current.events if e["event"] == "top_creature_selection_resolved")
        assert event["stack_object_id"] == stacked.object_id
        assert len(event["selected"]) == 2  # Four plus two fits the combined limit.
        assert originals[0].zone == "library"  # The zero-power card was not selected.
        assert any(e["event"] == "sneak_cost_paid" for e in current.events)
        current.check_invariants()
        return current.snapshot()

    assert run() == run()


def test_state_based_zero_toughness_and_countered_spell():
    current, spell, originals = game(chooser=lambda _view, options: options[-1], inspected=(ZERO,))
    assert current.announce_spell(0, spell)
    current.resolve_top_of_stack()
    event = next(e for e in current.events if e["event"] == "top_creature_selection_resolved")
    assert len(event["selected"]) == 1
    assert current._objects[event["selected"][0]["battlefield_id"]].zone == "former"
    current.check_invariants()

    other, spell, _ = game(seed=321, inspected=(ONE, FOUR))
    stacked = other.announce_spell(0, spell)
    assert stacked is not None
    other.move_object(stacked, "graveyard", reason="countered")
    assert not any(e["event"] == "top_creature_selection_resolved" for e in other.events)
    other.check_invariants()


def test_both_creatures_enter_before_alliance_choices_resolve():
    ally = CardFact(
        "Anonymous Ally",
        "{1}{G}",
        2,
        "Creature — Turtle",
        "Alliance — Whenever another creature you control enters, put a +1/+1 counter on "
        "target creature you control.",
        power=2,
        toughness=2,
    )
    offered = []

    def counter_choice(_controller, _source, candidates):
        offered.append(candidates)
        return candidates[-1]

    current, spell, _ = game(inspected=(ONE, FOUR), counter_chooser=counter_choice)
    current.create_permanent(ally, 0)
    assert current.announce_spell(0, spell)
    current.resolve_top_of_stack()
    event = next(e for e in current.events if e["event"] == "top_creature_selection_resolved")
    entered_ids = {item["battlefield_id"] for item in event["selected"]}
    assert len(offered) == 2
    assert all(entered_ids <= set(candidates) for candidates in offered)
    assert all(
        any(
            log["event"] == "zone_changed"
            and log.get("reason") == "top_creature_selection_entry"
            and log["destination_object_id"] == item
            for log in current.events
        )
        for item in entered_ids
    )
    current.check_invariants()
