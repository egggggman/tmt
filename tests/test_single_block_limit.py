"""A static one-block limit affects self or controlled creatures of a subtype."""

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
ROCKSTEADY = load_facts(
    load_card_data(CATALOG, CATALOG.with_suffix(".manifest.json")),
    {"Rocksteady, Crash Courser"},
)["Rocksteady, Crash Courser"]
LAND = CardFact("Plains", "", 0, "Basic Land — Plains")
BOAR = CardFact("Wild Boar", "{2}", 2, "Creature — Boar", power=4, toughness=4)
RHINO = CardFact("Wild Rhino", "{2}", 2, "Creature — Rhino", power=4, toughness=4)
BLOCKER = CardFact("Guard", "{1}", 1, "Creature — Soldier", power=2, toughness=2)
GRANT = CardFact(
    "Boar Standard",
    "{1}",
    1,
    "Enchantment",
    "Boars you control can't be blocked by more than one creature.",
)


def setup(source=ROCKSTEADY, attacker=BOAR, *, seed=9):
    game = Game(([LAND] * 35, [LAND] * 35), seed=seed)
    game.begin_turn()
    standing = game.create_permanent(source, 0, summoning_sick=attacker is not None)
    attacking = (
        standing if attacker is None else game.create_permanent(attacker, 0, summoning_sick=False)
    )
    blockers = [game.create_permanent(BLOCKER, 1) for _ in range(2)]
    game.advance_to(TurnStep.DECLARE_ATTACKERS)
    attack = next(
        option
        for option in game.legal_attack_options(0)
        if option.attacker_ids == (attacking.object_id,)
    )
    game.execute_attack_action(attack)
    return game, standing, attacking, blockers, attack


def options(game, attack):
    return game.legal_block_options(attack, 1)


def test_complete_parser_is_generic_and_rejects_partial_or_unrelated_text():
    interp = CardInterpreter()
    self_clause, team_clause = interp.fragments(ROCKSTEADY)[:2]
    assert interp.single_block_limit(ROCKSTEADY, self_clause) == "self"
    assert interp.single_block_limit(ROCKSTEADY, team_clause) == "Boar"
    renamed = replace(
        ROCKSTEADY,
        name="Anonymous Rhino",
        oracle_text=ROCKSTEADY.oracle_text.replace("Rocksteady", "Anonymous Rhino"),
    )
    assert interp.single_block_limit(renamed, interp.fragments(renamed)[0]) == "self"
    assert interp.single_block_limit(GRANT, GRANT.oracle_text) == "Boar"
    assert (
        interp.single_block_limit(ROCKSTEADY, team_clause.replace("more than one", "two or more"))
        is None
    )


@pytest.mark.parametrize("source,attacker", [(ROCKSTEADY, BOAR), (ROCKSTEADY, None), (GRANT, BOAR)])
def test_single_block_legal_multi_block_illegal_and_damage_is_assigned(source, attacker):
    game, standing, creature, blockers, attack = setup(source, attacker)
    offered = options(game, attack)
    assert offered == options(game, attack)  # legal actions have no mutating side effects
    assert any(o.blocks == ((creature.object_id, blockers[0].object_id),) for o in offered)
    assert not any(len(o.blocks) > 1 for o in offered)
    with pytest.raises(ValueError, match="not currently legal"):
        game.execute_block_action(
            ActionOption(
                ActionKind.DECLARE_BLOCKERS,
                1,
                blocks=(
                    (creature.object_id, blockers[0].object_id),
                    (creature.object_id, blockers[1].object_id),
                ),
            )
        )
    single = next(o for o in offered if len(o.blocks) == 1)
    game.execute_block_action(single)
    proof = [e for e in game.events if e["event"] == "single_block_limit_applied"]
    assert len(proof) == 1
    assert proof[0]["source_id"] == standing.object_id
    assert proof[0]["attacker_id"] == creature.object_id and proof[0]["blockers"] == 1
    assert game.priority_state is None  # static effect does not create a trigger or payment
    evidence = game.resolve_combat_damage()
    assert len([a for a in evidence.assignments if a.source_id == creature.object_id]) == 1
    assert all(game._objects[b.object_id].zone == "former" for b in blockers[:1])
    game.check_invariants()


def test_non_boar_is_unaffected_and_self_restriction_respects_full_oracle():
    game, _, creature, blockers, attack = setup(attacker=RHINO)
    double = next(o for o in options(game, attack) if len(o.blocks) == 2)
    game.execute_block_action(double)
    assert not any(e["event"] == "single_block_limit_applied" for e in game.events)
    game.check_invariants()


def test_source_departure_control_change_and_type_change_recalculate_legality():
    game, source, creature, blockers, attack = setup()
    assert not any(len(o.blocks) == 2 for o in options(game, attack))
    game.change_controller(source, 1)
    assert any(len(o.blocks) == 2 for o in options(game, attack))
    game.change_controller(source, 0)
    creature.type_line_override = "Creature — Rhino"
    assert any(len(o.blocks) == 2 for o in options(game, attack))
    creature.type_line_override = "Creature — Boar"
    assert not any(len(o.blocks) == 2 for o in options(game, attack))
    game.put_into_graveyard(source, state_based_action="fixture_removal")
    double = next(o for o in options(game, attack) if len(o.blocks) == 2)
    game.execute_block_action(double)
    assert len(game._combat_blocks) == 2
    game.check_invariants()


def test_source_leaving_after_block_declaration_does_not_undo_the_block():
    game, source, creature, blockers, attack = setup()
    single = next(o for o in options(game, attack) if len(o.blocks) == 1)
    game.execute_block_action(single)
    game.put_into_graveyard(source, state_based_action="fixture_removal")
    assert game._combat_blocks == ((creature.object_id, blockers[0].object_id),)
    game.resolve_combat_damage()
    assert game.players[1].life == 20  # blocked attacker stays blocked
    assert blockers[0].zone == "former" and blockers[1].zone == "battlefield"
    game.check_invariants()


def test_ability_loss_removes_limit_and_reattachment_restores_it():
    game, source, _, _, attack = setup()
    assert not any(len(o.blocks) == 2 for o in options(game, attack))
    # The evaluated rules card supplies the source text: loss of abilities removes it.
    source.ability_loss_timestamp = (game.turn, len(game.events))
    assert any(len(o.blocks) == 2 for o in options(game, attack))
    source.ability_loss_timestamp = None
    assert not any(len(o.blocks) == 2 for o in options(game, attack))
    game.check_invariants()


def test_menace_and_one_block_limit_make_blocking_impossible():
    menace_boar = replace(BOAR, oracle_text="Menace", keywords=("Menace",))
    game, _, _, _, attack = setup(attacker=menace_boar)
    assert [o.blocks for o in options(game, attack)] == [()]
    game.execute_block_action(options(game, attack)[0])
    game.resolve_combat_damage()
    assert game.players[1].life == 16
    game.check_invariants()


def test_replay_has_same_block_options_events_and_outcome():
    def trace():
        game, _, _, _, attack = setup(seed=109)
        game.execute_block_action(next(o for o in options(game, attack) if o.blocks))
        game.resolve_combat_damage()
        game.check_invariants()
        return game.events

    assert trace() == trace()
