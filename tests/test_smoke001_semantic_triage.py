"""Small synthetic checks used to classify Smoke 001 semantic evidence."""

from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import ActionKind, CardFact, Game, TriggerEffect

LAND = CardFact("Mountain", "", 0, "Basic Land - Mountain")
ARTIFACT = CardFact("Synthetic Artifact", "", 0, "Artifact")
RAVENOUS = CardFact(
    "Ravenous Robots",
    "{2}{R}",
    3,
    "Creature - Robot",
    "Whenever you cast an artifact spell, create a 1/1 colorless Robot artifact creature token.",
    power=2,
    toughness=2,
)
CASEY = CardFact(
    "Casey Jones, Vigilante",
    "{2}{R}",
    3,
    "Creature - Human Berserker",
    CardInterpreter.VIGILANTE_FRAGMENT,
    power=3,
    toughness=3,
)
APRIL = CardFact(
    "April O'Neil, Hacktivist",
    "{1}{W}",
    2,
    "Creature - Human Scientist",
    (
        "At the beginning of your end step, draw a card for each card type among spells "
        "you've cast this turn."
    ),
    power=2,
    toughness=2,
)
PIZZA = CardFact(
    "Spicy Oatmeal Pizza",
    "{2}{R}",
    3,
    "Artifact - Food",
    "When this artifact enters, it deals 4 damage to any target and 3 damage to you.",
)
PURPLE_DRAGON = CardFact(
    "Purple Dragon Punks",
    "{3}{R}",
    4,
    "Creature - Human Rogue",
    "{T}: Add {R}. Spend this mana only to cast an artifact spell or to activate an ability.",
    power=3,
    toughness=3,
)


def _resolve_all_priority(game: Game) -> None:
    while game.priority_state is not None and game.winner is None:
        state = game.priority_state
        if state.resolution_pending:
            game.process_priority_resolution()
        else:
            option = next(
                option
                for option in game.legal_priority_actions(state.player_index)
                if option.kind is ActionKind.PASS_PRIORITY
            )
            game.execute_priority_action(option)


def test_casey_witness_marker_can_coexist_with_authenticated_resolving_etb():
    game = Game(([LAND] * 20, [LAND] * 20), seed=8101)
    game.begin_turn()
    source = game.create_permanent(CASEY, 1, summoning_sick=False)
    before = len(game.players[1].hand)
    game._process_creature_entered_triggers(source)
    _resolve_all_priority(game)

    assert any(event["event"] == "semantic_opportunity_witnessed" for event in game.events)
    assert len(game.players[1].hand) == before + 3
    assert any(
        event.get("event") == "trigger_resolved"
        and event.get("effect") == TriggerEffect.ETB_VIGILANTE.value
        for event in game.events
    )


def test_ravenous_artifact_spell_trigger_is_not_executed():
    game = Game(([LAND] * 20, [LAND] * 20), seed=8102)
    game.begin_turn()
    source = game.create_permanent(RAVENOUS, 0, summoning_sick=False)
    artifact_spell = game.set_hand_for_testing(0, [ARTIFACT])[0]
    cast = next(
        option
        for option in game.legal_main_actions(0)
        if option.kind is ActionKind.CAST and option.object_id == artifact_spell.object_id
    )

    assert (
        not CardInterpreter()
        .token_semantic_coverage(RAVENOUS, RAVENOUS.oracle_text)
        .coverage.parent_executable
    )
    game.execute_main_action(cast)
    assert game.is_authoritative(source, "battlefield")
    assert any(event.get("event") == "spell_cast" for event in game.events)
    assert not any(event.get("event") == "tokens_created" for event in game.events)


def test_april_end_step_draw_remains_classified_unimplemented():
    limitations = CardInterpreter().unsupported_fragments(APRIL)
    assert (APRIL.oracle_text, "oracle_ability_not_implemented") in limitations


def test_spicy_pizza_damage_trigger_waits_for_priority_and_resolves_in_oracle_order():
    game = Game(([LAND] * 20, [LAND] * 20), seed=8103)
    game.begin_turn()
    lands = [game.create_permanent(LAND, 0, summoning_sick=False) for _ in range(3)]
    for land in lands:
        land.card = CardFact("Mountain", "", 0, "Basic Land - Mountain")
    pizza_spell = game.set_hand_for_testing(0, [PIZZA])[0]
    cast = next(
        option
        for option in game.legal_main_actions(0)
        if option.kind is ActionKind.CAST and option.object_id == pizza_spell.object_id
    )

    game.execute_main_action(cast)
    while game.priority_state is not None and game.winner is None:
        state = game.priority_state
        if state.resolution_pending:
            game.process_priority_resolution()
        else:
            option = next(
                action
                for action in game.legal_priority_actions(state.player_index)
                if action.kind is ActionKind.PASS_PRIORITY
            )
            game.execute_priority_action(option)

    reasons = {
        event["reason"]
        for event in game.events
        if event.get("event") == "unsupported_semantics" and event.get("card") == PIZZA.name
    }
    assert not reasons
    assert game.players[0].life == 17
    damage = [event for event in game.events if event.get("event") == "damage_dealt"]
    assert [event["amount"] for event in damage] == [4, 3]
    assert damage[0]["target_player"] == game.players[1].name
    assert damage[1]["target_player"] == game.players[0].name


def test_purple_dragon_restricted_mana_ability_is_not_offered():
    game = Game(([LAND] * 20, [LAND] * 20), seed=8104)
    game.begin_turn()
    source = game.create_permanent(PURPLE_DRAGON, 0, summoning_sick=False)
    options = game.legal_main_actions(0)

    assert "activation_child_semantics_not_implemented" in {
        reason for _fragment, reason in CardInterpreter().unsupported_fragments(PURPLE_DRAGON)
    }
    assert not any(
        option.kind is ActionKind.ACTIVATE_ABILITY and option.object_id == source.object_id
        for option in options
    )
