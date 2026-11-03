"""C1 coverage for generic single-block combat restrictions."""

import pytest

from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import ActionKind, ActionOption, CardFact, Game, TurnStep

LAND = CardFact("Forest", "", 0, "Basic Land — Forest")
BEAR = CardFact("Bear", "{1}", 1, "Creature — Bear", power=2, toughness=2)
BOAR = CardFact("Boar", "{2}", 2, "Creature — Boar", power=3, toughness=3)
ROCKSTEADY = CardFact(
    "Rocksteady, Crash Courser",
    "{4}{G}{G}",
    6,
    "Creature — Boar Mutant Warrior",
    "Rocksteady can't be blocked by more than one creature.",
    power=5,
    toughness=5,
)
BOAR_GRANT = CardFact(
    "Boar restriction source",
    "{3}{G}",
    4,
    "Creature — Mutant",
    "Boars you control can't be blocked by more than one creature.",
    power=2,
    toughness=2,
)


def declared_attack(game: Game, attackers, *, include_all=False):
    game.advance_to(TurnStep.DECLARE_ATTACKERS)
    option = next(
        item
        for item in game.legal_attack_options(0)
        if item.attacker_ids
        and (
            item.attacker_ids == tuple(permanent.object_id for permanent in attackers)
            or (
                include_all
                and all(permanent.object_id in item.attacker_ids for permanent in attackers)
            )
        )
    )
    game.execute_attack_action(option)
    return option


def test_direct_restriction_allows_zero_or_one_but_rejects_two_blockers():
    game = Game(([LAND] * 20, [LAND] * 20), seed=12001)
    game.begin_turn()
    attacker = game.create_permanent(ROCKSTEADY, 0, summoning_sick=False)
    first = game.create_permanent(BEAR, 1, summoning_sick=False)
    second = game.create_permanent(BEAR, 1, summoning_sick=False)
    attack = declared_attack(game, [attacker])
    options = game.legal_block_options(attack, 1)
    assert any(option.blocks == ((attacker.object_id, first.object_id),) for option in options)
    assert all(len(option.blocks) < 2 for option in options)
    illegal = ActionOption(
        ActionKind.DECLARE_BLOCKERS,
        1,
        blocks=((attacker.object_id, first.object_id), (attacker.object_id, second.object_id)),
    )
    with pytest.raises(ValueError, match="currently legal"):
        game.execute_block_action(illegal)


def test_interpreter_coverage_is_generic_for_direct_and_quality_clauses():
    interpreter = CardInterpreter()
    assert interpreter.unsupported_fragments(ROCKSTEADY) == ()
    assert interpreter.unsupported_fragments(BOAR_GRANT) == ()


def test_quality_restriction_tracks_controller_and_source_departure():
    game = Game(([LAND] * 20, [LAND] * 20), seed=12002)
    game.begin_turn()
    source = game.create_permanent(BOAR_GRANT, 0, summoning_sick=False)
    attacker = game.create_permanent(BOAR, 0, summoning_sick=False)
    blockers = [game.create_permanent(BEAR, 1, summoning_sick=False) for _ in range(2)]
    attack = declared_attack(game, [attacker], include_all=True)
    assert all(
        sum(attacker_id == attacker.object_id for attacker_id, _ in option.blocks) < 2
        for option in game.legal_block_options(attack, 1)
    )

    # The continuous restriction follows the source's controller and disappears
    # when the source leaves the battlefield; one blocker is then legal.
    game.move_object(source, "graveyard", reason="c1_source_departure")
    options = game.legal_block_options(attack, 1)
    assert any(len(option.blocks) == 1 for option in options)
    game.execute_block_action(
        next(
            option
            for option in options
            if option.blocks == ((attacker.object_id, blockers[0].object_id),)
        )
    )
    evidence = game.resolve_combat_damage()
    assert any(item.target_player == 0 for item in evidence.assignments) is False


def test_quality_restriction_stops_following_control_change_and_is_deterministic():
    def observe(seed):
        game = Game(([LAND] * 20, [LAND] * 20), seed=seed)
        game.begin_turn()
        source = game.create_permanent(BOAR_GRANT, 0, summoning_sick=False)
        attacker = game.create_permanent(BOAR, 0, summoning_sick=False)
        blocker = game.create_permanent(BEAR, 1, summoning_sick=False)
        game.change_controller(source, 1)
        attack = declared_attack(game, [attacker], include_all=True)
        return tuple(
            option.blocks for option in game.legal_block_options(attack, 1)
        ), blocker.object_id

    first = observe(12003)
    second = observe(12003)
    assert first == second
    assert any(len(blocks) == 1 for blocks in first[0])
