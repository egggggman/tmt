from tmnt_design_studio.card_interpreter07 import ActivatedEffectKind, CardInterpreter
from tmnt_design_studio.engine07 import CardFact, CastKind, Game, StackObject, TurnStep

LAND = CardFact("Swamp", "", 0, "Basic Land ? Swamp")
ISLAND = CardFact("Island", "", 0, "Basic Land ? Island")
RATS = CardFact(
    "Tunnel Rats",
    "{1}{B}",
    2,
    "Creature ? Rat",
    "{4}{B}: Return this card from your graveyard to the battlefield tapped.",
    power=2,
    toughness=2,
)
FRAGMENT = RATS.oracle_text


def test_tunnel_rats_exact_graveyard_semantics():
    semantics = CardInterpreter().activated_ability_semantics(RATS, FRAGMENT)
    assert semantics is not None and semantics.coverage.fully_supported
    assert semantics.program.effect_kind is ActivatedEffectKind.RETURN_SELF_FROM_GRAVEYARD_TAPPED


def test_tunnel_rats_can_activate_at_priority_and_remains_in_graveyard_until_resolution():
    game = Game(([LAND] * 30, [LAND] * 30), seed=912)
    game.begin_turn()
    for _ in range(5):
        game.create_permanent(LAND, 0, summoning_sick=False)
    source = game._create_card_object(RATS, 0, "graveyard")
    game.players[0].graveyard.append(source)
    dummy = StackObject(game._allocate_object_id(), RATS, 1, 1, CastKind.CREATURE)
    game._register(dummy)
    game.stack.append(dummy)
    game._begin_priority_window()
    game._step = TurnStep.END_STEP
    option = next(
        item
        for item in game.legal_priority_actions(0)
        if item.object_id == source.object_id and item.oracle_fragment == FRAGMENT
    )
    assert game.execute_priority_action(option)
    ability = game.stack[-1]
    assert ability is not None and source.zone == "graveyard"
    assert source in game.players[0].graveyard
    while game.priority_state is not None:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            game.execute_priority_action(
                game.legal_priority_actions(game.priority_state.player_index)[0]
            )
    returned = [p for p in game.players[0].battlefield if p.card.name == "Tunnel Rats"]
    assert len(returned) == 1 and returned[0].tapped and returned[0].object_id != source.object_id
    assert source.zone == "former"
    assert next(
        item for item in game.activation_evidence if item.stack_object_id == ability.object_id
    ).resolved
    event_kinds = [item["event"] for item in game.events]
    assert "activation_announced" in event_kinds
    assert "activation_cost_paid" in event_kinds
    assert "activated_ability_resolved" in event_kinds
    game.check_invariants()


def test_tunnel_rats_main_action_exposes_only_when_five_lands_include_black():
    game = Game(([LAND] * 30, [LAND] * 30), seed=914)
    game.begin_turn()
    for _ in range(4):
        game.create_permanent(LAND, 0, summoning_sick=False)
    source = game._create_card_object(RATS, 0, "graveyard")
    game.players[0].graveyard.append(source)
    assert not any(
        item.object_id == source.object_id and item.oracle_fragment == FRAGMENT
        for item in game.legal_main_actions(0)
    )

    game.create_permanent(LAND, 0, summoning_sick=False)
    option = next(
        item
        for item in game.legal_main_actions(0)
        if item.object_id == source.object_id and item.oracle_fragment == FRAGMENT
    )
    assert game.execute_main_action(option)
    ability = game.stack[-1]
    assert source in game.players[0].graveyard
    assert source.zone == "graveyard"
    assert all(land.tapped for land in game.players[0].battlefield if land.card.is_land)
    payment = next(
        item
        for item in game.events
        if item["event"] == "activation_cost_paid" and item["stack_object_id"] == ability.object_id
    )
    assert payment["generic"] == 4 and payment["colored"] == ["B"]


def test_tunnel_rats_requires_a_black_source_even_with_five_available_lands():
    game = Game(([LAND] * 30, [LAND] * 30), seed=915)
    game.begin_turn()
    for _ in range(5):
        game.create_permanent(ISLAND, 0, summoning_sick=False)
    source = game._create_card_object(RATS, 0, "graveyard")
    game.players[0].graveyard.append(source)

    assert not any(
        item.object_id == source.object_id and item.oracle_fragment == FRAGMENT
        for item in game.legal_main_actions(0)
    )


def test_tunnel_rats_does_not_return_if_graveyard_object_leaves_before_resolution():
    game = Game(([LAND] * 30, [LAND] * 30), seed=913)
    game.begin_turn()
    for _ in range(5):
        game.create_permanent(LAND, 0, summoning_sick=False)
    source = game._create_card_object(RATS, 0, "graveyard")
    game.players[0].graveyard.append(source)
    hand_before = len(game.players[0].hand)
    dummy = StackObject(game._allocate_object_id(), RATS, 1, 1, CastKind.CREATURE)
    game._register(dummy)
    game.stack.append(dummy)
    game._begin_priority_window()
    ability = game.announce_graveyard_activated_ability(0, source, FRAGMENT)
    assert ability is not None
    game.move_object(source, "hand", reason="synthetic_response")
    while game.priority_state is not None:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            game.execute_priority_action(
                game.legal_priority_actions(game.priority_state.player_index)[0]
            )
    assert not [p for p in game.players[0].battlefield if p.card.name == "Tunnel Rats"]
    assert source.zone == "former"
    assert len(game.players[0].hand) == hand_before + 1
    assert any(
        item["event"] == "activated_ability_resolved_no_effect"
        and item.get("reason") == "source_no_longer_in_graveyard"
        for item in game.events
    )
    game.check_invariants()
