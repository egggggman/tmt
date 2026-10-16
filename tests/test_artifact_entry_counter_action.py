from dataclasses import replace
from pathlib import Path

import pytest

from tmnt_design_studio.card_interpreter07 import (
    CardInterpreter,
    TokenCreationProgram,
    TokenDefinition,
)
from tmnt_design_studio.engine07 import CardFact, Game, TriggeredAbilityObject, TriggerEffect
from tmnt_design_studio.smoke01 import run_smoke_game
from tmnt_design_studio.stage002 import DeckSpec, GameSpec

FRAGMENT = (
    "Whenever an artifact you control enters, put a +1/+1 counter on Donatello, Way with Machines."
)
SOURCE = CardFact(
    "Donatello, Way with Machines",
    "{2}{U}",
    3,
    "Creature - Turtle",
    FRAGMENT,
    power=2,
    toughness=2,
    oracle_id="donatello-way",
)
ARTIFACT = CardFact("Relic", "{1}", 1, "Artifact", oracle_id="relic")
NONARTIFACT = CardFact("Bear", "{1}{G}", 2, "Creature - Bear", power=2, toughness=2)
ARTIFACT_TOKEN = TokenDefinition("Robot", "Artifact Creature - Robot", power=1, toughness=1)
ROOT = Path(__file__).resolve().parents[1]


def test_exact_recognizer_and_neighbors_fail_closed():
    i = CardInterpreter()
    assert i.artifact_entry_self_counter_semantic_coverage(SOURCE, FRAGMENT).fully_supported
    short_fragment = FRAGMENT.replace("Donatello, Way with Machines", "Donatello")
    assert i.artifact_entry_self_counter_semantic_coverage(SOURCE, short_fragment).fully_supported
    assert (
        i.artifact_entry_self_counter_semantic_coverage(
            SOURCE, FRAGMENT.replace("artifact", "creature")
        )
        is None
    )


def test_artifact_entry_stacks_once_and_resolves_counter_on_source():
    g = Game(([SOURCE], [ARTIFACT]), seed=21)
    g.begin_turn()
    source = g.create_permanent(SOURCE, 0)
    entering = g.create_permanent(ARTIFACT, 0)
    g._process_creature_entered_triggers(entering, defer_triggers=True)
    abilities = [
        x
        for x in g.stack
        if isinstance(x, TriggeredAbilityObject)
        and x.effect is TriggerEffect.ARTIFACT_ENTRY_SELF_COUNTER
    ]
    assert len(abilities) == 1
    assert source.counters.get("+1/+1", 0) == 0
    g.resolve_top_of_stack()
    assert source.counters.get("+1/+1", 0) == 1


def test_entry_counter_uses_original_event_after_entering_artifact_leaves():
    def trace():
        g = Game(([SOURCE, ARTIFACT], [NONARTIFACT]), seed=334)
        g.begin_turn()
        source = g.create_permanent(SOURCE, 0)
        entering = g.create_permanent(ARTIFACT, 0)
        g._process_creature_entered_triggers(entering, defer_triggers=True)
        ability = g.stack[-1]
        assert isinstance(ability, TriggeredAbilityObject)
        assert ability.target_id is None  # The entering artifact is not a target.
        entry_id = ability.event.event_id
        entered_id = entering.object_id
        g.move_object(entering, "graveyard", reason="priority_response")
        assert source.counters == {}
        assert g.stack[-1] is ability
        g.resolve_top_of_stack()
        assert source.counters == {"+1/+1": 1}
        assert (source.power, source.toughness) == (3, 3)
        g.check_state_based_actions()
        assert g.is_authoritative(source, "battlefield")
        assert any(
            event["event"] == "artifact_entry_counter_resolved"
            and event["event_id"] == entry_id
            and event["entered_id"] == entered_id
            and event["source_id"] == source.object_id
            for event in g.events
        )
        return g.events

    assert trace() == trace()


