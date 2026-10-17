"""Static Oracle discount for controlled artifact-token activated abilities."""

import copy
import json

import pytest

from tmnt_design_studio.card_interpreter07 import (
    CardInterpreter,
    TokenCreationProgram,
    TokenDefinition,
)
from tmnt_design_studio.engine07 import ActionKind, CardFact, Game, TurnStep

FRAGMENT = "Activated abilities of artifact tokens you control cost {1} less to activate."
REDUCER = CardFact("Renamed Reducer", "{X}{G}{G}", 2, "Creature — Ooze", FRAGMENT, 4, 4)
LAND = CardFact("Forest", "", 0, "Basic Land — Forest")
BEAR = CardFact("Bear", "{1}{G}", 2, "Creature — Beast", power=2, toughness=2)
ABILITY = CardInterpreter.PREDEFINED_TOKENS["mutagen"].oracle_text
TOKEN = CardInterpreter.PREDEFINED_TOKENS["mutagen"]


def setup(*, reducers=1, lands=0, owner=0):
    game = Game(([LAND] * 60, [LAND] * 60), seed=412)
    game.begin_turn()
    for _ in range(lands):
        game.create_permanent(LAND, 0, summoning_sick=False)
    reduction_sources = [game.create_permanent(REDUCER, 0) for _ in range(reducers)]
    source = game.create_tokens(
        owner,
        TokenCreationProgram(TOKEN, 1),
        source_card="Token Maker",
        oracle_fragment="Create a Mutagen token.",
    )[0]
    target = game.create_permanent(BEAR, 1, summoning_sick=False)
    return game, reduction_sources, source, target


def resolve(game):
    while game.priority_state is not None:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            options = game.legal_priority_actions(game.priority_state.player_index)
            game.execute_priority_action(
                next(o for o in options if o.kind is ActionKind.PASS_PRIORITY)
            )


def test_generic_oracle_parser_and_frozen_clause():
    card = REDUCER
    parsed = CardInterpreter().activated_token_cost_reduction_program(card, FRAGMENT)
    assert parsed is not None and (parsed.permanent_type, parsed.amount) == ("Artifact", 1)
    assert (
        FRAGMENT,
        "oracle_ability_not_implemented",
    ) not in CardInterpreter().unsupported_fragments(card)
    for malformed in (
        FRAGMENT.replace("tokens you control", "spells you cast"),
        FRAGMENT + " Draw a card.",
    ):
        variant = CardFact("Different Source", "{2}", 2, "Artifact", malformed)
        assert CardInterpreter().activated_token_cost_reduction_program(variant, malformed) is None


@pytest.mark.parametrize("reducers,expected_generic", [(0, 1), (1, 0), (2, 0)])
def test_discount_floors_and_targeted_sacrifice_transaction(reducers, expected_generic):
    game, reduction_sources, token, target = setup(reducers=reducers)
    plan = game.activation_payment_plan(0, token, ABILITY)
    assert (plan is None) == (reducers == 0)
    if reducers == 0:
        assert (
            game.announce_activated_ability(0, token, ABILITY, target_ids=(target.object_id,))
            is None
        )
        return
    assert plan.requirement.generic == expected_generic
    assert plan.reduction_source_ids == tuple(p.object_id for p in reduction_sources)
    options = [o for o in game.legal_main_actions(0) if o.object_id == token.object_id]
    option = next(o for o in options if o.target_id == target.object_id)
    assert game.execute_main_action(option)
    assert token.zone == "former" and token.tapped
    assert target.counters.get("+1/+1", 0) == 0
    payment = next(
        e
        for e in game.events
        if e["event"] == "activation_cost_paid" and e["source_id"] == token.object_id
    )
    discount = next(e for e in game.events if e["event"] == "activation_cost_reduced")
    assert payment["generic"] == discount["paid_generic"] == 0
    assert discount["printed_generic"] == 1
    assert discount["reduction_source_ids"] == [p.object_id for p in reduction_sources]
    with pytest.raises(ValueError, match="all players pass"):
        game.resolve_top_of_stack()
    game.move_object(reduction_sources[0], "graveyard", reason="response_removed")
    resolve(game)
    assert target.counters["+1/+1"] == 1
    game.check_invariants()


