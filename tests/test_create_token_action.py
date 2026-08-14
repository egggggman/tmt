import copy
import hashlib
import inspect
import json
from pathlib import Path

import pytest

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import (
    CardInterpreter,
    TokenCreationProgram,
    TokenDefinition,
)
from tmnt_design_studio.engine07 import CardFact, CardObject, Game, RulesEventKind
from tmnt_design_studio.semantic_coverage import SemanticCoverage

PLAINS = CardFact("Plains", "", 0, "Basic Land — Plains")
BEAR = CardFact("Bear", "{1}{W}", 2, "Creature — Bear", power=2, toughness=2)
ROOT = Path(__file__).resolve().parents[1]
EXPECTED_RECOGNIZED_NAMES = {
    "April O'Neil, Human Element",
    "April O'Neil, Live on the Scene",
    "Baxter Stockman",
    "Big Apple, 3 a.m.",
    "Big Mother Mouser",
    "Biogenic Ooze",
    "Casey & Raph, Hotheads",
    "Chrome Dome",
    "Coin of Mastery",
    "Courier of Comestibles",
    "Crustacean Commando",
    "Dark Leo & Shredder",
    "Donatello, Gadget Master",
    "Doubling Season",
    "Endless Foot Assault",
    "Featherbrained Filcher",
    "Foot Chopper",
    "Foot Mystic",
    "Genghis Frog",
    "Here Comes a New Hero!",
    "Improvised Arsenal",
    "Jennika, Bad Apple Big Sister",
    "Lita, Little Orphan Amphibian",
    "Lord Dregg, Insect Invader",
    "Mechanized Ninja Cavalry",
    "Michelangelo, Mutant BFF",
    "Michelangelo, Weirdness to 11",
    "Michelangelo, the Heart",
    "Mighty Mutanimals",
    "Mona Lisa, Ever Adaptable",
    "Mouser Attack!",
    "Mouser Foundry",
    "Mutagen Man, Living Ooze",
    "Mutant Chain Reaction",
    "Ninja Pizza",
    "Old Hob, Alleycat Blues",
    "Ooze Spill",
    "Party Dude",
    "Pizza Face, Gastromancer",
    "Plague of Vermin",
    "Raphael, the Muscle",
    "Rat King, Pale Piper",
    "Rat King, Verminister",
    "Ravenous Robots",
    "Ray Fillet, Man Ray",
    "Return to the Sewers",
    "Roadkill Rodney",
    "Sally Pride, Lioness Leader",
    "Shellshock",
    "Shredder, Shadow Master",
    "Slash, Reptile Rampager",
    "Slithering Cryptid",
    "Splinter & Leo, Father & Son",
    "Splinter, the Mentor",
    "Tainted Treats",
    "Tempestra, Dame of Games",
    "The Cloning of Shredder",
    "The Last Ronin's Technique",
    "The Ooze",
    "Tokka & Rahzar, Unsupervised",
    "Triceraton Commander",
    "Turtle Blimp",
    "Uneasy Alliance",
    "Waste Not",
    "Wooden Cane",
    "Zoo Escapees",
}
EXPECTED_EXECUTABLE_NAMES = EXPECTED_RECOGNIZED_NAMES - {
    "Big Apple, 3 a.m.",
    "Big Mother Mouser",
    "Chrome Dome",
    "Donatello, Gadget Master",
    "Doubling Season",
    "Endless Foot Assault",
    "Here Comes a New Hero!",
    "Improvised Arsenal",
    "Mutagen Man, Living Ooze",
    "Plague of Vermin",
    "Sally Pride, Lioness Leader",
    "Shellshock",
    "Shredder, Shadow Master",
    "Tempestra, Dame of Games",
    "The Cloning of Shredder",
    "The Last Ronin's Technique",
    "Triceraton Commander",
}
EXPECTED_ROSTER_NAMES = {
    "Courier of Comestibles",
    "Crustacean Commando",
    "Donatello, Gadget Master",
    "Foot Mystic",
    "Improvised Arsenal",
    "Lita, Little Orphan Amphibian",
    "Michelangelo, Mutant BFF",
    "Michelangelo, Weirdness to 11",
    "Mighty Mutanimals",
    "Mouser Attack!",
    "Mouser Foundry",
    "Mutagen Man, Living Ooze",
    "Mutant Chain Reaction",
    "Ooze Spill",
    "Ravenous Robots",
    "Ray Fillet, Man Ray",
    "Return to the Sewers",
    "Slithering Cryptid",
    "Tainted Treats",
    "The Last Ronin's Technique",
    "Zoo Escapees",
}
EXPECTED_UNKNOWN_NAMES = {
    "Command Tower",
    "Arcane Signet",
    "Exotic Orchard",
    "Chromatic Lantern",
    "Fast Forward",
    "Double Jump // Flying Kick",
    "Plague of Vermin",
}


