"""Synthetic regressions for April O'Neil's end-step card-type draw."""

from pathlib import Path

from tmnt_design_studio.conformance07 import semantic_key
from tmnt_design_studio.engine07 import (
    ActionKind,
    ActionOption,
    CardFact,
    CastKind,
    Game,
    TriggeredAbilityObject,
    TriggerEffect,
    TurnStep,
    load_facts,
)
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, load_catalog, reconcile_snapshot

ROOT = Path(__file__).resolve().parents[1]

LAND = CardFact("Island", "", 0, "Basic Land — Island")
APRIL_FRAGMENT = (
    "At the beginning of your end step, draw a card for each card type among spells "
    "you've cast this turn."
)
APRIL = CardFact(
    "April O'Neil, Hacktivist",
    "{2}{U}",
    3,
    "Legendary Creature — Human Scientist",
    APRIL_FRAGMENT,
    power=2,
    toughness=2,
    oracle_id="d379a919-02cd-46fd-a6ce-b66a77745ae7",
)
BEAR = CardFact(
    "Bear",
    "{1}",
    1,
    "Creature — Bear",
    power=2,
    toughness=2,
    oracle_id="00000000-0000-4000-8000-000000000001",
)
ARTIFACT_BEAR = CardFact(
    "Clockwork Bear",
    "{1}",
    1,
    "Artifact Creature — Construct",
    power=2,
    toughness=2,
    oracle_id="00000000-0000-4000-8000-000000000002",
)
PLAINS = CardFact("Plains", "", 0, "Basic Land — Plains")
SNEAK_FRAGMENT = (
    "Sneak {W} (You may cast this spell for {W} if you also return an unblocked attacker "
    "you control to hand during the declare blockers step. It enters tapped and attacking.)"
)
SNEAK_CREATURE = CardFact(
    "Synthetic Sneak Ninja",
    "{3}{W}",
    4,
    "Creature — Ninja",
    SNEAK_FRAGMENT,
    power=4,
    toughness=4,
    keywords=("Sneak",),
    oracle_id="00000000-0000-4000-8000-000000000003",
)


def make_game():
    game = Game(([LAND] * 40, [LAND] * 40), seed=4419)
    game.begin_turn()
    return game


def pass_priority(game):
    while game.priority_state is not None:
        state = game.priority_state
        if state.resolution_pending:
            game.process_priority_resolution()
        else:
            game.execute_priority_action(
                next(
                    option
                    for option in game.legal_priority_actions(state.player_index)
                    if option.kind is ActionKind.PASS_PRIORITY
                )
            )


def cast(game, player, fact, target=None):
    card = game.set_hand_for_testing(player, [fact])[0]
    spell = game.announce_spell(player, card, target)
    assert spell is not None
    if game.priority_state is None:
        game._begin_priority_window()
    pass_priority(game)
    return spell


def frozen_card(name):
    return load_facts(load_catalog(ROOT), {name})[name]


def begin_april_end_step(game, april):
    game._step = TurnStep.POSTCOMBAT_MAIN
    game.advance_step()
    abilities = [
        item
        for item in game.stack
        if isinstance(item, TriggeredAbilityObject)
        and item.effect is TriggerEffect.APRIL_END_STEP_DRAW
    ]
    assert len(abilities) == int(april is not None)
    if abilities:
        game._begin_priority_window()
    return abilities


