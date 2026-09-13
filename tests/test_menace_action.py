from tmnt_design_studio.engine07 import ActionKind, CardFact, Game, TurnStep

LAND = CardFact("Plains", "", 0, "Basic Land ? Plains")
MENACE = CardFact("Menace Beast", "{2}", 2, "Creature ? Beast", "Menace", power=5, toughness=5)
BEAR = CardFact("Bear", "{1}", 1, "Creature ? Bear", power=2, toughness=2)
SINGLE_BLOCK = CardFact("Single Block", "{2}", 2, "Creature ? Beast", "This creature can't be blocked by more than one creature.", power=5, toughness=5)


def test_menace_requires_two_blockers_and_preserves_ordered_assignment():
    game = Game(([LAND] * 20, [LAND] * 20), seed=9101)
    game.begin_turn()
    attacker = game.create_permanent(MENACE, 0, summoning_sick=False)
    one = game.create_permanent(BEAR, 1, summoning_sick=False)
    two = game.create_permanent(BEAR, 1, summoning_sick=False)
    game.advance_to(TurnStep.DECLARE_ATTACKERS)
    attack = next(option for option in game.legal_attack_options(0) if option.attacker_ids)
    game.execute_attack_action(attack)
    options = game.legal_block_options(attack, 1)
    assert all(len(option.blocks) != 1 for option in options)
    multi = next(option for option in options if len(option.blocks) == 2)
    assert [blocker for _, blocker in multi.blocks] == [one.object_id, two.object_id]
    game.execute_block_action(multi)
    evidence = game.resolve_combat_damage()
    assert [
        assignment.target_id
        for assignment in evidence.assignments
        if assignment.source_id == attacker.object_id
    ] == [one.object_id, two.object_id]
    assert game.players[1].life == 20


def test_menace_rejects_single_block_and_allows_empty_assignment():
    game = Game(([LAND] * 20, [LAND] * 20), seed=9102)
    game.begin_turn()
    game.create_permanent(MENACE, 0, summoning_sick=False)
    blocker = game.create_permanent(BEAR, 1, summoning_sick=False)
    game.advance_to(TurnStep.DECLARE_ATTACKERS)
    attack = next(option for option in game.legal_attack_options(0) if option.attacker_ids)
    game.execute_attack_action(attack)
    assert all(len(option.blocks) != 1 for option in game.legal_block_options(attack, 1))
    game.execute_block_action(
        next(
            option
            for option in game.legal_block_options(attack, 1)
            if option.kind is ActionKind.DECLARE_BLOCKERS and not option.blocks
        )
    )
    evidence = game.resolve_combat_damage()
    assert evidence.assignments[0].target_player == 1
    assert blocker.object_id in {p.object_id for p in game.players[1].battlefield}


def test_single_block_restriction_rejects_multi_block_assignment():
    game = Game(([LAND] * 20, [LAND] * 20), seed=9103)
    game.begin_turn()
    game.create_permanent(SINGLE_BLOCK, 0, summoning_sick=False)
    game.create_permanent(BEAR, 1, summoning_sick=False)
    game.create_permanent(BEAR, 1, summoning_sick=False)
    game.advance_to(TurnStep.DECLARE_ATTACKERS)
    attack = next(option for option in game.legal_attack_options(0) if option.attacker_ids)
    game.execute_attack_action(attack)
    assert all(len(option.blocks) < 2 for option in game.legal_block_options(attack, 1))
