"""C10: generic activation-cost reductions for qualifying artifact tokens."""

import json
from dataclasses import replace

from tmnt_design_studio.card_interpreter07 import (
    CardInterpreter,
    TokenCreationProgram,
    TokenDefinition,
)
from tmnt_design_studio.engine07 import ActionKind, CardFact, Game

ABILITY = (
    "{1}, {T}, Sacrifice this artifact: Put a +1/+1 counter on target creature. "
    "Activate only as a sorcery."
)
GRANT = "Activated abilities of artifact tokens you control cost {1} less to activate."
MUTAGEN = TokenDefinition("Mutagen", "Artifact — Mutagen", oracle_text=ABILITY)
CREATURE_TOKEN = TokenDefinition(
    "Creature Token", "Creature — Test", power=1, toughness=1, oracle_text=ABILITY
)
LAND = CardFact("Plains", "", 0, "Basic Land — Plains")
TARGET = CardFact("Bear", "{1}", 1, "Creature — Beast", power=2, toughness=2)
GRANTOR = CardFact(
    "Generic Artifact Token Discount",
    "{2}{G}",
    3,
    "Creature — Ooze",
    GRANT,
    power=2,
    toughness=2,
)


def setup(*, grantors=1, lands=0):
    game = Game(([LAND] * 40, [LAND] * 40), seed=811)
    game.begin_turn()
    for _ in range(lands):
        game.create_permanent(LAND, 0, summoning_sick=False)
    for _ in range(grantors):
        game.create_permanent(
            replace(GRANTOR, name=f"Grantor {_}"),
            0,
            summoning_sick=False,
        )
    token = game.create_tokens(
        0,
        TokenCreationProgram(MUTAGEN, 1),
        source_card="generic token spell",
        oracle_fragment="Create a Mutagen token.",
    )[0]
    target = game.create_permanent(TARGET, 1, summoning_sick=False)
    return game, token, target


def resolve(game):
    while game.priority_state is not None:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            game.execute_priority_action(
                game.legal_priority_actions(game.priority_state.player_index)[0]
            )


def test_discount_grammar_is_generic_and_fully_supported():
    interpreter = CardInterpreter()
    semantics = interpreter.static_activation_cost_reduction_semantic_coverage(GRANTOR, GRANT)
    assert semantics is not None and semantics.coverage.fully_supported
    assert semantics.program.quality == "artifact"
    assert semantics.program.reduction == 1
    renamed = replace(GRANTOR, name="Renamed Rules Source")
    assert interpreter.static_activation_cost_reduction_semantic_coverage(renamed, GRANT)
    unsupported = interpreter.static_activation_cost_reduction_semantic_coverage(
        CardFact("Spell", "{G}", 1, "Instant", GRANT), GRANT
    )
    assert unsupported is not None and not unsupported.coverage.fully_supported


def test_one_qualifying_artifact_token_gets_exact_zero_cost_activation():
    game, token, target = setup(grantors=1, lands=0)
    option = next(
        item
        for item in game.legal_main_actions(0)
        if item.kind is ActionKind.ACTIVATE_ABILITY
        and item.object_id == token.object_id
        and item.target_id == target.object_id
    )
    assert game.execute_main_action(option)
    resolve(game)
    assert target.counters["+1/+1"] == 1
    paid = next(event for event in game.events if event["event"] == "activation_cost_paid")
    assert paid["printed_generic"] == 1
    assert paid["generic"] == 0
    assert paid["cost_reduction"] == 1


def test_without_qualifying_artifact_the_original_cost_remains_required():
    game, token, target = setup(grantors=0, lands=0)
    before = json.dumps(game.snapshot(), sort_keys=True)
    assert (
        game.announce_activated_ability(0, token, ABILITY, target_ids=(target.object_id,)) is None
    )
    assert json.dumps(game.snapshot(), sort_keys=True) == before


def test_multiple_reductions_stack_but_never_make_a_negative_cost():
    game, token, target = setup(grantors=2, lands=0)
    assert game.announce_activated_ability(0, token, ABILITY, target_ids=(target.object_id,))
    resolve(game)
    paid = next(event for event in game.events if event["event"] == "activation_cost_paid")
    assert paid["generic"] == 0 and paid["cost_reduction"] == 2


def test_reduction_is_live_for_controller_changes_and_source_departure():
    game, token, target = setup(grantors=1, lands=0)
    grantor = game.players[0].battlefield[0]
    game.change_controller(grantor, 1)
    assert (
        game.announce_activated_ability(0, token, ABILITY, target_ids=(target.object_id,)) is None
    )
    game2, token2, target2 = setup(grantors=1, lands=0)
    grantor2 = game2.players[0].battlefield[0]
    game2.move_object(grantor2, "graveyard", reason="discount_source_departure")
    assert (
        game2.announce_activated_ability(0, token2, ABILITY, target_ids=(target2.object_id,))
        is None
    )


def test_nonqualifying_creature_token_does_not_receive_artifact_reduction():
    game, _token, target = setup(grantors=1, lands=0)
    token = game.create_tokens(
        0,
        TokenCreationProgram(CREATURE_TOKEN, 1),
        source_card="generic token spell",
        oracle_fragment="Create a creature token.",
    )[0]
    assert (
        game.announce_activated_ability(0, token, ABILITY, target_ids=(target.object_id,)) is None
    )


def test_discount_replay_is_deterministic():
    def observe():
        game, token, target = setup(grantors=1, lands=0)
        game.announce_activated_ability(0, token, ABILITY, target_ids=(target.object_id,))
        resolve(game)
        return json.dumps(game.snapshot(), sort_keys=True)

    assert observe() == observe()
