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
            "per Capability: copies, unique Oracle cards, and sum(quantity × effective confidence)",
            [],
        ),
        "interaction_density": Metric(
            interaction_copies / nonland_count if nonland_count else 0.0,
            "nonland copies with any interaction Capability / nonland_count",
            [],
        ),
        "threat_density": Metric(
            threat_copies / nonland_count if nonland_count else 0.0,
            "nonland Creature, Planeswalker, Battle, or finisher copies / nonland_count",
            [],
        ),
        "finisher_density": Metric(
            finisher_copies / nonland_count if nonland_count else 0.0,
            "copies with finisher Capability / nonland_count",
            [],
        ),
        "land_ratio": Metric(
            land_count / total if total else 0.0, "land_count / total_card_count", []
        ),
        "creature_ratio": Metric(
            type_counts["creature"] / total if total else 0.0,
            "creature copy count / total_card_count",
            [],
        ),
        "duplicate_groups": Metric(
            duplicate_groups, "main-deck Oracle cards with quantity > 1", duplicate_groups
        ),
        "redundancy_groups": Metric(
            redundancy, "Capabilities represented by more than one unique Oracle card", redundancy
        ),
    }
    return metrics, card_caps


def _findings(metrics: dict[str, Metric]) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    histogram = metrics["mana_value_histogram"].value
    if histogram:
        peak = max(histogram.values())
        modes = [value for value, count in histogram.items() if count == peak]
        findings.append(
            {
                "severity": "observation",
                "rule_key": "curve.mode",
                "metric_key": "mana_value_histogram",
                "message": f"The deck has most of its nonland cards at mana value {', '.join(modes)} ({peak} copies).",
                "threshold": {"rule": "all histogram bins equal to maximum copy count"},
            }
        )
    pips = metrics["color_requirements_by_pip"].value
    sources = metrics["land_color_production"].value
    for color in COLORS:
        if pips[color] > sources[color]["unrestricted"]:
            findings.append(
                {
                    "severity": "warning",
                    "rule_key": f"mana.shortfall.{color.lower()}",
                    "metric_key": "mana_source_availability",
                    "message": f"{color} requirements ({pips[color]} pips) exceed unrestricted {color}-producing land sources ({sources[color]['unrestricted']}).",
                    "threshold": {"pip_count_gt_unrestricted_land_sources": True},
                }
            )
    capabilities = metrics["capability_totals"].value
    if capabilities["board-wipe"]["copy_count"] == 0:
        findings.append(
            {
                "severity": "warning",
                "rule_key": "capability.no-board-wipe",
                "metric_key": "capability_totals",
                "message": "The deck contains no board-wipe Capability.",
                "threshold": {"copy_count": 0},
            }
        )
    removal = capabilities["targeted-removal"]["copy_count"]
    findings.append(
        {
            "severity": "information",
            "rule_key": "capability.targeted-removal",
            "metric_key": "capability_totals",
            "message": f"{removal} card copies contribute targeted removal.",
            "threshold": {"report": "copy_count"},
        }
    )
    finishers = capabilities["finisher"]["copy_count"]
    findings.append(
        {
            "severity": "information",
            "rule_key": "capability.finishers",
            "metric_key": "capability_totals",
            "message": f"{finishers} card copies are classified as finishers.",
            "threshold": {"report": "copy_count"},
        }
    )
    creature_ratio = float(metrics["creature_ratio"].value)
    findings.append(
        {
            "severity": "observation",
            "rule_key": "composition.creature-ratio",
            "metric_key": "creature_ratio",
            "message": f"Creature cards make up {creature_ratio:.1%} of the main deck.",
            "threshold": {"report": "ratio"},
        }
    )
    return findings


def _relationships(
    connection: sqlite3.Connection, cards: list[sqlite3.Row], card_caps: dict[str, set[str]]
) -> list[dict[str, object]]:
    main = [row for row in cards if row["section"] == "main"]
    card_types = {row["oracle_id"]: _types(connection, row["oracle_id"]) for row in main}
    card_subtypes = {row["oracle_id"]: _subtypes(connection, row["oracle_id"]) for row in main}
    facts: dict[str, set[str]] = {
        "Artifact": {
            row["oracle_id"] for row in main if "Artifact" in card_types[row["oracle_id"]]
        },
        "Equipment": {
            row["oracle_id"] for row in main if "Equipment" in card_subtypes[row["oracle_id"]]
        },
    }
    for capability in CAPABILITY_IDS:
        facts[capability] = {
            row["oracle_id"] for row in main if capability in card_caps[row["oracle_id"]]
        }
    relationships = []
    for key, left, right in ANALYSIS_SPEC["relationships"]:
        if facts.get(left) and facts.get(right):
            relationships.append(
                {
                    "relationship_key": key,
                    "left_fact": left,
                    "right_fact": right,
                    "evidence": {
                        "left_oracle_ids": sorted(facts[left]),
                        "right_oracle_ids": sorted(facts[right]),
                    },
                }
            )
    return relationships