def game(seed: int = 91) -> Game:
    deck = [PLAINS] * 60
    current = Game((deck, deck), seed=seed)
    current.begin_turn()
    return current


def program(fragment: str) -> TokenCreationProgram:
    result = CardInterpreter().token_creation_program(fragment)
    assert result is not None
    return result


def authoritative_catalog():
    return load_card_data(
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json",
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json",
    )


def test_predefined_tokens_are_oracle_derived_without_enabling_their_activations():
    food = program("Create a Food token.")
    mutagen = program("Create a Mutagen token.")

    assert food.executable and food.definition == CardInterpreter.PREDEFINED_TOKENS["food"]
    assert food.definition.type_line == "Artifact — Food"
    assert "gain 3 life" in food.definition.oracle_text
    assert food.retained_limitation == "token_activated_ability_not_implemented"
    assert mutagen.executable and mutagen.definition.type_line == "Artifact — Mutagen"
    assert "Activate only as a sorcery" in mutagen.definition.oracle_text
    assert mutagen.retained_limitation == "token_activated_ability_not_implemented"


@pytest.mark.parametrize("token_name", ["Food", "Mutagen", "Treasure", "Clue"])
def test_predefined_token_creation_never_claims_its_activation(token_name):
    fragment = f"Create a {token_name} token."
    source = CardFact("Renamed Token Source", "{1}", 1, "Sorcery", fragment)
    coverage = CardInterpreter().token_semantic_coverage(source, fragment)

    assert coverage is not None and coverage.payload_executable
    assert not coverage.followup_executable
    assert not coverage.fully_supported
    assert coverage.program.retained_limitation == "token_activated_ability_not_implemented"
    assert (fragment, "token_activated_ability_not_implemented") in (
        CardInterpreter().unsupported_fragments(source)
    )


def test_fixed_explicit_creature_characteristics_quantity_and_tapped_state_are_typed():
    result = program("Create two tapped 1/1 black Ninja creature tokens with flying.")

    assert result.executable
    assert result.quantity == 2
    assert result.tapped
    assert result.definition == TokenDefinition(
        "Ninja",
        "Creature — Ninja",
        ("B",),
        1,
        1,
        keywords=("Flying",),
    )


@pytest.mark.parametrize(
    ("fragment", "reason"),
    [
        ("Create X 1/1 green Turtle creature tokens.", "variable_token_quantity_not_implemented"),
        ("Create a token that's a copy of target Equipment.", "token_copy_not_implemented"),
        (
            "If you would create a token, create twice that many of those tokens instead.",
            "token_replacement_effect_not_implemented",
        ),
        (
            "Create a 2/2 red Mutant creature token that's tapped and attacking.",
            "token_attacking_context_not_implemented",
        ),
    ],
)
def test_context_dependent_token_semantics_remain_explicitly_unsupported(fragment, reason):
    result = program(fragment)
    assert not result.executable
    assert result.unsupported_reason == reason


