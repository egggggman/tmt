import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter, TokenCreationProgram
from tmnt_design_studio.engine07 import (
    CardFact,
    Game,
    RulesEventKind,
    TriggeredAbilityObject,
    TriggerEffect,
)
from tmnt_design_studio.semantic_coverage import SemanticCoverage

ROOT = Path(__file__).resolve().parents[1]
LAND = CardFact("Island", "", 0, "Basic Land — Island")
ARTIFACT = CardFact("Test Relic", "{1}", 1, "Artifact", oracle_id="test-relic")
FRAGMENT = "When this source enters, if its controller controls an artifact, draw a card."
SOURCE = CardFact(
    "Tech Fixture",
    "{2}{U}",
    3,
    "Creature — Turtle Artificer",
    FRAGMENT,
    power=2,
    toughness=4,
    oracle_id="tech-fixture",
)
DIES_DRAW = CardFact(
    "Draw Child Fixture",
    "{1}",
    1,
    "Creature — Robot",
    "When this creature dies, draw a card.",
    power=1,
    toughness=1,
    oracle_id="draw-child-fixture",
)


def catalog():
    return load_card_data(
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json",
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json",
    )


def game(*, library_size=8, artifact=True):
    current = Game(([LAND] * library_size, [LAND] * 20), seed=1601)
    current.begin_turn()
    if artifact:
        current.create_permanent(ARTIFACT, 0)
    source = current.create_permanent(SOURCE, 0)
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
    assert isinstance(current.stack[-1], TriggeredAbilityObject)
    return current.stack[-1]


def test_exact_generic_and_established_named_normalization_are_fully_supported():
    interpreter = CardInterpreter()
    assert interpreter.etb_artifact_draw_semantic_coverage(SOURCE, FRAGMENT) == SemanticCoverage(
        True, True, True, ()
    )
    named_fragment = "When Tech Fixture enters, if you control an artifact, draw a card."
    assert interpreter.etb_artifact_draw_semantic_coverage(
        replace(SOURCE, oracle_text=named_fragment), named_fragment
    ) == SemanticCoverage(True, True, True, ())


@pytest.mark.parametrize(
    "fragment",
    [
        "When this source enters, if its controller controls a creature, draw a card.",
        "When this source enters, if its controller controls an artifact, draw two cards.",
        "When this source enters, unless its controller controls an artifact, draw a card.",
        "When this source enters, if its controller controls an artifact, you may draw a card.",
        "When this source enters, if an opponent controls an artifact, draw a card.",
        "When this source enters, if its controller controls two artifacts, draw a card.",
        "When this source enters, if its controller controls an artifact, "
        "search your library for a card.",
        "Whenever this source attacks, if its controller controls an artifact, draw a card.",
    ],
)
def test_near_neighbor_grammar_remains_unrecognized(fragment):
    assert CardInterpreter().etb_artifact_draw_semantic_coverage(SOURCE, fragment) is None


def test_unproven_normalization_and_mismatched_source_are_not_executable():
    interpreter = CardInterpreter()
    generic_you = "When this source enters, if you control an artifact, draw a card."
    wrong_name = "When Other Fixture enters, if you control an artifact, draw a card."
    assert interpreter.etb_artifact_draw_semantic_coverage(SOURCE, generic_you) == SemanticCoverage(
        False, False, False, ("etb_artifact_draw_source_or_condition_mismatch",)
    )
    assert interpreter.etb_artifact_draw_semantic_coverage(SOURCE, wrong_name) == SemanticCoverage(
        False, False, False, ("etb_artifact_draw_source_or_condition_mismatch",)
    )


def test_noncreature_source_is_recognized_but_not_executable():
    coverage = CardInterpreter().etb_artifact_draw_semantic_coverage(
        replace(SOURCE, type_line="Artifact"), FRAGMENT
    )
    assert coverage == SemanticCoverage(
        False, False, False, ("etb_artifact_draw_source_is_not_a_creature",)
    )


