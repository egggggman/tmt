import json
from pathlib import Path

import pytest

from tmnt_design_studio.card_interpreter07 import CardInterpreter, CastKind
from tmnt_design_studio.engine07 import CardFact, CardObject, Game, Permanent

PLAINS = CardFact("Plains", "", 0, "Basic Land — Plains")
MAKE_YOUR_MOVE = CardFact(
    "Make Your Move",
    "{2}{W}",
    3,
    "Instant",
    "Destroy target artifact, enchantment, or creature with power 4 or greater.",
    oracle_id="8226f31d-6f51-49c3-87f7-0c68f7f4f9ce",
)
ARTIFACT = CardFact("Relic", "{1}", 1, "Artifact", power=2, toughness=2)
ENCHANTMENT = CardFact("Aura", "{1}{W}", 2, "Enchantment")
SMALL_CREATURE = CardFact("Scout", "{1}{W}", 2, "Creature — Turtle", power=2, toughness=2)
LARGE_CREATURE = CardFact("Bruiser", "{3}{W}", 4, "Creature — Turtle", power=4, toughness=4)


def game_with_spell() -> Game:
    game = Game(([PLAINS] * 60, [PLAINS] * 60), seed=661)
    game.begin_turn()
    for _ in range(4):
        game.create_permanent(PLAINS, 0, summoning_sick=False)
    game.set_hand_for_testing(0, [MAKE_YOUR_MOVE])
    return game


@pytest.mark.parametrize("target_card", [ARTIFACT, ENCHANTMENT, LARGE_CREATURE])
@pytest.mark.parametrize("controller", [0, 1])
def test_exact_spell_destroys_each_legal_current_permanent_type(target_card, controller):
    game = game_with_spell()
    target = game.create_permanent(target_card, controller, summoning_sick=False)
    spell = game.announce_spell(0, game.players[0].hand[0], target)

    assert spell is not None
    assert spell.cast_kind is CastKind.DESTROY_ARTIFACT_ENCHANTMENT_OR_POWER_4_CREATURE
    assert spell.target_id == target.object_id
    result = game.resolve_top_of_stack()

    assert isinstance(result, CardObject)
    assert target.zone == "former"
    assert any(card.card is target_card for card in game.players[target.owner].graveyard)
    reference = next(
        item
        for item in game.snapshot()["conformance"]["executed_references"]
        if item["evidence_kind"] == "spell_resolved"
    )
    assert reference["oracle_fragment"] == MAKE_YOUR_MOVE.oracle_text
    game.check_invariants()


def test_target_generation_uses_current_types_and_power_not_printed_shortcuts():
    game = game_with_spell()
    printed_artifact = game.create_permanent(ARTIFACT, 1, summoning_sick=False)
    printed_artifact.type_line_override = "Creature — Construct"
    printed_small = game.create_permanent(SMALL_CREATURE, 1, summoning_sick=False)
    printed_small.type_line_override = "Artifact"
    large = game.create_permanent(LARGE_CREATURE, 1, summoning_sick=False)
    large.counters["-1/-1"] = 1

    targets = {
        action.target_id
        for action in game.legal_main_actions(0)
        if action.kind.value == "cast" and action.object_id == game.players[0].hand[0].object_id
    }

    assert printed_artifact.object_id not in targets
    assert printed_small.object_id in targets
    assert large.object_id not in targets


def test_resolution_rechecks_current_legality_and_does_not_destroy_illegal_target():
    game = game_with_spell()
    target = game.create_permanent(LARGE_CREATURE, 1, summoning_sick=False)
    spell = game.announce_spell(0, game.players[0].hand[0], target)
    assert spell is not None
    target.counters["-1/-1"] = 1

    game.resolve_top_of_stack()

    assert game.is_authoritative(target, "battlefield")
    assert any(
        event["event"] == "spell_resolved_no_effect" and event["reason"] == "all_targets_illegal"
        for event in game.events
    )


