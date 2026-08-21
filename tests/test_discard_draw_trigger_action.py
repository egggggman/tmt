import hashlib
import inspect
import json
from dataclasses import replace
from pathlib import Path

import pytest

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter, DiscardDrawProgram
from tmnt_design_studio.engine07 import (
    CardFact,
    DiscardDrawOption,
    Game,
    RulesEventKind,
    TriggerEffect,
    TurnStep,
)
from tmnt_design_studio.semantic_coverage import SemanticCoverage

ROOT = Path(__file__).resolve().parents[1]
PLAINS = CardFact("Plains", "", 0, "Basic Land — Plains")
BEAR = CardFact("Bear", "{1}{G}", 2, "Creature — Bear", power=2, toughness=2)
FRAGMENT = "Whenever this creature attacks, you may discard a card. If you do, draw a card."
NULL_GROUP = CardFact(
    "Renamed Biological Asset",
    "{2}{U}",
    3,
    "Creature — Mutant",
    oracle_text="During your turn, this creature has first strike.\n" + FRAGMENT,
    power=3,
    toughness=3,
)


def catalog():
    return load_card_data(
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json",
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json",
    )


def coverage_sets():
    interpreter = CardInterpreter()
    recognized, payload, full = [], [], []
    seen = set()
    for card in sorted(catalog().cards, key=lambda value: (value.name, value.oracle_id)):
        if card.oracle_id in seen:
            continue
        seen.add(card.oracle_id)
        for fragment in interpreter.fragments(card):
            semantics = interpreter.discard_draw_semantic_coverage(card, fragment)
            if semantics is None:
                continue
            member = (card.oracle_id, card.name, fragment)
            recognized.append(member)
            if semantics.coverage.payload_executable:
                payload.append(member)
            if semantics.coverage.fully_supported:
                full.append(member)
    return recognized, payload, full


