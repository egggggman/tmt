"""Audit Cardcade's frozen decks and card model against current Scryfall set data."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import urllib.parse
import urllib.request
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SET_CODES = ("tmt", "pza", "tmc")
USER_AGENT = "TMNTDesignStudio/0.5.0 (+https://github.com/egggggman/tmt)"
HEADERS = {"User-Agent": USER_AGENT, "Accept": "application/json"}


def request_json(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(  # noqa: S310
        urllib.request.Request(url, headers=HEADERS), timeout=120
    ) as response:
        return json.loads(response.read())


def set_cards(code: str) -> tuple[dict[str, Any], list[dict[str, Any]], list[str]]:
    metadata_url = f"https://api.scryfall.com/sets/{code}"
    search_url = "https://api.scryfall.com/cards/search?" + urllib.parse.urlencode(
        {"q": f"e:{code}", "unique": "prints", "order": "set"}
    )
    metadata = request_json(metadata_url)
    cards: list[dict[str, Any]] = []
    page_urls: list[str] = []
    url: str | None = search_url
    while url:
        page_urls.append(url)
        page = request_json(url)
        cards.extend(page["data"])
        url = page.get("next_page") if page.get("has_more") else None
    return metadata, cards, [metadata_url, *page_urls]


def normalized_face(face: dict[str, Any]) -> dict[str, Any]:
    return {
        key: face.get(key)
        for key in ("name", "mana_cost", "type_line", "oracle_text", "power", "toughness")
    }


def normalized_card(card: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": card["id"],
        "oracle_id": card.get("oracle_id"),
        "set": card["set"],
        "collector_number": card["collector_number"],
        "name": card["name"],
        "layout": card["layout"],
        "mana_cost": card.get("mana_cost"),
        "mana_value": card.get("cmc"),
        "type_line": card.get("type_line"),
        "oracle_text": card.get("oracle_text"),
        "keywords": card.get("keywords"),
        "power": card.get("power"),
        "toughness": card.get("toughness"),
        "legalities": card.get("legalities"),
        "card_faces": [normalized_face(face) for face in card.get("card_faces", [])],
    }


def deck_entries(path: Path) -> list[tuple[int, str]]:
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line and line != "Deck":
            quantity, name = line.split(" ", 1)
            entries.append((int(quantity), name))
    return entries


def has_field(card: dict[str, Any], field: str) -> bool:
    if card.get(field) not in (None, "", []):
        return True
    return bool(card.get("card_faces")) and all(
        face.get(field) not in (None, "", []) for face in card["card_faces"]
    )


def git_value(root: Path, *arguments: str) -> str:
    return subprocess.check_output(  # noqa: S603
        ["git", *arguments], cwd=root, text=True, encoding="utf-8"
    ).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    retrieved_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")

    all_cards: list[dict[str, Any]] = []
    sets = []
    source_urls = []
    for code in SET_CODES:
        metadata, cards, urls = set_cards(code)
        all_cards.extend(normalized_card(card) for card in cards)
        source_urls.extend(urls)
        sets.append(
            {
                "code": code,
                "id": metadata["id"],
                "name": metadata["name"],
                "released_at": metadata["released_at"],
                "advertised_card_count": metadata["card_count"],
                "retrieved_print_count": len(cards),
                "unique_oracle_object_count": len(
                    {card.get("oracle_id") for card in cards if card.get("oracle_id")}
                ),
            }
        )
    all_cards.sort(key=lambda card: (card["set"], card["collector_number"], card["id"]))
    canonical = json.dumps(all_cards, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    snapshot_faces = [face for card in all_cards for face in card["card_faces"]]
    snapshot_creatures = [card for card in all_cards if "Creature" in (card["type_line"] or "")]

    roster = json.loads((root / "cardcade/roster-0.2.json").read_text(encoding="utf-8"))
    model_path = root / "cardcade/card-model-0.6.json"
    model_bytes = model_path.read_bytes()
    model = json.loads(model_bytes)["cards"]
    by_name: dict[str, list[dict[str, Any]]] = {}
    for card in all_cards:
        by_name.setdefault(card["name"], []).append(card)

    decks = []
    total_slots = 0
    unique_deck_names: set[str] = set()
    discrepancies = []
    availability = Counter()
    creature_slots = 0
    creature_pt_complete_slots = 0
    multiface_slots = 0
    multiface_complete_slots = 0
    legality_values: dict[str, Counter[str]] = {}
    matched_set_slots: Counter[str] = Counter()
    current_oracles: dict[str, str] = {}
    for deck in roster["decks"]:
        entries = deck_entries(root / deck["decklist"])
        slot_count = sum(quantity for quantity, _ in entries)
        total_slots += slot_count
        unresolved = []
        for quantity, name in entries:
            unique_deck_names.add(name)
            matches = by_name.get(name, [])
            if not matches:
                unresolved.append(name)
                continue
            current = matches[0]
            matched_set_slots[current["set"]] += quantity
            current_oracles[name] = current.get("oracle_text") or "\n".join(
                face.get("oracle_text") or "" for face in current["card_faces"]
            )
            for field in ("oracle_text", "keywords", "type_line", "mana_cost", "legalities"):
                if field in current and (field != "oracle_text" or has_field(current, field)):
                    availability[field] += quantity
            if "Creature" in (current.get("type_line") or ""):
                creature_slots += quantity
                if has_field(current, "power") and has_field(current, "toughness"):
                    creature_pt_complete_slots += quantity
            if current["card_faces"]:
                multiface_slots += quantity
                if all(
                    face.get("name")
                    and face.get("type_line")
                    and face.get("mana_cost") is not None
                    and face.get("oracle_text") is not None
                    for face in current["card_faces"]
                ):
                    multiface_complete_slots += quantity
            for format_name, legality in current["legalities"].items():
                legality_values.setdefault(format_name, Counter())[legality] += quantity
        decks.append(
            {
                "id": deck["id"],
                "decklist": deck["decklist"],
                "slots": slot_count,
                "unique_names": len(entries),
                "unresolved_names": sorted(unresolved),
            }
        )

    for name in sorted(unique_deck_names):
        if name not in model:
            discrepancies.append({"card": name, "field": "model_record", "status": "missing"})
            continue
        current = by_name.get(name, [None])[0]
        if current is None:
            continue
        for field in ("oracle_id", "mana_cost", "type_line", "oracle_text", "keywords"):
            current_value = current.get(field)
            if field == "oracle_text" and not current_value:
                current_value = "\n".join(
                    face.get("oracle_text") or "" for face in current["card_faces"]
                )
            committed_value = model[name].get(field)
            if field == "keywords":
                committed_value = sorted(committed_value)
                current_value = sorted(current_value)
            if committed_value != current_value:
                discrepancies.append(
                    {
                        "card": name,
                        "field": field,
                        "committed": committed_value,
                        "current_scryfall": current_value,
                    }
                )

    fixture_path = root / "tests/fixtures/scryfall-default-cards.json"
    fixture_bytes = fixture_path.read_bytes()
    fixture_records = json.loads(fixture_bytes)
    model_commit = git_value(root, "log", "-1", "--format=%H", "--", str(model_path))
    model_commit_date = git_value(root, "log", "-1", "--format=%aI", "--", str(model_path))
    manifest = {
        "schema_version": "1.0.0",
        "retrieved_at": retrieved_at,
        "source": {
            "provider": "Scryfall",
            "api": "https://api.scryfall.com",
            "set_codes": list(SET_CODES),
            "request_user_agent": USER_AGENT,
            "identifiers": source_urls,
        },
        "snapshot": {
            "canonicalization": (
                "UTF-8 JSON, sorted keys, compact separators; records sorted by "
                "set/collector_number/id"
            ),
            "sha256": hashlib.sha256(canonical.encode()).hexdigest(),
            "print_count": len(all_cards),
            "unique_oracle_object_count": len(
                {card["oracle_id"] for card in all_cards if card["oracle_id"]}
            ),
            "field_coverage": {
                "records_with_oracle_text_or_complete_face_text": sum(
                    has_field(card, "oracle_text") for card in all_cards
                ),
                "records_with_keywords_array": sum(
                    isinstance(card["keywords"], list) for card in all_cards
                ),
                "records_with_type_line": sum(has_field(card, "type_line") for card in all_cards),
                "records_with_mana_cost_field": sum(
                    card["mana_cost"] is not None for card in all_cards
                ),
                "creature_records": len(snapshot_creatures),
                "creature_records_with_power_toughness": sum(
                    has_field(card, "power") and has_field(card, "toughness")
                    for card in snapshot_creatures
                ),
                "records_with_legalities": sum(
                    isinstance(card["legalities"], dict) and bool(card["legalities"])
                    for card in all_cards
                ),
                "multiface_print_records": sum(bool(card["card_faces"]) for card in all_cards),
                "card_face_count": len(snapshot_faces),
                "faces_with_name_type_mana_oracle": sum(
                    face.get("name")
                    and face.get("type_line")
                    and face.get("mana_cost") is not None
                    and face.get("oracle_text") is not None
                    for face in snapshot_faces
                ),
            },
            "sets": sets,
        },
        "committed_cardcade_source": {
            "path": "cardcade/card-model-0.6.json",
            "sha256": hashlib.sha256(model_bytes).hexdigest(),
            "record_count": len(model),
            "declared_source": json.loads(model_bytes)["source"],
            "contains_retrieval_timestamp": False,
            "contains_import_id_or_source_checksum": False,
            "fields": sorted(next(iter(model.values()))),
            "introducing_commit": model_commit,
            "introducing_commit_author_date": model_commit_date,
            "omitted_fields": ["card_faces", "legalities", "power", "toughness"],
        },
        "other_committed_scryfall_data": {
            "path": "tests/fixtures/scryfall-default-cards.json",
            "purpose": "synthetic test fixture, not a TMT/PZA/TMC snapshot",
            "sha256": hashlib.sha256(fixture_bytes).hexdigest(),
            "printing_count": len(fixture_records),
            "unique_oracle_object_count": len({record["oracle_id"] for record in fixture_records}),
        },
        "deck_validation": {
            "roster": "cardcade/roster-0.2.json",
            "deck_count": len(decks),
            "total_slots": total_slots,
            "unique_card_names": len(unique_deck_names),
            "resolved_slots": total_slots
            - sum(
                quantity
                for deck in roster["decks"]
                for quantity, name in deck_entries(root / deck["decklist"])
                if name not in by_name
            ),
            "decks": decks,
            "current_scryfall_field_presence_by_slot": dict(sorted(availability.items())),
            "creature_slots": creature_slots,
            "creature_slots_with_complete_power_toughness": creature_pt_complete_slots,
            "multiface_slots": multiface_slots,
            "multiface_slots_with_complete_face_facts": multiface_complete_slots,
            "representative_print_set_by_slot": dict(sorted(matched_set_slots.items())),
            "legality_values_by_format_and_slot": {
                format_name: dict(sorted(counts.items()))
                for format_name, counts in sorted(legality_values.items())
            },
            "committed_model_discrepancies": discrepancies,
        },
    }
    args.output.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
