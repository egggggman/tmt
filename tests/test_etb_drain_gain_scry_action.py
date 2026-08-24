import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import (
    CardFact,
    Game,
    RulesEventKind,
    TriggeredAbilityObject,
    TriggerEffect,
)
from tmnt_design_studio.semantic_coverage import SemanticCoverage

ROOT = Path(__file__).resolve().parents[1]
LAND = CardFact("Swamp", "", 0, "Basic Land — Swamp")
FRAGMENT = (
    "When this creature enters, each opponent loses 1 life and you gain 1 life. "
    "Scry 1. (Look at the top card of your library. You may put that card on the bottom.)"
)
DREAM = CardFact(
    "Renamed Dream Fixture",
    "{B}",
    1,
    "Creature — Beaver Nightmare",
    FRAGMENT,
    power=1,
    toughness=1,
    oracle_id="dream-fixture",
)
LIFE_GAIN_COUNTER = CardFact(
    "Growing Bear",
    "{1}{G}",
    2,
    "Creature — Bear",
    "Whenever you gain life, put a +1/+1 counter on Growing Bear.",
    power=2,
    toughness=2,
    oracle_id="growing-bear-fixture",
)


def game(*, library_size=12):
    current = Game(([LAND] * library_size, [LAND] * 20), seed=141)
    current.begin_turn()
    source = current.create_permanent(DREAM, 0)
    return current, source


def pass_priority(current):
    while current.priority_state is not None:
        if current.priority_state.resolution_pending:
            current.process_priority_resolution()
        else:
            option = current.legal_priority_actions(current.priority_state.player_index)[0]
            current.execute_priority_action(option)


def trigger(current, source):
    current._process_creature_entered_triggers(source)
    ability = current.stack[-1]
    assert isinstance(ability, TriggeredAbilityObject)
    return ability


def catalog():
    return load_card_data(
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json",
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json",
    )


def test_exact_oracle_grammar_is_generic_and_fully_supported():
    coverage = CardInterpreter().etb_drain_gain_scry_semantic_coverage(DREAM, FRAGMENT)
    assert coverage == SemanticCoverage(True, True, True, ())
    assert (
        CardInterpreter().etb_drain_gain_scry_semantic_coverage(
            replace(DREAM, name="No Card Name Dispatch"), FRAGMENT
        )
        == coverage
    )


@pytest.mark.parametrize(
    "fragment",
    [
        FRAGMENT.replace("loses 1 life", "loses 2 life"),
        FRAGMENT.replace("gain 1 life", "gain 2 life"),
        FRAGMENT.replace("Scry 1", "Scry 2"),
        FRAGMENT.replace("Scry 1.", "You may Scry 1."),
        "When this creature enters, scry 1. Each opponent loses 1 life and you gain 1 life.",
        "Whenever this creature attacks, each opponent loses 1 life and you gain 1 life. Scry 1.",
        "When this creature enters, target player loses 1 life and you gain 1 life. Scry 1.",
    ],
)
def test_near_neighbor_compounds_remain_unrecognized(fragment):
    assert CardInterpreter().etb_drain_gain_scry_semantic_coverage(DREAM, fragment) is None


def test_named_self_reference_is_generic_but_mismatched_name_is_not_executable():
    named = replace(
        DREAM, name="Night Visitor", oracle_text=FRAGMENT.replace("this creature", "Night Visitor")
    )
    mismatch = replace(
        named, oracle_text=named.oracle_text.replace("Night Visitor", "Other Visitor")
    )
    interpreter = CardInterpreter()
    assert interpreter.etb_drain_gain_scry_semantic_coverage(
        named, named.oracle_text
    ).fully_supported
    assert interpreter.etb_drain_gain_scry_semantic_coverage(
        mismatch, mismatch.oracle_text
    ) == SemanticCoverage(False, False, False, ("etb_drain_gain_scry_source_mismatch",))


def test_noncreature_exact_text_is_recognized_but_not_executable():
    relic = replace(DREAM, type_line="Artifact")
    assert CardInterpreter().etb_drain_gain_scry_semantic_coverage(
        relic, FRAGMENT
    ) == SemanticCoverage(False, False, False, ("etb_drain_gain_scry_source_is_not_a_creature",))


