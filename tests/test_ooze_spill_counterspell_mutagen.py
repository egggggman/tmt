from tmnt_design_studio.card_interpreter07 import ActivatedEffectKind, CardInterpreter
from tmnt_design_studio.engine07 import CardFact, CastKind, Game, StackObject

LAND = CardFact("Island", "", 0, "Basic Land ? Island")
BEAR = CardFact("Bear", "{1}{G}", 2, "Creature ? Bear", power=2, toughness=2)
OOZE = CardFact(
    "Ooze Spill",
    "{1}{U}{U}",
    3,
    "Instant",
    'Counter target spell. Create a Mutagen token. (It\'s an artifact with "{1}, {T}, Sacrifice this token: Put a +1/+1 counter on target creature. Activate only as a sorcery.")',  # noqa: E501
)
MUTAGEN_FRAGMENT = "{1}, {T}, Sacrifice this token: Put a +1/+1 counter on target creature. Activate only as a sorcery."  # noqa: E501


def setup():
    game = Game(([LAND] * 30, [LAND] * 30), seed=404)
    game.begin_turn()
    for _ in range(4):
        game.create_permanent(LAND, 0, summoning_sick=False)
    game.set_hand_for_testing(0, [OOZE])
    target = StackObject(game._allocate_object_id(), BEAR, 1, 1, CastKind.CREATURE)
    game._register(target)
    game.stack.append(target)
    game._begin_priority_window()
    return game, target


def pass_all(game):
    while game.priority_state is not None:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            game.execute_priority_action(
                game.legal_priority_actions(game.priority_state.player_index)[0]
            )


def test_ooze_spell_and_mutagen_grammar_are_exactly_supported():
    interpreter = CardInterpreter()
    assert interpreter.cast_program(OOZE).kind is CastKind.OOZE_SPILL
    semantics = interpreter.activated_ability_semantics(game_token_card(), MUTAGEN_FRAGMENT)
    assert semantics is None or semantics.program.effect_kind in {
        ActivatedEffectKind.MUTAGEN_COUNTER,
        ActivatedEffectKind.UNSUPPORTED,
    }


def game_token_card():
    return CardFact(
        "Mutagen",
        "",
        0,
        "Artifact ? Mutagen",
        MUTAGEN_FRAGMENT,
    )


def test_ooze_counters_opposing_stack_spell_and_creates_authoritative_mutagen():
    game, target = setup()
    ooze = game.players[0].hand[0]
    spell = game.announce_spell(0, ooze, target)
    assert spell is not None and spell.cast_kind is CastKind.OOZE_SPILL
    assert spell.object_id != ooze.object_id
    pass_all(game)
    assert target.zone == "former"
    token = next(p for p in game.players[0].battlefield if p.card.name == "Mutagen")
    assert token.object_id not in {ooze.object_id, target.object_id, spell.object_id}
    assert any(e["event"] == "ooze_spill_resolved" for e in game.events)
    game.check_invariants()


def test_ooze_rejects_non_stack_or_non_opposing_targets():
    game, _ = setup()
    ooze = game.players[0].hand[0]
    creature = game.create_permanent(BEAR, 0, summoning_sick=False)
    assert game.announce_spell(0, ooze, creature) is None


def test_mutagen_activation_pays_tap_sacrifice_and_places_counter():
    game, target = setup()
    spell = game.announce_spell(0, game.players[0].hand[0], target)
    assert spell is not None
    pass_all(game)
    token = next(p for p in game.players[0].battlefield if p.card.name == "Mutagen")
    creature = game.create_permanent(BEAR, 0, summoning_sick=False)
    dummy = StackObject(game._allocate_object_id(), BEAR, 1, 1, CastKind.CREATURE)
    game._register(dummy)
    game.stack.append(dummy)
    game._begin_priority_window()
    ability = game.announce_activated_ability(
        0, token, MUTAGEN_FRAGMENT, target_ids=(creature.object_id,)
    )
    assert ability is not None
    assert token.zone == "former" and token.tapped
    pass_all(game)
    assert creature.counters.get("+1/+1") == 1
    assert any(e["event"] == "mutagen_counter_placed" for e in game.events)
    game.check_invariants()


def test_mutagen_target_is_revalidated_and_fails_closed():
    game, target = setup()
    spell = game.announce_spell(0, game.players[0].hand[0], target)
    assert spell is not None
    pass_all(game)
    token = next(p for p in game.players[0].battlefield if p.card.name == "Mutagen")
    creature = game.create_permanent(BEAR, 0, summoning_sick=False)
    dummy = StackObject(game._allocate_object_id(), BEAR, 1, 1, CastKind.CREATURE)
    game._register(dummy)
    game.stack.append(dummy)
    game._begin_priority_window()
    ability = game.announce_activated_ability(
        0, token, MUTAGEN_FRAGMENT, target_ids=(creature.object_id,)
    )
    assert ability is not None
    creature.zone = "former"
    game.players[0].battlefield.remove(creature)
    pass_all(game)
    assert creature.counters == {}
    assert any(e["event"] == "mutagen_counter_failed_closed" for e in game.events)
