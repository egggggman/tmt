from pathlib import Path

import pytest

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import ActivatedEffectKind, CardInterpreter
from tmnt_design_studio.engine07 import Game, TurnStep, load_facts
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
