import hashlib
import inspect
import json
from pathlib import Path

import pytest

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import (
    ActivatedEffectKind,
    CardInterpreter,
    InterpretedReturnToHandSemantics,
    ReturnClause,
    ReturnToHandProgram,
    TokenCreationProgram,
    TokenDefinition,
)
from tmnt_design_studio.engine07 import ActionKind, CardFact, Game, Permanent
from tmnt_design_studio.semantic_coverage import SemanticCoverage

ROOT = Path(__file__).resolve().parents[1]
LAND = CardFact("Plains", "", 0, "Basic Land — Plains", "({T}: Add {W}.)")
PET = CardFact(
    "Renamed Pet",
    "{1}{W}",
    2,
    "Creature — Dinosaur",
    "{1}{W}, {T}: Return another target creature you control to its owner's hand. "
    "Activate only during your turn.",
    1,
    2,
)
BEAR = CardFact("Bear", "{1}{G}", 2, "Creature — Bear", "", 2, 2)
ROCK = CardFact("Rock", "{1}", 1, "Artifact", "")


def authoritative_card(name):
    return load_card_data(
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json",
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json",
    ).resolve_name(name)


def game(seed=901):
    current = Game(([LAND] * 60, [LAND] * 60), seed=seed)
    current.begin_turn()
    return current


def setup_activation(*, target_owner=0, target_controller=0):
    current = game()
    current.create_permanent(LAND, 0, summoning_sick=False)
    current.create_permanent(LAND, 0, summoning_sick=False)
    source = current.create_permanent(PET, 0, summoning_sick=False)
    target = current.create_permanent(BEAR, target_owner, summoning_sick=False)
    if target_controller != target_owner:
        current.change_controller(target, target_controller)
    return current, source, target


def resolve(current):
    for _ in range(2):
        current.execute_priority_action(
            current.legal_priority_actions(current.priority_state.player_index)[0]
        )
    current.process_priority_resolution()


def activation_option(current, target):
    return next(
        option
        for option in current.legal_main_actions(0)
        if option.kind is ActionKind.ACTIVATE_ABILITY and option.target_id == target.object_id
    )


def test_generic_oracle_interpretation_and_broad_recognition():
    interpreter = CardInterpreter()
    semantics = interpreter.activated_ability_semantics(PET, PET.oracle_text)
    assert semantics is not None and semantics.coverage.fully_supported
    assert semantics.program.effect_kind is (
        ActivatedEffectKind.RETURN_ANOTHER_CREATURE_YOU_CONTROL_TO_OWNERS_HAND
    )
    broad = interpreter.return_to_hand_semantics(
        BEAR, "Return all creatures to their owners' hands."
    )
    assert broad is not None
    assert not broad.coverage.payload_executable
    assert not broad.coverage.fully_supported
    assert "return_target_shape_not_implemented" in broad.limitations


def test_generic_return_interpretation_is_independent_of_activated_delivery():
    text = "Return another target creature you control to its owner's hand."
    semantics = CardInterpreter().return_to_hand_semantics(BEAR, text)
    assert semantics is not None and semantics.program.executable
    assert semantics.coverage.payload_executable
    assert not semantics.coverage.parent_executable
    assert not semantics.coverage.fully_supported
    assert semantics.limitations == ("return_parent_context_not_implemented",)


@pytest.mark.parametrize(
    ("effect", "limitation"),
    (
        (
            "Draw a card. Return another target creature you control to its owner's hand.",
            "return_preceding_semantics_not_implemented",
        ),
        (
            "Return another target creature you control to its owner's hand. You gain 1 life.",
            "return_followup_semantics_not_implemented",
        ),
    ),
)
def test_executable_payload_does_not_upgrade_unsupported_surrounding_semantics(effect, limitation):
    text = f"{{1}}, {{T}}: {effect} Activate only during your turn."
    card = CardFact("Renamed Fixture", "", 0, "Creature", text, 1, 1)
    child = CardInterpreter().return_to_hand_semantics(card, text)
    activation = CardInterpreter().activated_ability_semantics(card, text)
    assert child is not None and child.coverage.payload_executable
    assert not child.coverage.fully_supported
    assert limitation in child.limitations
    assert activation is not None and not activation.coverage.fully_supported
    assert limitation in activation.limitations


