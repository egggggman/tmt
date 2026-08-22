from dataclasses import replace

import pytest

from tmnt_design_studio.card_interpreter07 import CastKind
from tmnt_design_studio.engine07 import CardFact, Game, RulesEventKind, TurnStep

LAND = CardFact("Plains", "", 0, "Basic Land — Plains", oracle_id="land")
BEAR = CardFact("Bear", "{1}{W}", 2, "Creature — Bear", power=2, toughness=2, oracle_id="bear")


def game() -> Game:
    return Game(([LAND] * 30 + [BEAR] * 30, [LAND] * 30 + [BEAR] * 30), seed=71)


def permanent(current: Game, card: CardFact, controller: int = 0):
    result = current.create_permanent(card, controller, summoning_sick=False)
    current.place_on_battlefield(result)
    return result


def register(current: Game, source):
    current.report_unsupported_abilities(source.controller, source.card, source=source)
    return current.semantic_occurrences[-1]


def test_present_text_is_not_promoted_without_positive_opportunity_evidence():
    card = CardFact(
        "Dormant",
        "{1}{W}",
        2,
        "Creature — Turtle",
        "Whenever Dormant attacks, draw a card.",
        2,
        2,
        oracle_id="dormant",
    )
    current = game()
    source = permanent(current, card)
    register(current, source)

    record = current.snapshot()["conformance"]["semantic_occurrences"][0]
    assert record["classification"] == "present_unreached"
    assert current.opportunity_witnesses == []


def test_etb_and_attack_witnesses_join_authoritative_events_to_exact_fragments():
    etb = CardFact(
        "Visitor",
        "{1}{W}",
        2,
        "Creature — Turtle",
        "When Visitor enters, draw a card.",
        2,
        2,
        oracle_id="visitor",
    )
    attacker_card = CardFact(
        "Runner",
        "{1}{W}",
        2,
        "Creature — Turtle",
        "Whenever Runner attacks, draw a card.",
        2,
        2,
        oracle_id="runner",
    )
    current = game()
    visitor = permanent(current, etb)
    event = current._new_rules_event(RulesEventKind.CREATURE_ENTERED, 0, (visitor.object_id,))
    register(current, visitor)
    assert current.opportunity_witnesses[-1].cause_id == event.event_id

    runner = permanent(current, attacker_card)
    register(current, runner)
    current._turn = 1
    current._step = TurnStep.DECLARE_ATTACKERS
    attack = current._new_rules_event(RulesEventKind.ATTACKERS_DECLARED, 0, (runner.object_id,))
    assert current.opportunity_witnesses[-1].cause_id == attack.event_id


def test_alliance_requires_another_controlled_creature_and_deduplicates_one_event():
    card = CardFact(
        "Ally",
        "{1}{W}",
        2,
        "Creature — Turtle",
        "Alliance — Whenever another creature you control enters, draw a card.",
        2,
        2,
        oracle_id="ally",
    )
    current = game()
    source = permanent(current, card)
    occurrence = register(current, source)
    current._new_rules_event(RulesEventKind.CREATURE_ENTERED, 0, (source.object_id,))
    current._new_rules_event(
        RulesEventKind.CREATURE_ENTERED, 1, (permanent(current, BEAR, 1).object_id,)
    )
    assert current.opportunity_witnesses == []

    entering = permanent(current, BEAR)
    event = current._new_rules_event(RulesEventKind.CREATURE_ENTERED, 0, (entering.object_id,))
    current._witness_from_event(occurrence, event)
    assert len(current.opportunity_witnesses) == 1


def test_graveyard_permission_requires_timing_source_and_eligible_card():
    card = CardFact(
        "Keeper",
        "{2}{W}",
        3,
        "Creature — Turtle",
        "During your turn, you may cast creature spells with power or toughness 1 or less from "
        "your graveyard.",
        2,
        3,
        oracle_id="keeper",
    )
    small = CardFact("Small", "{W}", 1, "Creature — Turtle", power=1, toughness=2)
    current = game()
    current.begin_turn()
    source = permanent(current, card)
    register(current, source)
    current.legal_main_actions(0)
    assert current.opportunity_witnesses == []
    grave = current.set_hand_for_testing(0, [small])[0]
    current.move_object(grave, "graveyard", reason="test")
    current.legal_main_actions(0)
    assert current.opportunity_witnesses[-1].cause_kind == "legal_action_context"
    current.legal_main_actions(0)
    assert len(current.opportunity_witnesses) == 1


