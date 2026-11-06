from tmnt_design_studio.engine07 import CardFact, CastKind, Game, StackObject

LAND = CardFact("Forest", "", 0, "Basic Land ? Forest")
FROG = CardFact(
    "Frog Butler",
    "{1}{G}",
    2,
    "Creature ? Frog Spirit",
    "Deathtouch\n{T}: Add one mana of any color.\n{2}: This creature gains reach until end of turn.",  # noqa: E501
    keywords=("Deathtouch",),
    power=2,
    toughness=2,
)
FRAGMENT = "{T}: Add one mana of any color."


def test_frog_butler_produces_chosen_color_with_source_provenance():
    game = Game(([LAND] * 20, [LAND] * 20), seed=77)
    game.begin_turn()
    frog = game.create_permanent(FROG, 0, summoning_sick=False)
    dummy = StackObject(game._allocate_object_id(), FROG, 1, 1, CastKind.CREATURE)
    game._register(dummy)
    game.stack.append(dummy)
    game._begin_priority_window()
    priority = game.priority_state
    stack_before = tuple(game.stack)
    ability = game.announce_activated_ability(0, frog, FRAGMENT, choice_ids=("U",))
    assert ability is not None
    assert ability.zone == "former"
    assert tuple(game.stack) == stack_before
    assert game.priority_state is priority
    assert frog.tapped
    assert game.floating_mana.snapshot(0) == {"U": 1}
    production = game.floating_mana.productions(0)[0]
    assert production.source_id == frog.object_id and production.color == "U"
    assert game.activation_evidence[-1].stack_object_id == ability.object_id
    assert game.activation_evidence[-1].resolved
    assert any(
        item["event"] == "floating_mana_produced"
        and item["source_id"] == frog.object_id
        and item["color"] == "U"
        for item in game.events
    )
    spell_card = CardFact("Off Color Spell", "{U}", 1, "Creature", "", power=1, toughness=1)
    game.set_hand_for_testing(0, [spell_card])
    second = StackObject(game._allocate_object_id(), FROG, 1, 1, CastKind.CREATURE)
    game._register(second)
    game.stack.append(second)
    game._begin_priority_window()
    spell = game.announce_spell(0, game.players[0].hand[0])
    assert spell is not None
    assert game.floating_mana.snapshot(0) == {}
    assert game.floating_mana.consumptions(0)[0].payment_id != production.event_id


def test_frog_butler_mana_ability_rejects_summoning_sick_source():
    game = Game(([LAND] * 20, [LAND] * 20), seed=78)
    game.begin_turn()
    frog = game.create_permanent(FROG, 0)
    dummy = StackObject(game._allocate_object_id(), FROG, 1, 1, CastKind.CREATURE)
    game._register(dummy)
    game.stack.append(dummy)
    game._begin_priority_window()
    stack_before = tuple(game.stack)
    evidence_before = tuple(game.activation_evidence)

    assert game.announce_activated_ability(0, frog, FRAGMENT, choice_ids=("G",)) is None
    assert not frog.tapped
    assert tuple(game.stack) == stack_before
    assert tuple(game.activation_evidence) == evidence_before
    assert game.floating_mana.snapshot(0) == {}
