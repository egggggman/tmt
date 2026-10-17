"""Targeted counter placement followed by lasting artifact animation."""

from dataclasses import replace
from pathlib import Path

from tmnt_design_studio.card_interpreter07 import ActivatedEffectKind, CardInterpreter
from tmnt_design_studio.engine07 import ActionKind, CardFact, Game, TurnStep
from tmnt_design_studio.stage002 import load_catalog

ROOT = Path(__file__).resolve().parents[1]
ROW = load_catalog(ROOT).resolve_name("Donatello, Mutant Mechanic")
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
FRAGMENT = CardInterpreter().fragments(SOURCE)[0]
ARTIFACT = CardFact("Fixture Device", "{1}", 1, "Artifact — Equipment")
CREATURE = CardFact("Fixture Robot", "{2}", 2, "Artifact Creature — Robot", power=2, toughness=2)
LAND = CardFact("Island", "", 0, "Basic Land — Island")


def setup(target_card=ARTIFACT):
    game = Game(([LAND] * 60, [LAND] * 60), seed=337)
    game.begin_turn()
    source = game.create_permanent(SOURCE, 0, summoning_sick=False)
    target = game.create_permanent(target_card, 0, summoning_sick=False)
    return game, source, target


def resolve(game):
    while game.priority_state is not None:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            game.execute_priority_action(
                game.legal_priority_actions(game.priority_state.player_index)[0]
            )


def test_frozen_and_generic_clause_fail_closed():
    interpreter = CardInterpreter()
    assert interpreter.counter_and_animate_artifact_program(FRAGMENT) == (3, 0, 0, "Robot")
    semantics = interpreter.activated_ability_semantics(SOURCE, FRAGMENT)
    assert semantics.coverage.fully_supported
    assert semantics.program.effect_kind is ActivatedEffectKind.COUNTER_AND_ANIMATE_ARTIFACT
    assert semantics.activation_parent_executable is True
    assert not any(f == FRAGMENT for f, _ in interpreter.unsupported_fragments(SOURCE))
    renamed = replace(SOURCE, name="Fixture Inventor")
    assert interpreter.activated_ability_semantics(renamed, FRAGMENT).coverage.fully_supported
    for variant in (
        FRAGMENT.replace("target artifact you control", "target creature you control"),
        FRAGMENT.replace("in addition to its other types", "instead of its other types"),
        FRAGMENT + " Draw a card.",
    ):
        assert interpreter.counter_and_animate_artifact_program(variant) is None
        assert not interpreter.activated_ability_semantics(SOURCE, variant).coverage.fully_supported


def test_payment_stack_source_departure_and_persistent_layers():
    game, source, target = setup()
    options = game.legal_activated_ability_actions(0)
    assert any(
        o.kind is ActionKind.ACTIVATE_ABILITY
        and o.object_id == source.object_id
        and o.target_id == target.object_id
        and o.oracle_fragment == FRAGMENT
        for o in options
    )
    ability = game.announce_activated_ability(0, source, FRAGMENT, target_ids=(target.object_id,))
    assert ability is not None and source.tapped and not target.counters
    game.move_object(source, "graveyard")
    resolve(game)
    assert target.counters["+1/+1"] == 3
    assert target.type_line == "Artifact Creature — Equipment Robot"
    assert (target.power, target.toughness) == (3, 3)
    assert any(
        e["event"] == "activated_counter_artifact_animation_resolved"
        and e["source_id"] == source.object_id
        and e["target_id"] == target.object_id
        and e["stack_object_id"] == ability.object_id
        for e in game.events
    )
    game.advance_to(TurnStep.COMBAT_DAMAGE)
    game.resolve_combat_damage()
    game.advance_to(TurnStep.CLEANUP)
    assert target.is_creature and (target.power, target.toughness) == (3, 3)
    game.check_invariants()


def test_already_creature_timing_illegal_targets_and_stale_identity():
    game, source, target = setup(CREATURE)
    assert (
        game.announce_activated_ability(0, source, FRAGMENT, target_ids=(source.object_id,)) is None
    )
    enemy = game.create_permanent(ARTIFACT, 1)
    assert (
        game.announce_activated_ability(0, source, FRAGMENT, target_ids=(enemy.object_id,)) is None
    )
    assert game.announce_activated_ability(0, source, FRAGMENT, target_ids=()) is None
    assert game.activate_ability(0, source, FRAGMENT, target_ids=(target.object_id,))
    assert not target.counters
    resolve(game)
    assert (target.power, target.toughness) == (5, 5)
    assert target.type_line == CREATURE.type_line and not target.temporary_type_effects
    game.check_invariants()

    other, source, target = setup()
    assert other.activate_ability(0, source, FRAGMENT, target_ids=(target.object_id,))
    other.change_controller(target, 1)
    resolve(other)
    assert not target.counters and not target.is_creature
    assert any(
        e["event"] == "activated_ability_resolved_no_effect"
        and e.get("reason") == "target_illegal_at_resolution"
        for e in other.events
    )
    other.check_invariants()

    delayed, source, target = setup()
    delayed.advance_to(TurnStep.DECLARE_ATTACKERS)
    assert (
        delayed.announce_activated_ability(0, source, FRAGMENT, target_ids=(target.object_id,))
        is None
    )
    delayed.check_invariants()


def test_zone_change_and_deterministic_replay():
    def replay():
        game, source, target = setup()
        assert game.activate_ability(0, source, FRAGMENT, target_ids=(target.object_id,))
        game.move_object(target, "graveyard")
        replacement = game.create_permanent(ARTIFACT, 0)
        resolve(game)
        assert replacement.object_id != target.object_id
        assert not replacement.counters and not replacement.is_creature
        game.check_invariants()
        return game.snapshot(), game.events

    assert replay() == replay()