def analyze_deck(
    database: str | Path,
    deck_version_id: int,
    *,
    diagnostic: bool = False,
    fail_after_metrics: bool = False,
) -> dict[str, object]:
    initialize_database(database)
    checksum = engine_checksum()
    started = datetime.now(UTC).isoformat()
    with connect(database) as connection, connection:
        imported, capability = _provenance(connection)
        version, cards, warnings = _load_deck(connection, deck_version_id, diagnostic)
        deck_checksum = _deck_checksum(version, cards)
        connection.execute(
            "INSERT INTO deck_analysis_engine_versions(version,checksum,description,status) "
            "VALUES (?,?,?,'active') ON CONFLICT(version) DO NOTHING",
            (
                ENGINE_VERSION,
                checksum,
                "Initial deterministic Deck Metrics and Deck Analysis rules",
            ),
        )
        stored = connection.execute(
            "SELECT checksum FROM deck_analysis_engine_versions WHERE version=?", (ENGINE_VERSION,)
        ).fetchone()[0]
        if stored != checksum:
            raise DeckAnalysisError(
                f"Analysis engine {ENGINE_VERSION} changed without a version bump"
            )
        connection.execute(
            "UPDATE deck_analysis_engine_versions SET status=CASE WHEN version=? THEN 'active' ELSE 'retired' END",
            (ENGINE_VERSION,),
        )
        run_id = connection.execute(
            "INSERT INTO deck_analysis_runs(deck_version_id,import_id,capability_run_id,engine_version,"
            "engine_checksum,deck_checksum,status,diagnostic,started_at,warnings) "
            "VALUES (?,?,?,?,?,?,'running',?,?,?)",
            (
                deck_version_id,
                imported["id"],
                capability["id"],
                ENGINE_VERSION,
                checksum,
                deck_checksum,
                int(diagnostic),
                started,
                json.dumps(warnings),
            ),
        ).lastrowid
    try:
        with connect(database) as connection:
            connection.execute("BEGIN IMMEDIATE")
            _, current_capability = _provenance(connection)
            if current_capability["id"] != capability["id"]:
                raise DeckAnalysisError("Capability provenance changed while analysis was running")
            _, current_cards, _ = _load_deck(connection, deck_version_id, diagnostic)
            if _deck_checksum(version, current_cards) != deck_checksum:
                raise DeckAnalysisError("Deck Version facts changed while analysis was running")
            metrics, card_caps = compute_metrics(connection, current_cards)
            for key, metric in sorted(metrics.items()):
                connection.execute(
                    "INSERT INTO deck_analysis_metrics(run_id,metric_key,value_json,formula,evidence_json) "
                    "VALUES (?,?,?,?,?)",
                    (
                        run_id,
                        key,
                        json.dumps(metric.value, sort_keys=True),
                        metric.formula,
                        json.dumps(metric.evidence, sort_keys=True),
                    ),
                )
            if fail_after_metrics:
                raise RuntimeError("injected deck analysis failure")
            findings = _findings(metrics)
            for ordinal, finding in enumerate(findings):
                connection.execute(
                    "INSERT INTO deck_analysis_findings(run_id,ordinal,severity,rule_key,metric_key,"
                    "message,threshold_json) VALUES (?,?,?,?,?,?,?)",
                    (
                        run_id,
                        ordinal,
                        finding["severity"],
                        finding["rule_key"],
                        finding["metric_key"],
                        finding["message"],
                        json.dumps(finding["threshold"], sort_keys=True),
                    ),
                )
            relationships = _relationships(connection, current_cards, card_caps)
            for relationship in relationships:
                connection.execute(
                    "INSERT INTO deck_analysis_relationships(run_id,relationship_key,left_fact,"
                    "right_fact,evidence_json) VALUES (?,?,?,?,?)",
                    (
                        run_id,
                        relationship["relationship_key"],
                        relationship["left_fact"],
                        relationship["right_fact"],
                        json.dumps(relationship["evidence"], sort_keys=True),
                    ),
                )
            connection.execute(
                "UPDATE deck_analysis_runs SET status='succeeded',completed_at=?,metric_count=?,"
                "finding_count=?,relationship_count=? WHERE id=?",
                (
                    datetime.now(UTC).isoformat(),
                    len(metrics),
                    len(findings),
                    len(relationships),
                    run_id,
                ),
            )
            connection.execute(
                "INSERT INTO current_deck_analyses(deck_version_id,run_id) VALUES (?,?) "
                "ON CONFLICT(deck_version_id) DO UPDATE SET run_id=excluded.run_id",
                (deck_version_id, run_id),
            )
            connection.commit()
        return {
            "run_id": run_id,
            "deck_version_id": deck_version_id,
            "deck_checksum": deck_checksum,
            "engine_version": ENGINE_VERSION,
            "engine_checksum": checksum,
            "import_id": imported["id"],
            "capability_run_id": capability["id"],
            "metric_count": len(metrics),
            "finding_count": len(findings),
            "relationship_count": len(relationships),
            "warnings": warnings,
        }
    except Exception as error:
        with connect(database) as connection, connection:
            connection.execute(
                "UPDATE deck_analysis_runs SET status='failed',completed_at=?,error=? WHERE id=?",
                (datetime.now(UTC).isoformat(), str(error), run_id),
            )
        raise DeckAnalysisError(str(error)) from error


