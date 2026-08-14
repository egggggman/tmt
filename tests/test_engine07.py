import pytest

from tmnt_design_studio.engine07 import (
    CardFact,
    CardObject,
    Game,
    Permanent,
    PowerToughnessModifier,
)

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
    player.hand = current.set_hand_for_testing(0, [PLAINS, PLAINS])
    assert current.play_land(0, player.hand[0])
    assert not current.play_land(0, player.hand[0])


def test_summoning_sickness_then_legal_attack():
    current = game()
    current.begin_turn()
    player = current.players[0]
    player.battlefield = [current_land(current, 0), current_land(current, 0)]
    player.hand = current.set_hand_for_testing(0, [BEAR])
    assert current.cast(0, player.hand[0])
    assert current.legal_attackers(0) == []
    current.turn = 2
    current.begin_turn()
    assert [p.card.name for p in current.legal_attackers(0)] == ["Bear"]


def current_land(current, controller, card=PLAINS):
    return current.create_permanent(card, controller, summoning_sick=False)


def test_attack_block_damage_and_lethal_to_graveyard():
    current = game()
    current.begin_turn()
    attacker = current.create_permanent(BEAR, 0, summoning_sick=False)
    blocker = current.create_permanent(BEAR, 1, summoning_sick=False)
    current.players[0].battlefield = [attacker]
    current.players[1].battlefield = [blocker]
    current.combat([attacker], {attacker.object_id: blocker})
    assert [obj.card for obj in current.players[0].graveyard] == [BEAR]
    assert [obj.card for obj in current.players[1].graveyard] == [BEAR]


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
    attacker = current.create_permanent(evasive, 0, summoning_sick=False)
    illegal = current.create_permanent(OGRE, 1, summoning_sick=False)
    legal = current.create_permanent(BEAR, 1, summoning_sick=False)
    current.players[0].battlefield = [attacker]
    current.players[1].battlefield = [illegal, legal]

    assert current.generate_blocks([attacker], 1) == {attacker.object_id: legal}
    rejected = next(
        event for event in current.events if event["event"] == "block_candidate_rejected"
    )
    assert rejected["oracle_fragment"] == evasive.oracle_text
    assert rejected["attacker_power"] == 2
    assert rejected["blocker_power"] == 3

    with pytest.raises(ValueError, match="illegal blocker"):
        current.combat([attacker], {attacker.object_id: illegal})


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
    source = current.create_permanent(leader, 0, summoning_sick=False)
    attacker = current.create_permanent(evasive, 0, summoning_sick=False)
    equal_after_modifier = current.create_permanent(OGRE, 1, summoning_sick=False)
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
    first = current.create_permanent(BEAR, 0, summoning_sick=False)
    second = current.create_permanent(BEAR, 0, summoning_sick=False)
    blocker = current.create_permanent(OGRE, 1, summoning_sick=False)
    current.players[0].battlefield = [first, second]
    current.players[1].battlefield = [blocker]

    with pytest.raises(ValueError, match="illegal blocker"):
        current.combat(
            [first, second],
            {first.object_id: blocker, second.object_id: blocker},
        )

    fresh = game()
    fresh.begin_turn()
    attacker = fresh.create_permanent(BEAR, 0, summoning_sick=False)
    nonattacker = fresh.create_permanent(BEAR, 0, summoning_sick=False)
    defending = fresh.create_permanent(OGRE, 1, summoning_sick=False)
    fresh.players[0].battlefield = [attacker, nonattacker]
    fresh.players[1].battlefield = [defending]
    with pytest.raises(ValueError, match="nonattacker"):
        fresh.combat([attacker], {nonattacker.object_id: defending})


def test_unblocked_life_loss_and_win():
    giant = CardFact("Giant", "{R}", 1, "Creature — Giant", power=20, toughness=20)
    current = game()
    current.begin_turn()
    attacker = current.create_permanent(giant, 0, summoning_sick=False)
    current.players[0].battlefield = [attacker]
    current.combat([attacker])
    assert current.players[1].life == 0
    assert current.winner == 0


