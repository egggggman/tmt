"""A self modifier counts current controlled artifacts in P/T layer 7c."""

from dataclasses import replace
from pathlib import Path

from tmnt_design_studio.card_interpreter07 import (
    CardInterpreter,
    TokenCreationProgram,
    TokenDefinition,
)
from tmnt_design_studio.engine07 import CardFact, Game, TurnStep
from tmnt_design_studio.stage002 import _semantic_coverage, load_catalog

ROOT = Path(__file__).resolve().parents[1]
ROW = load_catalog(ROOT).resolve_name("Krang, Master Mind")
SOURCE = CardFact(
    ROW.name,
    ROW.mana_cost,
    int(ROW.mana_value),
    ROW.type_line,
    ROW.oracle_text,
    power=int(ROW.power),
    toughness=int(ROW.toughness),
    oracle_id=ROW.oracle_id,
)
FRAGMENT = "Krang gets +1/+0 for each other artifact you control."
LAND = CardFact("Island", "", 0, "Basic Land — Island")
ARTIFACT = CardFact("Fixture Relic", "{1}", 1, "Artifact")
CREATURE = CardFact("Fixture Creature", "{1}", 1, "Creature", power=2, toughness=2)
TOKEN = TokenDefinition("Fixture Artifact", "Artifact")
AURA_ROW = load_catalog(ROOT).resolve_name("Retro-Mutation")
AURA = CardFact(
    AURA_ROW.name,
    AURA_ROW.mana_cost,
    int(AURA_ROW.mana_value),
    AURA_ROW.type_line,
    AURA_ROW.oracle_text,
)


def setup(seed=3361):
    game = Game(([LAND] * 60, [LAND] * 60), seed=seed)
    game.begin_turn()
    source = game.create_permanent(SOURCE, 0, summoning_sick=False)
    game.refresh_static_pt_modifiers()
    return game, source


def enter(game, card, controller=0):
    permanent = game.create_permanent(card, controller, summoning_sick=False)
    game.refresh_static_pt_modifiers()
    return permanent


def add_token(game, controller=0):
    return game.create_tokens(
        controller,
        TokenCreationProgram(TOKEN, 1),
        source_card="Fixture creator",
        oracle_fragment="Create an artifact token.",
    )[0]


def changes(game):
    return [event for event in game.events if event["event"] == "pt_static_self_quality_changed"]


def test_frozen_and_renamed_complete_clause_with_fail_closed_neighbors():
    assert SOURCE.oracle_text.splitlines()[-1] == FRAGMENT
    assert ROW.type_line == "Legendary Artifact Creature — Utrom Warrior"
    assert CardInterpreter().static_self_per_other_quality(SOURCE, FRAGMENT) == (1, 0, "Artifact")
    assert _semantic_coverage(CardInterpreter(), SOURCE, FRAGMENT, ()) == {
        "family": "static_self_per_other_quality",
        "payload_executable": True,
        "parent_executable": True,
        "followup_executable": True,
        "fully_supported": True,
        "limitations": [],
    }
    renamed = replace(
        SOURCE, name="Fixture Engine", oracle_text=FRAGMENT.replace("Krang", "Fixture Engine")
    )
    assert CardInterpreter().static_self_per_other_quality(renamed, renamed.oracle_text) == (
        1,
        0,
        "Artifact",
    )
    assert not CardInterpreter().unsupported_fragments(renamed)
    wrong_recipient = replace(SOURCE, oracle_text=FRAGMENT.replace("Krang", "Other creature"))
    assert (
        CardInterpreter().static_self_per_other_quality(
            wrong_recipient, wrong_recipient.oracle_text
        )
        is None
    )
    assert CardInterpreter().unsupported_fragments(wrong_recipient)
    incomplete = replace(SOURCE, oracle_text=FRAGMENT + " It gains flying.")
    assert (
        CardInterpreter().static_self_per_other_quality(incomplete, incomplete.oracle_text) is None
    )


def test_artifact_entry_departure_control_and_sba_recalculation():
    game, source = setup()
    assert (source.power, source.toughness) == (1, 4)  # Excludes its own artifact type.
    creature = enter(game, CREATURE)
    enemy = enter(game, ARTIFACT, 1)
    assert source.power == 1
    artifact = enter(game, ARTIFACT)
    token = add_token(game)
    assert source.power == 3 and source.toughness == 4
    assert changes(game)[-1]["qualifying_count"] == 2
    game.change_controller(enemy, 0)
    assert source.power == 4
    game.change_controller(token, 1)
    assert source.power == 3
    game.put_into_graveyard(artifact)
    assert source.power == 2
    creature.type_line_override = "Artifact Creature — Fixture"
    game.refresh_static_pt_modifiers()
    assert source.power == 3
    creature.type_line_override = None
    game.refresh_static_pt_modifiers()
    assert source.power == 2
    previous_events = list(changes(game))
    game.refresh_static_pt_modifiers()
    assert changes(game) == previous_events
    assert all(event["source_id"] == source.object_id for event in changes(game))
    game.check_invariants()


def test_aura_ability_loss_layer_source_departure_and_reentry():
    game, source = setup(seed=3362)
    enter(game, ARTIFACT)
    enter(game, ARTIFACT)
    assert source.power == 3
    aura = enter(game, AURA, 1)
    game.attach_aura(aura, source)
    assert source.ability_loss_timestamp is not None
    assert (source.power, source.toughness) == (0, 1)
    assert changes(game)[-1]["power_delta"] == -2
    game.put_into_graveyard(aura)
    assert source.power == 3
    game.put_into_graveyard(source)
    fresh = enter(game, SOURCE)
    assert fresh.object_id != source.object_id and fresh.power == 3
    assert changes(game)[-1]["source_id"] == fresh.object_id
    game.check_invariants()


def test_multiple_sources_counters_combat_and_deterministic_trace():
    def replay():
        game, source = setup(seed=3363)
        other = enter(
            game,
            replace(
                SOURCE,
                name="Another Engine",
                oracle_text=FRAGMENT.replace("Krang", "Another Engine"),
            ),
        )
        add_token(game)
        source.counters["+1/+1"] = 1
        game.check_state_based_actions()
        assert (source.power, source.toughness) == (4, 5)
        assert other.power == 3
        game.advance_to(TurnStep.DECLARE_ATTACKERS)
        game.combat([source, other], {})
        assert game.players[1].life == 13
        game.check_invariants()
        return game.events

    assert replay() == replay()
