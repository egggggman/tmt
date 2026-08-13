import hashlib
import json
from pathlib import Path

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.engine07 import load_deck, load_facts

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
MANIFEST = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json"
HISTORICAL_MODEL = ROOT / "cardcade/card-model-0.6.json"

HISTORICAL_ACCEPTANCE_PT = {
    "April O'Neil, Kunoichi Trainee": (2, 2),
    "Casey Jones, Jury-Rig Justiciar": (2, 1),
    "Leonardo, Big Brother": (1, 3),
    "Leonardo, Cutting Edge": (1, 1),
    "Leonardo, Leader in Blue": (2, 1),
    "Leonardo, Sewer Samurai": (3, 3),
    "Lita, Little Orphan Amphibian": (2, 1),
    "Mighty Mutanimals": (2, 1),
    "Mutant Town Musicians": (2, 4),
    "Null Group Biological Assets": (3, 1),
    "Prehistoric Pet": (1, 2),
    "Raphael, Most Attitude": (4, 3),
    "Raphael, Ninja Destroyer": (4, 4),
    "Raphael, Tough Turtle": (1, 3),
    "Raphael, the Nightwatcher": (2, 3),
    "Wingnut, Bat on the Belfry": (1, 2),
}


def deck_names(path):
    return {
        line.split(" ", 1)[1]
        for line in path.read_text(encoding="utf-8").splitlines()
        if line and line != "Deck"
    }


def test_authoritative_snapshot_matches_manifest_and_required_counts():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    raw = SNAPSHOT.read_bytes()
    catalog = load_card_data(SNAPSHOT, MANIFEST)

    assert hashlib.sha256(raw).hexdigest() == manifest["snapshot"]["sha256"]
    assert len(catalog.cards) == manifest["snapshot"]["print_count"] == 472
    assert len({card.oracle_id for card in catalog.cards}) == 332
    assert [(row["code"], row["print_count"]) for row in manifest["snapshot"]["sets"]] == [
        ("tmt", 320),
        ("pza", 20),
        ("tmc", 132),
    ]


def test_normalized_interface_exposes_faces_characteristics_identity_and_legality():
    catalog = load_card_data(SNAPSHOT, MANIFEST)
    assert all(
        card.scryfall_id
        and card.oracle_id
        and card.name
        and card.type_line
        and card.mana_value is not None
        and card.set_code
        and card.collector_number
        and card.legalities
        for card in catalog.cards
    )
    multiface = [card for card in catalog.cards if card.card_faces]
    assert len(multiface) == 1
    assert len(multiface[0].card_faces) == 2
    assert all(face.name and face.type_line for face in multiface[0].card_faces)
    creatures = [card for card in catalog.cards if "Creature" in card.type_line]
    assert len(creatures) == 265
    assert all(card.power is not None and card.toughness is not None for card in creatures)


def test_historical_engine06_facts_are_equivalent_to_authoritative_source():
    historical = json.loads(HISTORICAL_MODEL.read_text(encoding="utf-8"))["cards"]
    catalog = load_card_data(SNAPSHOT, MANIFEST)

    for name, previous in historical.items():
        current = catalog.resolve_name(name)
        assert current.oracle_id == previous["oracle_id"]
        assert current.mana_cost == previous["mana_cost"]
        assert current.mana_value == previous["mana_value"]
        assert current.type_line == previous["type_line"]
        assert current.oracle_text == previous["oracle_text"]
        assert current.keywords == tuple(previous["keywords"])


def test_acceptance_facts_match_removed_hard_coded_pt_and_historical_model():
    catalog = load_card_data(SNAPSHOT, MANIFEST)
    historical = json.loads(HISTORICAL_MODEL.read_text(encoding="utf-8"))["cards"]
    facts = load_facts(catalog, set(historical))

    for name, expected_pt in HISTORICAL_ACCEPTANCE_PT.items():
        fact = facts[name]
        previous = historical[name]
        assert (fact.power, fact.toughness) == expected_pt
        assert (
            fact.name,
            fact.mana_cost,
            fact.mana_value,
            fact.type_line,
            fact.oracle_text,
            fact.keywords,
        ) == (
            name,
            previous["mana_cost"],
            previous["mana_value"],
            previous["type_line"],
            previous["oracle_text"],
            tuple(previous["keywords"]),
        )


def test_all_ten_frozen_decks_resolve_all_600_slots_through_catalog():
    roster = json.loads((ROOT / "cardcade/roster-0.2.json").read_text(encoding="utf-8"))
    catalog = load_card_data(SNAPSHOT, MANIFEST)
    total = 0
    for deck in roster["decks"]:
        path = ROOT / deck["decklist"]
        facts = load_facts(catalog, deck_names(path))
        resolved = load_deck(path, facts)
        assert len(resolved) == 60
        total += len(resolved)
    assert total == 600
