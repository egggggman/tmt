"""Authoritative, normalized Cardcade card facts backed by a verified Scryfall snapshot."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CardFace:
    name: str
    mana_cost: str
    type_line: str
    oracle_text: str
    power: str | None
    toughness: str | None


@dataclass(frozen=True)
class CardData:
    scryfall_id: str
    oracle_id: str
    name: str
    card_faces: tuple[CardFace, ...]
    oracle_text: str
    keywords: tuple[str, ...]
    type_line: str
    mana_cost: str
    mana_value: int | float
    power: str | None
    toughness: str | None
    set_code: str
    collector_number: str
    legalities: dict[str, str]


class CardDataError(ValueError):
    """The authoritative card-data source is missing, invalid, or ambiguous."""


class CardDataCatalog:
    def __init__(self, cards: tuple[CardData, ...], *, snapshot_sha256: str):
        self.cards = cards
        self.snapshot_sha256 = snapshot_sha256
        by_name: dict[str, list[CardData]] = {}
        for card in cards:
            by_name.setdefault(card.name, []).append(card)
        self._by_name = {
            name: tuple(sorted(printings, key=lambda card: (card.set_code, card.collector_number)))
            for name, printings in by_name.items()
        }

    def resolve_name(self, name: str) -> CardData:
        printings = self._by_name.get(name, ())
        if not printings:
            raise CardDataError(f"card name not found in authoritative snapshot: {name}")
        oracle_ids = {card.oracle_id for card in printings}
        if len(oracle_ids) != 1:
            raise CardDataError(f"card name has ambiguous Oracle identities: {name}")
        return printings[0]


def _required(record: dict[str, Any], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value:
        raise CardDataError(
            f"snapshot record has invalid {field}: {record.get('name', '<unknown>')}"
        )
    return value


def _face(record: dict[str, Any]) -> CardFace:
    return CardFace(
        name=_required(record, "name"),
        mana_cost=record.get("mana_cost") or "",
        type_line=_required(record, "type_line"),
        oracle_text=record.get("oracle_text") or "",
        power=record.get("power"),
        toughness=record.get("toughness"),
    )


def load_card_data(snapshot_path: Path, manifest_path: Path) -> CardDataCatalog:
    raw = snapshot_path.read_bytes()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = manifest["snapshot"]["sha256"]
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected:
        raise CardDataError(f"snapshot checksum mismatch: expected {expected}, found {actual}")
    records = json.loads(raw)
    if len(records) != manifest["snapshot"]["print_count"]:
        raise CardDataError("snapshot print count does not match manifest")
    cards = []
    for record in records:
        oracle_id = _required(record, "oracle_id")
        legalities = record.get("legalities")
        if not isinstance(legalities, dict) or not legalities:
            raise CardDataError(f"snapshot record lacks legalities: {record.get('name')}")
        cards.append(
            CardData(
                scryfall_id=_required(record, "id"),
                oracle_id=oracle_id,
                name=_required(record, "name"),
                card_faces=tuple(_face(face) for face in record.get("card_faces", [])),
                oracle_text=record.get("oracle_text") or "",
                keywords=tuple(sorted(record.get("keywords", []))),
                type_line=_required(record, "type_line"),
                mana_cost=record.get("mana_cost") or "",
                mana_value=record["mana_value"],
                power=record.get("power"),
                toughness=record.get("toughness"),
                set_code=_required(record, "set"),
                collector_number=_required(record, "collector_number"),
                legalities=dict(sorted(legalities.items())),
            )
        )
    return CardDataCatalog(tuple(cards), snapshot_sha256=actual)