def test_april_creates_authenticated_trigger_at_its_controllers_end_step():
    game = make_game()
    source = game.create_permanent(APRIL, 0, summoning_sick=False)
    for _ in range(3):
        game.create_permanent(LAND, 0, summoning_sick=False)
    card = game.set_hand_for_testing(0, [BEAR])[0]
    spell = game.announce_spell(0, card)
    assert spell is not None
    game._begin_priority_window()
    while game.priority_state is not None:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            game.execute_priority_action(
                next(
                    option
                    for option in game.legal_priority_actions(game.priority_state.player_index)
                    if option.kind.value == "pass_priority"
                )
            )

    triggers = begin_april_end_step(game, source)
    assert len(triggers) == 1
    assert triggers[0].effect.value == "april_end_step_draw"
    assert triggers[0].source_id == source.object_id
    assert triggers[0].oracle_fragment == APRIL_FRAGMENT
    assert len([item for item in game.stack if isinstance(item, TriggeredAbilityObject)]) == 1
    game._enqueue_trigger(
        triggers[0].event, source, APRIL_FRAGMENT, TriggerEffect.APRIL_END_STEP_DRAW
    )
    assert len([item for item in game.stack if isinstance(item, TriggeredAbilityObject)]) == 1
    initial = game.priority_state
    assert initial is not None and initial.player_index == 0
    game.execute_priority_action(
        next(
            option
            for option in game.legal_priority_actions(0)
            if option.kind is ActionKind.PASS_PRIORITY
        )
    )
    assert game.priority_state is not None
    assert game.priority_state.player_index == 1
    assert game.priority_state.epoch == initial.epoch
    game.execute_priority_action(
        next(
            option
            for option in game.legal_priority_actions(1)
            if option.kind is ActionKind.PASS_PRIORITY
        )
    )
    assert game.priority_state is not None and game.priority_state.resolution_pending
    game.process_priority_resolution()
    result = next(
        event for event in game.events if event["event"] == "april_end_step_draw_committed"
    )
    assert result["card_types"] == ["Creature"]
    assert result["requested_draw_count"] == len(result["drawn_object_ids"]) == 1


def test_zero_spell_types_draw_zero():
    game = make_game()
    april = game.create_permanent(APRIL, 0, summoning_sick=False)
    hand_before = len(game.players[0].hand)
    trigger = begin_april_end_step(game, april)[0]
    pass_priority(game)
    result = next(e for e in game.events if e["event"] == "april_end_step_draw_committed")
    assert result["requested_draw_count"] == 0
    assert result["drawn_object_ids"] == []
    assert len(game.players[0].hand) == hand_before
    assert result["source_id"] == trigger.source_id == april.object_id


def test_distinct_card_types_count_once_with_multitype_spell_and_repeated_casts():
    game = make_game()
    assert game._card_types_from_type_line("Legendary Artifact Creature — Construct") == {
        "Artifact",
        "Creature",
    }
    assert game._card_types_from_type_line("Legendary Planeswalker — April") == {"Planeswalker"}
    april = game.create_permanent(APRIL, 0, summoning_sick=False)
    for _ in range(3):
        game.create_permanent(LAND, 0, summoning_sick=False)
    spells = [cast(game, 0, BEAR), cast(game, 0, BEAR), cast(game, 0, ARTIFACT_BEAR)]
    trigger = begin_april_end_step(game, april)[0]
    pass_priority(game)

    cast_events = [
        event for event in game._rules_event_evidence if event.kind.value == "spell_cast"
    ]
    assert [event.source_id for event in cast_events] == [spell.object_id for spell in spells]
    assert all(
        event.player_index == 0
        and event.card_type_line == spell.card.type_line
        and event.card_oracle_id == spell.card.oracle_id
        for event, spell in zip(cast_events, spells, strict=True)
    )
    result = next(e for e in game.events if e["event"] == "april_end_step_draw_committed")
    assert result["source_id"] == trigger.source_id == april.object_id
    assert result["card_types"] == ["Artifact", "Creature"]
    assert result["requested_draw_count"] == len(result["drawn_object_ids"]) == 2
    assert len(result["cast_event_ids_by_type"]["Creature"]) == 3


def test_rejected_spell_announcement_creates_no_cast_event():
    game = make_game()
    card = game.set_hand_for_testing(0, [BEAR])[0]
    assert game.announce_spell(0, card) is None
    assert not [event for event in game._rules_event_evidence if event.kind.value == "spell_cast"]


def test_sneak_announcement_creates_one_authenticated_cast_event():
    game = make_game()
    card = game.set_hand_for_testing(0, [SNEAK_CREATURE])[0]
    game.create_permanent(PLAINS, 0, summoning_sick=False)
    attacker = game.create_permanent(BEAR, 0, summoning_sick=False)
    game.advance_to(TurnStep.DECLARE_ATTACKERS)
    game.execute_attack_action(
        ActionOption(ActionKind.DECLARE_ATTACKERS, 0, attacker_ids=(attacker.object_id,))
    )
    game.execute_block_action(ActionOption(ActionKind.DECLARE_BLOCKERS, 1))
    option = next(
        choice
        for choice in game.legal_sneak_actions(0)
        if choice.kind is ActionKind.CAST and choice.object_id == card.object_id
    )
    assert game.execute_sneak_action(option)

    spell = game.stack[-1]
    cast_events = [
        event
        for event in game._rules_event_evidence
        if event.kind.value == "spell_cast" and event.source_id == spell.object_id
    ]
    assert len(cast_events) == 1
    event = cast_events[0]
    assert event.player_index == spell.controller == 0
    assert event.subject_ids == (spell.object_id,)
    assert event.card_oracle_id == spell.card.oracle_id == SNEAK_CREATURE.oracle_id
    assert event.card_type_line == spell.card.type_line == SNEAK_CREATURE.type_line