def test_activated_interpretation_consumes_generic_return_result_and_limitations():
    limitation = "dummy_non_token_action_context_not_implemented"

    class ReturnFixtureInterpreter(CardInterpreter):
        def __init__(self):
            self.calls = 0

        def return_to_hand_semantics(self, card, fragment):
            self.calls += 1
            return InterpretedReturnToHandSemantics(
                ReturnToHandProgram(True, True),
                SemanticCoverage(True, False, True, (limitation,)),
                ReturnClause(
                    "Return another target creature you control to its owner's hand",
                    0,
                    64,
                    "",
                    ".",
                ),
                "",
                ".",
                True,
                True,
            )

    interpreter = ReturnFixtureInterpreter()
    semantics = interpreter.activated_ability_semantics(PET, PET.oracle_text)
    assert interpreter.calls == 1
    assert semantics is not None
    assert semantics.child_payload_executable
    assert not semantics.coverage.fully_supported
    assert semantics.limitations == (limitation,)
    source = inspect.getsource(CardInterpreter.activated_ability_semantics)
    assert "owner's hand" not in source
    assert "return_to_hand_semantics" in source


def test_supported_return_parent_payload_and_surrounding_semantics_are_full():
    interpreter = CardInterpreter()
    child = interpreter.return_to_hand_semantics(PET, PET.oracle_text)
    activation = interpreter.activated_ability_semantics(PET, PET.oracle_text)
    assert child is not None and child.coverage.fully_supported
    assert child.limitations == ()
    assert activation is not None and activation.coverage.fully_supported
    assert activation.limitations == ()


def test_text_on_both_sides_and_case_punctuation_variants_stay_explicit():
    text = (
        "{1}, {T}: CHOOSE ONE. RETURN another target creature you control to its owner's hand! "
        "Draw a card. Activate only during your turn."
    )
    card = CardFact("Case Fixture", "", 0, "Creature", text, 1, 1)
    semantics = CardInterpreter().return_to_hand_semantics(card, text)
    assert semantics is not None and semantics.coverage.payload_executable
    assert not semantics.preceding_executable
    assert not semantics.followup_executable
    assert not semantics.coverage.fully_supported
    assert "return_preceding_semantics_not_implemented" in semantics.limitations
    assert "return_followup_semantics_not_implemented" in semantics.limitations


@pytest.mark.parametrize(
    "text",
    (
        "Draw a card and put it into your hand.",
        "A returned creature enters tapped.",
        "Return target creature to the battlefield.",
    ),
)
def test_no_return_to_hand_false_positive(text):
    assert CardInterpreter().return_to_hand_semantics(BEAR, text) is None


@pytest.mark.parametrize(
    ("card_name", "expected_clause", "preceding", "following", "limitations"),
    (
        (
            "Nobody",
            "return up to one other target artifact you control to its owner's hand",
            "When this creature enters, ",
            ". Scry 1. (Look at the top card of your library. You may put that card "
            "on the bottom.)",
            {
                "return_target_shape_not_implemented",
                "return_parent_context_not_implemented",
                "return_preceding_semantics_not_implemented",
                "return_followup_semantics_not_implemented",
            },
        ),
        (
            "Karai, Future of the Foot",
            "return target creature card from your graveyard to your hand",
            "Whenever Karai deals combat damage to a player, ",
            ". If her sneak cost was paid this turn, instead return that card to the battlefield.",
            {
                "return_target_shape_not_implemented",
                "return_parent_context_not_implemented",
                "return_preceding_semantics_not_implemented",
                "return_followup_semantics_not_implemented",
            },
        ),
        (
            "Northampton Farm",
            "Return each other card exiled with this land to its owner's hand",
            "Return a creature card exiled with this land to the battlefield under your control. ",
            ".",
            {
                "return_target_shape_not_implemented",
                "return_parent_context_not_implemented",
                "return_preceding_semantics_not_implemented",
            },
        ),
        (
            "Together Forever",
            "return that card to its owner's hand",
            "Choose target creature with a counter on it. When that creature dies this turn, ",
            ".",
            {
                "return_target_shape_not_implemented",
                "return_parent_context_not_implemented",
                "return_preceding_semantics_not_implemented",
            },
        ),
        (
            "Ashcoat of the Shadow Swarm",
            "return up to two Rat creature cards from your graveyard to your hand",
            "At the beginning of your end step, you may mill four cards. If you do, ",
            ". (To mill a card, put the top card of your library into your graveyard.)",
            {
                "return_target_shape_not_implemented",
                "return_parent_context_not_implemented",
                "return_preceding_semantics_not_implemented",
                "return_followup_semantics_not_implemented",
            },
        ),
        (
            "Turtles in Time",
            "Return all creatures to their owners' hands",
            "",
            ". Each player may shuffle their hand and graveyard into their library, then each "
            "player who does draws seven cards.",
            {
                "return_target_shape_not_implemented",
                "return_parent_context_not_implemented",
                "return_followup_semantics_not_implemented",
            },
        ),
    ),
)
def test_authoritative_compound_return_clause_boundaries(
    card_name, expected_clause, preceding, following, limitations
):
    card = authoritative_card(card_name)
    matches = []
    for fragment in CardInterpreter().fragments(card):
        semantics = CardInterpreter().return_to_hand_semantics(card, fragment)
        if semantics is not None and semantics.clause.text == expected_clause:
            matches.append(semantics)
    assert len(matches) == 1
    semantics = matches[0]
    assert semantics.preceding_semantics == preceding
    assert semantics.following_semantics == following
    card_fragment = next(
        fragment
        for fragment in CardInterpreter().fragments(card)
        if fragment[semantics.clause.start : semantics.clause.end] == expected_clause
    )
    assert semantics.clause.preceding_text == card_fragment[: semantics.clause.start]
    assert semantics.clause.following_text == card_fragment[semantics.clause.end :]
    assert not semantics.coverage.payload_executable
    assert not semantics.coverage.fully_supported
    assert semantics.preceding_executable == (not preceding)
    assert semantics.followup_executable == (
        not CardInterpreter._meaningful_semantic_text(following)
    )
    assert set(semantics.limitations) == limitations


