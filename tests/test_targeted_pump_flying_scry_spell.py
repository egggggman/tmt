"""Oracle-derived Hamato-style temporary pump, flying, and Scry spell."""

from dataclasses import replace
from pathlib import Path

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter, CastKind
from tmnt_design_studio.engine07 import ActionKind, CardFact, Game, load_facts

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
FACTS = load_facts(
    load_card_data(CATALOG, CATALOG.with_suffix(".manifest.json")),
    {"Hamato Guardian Stance"},
)
STANCE = FACTS["Hamato Guardian Stance"]
ISLAND = CardFact("Plains", "", 0, "Basic Land — Plains")
BEAR = CardFact("Quiet Bear", "{1}{G}", 2, "Creature — Bear", power=2, toughness=2)


def game():
    current = Game(([ISLAND] * 30, [ISLAND] * 30), seed=901)
    current.begin_turn()
    for _ in range(1):
        current.create_permanent(ISLAND, 0)
    card = current.set_hand_for_testing(0, [STANCE])[0]
    target = current.create_permanent(BEAR, 0)
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


def test_parser_is_generic_and_fails_closed_on_compound_neighbors():
    interpreter = CardInterpreter()
    assert interpreter.cast_program(STANCE).kind is CastKind.TARGETED_PUMP_FLYING_SCRY
    assert interpreter.targeted_pump_flying_scry_program(STANCE) is not None
    assert interpreter.unsupported_fragments(STANCE) == ()
    for text in (
        STANCE.oracle_text.replace("Scry 1", "Draw a card"),
        STANCE.oracle_text.replace("flying", "hexproof"),
        STANCE.oracle_text + "\nGain 1 life.",
    ):
        changed = replace(STANCE, oracle_text=text)
        assert interpreter.targeted_pump_flying_scry_program(changed) is None
        assert interpreter.cast_program(changed).kind is CastKind.UNSUPPORTED


def test_paid_spell_grants_temporary_pump_flying_and_authoritative_scry():
    current, card, target = game()
    actions = [a for a in current.legal_main_actions(0) if a.object_id == card.object_id]
    assert {a.target_id for a in actions} == {target.object_id}
    spell = current.announce_spell(0, card, target)
    assert spell is not None
    current.resolve_top_of_stack()
    assert (target.power, target.toughness) == (3, 5)
    assert current._has_flying(target)
    assert any(e["event"] == "scry_committed" for e in current.events)
    assert any(e["event"] == "targeted_pump_flying_scry_resolved" for e in current.events)
    current.end_turn()
    assert (target.power, target.toughness) == (2, 2)
    assert not current._has_flying(target)
    current.check_invariants()


def test_departed_target_fizzles_without_scry_or_partial_effect():
    current, card, target = game()
    spell = current.announce_spell(0, card, target)
    assert spell is not None
    current.move_object(target, "graveyard", reason="target_departed")
    current.resolve_top_of_stack()
    assert not any(e["event"] == "scry_committed" for e in current.events)
    assert any(e["event"] == "spell_resolved_no_effect" for e in current.events)
    current.check_invariants()
