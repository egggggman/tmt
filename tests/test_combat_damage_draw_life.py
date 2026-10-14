"""Generic self combat-damage-to-player draw/life triggers."""

from dataclasses import replace
from pathlib import Path

import pytest

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import (
    ActionKind,
    ActionOption,
    CardFact,
    Game,
    TriggerEffect,
    TurnStep,
    load_facts,
)

ROOT = Path(__file__).resolve().parents[1]
LAND = CardFact("Plains", "", 0, "Basic Land — Plains")
FRAGMENT = "Whenever Herald deals combat damage to a player, you draw a card and lose 1 life."
HERALD = CardFact("Herald, Night Runner", "{2}{B}", 3, "Creature — Ninja", FRAGMENT, 2, 3)
GUARD = CardFact("Guard", "{1}", 1, "Creature", power=2, toughness=2)


def game(source=HERALD, *, library_size=30):
    current = Game(([LAND] * library_size, [LAND] * 30), seed=308)
    current.begin_turn()
    attacker = current.create_permanent(source, 0, summoning_sick=False)
    return current, attacker


def combat(current, attacker, blocker=None):
    current.advance_to(TurnStep.DECLARE_ATTACKERS)
    current.execute_attack_action(
        next(
            option
            for option in current.legal_attack_options(0)
            if option.attacker_ids == (attacker.object_id,)
        )
    )
    current.execute_block_action(
        ActionOption(
            ActionKind.DECLARE_BLOCKERS,
            1,
            blocks=((attacker.object_id, blocker.object_id),) if blocker else (),
        )
    )


def resolve(current):
    while current.priority_state is not None:
        if current.priority_state.resolution_pending:
            current.process_priority_resolution()
        else:
            current.execute_priority_action(
                current.legal_priority_actions(current.priority_state.player_index)[0]
            )


def test_frozen_oracle_and_renamed_variants_are_interpreted_without_name_dispatch():
    path = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
    frozen = load_facts(
        load_card_data(path, path.with_suffix(".manifest.json")),
        {"Oroku Saki, Shredder Rising"},
    )["Oroku Saki, Shredder Rising"]
    fragment = CardInterpreter.fragments(frozen)[1]
    interpreter = CardInterpreter()
    assert interpreter.combat_damage_draw_lose_life(frozen, fragment) == (1, 1)
    assert interpreter.combat_damage_draw_lose_life(HERALD, FRAGMENT) == (1, 1)
    renamed = replace(HERALD, name="Envoy", oracle_text=FRAGMENT.replace("Herald", "Envoy"))
    assert interpreter.combat_damage_draw_lose_life(renamed, renamed.oracle_text) == (1, 1)
    assert interpreter.combat_damage_draw_lose_life(
        replace(
            HERALD,
            oracle_text="Whenever this creature deals combat damage to a player, "
            "you draw 2 cards and lose 3 life.",
        ),
        "Whenever this creature deals combat damage to a player, you draw 2 cards and lose 3 life.",
    ) == (2, 3)
    assert interpreter.combat_damage_draw_lose_life(renamed, FRAGMENT) is None
    assert not interpreter.unsupported_fragments(frozen)


def test_unblocked_trigger_waits_for_priority_and_keeps_source_event_provenance():
    current, attacker = game()
    combat(current, attacker)
    before = len(current.players[0].hand)
    current.resolve_combat_damage()
    ability = current.stack[-1]
    assert ability.effect is TriggerEffect.COMBAT_DAMAGE_DRAW_LOSE_LIFE
    assert ability.source_id == attacker.object_id
    assert (len(current.players[0].hand), current.players[0].life) == (before, 20)
    with pytest.raises(ValueError, match="before all players pass"):
        current.resolve_top_of_stack()
    resolve(current)
    evidence = [e for e in current.events if e["event"] == "combat_draw_life_resolved"]
    assert len(evidence) == 1
    assert evidence[0]["event_id"] == ability.event.event_id
    assert evidence[0]["source_id"] == attacker.object_id
    assert evidence[0]["drawn_count"] == 1 and evidence[0]["life_lost"] == 1
    assert (len(current.players[0].hand), current.players[0].life) == (before + 1, 19)
    assert current.players[1].life == 18
    current.check_invariants()


def test_blocking_suppresses_player_trigger_and_strike_steps_are_independent():
    current, attacker = game()
    blocker = current.create_permanent(GUARD, 1)
    combat(current, attacker, blocker)
    current.resolve_combat_damage()
    assert not current.stack
    assert current.players[0].life == 20

    source = replace(HERALD, oracle_text="Double strike\n" + FRAGMENT, keywords=("Double strike",))
    current, attacker = game(source)
    combat(current, attacker)
    current.resolve_combat_damage()
    resolve(current)
    current.resolve_combat_damage()
    resolve(current)
    evidence = [e for e in current.events if e["event"] == "combat_draw_life_resolved"]
    assert len(evidence) == 2 and evidence[0]["event_id"] != evidence[1]["event_id"]
    assert current.players[0].life == 18 and current.players[1].life == 16
    current.check_invariants()


def test_trigger_survives_source_departure_and_replay_is_identical():
    def run():
        current, attacker = game()
        combat(current, attacker)
        current.resolve_combat_damage()
        current.move_object(attacker, "graveyard", reason="response")
        resolve(current)
        current.check_invariants()
        return current.snapshot(), current.events

    first, second = run(), run()
    assert first == second
    assert any(e["event"] == "combat_draw_life_resolved" for e in first[1])


def test_empty_library_still_loses_life_then_state_based_draw_loss():
    current, attacker = game(library_size=7)
    assert not current.players[0].library
    combat(current, attacker)
    current.resolve_combat_damage()
    resolve(current)
    evidence = [e for e in current.events if e["event"] == "combat_draw_life_resolved"]
    assert len(evidence) == 1
    assert evidence[0]["drawn_count"] == 0
    assert evidence[0]["failed_draw_pending"] is True
    assert evidence[0]["life_after"] == 19
    assert current.winner == 1
