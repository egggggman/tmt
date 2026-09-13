from tmnt_design_studio.engine07 import ActionKind, CardFact, Game, TurnStep

LAND = CardFact("Plains", "", 0, "Basic Land ? Plains")
MENACE = CardFact("Menace Beast", "{2}", 2, "Creature ? Beast", "Menace", power=5, toughness=5)
BEAR = CardFact("Bear", "{1}", 1, "Creature ? Bear", power=2, toughness=2)
MENACE_TRAMPLE_DEATHTOUCH = CardFact(
    "Menace Deathdealer",
    "{3}{G}",
    4,
    "Creature ? Beast",
    "Menace\nDeathtouch\nTrample",
    power=5,
    toughness=5,
    keywords=("Menace", "Deathtouch", "Trample"),
)
MENACE_FIRST = CardFact(
    "Menace First",
    "{3}{W}",
    4,
    "Creature ? Soldier",
    "Menace\nFirst strike",
    power=10,
    toughness=3,
    keywords=("Menace", "First strike"),
)
MENACE_DOUBLE = CardFact(
    "Menace Double",
    "{3}{W}",
    4,
    "Creature ? Soldier",
    "Menace\nDouble strike",
    power=10,
    toughness=5,
    keywords=("Menace", "Double strike"),
)
SINGLE_BLOCK = CardFact(
    "Single Block",
    "{2}",
    2,
    "Creature ? Beast",
    "This creature can't be blocked by more than one creature.",
    power=5,
    toughness=5,
)


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


def _declare(game, attackers):
    game.advance_to(TurnStep.DECLARE_ATTACKERS)
    attack = next(
        option
        for option in game.legal_attack_options(0)
        if option.attacker_ids == tuple(attacker.object_id for attacker in attackers)
    )
    game.execute_attack_action(attack)
    return attack


def test_menace_multi_block_trample_assigns_lethal_then_excess():
    game = Game(([LAND] * 20, [LAND] * 20), seed=9104)
    game.begin_turn()
    attacker = game.create_permanent(MENACE_TRAMPLE_DEATHTOUCH, 0, summoning_sick=False)
    first = game.create_permanent(BEAR, 1, summoning_sick=False)
    second = game.create_permanent(BEAR, 1, summoning_sick=False)
    attack = _declare(game, [attacker])
    multi = next(
        option for option in game.legal_block_options(attack, 1) if len(option.blocks) == 2
    )
    game.execute_block_action(multi)
    evidence = game.resolve_combat_damage()
    attacker_assignments = [
        item for item in evidence.assignments if item.source_id == attacker.object_id
    ]
    assert [item.target_id for item in attacker_assignments[:2]] == [
        first.object_id,
        second.object_id,
    ]
    assert attacker_assignments[-1].target_player == 1 and attacker_assignments[-1].amount == 1
    assert game.players[1].life == 19


def test_menace_deathtouch_multi_block_damage_marks_both_blockers():
    game = Game(([LAND] * 20, [LAND] * 20), seed=9105)
    game.begin_turn()
    attacker = game.create_permanent(MENACE_TRAMPLE_DEATHTOUCH, 0, summoning_sick=False)
    blockers = [game.create_permanent(BEAR, 1, summoning_sick=False) for _ in range(2)]
    attack = _declare(game, [attacker])
    multi = next(
        option for option in game.legal_block_options(attack, 1) if len(option.blocks) == 2
    )
    game.execute_block_action(multi)
    evidence = game.resolve_combat_damage()
    assert {
        item.target_id for item in evidence.assignments if item.source_id == attacker.object_id
    } >= {b.object_id for b in blockers}


def test_menace_multi_block_first_and_double_strike_steps_preserve_roles():
    for seed, card in ((9106, MENACE_FIRST), (9107, MENACE_DOUBLE)):
        game = Game(([LAND] * 20, [LAND] * 20), seed=seed)
        game.begin_turn()
        attacker = game.create_permanent(card, 0, summoning_sick=False)
        blockers = [
            game.create_permanent(
                CardFact("Durable Bear", "{1}", 1, "Creature ? Bear", power=1, toughness=5),
                1,
                summoning_sick=False,
            )
            for _ in range(2)
        ]
        attack = _declare(game, [attacker])
        multi = next(
            option for option in game.legal_block_options(attack, 1) if len(option.blocks) == 2
        )
        game.execute_block_action(multi)
        first = game.resolve_combat_damage()
        second = game.resolve_combat_damage()
        assert first.kind.value == "first_strike"
        assert {
            item.target_id for item in first.assignments if item.source_id == attacker.object_id
        } == {b.object_id for b in blockers}
        assert second.kind.value == "regular"
        assert not any(item.source_id == attacker.object_id for item in second.assignments)


def test_menace_and_single_block_restriction_is_effectively_unblockable():
    card = CardFact(
        "Menace Single",
        "{2}",
        2,
        "Creature ? Beast",
        "Menace\nThis creature can't be blocked by more than one creature.",
        power=5,
        toughness=5,
        keywords=("Menace",),
    )
    game = Game(([LAND] * 20, [LAND] * 20), seed=9108)
    game.begin_turn()
    game.create_permanent(card, 0, summoning_sick=False)
    for _ in range(2):
        game.create_permanent(BEAR, 1, summoning_sick=False)
    attack = _declare(game, [game.players[0].battlefield[-1]])
    assert [option.blocks for option in game.legal_block_options(attack, 1)] == [()]


def test_multiple_attackers_never_reuse_shared_blockers():
    game = Game(([LAND] * 20, [LAND] * 20), seed=9109)
    game.begin_turn()
    attackers = [game.create_permanent(MENACE, 0, summoning_sick=False) for _ in range(2)]
    game.create_permanent(BEAR, 1, summoning_sick=False)
    game.create_permanent(BEAR, 1, summoning_sick=False)
    attack = _declare(game, attackers)
    options = game.legal_block_options(attack, 1)
    assert all(
        len({blocker_id for _, blocker_id in option.blocks}) == len(option.blocks)
        for option in options
    )
    assert any(len(option.blocks) == 2 for option in options)


def test_menace_options_are_deterministic_for_repeated_identity_observations():
    game = Game(([LAND] * 20, [LAND] * 20), seed=9110)
    game.begin_turn()
    attacker = game.create_permanent(MENACE, 0, summoning_sick=False)
    game.create_permanent(BEAR, 1, summoning_sick=False)
    game.create_permanent(BEAR, 1, summoning_sick=False)
    attack = _declare(game, [attacker])
    first = game.legal_block_options(attack, 1)
    second = game.legal_block_options(attack, 1)
    assert first == second
    assert tuple(
        (a, b) for a, b in next(option for option in first if len(option.blocks) == 2).blocks
    ) == tuple(
        (a, b) for a, b in next(option for option in second if len(option.blocks) == 2).blocks
    )