def test_dead_interaction_with_no_target_is_not_spent():
    current = Game((deck(MOUNTAIN), deck()), seed=3)
    current.begin_turn()
    player = current.players[0]
    player.hand = current.set_hand_for_testing(0, [MISSILE])
    player.battlefield = [
        current_land(current, 0, MOUNTAIN),
        current_land(current, 0, MOUNTAIN),
    ]
    assert not current.cast(0, player.hand[0])
    assert [obj.card for obj in player.hand] == [MISSILE]
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
    original = current_land(current, 0, legend)
    player.battlefield = [current_land(current, 0), current_land(current, 0), original]
    player.hand = current.set_hand_for_testing(0, [legend])

    assert current.cast(0, player.hand[0])
    assert [permanent for permanent in player.battlefield if permanent.card == legend] == [original]
    assert [obj.card for obj in player.graveyard] == [legend]
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
    original = current_land(current, 0, legend)
    player.battlefield = [current_land(current, 0), current_land(current, 0), original]
    player.hand = current.set_hand_for_testing(0, [legend])

    assert current.cast(0, player.hand[0])
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
    player.battlefield = [current_land(current, 0), current_land(current, 0)]
    player.hand = current.set_hand_for_testing(0, [card])

    assert current.cast(0, player.hand[0])
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
    player.battlefield = [current_land(current, 0), current_land(current, 0)]
    player.hand = current.set_hand_for_testing(0, [card])

    assert current.cast(0, player.hand[0])
    event = next(event for event in current.events if event["event"] == "unsupported_semantics")
    assert event["oracle_fragment"] == "Flying"
    assert event["reason"] == "keyword_not_implemented"


def test_printed_pt_counters_and_continuous_modifiers_are_separate():
    current = game()
    permanent = current.create_permanent(BEAR, 0)
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


def test_counter_placement_accumulates_and_combines_with_continuous_pt():
    current = game()
    target = current.create_permanent(BEAR, 0)
    target.pt_modifiers.append(
        PowerToughnessModifier(1, 0, "persistent", "Anthem", "Anthem text", 0)
    )
    current.players[0].battlefield = [target]

    current.place_counters(
        target, "+1/+1", 1, source_card="First source", oracle_fragment="First effect"
    )
    current.place_counters(
        target, "+1/+1", 2, source_card="Second source", oracle_fragment="Second effect"
    )
    current.place_counters(
        target, "finality", 1, source_card="Third source", oracle_fragment="Third effect"
    )

    assert target.printed_power == target.printed_toughness == 2
    assert target.counters == {"+1/+1": 3, "finality": 1}
    assert (target.power, target.toughness) == (6, 5)
    assert [event["total"] for event in current.events if event["event"] == "counters_placed"] == [
        1,
        3,
        1,
    ]


def test_alliance_counter_placement_uses_generic_target_choice_and_persists():
    ally = CardFact(
        "Counter Ally",
        "{1}{W}",
        2,
        "Creature — Bear",
        "Alliance — Whenever another creature you control enters, put a +1/+1 counter on "
        "target creature you control.",
        power=2,
        toughness=2,
    )
    chosen_targets = []
    current = Game(
        (deck(), deck()),
        counter_target_chooser=lambda _player, _source, candidates: candidates[-1],
    )
    current.begin_turn()
    source = current.create_permanent(ally, 0, summoning_sick=False)
    current.players[0].battlefield = [
        current_land(current, 0),
        current_land(current, 0),
        source,
    ]
    current.players[0].hand = current.set_hand_for_testing(0, [BEAR])

    assert current.cast(0, current.players[0].hand[0])
    target = current.players[0].battlefield[-1]
    chosen_targets.append(target.card.name)
    assert chosen_targets == [BEAR.name]
    assert target.counters == {"+1/+1": 1}
    assert (target.power, target.toughness) == (3, 3)

    current.end_turn()
    assert target.counters == {"+1/+1": 1}
    assert (target.power, target.toughness) == (3, 3)


def test_life_gain_counter_trigger_accumulates_without_implementing_lifelink():
    grower = CardFact(
        "Growing Bear",
        "{1}{W}",
        2,
        "Creature — Bear",
        "Whenever you gain life, put a +1/+1 counter on Growing Bear.",
        power=2,
        toughness=2,
    )
    current = game()
    source = current.create_permanent(grower, 0, summoning_sick=False)
    current.players[0].battlefield = [source]

    current.gain_life(0, 2, source_card="Test source", oracle_fragment="You gain 2 life.")
    current.gain_life(0, 1, source_card="Test source", oracle_fragment="You gain 1 life.")

    assert current.players[0].life == 23
    assert source.counters == {"+1/+1": 2}
    assert (source.power, source.toughness) == (4, 4)


def test_modal_alliance_counter_choice_is_once_per_turn_and_resets_at_cleanup():
    modal = CardFact(
        "Modal Bear",
        "{1}{W}",
        2,
        "Creature — Bear",
        "Alliance — Whenever another creature you control enters, choose one that hasn't been "
        "chosen this turn.\n• Put a +1/+1 counter on Modal Bear.\n• Scry 1.",
        power=2,
        toughness=2,
    )
    current = game()
    source = current.create_permanent(modal, 0, summoning_sick=False)
    entering = current.create_permanent(BEAR, 0)
    current.players[0].battlefield = [source, entering]

    current.resolve_creature_entered_counter_effects(entering)
    assert source.counters == {"+1/+1": 1}
    current.resolve_creature_entered_counter_effects(entering)
    assert source.counters == {"+1/+1": 1}
    assert any(event["event"] == "alliance_mode_not_executed" for event in current.events)

    current.end_turn()
    current.resolve_creature_entered_counter_effects(entering)
    assert source.counters == {"+1/+1": 2}