def test_menace_is_reached_only_when_a_real_block_candidate_is_considered():
    menace = CardFact(
        "Threat",
        "{2}{B}",
        3,
        "Creature — Turtle",
        "Menace (This creature can't be blocked except by two or more creatures.)",
        3,
        3,
        oracle_id="threat",
    )
    current = game()
    current.begin_turn()
    attacker = permanent(current, menace)
    register(current, attacker)
    current.advance_to(TurnStep.DECLARE_ATTACKERS)
    current.execute_attack_action(
        next(option for option in current.legal_attack_options(0) if option.attacker_ids)
    )
    assert current.opportunity_witnesses == []
    blocker = permanent(current, BEAR, 1)
    current.generate_blocks([attacker], 1, log_rejections=False)
    witness = current.opportunity_witnesses[-1]
    assert witness.cause_subject_ids == (attacker.object_id, blocker.object_id)


def test_fabricated_event_and_stale_or_mismatched_evidence_are_rejected_before_mutation():
    card = CardFact(
        "Visitor",
        "{1}{W}",
        2,
        "Creature — Turtle",
        "When Visitor enters, draw a card.",
        2,
        2,
        oracle_id="visitor",
    )
    current = game()
    source = permanent(current, card)
    event = current._new_rules_event(RulesEventKind.CREATURE_ENTERED, 0, (source.object_id,))
    occurrence = register(current, source)
    before = current.authoritative_state_fingerprint()
    with pytest.raises(ValueError, match="fabricated"):
        current._record_opportunity(
            occurrence,
            cause_kind="rules_event",
            cause_id="event-fabricated",
            cause_subject_ids=(source.object_id,),
        )
    assert current.authoritative_state_fingerprint() == before
    current.opportunity_witnesses[0] = replace(
        current.opportunity_witnesses[0], cause_id="event-fabricated"
    )
    with pytest.raises(AssertionError, match="fabricated"):
        current.check_invariants()
    assert event.event_id != "event-fabricated"


def test_departed_or_recontrolled_alliance_source_cannot_gain_a_later_witness():
    card = CardFact(
        "Ally",
        "{1}{W}",
        2,
        "Creature — Turtle",
        "Alliance — Whenever another creature you control enters, draw a card.",
        2,
        2,
        oracle_id="ally",
    )
    departed_game = game()
    departed = permanent(departed_game, card)
    occurrence = register(departed_game, departed)
    departed_game.put_into_graveyard(departed)
    entering = permanent(departed_game, BEAR)
    departed_game._new_rules_event(RulesEventKind.CREATURE_ENTERED, 0, (entering.object_id,))
    assert departed_game.opportunity_witnesses == []
    with pytest.raises(ValueError, match="authoritative source"):
        departed_game._record_opportunity(
            occurrence,
            cause_kind="rules_event",
            cause_id="event-000001",
            cause_subject_ids=(entering.object_id,),
        )

    controlled_game = game()
    controlled = permanent(controlled_game, card)
    register(controlled_game, controlled)
    controlled_game.change_controller(controlled, 1)
    old_controller_entry = permanent(controlled_game, BEAR)
    controlled_game._new_rules_event(
        RulesEventKind.CREATURE_ENTERED, 0, (old_controller_entry.object_id,)
    )
    assert controlled_game.opportunity_witnesses == []


def test_unrelated_valid_event_cannot_authenticate_an_attack_semantic():
    card = CardFact(
        "Runner",
        "{1}{W}",
        2,
        "Creature — Turtle",
        "Whenever Runner attacks, draw a card.",
        2,
        2,
        oracle_id="runner",
    )
    current = game()
    source = permanent(current, card)
    occurrence = register(current, source)
    event = current._new_rules_event(
        RulesEventKind.LIFE_GAINED,
        0,
        (source.object_id,),
        source_id=source.object_id,
        amount=3,
    )
    with pytest.raises(ValueError, match="applicability"):
        current._record_opportunity(
            occurrence,
            cause_kind="rules_event",
            cause_id=event.event_id,
            cause_subject_ids=event.subject_ids,
        )
    assert current.opportunity_witnesses == []