@pytest.mark.parametrize(
    ("card_name", "fragment_marker", "parent_executable", "parent_limitation", "followup"),
    [
        ("Waste Not", "discards", False, "token_trigger_context_not_implemented", None),
        (
            "Rat King, Pale Piper",
            "leaves the battlefield",
            False,
            "token_trigger_context_not_implemented",
            None,
        ),
        ("Biogenic Ooze", "When this creature enters", True, None, None),
        (
            "Biogenic Ooze",
            "{1}{G}{G}{G}",
            False,
            "token_activation_context_not_implemented",
            None,
        ),
        ("Jennika, Bad Apple Big Sister", "When Jennika enters", True, None, None),
        (
            "Ravenous Robots",
            "artifact spell",
            False,
            "token_trigger_context_not_implemented",
            None,
        ),
        ("Slash, Reptile Rampager", "Whenever Slash attacks", True, None, None),
        ("Baxter Stockman", "When Baxter Stockman enters", True, None, None),
        (
            "Dark Leo & Shredder",
            "combat damage",
            False,
            "token_trigger_context_not_implemented",
            "token_followup_semantics_not_implemented",
        ),
        ("Mechanized Ninja Cavalry", "When this creature enters", True, None, None),
        (
            "Turtle Blimp",
            "When this Vehicle enters",
            False,
            "token_trigger_context_not_implemented",
            None,
        ),
        ("Mighty Mutanimals", "When this creature enters", True, None, None),
        (
            "Rat King, Verminister",
            "At the beginning of your end step",
            False,
            "token_condition_context_not_implemented",
            "token_followup_semantics_not_implemented",
        ),
        (
            "Uneasy Alliance",
            "{5}, Sacrifice",
            False,
            "token_activation_context_not_implemented",
            None,
        ),
        (
            "Foot Mystic",
            "if a permanent left",
            False,
            "token_condition_context_not_implemented",
            None,
        ),
        (
            "Lord Dregg, Insect Invader",
            "if a permanent left",
            False,
            "token_condition_context_not_implemented",
            None,
        ),
        (
            "Mouser Attack!",
            "• Create",
            False,
            "token_choice_context_not_implemented",
            None,
        ),
        (
            "Mouser Foundry",
            "artifact enters or leaves",
            False,
            "token_trigger_context_not_implemented",
            None,
        ),
    ],
)
def test_all_eighteen_rejected_payloads_preserve_parent_and_followup_coverage(
    card_name, fragment_marker, parent_executable, parent_limitation, followup
):
    card = authoritative_catalog().resolve_name(card_name)
    fragment = next(
        item
        for item in CardInterpreter().fragments(card)
        if fragment_marker in item and CardInterpreter().token_creation_program(item) is not None
    )
    coverage = CardInterpreter().token_semantic_coverage(card, fragment)

    assert coverage is not None and coverage.payload_executable
    assert coverage.parent_executable is parent_executable
    assert coverage.parent_limitation == parent_limitation
    assert coverage.program.retained_limitation == followup
    assert coverage.fully_supported is (parent_executable and followup is None)
    reported = CardInterpreter().unsupported_fragments(card)
    if parent_limitation is not None:
        assert (fragment, parent_limitation) in reported
    if followup is not None:
        assert (fragment, followup) in reported


@pytest.mark.parametrize(
    ("oracle_text", "expected_reason"),
    [
        (
            "Whenever an opponent discards a card, create a 1/1 black Rat creature token.",
            "token_trigger_context_not_implemented",
        ),
        (
            "{2}, {T}: Create a 1/1 black Rat creature token.",
            "token_activation_context_not_implemented",
        ),
        (
            "When Test Source enters, if you attacked, create a 1/1 black Rat creature token.",
            "token_condition_context_not_implemented",
        ),
        (
            "Draw a card. Create a 1/1 black Rat creature token.",
            "token_preceding_effect_not_implemented",
        ),
    ],
)
def test_executable_child_never_upgrades_unsupported_parent(oracle_text, expected_reason):
    card = CardFact(
        "Renamed Context Fixture",
        "{1}{B}",
        2,
        "Creature — Test",
        oracle_text,
        power=2,
        toughness=2,
    )
    coverage = CardInterpreter().token_semantic_coverage(card, oracle_text)
    assert coverage is not None and coverage.payload_executable
    assert not coverage.parent_executable
    assert not coverage.fully_supported
    assert (oracle_text, expected_reason) in CardInterpreter().unsupported_fragments(card)


def test_unsupported_parent_prevents_child_execution_when_it_controls_timing():
    current = game()
    source = CardFact(
        "Renamed Conditional Fixture",
        "{1}{G}",
        2,
        "Creature — Test",
        "When Renamed Conditional Fixture enters, if you attacked this turn, create two 1/1 "
        "green Turtle creature tokens.",
        power=2,
        toughness=2,
    )
    permanent = current.create_permanent(source, 0, summoning_sick=True)

    current._process_creature_entered_triggers(permanent)

    assert not any(item.is_token for item in current.players[0].battlefield)
    coverage = CardInterpreter().token_semantic_coverage(source, source.oracle_text)
    assert coverage is not None and coverage.payload_executable
    assert coverage.parent_limitation == "token_condition_context_not_implemented"


def test_plague_grammar_is_generic_recognized_nonexecutable_and_unknown():
    card = authoritative_catalog().resolve_name("Plague of Vermin")
    coverage = CardInterpreter().token_semantic_coverage(card, card.oracle_text)

    assert coverage is not None
    assert not coverage.payload_executable
    assert coverage.program.unsupported_reason == "variable_token_quantity_not_implemented"
    assert coverage.parent_limitation == "token_iterative_choice_context_unknown"
    assert not coverage.fully_supported
    assert "Plague of Vermin" in EXPECTED_UNKNOWN_NAMES
    assert (card.oracle_text, "token_iterative_choice_context_unknown") in (
        CardInterpreter().unsupported_fragments(card)
    )


