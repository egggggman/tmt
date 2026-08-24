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
FRAGMENT = "Whenever another permanent leaves the battlefield, put a +1/+1 counter on Test Watcher."
WATCHER = CardFact(
    "Test Watcher",
    "{2}{B}",
    3,
    "Creature — Mutant",
    FRAGMENT,
    power=3,
    toughness=3,
    oracle_id="permanent-left-counter-fixture",
)
BEAR = CardFact("Bear", "{1}{G}", 2, "Creature — Bear", power=2, toughness=2)
RELIC = CardFact("Relic", "{1}", 1, "Artifact")
REMOVAL = CardFact(
    "Bounded Removal",
    "{1}{B}",
    2,
    "Instant",
    "Destroy target artifact, enchantment, or creature with power 4 or greater.",
)


def game():
    current = Game(([LAND] * 20, [LAND] * 20), seed=151)
    current.begin_turn()
    watcher = current.create_permanent(WATCHER, 0)
    return current, watcher


def pass_priority(current):
    while current.priority_state is not None:
        if current.priority_state.resolution_pending:
            current.process_priority_resolution()
        else:
            current.execute_priority_action(
                current.legal_priority_actions(current.priority_state.player_index)[0]
            )


def stack_departure_triggers(current):
    current.check_state_based_actions()
    return tuple(
        item
        for item in current.stack
        if isinstance(item, TriggeredAbilityObject)
        and item.effect is TriggerEffect.PERMANENT_LEFT_SELF_COUNTER
    )


def catalog():
    return load_card_data(
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json",
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json",
    )


def test_exact_oracle_grammar_is_generic_and_fully_supported():
    interpreter = CardInterpreter()
    assert interpreter.permanent_left_self_counter_semantic_coverage(
        WATCHER, FRAGMENT
    ) == SemanticCoverage(True, True, True, ())
    renamed = replace(
        WATCHER,
        name="Renamed Watcher",
        oracle_text=FRAGMENT.replace("Test Watcher", "Renamed Watcher"),
    )
    assert interpreter.permanent_left_self_counter_semantic_coverage(
        renamed, renamed.oracle_text
    ) == SemanticCoverage(True, True, True, ())


def test_authorized_this_source_representation_is_fully_supported():
    fragment = FRAGMENT.replace("Test Watcher", "this source")
    assert CardInterpreter().permanent_left_self_counter_semantic_coverage(
        WATCHER, fragment
    ) == SemanticCoverage(True, True, True, ())


def test_literal_this_permanent_is_not_recognized_as_this_action():
    fragment = FRAGMENT.replace("Test Watcher", "this permanent")
    assert (
        CardInterpreter().permanent_left_self_counter_semantic_coverage(WATCHER, fragment) is None
    )


@pytest.mark.parametrize("type_line", ["Instant", "Sorcery"])
def test_nonpermanent_card_source_is_recognized_but_not_executable(type_line):
    card = replace(WATCHER, type_line=type_line)
    assert CardInterpreter().permanent_left_self_counter_semantic_coverage(
        card, FRAGMENT
    ) == SemanticCoverage(
        False,
        False,
        False,
        ("permanent_left_counter_source_is_not_a_permanent",),
    )


@pytest.mark.parametrize(
    "type_line",
    [
        "Artifact",
        "Battle — Siege",
        "Creature — Mutant",
        "Enchantment",
        "Land",
        "Planeswalker — Turtle",
    ],
)
def test_represented_permanent_card_types_are_executable(type_line):
    card = replace(WATCHER, type_line=type_line)
    assert CardInterpreter().permanent_left_self_counter_semantic_coverage(
        card, FRAGMENT
    ) == SemanticCoverage(True, True, True, ())


