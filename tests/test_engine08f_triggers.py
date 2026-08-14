import pytest

from tmnt_design_studio.engine07 import (
    CardFact,
    Game,
    RulesEventKind,
    TriggeredAbilityObject,
    TriggerEffect,
)

PLAINS = CardFact("Plains", "", 0, "Basic Land — Plains", "({T}: Add {W}.)")
BEAR = CardFact("Bear", "{1}{W}", 2, "Creature — Bear", power=2, toughness=2)
ALLY = CardFact(
    "Alliance Test",
    "{1}{W}",
    2,
    "Creature — Ally",
    "Alliance — Whenever another creature you control enters, this creature gets +1/+0 "
    "until end of turn.",
    power=2,
    toughness=2,
)


def game() -> Game:
    deck = [PLAINS] * 60
    current = Game((deck, deck), seed=83)
    current.begin_turn()
    return current


def test_creature_event_creates_pending_and_stack_objects_before_resolution(monkeypatch):
    current = game()
    source = current.create_permanent(ALLY, 0, summoning_sick=False)
    entering = current.create_permanent(BEAR, 0, summoning_sick=False)
    monkeypatch.setattr(current, "_drain_triggered_abilities", lambda: None)

    current._process_creature_entered_triggers(entering)

    assert current.pending_triggers == []
    assert len(current.stack) == 1
    ability = current.stack[-1]
    assert isinstance(ability, TriggeredAbilityObject)
    assert ability.source_id == source.object_id
    assert ability.source_card is ALLY
    assert ability.event.kind is RulesEventKind.CREATURE_ENTERED
    assert ability.event.subject_ids == (entering.object_id,)
    assert ability.effect is TriggerEffect.ALLIANCE_PT
    assert source.power == 2
    current.resolve_top_of_stack()
    assert source.power == 3


def test_triggered_ability_exists_independently_after_its_source_leaves():
    current = game()
    source = current.create_permanent(ALLY, 0, summoning_sick=False)
    entering = current.create_permanent(BEAR, 0, summoning_sick=False)
    event = current._new_rules_event(RulesEventKind.CREATURE_ENTERED, 0, (entering.object_id,))
    current._enqueue_trigger(event, source, ALLY.oracle_text, TriggerEffect.ALLIANCE_PT)
    current._put_pending_triggers_on_stack()
    current.destroy(source)

    ability = current.stack[-1]
    assert isinstance(ability, TriggeredAbilityObject)
    assert ability.source_card is ALLY
    current.resolve_top_of_stack()

    assert current.stack == []
    assert any(
        item["event"] == "trigger_resolved" and item["source"] == ALLY.name
        for item in current.events
    )


def test_simultaneous_triggers_use_apnap_stack_order_and_deterministic_source_order():
    current = game()
    active_first = current.create_permanent(ALLY, 0, summoning_sick=False)
    active_second = current.create_permanent(ALLY, 0, summoning_sick=False)
    nonactive = current.create_permanent(ALLY, 1, summoning_sick=False)
    entering = current.create_permanent(BEAR, 0, summoning_sick=False)
    event = current._new_rules_event(RulesEventKind.CREATURE_ENTERED, 0, (entering.object_id,))
    for source in (active_first, active_second, nonactive):
        current._enqueue_trigger(event, source, ALLY.oracle_text, TriggerEffect.ALLIANCE_PT)

    current._put_pending_triggers_on_stack()

    assert [entry.source_id for entry in current.stack] == [
        active_second.object_id,
        active_first.object_id,
        nonactive.object_id,
    ]
    assert current.stack[-1].controller == 1
    current._drain_triggered_abilities()
    assert (active_first.power, active_second.power, nonactive.power) == (3, 3, 3)


def test_triggered_ability_resolves_above_existing_spell_without_moving_the_spell():
    current = game()
    for _ in range(2):
        current.create_permanent(PLAINS, 0, summoning_sick=False)
    current.set_hand_for_testing(0, [BEAR])
    spell = current.announce_spell(0, current.players[0].hand[0])
    assert spell is not None
    source = current.create_permanent(ALLY, 0, summoning_sick=False)
    event = current._new_rules_event(RulesEventKind.LIFE_GAINED, 0, ())
    current._enqueue_trigger(event, source, ALLY.oracle_text, TriggerEffect.ALLIANCE_PT)
    current._put_pending_triggers_on_stack()

    assert current.stack[0] is spell
    assert isinstance(current.stack[-1], TriggeredAbilityObject)
    current.resolve_top_of_stack()
    assert current.stack == [spell]
    current.resolve_top_of_stack()
    assert current.stack == []


def test_fabricated_trigger_stack_object_is_rejected_by_resolution_and_invariants():
    current = game()
    source = current.create_permanent(ALLY, 0, summoning_sick=False)
    event = current._new_rules_event(RulesEventKind.LIFE_GAINED, 0, ())
    fake = TriggeredAbilityObject(
        "object-fake",
        0,
        source.object_id,
        ALLY,
        ALLY.oracle_text,
        TriggerEffect.ALLIANCE_PT,
        event,
    )
    current.stack.append(fake)

    with pytest.raises(ValueError, match="not authoritative"):
        current.resolve_top_of_stack()
    with pytest.raises(AssertionError, match="unregistered"):
        current.check_invariants()


def test_existing_trigger_paths_emit_deterministic_pending_stack_resolved_telemetry():
    first = game()
    second = game()
    for current in (first, second):
        current.create_permanent(ALLY, 0, summoning_sick=False)
        entering = current.create_permanent(BEAR, 0, summoning_sick=False)
        current._process_creature_entered_triggers(entering)

    def trigger_events(current):
        return [
            event
            for event in current.events
            if event["event"]
            in {"rules_event", "trigger_pending", "trigger_stacked", "trigger_resolved"}
        ]

    assert trigger_events(first) == trigger_events(second)
    assert [event["event"] for event in trigger_events(first)] == [
        "rules_event",
        "trigger_pending",
        "trigger_stacked",
        "trigger_resolved",
    ]
