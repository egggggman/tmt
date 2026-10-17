"""Generic controlled-subtype continuous keyword grants in combat."""

from dataclasses import replace
from pathlib import Path

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter
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
FACTS = load_facts(
    load_card_data(CATALOG, CATALOG.with_suffix(".manifest.json")),
    {"Bebop, Warthog Warrior", "Rocksteady, Crash Courser", "Retro-Mutation"},
)
BEBOP = FACTS["Bebop, Warthog Warrior"]
ROCKSTEADY = FACTS["Rocksteady, Crash Courser"]
AURA = FACTS["Retro-Mutation"]
RHINO_AURA = CardFact(
    "Rhino Silence",
    "{1}{B}",
    2,
    "Enchantment — Aura",
    "Enchant creature\nEnchanted creature is a Rhino with base power and toughness "
    "0/1. It can't attack and loses all abilities. (It also loses all other creature types.)",
)
SWAMP = CardFact("Swamp", "", 0, "Basic Land — Swamp")
RHINO = CardFact("Quiet Rhino", "{2}{B}", 3, "Creature — Rhino", power=3, toughness=3)
BEAR = CardFact("Quiet Bear", "{1}{G}", 2, "Creature — Bear", power=2, toughness=2)
GRANT = "Rhinos you control have menace."


def game(seed=344):
    current = Game(([SWAMP] * 40, [SWAMP] * 40), seed=seed)
    current.begin_turn()
    return current


def enter(current, card, controller, *, sick=False):
    return current.create_permanent(card, controller, summoning_sick=sick)


def declare(current, attacker):
    current.advance_to(TurnStep.DECLARE_ATTACKERS)
    option = next(
        choice
        for choice in current.legal_attack_options(0)
        if choice.attacker_ids == (attacker.object_id,)
    )
    current.execute_attack_action(option)
    return option


def test_frozen_clause_generic_parser_and_fail_closed_neighbors():
    interpreter = CardInterpreter()
    assert GRANT in interpreter.fragments(BEBOP)
    for card in (BEBOP, replace(BEBOP, name="Unrelated Warrior")):
        program = interpreter.static_subtype_keyword_grant(card, GRANT)
        assert program is not None
        assert (program.creature_subtype, program.keyword) == ("Rhino", "menace")
        assert GRANT not in dict(interpreter.unsupported_fragments(card))
    for card, fragment in (
        (BEBOP, "Ponies you control have menace."),
        (BEBOP, "Rhinos you control have flying."),
        (BEBOP, "Other Rhinos you control have menace."),
        (replace(BEBOP, type_line="Instant"), GRANT),
    ):
        assert interpreter.static_subtype_keyword_grant(card, fragment) is None


def test_controller_subtype_source_departure_and_control_recalculate():
    current = game()
    source = enter(current, BEBOP, 0)
    own = enter(current, RHINO, 0)
    enemy = enter(current, RHINO, 1)
    bear = enter(current, BEAR, 0)
    assert current._has_menace(own)
    assert not current._has_menace(enemy) and not current._has_menace(bear)

    own.type_line_override = "Creature — Bear"
    assert not current._has_menace(own)
    own.type_line_override = "Creature — Rhino"
    assert current._has_menace(own)

    current.change_controller(source, 1)
    assert not current._has_menace(own) and current._has_menace(enemy)
    current.change_controller(source, 0)
    assert current._has_menace(own) and not current._has_menace(enemy)
    current.move_object(source, "graveyard", reason="test_source_departure")
    assert not current._has_menace(own)
    current.check_invariants()


def test_source_and_recipient_ability_loss_use_layer_six_timestamps():
    current = game(seed=345)
    source = enter(current, BEBOP, 0)
    rhino = enter(current, RHINO, 0)
    assert current._has_menace(rhino)

    source_aura = enter(current, AURA, 1)
    current.attach_aura(source_aura, source)
    assert not current._has_menace(rhino)
    current.move_object(source_aura, "graveyard", reason="test_source_restored")
    assert current._has_menace(rhino)

    target_aura = enter(current, RHINO_AURA, 1)
    current.attach_aura(target_aura, rhino)
    assert not current._has_menace(rhino)
    later_source = enter(current, replace(BEBOP, name="Later Warrior"), 0)
    assert later_source.entered_timestamp > rhino.ability_loss_timestamp
    assert current._has_menace(rhino)
    current.move_object(later_source, "graveyard", reason="test_later_source_departure")
    assert not current._has_menace(rhino)
    current.move_object(target_aura, "graveyard", reason="test_target_restored")
    assert current._has_menace(rhino)


def test_granted_menace_requires_two_blockers_and_records_selected_use():
    current = game(seed=346)
    source = enter(current, BEBOP, 0)
    source.tapped = True
    rhino = enter(current, RHINO, 0)
    first = enter(current, BEAR, 1)
    second = enter(current, BEAR, 1)
    attack = declare(current, rhino)
    options = current.legal_block_options(attack, 1)
    assert all(len(option.blocks) != 1 for option in options)
    two = next(option for option in options if len(option.blocks) == 2)
    assert {blocker for _attacker, blocker in two.blocks} == {
        first.object_id,
        second.object_id,
    }
    current.execute_block_action(two)
    uses = [e for e in current.events if e["event"] == "static_subtype_keyword_used"]
    assert len(uses) == 1
    assert uses[0]["attacker_id"] == rhino.object_id
    assert uses[0]["oracle_fragment"] == GRANT
    current.resolve_combat_damage()
    current.check_invariants()


def test_frozen_rocksteady_one_block_limit_plus_granted_menace_is_unblockable():
    current = game(seed=347)
    source = enter(current, BEBOP, 0)
    source.tapped = True
    rocksteady = enter(current, ROCKSTEADY, 0)
    enter(current, BEAR, 1)
    enter(current, BEAR, 1)
    attack = declare(current, rocksteady)
    options = current.legal_block_options(attack, 1)
    assert all(not option.blocks for option in options)
    current.execute_block_action(ActionOption(ActionKind.DECLARE_BLOCKERS, 1))
    current.resolve_combat_damage()
    assert current.players[1].life == 13


def test_replay_is_exact_across_source_exit_subtype_change_and_combat():
    def run():
        current = game(seed=348)
        source = enter(current, replace(BEBOP, name="Generic Grant Source"), 0)
        source.tapped = True
        rhino = enter(current, RHINO, 0)
        enter(current, BEAR, 1)
        enter(current, BEAR, 1)
        rhino.type_line_override = "Creature — Bear"
        assert not current._has_menace(rhino)
        rhino.type_line_override = "Creature — Rhino"
        attack = declare(current, rhino)
        assert all(len(option.blocks) != 1 for option in current.legal_block_options(attack, 1))
        current.execute_block_action(
            next(option for option in current.legal_block_options(attack, 1) if not option.blocks)
        )
        current.resolve_combat_damage()
        current.move_object(source, "graveyard", reason="test_source_departure")
        current.check_invariants()
        return current.snapshot(), current.events, current.rng.records

    assert run() == run()