def test_locked_target_cannot_relink_to_a_new_incarnation():
    game = game_with_spell()
    target = game.create_permanent(ARTIFACT, 1, summoning_sick=False)
    spell = game.announce_spell(0, game.players[0].hand[0], target)
    assert spell is not None
    game.destroy(target)
    replacement = game.create_permanent(ARTIFACT, 1, summoning_sick=False)

    game.resolve_top_of_stack()

    assert game.is_authoritative(replacement, "battlefield")
    assert spell.target_id != replacement.object_id


def test_fabricated_stale_wrong_zone_and_small_creature_targets_fail_without_payment():
    game = game_with_spell()
    card = game.players[0].hand[0]
    small = game.create_permanent(SMALL_CREATURE, 1, summoning_sick=False)
    artifact = game.create_permanent(ARTIFACT, 1, summoning_sick=False)
    game.destroy(artifact)
    fabricated = Permanent("object-fabricated", ARTIFACT, 1, 1)
    tapped_before = [permanent.tapped for permanent in game.players[0].battlefield]

    assert game.announce_spell(0, card, small) is None
    assert game.announce_spell(0, card, artifact) is None
    assert game.announce_spell(0, card, fabricated) is None
    assert game.is_authoritative(card, "hand")
    assert [permanent.tapped for permanent in game.players[0].battlefield] == tapped_before


@pytest.mark.parametrize(
    "text",
    [
        "Destroy target artifact or enchantment.",
        "Destroy target creature with power 4 or greater.",
        "Destroy target artifact, enchantment, or creature with power 3 or greater.",
        "You may destroy target artifact, enchantment, or creature with power 4 or greater.",
        "Destroy target artifact, enchantment, or creature with power 4 or greater. Draw a card.",
    ],
)
def test_near_neighbor_grammar_remains_unsupported(text):
    card = CardFact("Neighbor", "{2}{W}", 3, "Instant", text)
    interpreter = CardInterpreter()

    assert interpreter.destroy_permanent_semantic_coverage(card, text) is None
    assert interpreter.cast_program(card).kind is CastKind.UNSUPPORTED
    assert interpreter.unsupported_fragments(card)


def test_exact_text_requires_a_direct_spell_parent():
    interpreter = CardInterpreter()
    permanent = CardFact(
        "Static Neighbor",
        "{2}{W}",
        3,
        "Creature — Turtle",
        MAKE_YOUR_MOVE.oracle_text,
        power=3,
        toughness=3,
    )

    semantics = interpreter.destroy_permanent_semantic_coverage(permanent, permanent.oracle_text)

    assert semantics is not None
    assert not semantics.coverage.fully_supported
    assert semantics.limitations == ("destroy_nonspell_source_not_implemented",)
    assert interpreter.cast_program(permanent).kind is CastKind.CREATURE
    assert interpreter.unsupported_fragments(permanent) == (
        (permanent.oracle_text, "destroy_nonspell_source_not_implemented"),
    )


def test_frozen_corpus_membership_is_make_your_move_only():
    root = Path(__file__).resolve().parents[1]
    cards = json.loads((root / "cardcade/card-model-0.6.json").read_text())["cards"]
    matches = {
        name: card
        for name, card in cards.items()
        if card["oracle_text"] == MAKE_YOUR_MOVE.oracle_text
    }
    printings = json.loads(
        (root / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json").read_text(encoding="utf-8")
    )

    assert matches == {
        "Make Your Move": {
            "oracle_id": "8226f31d-6f51-49c3-87f7-0c68f7f4f9ce",
            "mana_cost": "{2}{W}",
            "mana_value": 3,
            "type_line": "Instant",
            "oracle_text": MAKE_YOUR_MOVE.oracle_text,
            "keywords": [],
        }
    }
    assert [
        (card["name"], card["oracle_id"], card["set"], card["collector_number"])
        for card in printings
        if card["oracle_text"] == MAKE_YOUR_MOVE.oracle_text
    ] == [
        (
            "Make Your Move",
            "8226f31d-6f51-49c3-87f7-0c68f7f4f9ce",
            "tmt",
            "20",
        )
    ]