def test_counters_cease_to_exist_on_zone_change_and_new_object_has_none():
    current = game()
    original = current.create_permanent(BEAR, 0)
    current.players[0].battlefield = [original]
    current.place_counters(
        original, "+1/+1", 2, source_card="Test source", oracle_fragment="Test effect"
    )

    current.put_into_graveyard(original)
    returned = current.create_permanent(BEAR, 0)
    current.players[0].battlefield.append(returned)

    assert original.counters == {"+1/+1": 2}
    assert returned.counters == {}
    assert (returned.power, returned.toughness) == (2, 2)


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
    source = current.create_permanent(captain, 0, summoning_sick=False)
    current.players[0].battlefield = [
        current_land(current, 0),
        current_land(current, 0),
        source,
    ]
    current.players[0].hand = current.set_hand_for_testing(0, [BEAR])

    assert current.cast(0, current.players[0].hand[0])
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
    source = current.create_permanent(ally, 0, summoning_sick=False)
    current.players[0].battlefield = [
        current_land(current, 0),
        current_land(current, 0),
        source,
    ]
    current.players[0].hand = current.set_hand_for_testing(0, [BEAR])

    assert current.cast(0, current.players[0].hand[0])
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
    source = current.create_permanent(leader, 0, summoning_sick=False)
    teammate = current.create_permanent(BEAR, 0, summoning_sick=False)
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
    current.players[0].battlefield = [current_land(current, 0), current_land(current, 0)]
    current.players[0].hand = current.set_hand_for_testing(0, [leader])

    assert current.cast(0, current.players[0].hand[0])
    assert any(event["event"] == "pt_effect_condition_not_met" for event in current.events)
    assert not any(
        event["event"] == "unsupported_semantics" and event["card"] == leader.name
        for event in current.events
    )


def test_pt_invariants_reject_invalid_counter_state():
    current = game()
    bad = current.create_permanent(BEAR, 0)
    bad.counters["+1/+1"] = -1
    current.players[0].battlefield = [bad]

    with pytest.raises(AssertionError, match="counter quantities"):
        current.check_invariants()


@pytest.mark.parametrize("counter_type, quantity", [("", 1), ("+1/+1", 0), ("stun", True)])
def test_counter_invariants_reject_invalid_counter_state(counter_type, quantity):
    current = game()
    bad = current.create_permanent(BEAR, 0)
    bad.counters[counter_type] = quantity
    current.players[0].battlefield = [bad]

    with pytest.raises(AssertionError, match="counter quantities"):
        current.check_invariants()


def fabricated_copy(permanent):
    """Build an unregistered value-copy, including a spoofed runtime ID."""
    return Permanent(
        permanent.object_id,
        permanent.card,
        permanent.owner,
        permanent.controller,
        zone=permanent.zone,
        tapped=permanent.tapped,
        summoning_sick=permanent.summoning_sick,
        entered_battlefield_turn=permanent.entered_battlefield_turn,
        damage=permanent.damage,
        counters=dict(permanent.counters),
        pt_modifiers=list(permanent.pt_modifiers),
    )


def test_runtime_objects_from_one_definition_are_distinct_and_deterministic():
    first = game(44)
    second = game(44)
    first_bears = [obj for obj in first.players[0].library if obj.card is BEAR][:2]
    second_bears = [obj for obj in second.players[0].library if obj.card is BEAR][:2]

    assert first_bears[0] is not first_bears[1]
    assert first_bears[0] != first_bears[1]
    assert first_bears[0].object_id != first_bears[1].object_id
    assert [obj.object_id for obj in first_bears] == [obj.object_id for obj in second_bears]
    assert first.snapshot() == second.snapshot()


def test_fabricated_equal_valued_attacker_is_rejected_without_mutation():
    current = game()
    current.begin_turn()
    real = current.create_permanent(BEAR, 0, summoning_sick=False)
    fabricated = fabricated_copy(real)

    with pytest.raises(ValueError, match="illegal attacker"):
        current.combat([fabricated])

    assert not real.tapped
    assert not fabricated.tapped
    assert current.players[1].life == 20