def test_create_token_interpretation_contains_no_source_card_name_dispatch():
    source = inspect.getsource(CardInterpreter.token_creation_program) + inspect.getsource(
        CardInterpreter.token_semantic_coverage
    )
    assert not any(name in source for name in EXPECTED_RECOGNIZED_NAMES)


def test_create_token_converts_program_state_into_generic_coverage_without_losing_reasons():
    source = CardFact(
        "Renamed Conditional Source",
        "{1}{G}",
        2,
        "Creature — Test",
        "When Renamed Conditional Source enters, if you attacked, create a Food token.",
        power=2,
        toughness=2,
    )
    result = CardInterpreter().token_semantic_coverage(source, source.oracle_text)

    assert result is not None
    assert isinstance(result.coverage, SemanticCoverage)
    assert result.program.executable
    assert result.coverage.payload_executable
    assert not result.coverage.parent_executable
    assert not result.coverage.followup_executable
    assert not result.coverage.fully_supported
    assert result.coverage.limitations == (
        "token_condition_context_not_implemented",
        "token_activated_ability_not_implemented",
    )
    assert result.limitations == result.coverage.limitations


def test_batch_creation_has_fresh_authoritative_identity_owner_controller_and_events():
    current = game()
    result = program("Create three 2/2 red Mutant creature tokens.")

    tokens = current.create_tokens(
        0,
        result,
        controller=1,
        source_card="Generic Source",
        oracle_fragment="Create three 2/2 red Mutant creature tokens.",
    )

    assert len(tokens) == 3
    assert len({token.object_id for token in tokens}) == 3
    assert all(token.owner == token.controller == 1 for token in tokens)
    assert all(token.is_token and token.summoning_sick for token in tokens)
    assert all(token.card.colors == ("R",) for token in tokens)
    assert all(token in current.players[1].battlefield for token in tokens)
    created_event = next(
        event
        for event in current.events
        if event.get("event") == "rules_event"
        and event.get("rules_event") == RulesEventKind.TOKENS_CREATED.value
    )
    assert created_event["subject_ids"] == [token.object_id for token in tokens]
    entered = [
        event
        for event in current.events
        if event.get("event") == "rules_event"
        and event.get("rules_event") == RulesEventKind.CREATURE_ENTERED.value
    ]
    assert [event["subject_ids"] for event in entered] == [[token.object_id] for token in tokens]
    current.check_invariants()


def test_invalid_creation_is_atomic_and_does_not_consume_runtime_identity():
    current = game()
    before = current.snapshot()
    next_number = current._next_object_number
    invalid = TokenCreationProgram(TokenDefinition("Broken", "Creature — Broken"), 2)

    with pytest.raises(ValueError, match="requires power and toughness"):
        current.create_tokens(
            0,
            invalid,
            source_card="Generic Source",
            oracle_fragment="Create two Broken tokens.",
        )

    assert current.snapshot() == before
    assert current._next_object_number == next_number
    assert not any(event["event"] == "tokens_created" for event in current.events)


def test_token_counters_and_pt_modifiers_use_existing_layer_evaluation():
    current = game()
    token = current.create_tokens(
        0,
        program("Create a 1/1 green Turtle creature token."),
        source_card="Generic Source",
        oracle_fragment="Create a 1/1 green Turtle creature token.",
    )[0]

    current.place_counters(token, "+1/+1", 2, source_card="Test", oracle_fragment="Test")
    current.apply_pt_modifier(
        token,
        3,
        -1,
        duration="until_end_of_turn",
        source_card="Test",
        oracle_fragment="Test",
    )
    assert token.evaluate_power_toughness() == (6, 2)
    current.end_turn()
    assert token.evaluate_power_toughness() == (3, 3)
    assert token in current.players[0].battlefield
    current.check_invariants()


