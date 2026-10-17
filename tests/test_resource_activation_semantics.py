"""Complete resource conversion activations with independent stack resolution."""

from tmnt_design_studio.card_interpreter07 import (
    ActivatedEffectKind,
    CardInterpreter,
    TokenCreationProgram,
    TokenDefinition,
)
from tmnt_design_studio.engine07 import ActionKind, CardFact, Game, TurnStep
from tmnt_design_studio.pilot07 import AcceptancePilot

LAND = CardFact("Plains", "", 0, "Basic Land — Plains", "({T}: Add {W}.)")
DRAW = "{2}, Sacrifice another creature or token: Draw a card. Activate only as a sorcery."
LIFE = "{2}, {T}, Sacrifice this creature: You gain 3 life."
SOURCE = CardFact(
    "Resource Cat", "{1}{B/G}", 2, "Artifact Creature — Food Cat", DRAW + "\n" + LIFE, 2, 2
)
CREATURE = CardFact("Volunteer", "{1}", 1, "Creature", power=1, toughness=1)
TOKEN = TokenDefinition("Spare token", "Artifact")


def add_token(game):
    return game.create_tokens(
        0,
        TokenCreationProgram(TOKEN, 1),
        controller=0,
        source_card="Generic creator",
        oracle_fragment="Create an artifact token.",
    )[0]


def setup(seed=3351, *, mana=4):
    game = Game(([LAND] * 40, [LAND] * 40), seed=seed)
    game.begin_turn()
    for _ in range(mana):
        game.create_permanent(LAND, 0, summoning_sick=False)
    source = game.create_permanent(SOURCE, 0, summoning_sick=False)
    return game, source


def drain(game):
    while game.priority_state:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            game.execute_priority_action(
                game.legal_priority_actions(game.priority_state.player_index)[0]
            )


def test_complete_oracle_clauses_and_fail_closed_variants():
    interpreter = CardInterpreter()
    for name in ("Resource Cat", "Other Cat"):
        card = CardFact(name, "{1}{B/G}", 2, SOURCE.type_line, SOURCE.oracle_text, 2, 2)
        draw = interpreter.activated_ability_semantics(card, DRAW)
        life = interpreter.activated_ability_semantics(card, LIFE)
        assert draw.coverage.fully_supported and life.coverage.fully_supported
        assert draw.program.effect_kind is ActivatedEffectKind.DRAW_CARDS
        assert draw.program.cost.sacrifice_other_creature_or_token
        assert life.program.effect_kind is ActivatedEffectKind.GAIN_THREE_LIFE
        assert life.program.cost.tap_source and life.program.cost.sacrifice_source
    altered = DRAW.replace("Draw a card.", "Draw two cards.")
    assert not interpreter.activated_ability_semantics(
        CardFact("Other", "", 0, SOURCE.type_line, altered), altered
    ).coverage.fully_supported


def test_sorcery_speed_payment_choices_and_independent_draw_resolution():
    game, source = setup()
    creature = game.create_permanent(CREATURE, 0)
    token = add_token(game)
    enemy = game.create_permanent(CREATURE, 1)
    options = tuple(
        option
        for option in game.legal_main_actions(0)
        if option.kind is ActionKind.ACTIVATE_ABILITY and option.oracle_fragment == DRAW
    )
    assert {option.cost_object_id for option in options} == {creature.object_id, token.object_id}
    assert (
        AcceptancePilot()
        .choose_main_action(game.public_view(), game.legal_main_actions(0), "activate")
        .cost_object_id
        == token.object_id
    )
    for illegal in (source, enemy, game.players[0].battlefield[0]):
        assert (
            game.announce_activated_ability(0, source, DRAW, other_sacrifice_id=illegal.object_id)
            is None
        )
    before = len(game.players[0].hand)
    ability = game.announce_activated_ability(0, source, DRAW, other_sacrifice_id=token.object_id)
    assert ability and token.zone == "former" and source.zone == "battlefield"
    assert ability.other_sacrifice_id == token.object_id
    assert game.players[0].battlefield[0].tapped
    game.move_object(source, "graveyard", reason="test_response")
    drain(game)
    assert len(game.players[0].hand) == before + 1
    assert ability.zone == "former"
    game.check_invariants()


def test_timing_repeated_payment_and_pilot_declines_creature_sacrifice():
    game, source = setup()
    first = game.create_permanent(CREATURE, 0)
    second = game.create_permanent(CREATURE, 0)
    assert (
        AcceptancePilot()
        .choose_main_action(game.public_view(), game.legal_main_actions(0), "activate")
        .kind
        is ActionKind.PASS
    )
    timing, timing_source = setup(seed=3353)
    timing_cost = timing.create_permanent(CREATURE, 0)
    timing.advance_to(TurnStep.BEGINNING_OF_COMBAT)
    assert (
        timing.announce_activated_ability(
            0, timing_source, DRAW, other_sacrifice_id=timing_cost.object_id
        )
        is None
    )
    assert game.announce_activated_ability(0, source, DRAW, other_sacrifice_id=first.object_id)
    assert (
        game.announce_activated_ability(0, source, DRAW, other_sacrifice_id=second.object_id)
        is None
    )
    drain(game)
    assert game.announce_activated_ability(0, source, DRAW, other_sacrifice_id=second.object_id)
    drain(game)
    assert first.zone == second.zone == "former"
    game.check_invariants()


def test_tap_self_sacrifice_life_priority_and_source_independence():
    game, source = setup(mana=2)
    game.players[0].life = 4
    option = next(
        option
        for option in game.legal_main_actions(0)
        if option.kind is ActionKind.ACTIVATE_ABILITY and option.oracle_fragment == LIFE
    )
    assert (
        AcceptancePilot().choose_main_action(
            game.public_view(), game.legal_main_actions(0), "activate"
        )
        == option
    )
    assert game.execute_main_action(option)
    assert source.zone == "former" and game.stack
    assert game.priority_state and not game.priority_state.resolution_pending
    drain(game)
    assert game.players[0].life == 7
    assert game.food_activation_evidence[-1].resolved
    game.check_invariants()


def test_insufficient_mana_tap_sickness_and_deterministic_replay():
    game, source = setup(mana=1)
    cost = game.create_permanent(CREATURE, 0)
    assert (
        game.announce_activated_ability(0, source, DRAW, other_sacrifice_id=cost.object_id) is None
    )
    assert not game.stack and cost.zone == "battlefield"
    game.create_permanent(LAND, 0)
    source.summoning_sick = True
    assert game.announce_activated_ability(0, source, LIFE) is None
    assert not game.stack

    def replay():
        current, source = setup(seed=3352)
        token = add_token(current)
        option = next(
            option
            for option in current.legal_main_actions(0)
            if option.oracle_fragment == DRAW and option.cost_object_id == token.object_id
        )
        current.execute_main_action(option)
        drain(current)
        current.check_invariants()
        return current.events

    assert replay() == replay()
