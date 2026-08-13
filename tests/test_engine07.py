from tmnt_design_studio.engine07 import CardFact, Game

PLAINS = CardFact("Plains", "", 0, "Basic Land — Plains")
MOUNTAIN = CardFact("Mountain", "", 0, "Basic Land — Mountain")
BEAR = CardFact("Bear", "{1}{W}", 2, "Creature — Bear", power=2, toughness=2)
OGRE = CardFact("Ogre", "{2}{R}", 3, "Creature — Ogre", power=3, toughness=3)
MISSILE = CardFact(
    "Manhole Missile", "{1}{R}", 2, "Instant", "Manhole Missile deals 3 damage to target creature."
)


def deck(color_land=PLAINS):
    return [color_land] * 30 + [BEAR] * 30


def game(seed=1):
    return Game((deck(), deck()), seed=seed)


def test_opening_state_is_deterministic_and_explicit():
    first = game(12).snapshot()
    second = game(12).snapshot()
    assert first == second
    assert [len(player.hand) for player in game(12).players] == [7, 7]
    assert [player.life for player in game(12).players] == [20, 20]
    assert [len(player.library) for player in game(12).players] == [53, 53]


def test_starting_player_skips_first_turn_draw():
    current = game()
    current.begin_turn()
    assert len(current.players[0].hand) == 7
    current.begin_turn()
    assert len(current.players[1].hand) == 8


def test_one_land_per_turn():
    current = game()
    current.begin_turn()
    player = current.players[0]
    player.hand = [PLAINS, PLAINS]
    assert current.play_land(0, player.hand[0])
    assert not current.play_land(0, player.hand[0])


def test_summoning_sickness_then_legal_attack():
    current = game()
    current.begin_turn()
    player = current.players[0]
    player.battlefield = [current_land(0), current_land(0)]
    player.hand = [BEAR]
    assert current.cast(0, BEAR)
    assert current.legal_attackers(0) == []
    current.turn = 2
    current.begin_turn()
    assert [p.card.name for p in current.legal_attackers(0)] == ["Bear"]


def current_land(controller, card=PLAINS):
    from tmnt_design_studio.engine07 import Permanent

    return Permanent(card, controller, summoning_sick=False)


def test_attack_block_damage_and_lethal_to_graveyard():
    from tmnt_design_studio.engine07 import Permanent

    current = game()
    current.begin_turn()
    attacker = Permanent(BEAR, 0, summoning_sick=False)
    blocker = Permanent(BEAR, 1, summoning_sick=False)
    current.players[0].battlefield = [attacker]
    current.players[1].battlefield = [blocker]
    current.combat([attacker], {id(attacker): blocker})
    assert current.players[0].graveyard == [BEAR]
    assert current.players[1].graveyard == [BEAR]


def test_unblocked_life_loss_and_win():
    from tmnt_design_studio.engine07 import Permanent

    giant = CardFact("Giant", "{R}", 1, "Creature — Giant", power=20, toughness=20)
    current = game()
    current.begin_turn()
    attacker = Permanent(giant, 0, summoning_sick=False)
    current.players[0].battlefield = [attacker]
    current.combat([attacker])
    assert current.players[1].life == 0
    assert current.winner == 0


def test_dead_interaction_with_no_target_is_not_spent():
    current = Game((deck(MOUNTAIN), deck()), seed=3)
    current.begin_turn()
    player = current.players[0]
    player.hand = [MISSILE]
    player.battlefield = [current_land(0, MOUNTAIN), current_land(0, MOUNTAIN)]
    assert not current.cast(0, MISSILE)
    assert player.hand == [MISSILE]
    assert current.events[-1]["event"] == "dead_interaction"


def test_draw_from_empty_library_is_a_loss():
    current = game()
    current.players[0].library.clear()
    assert not current.draw(current.players[0])
    assert current.winner == 1


def test_legend_rule_is_a_state_based_action_after_resolution():
    legend = CardFact(
        "Unique Bear",
        "{1}{W}",
        2,
        "Legendary Creature — Bear",
        power=2,
        toughness=2,
    )
    current = game()
    current.begin_turn()
    player = current.players[0]
    original = current_land(0, legend)
    player.battlefield = [current_land(0), current_land(0), original]
    player.hand = [legend]

    assert current.cast(0, legend)
    assert [permanent for permanent in player.battlefield if permanent.card == legend] == [original]
    assert player.graveyard == [legend]
    assert any(event["event"] == "legend_rule_choice" for event in current.events)
    moved = next(
        event
        for event in current.events
        if event["event"] == "permanent_to_graveyard" and event["card"] == legend.name
    )
    assert moved["state_based_action"] == "legend_rule"


def test_legend_rule_chooser_can_keep_the_new_permanent():
    legend = CardFact(
        "Unique Bear",
        "{1}{W}",
        2,
        "Legendary Creature — Bear",
        power=2,
        toughness=2,
    )
    current = Game(
        (deck(), deck()),
        legend_rule_chooser=lambda _player, permanents: permanents[-1],
    )
    current.begin_turn()
    player = current.players[0]
    original = current_land(0, legend)
    player.battlefield = [current_land(0), current_land(0), original]
    player.hand = [legend]

    assert current.cast(0, legend)
    kept = [permanent for permanent in player.battlefield if permanent.card == legend]
    assert len(kept) == 1 and kept[0] is not original


def test_unsupported_telemetry_is_per_oracle_fragment_and_contextual():
    card = CardFact(
        "Verbose Bear",
        "{1}{W}",
        2,
        "Creature — Bear",
        "Whenever this creature attacks, draw a card.\nThis creature has flying.",
        power=2,
        toughness=2,
        keywords=("Flying",),
    )
    current = game()
    current.begin_turn()
    player = current.players[0]
    player.battlefield = [current_land(0), current_land(0)]
    player.hand = [card]

    assert current.cast(0, card)
    events = [event for event in current.events if event["event"] == "unsupported_semantics"]
    assert [event["oracle_fragment"] for event in events] == card.oracle_text.splitlines()
    assert all(
        event["card"] == card.name
        and event["player"] == "A"
        and event["turn"] == 1
        and event["phase"] == "precombat_main"
        and event["reason"] == "oracle_ability_not_implemented"
        for event in events
    )


def test_unsupported_keyword_without_oracle_line_is_reported():
    card = CardFact(
        "Flying Bear",
        "{1}{W}",
        2,
        "Creature — Bear",
        power=2,
        toughness=2,
        keywords=("Flying",),
    )
    current = game()
    current.begin_turn()
    player = current.players[0]
    player.battlefield = [current_land(0), current_land(0)]
    player.hand = [card]

    assert current.cast(0, card)
    event = next(event for event in current.events if event["event"] == "unsupported_semantics")
    assert event["oracle_fragment"] == "Flying"
    assert event["reason"] == "keyword_not_implemented"
