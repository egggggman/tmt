"""Focused synthetic coverage for Ravenous Robots artifact-cast triggers."""

from pathlib import Path

from tmnt_design_studio.conformance07 import semantic_key
from tmnt_design_studio.engine07 import (
    ActionKind,
    CardFact,
    Game,
    TriggeredAbilityObject,
    TriggerEffect,
    load_facts,
)
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, load_catalog, reconcile_snapshot

ROOT = Path(__file__).resolve().parents[1]
CATALOG = load_catalog(ROOT)
RAVENOUS = load_facts(CATALOG, {"Ravenous Robots"})["Ravenous Robots"]
PIZZA = load_facts(CATALOG, {"Spicy Oatmeal Pizza"})["Spicy Oatmeal Pizza"]
OOZE_SPILL = load_facts(CATALOG, {"Ooze Spill"})["Ooze Spill"]
MOUNTAIN = CardFact("Mountain", "", 0, "Basic Land — Mountain")
ISLAND = CardFact("Island", "", 0, "Basic Land — Island")
ARTIFACT_CAST_FRAGMENT = (
    "Whenever you cast an artifact spell, create a 1/1 colorless Robot artifact creature token."
)
BEAR = CardFact("Synthetic Bear", "{1}", 1, "Creature — Bear", power=2, toughness=2)
ARTIFACT_BEAR = CardFact(
    "Synthetic Clockwork Bear", "{1}", 1, "Artifact Creature — Construct", power=2, toughness=2
)


def setup_cast(card_fact=PIZZA, *, robots=1, caster=0, active=0):
    game = Game(([MOUNTAIN] * 20, [MOUNTAIN] * 20), seed=8391)
    game.begin_turn()
    if active:
        game._active_player = active
    sources = [game.create_permanent(RAVENOUS, 0, summoning_sick=False) for _ in range(robots)]
    for _ in range(3):
        game.create_permanent(MOUNTAIN, caster, summoning_sick=False)
    card = game.set_hand_for_testing(caster, [card_fact])[0]
    spell = game.announce_spell(caster, card)
    assert spell is not None
    return game, sources, spell


def resolve_one_priority_cycle(game):
    if game.priority_state is None:
        game._begin_priority_window()
    for _ in range(2):
        state = game.priority_state
        assert state is not None and not state.resolution_pending
        option = next(
            option
            for option in game.legal_priority_actions(state.player_index)
            if option.kind is ActionKind.PASS_PRIORITY
        )
        assert game.execute_priority_action(option)
    assert game.priority_state is not None and game.priority_state.resolution_pending
    assert game.process_priority_resolution()


def test_ravenous_robots_triggers_for_normally_cast_spicy_oatmeal_pizza():
    game = Game(([MOUNTAIN] * 20, [MOUNTAIN] * 20), seed=8391)
    game.begin_turn()
    source = game.create_permanent(RAVENOUS, 0, summoning_sick=False)
    for _ in range(3):
        game.create_permanent(MOUNTAIN, 0, summoning_sick=False)
    card = game.set_hand_for_testing(0, [PIZZA])[0]
    spell = game.announce_spell(0, card)
    assert spell is not None

    cast_event = next(
        event
        for event in game._rules_events.values()
        if event.kind.value == "spell_cast" and event.source_id == spell.object_id
    )
    assert "Artifact" in game._card_types_from_type_line(cast_event.card_type_line)

    triggers = [
        item
        for item in game.stack
        if isinstance(item, TriggeredAbilityObject)
        and item.effect is TriggerEffect.CREATE_TOKEN
        and item.source_id == source.object_id
    ]
    assert len(triggers) == 1


def test_ravenous_artifact_spell_trigger_resolves_to_exact_robot_token():
    game, sources, spell = setup_cast()
    trigger = game.stack[-1]
    assert isinstance(trigger, TriggeredAbilityObject)
    assert trigger.event.kind.value == "spell_cast"
    assert trigger.event.source_id == spell.object_id
    assert trigger.event.card_oracle_id == PIZZA.oracle_id
    assert trigger.source_id == sources[0].object_id
    assert trigger.oracle_fragment == ARTIFACT_CAST_FRAGMENT
    assert trigger.controller == 0
    resolve_one_priority_cycle(game)
    tokens = [p for p in game.players[0].battlefield if p.is_token]
    assert len(tokens) == 1
    token = tokens[0]
    assert token.card.name == "Robot"
    assert token.type_line == "Artifact Creature — Robot"
    assert token.power == 1 and token.toughness == 1
    assert token.card.colors == ()
    assert game.stack[-1] is spell
    artifact_entry_ids = [item[2] for item in game._artifact_entries_this_turn]
    assert sources[0].object_id in artifact_entry_ids
    assert token.object_id in artifact_entry_ids


