from tmnt_design_studio.engine07 import CardFact, Game, RulesEventKind, TriggerEffect, TurnStep

FOREST = CardFact("Forest", "", 0, "Basic Land — Forest")
MUTAGEN_CREATURE = CardFact(
    "Variable Token Creature",
    "{X}{G}{G}",
    2,
    "Creature — Ooze",
    "When this creature enters, create X Mutagen tokens.",
    power=2,
    toughness=2,
)


def game_with_mana(lands: int, cards: list[CardFact]) -> Game:
    game = Game(([FOREST] * 30, [FOREST] * 30), seed=701)
    game.set_hand_for_testing(0, cards)
    for _ in range(lands):
        game.create_permanent(FOREST, 0)
    game._step = TurnStep.PRECOMBAT_MAIN
    return game


def resolve_spell_and_trigger(game: Game):
    spell = game.resolve_top_of_stack()
    assert spell is not None
    return spell


def test_variable_x_announces_pays_and_creates_exact_zero_one_and_many_tokens():
    for x, expected in ((0, 0), (1, 1), (3, 3)):
        game = game_with_mana(2 + x, [MUTAGEN_CREATURE])
        card = game.players[0].hand[0]
        assert game.legal_x_values(0, card) == tuple(range(x + 1))
        stack = game.announce_spell(0, card, x_value=x)
        assert stack is not None and stack.x_value == x
        resolve_spell_and_trigger(game)
        tokens = [item for item in game.players[0].battlefield if item.is_token]
        assert len(tokens) == expected
        assert all(item.card.name == "Mutagen" and item.controller == 0 for item in tokens)
        game.check_invariants()


def test_variable_x_rejects_missing_illegal_and_insufficient_payment():
    game = game_with_mana(3, [MUTAGEN_CREATURE])
    card = game.players[0].hand[0]
    assert game.announce_spell(0, card) is None
    assert game.announce_spell(0, card, x_value=-1) is None
    assert game.announce_spell(0, card, x_value=2) is None
    assert game.players[0].hand[0] is card


def test_variable_x_is_retained_when_the_source_leaves_before_trigger_resolution():
    game2 = game_with_mana(4, [])
    source = game2.create_permanent(MUTAGEN_CREATURE, 0)
    source.cast_x_value = 2
    event = game2._new_rules_event(RulesEventKind.CREATURE_ENTERED, 0, (source.object_id,))
    game2._enqueue_trigger(
        event, source, MUTAGEN_CREATURE.oracle_text, TriggerEffect.CREATE_TOKEN, x_value=2
    )
    game2._put_pending_triggers_on_stack()
    game2.move_object(source, "graveyard", reason="c3_source_departure")
    game2._priority_resolution_in_progress = True
    try:
        game2.resolve_top_of_stack()
    finally:
        game2._priority_resolution_in_progress = False
    assert len([item for item in game2.players[0].battlefield if item.is_token]) == 2
    game2.check_invariants()


def test_independent_x_values_are_retained_per_spell():
    game = game_with_mana(7, [MUTAGEN_CREATURE, MUTAGEN_CREATURE])
    first, second = game.players[0].hand
    assert game.announce_spell(0, first, x_value=1) is not None
    assert game.announce_spell(0, second, x_value=2) is not None
    game._priority_resolution_in_progress = True
    try:
        game.resolve_top_of_stack()
        game.resolve_top_of_stack()
    finally:
        game._priority_resolution_in_progress = False
    assert len([item for item in game.players[0].battlefield if item.is_token]) == 3
    game.check_invariants()


def test_countered_variable_x_spell_has_no_partial_etb_resolution():
    game = game_with_mana(4, [MUTAGEN_CREATURE])
    spell = game.announce_spell(0, game.players[0].hand[0], x_value=2)
    assert spell is not None
    game.move_object(spell, "graveyard", reason="c3_countered")
    assert not any(item.is_token for item in game.players[0].battlefield)
    game.check_invariants()
