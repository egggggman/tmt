from tmnt_design_studio.engine07 import CardFact, Game, TriggerEffect

MOUNTAIN = CardFact("Mountain", "", 0, "Basic Land")
RAPHAEL = CardFact(
    "Raphael, Most Attitude",
    "{3}{R}",
    4,
    "Legendary Creature",
    "Menace (This creature cannot be blocked except by two or more creatures.)\n"
    "Alliance - Whenever another creature you control enters, you may exile the top card "
    "of your library.\n"
    "Whenever Raphael attacks, until end of turn, you may play a card exiled with Raphael.",
    4,
    3,
)
SPELL = CardFact("Shock", "{R}", 1, "Instant", "Shock deals 3 damage to any target.")
REMOVAL = CardFact(
    "Generic Conditional Removal",
    "{1}{B}{G}",
    3,
    "Instant",
    "Destroy target artifact or creature. If its mana value was 4 or less, create a Food token. "
    '(It\'s an artifact with "{2}, {T}, Sacrifice this token: You gain 3 life.")',
)
COUNTER = CardFact("Generic Counter", "{U}", 1, "Instant", "Counter target spell.")
TARGET = CardFact("Target Bear", "{1}{G}", 2, "Creature — Bear", power=2, toughness=2)


def resolve_all(game):
    while game.priority_state is not None:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            game.execute_priority_action(
                game.legal_priority_actions(game.priority_state.player_index)[0]
            )


def test_alliance_exile_is_linked_to_source():
    game = Game(([MOUNTAIN] * 12, [MOUNTAIN] * 12), seed=81)
    game.begin_turn()
    source = game.create_permanent(RAPHAEL, 0)
    entering = game.create_permanent(TARGET, 0)
    game._process_creature_entered_triggers(entering)
    assert game.stack[-1].effect is TriggerEffect.RAPHAEL_ALLIANCE_EXILE
    resolve_all(game)
    assert source.object_id in game._raphael_linked_exile
    assert len(game._raphael_linked_exile[source.object_id]) == 1


def test_attack_permission_exposes_only_linked_exile_and_expires_by_turn():
    game = Game(([MOUNTAIN] * 12, [MOUNTAIN] * 12), seed=82)
    game.begin_turn()
    source = game.create_permanent(RAPHAEL, 0)
    linked = game._create_card_object(SPELL, 0, "exile")
    unrelated = game._create_card_object(SPELL, 0, "exile")
    game.players[0].exile.extend((linked, unrelated))
    game._raphael_linked_exile[source.object_id] = [
        (linked.object_id, linked.card, source.object_id)
    ]
    game.resolve_attack_pt_effects([source])
    resolve_all(game)
    assert game._raphael_permissions[source.object_id] == (game.turn, linked.object_id)
    assert game._raphael_permissions[source.object_id][1] != unrelated.object_id


def test_two_attack_grants_preserve_both_distinct_choices_until_turn_ends():
    chosen = iter((0, 1))
    game = Game(
        ([MOUNTAIN] * 20, [MOUNTAIN] * 20),
        seed=85,
        raphael_play_chooser=lambda _controller, _source, options: options[next(chosen)],
    )
    game.begin_turn()
    source = game.create_permanent(RAPHAEL, 0)
    first = game._create_card_object(MOUNTAIN, 0, "exile")
    second = game._create_card_object(SPELL, 0, "exile")
    game.players[0].exile.extend((first, second))
    game._raphael_linked_exile[source.object_id] = [
        (first.object_id, first.card, source.object_id),
        (second.object_id, second.card, source.object_id),
    ]
    game.resolve_attack_pt_effects([source])
    resolve_all(game)
    assert game._raphael_permission_for(0, first) == source.object_id
    game.resolve_attack_pt_effects([source])
    resolve_all(game)
    assert game._raphael_permission_for(0, first) == source.object_id
    assert game._raphael_permission_for(0, second) == source.object_id
    game._turn += 1
    assert game._raphael_permission_for(0, first) is None
    assert game._raphael_permission_for(0, second) is None