def test_artifact_creature_spell_triggers_and_nonartifact_spell_does_not():
    game, sources, spell = setup_cast(ARTIFACT_BEAR)
    assert spell.card.type_line == ARTIFACT_BEAR.type_line
    assert sum(isinstance(item, TriggeredAbilityObject) for item in game.stack) == 1
    other, _, _ = setup_cast(BEAR)
    assert not any(
        isinstance(item, TriggeredAbilityObject) and item.effect is TriggerEffect.CREATE_TOKEN
        for item in other.stack
    )


def test_opponent_artifact_cast_does_not_trigger_controller_robots():
    game, sources, spell = setup_cast(caster=1, active=1)
    assert spell.controller == 1
    assert not any(
        isinstance(item, TriggeredAbilityObject) and item.effect is TriggerEffect.CREATE_TOKEN
        for item in game.stack
    )


def test_robots_leaving_after_trigger_does_not_remove_trigger():
    game, sources, _spell = setup_cast()
    trigger = game.stack[-1]
    game.move_object(sources[0], "graveyard", reason="synthetic_source_departure")
    resolve_one_priority_cycle(game)
    assert any(p.is_token and p.card.name == "Robot" for p in game.players[0].battlefield)
    assert trigger.zone == "former"


def test_robots_entering_after_cast_does_not_trigger_retroactively():
    game, _, _spell = setup_cast(robots=0)
    game.create_permanent(RAVENOUS, 0, summoning_sick=False)
    assert not any(
        isinstance(item, TriggeredAbilityObject) and item.effect is TriggerEffect.CREATE_TOKEN
        for item in game.stack
    )


def test_artifact_permanent_entry_without_a_cast_does_not_trigger():
    game = Game(([MOUNTAIN] * 20, [MOUNTAIN] * 20), seed=8391)
    game.begin_turn()
    game.create_permanent(RAVENOUS, 0, summoning_sick=False)
    game.create_permanent(PIZZA, 0, summoning_sick=False)
    assert not any(
        isinstance(item, TriggeredAbilityObject) and item.effect is TriggerEffect.CREATE_TOKEN
        for item in game.stack
    )


def test_each_simultaneous_robots_source_creates_one_trigger_and_token():
    game, sources, _spell = setup_cast(robots=2)
    triggers = [
        item
        for item in game.stack
        if isinstance(item, TriggeredAbilityObject) and item.effect is TriggerEffect.CREATE_TOKEN
    ]
    assert len(triggers) == len(sources) == 2
    resolve_one_priority_cycle(game)
    resolve_one_priority_cycle(game)
    assert sum(p.is_token and p.card.name == "Robot" for p in game.players[0].battlefield) == 2


def test_artifact_cast_trigger_priority_is_two_player_and_epoch_bound():
    game, _sources, _spell = setup_cast()
    game._begin_priority_window()
    initial = game.priority_state
    assert initial is not None
    first = next(
        option
        for option in game.legal_priority_actions(initial.player_index)
        if option.kind is ActionKind.PASS_PRIORITY
    )
    assert game.execute_priority_action(first)
    second_state = game.priority_state
    assert second_state is not None
    assert second_state.player_index != initial.player_index
    assert second_state.epoch == initial.epoch
    second = next(
        option
        for option in game.legal_priority_actions(second_state.player_index)
        if option.kind is ActionKind.PASS_PRIORITY
    )
    assert game.execute_priority_action(second)
    assert game.priority_state is not None and game.priority_state.resolution_pending


