import hashlib
import inspect
import json
from pathlib import Path

import pytest

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter, HandBottomDrawProgram
from tmnt_design_studio.engine07 import (
    CardFact,
    Game,
    HandBottomDrawOption,
    RulesEventKind,
)
from tmnt_design_studio.semantic_coverage import SemanticCoverage

ROOT = Path(__file__).resolve().parents[1]
PLAINS = CardFact("Plains", "", 0, "Basic Land — Plains")
MOUNTAIN = CardFact("Mountain", "", 0, "Basic Land — Mountain")
BEAR = CardFact("Bear", "{1}{G}", 2, "Creature — Bear", power=2, toughness=2)
FRAGMENT = (
    "Renamed Missile deals 3 damage to target creature. "
    "You may put a card from your hand on the bottom of your library. "
    "If you do, draw a card."
)
MISSILE = CardFact("Renamed Missile", "{1}{R}", 2, "Instant", FRAGMENT)


def catalog():
    return load_card_data(
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json",
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json",
    )


def coverage_sets():
    interpreter = CardInterpreter()
    recognized, executable, full = [], [], []
    seen = set()
    for card in sorted(catalog().cards, key=lambda value: (value.name, value.oracle_id)):
        if card.oracle_id in seen:
            continue
        seen.add(card.oracle_id)
        for fragment in interpreter.fragments(card):
            semantics = interpreter.hand_bottom_draw_semantic_coverage(card, fragment)
            if semantics is None:
                continue
            member = (card.oracle_id, card.name, fragment)
            recognized.append(member)
            if semantics.coverage.payload_executable:
                executable.append(member)
            if semantics.coverage.fully_supported:
                full.append(member)
    return recognized, executable, full


