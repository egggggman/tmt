from tmnt_design_studio.card_interpreter07 import ActivatedEffectKind, CardInterpreter
from tmnt_design_studio.engine07 import CardFact, CastKind, Game, StackObject

LAND = CardFact("Swamp", "", 0, "Basic Land ? Swamp")
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


def test_tunnel_rats_returns_own_graveyard_card_as_new_tapped_incarnation():
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
    ability = game.announce_graveyard_activated_ability(0, source, FRAGMENT)
    assert ability is not None and source.zone == "former"
    while game.priority_state is not None:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            game.execute_priority_action(
                game.legal_priority_actions(game.priority_state.player_index)[0]
            )
    returned = [p for p in game.players[0].battlefield if p.card.name == "Tunnel Rats"]
    assert len(returned) == 1 and returned[0].tapped and returned[0].object_id != source.object_id
    game.check_invariants()