@pytest.mark.parametrize(
    ("card_name", "prefix", "suffix"),
    (
        ("Northampton Farm", "{2}, {T}, Sacrifice this land:", "."),
        ("Together Forever", "{1}:", "."),
        (
            "Prehistoric Pet",
            "{1}{W}, {T}:",
            ". Activate only during your turn.",
        ),
    ),
)
def test_raw_clause_evidence_preserves_activation_parent_text(card_name, prefix, suffix):
    card = authoritative_card(card_name)
    semantics = next(
        result
        for fragment in CardInterpreter().fragments(card)
        if (result := CardInterpreter().return_to_hand_semantics(card, fragment)) is not None
        and (card_name != "Northampton Farm" or "each other card" in result.clause.text)
    )
    assert semantics.clause.preceding_text.startswith(prefix)
    assert semantics.clause.following_text == suffix


def test_legal_option_is_targeted_deterministically_and_return_creates_new_identity():
    current, source, target = setup_activation()
    options = [
        option
        for option in current.legal_main_actions(0)
        if option.kind is ActionKind.ACTIVATE_ABILITY
    ]
    assert [option.target_id for option in options] == [target.object_id]
    assert current.execute_main_action(options[0])
    assert current.stack[-1].target_ids == (target.object_id,)
    resolve(current)
    replacement = current.players[0].hand[-1]
    assert replacement.card == target.card
    assert replacement.object_id != target.object_id
    assert target.zone == "former"
    assert not current.is_authoritative(target, "battlefield")
    assert source.tapped


def test_controlled_but_not_owned_target_returns_to_owner():
    current, _, target = setup_activation(target_owner=1, target_controller=0)
    current.execute_main_action(activation_option(current, target))
    resolve(current)
    assert all(card.card != BEAR for card in current.players[0].hand)
    assert current.players[1].hand[-1].card == BEAR
    assert current.players[1].hand[-1].controller == 1


@pytest.mark.parametrize("bad", ["fabricated", "source", "opponent", "noncreature"])
def test_illegal_or_fabricated_targets_are_rejected_without_payment(bad):
    current, source, target = setup_activation()
    if bad == "fabricated":
        target_id = "obj-fabricated"
    elif bad == "source":
        target_id = source.object_id
    elif bad == "opponent":
        other = current.create_permanent(BEAR, 1, summoning_sick=False)
        target_id = other.object_id
    else:
        other = current.create_permanent(ROCK, 0, summoning_sick=False)
        target_id = other.object_id
    before = (
        source.tapped,
        tuple(current.stack),
        tuple(current.players[0].battlefield),
        len(current.events),
    )
    assert (
        current.announce_activated_ability(0, source, PET.oracle_text, target_ids=(target_id,))
        is None
    )
    assert (
        source.tapped,
        tuple(current.stack),
        tuple(current.players[0].battlefield),
        len(current.events),
    ) == before
    assert not source.tapped and not current.stack
    assert current.is_authoritative(target, "battlefield")


def test_target_that_changes_zone_or_control_is_illegal_at_resolution_and_costs_stay_paid():
    current, source, target = setup_activation()
    current.execute_main_action(activation_option(current, target))
    current.change_controller(target, 1)
    resolve(current)
    assert current.is_authoritative(target, "battlefield")
    assert target.controller == 1 and source.tapped
    assert any(
        event["event"] == "activated_ability_resolved_no_effect"
        and event["reason"] == "target_illegal_at_resolution"
        for event in current.events
    )


def test_target_that_leaves_battlefield_while_stacked_is_not_rebound():
    current, source, target = setup_activation()
    current.execute_main_action(activation_option(current, target))
    replacement = current.move_object(target, "graveyard", reason="adversarial_probe")
    resolve(current)
    assert current.is_authoritative(replacement, "graveyard")
    assert source.tapped
    assert all(card.card != BEAR for card in current.players[0].hand)