def digest(members):
    encoded = json.dumps(members, ensure_ascii=False, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def game(chooser=None, *, hand=(BEAR, PLAINS), library=(PLAINS,) * 8):
    current = Game((list(library), [PLAINS] * 20), seed=73, discard_draw_chooser=chooser)
    current.begin_turn()
    current.set_hand_for_testing(0, list(hand))
    attacker = current.create_permanent(NULL_GROUP, 0, summoning_sick=False)
    return current, attacker


def choose_first(_view, options):
    return next(option for option in options if option.card_id is not None)


def execute_trigger(current, attacker):
    if current.step is not TurnStep.DECLARE_ATTACKERS:
        current.advance_to(TurnStep.DECLARE_ATTACKERS)
    current.resolve_attack_pt_effects([attacker])
    while current.priority_state is not None:
        if current.priority_state.resolution_pending:
            current.process_priority_resolution()
        else:
            option = current.legal_priority_actions(current.priority_state.player_index)[0]
            current.execute_priority_action(option)


def detached_resolving_trigger(current, attacker):
    current.advance_to(TurnStep.DECLARE_ATTACKERS)
    event = current._new_rules_event(
        RulesEventKind.ATTACKERS_DECLARED, attacker.controller, (attacker.object_id,)
    )
    current._enqueue_trigger(event, attacker, FRAGMENT, TriggerEffect.DISCARD_DRAW)
    current._put_pending_triggers_on_stack()
    trigger = current.stack.pop()
    trigger.zone = "former"
    return trigger


def test_oracle_grammar_and_semantic_coverage_are_generic():
    semantics = CardInterpreter().discard_draw_semantic_coverage(NULL_GROUP, FRAGMENT)
    assert semantics is not None
    assert semantics.program == DiscardDrawProgram(1, 1, True, True)
    assert semantics.coverage == SemanticCoverage(True, True, True, ())
    renamed = CardFact("Anything", "", 0, "Creature", FRAGMENT, power=1, toughness=1)
    assert CardInterpreter().discard_draw_semantic_coverage(renamed, FRAGMENT) == semantics


def test_player_attack_parent_is_recognized_but_not_executable():
    fragment = "Whenever you attack, you may discard a card. If you do, draw a card."
    semantics = CardInterpreter().discard_draw_semantic_coverage(NULL_GROUP, fragment)
    assert semantics is not None and semantics.coverage.payload_executable
    assert not semantics.coverage.parent_executable
    assert semantics.limitations == ("discard_draw_attack_trigger_context_not_implemented",)


@pytest.mark.parametrize(
    "fragment",
    [
        "Discard a card, then draw a card.",
        "You may discard two cards. If you do, draw two cards.",
        "Whenever this creature attacks, discard a card at random. Draw a card.",
        "Whenever this creature attacks, you may sacrifice a creature. If you do, draw a card.",
    ],
)
def test_unrelated_discard_draw_patterns_remain_unsupported(fragment):
    assert CardInterpreter().discard_draw_semantic_coverage(NULL_GROUP, fragment) is None


def test_attack_trigger_uses_stack_and_resolves_discard_then_draw():
    observations = []

    def chooser(view, options):
        observations.append(
            (
                tuple(object_id for object_id, _name in view.cards),
                tuple(event["event"] for event in current.events[-3:]),
            )
        )
        return next(option for option in options if option.card_id is not None)

    current, attacker = game(chooser)
    selected = current.players[0].hand[0]
    old_top = current.players[0].library[-1]
    execute_trigger(current, attacker)
    evidence = current.discard_draw_evidence[-1]
    names = [event["event"] for event in current.events]
    stacked_index = names.index("trigger_stacked")
    first_priority_index = names.index("priority_granted", stacked_index)
    first_pass_index = names.index("priority_passed", first_priority_index)
    discard_index = names.index("zone_changed", stacked_index)
    draw_index = names.index("card_drawn", discard_index)
    resolved_index = names.index("trigger_resolved", draw_index)
    assert stacked_index < first_priority_index < first_pass_index < discard_index
    assert discard_index < draw_index < resolved_index
    assert observations and observations[0][0] == evidence.pre_hand_ids
    assert evidence.selected_hand_id == selected.object_id
    assert evidence.discarded_graveyard_id != selected.object_id
    assert evidence.pre_draw_top_id == old_top.object_id
    assert evidence.drawn_hand_id != old_top.object_id
    assert selected.zone == old_top.zone == "former"
    assert not current.stack
    provenance = evidence.attack_provenance
    assert provenance.event_kind is RulesEventKind.ATTACKERS_DECLARED
    assert provenance.subject_ids == (attacker.object_id,)
    assert provenance.attacker_id == attacker.object_id
    assert provenance.controller == provenance.event_player_index == 0
    assert provenance.active_player == 0
    assert provenance.step == TurnStep.DECLARE_ATTACKERS.value


def test_trigger_resolution_cannot_bypass_priority_or_authoritative_stack():
    current, attacker = game(choose_first)
    current.resolve_attack_pt_effects([attacker])
    assert current.priority_state is not None and current.stack
    with pytest.raises(ValueError, match="before all players pass"):
        current.resolve_top_of_stack()
    fabricated = type(current.stack[-1])(**vars(current.stack[-1]))
    with pytest.raises(ValueError, match="authoritative top stack"):
        current._resolve_triggered_ability(fabricated)


def test_decline_and_empty_hand_do_not_discard_or_draw():
    for hand in ((BEAR,), ()):
        current, attacker = game(hand=hand)
        before = current.snapshot()
        execute_trigger(current, attacker)
        evidence = current.discard_draw_evidence[-1]
        assert evidence.declined and not evidence.movement_succeeded
        assert not evidence.conditional_draw_performed
        assert evidence.pre_hand_ids == evidence.post_hand_ids
        assert evidence.pre_library_ids == evidence.post_library_ids
        assert current.players[0].life == before["players"][0]["life"]


def test_successful_discard_with_empty_library_attempts_draw_and_records_loss():
    current, attacker = game(choose_first)
    while current.players[0].library:
        current.move_object(current.players[0].library[-1], "graveyard", reason="test_empty")
    execute_trigger(current, attacker)
    evidence = current.discard_draw_evidence[-1]
    assert evidence.movement_succeeded
    assert not evidence.conditional_draw_performed
    assert evidence.pre_draw_top_id is None and evidence.drawn_hand_id is None
    assert current.players[0].lost
    assert current.players[0].loss_reason == "draw_from_empty_library"
    event_names = [event["event"] for event in current.events]
    assert event_names.index("draw_failed") < event_names.index("trigger_resolved")
    assert event_names.index("trigger_resolved") < event_names.index("player_lost")
    loss = next(event for event in current.events if event["event"] == "player_lost")
    assert loss["state_based_action"] == "failed_draw"


def test_empty_library_loss_is_pending_until_post_resolution_sba_boundary():
    current, attacker = game(choose_first)
    while current.players[0].library:
        current.move_object(current.players[0].library[-1], "graveyard", reason="test_empty")
    current.advance_to(TurnStep.DECLARE_ATTACKERS)
    current.resolve_attack_pt_effects([attacker])
    while current.priority_state and not current.priority_state.resolution_pending:
        current.execute_priority_action(
            current.legal_priority_actions(current.priority_state.player_index)[0]
        )
    current.resolve_top_of_stack()
    assert current.players[0].failed_draw_pending
    assert not current.players[0].lost and current.winner is None
    assert current.events[-1]["event"] == "trigger_resolved"
    current.priority_state = None
    current.check_invariants()
    current.check_state_based_actions()
    assert not current.players[0].failed_draw_pending
    assert current.players[0].lost and current.winner == 1


def test_fabricated_choice_rejected_without_zone_mutation():
    current, attacker = game(lambda _view, _options: DiscardDrawOption("fabricated"))
    hand = tuple(current.players[0].hand)
    library = tuple(current.players[0].library)
    graveyard = tuple(current.players[0].graveyard)
    with pytest.raises(ValueError, match="listed option"):
        execute_trigger(current, attacker)
    assert tuple(current.players[0].hand) == hand
    assert tuple(current.players[0].library) == library
    assert tuple(current.players[0].graveyard) == graveyard
    assert not current.discard_draw_evidence


def test_stale_plan_and_failed_movement_cannot_draw(monkeypatch):
    current, attacker = game(choose_first)
    program = DiscardDrawProgram(1, 1, True, True)
    plan = current.choose_discard_draw(0, program)
    trigger = detached_resolving_trigger(current, attacker)
    current.move_object(current.players[0].hand[-1], "graveyard", reason="test")
    before = current.snapshot()
    with pytest.raises(ValueError, match="became stale"):
        current.commit_discard_draw(0, program, plan, trigger=trigger)
    assert current.snapshot() == before

    current, attacker = game(choose_first)
    plan = current.choose_discard_draw(0, program)
    trigger = detached_resolving_trigger(current, attacker)
    draw_called = False

    def fail_move(*_args, **_kwargs):
        raise ValueError("injected movement failure")

    def observe_draw(*_args, **_kwargs):
        nonlocal draw_called
        draw_called = True
        return True

    monkeypatch.setattr(current, "move_object", fail_move)
    monkeypatch.setattr(current, "draw", observe_draw)
    with pytest.raises(ValueError, match="injected movement failure"):
        current.commit_discard_draw(0, program, plan, trigger=trigger)
    assert not draw_called and not current.discard_draw_evidence


def test_equal_valued_cards_are_distinct_and_evidence_is_reconstructive():
    def choose_second(view, options):
        return next(option for option in options if option.card_id == view.cards[1][0])

    current, attacker = game(choose_second, hand=(PLAINS, PLAINS))
    execute_trigger(current, attacker)
    evidence = current.discard_draw_evidence[-1]
    serialized = current.snapshot()["discard_draw"][0]
    assert evidence.selected_hand_id == evidence.pre_hand_ids[1]
    assert evidence.discarded_graveyard_id not in evidence.pre_hand_ids
    assert serialized["pre_hand_ids"] == list(evidence.pre_hand_ids)
    assert serialized["post_library_ids"] == list(evidence.post_library_ids)
    assert serialized["post_graveyard_ids"] == list(evidence.post_graveyard_ids)
    assert serialized["attack_provenance"] == {
        "event_id": evidence.attack_provenance.event_id,
        "event_kind": RulesEventKind.ATTACKERS_DECLARED.value,
        "event_player_index": 0,
        "subject_ids": [attacker.object_id],
        "attacker_id": attacker.object_id,
        "controller": 0,
        "turn": evidence.attack_provenance.turn,
        "step": TurnStep.DECLARE_ATTACKERS.value,
        "active_player": 0,
    }


def test_distinct_attack_events_have_distinct_immutable_provenance():
    current, attacker = game(choose_first, hand=(PLAINS, PLAINS, PLAINS))
    execute_trigger(current, attacker)
    execute_trigger(current, attacker)
    first, second = current.discard_draw_evidence
    assert first.attack_provenance.event_id != second.attack_provenance.event_id
    assert first.stack_object_id != second.stack_object_id
    assert first.attack_provenance.attacker_id == second.attack_provenance.attacker_id
    assert first.attack_provenance.subject_ids == second.attack_provenance.subject_ids


def test_fabricated_stale_and_mismatched_attack_provenance_are_rejected():
    current, attacker = game(choose_first)
    program = DiscardDrawProgram(1, 1, True, True)
    plan = current.choose_discard_draw(0, program)
    trigger = detached_resolving_trigger(current, attacker)
    zones_before = (
        tuple(current.players[0].hand),
        tuple(current.players[0].library),
        tuple(current.players[0].graveyard),
    )
    fabricated = replace(trigger, object_id="fabricated")
    with pytest.raises(ValueError, match="resolving trigger"):
        current.commit_discard_draw(0, program, plan, trigger=fabricated)

    trigger.zone = "stack"
    with pytest.raises(ValueError, match="resolving trigger"):
        current.commit_discard_draw(0, program, plan, trigger=trigger)
    trigger.zone = "former"

    original_event = trigger.event
    trigger.event = replace(original_event, subject_ids=("mismatched",))
    with pytest.raises(ValueError, match="mismatched attack provenance"):
        current.commit_discard_draw(0, program, plan, trigger=trigger)
    trigger.event = original_event
    assert zones_before == (
        tuple(current.players[0].hand),
        tuple(current.players[0].library),
        tuple(current.players[0].graveyard),
    )
    assert not current.discard_draw_evidence


def test_consumed_trigger_provenance_cannot_validate_a_second_transaction():
    current, attacker = game(choose_first, hand=(PLAINS, PLAINS))
    program = DiscardDrawProgram(1, 1, True, True)
    trigger = detached_resolving_trigger(current, attacker)
    first_plan = current.choose_discard_draw(0, program)
    current.commit_discard_draw(0, program, first_plan, trigger=trigger)
    second_plan = current.choose_discard_draw(0, program)
    zones_before = current.snapshot()
    with pytest.raises(ValueError, match="resolving trigger"):
        current.commit_discard_draw(0, program, second_plan, trigger=trigger)
    assert current.snapshot() == zones_before
    assert len(current.discard_draw_evidence) == 1


def test_nonattacking_source_and_other_attacker_do_not_trigger():
    current, source = game(choose_first)
    other = current.create_permanent(BEAR, 0, summoning_sick=False)
    execute_trigger(current, other)
    assert not current.discard_draw_evidence
    assert source.zone == "battlefield"


def test_trigger_controller_not_card_owner_makes_the_choice():
    current, _attacker = game(choose_first)
    owned_by_opponent = current.create_permanent(NULL_GROUP, 1, summoning_sick=False)
    current.change_controller(owned_by_opponent, 0)
    controller_hand = tuple(card.object_id for card in current.players[0].hand)
    owner_hand = tuple(card.object_id for card in current.players[1].hand)
    execute_trigger(current, owned_by_opponent)
    evidence = current.discard_draw_evidence[-1]
    assert evidence.player_index == 0 and evidence.pre_hand_ids == controller_hand
    assert tuple(card.object_id for card in current.players[1].hand) == owner_hand


def test_fabricated_or_stale_attacker_cannot_deliver_trigger():
    current, attacker = game(choose_first)
    fabricated = type(attacker)(
        attacker.object_id,
        attacker.card,
        attacker.owner,
        attacker.controller,
        summoning_sick=False,
    )
    with pytest.raises(ValueError, match="authoritative"):
        execute_trigger(current, fabricated)
    current.move_object(attacker, "graveyard", reason="test")
    with pytest.raises(ValueError, match="authoritative"):
        execute_trigger(current, attacker)
    assert not current.discard_draw_evidence


def test_trigger_is_independent_after_authoritative_source_leaves():
    current, attacker = game(choose_first)
    current.advance_to(TurnStep.DECLARE_ATTACKERS)
    event = current._new_rules_event(RulesEventKind.ATTACKERS_DECLARED, 0, (attacker.object_id,))
    current._enqueue_trigger(event, attacker, FRAGMENT, TriggerEffect.DISCARD_DRAW)
    current._put_pending_triggers_on_stack()
    current.move_object(attacker, "graveyard", reason="after_trigger")
    current._drain_triggered_abilities()
    while current.priority_state is not None:
        if current.priority_state.resolution_pending:
            current.process_priority_resolution()
        else:
            option = current.legal_priority_actions(current.priority_state.player_index)[0]
            current.execute_priority_action(option)
    evidence = current.discard_draw_evidence[-1]
    assert evidence.source_id == attacker.object_id
    assert evidence.movement_succeeded and evidence.conditional_draw_performed


def test_typed_event_and_snapshot_are_deterministic():
    def run():
        current, attacker = game(choose_first)
        execute_trigger(current, attacker)
        current.check_invariants()
        return current.snapshot()

    first, second = run(), run()
    assert first == second
    assert any(
        event.get("rules_event") == RulesEventKind.DISCARD_DRAW.value for event in first["events"]
    )


def test_authoritative_coverage_membership_and_digests_are_locked():
    recognized, payload, full = coverage_sets()
    assert [member[1] for member in recognized] == ["Cool but Rude", "Null Group Biological Assets"]
    assert recognized == payload
    assert [member[1] for member in full] == ["Null Group Biological Assets"]
    assert digest(recognized) == "0adbade241a770917df78da65282c73d2296a5fe8511f24bff46a47005549065"
    assert digest(payload) == "0adbade241a770917df78da65282c73d2296a5fe8511f24bff46a47005549065"
    assert digest(full) == "71732520f3cf6094c7ea9d2dee6377d5677cb6448a7876ba803cda9bbc200821"


def test_frozen_roster_coverage_is_two_cards_across_two_decks():
    recognized, payload, full = coverage_sets()
    names = {member[1] for member in recognized}
    decks = {
        path.parent.name: {
            line.split(" ", 1)[1]
            for line in path.read_text(encoding="utf-8").splitlines()
            if line and line != "Deck"
        }
        for path in ROOT.glob("decks/*/PROTOTYPE_0.1.txt")
    }
    assert names == {"Cool but Rude", "Null Group Biological Assets"}
    assert {name for name, cards in decks.items() if names & cards} == {
        "casey_jones",
        "raphael",
    }
    assert {member[1] for member in payload} == names
    assert {member[1] for member in full} == {"Null Group Biological Assets"}


def test_no_card_name_dispatch_or_parallel_zone_mutation():
    source = inspect.getsource(CardInterpreter.discard_draw_semantic_coverage)
    engine = inspect.getsource(Game.commit_discard_draw)
    assert "Null Group" not in source + engine
    assert "Cool but Rude" not in source + engine
    assert "self.move_object(" in engine and "self.draw(" in engine
    assert "player.hand.append" not in engine
