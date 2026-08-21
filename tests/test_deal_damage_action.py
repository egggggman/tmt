import copy
import hashlib
import inspect
import json
from pathlib import Path

import pytest

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import (
    CardInterpreter,
    DamageProgram,
    DamageTargetKind,
)
from tmnt_design_studio.engine07 import CardFact, DamageTransaction, Game, RulesEventKind
from tmnt_design_studio.semantic_coverage import SemanticCoverage

ROOT = Path(__file__).resolve().parents[1]
PLAINS = CardFact("Plains", "", 0, "Basic Land — Plains")
MOUNTAIN = CardFact("Mountain", "", 0, "Basic Land — Mountain")
BEAR = CardFact("Bear", "{1}{G}", 2, "Creature — Bear", power=2, toughness=2)
SOURCE = CardFact("Generic Source", "{1}{R}", 2, "Creature — Mutant", power=2, toughness=3)
RECOGNIZED_NAMES = {
    "All Will Be One",
    "Blasphemous Act",
    "Bot Bashing Time",
    "Brilliance Unleashed",
    "Casey Jones, Back Alley Brute",
    "City of Brass",
    "Cool but Rude",
    "Electric Seaweed",
    "Everything Pizza",
    "Exploding Barrel",
    "General Traag, Heart of Stone",
    "Go Ninja Go",
    "Grand Coliseum",
    "Hamato Ninpō",
    "Jennika's Technique",
    "Manhole Missile",
    "Mouser Foundry",
    "Raphael, Tough Turtle",
    "Shellshock",
    "Slash, Reptile Rampager",
    "Special Move",
    "Spicy Oatmeal Pizza",
    "Storm of Steel",
    "Super Combo",
    "Swift Demise",
    "Tenderize",
    "Tokka & Rahzar, Terrible Twos",
    "Weather Maker",
}
EXECUTABLE_NAMES = {
    "Bot Bashing Time",
    "Brilliance Unleashed",
    "City of Brass",
    "Cool but Rude",
    "Exploding Barrel",
    "General Traag, Heart of Stone",
    "Grand Coliseum",
    "Manhole Missile",
    "Mouser Foundry",
    "Raphael, Tough Turtle",
    "Slash, Reptile Rampager",
    "Swift Demise",
}
FULL_NAMES = {"Manhole Missile", "Raphael, Tough Turtle", "Slash, Reptile Rampager"}
ROSTER_RECOGNIZED = {
    "Cool but Rude",
    "Manhole Missile",
    "Mouser Foundry",
    "Raphael, Tough Turtle",
    "Spicy Oatmeal Pizza",
    "Tenderize",
}
ROSTER_EXECUTABLE = {
    "Cool but Rude",
    "Manhole Missile",
    "Mouser Foundry",
    "Raphael, Tough Turtle",
}


def game(seed: int = 41) -> Game:
    current = Game(([PLAINS] * 60, [PLAINS] * 60), seed=seed)
    current.begin_turn()
    return current


def transaction(
    source,
    *,
    amount: int = 1,
    target=None,
    target_player: int | None = None,
    target_kind: DamageTargetKind = DamageTargetKind.CREATURE,
) -> DamageTransaction:
    return DamageTransaction(
        0,
        source,
        target_kind,
        amount,
        "Renamed Source deals 1 damage to target creature.",
        target,
        target_player,
    )


def catalog():
    return load_card_data(
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json",
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json",
    )


def coverage_sets():
    interpreter = CardInterpreter()
    seen = set()
    recognized = []
    executable = []
    fully_supported = []
    for card in sorted(catalog().cards, key=lambda value: (value.name, value.oracle_id)):
        if card.oracle_id in seen:
            continue
        seen.add(card.oracle_id)
        for fragment in interpreter.fragments(card):
            semantics = interpreter.damage_semantic_coverage(card, fragment)
            if semantics is None:
                continue
            member = (card.oracle_id, card.name, fragment)
            recognized.append(member)
            if semantics.coverage.payload_executable:
                executable.append(member)
            if semantics.coverage.fully_supported:
                fully_supported.append(member)
    return recognized, executable, fully_supported