def test_april_departure_before_trigger_and_after_trigger_boundaries():
    absent = make_game()
    source = absent.create_permanent(APRIL, 0, summoning_sick=False)
    absent.move_object(source, "graveyard", reason="synthetic_departure_before_end_step")
    assert begin_april_end_step(absent, None) == []

    present = make_game()
    april = present.create_permanent(APRIL, 0, summoning_sick=False)
    trigger = begin_april_end_step(present, april)[0]
    present.move_object(april, "graveyard", reason="synthetic_departure_after_trigger")
    pass_priority(present)
    result = next(e for e in present.events if e["event"] == "april_end_step_draw_committed")
    assert result["source_id"] == trigger.source_id == april.object_id


def test_april_entering_after_end_step_begins_does_not_trigger_retroactively():
    game = make_game()
    game._step = TurnStep.POSTCOMBAT_MAIN
    game.advance_step()
    game.create_permanent(APRIL, 0, summoning_sick=False)
    assert not any(
        isinstance(item, TriggeredAbilityObject)
        and item.effect is TriggerEffect.APRIL_END_STEP_DRAW
        for item in game.stack
    )


def test_april_execution_reconciles_with_authenticated_spell_cast_lineage():
    game = make_game()
    april = game.create_permanent(APRIL, 0, summoning_sick=False)
    game.create_permanent(LAND, 0, summoning_sick=False)
    spell = cast(game, 0, BEAR)
    trigger = begin_april_end_step(game, april)[0]
    pass_priority(game)
    snapshot = game.snapshot()
    key = semantic_key(april.card.oracle_id, 0, 0, APRIL_FRAGMENT)
    snapshot["stage002_presence"] = [
        {
            "semantic_key": key,
            "oracle_fragment": APRIL_FRAGMENT,
            "origin": "deck_card",
            "object_ids": [april.object_id],
            "is_token": False,
        }
    ]
    manifest = {
        "decks": [
            {
                "cards": [
                    {
                        "fragments": [
                            {
                                "semantic_key": key,
                                "oracle_fragment": APRIL_FRAGMENT,
                            }
                        ]
                    }
                ]
            }
        ]
    }
    report = reconcile_snapshot(
        GameSpec(
            "synthetic-april",
            "synthetic",
            4419,
            "canonical",
            (DeckSpec("A", ""), DeckSpec("B", "")),
        ),
        snapshot,
        manifest,
    )
    assert report["stop_records"] == []
    references = [
        ref for ref in snapshot["conformance"]["executed_references"] if ref["semantic_key"] == key
    ]
    assert len(references) == 1
    assert references[0]["source_id"] == trigger.source_id == april.object_id
    assert spell.object_id in [
        event.source_id for event in game._rules_event_evidence if event.kind.value == "spell_cast"
    ]


def test_countered_spell_remains_in_april_cast_history():
    game = make_game()
    april = game.create_permanent(APRIL, 0, summoning_sick=False)
    for _ in range(3):
        game.create_permanent(LAND, 0, summoning_sick=False)
        game.create_permanent(LAND, 1, summoning_sick=False)
    creature_card = game.set_hand_for_testing(0, [BEAR])[0]
    creature_spell = game.announce_spell(0, creature_card)
    assert creature_spell is not None
    game._begin_priority_window()
    game.execute_priority_action(
        next(
            option
            for option in game.legal_priority_actions(0)
            if option.kind is ActionKind.PASS_PRIORITY
        )
    )
    counter_card = game.set_hand_for_testing(1, [frozen_card("Ooze Spill")])[0]
    counter_option = next(
        option
        for option in game.legal_priority_actions(1)
        if option.kind is ActionKind.CAST and option.object_id == counter_card.object_id
    )
    assert game.execute_priority_action(counter_option)
    counter_spell = next(item for item in game.stack if item.card is counter_card.card)
    assert counter_spell is not None and counter_spell.cast_kind is CastKind.OOZE_SPILL
    game._begin_priority_window(priority_player=1)
    pass_priority(game)
    assert creature_spell.zone == "former"

    trigger = begin_april_end_step(game, april)[0]
    pass_priority(game)
    result = next(e for e in game.events if e["event"] == "april_end_step_draw_committed")
    assert result["card_types"] == ["Creature"]
    assert result["requested_draw_count"] == 1
    assert creature_spell.object_id in [
        item.source_id for item in game._rules_event_evidence if item.kind.value == "spell_cast"
    ]
    assert counter_spell.object_id in [
        item.source_id for item in game._rules_event_evidence if item.kind.value == "spell_cast"
    ]
    assert trigger.source_id == april.object_id