def _permission_fixture():
    game = Game(([MOUNTAIN] * 15, [MOUNTAIN] * 15), seed=83)
    game.begin_turn()
    game.players[0].battlefield.append(
        game._create_card_object(MOUNTAIN, 0, "battlefield")
    ) if False else None
    source = game.create_permanent(RAPHAEL, 0)
    land = game._create_card_object(MOUNTAIN, 0, "exile")
    spell_card = CardFact("Free Bear", "", 0, "Creature", "", 2, 2)
    spell = game._create_card_object(spell_card, 0, "exile")
    game.players[0].exile.extend((land, spell))
    game._raphael_linked_exile[source.object_id] = [
        (land.object_id, land.card, source.object_id),
        (spell.object_id, spell.card, source.object_id),
    ]
    game._raphael_permissions[source.object_id] = (game.turn, spell.object_id)
    return game, source, land, spell


def test_linked_spell_cast_uses_exile_stack_lineage():
    game, source, _land, spell = _permission_fixture()
    stack = game.announce_spell(0, spell, cast_from_exile=True)
    assert stack is not None and stack.cast_from_raphael
    assert stack.object_id != spell.object_id
    game.resolve_top_of_stack()
    assert game.players[0].battlefield[-1].card.name == "Free Bear"
    assert any(e.get("reason") == "spell_cast" for e in game.events if e["event"] == "zone_changed")


def test_linked_land_respects_one_land_limit_and_turn_expiry():
    game, source, land, _spell = _permission_fixture()
    game._raphael_permissions[source.object_id] = (game.turn, land.object_id)
    assert game.play_land(0, land, from_raphael=True)
    assert game.players[0].lands_played == 1
    second = game._create_card_object(MOUNTAIN, 0, "exile")
    game.players[0].exile.append(second)
    game._raphael_linked_exile[source.object_id].append(
        (second.object_id, second.card, source.object_id)
    )
    game._raphael_permissions[source.object_id] = (game.turn, second.object_id)
    assert not game.play_land(0, second, from_raphael=True)
    game._turn += 1
    assert not game.announce_spell(0, _spell, cast_from_exile=True)


def test_source_departure_preserves_attack_resolution_and_cross_source_isolation():
    game = Game(([MOUNTAIN] * 15, [MOUNTAIN] * 15), seed=84)
    game.begin_turn()
    first = game.create_permanent(RAPHAEL, 0)
    second = game.create_permanent(RAPHAEL, 0)
    card = game._create_card_object(MOUNTAIN, 0, "exile")
    game.players[0].exile.append(card)
    game._raphael_linked_exile[first.object_id] = [(card.object_id, card.card, first.object_id)]
    game._raphael_permissions[first.object_id] = (game.turn, card.object_id)
    assert game._raphael_permission_for(0, card) == first.object_id
    assert game._raphael_permission_for(1, card) is None
    game.resolve_attack_pt_effects([second])
    game.put_into_graveyard(second, state_based_action="test_departure")
    while game.priority_state is not None:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            game.execute_priority_action(
                game.legal_priority_actions(game.priority_state.player_index)[0]
            )
    assert game._raphael_permissions[second.object_id] == (game.turn, None)
    assert game._raphael_permission_for(0, card) == first.object_id


