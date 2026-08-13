import pytest

from tmnt_design_studio.engine07 import CardFact, Game, Permanent, PowerToughnessModifier

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


def test_power_threshold_evasion_is_used_by_block_generation_and_validation():
    evasive = CardFact(
        "Threshold Rogue",
        "{1}{W}",
        2,
        "Creature — Rogue",
        "Threshold Rogue can't be blocked by creatures with power 3 or greater.",
        power=2,
        toughness=4,
    )
    current = game()
    current.begin_turn()
    attacker = Permanent(evasive, 0, summoning_sick=False)
    illegal = Permanent(OGRE, 1, summoning_sick=False)
    legal = Permanent(BEAR, 1, summoning_sick=False)
    current.players[0].battlefield = [attacker]
    current.players[1].battlefield = [illegal, legal]

    assert current.generate_blocks([attacker], 1) == {id(attacker): legal}
    rejected = next(
        event for event in current.events if event["event"] == "block_candidate_rejected"
    )
    assert rejected["oracle_fragment"] == evasive.oracle_text
    assert rejected["attacker_power"] == 2
    assert rejected["blocker_power"] == 3

    with pytest.raises(ValueError, match="illegal blocker"):
        current.combat([attacker], {id(attacker): illegal})


def test_greater_power_evasion_uses_current_power_after_attack_modifiers():
    evasive = CardFact(
        "Relative Rogue",
        "{1}{W}",
        2,
        "Creature — Rogue",
        "This creature can't be blocked by creatures with greater power.",
        power=2,
        toughness=4,
    )
    leader = CardFact(
        "Attack Leader",
        "{1}{W}",
        2,
        "Creature — Bear",
        "Whenever Attack Leader attacks, each other attacking creature gets +1/+0 until end "
        "of turn.",
        power=1,
        toughness=4,
    )
    current = game()
    current.begin_turn()
    source = Permanent(leader, 0, summoning_sick=False)
    attacker = Permanent(evasive, 0, summoning_sick=False)
    equal_after_modifier = Permanent(OGRE, 1, summoning_sick=False)
    current.players[0].battlefield = [source, attacker]
    current.players[1].battlefield = [equal_after_modifier]

    current.combat([attacker, source], auto_assign_blockers=True)

    assert attacker.power == 3
    creature_damage = [
        event for event in current.events if event["event"] == "combat_damage_creatures"
    ]
    assert creature_damage == [
        {
            "turn": 1,
            "phase": "combat",
            "event": "combat_damage_creatures",
            "attacker": evasive.name,
            "blocker": OGRE.name,
        }
    ]


def test_block_invariants_reject_duplicate_blocker_and_nonattacker_assignment():
    current = game()
    current.begin_turn()
    first = Permanent(BEAR, 0, summoning_sick=False)
    second = Permanent(BEAR, 0, summoning_sick=False)
    blocker = Permanent(OGRE, 1, summoning_sick=False)
    current.players[0].battlefield = [first, second]
    current.players[1].battlefield = [blocker]

    with pytest.raises(ValueError, match="illegal blocker"):
        current.combat([first, second], {id(first): blocker, id(second): blocker})

    fresh = game()
    fresh.begin_turn()
    attacker = Permanent(BEAR, 0, summoning_sick=False)
    nonattacker = Permanent(BEAR, 0, summoning_sick=False)
    defending = Permanent(OGRE, 1, summoning_sick=False)
    fresh.players[0].battlefield = [attacker, nonattacker]
    fresh.players[1].battlefield = [defending]
    with pytest.raises(ValueError, match="nonattacker"):
        fresh.combat([attacker], {id(nonattacker): defending})


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


def test_printed_pt_counters_and_continuous_modifiers_are_separate():
    permanent = Permanent(BEAR, 0)
    permanent.counters["+1/+1"] = 2
    permanent.pt_modifiers.append(
        PowerToughnessModifier(
            3,
            0,
            "until_end_of_turn",
            "Anthem",
            "Target creature gets +3/+0 until end of turn.",
            1,
        )
    )

    assert (permanent.printed_power, permanent.printed_toughness) == (2, 2)
    assert permanent.card == BEAR
    assert permanent.counters == {"+1/+1": 2}
    assert (permanent.power, permanent.toughness) == (7, 4)


