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
