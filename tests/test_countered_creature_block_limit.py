"""Continuous one-block restriction for controlled creatures with counters."""

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
    TurnStep,
    load_facts,
)

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
FACTS = load_facts(
    load_card_data(CATALOG, CATALOG.with_suffix(".manifest.json")),
    {"Michelangelo, Mutant BFF", "Bebop, Warthog Warrior", "Rocksteady, Crash Courser"},
)
SOURCE = FACTS["Michelangelo, Mutant BFF"]
BEBOP = FACTS["Bebop, Warthog Warrior"]
ROCKSTEADY = FACTS["Rocksteady, Crash Courser"]
FRAGMENT = (
    "Each creature you control with a counter on it can't be blocked by more than one creature."
)
LAND = CardFact("Forest", "", 0, "Basic Land — Forest")
CREATURE = CardFact("Anonymous Attacker", "{2}{G}", 3, "Creature — Mutant", power=4, toughness=4)
RHINO = replace(CREATURE, name="Anonymous Rhino", type_line="Creature — Rhino")
GUARD = CardFact("Anonymous Guard", "{1}{W}", 2, "Creature — Soldier", power=2, toughness=2)
BOAR = replace(CREATURE, name="Anonymous Boar", type_line="Creature — Boar")


def setup(*, seed=346, source=SOURCE, attacker=CREATURE, counter_type="+1/+1"):
    game = Game(([LAND] * 40, [LAND] * 40), seed=seed)
    game.begin_turn()
    standing = game.create_permanent(source, 0)
    creature = game.create_permanent(attacker, 0, summoning_sick=False)
    if counter_type:
        game.place_counters(
            creature,
            counter_type,
            1,
            source_card="Fixture counter source",
            oracle_fragment="Put a counter on target creature.",
        )
    guards = [game.create_permanent(GUARD, 1) for _ in range(2)]
    game.advance_to(TurnStep.DECLARE_ATTACKERS)
    attack = next(
        option
        for option in game.legal_attack_options(0)
        if option.attacker_ids == (creature.object_id,)
    )
    game.execute_attack_action(attack)
    return game, standing, creature, guards, attack


def options(game, attack):
    return game.legal_block_options(attack, 1)


def test_frozen_clause_parser_and_incomplete_variants_fail_closed():
    interpreter = CardInterpreter()
    assert FRAGMENT in interpreter.fragments(SOURCE)
    assert interpreter.single_block_limit(SOURCE, FRAGMENT) == "controlled_with_counter"
    assert FRAGMENT not in dict(interpreter.unsupported_fragments(SOURCE))
    renamed = replace(SOURCE, name="Anonymous Team Leader", oracle_text=FRAGMENT)
    assert interpreter.single_block_limit(renamed, FRAGMENT) == "controlled_with_counter"
    for text in (
        "Each creature you control can't be blocked by more than one creature.",
        "Each creature you control with a counter on it can't be blocked.",
        "Each creature with a counter on it can't be blocked by more than one creature.",
    ):
        assert interpreter.single_block_limit(renamed, text) is None
    assert interpreter.single_block_limit(replace(renamed, type_line="Sorcery"), FRAGMENT) is None


@pytest.mark.parametrize("counter_type", ["+1/+1", "stun", "finality"])
def test_any_current_counter_limits_blocks_and_proves_source(counter_type):
    game, standing, creature, guards, attack = setup(counter_type=counter_type)
    offered = options(game, attack)
    assert offered == options(game, attack)
    assert any(len(option.blocks) == 1 for option in offered)
    assert not any(len(option.blocks) == 2 for option in offered)
    with pytest.raises(ValueError, match="not currently legal"):
        game.execute_block_action(
            ActionOption(
                ActionKind.DECLARE_BLOCKERS,
                1,
                blocks=(
                    (creature.object_id, guards[0].object_id),
                    (creature.object_id, guards[1].object_id),
                ),
            )
        )
    game.execute_block_action(next(option for option in offered if len(option.blocks) == 1))
    evidence = [event for event in game.events if event["event"] == "single_block_limit_applied"]
    assert len(evidence) == 1
    assert evidence[0]["source_id"] == standing.object_id
    assert evidence[0]["attacker_id"] == creature.object_id
    assert evidence[0]["oracle_fragment"] == FRAGMENT
    game.resolve_combat_damage()
    game.check_invariants()


