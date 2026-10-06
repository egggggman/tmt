"""Oracle-derived artifact sacrifice counter activation and sorcery timing."""

import json

from tmnt_design_studio.card_interpreter07 import (
    CardInterpreter,
    TokenCreationProgram,
    TokenDefinition,
)
from tmnt_design_studio.engine07 import ActionKind, CardFact, Game, TurnStep

ABILITY = (
    "{1}, {T}, Sacrifice this artifact: Put a +1/+1 counter on target creature. "
    "Activate only as a sorcery."
)
TOKEN = TokenDefinition("Anonymous Artifact", "Artifact — Test", oracle_text=ABILITY)
ISLAND = CardFact("Island", "", 0, "Basic Land — Island")
BEAR = CardFact("Bear", "{1}{G}", 2, "Creature — Beast", power=2, toughness=2)


def setup(*, land=True):
    game = Game(([ISLAND] * 60, [ISLAND] * 60), seed=23)
    game.begin_turn()
    if land:
        game.create_permanent(ISLAND, 0, summoning_sick=False)
    source = game.create_tokens(
        0,
        TokenCreationProgram(TOKEN, 1),
        source_card="Anonymous Spell",
        oracle_fragment="Create an Anonymous Artifact token.",
    )[0]
    target = game.create_permanent(BEAR, 1, summoning_sick=False)
    return game, source, target


def resolve(game):
    while game.priority_state is not None:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            game.execute_priority_action(
                game.legal_priority_actions(game.priority_state.player_index)[0]
            )


def test_counter_token_is_generic_and_targets_opposing_creature():
    semantics = CardInterpreter().activated_ability_semantics(TOKEN, ABILITY)
    assert semantics is not None and semantics.coverage.fully_supported
    game, source, target = setup()
    option = next(
        o
        for o in game.legal_main_actions(0)
        if o.kind is ActionKind.ACTIVATE_ABILITY
        and o.object_id == source.object_id
        and o.target_id == target.object_id
    )
    assert game.execute_main_action(option)
    assert source.zone == "former" and source.tapped
    assert not any(p.object_id == source.object_id for p in game.players[0].battlefield)
    assert target.counters.get("+1/+1", 0) == 0
    game.check_invariants()
    resolve(game)
    assert target.counters["+1/+1"] == 1 and target.power == 3
    assert any(e["event"] == "mutagen_counter_placed" for e in game.events)
    game.check_invariants()


def test_counter_token_illegal_timing_target_and_cost_do_not_mutate():
    game, source, target = setup(land=False)
    before = json.dumps(game.snapshot(), sort_keys=True)
    assert (
        game.announce_activated_ability(0, source, ABILITY, target_ids=(target.object_id,)) is None
    )
    assert json.dumps(game.snapshot(), sort_keys=True) == before

    game, source, target = setup()
    before = json.dumps(game.snapshot(), sort_keys=True)
    assert game.announce_activated_ability(0, source, ABILITY, target_ids=("fake",)) is None
    assert json.dumps(game.snapshot(), sort_keys=True) == before

    game.advance_to(TurnStep.DECLARE_ATTACKERS)
    before = json.dumps(game.snapshot(), sort_keys=True)
    assert (
        game.announce_activated_ability(0, source, ABILITY, target_ids=(target.object_id,)) is None
    )
    assert json.dumps(game.snapshot(), sort_keys=True) == before


def test_counter_token_replay_is_deterministic():
    def run():
        game, source, target = setup()
        game.announce_activated_ability(0, source, ABILITY, target_ids=(target.object_id,))
        resolve(game)
        return json.dumps(game.snapshot(), sort_keys=True)

    assert run() == run()