def test_condition_true_at_entry_and_resolution_draws_exactly_one_through_priority():
    current, source = game()
    hand_before = tuple(card.object_id for card in current.players[0].hand)
    ability = trigger(current, source)
    assert ability.effect is TriggerEffect.ETB_ARTIFACT_DRAW
    assert current.priority_state is not None
    assert tuple(card.object_id for card in current.players[0].hand) == hand_before

    pass_priority(current)

    assert len(current.players[0].hand) == len(hand_before) + 1
    resolved = [event for event in current.events if event["event"] == "etb_artifact_draw_resolved"]
    assert len(resolved) == 1
    assert resolved[0]["stack_object_id"] == ability.object_id
    assert resolved[0]["condition_met"] and resolved[0]["draw_succeeded"]
    names = [event["event"] for event in current.events]
    assert names.index("trigger_stacked") < names.index("priority_granted")
    assert names.index("etb_artifact_draw_resolved") < names.index("trigger_resolved")
    current.check_invariants()


def test_false_at_entry_creates_no_trigger_even_if_artifact_arrives_later():
    current, source = game(artifact=False)
    current._process_creature_entered_triggers(source)
    assert not current.stack and not current.pending_triggers
    current.create_permanent(ARTIFACT, 0)
    assert not current.stack and not current.pending_triggers
    assert not any(event["event"] == "etb_artifact_draw_resolved" for event in current.events)


def test_true_at_entry_but_false_at_resolution_does_not_draw():
    current, source = game()
    artifact = next(item for item in current.players[0].battlefield if item.card is ARTIFACT)
    trigger(current, source)
    current.put_into_graveyard(artifact)
    current.check_state_based_actions()
    before = len(current.players[0].hand)
    pass_priority(current)
    assert len(current.players[0].hand) == before
    record = next(
        event for event in current.events if event["event"] == "etb_artifact_draw_resolved"
    )
    assert not record["condition_met"] and not record["draw_succeeded"]
    current.check_invariants()


def test_entering_artifact_creature_counts_itself_and_artifact_token_counts():
    interpreter = CardInterpreter()
    artifact_source = replace(SOURCE, type_line="Artifact Creature — Turtle Artificer")
    current = Game(([LAND] * 8, [LAND] * 20), seed=1602)
    current.begin_turn()
    source = current.create_permanent(artifact_source, 0)
    before = len(current.players[0].hand)
    current._process_creature_entered_triggers(source)
    pass_priority(current)
    assert len(current.players[0].hand) == before + 1
    assert interpreter.etb_artifact_draw_semantic_coverage(
        artifact_source, FRAGMENT
    ).fully_supported

    token_game, token_source = game(artifact=False)
    token_game.create_tokens(
        0,
        TokenCreationProgram(CardInterpreter.PREDEFINED_TOKENS["food"], 1),
        source_card="Generic token maker",
        oracle_fragment="Create a Food token.",
    )
    before = len(token_game.players[0].hand)
    trigger(token_game, token_source)
    pass_priority(token_game)
    assert len(token_game.players[0].hand) == before + 1


def test_trigger_time_uses_evaluated_battlefield_type_not_printed_type():
    printed_artifact_game, printed_source = game(artifact=False)
    printed_artifact = printed_artifact_game.create_permanent(ARTIFACT, 0)
    printed_artifact.type_line_override = "Enchantment"
    printed_artifact_game._process_creature_entered_triggers(printed_source)
    assert not printed_artifact_game.stack and not printed_artifact_game.pending_triggers

    printed_nonartifact_game, nonartifact_source = game(artifact=False)
    printed_nonartifact = printed_nonartifact_game.create_permanent(
        replace(ARTIFACT, name="Printed Charm", type_line="Enchantment"), 0
    )
    printed_nonartifact.type_line_override = "Artifact"
    before = len(printed_nonartifact_game.players[0].hand)
    trigger(printed_nonartifact_game, nonartifact_source)
    pass_priority(printed_nonartifact_game)
    assert len(printed_nonartifact_game.players[0].hand) == before + 1


def test_entering_printed_artifact_uses_its_current_battlefield_characteristics():
    artifact_source = replace(SOURCE, type_line="Artifact Creature — Turtle Artificer")
    current = Game(([LAND] * 8, [LAND] * 20), seed=1604)
    current.begin_turn()
    source = current.create_permanent(artifact_source, 0)
    source.type_line_override = "Creature — Turtle Artificer"
    current._process_creature_entered_triggers(source)
    assert not current.stack and not current.pending_triggers