def test_token_ceases_at_sba_boundary_after_leaving_battlefield_and_stale_reference_fails():
    current = game()
    token = current.create_tokens(
        0,
        program("Create a 1/1 colorless Robot artifact creature token."),
        source_card="Generic Source",
        oracle_fragment="Create a 1/1 colorless Robot artifact creature token.",
    )[0]
    graveyard_object = current.put_into_graveyard(token)

    assert isinstance(graveyard_object, CardObject)
    assert graveyard_object.is_token
    assert graveyard_object in current.players[0].graveyard
    with pytest.raises(ValueError, match="must cease"):
        current.move_object(graveyard_object, "hand", reason="fabricated continuation")

    current.check_state_based_actions()
    assert graveyard_object.zone == "former"
    assert graveyard_object not in current.players[0].graveyard
    with pytest.raises(ValueError, match="former object"):
        current.move_object(graveyard_object, "hand", reason="stale reference")


def test_lethal_token_is_moved_then_ceases_with_typed_evidence():
    current = game()
    token = current.create_tokens(
        0,
        program("Create a 1/1 black Ninja creature token."),
        source_card="Generic Source",
        oracle_fragment="Create a 1/1 black Ninja creature token.",
    )[0]
    token.damage = 1

    current.check_state_based_actions()

    assert token.zone == "former"
    assert token not in current.players[0].battlefield
    assert any(event["event"] == "token_ceased" for event in current.events)


def test_fabricated_equal_and_stale_token_objects_cannot_bind_authoritative_state():
    current = game()
    token = current.create_tokens(
        0,
        program("Create a 2/2 red Mutant creature token."),
        source_card="Generic Source",
        oracle_fragment="Create a 2/2 red Mutant creature token.",
    )[0]
    fabricated = copy.copy(token)

    with pytest.raises(ValueError, match="unregistered runtime object"):
        current.move_object(fabricated, "graveyard", reason="fabricated")
    current.put_into_graveyard(token)
    current.check_state_based_actions()
    with pytest.raises(ValueError, match="former object"):
        current.move_object(token, "hand", reason="stale")


def test_creature_token_is_summoning_sick_then_can_attack_on_a_later_controller_turn():
    current = game()
    token = current.create_tokens(
        0,
        program("Create a 2/2 green Turtle creature token."),
        source_card="Generic Source",
        oracle_fragment="Create a 2/2 green Turtle creature token.",
    )[0]
    assert token not in current.legal_attackers(0)

    current.end_turn()
    current.begin_turn()
    current.end_turn()
    current.begin_turn()

    assert current.active_player == 0
    assert not token.summoning_sick
    assert token in current.legal_attackers(0)


def test_same_seed_token_creation_is_byte_equivalent_and_rng_neutral():
    fragment = "Create two 1/1 blue Ninja creature tokens."
    first = game(seed=7001)
    second = game(seed=7001)
    first_rng = tuple(first.rng.records)
    second_rng = tuple(second.rng.records)
    for current in (first, second):
        current.create_tokens(
            0,
            program(fragment),
            source_card="Generic Source",
            oracle_fragment=fragment,
        )

    assert first.snapshot() == second.snapshot()
    assert first.events == second.events
    assert first.rng.records == second.rng.records
    assert tuple(first.rng.records) == first_rng
    assert tuple(second.rng.records) == second_rng


def test_noncreature_food_persists_cleanup_but_cannot_enter_combat():
    current = game()
    food = current.create_tokens(
        0,
        program("Create a Food token."),
        source_card="Generic Source",
        oracle_fragment="Create a Food token.",
    )[0]
    current.end_turn()

    assert food in current.players[0].battlefield
    assert food not in current.legal_attackers(0)
    assert not food.card.is_creature
    current.check_invariants()


def test_generic_etb_delivery_uses_oracle_shape_not_source_card_name():
    current = game()
    source = CardFact(
        "Renamed Fixture",
        "{2}{G}",
        3,
        "Creature — Test",
        "When Renamed Fixture enters, create two 1/1 green Turtle creature tokens.",
        power=2,
        toughness=2,
    )
    permanent = current.create_permanent(source, 0, summoning_sick=True)

    current._process_creature_entered_triggers(permanent)

    tokens = [item for item in current.players[0].battlefield if item.is_token]
    assert len(tokens) == 2
    assert all(item.card.name == "Turtle" for item in tokens)


