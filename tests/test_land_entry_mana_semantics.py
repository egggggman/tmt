"""Printed land entry and selectable mana execute from general permanent semantics."""

from dataclasses import replace
from pathlib import Path

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import ActionKind, CardFact, Game, TriggerEffect, load_facts

ROOT = Path(__file__).resolve().parents[1]
ORACLE = "This land enters tapped.\nWhen this land enters, you gain 1 life.\n{T}: Add {B} or {G}."
DUAL = CardFact("Anonymous Business", "", 0, "Land", ORACLE)
SWAMP = CardFact("Swamp", "", 0, "Basic Land — Swamp")
FOREST = CardFact("Forest", "", 0, "Basic Land — Forest")
BLACK = CardFact("Black Bear", "{B}", 1, "Creature — Bear", power=1, toughness=1)
GREEN = CardFact("Green Bear", "{G}", 1, "Creature — Bear", power=1, toughness=1)
TWO = CardFact("Mixed Bear", "{B}{G}", 2, "Creature — Bear", power=2, toughness=2)


def setup(seed=2898):
    current = Game(([SWAMP] * 30, [FOREST] * 30), seed=seed)
    current.begin_turn()
    return current


def frozen_land():
    catalog = load_card_data(
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json",
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json",
    )
    return load_facts(catalog, {"Illegitimate Business"})["Illegitimate Business"]


def resolve_priority(current):
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


def test_frozen_and_renamed_land_interpret_same_entry_and_mana_clauses():
    interpreter = CardInterpreter()
    for land in (frozen_land(), DUAL, replace(DUAL, name="Another Business")):
        assert land.oracle_text == ORACLE
        assert interpreter.enters_tapped_semantics(land)
        gain = interpreter.etb_self_life_gain_semantics(
            land, "When this land enters, you gain 1 life."
        )
        assert gain is not None and gain[0] == 1 and gain[1].fully_supported
        assert not interpreter.unsupported_fragments(land)


def test_play_land_enters_tapped_then_triggers_life_gain_exactly_once():
    current = setup()
    card = current.set_hand_for_testing(0, [frozen_land()])[0]
    before = current.players[0].life
    assert current.play_land(0, card)
    permanent = current.players[0].battlefield[0]
    assert permanent.tapped and current.players[0].life == before
    resolve_priority(current)
    assert current.players[0].life == before + 1
    assert sum(event["event"] == "etb_life_gain_resolved" for event in current.events) == 1
    assert sum(event["event"] == "trigger_stacked" for event in current.events) == 1
    assert current.payment_plan(0, current.set_hand_for_testing(0, [BLACK])[0]) is None
    current.check_invariants()


def test_black_green_choice_and_source_allocation_are_independent_of_land_order():
    for spell in (BLACK, GREEN):
        current = setup()
        dual = current.create_permanent(DUAL, 0, summoning_sick=False)
        card = current.set_hand_for_testing(0, [spell])[0]
        assert current.payment_plan(0, card).source_ids == (dual.object_id,)
        assert current.announce_spell(0, card) is not None and dual.tapped
        current.resolve_top_of_stack()
        current.check_invariants()

    current = setup()
    dual = current.create_permanent(DUAL, 0, summoning_sick=False)
    swamp = current.create_permanent(SWAMP, 0, summoning_sick=False)
    card = current.set_hand_for_testing(0, [TWO])[0]
    plan = current.payment_plan(0, card)
    assert plan is not None and plan.source_ids == (swamp.object_id, dual.object_id)
    assert current.announce_spell(0, card) is not None
    assert dual.tapped and swamp.tapped


def test_land_life_trigger_uses_entry_event_even_after_source_leaves():
    current = setup()
    card = current.set_hand_for_testing(0, [DUAL])[0]
    land = current.move_object(card, "battlefield", controller=0)
    current._process_creature_entered_triggers(
        land, effects={TriggerEffect.ETB_SELF_LIFE_GAIN}, defer_triggers=True
    )
    assert len(current.stack) == 1 and current.players[0].life == 20
    current.move_object(land, "graveyard", reason="test_source_left")
    current._begin_priority_window()
    resolve_priority(current)
    assert current.players[0].life == 21
    current.check_invariants()


def test_frozen_land_entry_and_dual_payment_replay_exactly():
    def run():
        current = setup()
        card = current.set_hand_for_testing(0, [frozen_land()])[0]
        current.play_land(0, card)
        resolve_priority(current)
        land = current.players[0].battlefield[0]
        current.untap_permanent(land)
        spell = current.set_hand_for_testing(0, [GREEN])[0]
        assert current.announce_spell(0, spell) is not None
        current.resolve_top_of_stack()
        current.check_invariants()
        return current.snapshot(), current.events

    assert run() == run()