def test_resolution_rechecks_evaluated_types_and_can_use_a_new_artifact():
    current, source = game()
    original = next(item for item in current.players[0].battlefield if item.card is ARTIFACT)
    trigger(current, source)
    original.type_line_override = "Enchantment"
    before = len(current.players[0].hand)
    pass_priority(current)
    assert len(current.players[0].hand) == before

    replacement_game, replacement_source = game()
    original = next(
        item for item in replacement_game.players[0].battlefield if item.card is ARTIFACT
    )
    trigger(replacement_game, replacement_source)
    original.type_line_override = "Enchantment"
    new_artifact = replacement_game.create_permanent(
        replace(ARTIFACT, name="Printed Charm", type_line="Enchantment"), 0
    )
    new_artifact.type_line_override = "Artifact"
    before = len(replacement_game.players[0].hand)
    pass_priority(replacement_game)
    assert len(replacement_game.players[0].hand) == before + 1


def test_multiple_artifacts_use_mixed_current_characteristics():
    current, source = game(artifact=False)
    printed_artifact = current.create_permanent(ARTIFACT, 0)
    printed_artifact.type_line_override = "Enchantment"
    current_artifact = current.create_permanent(
        replace(ARTIFACT, name="Animated Charm", type_line="Enchantment"), 0
    )
    current_artifact.type_line_override = "Artifact Creature — Construct"
    ability = trigger(current, source)
    frozen = {item[0]: item[2] for item in ability.event.battlefield_characteristics}
    assert frozen[printed_artifact.object_id] == "Enchantment"
    assert frozen[current_artifact.object_id] == "Artifact Creature — Construct"
    pass_priority(current)
    current.check_invariants()


def test_multiple_artifacts_still_draw_only_one_and_frozen_controller_is_used():
    current, source = game()
    current.create_permanent(ARTIFACT, 0)
    before = len(current.players[0].hand)
    opponent_before = len(current.players[1].hand)
    ability = trigger(current, source)
    current.players[0].battlefield.remove(source)
    source.controller = 1
    current.players[1].battlefield.append(source)
    pass_priority(current)
    assert ability.controller == 0
    assert len(current.players[0].hand) == before + 1
    assert len(current.players[1].hand) == opponent_before


def test_artifact_controller_change_is_rechecked_at_resolution():
    current, source = game()
    artifact = next(item for item in current.players[0].battlefield if item.card is ARTIFACT)
    before = len(current.players[0].hand)
    trigger(current, source)
    current.players[0].battlefield.remove(artifact)
    artifact.controller = 1
    current.players[1].battlefield.append(artifact)
    pass_priority(current)
    assert len(current.players[0].hand) == before


def test_source_control_change_still_checks_frozen_controller_current_artifacts():
    current, source = game()
    original = next(item for item in current.players[0].battlefield if item.card is ARTIFACT)
    ability = trigger(current, source)
    current.players[0].battlefield.remove(source)
    source.controller = 1
    current.players[1].battlefield.append(source)
    current.players[0].battlefield.remove(original)
    original.controller = 1
    current.players[1].battlefield.append(original)
    replacement_artifact = current.create_permanent(
        replace(ARTIFACT, name="Frozen Controller Charm", type_line="Enchantment"), 0
    )
    replacement_artifact.type_line_override = "Artifact"
    before = len(current.players[0].hand)
    opponent_before = len(current.players[1].hand)
    pass_priority(current)
    assert ability.controller == 0
    assert len(current.players[0].hand) == before + 1
    assert len(current.players[1].hand) == opponent_before


def test_source_departure_and_reincarnation_do_not_invalidate_or_relink_trigger():
    current, source = game()
    before = len(current.players[0].hand)
    ability = trigger(current, source)
    current.put_into_graveyard(source)
    current.check_state_based_actions()
    replacement = current.create_permanent(SOURCE, 0)
    pass_priority(current)
    assert ability.source_id == source.object_id
    assert replacement.object_id != source.object_id
    assert len(current.players[0].hand) == before + 1
    current.check_invariants()


def test_adjacent_entries_and_multiple_sources_have_distinct_event_and_stack_identity():
    current = Game(([LAND] * 12, [LAND] * 20), seed=1603)
    current.begin_turn()
    current.create_permanent(ARTIFACT, 0)
    sources = [current.create_permanent(SOURCE, 0) for _ in range(2)]
    before = len(current.players[0].hand)
    current._process_creatures_entered_triggers(tuple(sources))
    abilities = [item for item in current.stack if isinstance(item, TriggeredAbilityObject)]
    assert len(abilities) == 2
    assert len({item.object_id for item in abilities}) == 2
    assert len({item.event.event_id for item in abilities}) == 2
    pass_priority(current)
    assert len(current.players[0].hand) == before + 2
    current.check_invariants()