def digest(members):
    encoded = json.dumps(members, ensure_ascii=False, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def game(chooser=None, seed=91):
    current = Game(
        ([PLAINS] * 20, [PLAINS] * 20),
        seed=seed,
        hand_bottom_draw_chooser=chooser,
    )
    current.begin_turn()
    return current


def choose_first(_view, options):
    return next(option for option in options if option.card_id is not None)


def prepare_spell(current, target_card=None, extra_hand=(BEAR, PLAINS)):
    for land in (MOUNTAIN, PLAINS):
        current.create_permanent(land, 0, summoning_sick=False)
    spell = current.set_hand_for_testing(0, [MISSILE, *extra_hand])[0]
    target = current.create_permanent(
        target_card or CardFact("Large", "{4}", 4, "Creature", power=4, toughness=5),
        1,
    )
    stacked = current.announce_spell(0, spell, target)
    assert stacked is not None
    return stacked, target


def test_oracle_grammar_is_generic_and_exactly_bounded():
    interpreter = CardInterpreter()
    semantics = interpreter.hand_bottom_draw_semantic_coverage(MISSILE, FRAGMENT)
    renamed = interpreter.hand_bottom_draw_semantic_coverage(
        CardFact("Other Name", "", 0, "Instant", FRAGMENT), FRAGMENT
    )
    assert semantics == renamed
    assert semantics is not None
    assert semantics.program == HandBottomDrawProgram(1, 1, True, True)
    assert semantics.coverage == SemanticCoverage(True, True, True, ())
    assert semantics.clause_text.startswith("You may put a card")


@pytest.mark.parametrize(
    "fragment",
    [
        "Draw a card.",
        "Discard a card, then draw a card.",
        "Put two cards from your hand on the bottom of your library. Draw two cards.",
        "You may put a card from your graveyard on the bottom of your library. "
        "If you do, draw a card.",
    ],
)
def test_related_draw_and_filter_semantics_are_not_recognized(fragment):
    card = CardFact("Generic", "", 0, "Instant", fragment)
    assert CardInterpreter().hand_bottom_draw_semantic_coverage(card, fragment) is None


def test_unsupported_parent_and_followup_remain_explicit():
    interpreter = CardInterpreter()
    trigger = (
        "Whenever you attack, You may put a card from your hand on the bottom of your "
        "library. If you do, draw a card."
    )
    semantics = interpreter.hand_bottom_draw_semantic_coverage(MISSILE, trigger)
    assert semantics is not None and semantics.coverage.payload_executable
    assert not semantics.coverage.parent_executable
    assert "hand_bottom_draw_parent_context_not_implemented" in semantics.limitations

    compound = FRAGMENT + " Then create a token."
    semantics = interpreter.hand_bottom_draw_semantic_coverage(MISSILE, compound)
    assert semantics is not None and not semantics.coverage.followup_executable
    assert "hand_bottom_draw_followup_semantics_not_implemented" in semantics.limitations


def test_declining_moves_nothing_and_does_not_draw():
    current = game()
    stacked, target = prepare_spell(current)
    hand_ids = tuple(card.object_id for card in current.players[0].hand)
    library_ids = tuple(card.object_id for card in current.players[0].library)
    current.resolve_top_of_stack()
    assert target.damage == 3
    assert tuple(card.object_id for card in current.players[0].hand) == hand_ids
    assert tuple(card.object_id for card in current.players[0].library) == library_ids
    evidence = current.hand_bottom_draw_evidence[-1]
    assert evidence.declined and evidence.source_id == stacked.object_id
    assert evidence.offered_choice_ids == (None, *hand_ids)
    assert evidence.pre_hand_ids == evidence.post_hand_ids == hand_ids
    assert evidence.pre_library_ids == evidence.post_library_ids == library_ids
    assert not evidence.movement_succeeded
    assert not evidence.conditional_draw_performed


def test_empty_hand_offers_only_decline_and_does_not_draw():
    current = game()
    _stacked, target = prepare_spell(current, extra_hand=())
    library_ids = tuple(card.object_id for card in current.players[0].library)
    current.resolve_top_of_stack()
    evidence = current.hand_bottom_draw_evidence[-1]
    assert target.damage == 3
    assert evidence.offered_choice_ids == (None,)
    assert evidence.declined and not evidence.movement_succeeded
    assert evidence.pre_hand_ids == evidence.post_hand_ids == ()
    assert evidence.pre_library_ids == evidence.post_library_ids == library_ids


def test_accepting_moves_to_bottom_then_draws_top_with_new_identities():
    current = game(choose_first)
    stacked, target = prepare_spell(current)
    selected = current.players[0].hand[0]
    old_top = current.players[0].library[-1]
    current.resolve_top_of_stack()

    evidence = current.hand_bottom_draw_evidence[-1]
    assert target.damage == 3 and evidence.source_id == stacked.object_id
    assert evidence.selected_hand_id == selected.object_id
    assert evidence.library_bottom_id != selected.object_id
    assert evidence.drawn_library_id == old_top.object_id
    assert evidence.drawn_hand_id != old_top.object_id
    assert selected.zone == old_top.zone == "former"
    assert current.players[0].library[0].object_id == evidence.library_bottom_id
    assert current.players[0].hand[-1].object_id == evidence.drawn_hand_id
    assert evidence.offered_choice_ids == (None, *evidence.pre_hand_ids)
    assert evidence.movement_succeeded and evidence.conditional_draw_performed
    assert evidence.pre_library_ids[-1] == evidence.drawn_library_id
    assert evidence.post_library_ids == (
        evidence.library_bottom_id,
        *evidence.pre_library_ids[:-1],
    )
    assert evidence.post_hand_ids == (
        *(object_id for object_id in evidence.pre_hand_ids if object_id != selected.object_id),
        evidence.drawn_hand_id,
    )


def test_empty_library_draws_the_selected_card_as_another_new_object():
    current = game(choose_first)
    current.players[0].library.clear()
    selected = current.players[0].hand[0]
    program = HandBottomDrawProgram(1, 1, True, True)
    plan = current.choose_hand_bottom_draw(0, program)
    evidence = current.commit_hand_bottom_draw(
        0, program, plan, source_id="source", oracle_fragment=FRAGMENT
    )
    assert not current.players[0].library
    assert evidence.selected_hand_id == selected.object_id
    assert evidence.library_bottom_id == evidence.drawn_library_id
    assert evidence.drawn_hand_id != evidence.library_bottom_id
    assert selected.zone == "former"
    assert evidence.pre_library_ids == evidence.post_library_ids == ()
    assert evidence.movement_succeeded and evidence.conditional_draw_performed


def test_fabricated_choice_is_rejected_without_partial_filter_mutation():
    current = game(lambda _view, _options: HandBottomDrawOption("fabricated"))
    _stacked, target = prepare_spell(current)
    hand_before = tuple(current.players[0].hand)
    library_before = tuple(current.players[0].library)
    with pytest.raises(ValueError, match="listed option"):
        current.resolve_top_of_stack()
    assert target.damage == 3
    assert tuple(current.players[0].hand) == hand_before
    assert tuple(current.players[0].library) == library_before
    assert not current.hand_bottom_draw_evidence


def test_chooser_cannot_mutate_authoritative_hand_or_library():
    def malicious(view, options):
        del view
        current.players[0].hand.reverse()
        return options[0]

    current = game(malicious)
    _stacked, target = prepare_spell(current)
    hand_before = tuple(current.players[0].hand)
    library_before = tuple(current.players[0].library)
    with pytest.raises(ValueError, match="mutated authoritative zones"):
        current.resolve_top_of_stack()
    assert target.damage == 3
    assert tuple(current.players[0].hand) == hand_before
    assert tuple(current.players[0].library) == library_before
    assert not current.hand_bottom_draw_evidence


def test_stale_plan_is_rejected_before_commit():
    current = game(choose_first)
    program = HandBottomDrawProgram(1, 1, True, True)
    plan = current.choose_hand_bottom_draw(0, program)
    current.move_object(current.players[0].hand[-1], "graveyard", reason="test")
    before = current.snapshot()
    with pytest.raises(ValueError, match="became stale"):
        current.commit_hand_bottom_draw(
            0, program, plan, source_id="source", oracle_fragment=FRAGMENT
        )
    assert current.snapshot() == before


def test_illegal_target_counters_entire_spell_and_skips_filter():
    current = game(choose_first)
    _stacked, target = prepare_spell(current)
    current.put_into_graveyard(target)
    current.resolve_top_of_stack()
    assert not current.hand_bottom_draw_evidence


def test_damage_sba_waits_until_sequential_instructions_finish():
    observations = []

    def chooser(_view, options):
        observations.append(
            (
                target.zone,
                target.damage,
                tuple(object_id for object_id, _name in _view.cards),
                tuple(card.object_id for card in current.players[0].hand),
            )
        )
        return next(option for option in options if option.card_id is not None)

    current = game(chooser)
    stacked, target = prepare_spell(
        current, CardFact("Small", "{1}", 1, "Creature", power=1, toughness=3)
    )
    current.resolve_top_of_stack()
    event_names = [event["event"] for event in current.events]
    filter_index = event_names.index("hand_bottom_draw_committed")
    lethal_index = next(
        index
        for index, event in enumerate(current.events)
        if event["event"] == "zone_changed" and event.get("reason") == "lethal_damage"
    )
    spell_index = next(
        index
        for index, event in enumerate(current.events)
        if event["event"] == "zone_changed" and event.get("source_object_id") == stacked.object_id
    )
    assert observations == [
        (
            "battlefield",
            3,
            observations[0][3],
            observations[0][3],
        )
    ]
    assert filter_index < spell_index < lethal_index


def test_failed_bottom_movement_cannot_trigger_draw(monkeypatch):
    current = game(choose_first)
    program = HandBottomDrawProgram(1, 1, True, True)
    plan = current.choose_hand_bottom_draw(0, program)
    hand_before = tuple(current.players[0].hand)
    library_before = tuple(current.players[0].library)
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
        current.commit_hand_bottom_draw(
            0, program, plan, source_id="source", oracle_fragment=FRAGMENT
        )
    assert not draw_called
    assert tuple(current.players[0].hand) == hand_before
    assert tuple(current.players[0].library) == library_before
    assert not current.hand_bottom_draw_evidence


def test_equal_valued_cards_remain_distinct_choices_and_identities():
    chosen_id = None

    def choose_second(view, options):
        nonlocal chosen_id
        assert len({name for _object_id, name in view.cards}) == 1
        chosen_id = view.cards[1][0]
        return next(option for option in options if option.card_id == chosen_id)

    current = game(choose_second)
    program = HandBottomDrawProgram(1, 1, True, True)
    plan = current.choose_hand_bottom_draw(0, program)
    evidence = current.commit_hand_bottom_draw(
        0, program, plan, source_id="source", oracle_fragment=FRAGMENT
    )
    assert len(set(evidence.pre_hand_ids)) == len(evidence.pre_hand_ids)
    assert evidence.selected_hand_id == chosen_id
    assert evidence.library_bottom_id not in evidence.pre_hand_ids


def test_evidence_remains_reconstructive_after_later_zone_changes():
    current = game(choose_first)
    prepare_spell(current)
    current.resolve_top_of_stack()
    evidence = current.hand_bottom_draw_evidence[-1]
    serialized = current.snapshot()["hand_bottom_draw"][0]
    drawn = next(
        card for card in current.players[0].hand if card.object_id == evidence.drawn_hand_id
    )
    current.move_object(drawn, "graveyard", reason="later_test_movement")

    assert evidence.offered_choice_ids == (None, *evidence.pre_hand_ids)
    assert evidence.pre_library_ids[-1] == evidence.drawn_library_id
    assert evidence.post_library_ids[0] == evidence.library_bottom_id
    assert evidence.post_hand_ids[-1] == evidence.drawn_hand_id
    assert serialized["pre_hand_ids"] == list(evidence.pre_hand_ids)
    assert serialized["post_library_ids"] == list(evidence.post_library_ids)


def test_typed_evidence_and_snapshot_are_deterministic():
    def run_once():
        current = game(choose_first, seed=123)
        prepare_spell(current)
        current.resolve_top_of_stack()
        current.check_invariants()
        return current.snapshot()

    first = run_once()
    second = run_once()
    assert first == second
    assert first["hand_bottom_draw"][0]["declined"] is False
    assert any(
        event["rules_event"] == RulesEventKind.HAND_BOTTOM_DRAW.value
        for event in first["events"]
        if event["event"] == "rules_event"
    )


def test_authoritative_corpus_membership_and_digests_are_locked():
    recognized, executable, full = coverage_sets()
    assert len(recognized) == len(executable) == len(full) == 1
    assert recognized == executable == full
    assert recognized[0][1] == "Manhole Missile"
    assert digest(recognized) == "cb1c664c8b157f87bace7c9a2012bb69ab598e1d142cc6a2024e532575b443e8"


def test_frozen_roster_exposure_is_one_card_across_two_decks():
    recognized, _, _ = coverage_sets()
    names = {member[1] for member in recognized}
    decks = {
        path.parent.name: {
            line.split(" ", 1)[1]
            for line in path.read_text(encoding="utf-8").splitlines()
            if line and line != "Deck"
        }
        for path in ROOT.glob("decks/*/PROTOTYPE_0.1.txt")
    }
    assert names == {"Manhole Missile"}
    assert {name for name, cards in decks.items() if names & cards} == {
        "casey_jones",
        "raphael",
    }


def test_no_card_name_dispatch_or_parallel_draw_implementation():
    interpreter_source = inspect.getsource(CardInterpreter.hand_bottom_draw_semantic_coverage)
    engine_source = inspect.getsource(Game.commit_hand_bottom_draw)
    assert "Manhole Missile" not in interpreter_source + engine_source
    assert "self.draw(" in engine_source
    assert "player.hand.append" not in engine_source
