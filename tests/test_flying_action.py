from tmnt_design_studio.engine07 import CardFact, Game, TurnStep

LAND = CardFact("Plains", "", 0, "Basic Land - Plains")
WAY = CardFact(
    "Donatello, Way with Machines",
    "{2}{U}",
    3,
    "Legendary Creature - Mutant Ninja Turtle",
    "Flying\nWhenever an artifact you control enters, put a +1/+1 counter on Donatello.",
    power=2,
    toughness=2,
    keywords=("Flying",),
)
ORDINARY = CardFact("Bear", "{1}{G}", 2, "Creature - Bear", power=2, toughness=2)
FLYER = CardFact("Bird", "{1}{W}", 2, "Creature - Bird", power=2, toughness=2, keywords=("Flying",))
REACH = CardFact(
    "Spider", "{2}{G}", 3, "Creature - Spider", power=2, toughness=4, keywords=("Reach",)
)
FIRST_FLYER = CardFact(
    "First Flyer",
    "{2}{W}",
    3,
    "Creature - Bird",
    "Flying\nFirst strike",
    power=3,
    toughness=3,
    keywords=("Flying", "First strike"),
)
DOUBLE_FLYER = CardFact(
    "Double Flyer",
    "{3}{W}",
    4,
    "Creature - Bird",
    "Flying\nDouble strike",
    power=3,
    toughness=3,
    keywords=("Flying", "Double strike"),
)


def _game(attacker=WAY, blockers=(ORDINARY,), seed=9010):
    game = Game(([LAND] * 60, [LAND] * 60), seed=seed)
    game.begin_turn()
    source = game.create_permanent(attacker, 0, summoning_sick=False)
    defenders = [game.create_permanent(card, 1, summoning_sick=False) for card in blockers]
    game.advance_to(TurnStep.DECLARE_ATTACKERS)
    attack = next(option for option in game.legal_attack_options(0) if option.attacker_ids)
    game.execute_attack_action(attack)
    return game, source, defenders, attack


def _block_options(game, attack):
    return game.legal_block_options(attack, 1)


def test_flying_attacker_filters_ordinary_blocker_and_attacks_unblocked():
    game, source, _defenders, attack = _game()
    options = _block_options(game, attack)
    assert all(not option.blocks for option in options)
    game.execute_block_action(next(option for option in options if not option.blocks))
    evidence = game.resolve_combat_damage()
    assert any(
        item.source_id == source.object_id and item.target_player == 1
        for item in evidence.assignments
    )
    assert game.players[1].life == 18


def test_flying_attacker_can_be_blocked_by_flying_or_reach():
    for blocker in (FLYER, REACH):
        game, source, defenders, attack = _game(blockers=(blocker,), seed=9011)
        options = _block_options(game, attack)
        blocking = next(option for option in options if option.blocks)
        assert blocking.blocks == ((source.object_id, defenders[0].object_id),)


def test_ordinary_attacker_can_still_be_blocked_by_ordinary_creature():
    game, source, defenders, attack = _game(attacker=ORDINARY, blockers=(ORDINARY,), seed=9012)
    blocking = next(option for option in _block_options(game, attack) if option.blocks)
    assert blocking.blocks == ((source.object_id, defenders[0].object_id),)


def test_multiple_blockers_are_filtered_without_changing_order():
    game, source, defenders, attack = _game(blockers=(ORDINARY, FLYER, REACH), seed=9013)
    options = _block_options(game, attack)
    assert all(
        blocker_id in {defenders[1].object_id, defenders[2].object_id}
        for option in options
        for _attacker_id, blocker_id in option.blocks
    )
    two = next(option for option in options if len(option.blocks) == 2)
    assert two.blocks == (
        (source.object_id, defenders[1].object_id),
        (source.object_id, defenders[2].object_id),
    )


def test_way_counters_and_power_toughness_remain_active_with_flying():
    game, source, _defenders, attack = _game(blockers=(), seed=9014)
    source.counters["+1/+1"] = 2
    assert (source.power, source.toughness) == (4, 4)
    game.execute_block_action(
        next(option for option in _block_options(game, attack) if not option.blocks)
    )
    evidence = game.resolve_combat_damage()
    assert any(
        item.source_id == source.object_id and item.amount == 4 and item.target_player == 1
        for item in evidence.assignments
    )


def test_flying_replay_is_deterministic():
    def trace():
        game, _source, _defenders, attack = _game(blockers=(ORDINARY, FLYER, REACH), seed=9015)
        game.execute_block_action(
            next(option for option in _block_options(game, attack) if len(option.blocks) == 2)
        )
        game.resolve_combat_damage()
        return game.events, game.snapshot()

    assert trace() == trace()


def test_first_and_double_strike_flying_preserve_damage_steps():
    for attacker, expected_steps in ((FIRST_FLYER, 2), (DOUBLE_FLYER, 2)):
        game, _source, _defenders, attack = _game(attacker=attacker, blockers=(), seed=9016)
        game.execute_block_action(
            next(option for option in _block_options(game, attack) if not option.blocks)
        )
        first = game.resolve_combat_damage()
        regular = game.resolve_combat_damage()
        assert len(game.combat_damage_evidence) == expected_steps
        assert first.assignments
        if attacker is DOUBLE_FLYER:
            assert regular.assignments
        else:
            assert not regular.assignments