def test_spell_type_cast_during_response_is_counted_at_resolution():
    game = make_game()
    april = game.create_permanent(APRIL, 0, summoning_sick=False)
    target = game.create_permanent(BEAR, 0, summoning_sick=False)
    for _ in range(3):
        game.create_permanent(LAND, 0, summoning_sick=False)
    trigger = begin_april_end_step(game, april)[0]
    aura = frozen_card("Retro-Mutation")
    aura_card = game.set_hand_for_testing(0, [aura])[0]
    aura_spell = game.announce_spell(0, aura_card, target)
    assert aura_spell is not None
    game._begin_priority_window(priority_player=0)
    pass_priority(game)
    result = next(e for e in game.events if e["event"] == "april_end_step_draw_committed")
    assert trigger.object_id not in [item.object_id for item in game.stack]
    assert result["card_types"] == ["Enchantment"]
    assert result["requested_draw_count"] == 1
    cast_event = next(
        event for event in game._rules_events.values() if event.source_id == aura_spell.object_id
    )
    assert cast_event.event_id in result["cast_event_ids_by_type"]["Enchantment"]


def test_opponent_cast_during_april_priority_is_excluded():
    game = make_game()
    april = game.create_permanent(APRIL, 0, summoning_sick=False)
    target = game.create_permanent(BEAR, 1, summoning_sick=False)
    for _ in range(3):
        game.create_permanent(LAND, 1, summoning_sick=False)
    trigger = begin_april_end_step(game, april)[0]
    game.execute_priority_action(
        next(
            option
            for option in game.legal_priority_actions(0)
            if option.kind is ActionKind.PASS_PRIORITY
        )
    )
    aura_card = game.set_hand_for_testing(1, [frozen_card("Retro-Mutation")])[0]
    aura_spell = game.announce_spell(1, aura_card, target)
    assert aura_spell is not None
    game._begin_priority_window(priority_player=1)
    pass_priority(game)
    result = next(e for e in game.events if e["event"] == "april_end_step_draw_committed")
    assert trigger.object_id not in [item.object_id for item in game.stack]
    assert result["requested_draw_count"] == 0
    cast_event = next(
        item for item in game._rules_event_evidence if item.source_id == aura_spell.object_id
    )
    assert cast_event.player_index == 1


def test_previous_turn_spell_events_are_excluded_after_turn_boundary():
    game = make_game()
    april = game.create_permanent(APRIL, 0, summoning_sick=False)
    game.create_permanent(LAND, 0, summoning_sick=False)
    cast(game, 0, BEAR)
    old_april = game.players[0].battlefield[0] if game.players[0].battlefield else None
    if old_april is not None:
        game.move_object(old_april, "graveyard", reason="synthetic_leave_before_rollover")
    game._step = TurnStep.POSTCOMBAT_MAIN
    game.advance_step()  # end step
    game.advance_step()  # cleanup
    game.advance_step()  # next turn, active player 1
    game._step = TurnStep.POSTCOMBAT_MAIN
    game._active_player = 0
    assert game.turn == 2
    april = game.create_permanent(APRIL, 0, summoning_sick=False)
    trigger = begin_april_end_step(game, april)[0]
    pass_priority(game)
    result = next(e for e in game.events if e["event"] == "april_end_step_draw_committed")
    assert result["source_id"] == trigger.source_id
    assert result["card_types"] == []
    assert result["requested_draw_count"] == 0