def test_fabricated_relinked_event_or_source_provenance_fails_without_draw():
    current, source = game()
    ability = trigger(current, source)
    original = ability.event
    ability.event = replace(original, subject_ids=("fabricated",))
    before = current.authoritative_state_fingerprint()
    hand_before = len(current.players[0].hand)
    with pytest.raises(AssertionError, match="immutable original evidence"):
        current.check_invariants()
    with pytest.raises(ValueError, match="immutable original evidence"):
        current._resolve_triggered_ability(ability)
    assert current.authoritative_state_fingerprint() == before
    assert len(current.players[0].hand) == hand_before
    ability.event = original


def test_fabricated_historical_artifact_characteristics_fail_closed():
    current, source = game()
    ability = trigger(current, source)
    original = ability.event
    ability.event = replace(
        original,
        battlefield_characteristics=tuple(
            (object_id, controller, "Enchantment")
            for object_id, controller, _type_line in original.battlefield_characteristics
        ),
    )
    before = current.authoritative_state_fingerprint()
    hand_before = len(current.players[0].hand)
    with pytest.raises(AssertionError, match="immutable original evidence"):
        current.check_invariants()
    with pytest.raises(ValueError, match="immutable original evidence"):
        current._resolve_triggered_ability(ability)
    assert current.authoritative_state_fingerprint() == before
    assert len(current.players[0].hand) == hand_before
    ability.event = original


def test_fully_resigned_audit_2_historical_qualifier_attack_fails_invariants():
    current, source = game()
    decoy = current.create_permanent(
        replace(ARTIFACT, name="Nonartifact Decoy", type_line="Enchantment"), 0
    )
    ability = trigger(current, source)
    original = ability.event
    genuine = next(item for item in current.players[0].battlefield if item.card is ARTIFACT)
    forged = replace(
        original,
        battlefield_characteristics=tuple(
            (
                object_id,
                controller,
                "Enchantment"
                if object_id == genuine.object_id
                else "Artifact"
                if object_id == decoy.object_id
                else type_line,
            )
            for object_id, controller, type_line in original.battlefield_characteristics
        ),
    )
    current._rules_events[forged.event_id] = forged
    current._triggers[ability.trigger_id] = replace(
        current._triggers[ability.trigger_id], event=forged
    )
    ability.event = forged
    before = current.authoritative_state_fingerprint()
    hand_before = len(current.players[0].hand)

    with pytest.raises(AssertionError, match="immutable original evidence"):
        current.check_invariants()
    with pytest.raises(ValueError, match="immutable original evidence"):
        current._resolve_triggered_ability(ability)

    assert current.authoritative_state_fingerprint() == before
    assert len(current.players[0].hand) == hand_before


