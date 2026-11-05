from pathlib import Path

import pytest

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import ActivatedEffectKind, CardInterpreter
from tmnt_design_studio.engine07 import ActionKind, ActionOption, Game, TurnStep, load_facts
from tmnt_design_studio.stage002 import _authoritative_execution_index

ROOT = Path(__file__).resolve().parents[1]
LEVEL_TWO = "{1}{U}: Level 2"
LEVEL_THREE = "{4}{U}: Level 3"
LEVEL_THREE_TRIGGER = CardInterpreter.DOES_MACHINES_LEVEL_THREE


def _facts():
    catalog = load_card_data(
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json",
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json",
    )
    return load_facts(
        catalog,
        {
            "Does Machines",
            "Sewer-veillance Cam",
            "Fugitive Droid",
            "Quintessential Katana",
            "Turtle Van",
            "Michelangelo, Weirdness to 11",
            "Island",
        },
    )


def _game(*, island_count=5, target_chooser=None, artifacts=()):
    facts = _facts()
    deck = [facts["Island"], facts["Does Machines"]] * 20
    game = Game(
        (deck, deck),
        seed=74013,
        does_machines_target_chooser=target_chooser,
    )
    for _ in range(island_count):
        game.create_permanent(facts["Island"], 0, summoning_sick=False)
    source = game.create_permanent(facts["Does Machines"], 0, summoning_sick=False)
    targets = {
        name: game.create_permanent(facts[name], 0, summoning_sick=False) for name in artifacts
    }
    game.begin_turn()
    return game, source, facts, targets


def _resolve_top(game):
    for _ in range(2):
        action = game.legal_priority_actions(game.priority_state.player_index)[0]
        game.execute_priority_action(action)
    game.process_priority_resolution()


def test_level_three_activation_is_interpreted_from_the_card_fragment():
    card = _facts()["Does Machines"]
    semantics = CardInterpreter().activated_ability_semantics(card, LEVEL_THREE)

    assert semantics is not None
    assert semantics.coverage.fully_supported
    assert semantics.program.effect_kind is ActivatedEffectKind.ADVANCE_CLASS_LEVEL
    assert semantics.program.class_level_target == 3
    assert semantics.program.cost.mana_cost == "{4}{U}"


def test_level_two_exposes_level_three_action_and_pays_five_mana():
    game, source, _facts_by_name, _targets = _game()
    source.class_level = 2

    assert any(action.oracle_fragment == LEVEL_THREE for action in game.legal_main_actions(0))
    plan = game.activation_payment_plan(0, source, LEVEL_THREE)
    assert plan is not None
    assert len(plan.mana_source_ids) == 5
    assert game.activate_ability(0, source, LEVEL_THREE) is not None
    assert (
        sum(permanent.tapped for permanent in game.players[0].battlefield if permanent.card.is_land)
        == 5
    )
    _resolve_top(game)

    assert source.class_level == 3
    assert any(
        reference["evidence_kind"] == "activated_ability"
        and reference["source_id"] == source.object_id
        and reference["oracle_fragment"] == LEVEL_THREE
        for reference in game.snapshot()["conformance"]["executed_references"]
    )
    snapshot = game.snapshot()
    level_three_evidence = next(
        item for item in snapshot["activated_abilities"] if item["oracle_fragment"] == LEVEL_THREE
    )
    assert _authoritative_execution_index(snapshot)[
        ("activated_ability", level_three_evidence["stack_object_id"])
    ] == [{"source_id": source.object_id, "oracle_fragment": LEVEL_THREE}]
    assert any(
        event["event"] == "class_level_advanced"
        and event["from_level"] == 2
        and event["to_level"] == 3
        for event in game.events
    )


def test_insufficient_mana_rejects_level_three_without_payment():
    game, source, _facts_by_name, _targets = _game(island_count=4)
    source.class_level = 2

    assert game.activation_payment_plan(0, source, LEVEL_THREE) is None
    assert not any(action.oracle_fragment == LEVEL_THREE for action in game.legal_main_actions(0))
    assert game.activate_ability(0, source, LEVEL_THREE) is False
    assert all(
        not permanent.tapped for permanent in game.players[0].battlefield if permanent.card.is_land
    )
    assert source.class_level == 2