@pytest.mark.parametrize(
    "fragment",
    [
        "Whenever this permanent leaves the battlefield, put a +1/+1 counter on Test Watcher.",
        "Whenever another creature leaves the battlefield, put a +1/+1 counter on Test Watcher.",
        "Whenever another permanent dies, put a +1/+1 counter on Test Watcher.",
        "Whenever one or more other permanents leave the battlefield, put a +1/+1 "
        "counter on Test Watcher.",
        "Whenever another permanent an opponent controls leaves the battlefield, put a "
        "+1/+1 counter on Test Watcher.",
        "Whenever another permanent leaves the battlefield, you may put a +1/+1 counter "
        "on Test Watcher.",
        "Whenever another permanent leaves the battlefield, put two +1/+1 counters on "
        "Test Watcher.",
        "Whenever another permanent leaves the battlefield, put a charge counter on Test Watcher.",
        "Whenever another permanent leaves the battlefield, put a +1/+1 counter on Other Watcher.",
    ],
)
def test_near_neighbor_grammar_remains_unsupported(fragment):
    coverage = CardInterpreter().permanent_left_self_counter_semantic_coverage(WATCHER, fragment)
    if fragment.endswith("Other Watcher."):
        assert coverage == SemanticCoverage(
            False, False, False, ("permanent_left_counter_source_mismatch",)
        )
    else:
        assert coverage is None


def test_authoritative_corpus_membership_is_one_oracle_object_and_four_prints():
    cards = catalog().cards
    members = []
    interpreter = CardInterpreter()
    for card in cards:
        for fragment in interpreter.fragments(card):
            coverage = interpreter.permanent_left_self_counter_semantic_coverage(card, fragment)
            if coverage is not None and coverage.fully_supported:
                members.append((card.oracle_id, card.name, card.set_code, card.collector_number))
    assert len(members) == 4
    assert {item[0] for item in members} == {"b7ee76bf-d15a-489e-8f05-414788f8f649"}
    assert {item[1] for item in members} == {"Super Shredder"}
    assert {item[2] for item in members} == {"tmt"}
    assert {item[3] for item in members} == {"83", "217", "285", "295"}


@pytest.mark.parametrize(
    ("victim", "destination"),
    [(BEAR, "graveyard"), (BEAR, "hand"), (BEAR, "library"), (RELIC, "graveyard")],
)
def test_any_other_supported_permanent_departure_triggers_once(victim, destination):
    current, watcher = game()
    departing = current.create_permanent(victim, 1)
    current.move_object(departing, destination, reason="departure_probe")

    abilities = stack_departure_triggers(current)
    assert len(abilities) == 1
    ability = abilities[0]
    assert ability.event.kind is RulesEventKind.PERMANENT_LEFT
    assert ability.event.subject_ids == (departing.object_id,)
    assert ability.source_id == watcher.object_id
    assert current.priority_state is not None
    assert watcher.counters.get("+1/+1", 0) == 0

    pass_priority(current)

    assert watcher.counters["+1/+1"] == 1
    assert (watcher.power, watcher.toughness) == (4, 4)
    names = [item["event"] for item in current.events]
    assert names.index("zone_changed") < names.index("trigger_stacked")
    assert names.index("trigger_stacked") < names.index("priority_granted")
    assert names.index("priority_passed") < names.index("permanent_left_self_counter_resolved")
    assert names.index("permanent_left_self_counter_resolved") < names.index("trigger_resolved")
    current.check_invariants()


def test_source_own_departure_does_not_trigger_itself():
    current, watcher = game()
    current.move_object(watcher, "graveyard", reason="source_departure")
    current.check_state_based_actions()
    assert not current.pending_triggers
    assert not current.stack
    assert not any(item["event"] == "trigger_pending" for item in current.events)


def test_destroyed_creature_departure_triggers_from_battlefield_to_graveyard():
    current, watcher = game()
    victim = current.create_permanent(BEAR, 1)

    current.destroy(victim, state_based_action="destroy_probe")
    ability = stack_departure_triggers(current)[0]

    assert ability.event.kind is RulesEventKind.PERMANENT_LEFT
    assert ability.event.subject_ids == (victim.object_id,)
    assert any(
        item["event"] == "zone_changed"
        and item.get("source_object_id") == victim.object_id
        and item.get("source_zone") == "battlefield"
        and item.get("destination_zone") == "graveyard"
        for item in current.events
    )
    pass_priority(current)
    assert watcher.counters["+1/+1"] == 1


def test_multiple_simultaneous_departures_create_distinct_triggers_and_counters():
    current, watcher = game()
    victims = tuple(current.create_permanent(BEAR, 1) for _ in range(2))
    current.put_permanents_into_graveyard(victims, state_based_action="simultaneous_probe")
    abilities = stack_departure_triggers(current)
    assert len(abilities) == 2
    assert len({ability.event.event_id for ability in abilities}) == 2
    assert {ability.event.subject_ids[0] for ability in abilities} == {
        victim.object_id for victim in victims
    }

    pass_priority(current)

    assert watcher.counters["+1/+1"] == 2
    assert (watcher.power, watcher.toughness) == (5, 5)
    current.check_invariants()