def test_authoritative_snapshot_and_frozen_roster_recognition_contract():
    catalog = load_card_data(
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json",
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json",
    )
    interpreter = CardInterpreter()
    representatives = {card.oracle_id: card for card in catalog.cards}.values()
    rows_by_name = {
        card.name: tuple(
            (card.oracle_id, fragment, coverage)
            for fragment in interpreter.fragments(card)
            if (coverage := interpreter.token_semantic_coverage(card, fragment)) is not None
        )
        for card in representatives
    }
    rows_by_name = {name: items for name, items in rows_by_name.items() if items}

    assert set(rows_by_name) == EXPECTED_RECOGNIZED_NAMES
    assert {
        name for name, items in rows_by_name.items() if any(x[2].payload_executable for x in items)
    } == EXPECTED_EXECUTABLE_NAMES
    assert sum(map(len, rows_by_name.values())) == 71
    assert sum(x[2].payload_executable for items in rows_by_name.values() for x in items) == 50
    recognized_rows = {
        (oracle_id, fragment) for items in rows_by_name.values() for oracle_id, fragment, _ in items
    }
    executable_rows = {
        (oracle_id, fragment)
        for items in rows_by_name.values()
        for oracle_id, fragment, coverage in items
        if coverage.payload_executable
    }

    def digest(rows):
        return hashlib.sha256(
            "\n".join(sorted(f"{oracle_id}\t{fragment}" for oracle_id, fragment in rows)).encode()
        ).hexdigest()

    assert (
        digest(recognized_rows)
        == "c7cc01b61f3498a8cdb2576532d572815e852c7c47efc6af3a45579aabbc92f8"
    )
    assert (
        digest(executable_rows)
        == "3fdec6260d5627e3e2c0e57b9a8e56b71ea35e59c51efcbb574de10f67254d55"
    )

    roster = json.loads((ROOT / "cardcade/roster-0.2.json").read_text(encoding="utf-8"))
    exposed_names: set[str] = set()
    exposed_decks: set[str] = set()
    for deck in roster["decks"]:
        path = ROOT / deck["decklist"]
        names = {
            line.split(" ", 1)[1]
            for line in path.read_text(encoding="utf-8").splitlines()
            if line and line != "Deck"
        }
        matches = names & rows_by_name.keys()
        exposed_names.update(matches)
        if matches:
            exposed_decks.add(deck["id"])

    assert exposed_names == EXPECTED_ROSTER_NAMES
    assert len(exposed_decks) == 10
    assert exposed_names & EXPECTED_EXECUTABLE_NAMES == EXPECTED_ROSTER_NAMES - {
        "Donatello, Gadget Master",
        "Improvised Arsenal",
        "Mutagen Man, Living Ooze",
        "The Last Ronin's Technique",
    }


def test_every_bounded_full_pool_program_executes_the_same_authoritative_action():
    catalog = load_card_data(
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json",
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json",
    )
    interpreter = CardInterpreter()
    representatives = {card.oracle_id: card for card in catalog.cards}.values()
    executable = [
        (card.name, fragment, candidate)
        for card in representatives
        for fragment in interpreter.fragments(card)
        if (candidate := interpreter.token_creation_program(fragment)) is not None
        and candidate.executable
    ]
    current = game(seed=332)

    created = [
        current.create_tokens(
            0,
            candidate,
            source_card=card_name,
            oracle_fragment=fragment,
        )
        for card_name, fragment, candidate in executable
    ]

    assert len(executable) == len(created) == 50
    assert all(batch for batch in created)
    assert len({token.object_id for batch in created for token in batch}) == sum(
        len(batch) for batch in created
    )
    assert sum(event["event"] == "tokens_created" for event in current.events) == 50
    current.check_invariants()


def test_every_nonfully_supported_full_pool_fragment_retains_explicit_limitations():
    interpreter = CardInterpreter()
    representatives = {card.oracle_id: card for card in authoritative_catalog().cards}.values()
    rows = [
        (card, fragment, coverage)
        for card in representatives
        for fragment in interpreter.fragments(card)
        if (coverage := interpreter.token_semantic_coverage(card, fragment)) is not None
    ]
    fully_supported = {
        (card.name, fragment) for card, fragment, coverage in rows if coverage.fully_supported
    }

    assert {name for name, _ in fully_supported} == {
        "Baxter Stockman",
        "Biogenic Ooze",
        "Jennika, Bad Apple Big Sister",
        "Mechanized Ninja Cavalry",
        "Mighty Mutanimals",
        "Slash, Reptile Rampager",
    }
    assert len(fully_supported) == 6
    for card, fragment, coverage in rows:
        reported_reasons = {
            reason
            for reported_fragment, reason in interpreter.unsupported_fragments(card)
            if reported_fragment == fragment
        }
        if coverage.fully_supported:
            assert not reported_reasons
        else:
            assert set(coverage.limitations)
            assert set(coverage.limitations) <= reported_reasons