def inspect_deck(database: str | Path, deck_version_id: int) -> dict[str, object]:
    with connect(database) as connection:
        run = connection.execute(
            "SELECT r.*,dv.version_label,d.name deck_name,i.checksum import_checksum,"
            "cr.ruleset_version,rs.rules_checksum capability_checksum FROM current_deck_analyses ca "
            "JOIN deck_analysis_runs r ON r.id=ca.run_id JOIN deck_versions dv ON dv.id=r.deck_version_id "
            "JOIN decks d ON d.id=dv.deck_id JOIN imports i ON i.id=r.import_id "
            "JOIN capability_derivation_runs cr ON cr.id=r.capability_run_id "
            "JOIN capability_rule_sets rs ON rs.version=cr.ruleset_version "
            "WHERE ca.deck_version_id=?",
            (deck_version_id,),
        ).fetchone()
        if run is None:
            raise DeckAnalysisError(f"No successful analysis for Deck Version {deck_version_id}")
        metrics = {
            row["metric_key"]: {
                "value": json.loads(row["value_json"]),
                "formula": row["formula"],
                "evidence": json.loads(row["evidence_json"]),
            }
            for row in connection.execute(
                "SELECT * FROM deck_analysis_metrics WHERE run_id=? ORDER BY metric_key",
                (run["id"],),
            )
        }
        findings = [
            dict(row)
            for row in connection.execute(
                "SELECT severity,rule_key,metric_key,message,threshold_json FROM deck_analysis_findings "
                "WHERE run_id=? ORDER BY ordinal",
                (run["id"],),
            )
        ]
        relationships = [
            dict(row)
            for row in connection.execute(
                "SELECT relationship_key,left_fact,right_fact,evidence_json FROM deck_analysis_relationships "
                "WHERE run_id=? ORDER BY relationship_key",
                (run["id"],),
            )
        ]
        return {
            "run": dict(run),
            "metrics": metrics,
            "findings": findings,
            "relationships": relationships,
            "warnings": json.loads(run["warnings"]),
        }


def analysis_status(database: str | Path) -> dict[str, object]:
    with connect(database) as connection:
        latest = connection.execute(
            "SELECT * FROM deck_analysis_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
        succeeded = connection.execute(
            "SELECT COUNT(*) FROM deck_analysis_runs WHERE status='succeeded'"
        ).fetchone()[0]
        failed = connection.execute(
            "SELECT COUNT(*) FROM deck_analysis_runs WHERE status='failed'"
        ).fetchone()[0]
        current = connection.execute("SELECT COUNT(*) FROM current_deck_analyses").fetchone()[0]
        return {
            "engine_version": ENGINE_VERSION,
            "engine_checksum": engine_checksum(),
            "latest_run": dict(latest) if latest else None,
            "succeeded_runs": succeeded,
            "failed_runs": failed,
            "current_deck_versions": current,
            "warnings": [
                "Mana-source counts are conservative facts, not a mana-base quality grade."
            ],
        }