@pytest.mark.parametrize("card_name", ["Sewer-veillance Cam", "Fugitive Droid"])
def test_level_three_trigger_resolves_for_noncreature_and_creature_artifacts(card_name):
    game, source, facts, targets = _game(
        artifacts=(card_name,),
        target_chooser=lambda _player, _source, offered: next(
            object_id for object_id in offered if game._objects[object_id].card.name == card_name
        ),
    )
    source.class_level = 3
    target = targets[card_name]
    initial_type_line = target.type_line
    initial_power = target.power if target.is_creature else None
    initial_printed_stats = (
        (target.printed_power, target.printed_toughness) if target.is_creature else None
    )

    game.transition_to(TurnStep.BEGINNING_OF_COMBAT)
    assert len(game.stack) == 1
    game._begin_priority_window()
    ability = game.stack[-1]
    assert ability.effect.value == "does_machines_level_three"
    assert ability.target_ids == (target.object_id,)
    _resolve_top(game)

    assert target.counters.get("+1/+1") == 3
    if card_name == "Sewer-veillance Cam":
        assert target.is_creature
        assert "Artifact" in target.type_line and "Creature" in target.type_line
        assert "Robot" in target.type_line
        assert (target.power, target.toughness) == (3, 3)
        original_types = {
            part for part in initial_type_line.replace("—", " ").replace("�", " ").split()
        }
        resulting_types = {
            part for part in target.type_line.replace("—", " ").replace("�", " ").split()
        }
        assert original_types <= resulting_types
    else:
        assert target.type_line == initial_type_line
        assert target.power == initial_power + 3
        assert initial_printed_stats is not None
        assert (target.printed_power, target.printed_toughness) == initial_printed_stats
    assert any(
        event["event"] == "does_machines_level_three_resolved"
        and event["source_id"] == source.object_id
        and event["target_id"] == target.object_id
        and event["applied"]
        for event in game.events
    )
    assert (
        len(
            [
                event
                for event in game.events
                if event["event"] == "does_machines_level_three_resolved"
            ]
        )
        == 1
    )
    game.transition_to(TurnStep.DECLARE_ATTACKERS)
    legal_attacks = game.legal_attack_options(0)
    if card_name == "Sewer-veillance Cam":
        assert any(target.object_id in action.attacker_ids for action in legal_attacks)
    assert any(
        reference["evidence_kind"] == "trigger_resolved"
        and reference["source_id"] == source.object_id
        and reference["oracle_fragment"] == LEVEL_THREE_TRIGGER
        for reference in game.snapshot()["conformance"]["executed_references"]
    )
    snapshot = game.snapshot()
    execution = _authoritative_execution_index(snapshot)
    result_event = next(
        event for event in game.events if event["event"] == "does_machines_level_three_resolved"
    )
    assert result_event["result"]["type_line"] == target.type_line
    assert result_event["result"]["counters"] == target.counters["+1/+1"]
    trigger_references = [
        reference
        for (kind, _evidence_id), entries in execution.items()
        if kind == "trigger_resolved"
        for reference in entries
        if reference == {"source_id": source.object_id, "oracle_fragment": LEVEL_THREE_TRIGGER}
    ]
    assert len(trigger_references) == 1
    with pytest.raises(ValueError, match="authoritative top stack"):
        game._resolve_triggered_ability(ability)


def test_level_three_effect_state_is_deterministic_and_persists_after_cleanup():
    def run_once():
        game, source, facts, targets = _game(artifacts=("Sewer-veillance Cam",))
        source.class_level = 3
        target = targets["Sewer-veillance Cam"]
        game.transition_to(TurnStep.BEGINNING_OF_COMBAT)
        game._begin_priority_window()
        _resolve_top(game)
        game._perform_cleanup()
        return game, target

    first, first_target = run_once()
    second, second_target = run_once()
    assert first_target.type_line == second_target.type_line
    assert first_target.counters == second_target.counters
    assert first_target.power == second_target.power == 3
    assert [event for event in first.events if event["event"].startswith("does_machines_")] == [
        event for event in second.events if event["event"].startswith("does_machines_")
    ]


def test_level_three_trigger_does_not_stack_without_a_legal_artifact_target():
    game, source, _facts, _targets = _game()
    source.class_level = 3

    game.transition_to(TurnStep.BEGINNING_OF_COMBAT)

    assert game.stack == []
    assert not any(
        event["event"] == "trigger_pending" and event["oracle_fragment"] == LEVEL_THREE_TRIGGER
        for event in game.events
    )