def test_linked_targeted_instant_uses_priority_payment_and_survives_source_departure():
    from tmnt_design_studio.engine07 import ActionKind, TurnStep

    swamp = CardFact("Swamp", "", 0, "Basic Land — Swamp")
    forest = CardFact("Forest", "", 0, "Basic Land — Forest")
    game = Game(([MOUNTAIN] * 20, [MOUNTAIN] * 20), seed=86)
    game.begin_turn()
    for land in (MOUNTAIN, swamp, forest):
        game.create_permanent(land, 0, summoning_sick=False)
    source = game.create_permanent(RAPHAEL, 0)
    target = game.create_permanent(TARGET, 1)
    card = game._create_card_object(REMOVAL, 0, "exile")
    game.players[0].exile.append(card)
    game._raphael_linked_exile[source.object_id] = [(card.object_id, card.card, source.object_id)]
    game._raphael_permissions[source.object_id] = (game.turn, card.object_id)
    game.destroy(source)
    game.advance_to(TurnStep.DECLARE_ATTACKERS)
    game._begin_priority_window(allow_empty=True, priority_player=0)
    option = next(
        o
        for o in game.legal_priority_actions(0)
        if o.kind is ActionKind.CAST
        and o.object_id == card.object_id
        and o.target_id == target.object_id
    )
    assert game.execute_priority_action(option)
    resolve_all(game)
    assert target.zone == "former"
    assert any(p.card.name == "Food" for p in game.players[0].battlefield)
    assert any(e["event"] == "spell_cast" and e["card"] == REMOVAL.name for e in game.events)
    game.check_invariants()


def test_linked_counter_can_answer_a_spell_but_requires_payment_and_live_permission():
    from tmnt_design_studio.engine07 import ActionKind

    island = CardFact("Island", "", 0, "Basic Land — Island")
    game = Game(([MOUNTAIN] * 20, [MOUNTAIN] * 20), seed=87)
    game.begin_turn()
    mana = game.create_permanent(island, 0, summoning_sick=False)
    source = game.create_permanent(RAPHAEL, 0)
    card = game._create_card_object(COUNTER, 0, "exile")
    game.players[0].exile.append(card)
    game._raphael_linked_exile[source.object_id] = [(card.object_id, card.card, source.object_id)]
    game._raphael_permissions[source.object_id] = (game.turn, card.object_id)
    game.set_hand_for_testing(1, [TARGET])
    # Opponent's supported spell is already on the stack at this response window.
    opposing = game.move_object(
        game.players[1].hand[0],
        "stack",
        controller=1,
        cast_kind=game.interpreter.cast_program(TARGET).kind,
        reason="test_spell",
    )
    game._begin_priority_window(priority_player=0)
    action = next(
        o
        for o in game.legal_priority_actions(0)
        if o.kind is ActionKind.CAST
        and o.object_id == card.object_id
        and o.target_id == opposing.object_id
    )
    mana.tapped = True
    assert action not in game.legal_priority_actions(0)
    mana.tapped = False
    game.destroy(source)
    assert action in game.legal_priority_actions(0)
    game.execute_priority_action(action)
    resolve_all(game)
    assert opposing.zone == "former"
    assert any(e["event"] == "spell_countered" for e in game.events)
    game.check_invariants()


def test_linked_instant_fizzles_when_chosen_target_leaves_before_resolution():
    from tmnt_design_studio.engine07 import ActionKind

    swamp = CardFact("Swamp", "", 0, "Basic Land — Swamp")
    forest = CardFact("Forest", "", 0, "Basic Land — Forest")
    game = Game(([MOUNTAIN] * 20, [MOUNTAIN] * 20), seed=88)
    game.begin_turn()
    for land in (MOUNTAIN, swamp, forest):
        game.create_permanent(land, 0, summoning_sick=False)
    source = game.create_permanent(RAPHAEL, 0)
    target = game.create_permanent(TARGET, 1)
    card = game._create_card_object(REMOVAL, 0, "exile")
    game.players[0].exile.append(card)
    game._raphael_linked_exile[source.object_id] = [(card.object_id, card.card, source.object_id)]
    game._raphael_permissions[source.object_id] = (game.turn, card.object_id)
    game._begin_priority_window(allow_empty=True, priority_player=0)
    action = next(
        o
        for o in game.legal_priority_actions(0)
        if o.kind is ActionKind.CAST
        and o.object_id == card.object_id
        and o.target_id == target.object_id
    )
    game.execute_priority_action(action)
    game.destroy(target)
    resolve_all(game)
    assert not any(p.card.name == "Food" for p in game.players[0].battlefield)
    assert any(e["event"] == "spell_resolved_no_effect" for e in game.events)
