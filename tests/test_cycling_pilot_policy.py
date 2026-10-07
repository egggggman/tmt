"""A generic hand cycling choice competes with casting in the fixed pilot."""

import json

from tmnt_design_studio.engine07 import ActionKind, CardFact, Game
from tmnt_design_studio.pilot07 import AcceptancePilot

CYCLING = (
    "Islandcycling {2} ({2}, Discard this card: Search your library for an Island card, "
    "reveal it, put it into your hand, then shuffle.)"
)
LARGE = CardFact("Anonymous Hauler", "{3}{U}", 4, "Creature — Insect", CYCLING, 3, 3)
SMALL = CardFact("Anonymous Scout", "{1}{U}", 2, "Creature — Insect", "", 2, 2)
ISLAND = CardFact("Island", "", 0, "Basic Land — Island")


def setup(*, lands: int, with_small: bool = False) -> Game:
    game = Game(([ISLAND] * 60, [ISLAND] * 60), seed=725)
    game.begin_turn()
    for _ in range(lands):
        game.create_permanent(ISLAND, 0, summoning_sick=False)
    game.set_hand_for_testing(0, [LARGE, SMALL] if with_small else [LARGE])
    return game


def choose(game: Game, stage: str):
    return AcceptancePilot().choose_main_action(
        game.pilot_view(0), game.legal_main_actions(0), stage
    )


def resolve(game: Game) -> None:
    while game.priority_state is not None:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            option = next(
                option
                for option in game.legal_priority_actions(game.priority_state.player_index)
                if option.kind is ActionKind.PASS_PRIORITY
            )
            game.execute_priority_action(option)


def test_cycling_is_selected_when_no_spell_can_be_cast_and_replays_match():
    def play() -> str:
        game = setup(lands=2)
        source_id = game.players[0].hand[0].object_id
        assert choose(game, "activate").kind is ActionKind.PASS
        option = choose(game, "creature")
        assert option.kind is ActionKind.ACTIVATE_ABILITY and option.object_id == source_id
        assert game.execute_main_action(option)
        resolve(game)
        assert len(game.players[0].graveyard) == 1
        assert game.players[0].hand[0].name == "Island"
        assert any(event["event"] == "landcycling_found" for event in game.events)
        game.check_invariants()
        return json.dumps(game.snapshot(), sort_keys=True)

    assert play() == play()


def test_pilot_can_retain_cycling_creature_and_cast_it_when_affordable():
    game = setup(lands=4)
    source_id = game.players[0].hand[0].object_id
    options = game.legal_main_actions(0)
    assert any(
        option.kind is ActionKind.ACTIVATE_ABILITY and option.object_id == source_id
        for option in options
    )
    assert any(
        option.kind is ActionKind.CAST and option.object_id == source_id for option in options
    )
    assert choose(game, "activate").kind is ActionKind.PASS
    option = choose(game, "creature")
    assert option.kind is ActionKind.CAST and option.object_id == source_id
    assert game.execute_main_action(option)
    resolve(game)
    assert any(permanent.card.name == LARGE.name for permanent in game.players[0].battlefield)
    assert not any(event["event"] == "landcycling_found" for event in game.events)
    game.check_invariants()


def test_castable_creature_is_chosen_before_cycling_another_hand_card():
    game = setup(lands=2, with_small=True)
    large_id, small_id = (card.object_id for card in game.players[0].hand)
    assert choose(game, "activate").kind is ActionKind.PASS
    option = choose(game, "creature")
    assert option.kind is ActionKind.CAST and option.object_id == small_id
    assert game.execute_main_action(option)
    resolve(game)
    assert any(card.object_id == large_id for card in game.players[0].hand)
    assert not any(event["event"] == "landcycling_found" for event in game.events)
    game.check_invariants()
