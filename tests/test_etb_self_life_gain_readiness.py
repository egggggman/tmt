"""Generic self-ETB life gain and the frozen Pachyderm's existing combat rules."""

import json
from dataclasses import replace
from pathlib import Path

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import (
    ActionKind,
    CardFact,
    Game,
    TurnStep,
    load_facts,
)
from tmnt_design_studio.semantic_coverage import SemanticCoverage

ROOT = Path(__file__).resolve().parents[1]
CATALOG = load_card_data(
    ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json",
    ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json",
)
PACHYDERM = load_facts(CATALOG, {"Primordial Pachyderm"})["Primordial Pachyderm"]
FOREST = CardFact("Forest", "", 0, "Basic Land — Forest")
SWAMP = CardFact("Swamp", "", 0, "Basic Land — Swamp")
FLYER = CardFact("Generic Flyer", "{1}{U}", 2, "Creature — Bird", "Flying", 2, 2, ("Flying",))
BEAR = CardFact("Generic Bear", "{1}{G}", 2, "Creature — Bear", "", 2, 2)


def game(seed=830):
    current = Game(([FOREST] * 60, [FOREST] * 60), seed=seed)
    current.begin_turn()
    return current


def resolve(current):
    while current.priority_state is not None:
        if current.priority_state.resolution_pending:
            current.process_priority_resolution()
        else:
            current.execute_priority_action(
                next(
                    option
                    for option in current.legal_priority_actions(
                        current.priority_state.player_index
                    )
                    if option.kind is ActionKind.PASS_PRIORITY
                )
            )


def test_frozen_card_data_and_generic_self_etb_grammar():
    assert (PACHYDERM.mana_cost, PACHYDERM.power, PACHYDERM.toughness) == (
        "{3}{G}",
        4,
        4,
    )
    assert PACHYDERM.type_line == "Creature — Elephant Avatar"
    assert PACHYDERM.oracle_text == "Reach, trample\nWhen this creature enters, you gain 2 life."
    interpreter = CardInterpreter()
    fragment = "When this creature enters, you gain 2 life."
    assert interpreter.etb_self_life_gain_semantics(PACHYDERM, fragment) == (
        2,
        SemanticCoverage(True, True, True, ()),
    )
    renamed = replace(PACHYDERM, name="Anonymous Elephant")
    assert interpreter.etb_self_life_gain_semantics(
        renamed, "When Anonymous Elephant enters, you gain 3 life."
    ) == (3, SemanticCoverage(True, True, True, ()))
    mismatch = interpreter.etb_self_life_gain_semantics(
        renamed, "When Other Elephant enters, you gain 3 life."
    )
    assert mismatch is not None and not mismatch[1].fully_supported
    assert (
        interpreter.etb_self_life_gain_semantics(
            renamed, "When this creature attacks, you gain 3 life."
        )
        is None
    )


def test_normal_casting_payment_four_four_and_exact_stack_life_gain_replay():
    def trace():
        current = game()
        for land in (FOREST, FOREST, FOREST, SWAMP):
            current.create_permanent(land, 0, summoning_sick=False)
        source = current.set_hand_for_testing(0, [PACHYDERM])[0]
        option = next(
            action
            for action in current.legal_main_actions(0)
            if action.kind is ActionKind.CAST and action.object_id == source.object_id
        )
        assert current.execute_main_action(option)
        assert sum(land.tapped for land in current.players[0].battlefield) == 4
        assert current.players[0].life == 20
        resolve(current)
        permanent = next(
            permanent
            for permanent in current.players[0].battlefield
            if permanent.card.name == PACHYDERM.name
        )
        assert (permanent.power, permanent.toughness) == (4, 4)
        assert current.players[0].life == 22
        assert current.players[1].life == 20
        pending = [
            e
            for e in current.events
            if e["event"] == "trigger_pending" and e.get("source") == PACHYDERM.name
        ]
        gains = [
            e
            for e in current.events
            if e["event"] == "life_gained" and e.get("source") == PACHYDERM.name
        ]
        resolved = [e for e in current.events if e["event"] == "etb_life_gain_resolved"]
        assert len(pending) == len(gains) == len(resolved) == 1
        assert gains[0]["amount"] == resolved[0]["amount"] == 2
        assert (resolved[0]["life_before"], resolved[0]["life_after"]) == (20, 22)
        assert resolved[0]["source_id"] == permanent.object_id
        assert resolved[0]["source_card"] == PACHYDERM.name
        current.check_invariants()
        return json.dumps(current.snapshot(), sort_keys=True)

    assert trace() == trace()
    unaffordable = game(seed=831)
    for _ in range(4):
        unaffordable.create_permanent(SWAMP, 0, summoning_sick=False)
    card = unaffordable.set_hand_for_testing(0, [PACHYDERM])[0]
    assert not any(
        action.kind is ActionKind.CAST and action.object_id == card.object_id
        for action in unaffordable.legal_main_actions(0)
    )


def test_permanent_reach_blocks_flying_and_trample_assigns_excess_damage():
    current = game(seed=832)
    flyer = current.create_permanent(FLYER, 0, summoning_sick=False)
    blocker = current.create_permanent(PACHYDERM, 1, summoning_sick=False)
    current._process_creature_entered_triggers(blocker)
    resolve(current)
    assert current.players[1].life == 22
    current.advance_to(TurnStep.DECLARE_ATTACKERS)
    attack = next(
        option
        for option in current.legal_attack_options(0)
        if option.attacker_ids == (flyer.object_id,)
    )
    current.execute_attack_action(attack)
    assert any(
        (flyer.object_id, blocker.object_id) in option.blocks
        for option in current.legal_block_options(attack, 1)
    )
    current.check_invariants()

    trampling = game(seed=833)
    attacker = trampling.create_permanent(PACHYDERM, 0, summoning_sick=False)
    defender = trampling.create_permanent(BEAR, 1, summoning_sick=False)
    trampling._process_creature_entered_triggers(attacker)
    resolve(trampling)
    trampling.advance_to(TurnStep.DECLARE_ATTACKERS)
    attack = next(
        option
        for option in trampling.legal_attack_options(0)
        if option.attacker_ids == (attacker.object_id,)
    )
    trampling.execute_attack_action(attack)
    trampling.execute_block_action(
        next(
            option
            for option in trampling.legal_block_options(attack, 1)
            if option.blocks == ((attacker.object_id, defender.object_id),)
        )
    )
    evidence = trampling.resolve_combat_damage()
    assert trampling.players[1].life == 18
    assert any(
        item.source_id == attacker.object_id and item.target_player == 1 and item.amount == 2
        for item in evidence.assignments
    )
    assert evidence.trample_results
    trampling.check_invariants()


def test_renamed_creature_gains_its_own_amount_not_card_specific():
    renamed = replace(
        PACHYDERM,
        name="Anonymous Elephant",
        oracle_text="Reach, trample\nWhen this creature enters, you gain 3 life.",
    )
    current = game(seed=834)
    source = current.create_permanent(renamed, 0)
    current._process_creature_entered_triggers(source)
    assert current.players[0].life == 20
    resolve(current)
    assert current.players[0].life == 23
    assert [e["amount"] for e in current.events if e["event"] == "etb_life_gain_resolved"] == [3]
    current.check_invariants()