def test_entry_counter_does_not_retarget_source_after_departure_or_reentry():
    g = Game(([SOURCE, ARTIFACT], [NONARTIFACT]), seed=335)
    g.begin_turn()
    source = g.create_permanent(SOURCE, 0)
    entering = g.create_permanent(ARTIFACT, 0)
    g._process_creature_entered_triggers(entering, defer_triggers=True)
    former = g.move_object(source, "graveyard", reason="priority_response")
    replacement = g.move_object(former, "battlefield", controller=0, reason="reentry")
    g.resolve_top_of_stack()
    assert replacement.object_id != source.object_id
    assert replacement.counters == {}
    assert any(
        event["event"] == "artifact_entry_counter_source_absent"
        and event["source_id"] == source.object_id
        for event in g.events
    )


def test_entry_counter_survives_control_and_type_changes_after_trigger():
    g = Game(([SOURCE, ARTIFACT], [NONARTIFACT]), seed=336)
    g.begin_turn()
    source = g.create_permanent(SOURCE, 0)
    entering = g.create_permanent(ARTIFACT, 0)
    g._process_creature_entered_triggers(entering, defer_triggers=True)
    g.change_controller(source, 1)
    entering.type_line_override = "Enchantment"
    g.change_controller(entering, 1)
    g.resolve_top_of_stack()
    assert source.controller == 1
    assert source.counters == {"+1/+1": 1}


def test_entry_counter_ability_loss_before_or_after_trigger():
    g = Game(([SOURCE, ARTIFACT], [NONARTIFACT]), seed=339)
    g.begin_turn()
    source = g.create_permanent(SOURCE, 0)
    source.ability_loss_timestamp = g._effect_timestamp()
    first = g.create_permanent(ARTIFACT, 0)
    g._process_creature_entered_triggers(first, defer_triggers=True)
    assert not g.stack
    source.ability_loss_timestamp = None
    second = g.create_permanent(ARTIFACT, 0)
    g._process_creature_entered_triggers(second, defer_triggers=True)
    assert len(g.stack) == 1
    source.ability_loss_timestamp = g._effect_timestamp()
    g.resolve_top_of_stack()
    assert source.counters == {"+1/+1": 1}


def test_entry_counter_two_entries_keep_separate_original_provenance():
    g = Game(([SOURCE, ARTIFACT], [NONARTIFACT]), seed=337)
    g.begin_turn()
    source = g.create_permanent(SOURCE, 0)
    first, second = (g.create_permanent(ARTIFACT, 0) for _ in range(2))
    g._process_creatures_entered_triggers((first, second), defer_triggers=True)
    g.move_object(first, "graveyard", reason="priority_response")
    g.move_object(second, "graveyard", reason="priority_response")
    g.resolve_top_of_stack()
    g.resolve_top_of_stack()
    assert source.counters == {"+1/+1": 2}
    resolved = [e for e in g.events if e["event"] == "artifact_entry_counter_resolved"]
    assert {e["entered_id"] for e in resolved} == {first.object_id, second.object_id}
    assert len({e["event_id"] for e in resolved}) == 2


def test_entry_counter_rejects_relinked_event_without_consuming_stack():
    g = Game(([SOURCE], [ARTIFACT]), seed=338)
    g.begin_turn()
    source = g.create_permanent(SOURCE, 0)
    entering = g.create_permanent(ARTIFACT, 0)
    g._process_creature_entered_triggers(entering, defer_triggers=True)
    ability = g.stack[-1]
    original = ability.event
    ability.event = replace(original, subject_ids=(source.object_id,))
    with pytest.raises(ValueError, match="original evidence"):
        g.resolve_top_of_stack()
    assert g.stack[-1] is ability
    assert source.counters == {}
    ability.event = original
    g.resolve_top_of_stack()
    assert source.counters == {"+1/+1": 1}


def test_wrong_controller_entry_does_not_trigger():
    g = Game(([SOURCE], [ARTIFACT]), seed=22)
    g.begin_turn()
    g.create_permanent(SOURCE, 0)
    entering = g.create_permanent(ARTIFACT, 1)
    g._process_creature_entered_triggers(entering, defer_triggers=True)
    assert not any(
        isinstance(x, TriggeredAbilityObject)
        and x.effect is TriggerEffect.ARTIFACT_ENTRY_SELF_COUNTER
        for x in g.stack
    )