def test_wrong_zone_and_stale_target_cannot_be_announced_or_rebound():
    current, source, target = setup_activation()
    replacement = current.move_object(target, "hand", reason="probe")
    assert (
        current.announce_activated_ability(
            0, source, PET.oracle_text, target_ids=(target.object_id,)
        )
        is None
    )
    assert (
        current.announce_activated_ability(
            0, source, PET.oracle_text, target_ids=(replacement.object_id,)
        )
        is None
    )


def test_battlefield_state_does_not_follow_returned_object():
    current, _, target = setup_activation()
    target.tapped = True
    target.damage = 1
    target.counters["+1/+1"] = 2
    current.execute_main_action(activation_option(current, target))
    resolve(current)
    replacement = current.players[0].hand[-1]
    assert not isinstance(replacement, Permanent)
    assert not hasattr(replacement, "damage")
    assert not hasattr(replacement, "counters")
    assert replacement.controller == replacement.owner


def test_token_target_ceases_at_state_based_action_boundary():
    current, _, _ = setup_activation()
    token = current.create_tokens(
        0,
        TokenCreationProgram(
            TokenDefinition("Bear", "Token Creature — Bear", ("G",), 1, 1),
            1,
            False,
        ),
        source_card="Fixture",
        oracle_fragment="Create a 1/1 green Bear creature token.",
    )[0]
    current.execute_main_action(activation_option(current, token))
    resolve(current)
    assert all(not card.is_token for card in current.players[0].hand)
    assert any(event["event"] == "token_ceased" for event in current.events)


def test_repeated_resolution_is_rejected():
    current, _, target = setup_activation()
    current.execute_main_action(activation_option(current, target))
    ability = current.stack[-1]
    resolve(current)
    with pytest.raises(ValueError):
        current._resolve_activated_ability(ability)


def test_no_card_name_or_acceptance_special_case_dispatch():
    sources = "\n".join(
        (
            inspect.getsource(CardInterpreter.return_to_hand_semantics),
            inspect.getsource(CardInterpreter.activated_ability_semantics),
            inspect.getsource(Game.legal_activated_ability_actions),
            inspect.getsource(Game._resolve_activated_ability),
        )
    )
    assert "Prehistoric Pet" not in sources
    assert "7001" not in sources


def test_return_recognition_membership_is_stable_and_authoritative():
    catalog = load_card_data(
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json",
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json",
    )
    interpreter = CardInterpreter()
    members = []
    executable = []
    seen = set()
    for card in sorted(catalog.cards, key=lambda item: (item.name, item.oracle_id)):
        if card.oracle_id in seen:
            continue
        seen.add(card.oracle_id)
        for fragment in interpreter.fragments(card):
            semantics = interpreter.return_to_hand_semantics(card, fragment)
            if semantics is None:
                continue
            assert semantics.clause.text
            assert 0 <= semantics.clause.start < semantics.clause.end <= len(fragment)
            assert fragment[semantics.clause.start : semantics.clause.end] == semantics.clause.text
            assert fragment[: semantics.clause.start] == semantics.clause.preceding_text
            assert fragment[semantics.clause.end :] == semantics.clause.following_text
            assert (
                semantics.clause.preceding_text
                + semantics.clause.text
                + semantics.clause.following_text
                == fragment
            )
            repeated = interpreter.return_to_hand_semantics(card, fragment)
            assert repeated is not None and repeated.clause == semantics.clause
            assert semantics.coverage.fully_supported == (
                semantics.coverage.payload_executable
                and semantics.coverage.parent_executable
                and semantics.coverage.followup_executable
                and not semantics.coverage.limitations
            )
            if interpreter._meaningful_semantic_text(semantics.preceding_semantics):
                assert not semantics.preceding_executable
                assert "return_preceding_semantics_not_implemented" in semantics.limitations
            if interpreter._meaningful_semantic_text(semantics.following_semantics):
                assert not semantics.followup_executable
                assert "return_followup_semantics_not_implemented" in semantics.limitations
            member = (card.oracle_id, card.name, fragment)
            members.append(member)
            if semantics.coverage.payload_executable:
                executable.append(member)
    assert len({item[0] for item in members}) == 37 and len(members) == 38
    assert len({item[0] for item in executable}) == 1 and len(executable) == 1
    assert {name for _, name, _ in executable} == {"Prehistoric Pet"}
    encoded = json.dumps(members, ensure_ascii=False, separators=(",", ":")).encode()
    executable_encoded = json.dumps(executable, ensure_ascii=False, separators=(",", ":")).encode()
    assert (
        hashlib.sha256(encoded).hexdigest()
        == "59bb7f7c2a44fea44e7b94b5f47e6030beb2b25205b009f350a67b35a9b9cd59"
    )
    assert (
        hashlib.sha256(executable_encoded).hexdigest()
        == "8de28e00a41e8fedc23667860d223f241c22f6dbac89b12cd218cb5bb3aeca95"
    )
