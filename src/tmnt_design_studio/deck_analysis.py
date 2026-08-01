"""Deterministic metrics and explainable analysis for immutable Deck Versions."""

# ruff: noqa: E501

from __future__ import annotations

import json
import re
import sqlite3
import statistics
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

from tmnt_design_studio.capabilities import effective_capabilities
from tmnt_design_studio.database import connect, initialize_database

ENGINE_VERSION = "2026.08.0"
COLORS = ("W", "U", "B", "R", "G")
COUNTED_TYPES = (
    "Creature",
    "Artifact",
    "Enchantment",
    "Instant",
    "Sorcery",
    "Planeswalker",
    "Battle",
)
CAPABILITY_IDS = (
    "targeted-removal",
    "board-wipe",
    "protection",
    "counterspell",
    "card-draw",
    "card-selection",
    "ramp",
    "mana-fixing",
    "token-creation",
    "recursion",
    "graveyard-interaction",
    "combat-support",
    "evasion",
    "life-gain",
    "sacrifice-support",
    "artifact-synergy",
    "equipment-synergy",
    "cost-reduction",
    "tempo",
    "finisher",
)
INTERACTION_CAPABILITIES = {
    "targeted-removal",
    "board-wipe",
    "protection",
    "counterspell",
    "graveyard-interaction",
    "tempo",
}
ANALYSIS_SPEC = {
    "engine_version": ENGINE_VERSION,
    "counted_types": COUNTED_TYPES,
    "capabilities": CAPABILITY_IDS,
    "interaction_capabilities": sorted(INTERACTION_CAPABILITIES),
    "findings": {
        "curve_mode": "report every modal nonland mana value",
        "color_shortfall": "colored pip count > unrestricted land sources",
        "missing_board_wipe": "board-wipe copy_count == 0",
        "targeted_removal": "report copy_count",
        "finishers": "report copy_count",
        "creature_ratio": "creature copies / total main-deck copies",
    },
    "relationships": (
        ("artifact-enabler", "Artifact", "artifact-synergy"),
        ("equipment-enabler", "Equipment", "equipment-synergy"),
        ("token-sacrifice", "token-creation", "sacrifice-support"),
        ("graveyard-recursion", "graveyard-interaction", "recursion"),
    ),
}


class DeckAnalysisError(RuntimeError):
    """An actionable Deck Version validation or analysis failure."""


@dataclass(frozen=True)
class Metric:
    value: object
    formula: str
    evidence: object


