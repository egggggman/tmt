import hashlib
import inspect
import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter, ScryProgram
from tmnt_design_studio.engine07 import CardFact, Game, RulesEventKind, ScryOption
from tmnt_design_studio.pilot07 import PassingPilot
from tmnt_design_studio.semantic_coverage import SemanticCoverage

ROOT = Path(__file__).resolve().parents[1]
LANDS = [CardFact(f"Numbered Land {number}", "", 0, "Basic Land — Island") for number in range(20)]
RECOGNIZED_NAMES = {
    "April O'Neil, Kunoichi Trainee",
    "Dream Beavers",
    "Hamato Guardian Stance",
    "Insectoid Exterminator",
    "Lita, Little Orphan Amphibian",
    "Nobody",
    "Path of Ancestry",
}
FULL_NAMES = {"April O'Neil, Kunoichi Trainee", "Lita, Little Orphan Amphibian"}
ROSTER_NAMES = {
    "April O'Neil, Kunoichi Trainee",
    "Dream Beavers",
    "Hamato Guardian Stance",
    "Insectoid Exterminator",
    "Lita, Little Orphan Amphibian",
}


def game(seed=41, chooser=None, deck_size=20):
    deck = LANDS[:deck_size]
    return Game((deck, deck), seed=seed, scry_chooser=chooser)


def top_ids(current, player=0, count=3):
    return tuple(card.object_id for card in reversed(current.players[player].library[-count:]))


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
            semantics = interpreter.scry_semantic_coverage(card, fragment)
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


def test_fixed_scry_is_oracle_derived_and_distinct_from_related_library_actions():
    interpreter = CardInterpreter()
    assert interpreter.scry_program("Scry 2.") == ScryProgram(2)
    assert interpreter.scry_program("Completely Renamed — Scry 2.") == ScryProgram(2)
    assert interpreter.scry_program("Scry X.") == ScryProgram(
        None, "dynamic_scry_amount_not_implemented"
    )
    for text in (
        "Look at the top two cards of your library.",
        "Surveil 2.",
        "Draw two cards.",
        "Mill two cards.",
        "Search your library for a card.",
    ):
        assert interpreter.scry_program(text) is None


def test_generic_semantic_coverage_keeps_payload_parent_and_followup_separate():
    interpreter = CardInterpreter()
    card = CardFact("Renamed", "", 0, "Enchantment", "Whenever you draw, scry 1.")
    semantics = interpreter.scry_semantic_coverage(card, card.oracle_text)
    assert semantics is not None
    assert semantics.coverage == SemanticCoverage(
        True, False, True, ("scry_preceding_or_trigger_context_not_implemented",)
    )
    assert not semantics.coverage.fully_supported


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ("If you control a Mutant, scry 1.", "scry_condition_context_not_implemented"),
        ("{T}: Scry 1.", "scry_activation_context_not_implemented"),
        (
            "{T}: Add one mana. When that mana is spent to cast a creature, scry 1.",
            "scry_preceding_or_trigger_context_not_implemented",
        ),
        ("Draw a card, then scry 1.", "scry_preceding_effect_not_implemented"),
        ("Scry 1, then draw a card.", "scry_followup_semantics_not_implemented"),
    ],
)
def test_unsupported_contexts_remain_explicit(text, reason):
    card = CardFact("Generic", "", 0, "Enchantment", text)
    semantics = CardInterpreter().scry_semantic_coverage(card, text)
    assert semantics is not None and reason in semantics.limitations
    assert not semantics.coverage.fully_supported


def test_all_top_all_bottom_and_mixed_order_are_legal_and_authoritative():
    current = game()
    before = top_ids(current)
    current.scry(0, ScryProgram(3), source_card="Generic", oracle_fragment="Scry 3.")
    assert top_ids(current) == before

    current.scry_chooser = lambda view, options: next(
        option
        for option in options
        if not option.top_ids
        and option.bottom_ids == tuple(object_id for object_id, _name in view.cards)
    )
    former_top = top_ids(current)
    current.scry(0, ScryProgram(3), source_card="Generic", oracle_fragment="Scry 3.")
    assert tuple(card.object_id for card in current.players[0].library[:3]) == former_top

    current.scry_chooser = lambda view, options: next(
        option
        for option in options
        if option.top_ids == (view.cards[1][0], view.cards[0][0])
        and option.bottom_ids == (view.cards[2][0],)
    )
    inspected = top_ids(current)
    current.scry(0, ScryProgram(3), source_card="Generic", oracle_fragment="Scry 3.")
    assert top_ids(current, count=2) == (inspected[1], inspected[0])
    assert current.players[0].library[0].object_id == inspected[2]


def test_scry_inspects_available_cards_when_library_is_smaller_than_requested():
    current = game(deck_size=8)
    assert len(current.players[0].library) == 1
    only = current.players[0].library[-1]
    choice = current.scry(0, ScryProgram(5), source_card="Generic", oracle_fragment="Scry 5.")
    assert choice.top_ids == (only.object_id,)


@pytest.mark.parametrize(
    "bad_choice",
    [
        ScryOption(("object-fabricated",), ()),
        ScryOption((), ()),
    ],
)
def test_fabricated_incomplete_and_stale_choices_are_atomic(bad_choice):
    current = game()
    before = tuple(current.players[0].library)
    current.scry_chooser = lambda _view, _options: bad_choice
    with pytest.raises(ValueError):
        current.scry(0, ScryProgram(2), source_card="Generic", oracle_fragment="Scry 2.")
    assert tuple(current.players[0].library) == before
    assert not any(event["event"] == "scry_committed" for event in current.events)


