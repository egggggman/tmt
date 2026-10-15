"""Complete Class combat artifact animation through generic rules paths."""

from dataclasses import replace

from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import CardFact, Game, TurnStep

ISLAND = CardFact("Island", "", 0, "Basic Land — Island")
CLASS = CardFact(
    "Example Machine Class",
    "{1}{U}",
    2,
    "Enchantment — Class",
    "(Gain the next level as a sorcery to add its ability.)\n"
    "{U}: Level 2\nCreatures you control get +1/+0 and have menace.\n"
    "{4}{U}: Level 3\nAt the beginning of combat on your turn, put three "
    "+1/+1 counters on target artifact you control. If it isn't a creature, "
    "it becomes a 0/0 Robot creature in addition to its other types.",
)
ARTIFACT = CardFact("Example Tool", "{1}", 1, "Artifact — Equipment")
CREATURE = CardFact("Example Golem", "{2}", 2, "Artifact Creature — Golem", power=2, toughness=2)
BEAR = CardFact("Example Bear", "{1}", 1, "Creature — Bear", power=2, toughness=2)
FRAGMENT = CardInterpreter().fragments(CLASS)[-1]


def resolve_priority(game):
    while game.priority_state is not None:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            game.execute_priority_action(
                game.legal_priority_actions(game.priority_state.player_index)[0]
            )


def setup(*, mana=7, artifact=ARTIFACT):
    game = Game(([ISLAND] * 30, [ISLAND] * 30), seed=289)
    game.begin_turn()
    for _ in range(mana):
        game.create_permanent(ISLAND, 0, summoning_sick=False)
    source = game.create_permanent(CLASS, 0)
    target = game.create_permanent(artifact, 0, summoning_sick=False)
    return game, source, target


def advance_class(game, source):
    assert game.activate_ability(0, source, "{U}: Level 2")
    resolve_priority(game)
    assert source.class_level == 2
    assert game.activate_ability(0, source, "{4}{U}: Level 3")
    assert source.class_level == 2
    resolve_priority(game)
    assert source.class_level == 3


def test_complete_level_three_and_misplaced_or_incomplete_text_fail_closed():
    interpreter = CardInterpreter()
    program = interpreter.class_combat_artifact_animation(CLASS, FRAGMENT)
    assert (program.counter_quantity, program.base_power, program.base_toughness) == (3, 0, 0)
    assert program.creature_subtype == "Robot"
    assert interpreter.class_level_child(CLASS, 3) == FRAGMENT
    assert interpreter.activated_ability_semantics(
        CLASS, "{4}{U}: Level 3"
    ).coverage.fully_supported
    for altered in (
        replace(CLASS, name="Different Class"),
        replace(CLASS, oracle_text=CLASS.oracle_text + " Draw a card."),
        replace(CLASS, oracle_text=CLASS.oracle_text.replace("in addition to", "instead of")),
        replace(CLASS, oracle_text=CLASS.oracle_text.replace("{4}{U}: Level 3", "")),
    ):
        if altered.name == "Different Class":
            assert interpreter.class_combat_artifact_animation(altered, FRAGMENT) == program
        else:
            assert interpreter.class_combat_artifact_animation(altered, FRAGMENT) is None
            assert not interpreter.activated_ability_semantics(
                altered, "{4}{U}: Level 3"
            ).coverage.fully_supported


def test_activation_cost_timing_and_combat_trigger_priority():
    poor, source, _target = setup(mana=3)
    assert poor.activate_ability(0, source, "{U}: Level 2")
    resolve_priority(poor)
    assert poor.activation_payment_plan(0, source, "{4}{U}: Level 3") is None
    game, source, target = setup()
    assert game.activation_payment_plan(0, source, "{4}{U}: Level 3") is None
    advance_class(game, source)
    game.advance_to(TurnStep.BEGINNING_OF_COMBAT)
    trigger = game.stack[-1]
    assert trigger.oracle_fragment == FRAGMENT and trigger.target_id == target.object_id
    assert not target.is_creature and not target.counters
    assert game.priority_state is not None
    resolve_priority(game)
    assert target.is_creature and (target.power, target.toughness) == (4, 3)
    game.check_invariants()