def digest(members) -> str:
    encoded = json.dumps(members, ensure_ascii=False, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def test_fixed_damage_program_is_oracle_derived_and_card_name_independent():
    interpreter = CardInterpreter()
    first = interpreter.damage_program("Alpha deals 4 damage to target creature.")
    renamed = interpreter.damage_program("Completely Renamed deals 4 damage to target creature.")

    assert first == renamed == DamageProgram(4, DamageTargetKind.CREATURE, "target_creature")
    assert first.executable


@pytest.mark.parametrize(
    ("fragment", "reasons"),
    [
        ("A deals X damage to target creature.", ("dynamic_damage_amount_not_implemented",)),
        (
            "A deals damage equal to its power to any target.",
            ("dynamic_damage_amount_not_implemented", "damage_any_target_not_implemented"),
        ),
        ("A deals 2 damage to each creature.", ("multiple_damage_targets_not_implemented",)),
        (
            "A deals 2 damage to one or two targets.",
            ("multiple_damage_targets_not_implemented",),
        ),
        ("A deals 2 damage to any target.", ("damage_any_target_not_implemented",)),
    ],
)
def test_explicit_payload_exclusions(fragment, reasons):
    card = CardFact("Generic Source", "{1}", 1, "Sorcery", fragment)
    semantics = CardInterpreter().damage_semantic_coverage(card, fragment)
    assert semantics is not None and not semantics.program.executable
    assert semantics.coverage.limitations == reasons


@pytest.mark.parametrize(
    "fragment",
    [
        "A deals 2 damage to each of one or two targets.",
        "A deals 2 damage to each of up to 2 targets.",
    ],
)
def test_variable_count_multiple_target_grammar_is_recognized_but_not_executable(fragment):
    card = CardFact("Renamed Multi-Target Spell", "{1}{R}", 2, "Instant", fragment)
    semantics = CardInterpreter().damage_semantic_coverage(card, fragment)

    assert semantics is not None
    assert not semantics.coverage.payload_executable
    assert semantics.coverage.parent_executable
    assert semantics.coverage.followup_executable
    assert not semantics.coverage.fully_supported
    assert semantics.coverage.limitations == (
        "variable_count_multiple_damage_targets_not_implemented",
    )


def test_recognized_divided_damage_spell_cannot_deliver_a_transaction():
    fragment = "Renamed Spell deals 2 damage to each of one or two targets."
    spell = CardFact("Renamed Spell", "{1}{R}", 2, "Sorcery", fragment)
    current = game()
    current.create_permanent(MOUNTAIN, 0, summoning_sick=False)
    current.create_permanent(PLAINS, 0, summoning_sick=False)
    card = current.set_hand_for_testing(0, [spell])[0]
    target = current.create_permanent(BEAR, 1, summoning_sick=False)
    before = current.snapshot()

    assert current.announce_spell(0, card, target) is None
    assert target.damage == 0
    assert not any(event["event"] == "damage_dealt" for event in current.events)
    assert current.players[0].life == before["players"][0]["life"]
    assert current.players[1].life == before["players"][1]["life"]


def test_multi_kind_target_is_not_truncated_or_mislabeled_as_followup():
    fragment = (
        "Whenever a counter is put on a permanent, this enchantment deals that much damage "
        "to target opponent, creature an opponent controls, or planeswalker an opponent controls."
    )
    card = CardFact("Renamed Enchantment", "{3}{R}{R}", 5, "Enchantment", fragment)
    semantics = CardInterpreter().damage_semantic_coverage(card, fragment)

    assert semantics is not None
    assert not semantics.coverage.payload_executable
    assert not semantics.coverage.parent_executable
    assert semantics.coverage.followup_executable
    assert semantics.coverage.limitations == (
        "dynamic_damage_amount_not_implemented",
        "damage_multi_kind_target_not_implemented",
        "damage_trigger_context_not_implemented",
    )
    assert "damage_followup_semantics_not_implemented" not in semantics.coverage.limitations


@pytest.mark.parametrize(
    ("fragment", "reason"),
    [
        (
            "Whenever a creature enters, This deals 1 damage to target opponent.",
            "damage_trigger_context_not_implemented",
        ),
        (
            "{T}: This deals 1 damage to target opponent.",
            "damage_activation_context_not_implemented",
        ),
        ("• This deals 1 damage to target opponent.", "damage_choice_context_not_implemented"),
    ],
)
def test_executable_payload_does_not_upgrade_unsupported_parent(fragment, reason):
    card = CardFact("Arbitrary", "{1}", 1, "Enchantment", fragment)
    semantics = CardInterpreter().damage_semantic_coverage(card, fragment)
    assert semantics is not None
    assert semantics.coverage.payload_executable
    assert not semantics.coverage.parent_executable
    assert not semantics.coverage.fully_supported
    assert reason in semantics.coverage.limitations


def test_unsupported_followup_survives_generic_coverage():
    fragment = "Spell deals 3 damage to target creature. Then draw a card."
    card = CardFact("Spell", "{1}{R}", 2, "Instant", fragment)
    semantics = CardInterpreter().damage_semantic_coverage(card, fragment)

    assert semantics is not None and isinstance(semantics.coverage, SemanticCoverage)
    assert semantics.coverage.payload_executable and semantics.coverage.parent_executable
    assert not semantics.coverage.followup_executable
    assert semantics.coverage.limitations == ("damage_followup_semantics_not_implemented",)


def test_fixed_damage_spell_uses_stack_transaction_and_retains_followup_limitation():
    fragment = (
        "Renamed Blast deals 6 damage to target creature. "
        "If that creature would die this turn, exile it instead."
    )
    spell = CardFact("Renamed Blast", "{5}{R}", 6, "Sorcery", fragment)
    large = CardFact("Large Creature", "{7}", 7, "Creature", power=7, toughness=7)
    current = game()
    for land in [MOUNTAIN, *([PLAINS] * 5)]:
        current.create_permanent(land, 0, summoning_sick=False)
    card = current.set_hand_for_testing(0, [spell])[0]
    target = current.create_permanent(large, 1, summoning_sick=False)

    announced = current.announce_spell(0, card, target)
    assert announced is not None and announced.zone == "stack"
    current.resolve_top_of_stack()

    assert target.damage == 6 and target.zone == "battlefield"
    unsupported = [event for event in current.events if event["event"] == "unsupported_semantics"]
    assert [(event["oracle_fragment"], event["reason"]) for event in unsupported] == [
        (fragment, "damage_followup_semantics_not_implemented")
    ]


def test_player_damage_is_transactional_and_emits_typed_evidence():
    current = game()
    source = current.create_permanent(SOURCE, 0, summoning_sick=False)
    before_other = current.players[1].life
    event = current.deal_damage(
        transaction(
            source,
            amount=2,
            target_kind=DamageTargetKind.PLAYER,
            target_player=1,
        )
    )

    assert current.players[1].life == before_other - 2
    assert event.kind is RulesEventKind.DAMAGE_DEALT
    assert event.source_id == source.object_id
    assert event.target_player == 1 and event.amount == 2
    evidence = next(item for item in current.events if item["event"] == "damage_dealt")
    assert evidence["source_id"] == source.object_id
    assert evidence["target_player"] == current.players[1].name
    assert evidence["amount"] == 2 and evidence["combat"] is False


def test_lethal_player_damage_uses_existing_life_loss_boundary():
    current = game()
    source = current.create_permanent(SOURCE, 0, summoning_sick=False)
    current.players[1].life = 1
    current.deal_damage(
        transaction(
            source,
            target_kind=DamageTargetKind.PLAYER,
            target_player=1,
        )
    )
    assert current.players[1].lost
    assert current.players[1].loss_reason == "life_zero_or_less"
    assert current.winner == 0


def test_creature_damage_is_marked_and_lethal_is_applied_only_by_sba():
    current = game()
    source = current.create_permanent(SOURCE, 0, summoning_sick=False)
    nonlethal = current.create_permanent(BEAR, 1, summoning_sick=False)
    current.deal_damage(transaction(source, target=nonlethal))
    assert nonlethal.damage == 1 and nonlethal.zone == "battlefield"

    lethal = current.create_permanent(BEAR, 1, summoning_sick=False)
    current.deal_damage(transaction(source, amount=2, target=lethal))
    assert lethal.zone == "former"
    assert current.players[1].graveyard[-1].card is BEAR
    moved = next(
        item
        for item in reversed(current.events)
        if item["event"] == "zone_changed" and item.get("reason") == "lethal_damage"
    )
    assert moved["reason"] == "lethal_damage"


def test_nonlethal_damage_persists_until_cleanup():
    current = game()
    source = current.create_permanent(SOURCE, 0, summoning_sick=False)
    target = current.create_permanent(BEAR, 1, summoning_sick=False)
    current.deal_damage(transaction(source, target=target))
    current.end_turn()
    assert target.damage == 0


@pytest.mark.parametrize("fabrication", ["target", "source"])
def test_fabricated_equal_valued_runtime_objects_are_rejected_atomically(fabrication):
    current = game()
    source = current.create_permanent(SOURCE, 0, summoning_sick=False)
    target = current.create_permanent(BEAR, 1, summoning_sick=False)
    fabricated = copy.copy(target if fabrication == "target" else source)
    before = current.snapshot()
    proposal = transaction(
        fabricated if fabrication == "source" else source,
        target=fabricated if fabrication == "target" else target,
    )

    with pytest.raises(ValueError, match="authoritative|target"):
        current.deal_damage(proposal)
    assert current.snapshot() == before


def test_stale_and_illegal_targets_are_rejected_without_partial_mutation():
    current = game()
    source = current.create_permanent(SOURCE, 0, summoning_sick=False)
    stale = current.create_permanent(BEAR, 1, summoning_sick=False)
    current.put_into_graveyard(stale)
    land = current.create_permanent(PLAINS, 1, summoning_sick=False)
    for candidate in (stale, land, current.players[1].hand[0]):
        before = current.snapshot()
        with pytest.raises(ValueError, match="creature target"):
            current.deal_damage(transaction(source, target=candidate))
        assert current.snapshot() == before


def test_damage_is_not_life_loss_destroy_or_minus_toughness():
    current = game()
    source = current.create_permanent(SOURCE, 0, summoning_sick=False)
    target = current.create_permanent(BEAR, 1, summoning_sick=False)
    current.deal_damage(transaction(source, target=target))

    assert target.damage == 1
    assert target.toughness == 2 and target.zone == "battlefield"
    names = [event["event"] for event in current.events]
    assert "life_lost" not in names and "permanent_destroyed" not in names


def test_alliance_damage_executes_only_through_supported_parent():
    fragment = (
        "Alliance — Whenever another creature you control enters, "
        "This creature deals 1 damage to target opponent."
    )
    source_card = CardFact("Renamed Alliance Source", "{1}{R}", 2, "Creature", fragment, 2, 2)
    current = game()
    source = current.create_permanent(source_card, 0, summoning_sick=False)
    before = current.players[1].life
    current.create_permanent(BEAR, 0)
    current._process_creature_entered_triggers(current.players[0].battlefield[-1])

    assert current.players[1].life == before - 1
    damage = [event for event in current.events if event["event"] == "damage_dealt"]
    assert len(damage) == 1 and damage[0]["source_id"] == source.object_id


def test_unsupported_trigger_parent_is_not_delivered_by_engine():
    fragment = "Whenever you draw a card, This deals 1 damage to target opponent."
    source_card = CardFact("Renamed Unsupported Source", "{1}{R}", 2, "Creature", fragment, 2, 2)
    current = game()
    current.create_permanent(source_card, 0, summoning_sick=False)
    before = current.players[1].life
    current.create_permanent(BEAR, 0)
    current._process_creature_entered_triggers(current.players[0].battlefield[-1])
    assert current.players[1].life == before


def test_authoritative_memberships_and_digests_are_locked():
    recognized, executable, fully_supported = coverage_sets()
    assert len({member[0] for member in recognized}) == 28 and len(recognized) == 29
    assert len({member[0] for member in executable}) == 12 and len(executable) == 12
    assert len({member[0] for member in fully_supported}) == 3 and len(fully_supported) == 3
    assert {member[1] for member in recognized} == RECOGNIZED_NAMES
    assert {member[1] for member in executable} == EXECUTABLE_NAMES
    assert {member[1] for member in fully_supported} == FULL_NAMES
    assert digest(recognized) == "b8aa5f14cda90075a37af4cac2fab889d6c5f3299973cf4303f603e180e0d39a"
    assert digest(executable) == "5c977d6a1386af69dc65c694dcb146d1e5b52a7278a085df61ae667b852a89f1"
    assert (
        digest(fully_supported)
        == "94f348e8fc17c6cd1fe7f4da62a45735c0641df27b7ea44582c3f007b4765e9c"
    )


def test_frozen_roster_memberships_are_locked():
    recognized, executable, fully_supported = coverage_sets()
    decks = {
        path.parent.name: {
            line.split(" ", 1)[1]
            for line in path.read_text(encoding="utf-8").splitlines()
            if line and line != "Deck"
        }
        for path in ROOT.glob("decks/*/PROTOTYPE_0.1.txt")
    }
    all_names = set().union(*decks.values())
    assert {member[1] for member in recognized} & all_names == ROSTER_RECOGNIZED
    assert {member[1] for member in executable} & all_names == ROSTER_EXECUTABLE
    assert {member[1] for member in fully_supported} & all_names == {
        "Manhole Missile",
        "Raphael, Tough Turtle",
    }
    assert {name for name, cards in decks.items() if cards & ROSTER_RECOGNIZED} == {
        "casey_jones",
        "michelangelo",
        "raphael",
    }
    assert {name for name, cards in decks.items() if cards & ROSTER_EXECUTABLE} == {
        "casey_jones",
        "raphael",
    }


def test_no_card_name_dispatch_in_damage_interpreter_or_transaction():
    interpreter_source = inspect.getsource(CardInterpreter.damage_program)
    coverage_source = inspect.getsource(CardInterpreter.damage_semantic_coverage)
    engine_source = inspect.getsource(Game.deal_damage)
    for name in RECOGNIZED_NAMES:
        assert name not in interpreter_source
        assert name not in coverage_source
        assert name not in engine_source


def test_deterministic_damage_identity_and_events():
    def exercise():
        current = game(seed=7001)
        source = current.create_permanent(SOURCE, 0, summoning_sick=False)
        target = current.create_permanent(BEAR, 1, summoning_sick=False)
        current.deal_damage(transaction(source, target=target))
        return current.snapshot()

    assert exercise() == exercise()