@pytest.mark.parametrize(
    "mutation",
    [
        "event_identity",
        "event_type",
        "event_cursor",
        "source_incarnation",
        "trigger_controller",
        "qualifier_controller",
        "historical_type",
        "battlefield_authority",
        "stack_trigger_link",
        "trigger_event_link",
        "registry_ledger_link",
    ],
)
def test_original_event_evidence_rejects_independent_linkage_tampering(mutation):
    current, source = game()
    other_source = current.create_permanent(SOURCE, 0)
    ability = trigger(current, source)
    original = ability.event
    trigger_record = current._triggers[ability.trigger_id]

    if mutation in {"event_identity", "event_cursor"}:
        forged = replace(original, event_id="event-999999")
        del current._rules_events[original.event_id]
        current._rules_events[forged.event_id] = forged
        current._triggers[ability.trigger_id] = replace(trigger_record, event=forged)
        ability.event = forged
    elif mutation == "event_type":
        forged = replace(original, kind=RulesEventKind.DAMAGE_DEALT)
        current._rules_events[original.event_id] = forged
        current._triggers[ability.trigger_id] = replace(trigger_record, event=forged)
        ability.event = forged
    elif mutation == "source_incarnation":
        forged = replace(original, subject_ids=(other_source.object_id,))
        current._rules_events[original.event_id] = forged
        current._triggers[ability.trigger_id] = replace(
            trigger_record, source_id=other_source.object_id, event=forged
        )
        ability.source_id = other_source.object_id
        ability.event = forged
    elif mutation == "trigger_controller":
        current._triggers[ability.trigger_id] = replace(trigger_record, controller=1)
        ability.controller = 1
    elif mutation == "qualifier_controller":
        artifact_id = next(
            object_id
            for object_id, _controller, type_line in original.battlefield_characteristics
            if "Artifact" in type_line
        )
        forged = replace(
            original,
            battlefield_characteristics=tuple(
                (object_id, 1 if object_id == artifact_id else controller, type_line)
                for object_id, controller, type_line in original.battlefield_characteristics
            ),
        )
        current._rules_events[original.event_id] = forged
        current._triggers[ability.trigger_id] = replace(trigger_record, event=forged)
        ability.event = forged
    elif mutation == "historical_type":
        forged = replace(
            original,
            battlefield_characteristics=tuple(
                (object_id, controller, "Artifact")
                for object_id, controller, _type_line in original.battlefield_characteristics
            ),
        )
        current._rules_events[original.event_id] = forged
        current._triggers[ability.trigger_id] = replace(trigger_record, event=forged)
        ability.event = forged
    elif mutation == "battlefield_authority":
        forged = replace(original, battlefield_authority=((source.object_id, 0),))
        current._rules_events[original.event_id] = forged
        current._triggers[ability.trigger_id] = replace(trigger_record, event=forged)
        ability.event = forged
    elif mutation == "stack_trigger_link":
        ability.trigger_id = "trigger-fabricated"
    elif mutation == "trigger_event_link":
        forged = replace(original, amount=77)
        current._triggers[ability.trigger_id] = replace(trigger_record, event=forged)
    elif mutation == "registry_ledger_link":
        current._rules_events[original.event_id] = replace(original, amount=77)

    with pytest.raises(AssertionError):
        current.check_invariants()


def test_empty_library_failed_draw_uses_normal_sba_loss():
    current, source = game(library_size=0)
    trigger(current, source)
    pass_priority(current)
    assert current.winner == 1
    assert not current.players[0].hand
    record = next(
        event for event in current.events if event["event"] == "etb_artifact_draw_resolved"
    )
    assert not record["draw_succeeded"]
    assert any(event["event"] == "player_lost" for event in current.events)


def test_trigger_generated_during_draw_waits_until_parent_resolution_finishes():
    current, source = game()
    child_source = current.create_permanent(DIES_DRAW, 0)
    parent = trigger(current, source)
    original_draw = current.draw

    def draw_and_generate_child(player, count=1):
        result = original_draw(player, count)
        current.put_into_graveyard(child_source, state_based_action="draw_child_fixture")
        return result

    current.draw = draw_and_generate_child
    current.execute_priority_action(current.legal_priority_actions(0)[0])
    current.execute_priority_action(current.legal_priority_actions(1)[0])
    current.process_priority_resolution()
    current.draw = original_draw

    parent_resolved = next(
        index
        for index, event in enumerate(current.events)
        if event["event"] == "trigger_resolved" and event.get("stack_object_id") == parent.object_id
    )
    child_stacked = next(
        index
        for index, event in enumerate(current.events)
        if event["event"] == "trigger_stacked" and event.get("stack_object_id") != parent.object_id
    )
    assert parent_resolved < child_stacked
    assert len(current.stack) == 1
    assert current.priority_state is not None
    pass_priority(current)
    current.check_invariants()


def test_duplicate_execution_is_byte_identical():
    def run():
        current, source = game()
        trigger(current, source)
        pass_priority(current)
        current.check_invariants()
        return json.dumps(current.snapshot(), sort_keys=True, separators=(",", ":")).encode()

    first, second = run(), run()
    assert first == second
    assert hashlib.sha256(first).hexdigest() == hashlib.sha256(second).hexdigest()


def test_authoritative_corpus_membership_is_donatello_turtle_techie_only():
    interpreter = CardInterpreter()
    members = []
    for card in catalog().cards:
        for fragment in interpreter.fragments(card):
            coverage = interpreter.etb_artifact_draw_semantic_coverage(card, fragment)
            if coverage is not None:
                members.append(
                    (
                        card.oracle_id,
                        card.name,
                        card.collector_number,
                        fragment,
                        coverage.fully_supported,
                    )
                )
    unique = sorted(set(members))
    assert unique == [
        (
            "f84850bc-6348-449e-bd82-bb39e2119bec",
            "Donatello, Turtle Techie",
            "37",
            "When Donatello enters, if you control an artifact, draw a card.",
            True,
        )
    ]