def test_persistent_layer_counter_order_equipment_detachment_and_source_departure():
    game, source, equipment = setup()
    bearer = game.create_permanent(BEAR, 0)
    equipment.attached_to = bearer.object_id
    game.refresh_static_pt_modifiers()
    advance_class(game, source)
    game.advance_to(TurnStep.BEGINNING_OF_COMBAT)
    trigger = game.stack[-1]
    game.move_object(source, "graveyard")
    resolve_priority(game)
    assert equipment.counters["+1/+1"] == 3
    assert equipment.type_line == "Artifact Creature — Equipment Robot"
    assert (equipment.power, equipment.toughness) == (3, 3)
    assert equipment.attached_to is None
    assert trigger.source_id == source.object_id
    assert any(e["event"] == "equipment_detached" for e in game.events)
    game.advance_to(TurnStep.COMBAT_DAMAGE)
    game.resolve_combat_damage()
    game.advance_to(TurnStep.CLEANUP)
    assert equipment.is_creature and (equipment.power, equipment.toughness) == (3, 3)
    old_id = equipment.object_id
    moved = game.move_object(equipment, "graveyard")
    assert equipment.zone == "former" and moved.object_id != old_id
    game.check_invariants()


def test_already_creature_keeps_base_pt_and_invalid_target_fizzles():
    game, source, target = setup(artifact=CREATURE)
    advance_class(game, source)
    game.advance_to(TurnStep.BEGINNING_OF_COMBAT)
    resolve_priority(game)
    assert target.counters["+1/+1"] == 3
    assert (target.power, target.toughness) == (6, 5)  # Level-two anthem stays active.
    assert target.type_line == "Artifact Creature — Golem"
    assert not target.temporary_type_effects
    game.check_invariants()

    other, source, target = setup()
    advance_class(other, source)
    other.advance_to(TurnStep.BEGINNING_OF_COMBAT)
    other.move_object(target, "graveyard")
    resolve_priority(other)
    assert not target.counters
    assert any(e["event"] == "class_combat_target_invalid" for e in other.events)
    other.check_invariants()


def test_target_control_change_and_no_legal_artifact_do_not_apply_partial_effects():
    game, source, target = setup()
    advance_class(game, source)
    game.advance_to(TurnStep.BEGINNING_OF_COMBAT)
    game.change_controller(target, 1)
    resolve_priority(game)
    assert not target.counters and not target.is_creature
    assert any(e["event"] == "class_combat_target_invalid" for e in game.events)
    game.check_invariants()

    empty, source, target = setup()
    empty.move_object(target, "graveyard")
    advance_class(empty, source)
    empty.advance_to(TurnStep.BEGINNING_OF_COMBAT)
    assert not empty.stack
    assert any(e["event"] == "class_combat_no_legal_target" for e in empty.events)
    empty.check_invariants()


def test_deck_agnostic_replay_and_opponent_combat_does_not_trigger():
    def replay():
        game, source, target = setup()
        advance_class(game, source)
        game.advance_to(TurnStep.BEGINNING_OF_COMBAT)
        resolve_priority(game)
        game.check_invariants()
        return game.snapshot(), game.events

    assert replay() == replay()
    game, source, _target = setup()
    advance_class(game, source)
    game.advance_to(TurnStep.BEGINNING_OF_COMBAT)
    resolve_priority(game)
    game.advance_to(TurnStep.COMBAT_DAMAGE)
    game.resolve_combat_damage()
    game.advance_to(TurnStep.CLEANUP)
    game.begin_turn()
    game.advance_to(TurnStep.BEGINNING_OF_COMBAT)
    assert not any(item.effect.value == "class_combat_artifact_animation" for item in game.stack)