def test_source_and_others_leaving_simultaneously_preserves_two_independent_triggers():
    current, watcher = game()
    victims = tuple(current.create_permanent(BEAR, 1) for _ in range(2))
    current.put_permanents_into_graveyard(
        (watcher,) + victims, state_based_action="simultaneous_source_departure"
    )
    abilities = stack_departure_triggers(current)
    assert len(abilities) == 2
    assert watcher.zone == "former"

    pass_priority(current)

    resolutions = [
        item for item in current.events if item["event"] == "permanent_left_self_counter_resolved"
    ]
    assert len(resolutions) == 2
    assert all(item["counter_applied"] is False for item in resolutions)
    current.check_invariants()


def test_frozen_trigger_controller_survives_source_control_change():
    current, watcher = game()
    victim = current.create_permanent(BEAR, 1)
    current.move_object(victim, "hand", reason="return")
    ability = stack_departure_triggers(current)[0]
    current.change_controller(watcher, 1)

    pass_priority(current)

    assert ability.controller == 0
    assert watcher.controller == 1
    assert watcher.counters["+1/+1"] == 1
    current.check_invariants()


def test_source_departure_after_trigger_leaves_effect_without_legal_counter_recipient():
    current, watcher = game()
    victim = current.create_permanent(BEAR, 1)
    current.move_object(victim, "graveyard", reason="first_departure")
    ability = stack_departure_triggers(current)[0]
    current.move_object(watcher, "hand", reason="source_removed_in_response")

    pass_priority(current)

    resolution = next(
        item
        for item in current.events
        if item["event"] == "permanent_left_self_counter_resolved"
        and item["stack_object_id"] == ability.object_id
    )
    assert resolution["counter_applied"] is False
    assert resolution["counters_before"] is None
    current.check_invariants()


def test_departure_during_parent_spell_resolution_waits_until_parent_finishes():
    current, watcher = game()
    current.create_permanent(LAND, 0, summoning_sick=False)
    current.create_permanent(LAND, 0, summoning_sick=False)
    target = current.create_permanent(replace(BEAR, power=4, toughness=4), 1, summoning_sick=False)
    hand = current.set_hand_for_testing(0, [REMOVAL])[0]
    spell = current.announce_spell(0, hand, target)
    assert spell is not None
    current._begin_priority_window()

    pass_priority(current)

    parent_resolved = next(
        index
        for index, item in enumerate(current.events)
        if item["event"] == "spell_resolved" and item.get("card") == REMOVAL.name
    )
    child_stacked = next(
        index
        for index, item in enumerate(current.events)
        if item["event"] == "trigger_stacked" and item.get("source") == watcher.card.name
    )
    assert parent_resolved < child_stacked
    assert watcher.counters["+1/+1"] == 1
    current.check_invariants()


@pytest.mark.parametrize(
    "tamper",
    [
        {"subject_ids": ("fabricated",), "source_id": "fabricated"},
        {"battlefield_authority": ()},
        {"last_known_battlefield": ()},
    ],
)
def test_stale_fabricated_or_relinked_departure_provenance_fails_closed(tamper):
    current, _watcher = game()
    victim = current.create_permanent(BEAR, 1)
    current.move_object(victim, "hand", reason="return")
    ability = stack_departure_triggers(current)[0]
    ability.event = replace(ability.event, **tamper)

    with pytest.raises(AssertionError, match="permanent-left counter trigger"):
        current.check_invariants()
    with pytest.raises(ValueError, match="permanent-left counter trigger"):
        current._resolve_triggered_ability(ability)


def test_borrowed_departure_event_cannot_authenticate_another_trigger():
    current, _watcher = game()
    first = current.create_permanent(BEAR, 1)
    second = current.create_permanent(BEAR, 1)
    current.move_object(first, "hand", reason="first")
    current.move_object(second, "hand", reason="second")
    first_ability, second_ability = stack_departure_triggers(current)
    second_ability.event = first_ability.event

    with pytest.raises(AssertionError, match="permanent-left counter trigger"):
        current.check_invariants()