def test_artifact_cast_trigger_reconciles_with_original_spell_event():
    game, sources, spell = setup_cast()
    trigger = game.stack[-1]
    resolve_one_priority_cycle(game)
    key = semantic_key(RAVENOUS.oracle_id, 0, 0, ARTIFACT_CAST_FRAGMENT)
    snapshot = game.snapshot()
    snapshot["stage002_presence"] = [
        {
            "semantic_key": key,
            "oracle_fragment": ARTIFACT_CAST_FRAGMENT,
            "origin": "deck_card",
            "object_ids": [sources[0].object_id],
            "is_token": False,
        }
    ]
    manifest = {
        "decks": [
            {
                "cards": [
                    {
                        "fragments": [
                            {"semantic_key": key, "oracle_fragment": ARTIFACT_CAST_FRAGMENT}
                        ]
                    }
                ]
            }
        ]
    }
    report = reconcile_snapshot(
        GameSpec(
            "synthetic-robots",
            "synthetic",
            8391,
            "canonical",
            (DeckSpec("A", ""), DeckSpec("B", "")),
        ),
        snapshot,
        manifest,
    )
    assert report["stop_records"] == []
    refs = [
        ref for ref in snapshot["conformance"]["executed_references"] if ref["semantic_key"] == key
    ]
    assert {ref["evidence_kind"] for ref in refs} == {"tokens_created", "trigger_resolved"}
    assert all(ref["source_id"] == trigger.source_id for ref in refs)
    assert spell.object_id == trigger.event.source_id


def test_artifact_cast_event_keeps_april_cast_history_compatible():
    game, _, spell = setup_cast()
    event = next(
        event
        for event in game._rules_events.values()
        if event.kind.value == "spell_cast" and event.source_id == spell.object_id
    )
    assert event.player_index == 0
    assert event.card_oracle_id == PIZZA.oracle_id
    assert "Artifact" in game._card_types_from_type_line(event.card_type_line)
    assert sum(1 for e in game._rules_event_evidence if e.event_id == event.event_id) == 1


def test_robot_token_definition_is_interpreted_from_frozen_oracle_text():
    game, _, _spell = setup_cast()
    program = game.interpreter.token_creation_program(ARTIFACT_CAST_FRAGMENT)
    assert program is not None and program.definition is not None
    assert program.definition.name == "Robot"
    assert program.definition.type_line == "Artifact Creature — Robot"
    assert program.definition.colors == ()
    assert program.definition.power == program.definition.toughness == 1


def test_trigger_uses_cast_event_once_even_when_event_delivery_is_repeated():
    game, sources, spell = setup_cast()
    event = next(
        event
        for event in game._rules_events.values()
        if event.kind.value == "spell_cast" and event.source_id == spell.object_id
    )
    game._process_artifact_spell_cast_triggers(event)
    assert (
        sum(
            isinstance(item, TriggeredAbilityObject)
            and item.effect is TriggerEffect.CREATE_TOKEN
            and item.source_id == sources[0].object_id
            for item in game.stack
        )
        == 1
    )


def test_cast_trigger_does_not_need_source_to_remain_on_battlefield_at_resolution():
    game, sources, _spell = setup_cast()
    game.move_object(sources[0], "graveyard", reason="synthetic_source_departure")
    resolve_one_priority_cycle(game)
    assert sum(p.is_token and p.card.name == "Robot" for p in game.players[0].battlefield) == 1


def test_countered_artifact_spell_keeps_original_cast_event_and_trigger_result():
    game, _sources, artifact_spell = setup_cast()
    resolve_one_priority_cycle(game)
    for _ in range(3):
        game.create_permanent(ISLAND, 1, summoning_sick=False)
    counter_card = game.set_hand_for_testing(1, [OOZE_SPILL])[0]
    if game.priority_state.player_index != 1:
        pass_option = next(
            option
            for option in game.legal_priority_actions(game.priority_state.player_index)
            if option.kind is ActionKind.PASS_PRIORITY
        )
        assert game.execute_priority_action(pass_option)
    counter_option = next(
        option
        for option in game.legal_priority_actions(1)
        if option.kind is ActionKind.CAST and option.object_id == counter_card.object_id
    )
    assert game.execute_priority_action(counter_option)
    resolve_one_priority_cycle(game)
    cast_event = next(
        event
        for event in game._rules_events.values()
        if event.kind.value == "spell_cast" and event.source_id == artifact_spell.object_id
    )
    assert cast_event.card_oracle_id == PIZZA.oracle_id
    assert artifact_spell.zone == "former"
    assert sum(p.is_token and p.card.name == "Robot" for p in game.players[0].battlefield) == 1