def test_invariants_reapply_shared_applicability_to_frozen_witness_facts():
    card = CardFact(
        "Visitor",
        "{1}{W}",
        2,
        "Creature — Turtle",
        "When Visitor enters, draw a card.",
        2,
        2,
        oracle_id="visitor",
    )
    current = game()
    source = permanent(current, card)
    event = current._new_rules_event(RulesEventKind.CREATURE_ENTERED, 0, (source.object_id,))
    register(current, source)
    current.opportunity_witnesses[0] = replace(
        current.opportunity_witnesses[0],
        source_zone="former",
        cause_event_kind=RulesEventKind.LIFE_GAINED.value,
    )
    with pytest.raises(AssertionError, match="provenance|battlefield"):
        current.check_invariants()
    assert event.event_id == "event-000001"


def test_conformance_snapshot_is_deterministic_and_keeps_action_evidence_separate():
    first = game()
    second = game()
    card = CardFact(
        "Dormant",
        "{1}{W}",
        2,
        "Creature — Turtle",
        "Whenever Dormant attacks, draw a card.",
        2,
        2,
        oracle_id="dormant",
    )
    register(first, permanent(first, card))
    register(second, permanent(second, card))
    source = first._objects[first.semantic_occurrences[0].object_id]
    register(first, source)
    assert len(first.semantic_occurrences) == 1
    assert first.snapshot()["conformance"] == second.snapshot()["conformance"]
    assert first.snapshot()["conformance"]["executed_references"] == []


def test_fixed_cost_activation_context_requires_authoritative_source_and_resources():
    card = CardFact(
        "Device",
        "{2}",
        2,
        "Artifact",
        "{2}, {T}, Sacrifice this artifact: Draw two cards.",
        oracle_id="device",
    )
    current = game()
    current.begin_turn()
    source = permanent(current, card)
    register(current, source)
    current.legal_main_actions(0)
    assert current.opportunity_witnesses == []
    permanent(current, LAND)
    permanent(current, LAND)
    current.legal_main_actions(0)
    witness = current.opportunity_witnesses[-1]
    assert witness.cause_kind == "authoritative_context"
    assert witness.cause_subject_ids[0] == source.object_id
    current.legal_main_actions(0)
    assert len(current.opportunity_contexts) == 1


def test_departure_context_is_historical_and_distinguishes_separate_objects():
    card = CardFact(
        "Fugitive",
        "{1}{G}",
        2,
        "Creature — Mutant",
        "When this creature leaves the battlefield, create a Mutagen token.",
        2,
        2,
        oracle_id="fugitive",
    )
    current = game()
    first = permanent(current, card)
    second = permanent(current, card)
    register(current, first)
    register(current, second)
    current.put_into_graveyard(first)
    current.put_into_graveyard(second)
    contexts = [
        item for item in current.opportunity_contexts if item.context_kind == "permanent_departed"
    ]
    assert [item.subject_ids for item in contexts] == [(first.object_id,), (second.object_id,)]
    assert all(item.subject_zones == ("former",) for item in contexts)
    current.check_invariants()


def test_artifact_and_replacement_contexts_require_their_authoritative_predicates():
    artifact_watcher = CardFact(
        "Watcher",
        "{1}{U}",
        2,
        "Creature — Turtle",
        "Whenever an artifact you control enters, put a +1/+1 counter on Watcher.",
        1,
        3,
        oracle_id="watcher",
    )
    replacement = CardFact(
        "Mentor",
        "{2}{G}",
        3,
        "Creature — Turtle",
        "If one or more +1/+1 counters would be put on a creature you control, that many plus "
        "one +1/+1 counters are put on it instead.",
        2,
        3,
        oracle_id="mentor",
    )
    artifact = CardFact("Bot", "{1}", 1, "Artifact Creature — Robot", power=1, toughness=1)
    current = game()
    watcher = permanent(current, artifact_watcher)
    mentor = permanent(current, replacement)
    register(current, watcher)
    register(current, mentor)
    entering = permanent(current, artifact)
    current._new_rules_event(RulesEventKind.CREATURE_ENTERED, 0, (entering.object_id,))
    current.place_counters(watcher, "+1/+1", 1, source_card="test", oracle_fragment="test")
    assert {item.context_kind for item in current.opportunity_contexts} >= {
        "artifact_dependency",
        "replacement_evaluation",
    }