def test_chooser_cannot_mutate_authoritative_library_and_failed_choice_rolls_back():
    current = game()
    before = tuple(current.players[0].library)

    def malicious(view, options):
        current.players[0].library.reverse()
        return options[0]

    current.scry_chooser = malicious
    with pytest.raises(ValueError, match="stale"):
        current.scry(0, ScryProgram(2), source_card="Generic", oracle_fragment="Scry 2.")
    assert tuple(current.players[0].library) == before


def test_private_view_and_options_are_immutable_and_public_view_hides_library():
    observed = {}

    def chooser(view, options):
        observed.update(view=view, options=options)
        return next(
            option for option in options if option.top_ids == tuple(x[0] for x in view.cards)
        )

    current = game(chooser=chooser)
    current.scry(0, ScryProgram(2), source_card="Generic", oracle_fragment="Scry 2.")
    with pytest.raises(FrozenInstanceError):
        observed["view"].requested = 9
    assert isinstance(observed["options"], tuple)
    assert not hasattr(current.public_view(), "libraries")


def test_scry_emits_typed_and_auditable_evidence_without_changing_membership():
    current = game()
    before = {id(card) for card in current.players[0].library}
    current.scry(0, ScryProgram(2), source_card="Generic", oracle_fragment="Scry 2.")
    assert {id(card) for card in current.players[0].library} == before
    rules = [event for event in current.events if event.get("rules_event") == "scried"]
    commits = [event for event in current.events if event["event"] == "scry_committed"]
    assert len(rules) == len(commits) == 1
    assert rules[0]["subject_ids"] == commits[0]["inspected_ids"]
    assert current.scry_evidence[0].inspected_ids == tuple(commits[0]["inspected_ids"])
    assert current.scry_evidence[0].source_card == "Generic"
    assert current.scry_evidence[0].oracle_fragment == "Scry 2."
    assert RulesEventKind.SCRIED.value == "scried"


def test_passing_pilot_can_make_a_poor_but_legal_choice():
    pilot = PassingPilot()
    current = game(chooser=pilot.choose_scry)
    before = top_ids(current, count=2)
    current.scry(0, ScryProgram(2), source_card="Generic", oracle_fragment="Scry 2.")
    assert tuple(card.object_id for card in current.players[0].library[:2]) == before


def test_unsupported_parent_does_not_deliver_scry_but_direct_etb_does():
    current = game()
    unsupported = CardFact(
        "Renamed Trigger", "{1}{U}", 2, "Creature", "Whenever you draw a card, scry 1.", 2, 2
    )
    permanent = current.create_permanent(unsupported, 0)
    current._process_creature_entered_triggers(permanent)
    assert not any(event.get("rules_event") == "scried" for event in current.events)

    direct = CardFact(
        "Renamed Scout", "{1}{U}", 2, "Creature", "When Renamed Scout enters, scry 1.", 2, 2
    )
    permanent = current.create_permanent(direct, 0)
    current._process_creature_entered_triggers(permanent)
    assert sum(event.get("rules_event") == "scried" for event in current.events) == 1


def test_authoritative_memberships_and_digests_are_locked():
    recognized, executable, full = coverage_sets()
    assert len({member[0] for member in recognized}) == 7 and len(recognized) == 7
    assert executable == recognized
    assert len(full) == 2
    assert {member[1] for member in recognized} == RECOGNIZED_NAMES
    assert {member[1] for member in full} == FULL_NAMES
    assert digest(recognized) == "e62415c25929c3022801aefbcec0a0f562bba372d9ed15f2021d536179ae71a2"
    assert digest(executable) == "e62415c25929c3022801aefbcec0a0f562bba372d9ed15f2021d536179ae71a2"
    assert digest(full) == "8b1050d4ce183e29ad65f2a3b59346f2704db3bf7e5053990d732c86c5870f96"


def test_frozen_roster_membership_and_deck_exposure_are_locked():
    recognized, executable, full = coverage_sets()
    decks = {
        path.parent.name: {
            line.split(" ", 1)[1]
            for line in path.read_text(encoding="utf-8").splitlines()
            if line and line != "Deck"
        }
        for path in ROOT.glob("decks/*/PROTOTYPE_0.1.txt")
    }
    all_names = set().union(*decks.values())
    assert {member[1] for member in recognized} & all_names == ROSTER_NAMES
    assert {member[1] for member in executable} & all_names == ROSTER_NAMES
    assert {member[1] for member in full} & all_names == FULL_NAMES
    assert {name for name, cards in decks.items() if cards & ROSTER_NAMES} == {
        "leonardo",
        "shredder",
        "splinter",
    }


def test_no_card_name_dispatch_and_deterministic_replay():
    sources = (
        inspect.getsource(CardInterpreter.scry_program),
        inspect.getsource(CardInterpreter.scry_semantic_coverage),
        inspect.getsource(Game.scry),
    )
    for name in RECOGNIZED_NAMES:
        assert all(name not in source for source in sources)

    def exercise():
        current = game(seed=7001)
        current.scry_chooser = lambda view, options: next(
            option
            for option in options
            if not option.top_ids
            and option.bottom_ids == tuple(object_id for object_id, _name in reversed(view.cards))
        )
        current.scry(0, ScryProgram(3), source_card="Generic", oracle_fragment="Scry 3.")
        return tuple(card.object_id for card in current.players[0].library), current.events

    assert exercise() == exercise()
