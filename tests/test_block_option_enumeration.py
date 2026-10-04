"""Pruned block enumeration retains the complete ordered legal action surface."""

from itertools import permutations, product
from math import comb, perm

import pytest

from tmnt_design_studio.engine07 import ActionKind, ActionOption, CardFact, Game, TurnStep

LAND = CardFact("Plains", "", 0, "Basic Land — Plains")
BODY = CardFact("Fixture creature", "{1}", 1, "Creature — Turtle", power=2, toughness=2)
FLYER = CardFact("Fixture flyer", "{1}", 1, "Creature — Bird", "Flying", 2, 2, ("Flying",))
MENACE = CardFact("Fixture menace", "{1}", 1, "Creature — Rogue", "Menace", 2, 2, ("Menace",))


def combat_state(attack_count, block_count, restricted=False):
    game = Game(([LAND] * 60, [LAND] * 60), seed=711)
    game.begin_turn()
    attackers = [
        game.create_permanent(
            (BODY, FLYER, MENACE)[i % 3] if restricted else BODY, 0, summoning_sick=False
        )
        for i in range(attack_count)
    ]
    available = [
        game.create_permanent(FLYER if restricted and i == 0 else BODY, 1)
        for i in range(block_count)
    ]
    game.advance_to(TurnStep.DECLARE_ATTACKERS)
    attack = next(o for o in game.legal_attack_options(0) if len(o.attacker_ids) == attack_count)
    game.execute_attack_action(attack)
    assert game.step is TurnStep.DECLARE_BLOCKERS
    return game, attack, attackers, available


def old_cartesian_options(game, attackers, available):
    """Frozen pre-optimization algorithm as an independent ordered reference."""
    options = [ActionOption(ActionKind.DECLARE_BLOCKERS, 1)]
    choices = []
    for attacker in attackers:
        groups = [
            group
            for count in range(len(available) + 1)
            for group in permutations(available, count)
            if not group or (not game._has_menace(attacker) or count >= 2)
        ]
        choices.append((attacker, groups))
    for selected in product(*(groups for _attacker, groups in choices)):
        assignment = tuple(
            (attacker.object_id, blocker.object_id)
            for (attacker, _groups), group in zip(choices, selected, strict=True)
            for blocker in group
        )
        if assignment and game._valid_block_assignment(attackers, assignment, 1):
            options.append(ActionOption(ActionKind.DECLARE_BLOCKERS, 1, blocks=assignment))
    return tuple(options)


@pytest.mark.parametrize("attack_count,block_count", [(1, 0), (1, 3), (2, 3), (3, 3)])
@pytest.mark.parametrize("restricted", [False, True])
def test_same_legal_options_in_exact_order_as_original(attack_count, block_count, restricted):
    game, attack, attackers, available = combat_state(attack_count, block_count, restricted)
    events = list(game.events)
    assert game.legal_block_options(attack, 1) == old_cartesian_options(game, attackers, available)
    assert game.events == events


def test_large_invalid_cartesian_product_is_pruned_without_losing_legal_actions():
    game, attack, attackers, available = combat_state(6, 4)
    options = game.legal_block_options(attack, 1)
    # Choose k distinct blockers, order them, then divide the sequence among attackers.
    expected = sum(perm(4, k) * comb(k + 5, 5) for k in range(5))
    assert len(options) == expected == len(set(options))
    first_max = max(options, key=lambda option: len(option.blocks))
    assert first_max.blocks == tuple((attackers[-1].object_id, b.object_id) for b in available)