def test_live_counter_controller_creature_status_and_source_recalculate():
    game, standing, creature, _guards, attack = setup(counter_type=None)
    assert any(len(option.blocks) == 2 for option in options(game, attack))
    creature.counters["+1/+1"] = 1
    assert not any(len(option.blocks) == 2 for option in options(game, attack))
    creature.counters["+1/+1"] = 0
    assert any(len(option.blocks) == 2 for option in options(game, attack))
    creature.counters.pop("+1/+1")
    game.place_counters(creature, "+1/+1", 1, source_card="Fixture", oracle_fragment="Fixture")
    game.change_controller(standing, 1)
    assert any(len(option.blocks) == 2 for option in options(game, attack))
    game.change_controller(standing, 0)
    assert not any(len(option.blocks) == 2 for option in options(game, attack))
    creature.type_line_override = "Artifact"
    assert game._single_block_limit_sources(creature) == ()
    creature.type_line_override = None
    assert not any(len(option.blocks) == 2 for option in options(game, attack))
    game.move_object(standing, "graveyard", reason="fixture_departure")
    assert any(len(option.blocks) == 2 for option in options(game, attack))
    game.check_invariants()


def test_source_ability_loss_removes_limit_but_recipient_loss_does_not():
    game, standing, creature, _guards, attack = setup()
    creature.ability_loss_timestamp = (game.turn, len(game.events))
    assert not any(len(option.blocks) == 2 for option in options(game, attack))
    standing.ability_loss_timestamp = (game.turn, len(game.events))
    assert any(len(option.blocks) == 2 for option in options(game, attack))
    standing.ability_loss_timestamp = None
    assert not any(len(option.blocks) == 2 for option in options(game, attack))
    game.check_invariants()


def test_menace_combines_with_live_counter_limit_and_source_departure():
    menace_creature = replace(
        CREATURE, name="Anonymous Menace", oracle_text="Menace", keywords=("Menace",)
    )
    game, source, creature, _guards, attack = setup(attacker=menace_creature)
    assert [option.blocks for option in options(game, attack)] == [()]
    game.move_object(source, "graveyard", reason="fixture_departure")
    assert any(len(option.blocks) == 2 for option in options(game, attack))
    assert not any(len(option.blocks) == 1 for option in options(game, attack))
    game.execute_block_action(
        next(option for option in options(game, attack) if len(option.blocks) == 2)
    )
    game.resolve_combat_damage()
    game.check_invariants()


def test_frozen_rhino_menace_and_rocksteady_limit_compose():
    game, _standing, creature, _guards, attack = setup(attacker=RHINO)
    bebop = game.create_permanent(BEBOP, 0)
    assert game._has_menace(creature)
    assert [option.blocks for option in options(game, attack)] == [()]
    game.move_object(bebop, "graveyard", reason="fixture_departure")
    assert any(len(option.blocks) == 1 for option in options(game, attack))
    game.execute_block_action(
        next(option for option in options(game, attack) if len(option.blocks) == 1)
    )
    game.check_invariants()
    # The earlier frozen self/team limit remains independent of this new source.
    other, _source, rocksteady, _guards, other_attack = setup(source=ROCKSTEADY, attacker=BOAR)
    assert not any(len(option.blocks) == 2 for option in options(other, other_attack))
    other.check_invariants()


def test_replay_with_counter_changes_and_block_declaration_is_exact():
    def run():
        game, source, creature, _guards, attack = setup(seed=348)
        creature.counters.clear()
        assert any(len(option.blocks) == 2 for option in options(game, attack))
        game.place_counters(creature, "+1/+1", 1, source_card="Fixture", oracle_fragment="Fixture")
        assert not any(len(option.blocks) == 2 for option in options(game, attack))
        game.execute_block_action(next(option for option in options(game, attack) if option.blocks))
        game.move_object(source, "graveyard", reason="fixture_after_declaration")
        game.resolve_combat_damage()
        game.check_invariants()
        return game.snapshot(), game.events, game.rng.records

    assert run() == run()