def engine_checksum() -> str:
    payload = json.dumps(
        {**ANALYSIS_SPEC, "engine_version": ENGINE_VERSION},
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(payload.encode()).hexdigest()


def _deck_checksum(version: sqlite3.Row, cards: list[sqlite3.Row]) -> str:
    payload = {
        "deck_version": {
            "id": version["id"],
            "deck_id": version["deck_id"],
            "version_label": version["version_label"],
            "status": version["status"],
            "created_at": version["created_at"],
        },
        "cards": [
            {"oracle_id": row["oracle_id"], "section": row["section"], "quantity": row["quantity"]}
            for row in cards
        ],
    }
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _provenance(connection: sqlite3.Connection) -> tuple[sqlite3.Row, sqlite3.Row]:
    imported = connection.execute(
        "SELECT * FROM imports WHERE source='scryfall' AND status='succeeded' "
        "ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if imported is None:
        raise DeckAnalysisError("A successful Scryfall import is required")
    capability = connection.execute(
        "SELECT r.*,s.rules_checksum FROM capability_derivation_runs r "
        "JOIN capability_rule_sets s ON s.version=r.ruleset_version "
        "WHERE r.status='succeeded' ORDER BY r.id DESC LIMIT 1"
    ).fetchone()
    if capability is None:
        raise DeckAnalysisError("A successful Capability Engine run is required")
    if capability["import_id"] != imported["id"]:
        raise DeckAnalysisError(
            f"Capability data is stale: run #{capability['id']} uses Scryfall import "
            f"#{capability['import_id']}, latest is #{imported['id']}"
        )
    stale = connection.execute(
        "SELECT COUNT(*) FROM card_capabilities WHERE derivation_run_id IS NOT ?",
        (capability["id"],),
    ).fetchone()[0]
    if stale:
        raise DeckAnalysisError(f"Capability data is stale: {stale} result(s) use another run")
    if capability["card_count"] != connection.execute("SELECT COUNT(*) FROM cards").fetchone()[0]:
        raise DeckAnalysisError("Capability run does not cover the current Oracle-card facts")
    return imported, capability


def _load_deck(
    connection: sqlite3.Connection, deck_version_id: int, diagnostic: bool
) -> tuple[sqlite3.Row, list[sqlite3.Row], list[str]]:
    version = connection.execute(
        "SELECT dv.*,d.name deck_name,d.format FROM deck_versions dv "
        "JOIN decks d ON d.id=dv.deck_id WHERE dv.id=?",
        (deck_version_id,),
    ).fetchone()
    if version is None:
        raise DeckAnalysisError(f"Deck Version not found: {deck_version_id}")
    cards = connection.execute(
        "SELECT dc.*,c.name,c.mana_cost,c.mana_value,c.oracle_text,c.type_line,c.color_identity,"
        "l.legality FROM deck_cards dc LEFT JOIN cards c ON c.oracle_id=dc.oracle_id "
        "LEFT JOIN legalities l ON l.oracle_id=dc.oracle_id AND l.format='standard' "
        "WHERE dc.deck_version_id=? ORDER BY dc.section,dc.oracle_id",
        (deck_version_id,),
    ).fetchall()
    missing = [row["oracle_id"] for row in cards if row["name"] is None]
    if missing:
        raise DeckAnalysisError(f"Missing Oracle card facts: {', '.join(missing)}")
    unresolved = [
        row["oracle_id"]
        for row in cards
        if connection.execute(
            "SELECT 1 FROM card_printings WHERE oracle_id=? LIMIT 1", (row["oracle_id"],)
        ).fetchone()
        is None
    ]
    if unresolved:
        raise DeckAnalysisError(f"Unresolved printings: {', '.join(unresolved)}")
    illegal = [row["name"] for row in cards if row["legality"] != "legal"]
    if illegal:
        raise DeckAnalysisError(f"Non-Standard cards: {', '.join(illegal)}")
    main_count = sum(row["quantity"] for row in cards if row["section"] == "main")
    warnings: list[str] = []
    if main_count != 60:
        message = f"Main deck has {main_count} cards; Version 1 requires exactly 60"
        if not diagnostic:
            raise DeckAnalysisError(message + " (use --diagnostic to inspect incomplete decks)")
        warnings.append(message)
    for row in cards:
        is_basic = connection.execute(
            "SELECT 1 FROM card_subtypes cs JOIN subtypes s ON s.id=cs.subtype_id "
            "WHERE cs.oracle_id=? AND s.name IN ('Plains','Island','Swamp','Mountain','Forest')",
            (row["oracle_id"],),
        ).fetchone()
        unlimited = "any number of cards named" in (row["oracle_text"] or "").lower()
        if row["quantity"] > 4 and not is_basic and not unlimited:
            raise DeckAnalysisError(
                f"Illegal quantity: {row['quantity']} copies of {row['name']} (maximum 4)"
            )
    return version, cards, warnings


def _types(connection: sqlite3.Connection, oracle_id: str) -> set[str]:
    return {
        row[0]
        for row in connection.execute(
            "SELECT t.name FROM types t JOIN card_types ct ON ct.type_id=t.id WHERE ct.oracle_id=?",
            (oracle_id,),
        )
    }


def _subtypes(connection: sqlite3.Connection, oracle_id: str) -> set[str]:
    return {
        row[0]
        for row in connection.execute(
            "SELECT s.name FROM subtypes s JOIN card_subtypes cs ON cs.subtype_id=s.id "
            "WHERE cs.oracle_id=?",
            (oracle_id,),
        )
    }


def _pip_counts(mana_cost: str | None, quantity: int) -> dict[str, int]:
    counts = dict.fromkeys(COLORS, 0)
    for symbol in re.findall(r"\{([^}]+)\}", mana_cost or ""):
        for color in COLORS:
            if color in symbol.upper():
                counts[color] += quantity
    return counts


def _source_colors(row: sqlite3.Row, subtypes: set[str]) -> tuple[set[str], str]:
    colors = {
        color
        for color, subtype in zip(
            COLORS, ("Plains", "Island", "Swamp", "Mountain", "Forest"), strict=True
        )
        if subtype in subtypes
    }
    text = row["oracle_text"] or ""
    for clause in re.findall(r"[Aa]dd[^.\n]*", text):
        colors.update(re.findall(r"\{([WUBRG])\}", clause))
    if re.search(r"add one mana of any color", text, re.I):
        colors.update(COLORS)
    lower = text.lower()
    if "spend this mana only" in lower or "activate only" in lower or "only to cast" in lower:
        kind = "restricted"
    elif re.search(r"\b(if|unless|as long as)\b", lower):
        kind = "conditional"
    else:
        kind = "unrestricted"
    return colors, kind


def compute_metrics(
    connection: sqlite3.Connection, cards: list[sqlite3.Row]
) -> tuple[dict[str, Metric], dict[str, set[str]]]:
    main = [row for row in cards if row["section"] == "main"]
    total = sum(row["quantity"] for row in main)
    type_counts = {name.lower(): 0 for name in COUNTED_TYPES}
    type_counts["other"] = 0
    land_count = 0
    nonland_values: list[float] = []
    histogram: dict[str, int] = {}
    pips = dict.fromkeys(COLORS, 0)
    land_sources = {
        color: {"unrestricted": 0, "conditional": 0, "restricted": 0, "total": 0}
        for color in COLORS
    }
    capability_totals = {
        identifier: {"copy_count": 0, "unique_cards": 0, "confidence_weighted": 0.0}
        for identifier in CAPABILITY_IDS
    }
    card_caps: dict[str, set[str]] = {}
    interaction_copies = 0
    threat_copies = 0
    finisher_copies = 0
    evidence_cards: list[dict[str, object]] = []
    nonland_fixing = 0
    nonland_ramp = 0

    for row in main:
        quantity = row["quantity"]
        types = _types(connection, row["oracle_id"])
        subtypes = _subtypes(connection, row["oracle_id"])
        caps = effective_capabilities(connection, row["oracle_id"])
        identifiers = {str(item["identifier"]) for item in caps}
        card_caps[row["oracle_id"]] = identifiers
        for name in COUNTED_TYPES:
            if name in types:
                type_counts[name.lower()] += quantity
        if not types.intersection(COUNTED_TYPES) and "Land" not in types:
            type_counts["other"] += quantity
        is_land = "Land" in types
        if is_land:
            land_count += quantity
            colors, source_kind = _source_colors(row, subtypes)
            for color in colors:
                land_sources[color][source_kind] += quantity
                land_sources[color]["total"] += quantity
        else:
            value = float(row["mana_value"])
            nonland_values.extend([value] * quantity)
            label = str(int(value)) if value.is_integer() else str(value)
            histogram[label] = histogram.get(label, 0) + quantity
            for color, count in _pip_counts(row["mana_cost"], quantity).items():
                pips[color] += count
            if "mana-fixing" in identifiers:
                nonland_fixing += quantity
            if "ramp" in identifiers:
                nonland_ramp += quantity
        for capability in caps:
            identifier = str(capability["identifier"])
            if identifier not in capability_totals:
                continue
            capability_totals[identifier]["copy_count"] += quantity
            capability_totals[identifier]["unique_cards"] += 1
            capability_totals[identifier]["confidence_weighted"] += quantity * float(
                capability["confidence"]
            )
        if identifiers & INTERACTION_CAPABILITIES:
            interaction_copies += quantity
        if (
            "Creature" in types
            or "Planeswalker" in types
            or "Battle" in types
            or "finisher" in identifiers
        ):
            threat_copies += quantity
        if "finisher" in identifiers:
            finisher_copies += quantity
        evidence_cards.append(
            {"oracle_id": row["oracle_id"], "name": row["name"], "quantity": quantity}
        )

    nonland_count = total - land_count
    average = sum(nonland_values) / len(nonland_values) if nonland_values else None
    median = statistics.median(nonland_values) if nonland_values else None
    duplicate_groups = [
        {"oracle_id": row["oracle_id"], "name": row["name"], "quantity": row["quantity"]}
        for row in main
        if row["quantity"] > 1
    ]
    redundancy = {
        capability: sorted(row["name"] for row in main if capability in card_caps[row["oracle_id"]])
        for capability in CAPABILITY_IDS
        if sum(capability in card_caps[row["oracle_id"]] for row in main) > 1
    }
    availability = {
        color: {
            "unrestricted_land_sources": land_sources[color]["unrestricted"],
            "all_land_sources": land_sources[color]["total"],
            "conditional_land_sources": land_sources[color]["conditional"],
            "restricted_land_sources": land_sources[color]["restricted"],
            "nonland_fixing_copies": nonland_fixing,
            "nonland_ramp_copies": nonland_ramp,
        }
        for color in COLORS
    }
    metrics = {
        "total_card_count": Metric(total, "sum(main-deck quantity)", evidence_cards),
        "unique_oracle_card_count": Metric(
            len(main), "count(distinct main-deck Oracle IDs)", evidence_cards
        ),
        "land_count": Metric(land_count, "sum(quantity where normalized type includes Land)", []),
        "nonland_count": Metric(nonland_count, "total_card_count - land_count", []),
        "type_counts": Metric(
            type_counts, "sum quantity for each normalized Oracle type; non-exclusive", []
        ),
        "mana_value_histogram": Metric(
            dict(sorted(histogram.items(), key=lambda x: float(x[0]))),
            "nonland copies grouped by imported mana value",
            [],
        ),
        "average_nonland_mana_value": Metric(
            average, "sum(nonland mana values by copy) / nonland_count", []
        ),
        "median_nonland_mana_value": Metric(median, "median(nonland mana values by copy)", []),
        "color_requirements_by_pip": Metric(
            pips,
            "colored symbols across main-deck nonland mana costs by copy; hybrid counts for each represented color",
            [],
        ),
        "land_color_production": Metric(
            land_sources,
            "land copies with basic subtype or explicit add-mana text, separated by restrictions",
            [],
        ),
        "mana_source_availability": Metric(
            availability,
            "land sources by color plus separately reported nonland fixing and ramp copies",
            [],
        ),
        "capability_totals": Metric(
            capability_totals,
            "per Capabiliу{h‘йм¶»§q«^u[ћH[ќ\XЭ[Ы€Ш\Xљ[]HИ›Ы›[™ШЫЭ[ќ‹€ЧK€
K€ќ™X]Щ[њЪ]HЋ€Y]љXК€™X]ШЫЬY\ИИ›Ы›[™ШЫЭ[ќY€›Ы›[™ШЫЭ[ќ[ЩHЊ€››Ы›[™Ь™X]\™K[™\ЭШ[Щ\‹]KЬ€љ[љ\Ъ\€ЫЬY\ИИ›Ы›[™ШЫЭ[ќ‹€ЧK€
K€™љ[љ\Ъ\—Щ[њЪ]HЋ€Y]љXК€љ[љ\Ъ\—ШЫЬY\ИИ›Ы›[™ШЫЭ[ќY€›Ы›[™ШЫЭ[ќ[ЩHЊ€ЫЬY\ИЪ]љ[љ\Ъ\€Ш\Xљ[]HИ›Ы›[™ШЫЭ[ќ‹€ЧK€
K€›[™Ь][ИЋ€Y]љXК€[™ШЫЭ[ќИЭ[Y€Э[[ЩHЊ›[™ШЫЭ[ќИЭ[ШШ\™ШЫЭ[ќ‹ЧB€
K€Ь™X]\™WЬ][ИЋ€Y]љXК€\WШЫЭ[ќЦИЬ™X]\™H—HИЭ[Y€Э[[ЩHЊ€Ь™X]\™HЫЬHЫЭ[ќИЭ[ШШ\™ШЫЭ[ќ‹€ЧK€
K€™\XШ]WЩЬ›Э\ИЋ€Y]љXК€\XШ]WЩЬ›Э\Л›XZ[‹YXЪИЬXЫHШ\™ИЪ]]X[ќ]H€H‹\XШ]WЩЬ›Э\В€
K€њ™Y[™[ЮWЩЬ›Э\ИЋ€Y]љXК€™Y[™[ЮKђШ\Xљ[]Y\И™\™\Щ[ќYћH[Ь™H[€Ы™H[љ\]YHЬXЫHШ\™‹™Y[™[ЮB€
K€B€™]\›€Y]љXЬЛШ\™ШШ\В‚‚™Y€Щљ[™[™ЬКY]љXЬО€XЭЬЭ‹Y]љXЧJHO€\ЭЩXЭЬЭ‹Шљ™XЭWN‚€љ[™[™ЬО€\ЭЩXЭЬЭ‹Шљ™XЭWHHЧB€\ЭЩЬ[HHY]љXЬЦИ›X[WЭ[YWЪ\ЭЩЬ[H—Kќ[YB€Y€\ЭЩЬ[N‚€XZИHX^
\ЭЩЬ[Kќ[Y\К
JB€[Щ\ИHЭ[YH›Ь€[YKЫЭ[ќ[€\ЭЩЬ[Kљ][\К
HY€ЫЭ[ќOHXZЧB€љ[™[™ЬЛ\[™
€В€њЩ]™\љ]HЋ€›ШњЩ\ќ][Ы€‹€њќ[WЪЩ^HЋ€Э\ќ™K›[ЩH‹€›Y]љXЧЪЩ^HЋ€›X[WЭ[YWЪ\ЭЩЬ[H‹€›Y\ЬШYЩHЋ€€•HXЪИ\И[ЬЭЩ€]И›Ы›[™Ш\™И]X[H[YHЙЛ	Лљ›Ъ[Љ[Щ\К_H
ЬXZЯHЫЬY\КK€‹€ќ™\ЪЫЋ€Ињќ[HЋ€[\ЭЩЬ[Hљ[њИ\]X[ИX^[][HЫЬHЫЭ[ќџK€B€
B€\ИHY]љXЬЦИЫЫЬ—Ь™\]Z\™[Y[ќЧШћWЬ\—Kќ[YB€ЫЭ\Щ\ИHY]љXЬЦИ›[™ШЫЫЬ—Ь›ЩXЭ[Ы€—Kќ[YB€›Ь€ЫЫЬ€[€УУФ”О‚€Y€\ЦШЫЫЬ—H€ЫЭ\Щ\ЦШЫЫЬ—VИќ[њ™\ЭљXЭY—N‚€љ[™[™ЬЛ\[™
€В€њЩ]™\љ]HЋ€ќШ\›љ[™И‹€њќ[WЪЩ^HЋ€€›X[KњЪЬќ[ћШЫЫЬ‹›ЭЩ\Љ
_H‹€›Y]љXЧЪЩ^HЋ€›X[WЬЫЭ\ЩWШ]Z[Xљ[]H‹€›Y\ЬШYЩHЋ€€ћШЫЫЬџH™\]Z\™[Y[ќИ
Ь\ЦШЫЫЬ—_H\КH^ЩYY[њ™\ЭљXЭYШЫЫЬџK\›ЩXЪ[™И[™ЫЭ\Щ\И
ЬЫЭ\Щ\ЦШЫЫЬ—VЙЭ[њ™\ЭљXЭY	Ч_JK€‹€ќ™\ЪЫЋ€Ињ\ШЫЭ[ќЩЭЭ[њ™\ЭљXЭYЫ[™ЬЫЭ\Щ\ИЋ€ќY_K€B€
B€Ш\Xљ[]Y\ИHY]љXЬЦИШ\Xљ[]WЭЭ[И—Kќ[YB€Y€Ш\Xљ[]Y\ЦИ›Ш\™]Ъ\H—VИЫЬWШЫЭ[ќ—HOH‚€љ[™[™ЬЛ\[™
€В€њЩ]™\љ]HЋ€ќШ\›љ[™И‹€њќ[WЪЩ^HЋ€Ш\Xљ[]K››ЛX›Ш\™]Ъ\H‹€›Y]љXЧЪЩ^HЋ€Ш\Xљ[]WЭЭ[И‹€›Y\ЬШYЩHЋ€•HXЪИЫЫќZ[њИ›И›Ш\™]Ъ\HШ\Xљ[]K€‹€ќ™\ЪЫЋ€ИЫЬWШЫЭ[ќЋ€K€B€
B€™[[Э[HШ\Xљ[]Y\ЦИќ\™Щ]Y\™[[Э[—VИЫЬWШЫЭ[ќ—B€љ[™[™ЬЛ\[™
€В€њЩ]™\љ]HЋ€љ[™›Ь›X][Ы€‹€њќ[WЪЩ^HЋ€Ш\Xљ[]Kќ\™Щ]Y\™[[Э[‹€›Y]љXЧЪЩ^HЋ€Ш\Xљ[]WЭЭ[И‹€›Y\ЬШYЩHЋ€€ћЬ™[[Э[HШ\™ЫЬY\ИЫЫќљXќ]H\™Щ]Y™[[Э[€‹€ќ™\ЪЫЋ€Ињ™\ЬќЋ€ЫЬWШЫЭ[ќџK€B€
B€љ[љ\Ъ\њИHШ\Xљ[]Y\ЦИ™љ[љ\Ъ\€—VИЫЬWШЫЭ[ќ—B€љ[™[™ЬЛ\[™
€В€њЩ]™\љ]HЋ€љ[™›Ь›X][Ы€‹€њќ[WЪЩ^HЋ€Ш\Xљ[]K™љ[љ\Ъ\њИ‹€›Y]љXЧЪЩ^HЋ€Ш\Xљ[]WЭЭ[И‹€›Y\ЬШYЩHЋ€€ћЩљ[љ\Ъ\њЯHШ\™ЫЬY\И\™HЫ\ЬЪYљYY\Иљ[љ\Ъ\њЛ€‹€ќ™\ЪЫЋ€Ињ™\ЬќЋ€ЫЬWШЫЭ[ќџK€B€
B€Ь™X]\™WЬ][ИH›Ш]
Y]љXЬЦИЬ™X]\™WЬ][И—Kќ[YJB€љ[™[™ЬЛ\[™
€В€њЩ]™\љ]HЋ€›ШњЩ\ќ][Ы€‹€њќ[WЪЩ^HЋ€ЫЫ\ЬЪ][Ы‹Ь™X]\™K\][И‹€›Y]љXЧЪЩ^HЋ€Ь™X]\™WЬ][И‹€›Y\ЬШYЩHЋ€€ђЬ™X]\™HШ\™ИXZЩH\ШЬ™X]\™WЬ][О‹ЊI_HЩ€HXZ[€XЪЛ€‹€ќ™\ЪЫЋ€Ињ™\ЬќЋ€њ][ИџK€B€
B€™]\›€љ[™[™ЬВ‚‚™Y€Ь™[][ЫњЪ\К€ЫЫ›™XЭ[ЫЋ€Ь[]LЛђЫЫ›™XЭ[Ы‹Ш\™О€\ЭЬЬ[]LЛ”›ЭЧKШ\™ШШ\О€XЭЬЭ‹Щ]ЬЭ—WBЉHO€\ЭЩXЭЬЭ‹Шљ™XЭWN‚€XZ[€HЬ›ЭИ›Ь€›ЭИ[€Ш\™ИY€›ЭЦИњЩXЭ[Ы€—HOH›XZ[€—B€Ш\™Э\\ИHЬ›ЭЦИ›ЬXЫWЪY—N€Э\\КЫЫ›™XЭ[Ы‹›ЭЦИ›ЬXЫWЪY—JH›Ь€›ЭИ[€XZ[џB€Ш\™ЬЭXќ\\ИHЬ›ЭЦИ›ЬXЫWЪY—N€ЬЭXќ\\КЫЫ›™XЭ[Ы‹›ЭЦИ›ЬXЫWЪY—JH›Ь€›ЭИ[€XZ[џB€XЭО€XЭЬЭ‹Щ]ЬЭ—WHHВ€ђ\ќYXЭЋ€В€›ЭЦИ›ЬXЫWЪY—H›Ь€›ЭИ[€XZ[€Y€ђ\ќYXЭ€[€Ш\™Э\\ЦЬ›ЭЦИ›ЬXЫWЪY—WB€K€‘\]Z\Y[ќЋ€В€›ЭЦИ›ЬXЫWЪY—H›Ь€›ЭИ[€XZ[€Y€‘\]Z\Y[ќ€[€Ш\™ЬЭXќ\\ЦЬ›ЭЦИ›ЬXЫWЪY—WB€K€B€›Ь€Ш\Xљ[]H[€РTP’SUWТQО‚€XЭЦШШ\Xљ[]WHHВ€›ЭЦИ›ЬXЫWЪY—H›Ь€›ЭИ[€XZ[€Y€Ш\Xљ[]H[€Ш\™ШШ\ЦЬ›ЭЦИ›ЬXЫWЪY—WB€B€™[][ЫњЪ\ИHЧB€›Ь€Щ^KYќљYЪ[€SђSTТTЧФФPЦИњ™[][ЫњЪ\И—N‚€Y€XЭЛ™Щ]
Yќ
H[™XЭЛ™Щ]
љYЪ
N‚€™[][ЫњЪ\Л\[™
€В€њ™[][ЫњЪ\ЪЩ^HЋ€Щ^K€›YќЩXЭЋ€Yќ€њљYЪЩXЭЋ€љYЪ€™]љY[ЩHЋ€В€›YќЫЬXЫWЪYИЋ€ЫЬќY
XЭЦЫYќJK€њљYЪЫЬXЫWЪYИЋ€ЫЬќY
XЭЦЬљYЪJK€K€B€
B€™]\›€™[][ЫњЪ\В‚‚™Y€[[^™WЩXЪК€]X\ЩN€Э€]€XЪЧЭ™\њЪ[Ы—ЪY€[ќ€
‹€XYЫ›ЬЭXО€›ЫЫH[ЩK€Z[ШYќ\—ЫY]љXЬО€›ЫЫH[ЩKЉHO€XЭЬЭ‹Шљ™XЭN‚€[љ]X[^™WЩ]X\ЩJ]X\ЩJB€ЪXЪЬЭ[HH[™Ъ[™WШЪXЪЬЭ[J
B€Э\ќYH]][YK››ЭКUКKљ\ЫЩ›Ь›X]

B€Ъ]ЫЫ›™XЭ
]X\ЩJH\ИЫЫ›™XЭ[Ы‹ЫЫ›™XЭ[ЫЋ‚€[\ЬќYШ\Xљ[]HHЬ›Э™[[ЩJЫЫ›™XЭ[ЫЉB€™\њЪ[Ы‹Ш\™ЛШ\›љ[™ЬИHЫШYЩXЪКЫЫ›™XЭ[Ы‹XЪЧЭ™\њЪ[Ы—ЪYXYЫ›ЬЭXКB€XЪЧШЪXЪЬЭ[HHЩXЪЧШЪXЪЬЭ[J™\њЪ[Ы‹Ш\™КB€ЫЫ›™XЭ[Ы‹™^XЭ]J€’S”СT•S•ИXЪЧШ[[\Ъ\ЧЩ[™Ъ[™WЭ™\њЪ[ЫњК™\њЪ[Ы‹ЪXЪЬЭ[K\ШЬљ\[Ы‹Э]\КH‚€•ђSQTИ
ЛЛЛ	ШXЭ]™IКHУ€УУ‘“PХ
™\њЪ[ЫЉHИ“ХS‘И‹€
€S‘ТS‘WХ‘T”ТSУ‹€ЪXЪЬЭ[K€’[љ]X[]\›Z[љ\ЭXИXЪИY]љXЬИ[™XЪИ[[\Ъ\Иќ[\И‹€
K€
B€ЭЬ™YHЫЫ›™XЭ[Ы‹™^XЭ]J€”СSPХЪXЪЬЭ[H”“УHXЪЧШ[[\Ъ\ЧЩ[™Ъ[™WЭ™\њЪ[ЫњИТT‘H™\њЪ[ЫЏOИ‹
S‘ТS‘WХ‘T”ТSУ‹
B€
K™™]ЪЫ™J
VМB€Y€ЭЬ™YOHЪXЪЬЭ[N‚€Z\ЩHXЪР[[\Ъ\С\њ›ЬЉ€€ђ[[\Ъ\И[™Ъ[™HСS‘ТS‘WХ‘T”ТSУџHЪ[™ЩYЪ]Э]H™\њЪ[Ы€ќ[\‚€
B€ЫЫ›™XЭ[Ы‹™^XЭ]J€•TUHXЪЧШ[[\Ъ\ЧЩ[™Ъ[™WЭ™\њЪ[ЫњИСUЭ]\ПPРTСHТS€™\њЪ[ЫЏOИS€	ШXЭ]™IИSСH	Ь™]\™Y	ИS‘‹€
S‘ТS‘WХ‘T”ТSУ‹
K€
B€ќ[—ЪYHЫЫ›™XЭ[Ы‹™^XЭ]J€’S”СT•S•ИXЪЧШ[[\Ъ\ЧЬќ[њКXЪЧЭ™\њЪ[Ы—ЪY[\ЬќЪYШ\Xљ[]WЬќ[—ЪY[™Ъ[™WЭ™\њЪ[Ы‹‚€™[™Ъ[™WШЪXЪЬЭ[KXЪЧШЪXЪЬЭ[KЭ]\ЛXYЫ›ЬЭXЛЭ\ќYШ]Ш\›љ[™ЬКH‚€•ђSQTИ
ЛЛЛЛЛЛ	Ьќ[›љ[™ЙЛЛЛКH‹€
€XЪЧЭ™\њЪ[Ы—ЪY€[\ЬќYИљY—K€Ш\Xљ[]VИљY—K€S‘ТS‘WХ‘T”ТSУ‹€ЪXЪЬЭ[K€XЪЧШЪXЪЬЭ[K€[ќ
XYЫ›ЬЭXКK€Э\ќY€њЫЫ‹™[\КШ\›љ[™ЬКK€
K€
K›\Э›ЭЪY€ћN‚€Ъ]ЫЫ›™XЭ
]X\ЩJH\ИЫЫ›™XЭ[ЫЋ‚€ЫЫ›™XЭ[Ы‹™^XЭ]Jђ‘QТS€SSQQPUHЉB€ЛЭ\њ™[ќШШ\Xљ[]HHЬ›Э™[[ЩJЫЫ›™XЭ[ЫЉB€Y€Э\њ™[ќШШ\Xљ[]VИљY—HOHШ\Xљ[]VИљY—N‚€Z\ЩHXЪР[[\Ъ\С\њ›ЬЉђШ\Xљ[]H›Э™[[ЩHЪ[™ЩYЪ[H[[\Ъ\ИШ\Иќ[›љ[™ИЉB€ЛЭ\њ™[ќШШ\™ЛИHЫШYЩXЪКЫЫ›™XЭ[Ы‹XЪЧЭ™\њЪ[Ы—ЪYXYЫ›ЬЭXКB€Y€ЩXЪЧШЪXЪЬЭ[J™\њЪ[Ы‹Э\њ™[ќШШ\™КHOHXЪЧШЪXЪЬЭ[N‚€Z\ЩHXЪР[[\Ъ\С\њ›ЬЉ‘XЪИ™\њЪ[Ы€XЭИЪ[™ЩYЪ[H[[\Ъ\ИШ\Иќ[›љ[™ИЉB€Y]љXЬЛШ\™ШШ\ИHЫЫ\]WЫY]љXЬКЫЫ›™XЭ[Ы‹Э\њ™[ќШШ\™КB€›Ь€Щ^KY]љXИ[€ЫЬќY
Y]љXЬЛљ][\К
JN‚€ЫЫ›™XЭ[Ы‹™^XЭ]J€’S”СT•S•ИXЪЧШ[[\Ъ\ЧЫY]љXЬКќ[—ЪYY]љXЧЪЩ^K[YWЪњЫЫ‹›Ь›][K]љY[ЩWЪњЫЫЉH‚€•ђSQTИ
ЛЛЛЛКH‹€
€ќ[—ЪY€Щ^K€њЫЫ‹™[\КY]љXЛќ[YKЫЬќЪЩ^\ПUќYJK€Y]љXЛ™›Ь›][K€њЫЫ‹™[\КY]љXЛ™]љY[ЩKЫЬќЪЩ^\ПUќYJK€
K€
B€Y€Z[ШYќ\—ЫY]љXЬО‚€Z\ЩHќ[ќ[YQ\њ›ЬЉљ[љ™XЭYXЪИ[[\Ъ\ИZ[\™HЉB€љ[™[™ЬИHЩљ[™[™ЬКY]љXЬКB€›Ь€Ь™[[љ[™[™И[€[ќ[Y\]Jљ[™[™ЬКN‚€ЫЫ›™XЭ[Ы‹™^XЭ]J€’S”СT•S•ИXЪЧШ[[\Ъ\ЧЩљ[™[™ЬКќ[—ЪYЬ™[[Щ]™\љ]Kќ[WЪЩ^KY]љXЧЪЩ^K‚€›Y\ЬШYЩK™\ЪЫЪњЫЫЉHђSQTИ
ЛЛЛЛЛЛКH‹€
€ќ[—ЪY€Ь™[[€љ[™[™ЦИњЩ]™\љ]H—K€љ[™[™ЦИњќ[WЪЩ^H—K€љ[™[™ЦИ›Y]љXЧЪЩ^H—K€љ[™[™ЦИ›Y\ЬШYЩH—K€њЫЫ‹™[\Кљ[™[™ЦИќ™\ЪЫ—KЫЬќЪЩ^\ПUќYJK€
K€
B€™[][ЫњЪ\ИHЬ™[][ЫњЪ\КЫЫ›™XЭ[Ы‹Э\њ™[ќШШ\™ЛШ\™ШШ\КB€›Ь€™[][ЫњЪ\[€™[][ЫњЪ\О‚€ЫЫ›™XЭ[Ы‹™^XЭ]J€’S”СT•S•ИXЪЧШ[[\Ъ\ЧЬ™[][ЫњЪ\Кќ[—ЪY™[][ЫњЪ\ЪЩ^KYќЩXЭ‚€њљYЪЩXЭ]љY[ЩWЪњЫЫЉHђSQTИ
ЛЛЛЛКH‹€
€ќ[—ЪY€™[][ЫњЪ\Ињ™[][ЫњЪ\ЪЩ^H—K€™[][ЫњЪ\И›YќЩXЭ—K€™[][ЫњЪ\ИњљYЪЩXЭ—K€њЫЫ‹™[\К™[][ЫњЪ\И™]љY[ЩH—KЫЬќЪЩ^\ПUќYJK€
K€
B€ЫЫ›™XЭ[Ы‹™^XЭ]J€•TUHXЪЧШ[[\Ъ\ЧЬќ[њИСUЭ]\ПIЬЭXШЩYYY	ЛЫЫ\]YШ]OЛY]љXЧШЫЭ[ќOЛ‚€™љ[™[™ЧШЫЭ[ќOЛ™[][ЫњЪ\ШЫЭ[ќOИТT‘HYOИ‹€
€]][YK››ЭКUКKљ\ЫЩ›Ь›X]

K€[ЉY]љXЬКK€[Љљ[™[™ЬКK€[Љ™[][ЫњЪ\КK€ќ[—ЪY€
K€
B€ЫЫ›™XЭ[Ы‹™^XЭ]J€’S”СT•S•ИЭ\њ™[ќЩXЪЧШ[[\Щ\КXЪЧЭ™\њЪ[Ы—ЪYќ[—ЪY
HђSQTИ
ЛКH‚€“У€УУ‘“PХ
XЪЧЭ™\њЪ[Ы—ЪY
HИTUHСUќ[—ЪYY^ЫYYњќ[—ЪY‹€
XЪЧЭ™\њЪ[Ы—ЪYќ[—ЪY
K€
B€ЫЫ›™XЭ[Ы‹ЫЫ[Z]

B€™]\›€В€њќ[—ЪYЋ€ќ[—ЪY€™XЪЧЭ™\њЪ[Ы—ЪYЋ€XЪЧЭ™\њЪ[Ы—ЪY€™XЪЧШЪXЪЬЭ[HЋ€XЪЧШЪXЪЬЭ[K€™[™Ъ[™WЭ™\њЪ[Ы€Ћ€S‘ТS‘WХ‘T”ТSУ‹€™[™Ъ[™WШЪXЪЬЭ[HЋ€ЪXЪЬЭ[K€љ[\ЬќЪYЋ€[\ЬќYИљY—K€Ш\Xљ[]WЬќ[—ЪYЋ€Ш\Xљ[]VИљY—K€›Y]љXЧШЫЭ[ќЋ€[ЉY]љXЬКK€™љ[™[™ЧШЫЭ[ќЋ€[Љљ[™[™ЬКK€њ™[][ЫњЪ\ШЫЭ[ќЋ€[Љ™[][ЫњЪ\КK€ќШ\›љ[™ЬИЋ€Ш\›љ[™ЬЛ€B€^Щ\^Щ\[Ы€\И\њ›ЬЋ‚€Ъ]ЫЫ›™XЭ
]X\ЩJH\ИЫЫ›™XЭ[Ы‹ЫЫ›™XЭ[ЫЋ‚€ЫЫ›™XЭ[Ы‹™^XЭ]J€•TUHXЪЧШ[[\Ъ\ЧЬќ[њИСUЭ]\ПIЩZ[Y	ЛЫЫ\]YШ]OЛ\њ›ЬЏOИТT‘HYOИ‹€
]][YK››ЭКUКKљ\ЫЩ›Ь›X]

KЭЉ\њ›ЬЉKќ[—ЪY
K€
B€Z\ЩHXЪР[[\Ъ\С\њ›ЬЉЭЉ\њ›ЬЉJHњ›ЫH\њ›Ь‚‚‚™Y€[њЬXЭЩXЪК]X\ЩN€Э€]XЪЧЭ™\њЪ[Ы—ЪY€[ќ
HO€XЭЬЭ‹Шљ™XЭN‚€Ъ]ЫЫ›™XЭ
]X\ЩJH\ИЫЫ›™XЭ[ЫЋ‚€ќ[€HЫЫ›™XЭ[Ы‹™^XЭ]J€”СSPХ‹Љ‹‹ќ™\њЪ[Ы—ЫX™[›[YHXЪЧЫ[YKKЪXЪЬЭ[H[\ЬќШЪXЪЬЭ[K‚€Ь‹њќ[\Щ]Э™\њЪ[Ы‹њЛњќ[\ЧШЪXЪЬЭ[HШ\Xљ[]WШЪXЪЬЭ[H”“УHЭ\њ™[ќЩXЪЧШ[[\Щ\ИШH‚€’“ТS€XЪЧШ[[\Ъ\ЧЬќ[њИ€У€‹љYXШKњќ[—ЪY“ТS€XЪЧЭ™\њЪ[ЫњИ€У€‹љY\‹™XЪЧЭ™\њЪ[Ы—ЪY‚€’“ТS€XЪЬИУ€љYY‹™XЪЧЪY“ТS€[\ЬќИHУ€KљY\‹љ[\ЬќЪY‚€’“ТS€Ш\Xљ[]WЩ\љ]][Ы—Ьќ[њИЬ€У€Ь‹љY\‹Ш\Xљ[]WЬќ[—ЪY‚€’“ТS€Ш\Xљ[]WЬќ[WЬЩ]ИњИУ€њЛќ™\њЪ[ЫЏXЬ‹њќ[\Щ]Э™\њЪ[Ы€‚€•ТT‘HШK™XЪЧЭ™\њЪ[Ы—ЪYOИ‹€
XЪЧЭ™\њЪ[Ы—ЪY
K€
K™™]ЪЫ™J
B€Y€ќ[€\И›Ы™N‚€Z\ЩHXЪР[[\Ъ\С\њ›ЬЉ€“›ИЭXШЩ\ЬЩќ[[[\Ъ\И›Ь€XЪИ™\њЪ[Ы€ЩXЪЧЭ™\њЪ[Ы—ЪYHЉB€Y]љXЬИHВ€›ЭЦИ›Y]љXЧЪЩ^H—N€В€ќ[YHЋ€њЫЫ‹›ШYК›ЭЦИќ[YWЪњЫЫ€—JK€™›Ь›][HЋ€›ЭЦИ™›Ь›][H—K€™]љY[ЩHЋ€њЫЫ‹›ШYК›ЭЦИ™]љY[ЩWЪњЫЫ€—JK€B€›Ь€›ЭИ[€ЫЫ›™XЭ[Ы‹™^XЭ]J€”СSPХ
€”“УHXЪЧШ[[\Ъ\ЧЫY]љXЬИТT‘Hќ[—ЪYOИФ‘T€–HY]љXЧЪЩ^H‹€
ќ[–ИљY—K
K€
B€B€љ[™[™ЬИHВ€XЭ
›ЭКB€›Ь€›ЭИ[€ЫЫ›™XЭ[Ы‹™^XЭ]J€”СSPХЩ]™\љ]Kќ[WЪЩ^KY]љXЧЪЩ^KY\ЬШYЩK™\ЪЫЪњЫЫ€”“УHXЪЧШ[[\Ъ\ЧЩљ[™[™ЬИ‚€•ТT‘Hќ[—ЪYOИФ‘T€–HЬ™[[‹€
ќ[–ИљY—K
K€
B€B€™[][ЫњЪ\ИHВ€XЭ
›ЭКB€›Ь€›ЭИ[€ЫЫ›™XЭ[Ы‹™^XЭ]J€”СSPХ™[][ЫњЪ\ЪЩ^KYќЩXЭљYЪЩXЭ]љY[ЩWЪњЫЫ€”“УHXЪЧШ[[\Ъ\ЧЬ™[][ЫњЪ\И‚€•ТT‘Hќ[—ЪYOИФ‘T€–H™[][ЫњЪ\ЪЩ^H‹€
ќ[–ИљY—K
K€
B€B€™]\›€В€њќ[€Ћ€XЭ
ќ[ЉK€›Y]љXЬИЋ€Y]љXЬЛ€™љ[™[™ЬИЋ€љ[™[™ЬЛ€њ™[][ЫњЪ\ИЋ€™[][ЫњЪ\Л€ќШ\›љ[™ЬИЋ€њЫЫ‹›ШYКќ[–ИќШ\›љ[™ЬИ—JK€B‚‚™Y€[[\Ъ\ЧЬЭ]\К]X\ЩN€Э€]
HO€XЭЬЭ‹Шљ™XЭN‚€Ъ]ЫЫ›™XЭ
]X\ЩJH\ИЫЫ›™XЭ[ЫЋ‚€]\ЭHЫЫ›™XЭ[Ы‹™^XЭ]J€”СSPХ
€”“УHXЪЧШ[[\Ъ\ЧЬќ[њИФ‘T€–HYTРИSRUH‚€
K™™]ЪЫ™J
B€ЭXШЩYYYHЫЫ›™XЭ[Ы‹™^XЭ]J€”СSPХУХS•

ЉH”“УHXЪЧШ[[\Ъ\ЧЬќ[њИТT‘HЭ]\ПIЬЭXШЩYYY	И‚€
K™™]ЪЫ™J
VМB€Z[YHЫЫ›™XЭ[Ы‹™^XЭ]J€”СSPХУХS•

ЉH”“УHXЪЧШ[[\Ъ\ЧЬќ[њИТT‘HЭ]\ПIЩZ[Y	И‚€
K™™]ЪЫ™J
VМB€Э\њ™[ќHЫЫ›™XЭ[Ы‹™^XЭ]J”СSPХУХS•

ЉH”“УHЭ\њ™[ќЩXЪЧШ[[\Щ\ИЉK™™]ЪЫ™J
VМB€™]\›€В€™[™Ъ[™WЭ™\њЪ[Ы€Ћ€S‘ТS‘WХ‘T”ТSУ‹€™[™Ъ[™WШЪXЪЬЭ[HЋ€[™Ъ[™WШЪXЪЬЭ[J
K€›]\ЭЬќ[€Ћ€XЭ
]\Э
HY€]\Э[ЩH›Ы™K€њЭXШЩYYYЬќ[њИЋ€ЭXШЩYYY€™Z[YЬќ[њИЋ€Z[Y€Э\њ™[ќЩXЪЧЭ™\њЪ[ЫњИЋ€Э\њ™[ќ€ќШ\›љ[™ЬИЋ€В€“X[K\ЫЭ\ЩHЫЭ[ќИ\™HЫЫњЩ\ќ]]™HXЭЛ›ЭHX[KX\ЩH]X[]HЬYK€‚€K€B