def test_level_three_targeted_equipment_becomes_robot_and_detaches():
    game, source, _facts, targets = _game(
        artifacts=("Quintessential Katana", "Fugitive Droid"),
        target_chooser=lambda _player, _source, offered: next(
            object_id
            for object_id in offered
            if game._objects[object_id].card.name == "Quintessential Katana"
        ),
    )
    source.class_level = 3
    equipment = targets["Quintessential Katana"]
    equipment.attached_to = targets["Fugitive Droid"].object_id

    game.transition_to(TurnStep.BEGINNING_OF_COMBAT)
    game._begin_priority_window()
    _resolve_top(game)

    assert equipment.is_creature
    assert {"Artifact", "Creature", "Equipment", "Robot"} <= set(
        equipment.type_line.replace("—", " ").replace("�", " ").split()
    )
    assert equipment.attached_to is None
    assert equipment.counters["+1/+1"] == 3
    assert (equipment.power, equipment.toughness) == (3, 3)


def test_level_three_vehicle_animation_sets_zero_base_stats_before_counters():
    game, source, _facts, targets = _game(artifacts=("Turtle Van", "Michelangelo, Weirdness to 11"))
    source.class_level = 3
    vehicle = targets["Turtle Van"]
    replacement = targets["Michelangelo, Weirdness to 11"]
    replacement_fragment = game.interpreter.fragments(replacement.card)[-1]
    game._register_semantic_occurrence(replacement, 0, replacement_fragment, ())
    original_types = set(vehicle.type_line.replace("—", " ").replace("�", " ").split())

    game.transition_to(TurnStep.BEGINNING_OF_COMBAT)
    game._begin_priority_window()
    _resolve_top(game)

    resulting_types = set(vehicle.type_line.replace("—", " ").replace("�", " ").split())
    assert {"Artifact", "Vehicle", "Creature", "Robot"} <= resulting_types
    assert original_types <= resulting_types
    assert vehicle.counters["+1/+1"] == 3
    assert (vehicle.power, vehicle.toughness) == (3, 3)
    assert not any(
        event["event"] == "counter_replacement_applied" and event["target_id"] == vehicle.object_id
        for event in game.events
    )
    assert vehicle.characteristic_effects[-1].power == 0
    assert vehicle.characteristic_effects[-1].toughness == 0


def test_level_three_counter_placement_uses_michelangelo_replacement():
    game, source, _facts, targets = _game(
        artifacts=("Fugitive Droid", "Michelangelo, Weirdness to 11")
    )
    source.class_level = 3
    target = targets["Fugitive Droid"]
    replacement = targets["Michelangelo, Weirdness to 11"]
    replacement_fragment = game.interpreter.fragments(replacement.card)[-1]
    game._register_semantic_occurrence(replacement, 0, replacement_fragment, ())

    game.transition_to(TurnStep.BEGINNING_OF_COMBAT)
    game._begin_priority_window()
    _resolve_top(game)

    assert target.counters["+1/+1"] == 4
    replacement_event = next(
        event for event in game.events if event["event"] == "counter_replacement_applied"
    )
    assert replacement_event["source_id"] == replacement.object_id
    assert replacement_event["target_id"] == target.object_id
    assert replacement_event["quantity_before"] == 3
    assert replacement_event["quantity_after"] == 4
    result_event = next(
        event for event in game.events if event["event"] == "does_machines_level_three_resolved"
    )
    assert result_event["result"]["counters"] == 4


@pytest.mark.parametrize("invalidation", ["leaves", "controller", "not_artifact"])
def test_level_three_trigger_skips_resolution_when_its_target_becomes_illegal(invalidation):
    game, source, _facts, targets = _game(artifacts=("Sewer-veillance Cam",))
    source.class_level = 3
    target = targets["Sewer-veillance Cam"]
    game.transition_to(TurnStep.BEGINNING_OF_COMBAT)
    game._begin_priority_window()
    ability = game.stack[-1]

    if invalidation == "leaves":
        game.move_object(target, "graveyard", reason="synthetic target legality check")
    elif invalidation == "controller":
        game.change_controller(target, 1)
    else:
        target.type_line_override = "Creature â€” Robot"

    _resolve_top(game)

    assert target.counters.get("+1/+1", 0) == 0
    assert not any(
        event["event"] == "does_machines_level_three_resolved"
        and event["stack_object_id"] == ability.object_id
        for event in game.events
    )
    assert any(
        event["event"] == "does_machines_level_three_resolution_skipped"
        and event["stack_object_id"] == ability.object_id
        and event["reason"] == "all_targets_illegal"
        for event in game.events
    )
    assert not any(
        event["event"] == "trigger_resolved" and event["stack_object_id"] == ability.object_id
        for event in game.events
    )
    snapshot = game.snapshot()
    assert ("trigger_resolved", ability.event.event_id) not in _authoritative_execution_index(
        snapshot
    )