def test_restrictions_and_source_departure_recalculate_legal_actions():
    game, reducers, token, target = setup(lands=1)
    reducer = reducers[0]
    assert game.activation_payment_plan(0, token, ABILITY).requirement.generic == 0
    game.move_object(reducer, "graveyard")
    assert game.activation_payment_plan(0, token, ABILITY).requirement.generic == 1
    game.players[0].battlefield[-2].tapped = True  # the sole Forest
    before = json.dumps(game.snapshot(), sort_keys=True)
    assert (
        game.announce_activated_ability(0, token, ABILITY, target_ids=(target.object_id,)) is None
    )
    assert json.dumps(game.snapshot(), sort_keys=True) == before
    game.players[0].battlefield[-2].tapped = False
    game.advance_to(TurnStep.DECLARE_ATTACKERS)
    assert (
        game.announce_activated_ability(0, token, ABILITY, target_ids=(target.object_id,)) is None
    )


def test_discount_excludes_enemy_tokens_nontokens_and_spells():
    game, _reducers, enemy_token, _target = setup(owner=1)
    assert game.activation_payment_plan(1, enemy_token, ABILITY) is None
    own_artifact = game.create_permanent(
        CardFact("Ordinary Artifact", "{1}", 1, "Artifact", ABILITY),
        0,
        summoning_sick=False,
    )
    assert not own_artifact.is_token
    assert game.activation_payment_plan(0, own_artifact, ABILITY) is None
    spell = game._create_card_object(BEAR, 0, "hand")
    game.players[0].hand.append(spell)
    assert game.payment_plan(0, spell) is None


def test_control_ability_loss_and_token_type_recalculate_live_cost():
    game, reducers, token, _target = setup()
    reducer = reducers[0]
    assert game.activation_payment_plan(0, token, ABILITY).requirement.generic == 0
    game.change_controller(reducer, 1)
    assert game.activation_payment_plan(0, token, ABILITY) is None
    game.change_controller(reducer, 0)
    assert game.activation_payment_plan(0, token, ABILITY).requirement.generic == 0
    reducer.ability_loss_timestamp = (game.turn, 1)
    assert game.activation_payment_plan(0, token, ABILITY) is None
    reducer.ability_loss_timestamp = None
    assert game.activation_payment_plan(0, token, ABILITY).requirement.generic == 0
    creature_token = TokenDefinition(
        "Test Creature", "Creature — Test", power=1, toughness=1, oracle_text=ABILITY
    )
    other = game.create_tokens(
        0,
        TokenCreationProgram(creature_token, 1),
        source_card="Token Maker",
        oracle_fragment="Create a Test Creature token.",
    )[0]
    other.summoning_sick = False
    assert game.activation_payment_plan(0, other, ABILITY) is None
    game.check_invariants()


def test_colored_mana_remains_payable_and_replay_matches():
    draw_token = TokenDefinition(
        "Anonymous Token",
        "Artifact — Test",
        oracle_text="{1}{G}, Sacrifice this artifact: Draw two cards.",
    )

    def run(land):
        game, _reducers, _token, _target = setup(lands=land)
        card = game.create_tokens(
            0,
            TokenCreationProgram(draw_token, 1),
            source_card="Token Maker",
            oracle_fragment="Create a token.",
        )[0]
        plan = game.activation_payment_plan(0, card, draw_token.oracle_text)
        if not land:
            assert plan is None
            return None
        assert plan.requirement.generic == 0 and plan.requirement.colored == ("G",)
        assert game.announce_activated_ability(0, card, draw_token.oracle_text)
        resolve(game)
        game.check_invariants()
        return game.events

    assert run(False) is None
    assert run(True) == copy.deepcopy(run(True))