def test_fabricated_equal_valued_blocker_is_rejected():
    current = game()
    current.begin_turn()
    attacker = current.create_permanent(BEAR, 0, summoning_sick=False)
    real_blocker = current.create_permanent(BEAR, 1, summoning_sick=False)
    fabricated = fabricated_copy(real_blocker)

    with pytest.raises(ValueError, match="illegal blocker"):
        current.combat([attacker], {attacker.object_id: fabricated})
    assert not attacker.tapped


def test_fabricated_equal_valued_target_is_rejected_without_spending_card_or_mana():
    current = Game((deck(MOUNTAIN), deck()), seed=3)
    current.begin_turn()
    player = current.players[0]
    player.battlefield = [
        current_land(current, 0, MOUNTAIN),
        current_land(current, 0, MOUNTAIN),
    ]
    player.hand = current.set_hand_for_testing(0, [MISSILE])
    real_target = current.create_permanent(BEAR, 1, summoning_sick=False)
    fabricated = fabricated_copy(real_target)

    assert not current.cast(0, player.hand[0], fabricated)
    assert [obj.card for obj in player.hand] == [MISSILE]
    assert not any(permanent.tapped for permanent in player.battlefield)
    assert real_target.damage == fabricated.damage == 0


def test_invalid_zone_movement_is_atomic_and_does_not_consume_identity():
    current = game()
    real = current.players[0].library[-1]
    fabricated = CardObject(real.object_id, real.card, real.owner, real.controller, real.zone)
    before = (
        tuple(obj.object_id for obj in current.players[0].library),
        tuple(obj.object_id for obj in current.players[0].hand),
        current._next_object_number,
    )

    with pytest.raises(ValueError, match="unregistered"):
        current.move_object(fabricated, "hand")

    after = (
        tuple(obj.object_id for obj in current.players[0].library),
        tuple(obj.object_id for obj in current.players[0].hand),
        current._next_object_number,
    )
    assert after == before


def test_object_cannot_authoritatively_occupy_two_zones():
    current = game()
    obj = current.players[0].library[-1]
    current.players[0].hand.append(obj)

    with pytest.raises(AssertionError, match="more than one zone"):
        current.check_invariants()
    with pytest.raises(ValueError, match="exactly one authoritative zone"):
        current.move_object(obj, "hand")


def test_owner_is_stable_across_control_and_zone_changes():
    current = game()
    permanent = current.create_permanent(BEAR, 0, summoning_sick=False)
    original_id = permanent.object_id

    current.change_controller(permanent, 1)
    assert permanent.owner == 0
    assert permanent.controller == 1
    assert permanent.object_id == original_id
    assert current.players[1].battlefield[-1] is permanent

    graveyard_object = current.put_into_graveyard(permanent)
    assert graveyard_object.owner == graveyard_object.controller == 0
    assert graveyard_object.object_id != original_id
    assert current.players[0].graveyard[-1] is graveyard_object


def test_new_object_resets_counters_effects_damage_tap_and_stale_references():
    current = game()
    current.turn = 4
    old = current.create_permanent(BEAR, 0, summoning_sick=False)
    old.tapped = True
    old.damage = 1
    old.counters["+1/+1"] = 2
    current.apply_pt_modifier(
        old,
        3,
        0,
        duration="until_end_of_turn",
        source_card="Test effect",
        oracle_fragment="Test effect",
    )
    stale_reference = old.object_id

    hand_object = current.move_object(old, "hand", reason="test_return")
    returned = current.move_object(
        hand_object,
        "battlefield",
        controller=0,
        summoning_sick=True,
        reason="test_recast",
    )
    assert isinstance(returned, Permanent)
    assert returned.object_id not in {stale_reference, hand_object.object_id}
    assert old.zone == hand_object.zone == "former"
    assert not current.is_authoritative(old, "battlefield")
    assert not current.is_authoritative(hand_object, "hand")
    assert current.is_authoritative(returned, "battlefield")
    assert returned.owner == returned.controller == 0
    assert returned.counters == {}
    assert returned.pt_modifiers == []
    assert returned.damage == 0
    assert not returned.tapped
    assert returned.summoning_sick
    assert returned.entered_battlefield_turn == 4


def test_old_object_reference_cannot_bind_to_equal_new_incarnation():
    current = game()
    old = current.create_permanent(BEAR, 0, summoning_sick=False)
    references = {old.object_id: "attachment-or-target-reference"}
    graveyard_object = current.put_into_graveyard(old)
    replacement = current.move_object(graveyard_object, "battlefield", controller=0)

    assert replacement.card is old.card
    assert replacement is not old
    assert replacement.object_id not in references
    with pytest.raises(ValueError, match="former object"):
        current.move_object(old, "hand")