def test_authoritative_etb_uses_stack_priority_then_ordered_life_and_scry():
    current, source = game()
    top_before = current.players[0].library[-1].object_id
    ability = trigger(current, source)

    assert ability.effect is TriggerEffect.ETB_DRAIN_GAIN_SCRY
    assert ability.event.kind is RulesEventKind.CREATURE_ENTERED
    assert ability.event.subject_ids == (source.object_id,)
    assert current.priority_state is not None
    assert (current.players[0].life, current.players[1].life) == (20, 20)
    assert not current.etb_drain_gain_scry_evidence

    pass_priority(current)

    assert (current.players[0].life, current.players[1].life) == (21, 19)
    assert len(current.etb_drain_gain_scry_evidence) == 1
    evidence = current.etb_drain_gain_scry_evidence[0]
    assert evidence.stack_object_id == ability.object_id
    assert evidence.source_id == source.object_id
    assert evidence.opponent_life_before == 20
    assert evidence.opponent_life_after == 19
    assert evidence.controller_life_before == 20
    assert evidence.controller_life_after == 21
    assert evidence.scry_event_id == current.scry_evidence[-1].event_id
    assert current.scry_evidence[-1].inspected_ids == (top_before,)
    assert not evidence.terminal_after_life_loss
    names = [item["event"] for item in current.events]
    assert names.index("trigger_stacked") < names.index("priority_granted")
    assert names.index("life_lost") < names.index("life_gained")
    assert names.index("life_gained") < names.index("scry_committed")
    assert names.index("scry_committed") < names.index("trigger_resolved")
    current.check_invariants()


def test_terminal_life_loss_stops_gain_scry_and_trigger_completion():
    current, source = game()
    current.players[1].life = 1
    controller_before = current.players[0].life
    trigger(current, source)

    pass_priority(current)

    assert current.winner == 0
    assert current.players[1].life == 0
    assert current.players[0].life == controller_before
    assert not current.scry_evidence
    evidence = current.etb_drain_gain_scry_evidence[0]
    assert evidence.terminal_after_life_loss
    assert evidence.scry_event_id is None
    names = [item["event"] for item in current.events]
    assert "life_gained" not in names
    assert "scry_committed" not in names
    assert not any(
        item["event"] == "trigger_resolved"
        and item.get("stack_object_id") == evidence.stack_object_id
        for item in current.events
    )
    assert current.stack == []
    assert current.priority_state is None
    current.check_invariants()


def test_source_can_leave_after_trigger_without_losing_entry_provenance():
    current, source = game()
    current._process_creature_entered_triggers(source, defer_triggers=True)
    current.put_into_graveyard(source, state_based_action="legend_rule")
    current.check_state_based_actions()
    current._begin_priority_window()

    pass_priority(current)

    assert len(current.etb_drain_gain_scry_evidence) == 1
    assert current.etb_drain_gain_scry_evidence[0].source_id == source.object_id
    current.check_invariants()


def test_frozen_trigger_controller_survives_source_control_change_before_resolution():
    current, source = game()
    ability = trigger(current, source)
    current.players[0].battlefield.remove(source)
    source.controller = 1
    current.players[1].battlefield.append(source)

    current.check_invariants()
    pass_priority(current)

    assert ability.controller == 0
    assert source.controller == 1
    assert (current.players[0].life, current.players[1].life) == (21, 19)
    evidence = current.etb_drain_gain_scry_evidence[-1]
    assert evidence.controller == 0
    assert evidence.opponent == 1
    current.check_invariants()


def test_life_gain_trigger_is_delivered_only_after_compound_resolution_finishes():
    current, source = game()
    growing = current.create_permanent(LIFE_GAIN_COUNTER, 0)
    ability = trigger(current, source)

    current.execute_priority_action(current.legal_priority_actions(0)[0])
    current.execute_priority_action(current.legal_priority_actions(1)[0])
    current.process_priority_resolution()

    events = current.events
    parent_resolved = next(
        index
        for index, event in enumerate(events)
        if event["event"] == "trigger_resolved"
        and event.get("stack_object_id") == ability.object_id
    )
    child_stacked = next(
        index
        for index, event in enumerate(events)
        if event["event"] == "trigger_stacked" and event.get("stack_object_id") != ability.object_id
    )
    assert parent_resolved < child_stacked
    assert current.priority_state is not None
    assert len(current.stack) == 1
    assert growing.counters.get("+1/+1", 0) == 0

    pass_priority(current)

    assert growing.counters["+1/+1"] == 1
    current.check_invariants()