def test_static_per_other_creature_modifier_recomputes_on_zone_changes():
    captain = CardFact(
        "Captain Bear",
        "{1}{W}",
        2,
        "Creature — Bear",
        "Captain Bear gets +1/+0 for each other creature you control.",
        power=1,
        toughness=3,
    )
    current = game()
    current.begin_turn()
    source = Permanent(captain, 0, summoning_sick=False)
    current.players[0].battlefield = [current_land(0), current_land(0), source]
    current.players[0].hand = [BEAR]

    assert current.cast(0, BEAR)
    bear = next(permanent for permanent in current.players[0].battlefield if permanent.card == BEAR)
    assert source.printed_power == 1 and source.power == 2
    assert source.pt_modifiers[0].duration == "persistent"
    assert source.pt_modifiers[0].derived_static

    current.put_into_graveyard(bear)
    assert source.power == source.printed_power == 1


def test_alliance_pt_modifier_executes_and_expires_during_cleanup():
    ally = CardFact(
        "Alliance Bear",
        "{1}{W}",
        2,
        "Creature — Bear",
        "Alliance — Whenever another creature you control enters, this creature gets +1/+0 "
        "until end of turn.",
        power=2,
        toughness=2,
    )
    current = game()
    current.begin_turn()
    source = Permanent(ally, 0, summoning_sick=False)
    current.players[0].battlefield = [current_land(0), current_land(0), source]
    current.players[0].hand = [BEAR]

    assert current.cast(0, BEAR)
    assert source.power == 3
    assert source.pt_modifiers[-1].duration == "until_end_of_turn"
    assert not any(
        event["event"] == "unsupported_semantics" and event["card"] == ally.name
        for event in current.events
    )

    current.end_turn()
    assert source.power == source.printed_power == 2
    assert source.pt_modifiers == []
    assert current.events[-2]["event"] == "cleanup_completed"
    assert current.events[-2]["expired_pt_modifiers"] == 1


def test_attack_team_modifier_applies_to_other_attackers_only_then_expires():
    leader = CardFact(
        "Attack Leader",
        "{1}{W}",
        2,
        "Creature — Bear",
        "Whenever Attack Leader attacks, each other attacking creature gets +1/+0 until end "
        "of turn.",
        power=1,
        toughness=2,
    )
    current = game()
    current.begin_turn()
    source = Permanent(leader, 0, summoning_sick=False)
    teammate = Permanent(BEAR, 0, summoning_sick=False)
    current.players[0].battlefield = [source, teammate]

    current.combat([source, teammate])
    assert source.power == source.printed_power
    assert teammate.power == teammate.printed_power + 1
    applied = [event for event in current.events if event["event"] == "pt_modifier_applied"]
    assert applied[-1]["source"] == leader.name
    assert applied[-1]["target"] == BEAR.name

    current.end_turn()
    assert teammate.power == teammate.printed_power


def test_conditional_team_pt_fragment_is_executed_as_condition_not_met():
    leader = CardFact(
        "Sneaky Leader",
        "{1}{W}",
        2,
        "Creature — Bear",
        "When Sneaky Leader enters, if its sneak cost was paid, creatures you control get "
        "+2/+0 until end of turn.",
        power=2,
        toughness=2,
    )
    current = game()
    current.begin_turn()
    current.players[0].battlefield = [current_land(0), current_land(0)]
    current.players[0].hand = [leader]

    assert current.cast(0, leader)
    assert any(event["event"] == "pt_effect_condition_not_met" for event in current.events)
    assert not any(
        event["event"] == "unsupported_semantics" and event["card"] == leader.name
        for event in current.events
    )


def test_pt_invariants_reject_invalid_counter_state():
    current = game()
    bad = Permanent(BEAR, 0)
    bad.counters["+1/+1"] = -1
    current.players[0].battlefield = [bad]

    with pytest.raises(AssertionError, match="counter quantities"):
        current.check_invariants()
