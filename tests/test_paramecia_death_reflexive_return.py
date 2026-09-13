from tmnt_design_studio.engine07 import CardFact, Game

LAND = CardFact("Plains", "", 0, "Basic Land")
PARAMECIA = CardFact(
    "Paramecia Coloniex",
    "{1}{B}",
    2,
    "Creature",
    "When this creature enters, mill three cards. (Put the top three cards of your library "
    "into your graveyard.)\n"
    "When this creature dies, you may exile it. When you do, put target creature card from "
    "your graveyard on top of your library.",
    2,
    2,
)
BEAR = CardFact("Bear", "", 0, "Creature", "", 2, 2)


def setup(*, exile=True, target=None):
    game = Game(
        ([LAND] * 12, [LAND] * 12),
        seed=71,
        paramecia_exile_chooser=lambda _c, _s: exile,
        paramecia_target_chooser=target,
    )
    game.begin_turn()
    player = game.players[0]
    for card in tuple(player.library):
        game.move_object(card, "graveyard", reason="test_setup")
    player.library.append(game._create_card_object(LAND, 0, "library"))
    target_card = game._create_card_object(BEAR, 0, "graveyard")
    player.graveyard.append(target_card)
    source = game.create_permanent(PARAMECIA, 0)
    source.damage = 2
    game.check_state_based_actions()
    return game, source, target_card


def resolve_all(game):
    while game.priority_state is not None:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            game.execute_priority_action(
                game.legal_priority_actions(game.priority_state.player_index)[0]
            )


def test_declining_exile_leaves_dead_incarnation_in_graveyard():
    game, source, _ = setup(exile=False)
    resolve_all(game)
    player = game.players[0]
    assert [card.card.name for card in player.graveyard][-1] == source.card.name
    assert not player.exile
    assert not any(e["event"] == "paramecia_reflexive_trigger_created" for e in game.events)


def test_exile_and_reflexive_return_preserve_lineage():
    game, source, target = setup()
    resolve_all(game)
    player = game.players[0]
    assert player.exile[-1].card is source.card
    assert player.exile[-1].object_id != source.object_id
    assert player.library[-1].card is target.card
    assert player.library[-1].object_id != target.object_id
    assert any(e["event"] == "paramecia_reflexive_return" for e in game.events)
    assert any(
        e["event"] == "zone_changed" and e.get("reason") == "paramecia_optional_exile"
        for e in game.events
    )


def test_target_invalidation_fails_closed():
    chosen = []

    def choose(_controller, _source, options):
        chosen.extend(options)
        return options[0] if options else None

    game, _source, target = setup(target=choose)
    game.move_object(target, "hand", reason="invalidate_target")
    resolve_all(game)
    assert not any(card.card is BEAR for card in game.players[0].library)
    assert any(e["event"] == "paramecia_target_invalidated" for e in game.events)


def test_ordinary_death_keeps_normal_dies_event():
    plain = CardFact("Grizzly", "", 0, "Creature", "When this creature dies, draw a card.", 2, 2)
    game = Game(([LAND] * 8, [LAND] * 8), seed=73)
    game.begin_turn()
    source = game.create_permanent(plain, 0)
    source.damage = 2
    game.check_state_based_actions()
    assert any(e["kind"] == "creature_died" for e in game.snapshot()["rules_event_evidence"])
    assert any(
        e["event"] == "trigger_pending"
        and e.get("oracle_fragment") == "When this creature dies, draw a card."
        for e in game.events
    )
