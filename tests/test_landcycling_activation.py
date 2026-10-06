"""Hand-zone landcycling costs, search, and deterministic stack resolution."""

import json

import pytest

from tmnt_design_studio.card_interpreter07 import ActivatedEffectKind, CardInterpreter
from tmnt_design_studio.engine07 import ActionKind, CardFact, CastKind, Game, StackObject

FRAGMENT = (
    "Islandcycling {2} ({2}, Discard this card: Search your library for an Island card, "
    "reveal it, put it into your hand, then shuffle.)"
)
CARD = CardFact("Anonymous Flyer", "{3}{U}", 4, "Creature — Insect", FRAGMENT, 2, 2)
ISLAND = CardFact("Island", "", 0, "Basic Land — Island")
FOREST = CardFact("Forest", "", 0, "Basic Land — Forest")


def setup(*, lands=2, library_islands=2):
    game = Game(
        ([ISLAND] * library_islands + [FOREST] * (60 - library_islands), [FOREST] * 60), seed=112
    )
    game.begin_turn()
    for _ in range(lands):
        game.create_permanent(ISLAND, 0, summoning_sick=False)
    game.set_hand_for_testing(0, [CARD])
    return game


def resolve(game):
    while game.priority_state is not None:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            game.execute_priority_action(
                game.legal_priority_actions(game.priority_state.player_index)[0]
            )


def test_landcycling_uses_oracle_grammar_without_card_name_dispatch():
    semantics = CardInterpreter().activated_ability_semantics(CARD, FRAGMENT)
    assert semantics is not None and semantics.coverage.fully_supported
    assert semantics.program.effect_kind is ActivatedEffectKind.SEARCH_LAND_TYPE
    assert semantics.program.cost.discard_source
    near_neighbor = CardInterpreter().activated_ability_semantics(
        CARD, FRAGMENT.replace("Island", "Swamp", 1)
    )
    assert near_neighbor is not None and not near_neighbor.coverage.fully_supported


def test_landcycling_pays_cost_then_searches_reveals_and_shuffles():
    game = setup()
    card = game.players[0].hand[0]
    options = game.legal_main_actions(0)
    option = next(
        o
        for o in options
        if o.kind is ActionKind.ACTIVATE_ABILITY and o.object_id == card.object_id
    )
    assert game.execute_main_action(option)
    assert card.zone == "former"
    assert len(game.players[0].graveyard) == 1
    assert sum(p.tapped for p in game.players[0].battlefield if p.card.is_land) == 2
    assert len(game.players[0].hand) == 0
    game.check_invariants()
    resolve(game)
    assert len(game.players[0].hand) == 1 and game.players[0].hand[0].name == "Island"
    assert any(e["event"] == "landcycling_revealed" for e in game.events)
    assert any(e["event"] == "landcycling_shuffled" for e in game.events)
    game.check_invariants()


def test_landcycling_no_mana_fails_without_mutation_and_no_match_still_shuffles():
    game = setup(lands=1)
    card = game.players[0].hand[0]
    before = json.dumps(game.snapshot(), sort_keys=True)
    assert game.announce_hand_activated_ability(0, card, FRAGMENT) is None
    assert json.dumps(game.snapshot(), sort_keys=True) == before

    game = setup(library_islands=0)
    card = game.players[0].hand[0]
    assert game.announce_hand_activated_ability(0, card, FRAGMENT)
    resolve(game)
    assert not game.players[0].hand
    assert any(e["event"] == "landcycling_shuffled" and not e["found"] for e in game.events)
    game.check_invariants()


def test_hand_cost_cannot_be_paid_by_a_battlefield_permanent():
    game = setup()
    permanent = game.create_permanent(CARD, 0, summoning_sick=False)
    assert game.activation_payment_plan(0, permanent, FRAGMENT) is None
    assert game.announce_activated_ability(0, permanent, FRAGMENT) is None
    assert not any(
        option.kind is ActionKind.ACTIVATE_ABILITY and option.object_id == permanent.object_id
        for option in game.legal_main_actions(0)
    )


def test_landcycling_replay_matches_entire_state_and_rng():
    def run():
        game = setup()
        game.announce_hand_activated_ability(0, game.players[0].hand[0], FRAGMENT)
        resolve(game)
        return json.dumps(game.snapshot(), sort_keys=True)

    assert run() == run()


def test_landcycling_checks_paid_discard_provenance_before_resolution():
    game = setup()
    ability = game.announce_hand_activated_ability(0, game.players[0].hand[0], FRAGMENT)
    assert ability is not None
    discarded = game._objects[ability.discarded_destination_id]
    discarded.zone = "former"
    with pytest.raises(ValueError, match="discard provenance"):
        game._resolve_activated_ability(ability)
    assert game.stack[-1] is ability


def test_landcycling_can_be_announced_during_opponents_priority_window():
    game = setup()
    pending = StackObject(game._allocate_object_id(), CARD, 1, 1, CastKind.CREATURE)
    game._register(pending)
    game.stack.append(pending)
    game._begin_priority_window(priority_player=1)
    game.execute_priority_action(game.legal_priority_actions(1)[0])
    option = next(
        o
        for o in game.legal_priority_actions(0)
        if o.kind is ActionKind.ACTIVATE_ABILITY and o.oracle_fragment == FRAGMENT
    )
    assert game.execute_priority_action(option)
    resolve(game)
    game.check_invariants()