@pytest.mark.parametrize(
    "fragment",
    [
        "Affinity for artifacts (This spell costs {1} less to cast for each artifact you control.)",
        "Destroy target artifact.",
        "{2}, Sacrifice this artifact: Draw a card.",
        "Create a token that's a copy of target artifact you control.",
        "Equip {2} ({2}: Attach to target creature you control. Equip only as a sorcery.)",
    ],
)
def test_artifact_entry_does_not_promote_unrelated_artifact_semantics(fragment):
    source_card = CardFact(
        "Artifact Text",
        "{1}{U}",
        2,
        "Creature — Turtle",
        fragment,
        1,
        3,
        oracle_id=f"artifact-text-{fragment}",
    )
    artifact = CardFact("Bot", "{1}", 1, "Artifact Creature — Robot", power=1, toughness=1)
    current = game()
    source = permanent(current, source_card)
    occurrence = register(current, source)
    entering = permanent(current, artifact)
    current._new_rules_event(RulesEventKind.CREATURE_ENTERED, 0, (entering.object_id,))
    assert not any(
        item.occurrence_id == occurrence.occurrence_id for item in current.opportunity_witnesses
    )
    assert not any(item.source_id == source.object_id for item in current.opportunity_contexts)


@pytest.mark.parametrize(
    "fragment",
    [
        "Target player draws a card.",
        "Destroy target artifact.",
        "Counter target spell.",
        "Return target creature card from your graveyard to your hand.",
        "Choose a color.",
        "Put a counter on target creature you control.",
        "Destroy target creature with flying.",
        "Destroy up to one target creature.",
        "Two target creatures get +1/+1 until end of turn.",
    ],
)
def test_creature_candidate_context_rejects_incompatible_target_and_choice_grammar(fragment):
    source_card = CardFact(
        "Choice Text",
        "{1}",
        1,
        "Sorcery",
        fragment,
        oracle_id=f"choice-text-{fragment}",
    )
    current = game()
    hand_source = current.set_hand_for_testing(0, [source_card])[0]
    source = current.move_object(hand_source, "graveyard", reason="test_resolution")
    occurrence = register(current, source)
    candidate = permanent(current, BEAR, 1)
    instruction = current._new_opportunity_context(
        "instruction_reached",
        controller=0,
        source_id=source.object_id,
        subject_ids=(source.object_id,),
        facts=(("instruction_source_zone", "graveyard"),),
    )
    witnesses_before_target = len(current.opportunity_witnesses)
    context = current._new_opportunity_context(
        "target_choice_available",
        controller=0,
        source_id=source.object_id,
        subject_ids=(candidate.object_id,),
        facts=(
            ("candidate_kind", "battlefield_creature"),
            ("instruction_context_id", instruction.context_id),
        ),
    )
    assert len(current.opportunity_witnesses) == witnesses_before_target
    with pytest.raises(ValueError, match="applicability"):
        current._record_opportunity(
            occurrence,
            cause_kind="authoritative_context",
            cause_id=context.context_id,
            cause_subject_ids=context.subject_ids,
        )


def test_exact_bounded_creature_target_context_still_promotes():
    card = CardFact(
        "Choice Text",
        "{1}",
        1,
        "Sorcery",
        "Choose target creature. Draw a card.",
        oracle_id="bounded-creature-choice",
    )
    current = game()
    hand_source = current.set_hand_for_testing(0, [card])[0]
    source = current.move_object(hand_source, "graveyard", reason="test_resolution")
    occurrence = register(current, source)
    candidate = permanent(current, BEAR, 1)
    instruction = current._new_opportunity_context(
        "instruction_reached",
        controller=0,
        source_id=source.object_id,
        subject_ids=(source.object_id,),
        facts=(("instruction_source_zone", "graveyard"),),
    )
    current._new_opportunity_context(
        "target_choice_available",
        controller=0,
        source_id=source.object_id,
        subject_ids=(candidate.object_id,),
        facts=(
            ("candidate_kind", "battlefield_creature"),
            ("instruction_context_id", instruction.context_id),
        ),
    )
    assert current.opportunity_witnesses[-1].occurrence_id == occurrence.occurrence_id
    assert current.opportunity_witnesses[-1].cause_id != instruction.context_id