def test_simultaneous_life_gain_triggers_wait_for_parent_then_resolve_normally():
    current, source = game()
    growers = [current.create_permanent(LIFE_GAIN_COUNTER, 0) for _ in range(2)]
    ability = trigger(current, source)

    current.execute_priority_action(current.legal_priority_actions(0)[0])
    current.execute_priority_action(current.legal_priority_actions(1)[0])
    current.process_priority_resolution()

    parent_resolved = next(
        index
        for index, event in enumerate(current.events)
        if event["event"] == "trigger_resolved"
        and event.get("stack_object_id") == ability.object_id
    )
    child_indices = [
        index
        for index, event in enumerate(current.events)
        if event["event"] == "trigger_stacked" and event.get("stack_object_id") != ability.object_id
    ]
    assert len(child_indices) == 2
    assert all(parent_resolved < index for index in child_indices)
    assert len(current.stack) == 2
    assert all(permanent.counters.get("+1/+1", 0) == 0 for permanent in growers)

    pass_priority(current)

    assert all(permanent.counters["+1/+1"] == 1 for permanent in growers)
    current.check_invariants()


def test_fabricated_or_relinked_entry_provenance_fails_before_payload_mutation():
    current, source = game()
    ability = trigger(current, source)
    original = ability.event
    ability.event = replace(original, subject_ids=("fabricated",))
    before = current.authoritative_state_fingerprint()

    with pytest.raises(AssertionError, match="entry provenance"):
        current.check_invariants()
    with pytest.raises(ValueError, match="entry provenance"):
        current._resolve_triggered_ability(ability)

    assert current.authoritative_state_fingerprint() == before
    assert (current.players[0].life, current.players[1].life) == (20, 20)
    assert not current.scry_evidence
    ability.event = original


def test_simultaneous_triggers_remain_distinct_and_deterministic():
    def run():
        current = Game(([LAND] * 20, [LAND] * 20), seed=142)
        current.begin_turn()
        first = current.create_permanent(DREAM, 0)
        second = current.create_permanent(DREAM, 0)
        current._process_creatures_entered_triggers((first, second))
        pass_priority(current)
        current.check_invariants()
        return current.snapshot()

    first = run()
    second = run()
    assert first == second
    assert len(first["etb_drain_gain_scry"]) == 2
    assert len({item["event_id"] for item in first["etb_drain_gain_scry"]}) == 2
    assert len({item["stack_object_id"] for item in first["etb_drain_gain_scry"]}) == 2
    assert first["players"][0]["life"] == 22
    assert first["players"][1]["life"] == 18


def test_serialized_evidence_is_reconstructive_after_later_zone_changes():
    current, source = game()
    trigger(current, source)
    pass_priority(current)
    current.put_into_graveyard(source, state_based_action="later_removal")
    current.check_state_based_actions()

    snapshot = current.snapshot()
    record = snapshot["etb_drain_gain_scry"][0]
    assert record["source_id"] == source.object_id
    assert record["opponent_life_before"] - record["opponent_life_after"] == 1
    assert record["controller_life_after"] - record["controller_life_before"] == 1
    assert record["scry_event_id"] == snapshot["scry"][0]["event_id"]
    encoded = json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(encoded).hexdigest() == hashlib.sha256(encoded).hexdigest()
    current.check_invariants()


def test_authoritative_corpus_membership_is_dream_beavers_only():
    interpreter = CardInterpreter()
    members = []
    seen = set()
    for card in sorted(catalog().cards, key=lambda value: (value.name, value.oracle_id)):
        if card.oracle_id in seen:
            continue
        seen.add(card.oracle_id)
        for fragment in interpreter.fragments(card):
            coverage = interpreter.etb_drain_gain_scry_semantic_coverage(card, fragment)
            if coverage is not None:
                members.append((card.oracle_id, card.name, fragment, coverage.fully_supported))
    assert [(name, full) for _oracle_id, name, _fragment, full in members] == [
        ("Dream Beavers", True)
    ]