def test_nonartifact_entry_does_not_trigger():
    g = Game(([SOURCE], [NONARTIFACT]), seed=25)
    g.begin_turn()
    g.create_permanent(SOURCE, 0)
    entering = g.create_permanent(NONARTIFACT, 0)
    g._process_creature_entered_triggers(entering, defer_triggers=True)
    assert not any(
        isinstance(x, TriggeredAbilityObject)
        and x.effect is TriggerEffect.ARTIFACT_ENTRY_SELF_COUNTER
        for x in g.stack
    )


def test_artifact_creature_token_entry_qualifies_by_type_and_controller():
    g = Game(([SOURCE], [NONARTIFACT]), seed=26)
    g.begin_turn()
    source = g.create_permanent(SOURCE, 0)
    g.create_tokens(
        0,
        TokenCreationProgram(ARTIFACT_TOKEN, 1),
        source_card="test",
        oracle_fragment="test token",
    )
    assert source.counters.get("+1/+1") == 1


def test_artifact_entry_replay_is_deterministic():
    def trace():
        g = Game(([SOURCE, ARTIFACT], [NONARTIFACT]), seed=27)
        g.begin_turn()
        g.create_permanent(SOURCE, 0)
        for _ in range(2):
            entering = g.create_permanent(ARTIFACT, 0)
            g._process_creature_entered_triggers(entering, defer_triggers=True)
        g.resolve_top_of_stack()
        g.resolve_top_of_stack()
        return g.events

    assert trace() == trace()


def test_multiple_entries_log_counters_and_update_power_toughness():
    g = Game(([SOURCE, ARTIFACT], [NONARTIFACT]), seed=23)
    g.begin_turn()
    source = g.create_permanent(SOURCE, 0)
    first = g.create_permanent(ARTIFACT, 0)
    second = g.create_permanent(ARTIFACT, 0)
    g._process_creature_entered_triggers(first, defer_triggers=True)
    g._process_creature_entered_triggers(second, defer_triggers=True)
    assert (
        sum(
            isinstance(x, TriggeredAbilityObject)
            and x.effect is TriggerEffect.ARTIFACT_ENTRY_SELF_COUNTER
            for x in g.stack
        )
        == 2
    )
    g.resolve_top_of_stack()
    g.resolve_top_of_stack()
    assert source.counters == {"+1/+1": 2}
    assert (source.power, source.toughness) == (4, 4)
    resolved = [x for x in g.events if x["event"] == "artifact_entry_counter_resolved"]
    assert len(resolved) == 2
    assert [x["quantity"] for x in resolved] == [1, 1]


def test_recovered_artifact_reentry_uses_the_same_trigger_path():
    g = Game(([SOURCE, ARTIFACT], [NONARTIFACT]), seed=24)
    g.begin_turn()
    source = g.create_permanent(SOURCE, 0)
    card = g.set_hand_for_testing(0, [ARTIFACT])[0]
    graveyard_card = g.move_object(card, "graveyard", reason="test_recovery")
    recovered = g.move_object(graveyard_card, "battlefield", controller=0, reason="test_recovery")
    assert recovered.card is ARTIFACT
    g._process_creature_entered_triggers(recovered, defer_triggers=True)
    g.resolve_top_of_stack()
    assert source.counters.get("+1/+1") == 1
    assert any(
        event["event"] == "artifact_entry_counter_resolved"
        and event["entered_id"] == recovered.object_id
        for event in g.events
    )


def test_real_donatello_seed_converts_artifact_entry_into_counter_payoff():
    result = run_smoke_game(
        ROOT,
        GameSpec(
            "donatello-shredder-way-3006",
            "donatello/shredder",
            3006,
            "donatello-first",
            (
                DeckSpec("donatello-p0.3a", "decks/donatello/PROTOTYPE_0.3a.txt"),
                DeckSpec("shredder-p0.3", "decks/shredder/PROTOTYPE_0.3.txt"),
            ),
        ),
    )
    assert result.get("error") is None
    assert any(
        event["event"] == "spell_cast" and event["card"] == "Donatello, Way with Machines"
        for event in result["events"]
    )
    assert (
        sum(event["event"] == "artifact_entry_counter_resolved" for event in result["events"]) >= 2
    )
    assert sum(event["event"] == "counters_placed" for event in result["events"]) >= 2
