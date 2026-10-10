"""Deathtouch follows the damage source and survives source or keyword changes."""

from dataclasses import replace
from pathlib import Path

import pytest

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import DamageTargetKind
from tmnt_design_studio.engine07 import (
    ActionKind,
    ActionOption,
    CardFact,
    DamageTransaction,
    Game,
    TemporaryKeyword,
    TemporaryKeywordEffect,
    TurnStep,
    load_facts,
)

LAND = CardFact("Plains", "", 0, "Basic Land — Plains")
TOUCH = CardFact(
    "Venomous Scout", "{B}", 1, "Creature — Scout", "Deathtouch", 1, 2, ("Deathtouch",)
)
BEAR = CardFact("Durable Bear", "{2}", 2, "Creature — Bear", power=2, toughness=4)
TRAMPLE_TOUCH = replace(
    TOUCH,
    name="Venomous Charger",
    oracle_text="Deathtouch\nTrample",
    power=4,
    keywords=("Deathtouch", "Trample"),
)
ROOT = Path(__file__).resolve().parents[1]


def game(seed=2891):
    current = Game(([LAND] * 30, [LAND] * 30), seed=seed)
    current.begin_turn()
    return current


def combat(current, attacker, blockers=()):
    current.advance_to(TurnStep.DECLARE_ATTACKERS)
    attack = next(
        option
        for option in current.legal_attack_options(0)
        if option.attacker_ids == (attacker.object_id,)
    )
    current.execute_attack_action(attack)
    current.execute_block_action(
        ActionOption(
            ActionKind.DECLARE_BLOCKERS,
            1,
            blocks=tuple((attacker.object_id, blocker.object_id) for blocker in blockers),
        )
    )


def test_printed_deathtouch_kills_larger_blocker_on_one_damage():
    current = game()
    attacker = current.create_permanent(TOUCH, 0, summoning_sick=False)
    blocker = current.create_permanent(BEAR, 1)
    combat(current, attacker, (blocker,))
    evidence = current.resolve_combat_damage()
    assert any(
        item.target_id == blocker.object_id and item.amount == 1 for item in evidence.assignments
    )
    assert blocker.zone == "former"
    assert blocker.object_id in evidence.removed_before_next_step
    current.check_invariants()


@pytest.mark.parametrize(
    "name", ("Squirrelanoids", "Frog Butler", "Putrid Pals", "Shredder, Unrelenting")
)
def test_frozen_printed_sources_execute_the_same_lethal_rule(name):
    catalog = load_card_data(
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json",
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json",
    )
    fact = load_facts(catalog, {name})[name]
    current = game()
    source = current.create_permanent(fact, 0, summoning_sick=False)
    target = current.create_permanent(replace(BEAR, toughness=20), 1)
    assert current.evaluated_deathtouch(source)
    current.deal_damage(
        DamageTransaction(0, source, DamageTargetKind.CREATURE, 1, "Deal 1 damage.", target)
    )
    assert target.zone == "former"


def test_deathtouch_trample_assigns_one_then_three_to_player():
    current = game()
    attacker = current.create_permanent(TRAMPLE_TOUCH, 0, summoning_sick=False)
    blocker = current.create_permanent(BEAR, 1)
    combat(current, attacker, (blocker,))
    evidence = current.resolve_combat_damage()
    assert [(item.target_id, item.target_player, item.amount) for item in evidence.assignments] == [
        (blocker.object_id, None, 1),
        (None, 1, 3),
        (attacker.object_id, None, 2),
    ]
    assert evidence.trample_results[0].source_deathtouch
    assert evidence.trample_results[0].lethal_required == 1
    assert blocker.zone == "former" and current.players[1].life == 17


def test_temporary_deathtouch_stops_after_cleanup_but_prior_damage_is_lethal():
    current = game()
    source = current.create_permanent(BEAR, 0, summoning_sick=False)
    blocker = current.create_permanent(BEAR, 1)
    source.temporary_keyword_effects.append(
        TemporaryKeywordEffect(
            TemporaryKeyword.DEATHTOUCH,
            "until_end_of_turn",
            source.object_id,
            "Target creature gains deathtouch until end of turn.",
            timestamp=current._effect_timestamp(),
        )
    )
    assert current.evaluated_deathtouch(source)
    combat(current, source, (blocker,))
    current.resolve_combat_damage()
    assert blocker.zone == "former"
    current._perform_cleanup()
    assert source.zone == "battlefield" and not current.evaluated_deathtouch(source)


def test_renamed_source_without_keyword_does_not_kill_after_one_damage():
    current = game()
    ordinary = replace(TOUCH, name="Ordinary Scout", oracle_text="", keywords=())
    attacker = current.create_permanent(ordinary, 0, summoning_sick=False)
    blocker = current.create_permanent(BEAR, 1)
    combat(current, attacker, (blocker,))
    current.resolve_combat_damage()
    assert blocker.zone == "battlefield" and blocker.damage == 1
    assert not blocker.deathtouch_damage


def test_zero_toughness_still_leaves_without_damage():
    current = game()
    zero = replace(BEAR, name="Fragile Bear", toughness=0)
    permanent = current.create_permanent(zero, 0)
    current.check_state_based_actions()
    assert permanent.zone == "former"


def test_noncombat_deathtouch_marker_survives_source_departure_before_sba():
    current = game()
    source = current.create_permanent(TOUCH, 0)
    target = current.create_permanent(BEAR, 1)
    current.deal_damage(
        DamageTransaction(0, source, DamageTargetKind.CREATURE, 1, "Deal 1 damage.", target),
        defer_post_damage=True,
    )
    assert target.zone == "battlefield" and target.deathtouch_damage
    current.put_into_graveyard(source)
    current.check_state_based_actions()
    assert target.zone == "former"


def test_replay_same_seed_preserves_deathtouch_result_and_events():
    def run():
        current = game(2892)
        attacker = current.create_permanent(TRAMPLE_TOUCH, 0, summoning_sick=False)
        blocker = current.create_permanent(BEAR, 1)
        combat(current, attacker, (blocker,))
        current.resolve_combat_damage()
        return current.snapshot(), current.events

    assert run() == run()