def test_level_three_trigger_resolves_after_source_leaves_play():
    game, source, _facts, targets = _game(artifacts=("Sewer-veillance Cam",))
    source.class_level = 3
    target = targets["Sewer-veillance Cam"]
    game.transition_to(TurnStep.BEGINNING_OF_COMBAT)
    game._begin_priority_window()
    ability = game.stack[-1]
    game.move_object(source, "graveyard", reason="synthetic source departure")

    _resolve_top(game)

    assert target.counters["+1/+1"] == 3
    assert any(
        event["event"] == "trigger_resolved" and event["stack_object_id"] == ability.object_id
        for event in game.events
    )
    assert ("trigger_resolved", ability.event.event_id) in _authoritative_execution_index(
        game.snapshot()
    )


def test_newly_animated_artifact_remains_summoning_sick_and_cannot_attack():
    game, source, facts, _targets = _game()
    source.class_level = 3
    target = game.create_permanent(facts["Sewer-veillance Cam"], 0)
    assert target.summoning_sick

    game.transition_to(TurnStep.BEGINNING_OF_COMBAT)
    game._begin_priority_window()
    _resolve_top(game)
    game.transition_to(TurnStep.DECLARE_ATTACKERS)

    assert target.is_creature and target.summoning_sick
    assert all(
        target.object_id not in action.attacker_ids for action in game.legal_attack_options(0)
    )


def test_animated_artifact_can_block_as_a_creature():
    game, source, facts, _targets = _game()
    source.class_level = 3
    blocker = game.create_permanent(facts["Sewer-veillance Cam"], 0)
    attacker = game.create_permanent(facts["Fugitive Droid"], 1, summoning_sick=False)
    game.transition_to(TurnStep.BEGINNING_OF_COMBAT)
    game._begin_priority_window()
    _resolve_top(game)
    game._step = TurnStep.DECLARE_BLOCKERS
    game._combat_attackers = (attacker.object_id,)
    attack = ActionOption(
        ActionKind.DECLARE_ATTACKERS,
        1,
        attacker_ids=(attacker.object_id,),
    )

    assert blocker.summoning_sick
    assert game.can_block(attacker, blocker, 0)
    assert any(
        (attacker.object_id, blocker.object_id) in option.blocks
        for option in game.legal_block_options(attack, 0)
    )
    assert game.generate_blocks([attacker], 0, log_rejections=False) == {
        attacker.object_id: blocker
    }


def test_animation_preserves_types_counters_and_temporary_base_stat_modifier():
    game, source, _facts, targets = _game(artifacts=("Sewer-veillance Cam",))
    source.class_level = 3
    target = targets["Sewer-veillance Cam"]
    original_types = set(target.type_line.replace("â€”", " ").replace("ï¿½", " ").split())
    game.place_counters(target, "+1/+1", 2, source_card="Synthetic", oracle_fragment="synthetic")
    game.apply_pt_modifier(
        target,
        1,
        0,
        duration="until_end_of_turn",
        source_card="Synthetic",
        oracle_fragment="synthetic",
    )
    game.transition_to(TurnStep.BEGINNING_OF_COMBAT)
    game._begin_priority_window()
    _resolve_top(game)

    resulting_types = set(target.type_line.replace("â€”", " ").replace("ï¿½", " ").split())
    assert original_types <= resulting_types
    assert {"Artifact", "Creature", "Robot"} <= resulting_types
    assert target.counters["+1/+1"] == 5
    assert (target.power, target.toughness) == (6, 5)

    game._perform_cleanup()
    assert target.counters["+1/+1"] == 5
    assert (target.power, target.toughness) == (5, 5)
