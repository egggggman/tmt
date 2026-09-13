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
    entering = game.create_permanent(SPELL, 0)
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


def test_source_departure_blocks_attack_permission_and_cross_raphael_leakage():
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
    assert game._raphael_permissions.get(second.object_id) is None