def test_fabricated_context_and_mismatched_fragment_fail_invariants():
    card = CardFact(
        "Device",
        "{2}",
        2,
        "Artifact",
        "{2}: Draw a card.",
        oracle_id="device",
    )
    current = game()
    current.begin_turn()
    source = permanent(current, card)
    mana = (permanent(current, LAND), permanent(current, LAND))
    occurrence = register(current, source)
    with pytest.raises(ValueError, match="fabricated"):
        current._new_opportunity_context(
            "activation_available",
            controller=0,
            source_id=source.object_id,
            subject_ids=("object-fabricated",),
            facts=(
                ("mana_required", "2"),
                ("source_tap_required", "false"),
                ("source_tapped", "false"),
                ("timing", "precombat_main"),
            ),
        )
    context = current._new_opportunity_context(
        "activation_available",
        controller=0,
        source_id=source.object_id,
        subject_ids=(source.object_id, *(item.object_id for item in mana)),
        facts=(
            ("mana_required", "2"),
            ("source_tap_required", "false"),
            ("source_tapped", "false"),
            ("timing", "precombat_main"),
        ),
    )
    current.opportunity_witnesses[0] = replace(
        current.opportunity_witnesses[0], cause_id="context-fabricated"
    )
    with pytest.raises(AssertionError, match="context"):
        current.check_invariants()
    assert context.context_id != "context-fabricated"
    assert occurrence.oracle_fragment == "{2}: Draw a card."

    clean = game()
    clean.begin_turn()
    clean_source = permanent(clean, card)
    clean_mana = (permanent(clean, LAND), permanent(clean, LAND))
    register(clean, clean_source)
    clean._new_opportunity_context(
        "activation_available",
        controller=0,
        source_id=clean_source.object_id,
        subject_ids=(clean_source.object_id, *(item.object_id for item in clean_mana)),
        facts=(
            ("mana_required", "2"),
            ("source_tap_required", "false"),
            ("source_tapped", "false"),
            ("timing", "precombat_main"),
        ),
    )
    clean.opportunity_contexts[0] = replace(clean.opportunity_contexts[0], subject_zones=("hand",))
    with pytest.raises(AssertionError, match="context provenance"):
        clean.check_invariants()


def test_canonical_illegal_mutation_stop_requires_a_real_state_change():
    current = game()
    before = current.authoritative_state_fingerprint()
    with pytest.raises(ValueError, match="observed state change"):
        current.record_conformance_stop("illegal_mutation", before, detail="rejected option")
    current.players[0].life -= 1
    record = current.record_conformance_stop("illegal_mutation", before, detail="probe")
    assert record.before_fingerprint != record.after_fingerprint
    assert current.snapshot()["conformance"]["stop_records"][0]["kind"] == "illegal_mutation"


def test_stack_response_requires_card_mana_and_authoritative_stack_target():
    negate = CardFact(
        "Generic Denial",
        "{1}{U}",
        2,
        "Instant",
        "Counter target noncreature spell.",
        oracle_id="denial",
    )
    spell_card = CardFact("Effect", "{1}", 1, "Sorcery", "Draw a card.", oracle_id="effect")
    current = game()
    response = current.set_hand_for_testing(1, [negate])[0]
    spell = current.set_hand_for_testing(0, [spell_card])[0]
    permanent(current, CardFact("Island", "", 0, "Basic Land — Island"), 1)
    permanent(current, LAND, 1)
    stack_object = current.move_object(spell, "stack", controller=0, cast_kind=CastKind.DEAL_DAMAGE)
    current._begin_priority_window()
    witness = current.opportunity_witnesses[-1]
    assert witness.object_id == response.object_id
    assert witness.cause_subject_ids == (stack_object.object_id,)
    assert current.opportunity_contexts[-1].stack_object_id == stack_object.object_id


def test_resolution_instruction_context_preserves_present_but_unreached_until_resolution():
    card = CardFact(
        "Instruction",
        "{1}",
        1,
        "Sorcery",
        "Choose target creature. Draw a card, then discard a card.",
        oracle_id="instruction",
    )
    current = game()
    permanent(current, BEAR, 1)
    source = current.set_hand_for_testing(0, [card])[0]
    occurrence = register(current, source)
    assert current.opportunity_witnesses == []
    graveyard = current.move_object(source, "graveyard", reason="test_resolution")
    current._witness_resolved_unsupported_instructions(graveyard)
    assert occurrence.object_id != graveyard.object_id
    reached = current.semantic_occurrences[-1]
    assert reached.object_id == source.object_id
    # Zone movement creates a new object, so the old occurrence cannot be promoted by inference.
    assert current.opportunity_witnesses == []
    current.report_unsupported_abilities(0, graveyard.card, source=graveyard)
    current._witness_resolved_unsupported_instructions(graveyard)
    assert {item.context_kind for item in current.opportunity_contexts} == {
        "instruction_reached",
        "target_choice_available",
    }
