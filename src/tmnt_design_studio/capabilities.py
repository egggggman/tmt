"""Deterministic, evidence-backed capability derivation for Oracle cards."""
# ruff: noqa: E501

from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

from tmnt_design_studio.database import connect, initialize_database

RULESET_VERSION = "2026.08.0"

CATALOG = (
    (
        "targeted-removal",
        "targeted removal",
        "interaction",
        "Removes one or more chosen permanents or creatures.",
    ),
    (
        "board-wipe",
        "board wipe",
        "interaction",
        "Destroys, exiles, or gives a lethal global penalty to a broad class of permanents.",
    ),
    (
        "protection",
        "protection",
        "interaction",
        "Prevents harm to a permanent or player through protection, hexproof, indestructible, or prevention.",
    ),
    ("counterspell", "counterspell", "interaction", "Counters a spell or ability on the stack."),
    ("card-draw", "card draw", "cards", "Directly instructs a player to draw one or more cards."),
    (
        "card-selection",
        "card selection",
        "cards",
        "Looks at, scries, surveils, or otherwise filters cards without inherently increasing hand size.",
    ),
    (
        "ramp",
        "ramp",
        "mana",
        "Creates additional reusable mana capacity or puts extra lands onto the battlefield.",
    ),
    (
        "mana-fixing",
        "mana fixing",
        "mana",
        "Provides a choice of mana colors or changes what colors mana sources can produce.",
    ),
    ("token-creation", "token creation", "board", "Creates one or more game-piece tokens."),
    ("recursion", "recursion", "graveyard", "Returns or casts a card from a graveyard."),
    (
        "graveyard-interaction",
        "graveyard interaction",
        "graveyard",
        "Exiles, moves, or otherwise directly affects cards in a graveyard.",
    ),
    (
        "combat-support",
        "combat support",
        "combat",
        "Directly improves creatures in combat through a temporary team or combat bonus.",
    ),
    (
        "evasion",
        "evasion",
        "combat",
        "Makes a creature harder to block through an evasion keyword or explicit blocking restriction.",
    ),
    ("life-gain", "life gain", "life", "Directly causes a player to gain life."),
    (
        "sacrifice-support",
        "sacrifice support",
        "sacrifice",
        "Provides or rewards sacrificing a permanent as an explicit cost or event.",
    ),
    (
        "artifact-synergy",
        "artifact synergy",
        "synergy",
        "Explicitly references artifacts as a resource, condition, or beneficiary.",
    ),
    (
        "equipment-synergy",
        "equipment synergy",
        "synergy",
        "Explicitly references Equipment or equipping as a resource or beneficiary.",
    ),
    (
        "cost-reduction",
        "cost reduction",
        "mana",
        "Explicitly reduces a spell, ability, or equip cost.",
    ),
    (
        "tempo",
        "tempo",
        "interaction",
        "Temporarily sets an opposing permanent back by returning or tapping it.",
    ),
    (
        "finisher",
        "finisher",
        "threat",
        "Presents explicit broad game-ending pressure rather than merely being expensive.",
    ),
)


@dataclass(frozen=True)
class Rule:
    key: str
    capability: str
    field: str
    pattern: str
    confidence: float
    evidence_type: str = "oracle_text"
    exclude: tuple[str, ...] = ()
    description: str = ""


RULES = (
    Rule(
        "target.destroy",
        "targeted-removal",
        "oracle_text",
        r"destroy target (?:nonland )?(?:permanent|creature|artifact|enchantment|planeswalker)",
        0.95,
    ),
    Rule(
        "target.exile",
        "targeted-removal",
        "oracle_text",
        r"exile target (?:nonland )?(?:permanent|creature|artifact|enchantment|planeswalker)",
        0.95,
    ),
    Rule(
        "wipe.destroy-all",
        "board-wipe",
        "oracle_text",
        r"destroy all (?:creatures|artifacts|enchantments|nonland permanents|permanents)",
        0.98,
    ),
    Rule(
        "wipe.exile-all",
        "board-wipe",
        "oracle_text",
        r"exile all (?:creatures|artifacts|enchantments|nonland permanents|permanents)",
        0.98,
    ),
    Rule(
        "protect.keyword",
        "protection",
        "keyword",
        r"^(?:hexproof|indestructible|protection)$",
        0.90,
        "keyword",
    ),
    Rule(
        "protect.grant",
        "protection",
        "oracle_text",
        r"(?:gains?|have) (?:hexproof|indestructible|protection from)",
        0.90,
    ),
    Rule(
        "counter.spell",
        "counterspell",
        "oracle_text",
        r"counter target (?:spell|activated ability|triggered ability|spell or ability)",
        0.98,
        exclude=(r"can't be countered",),
    ),
    Rule(
        "draw.instruction",
        "card-draw",
        "oracle_text",
        r"\bdraw (?:a|one|two|three|x|that many) cards?\b",
        0.90,
        exclude=(r"if you would draw", r"skip that draw"),
    ),
    Rule("selection.scry", "card-selection", "keyword", r"^(?:scry|surveil)$", 0.95, "keyword"),
    Rule(
        "selection.look",
        "card-selection",
        "oracle_text",
        r"look at the top \w+ cards? of (?:your|a player's) library",
        0.85,
    ),
    Rule(
        "ramp.land",
        "ramp",
        "oracle_text",
        r"put (?:a|up to one|that) land card .* onto the battlefield",
        0.90,
    ),
    Rule("ramp.mana", "ramp", "oracle_text", r"add (?:\{[wubrgc]\}|one mana of any color)", 0.80),
    Rule("fix.any-color", "mana-fixing", "oracle_text", r"add one mana of any color", 0.98),
    Rule(
        "token.create",
        "token-creation",
        "oracle_text",
        r"create (?:a|an|one|two|three|x|that many|those) .* tokens?",
        0.95,
    ),
    Rule(
        "recursion.return",
        "recursion",
        "oracle_text",
        r"return target .* card from (?:your|a) graveyard to (?:your hand|the battlefield)",
        0.95,
    ),
    Rule(
        "recursion.cast",
        "recursion",
        "oracle_text",
        r"cast target .* card from (?:your|a) graveyard",
        0.95,
    ),
    Rule(
        "graveyard.exile",
        "graveyard-interaction",
        "oracle_text",
        r"exile (?:target|up to \w+) cards? from (?:a|target player's|your) graveyard",
        0.95,
    ),
    Rule(
        "combat.team-pump",
        "combat-support",
        "oracle_text",
        r"creatures you control get \+[0-9x]+/\+[0-9x]+ until end of turn",
        0.90,
    ),
    Rule(
        "evasion.keyword",
        "evasion",
        "keyword",
        r"^(?:flying|menace|fear|intimidate|shadow|skulk|horsemanship)$",
        0.90,
        "keyword",
    ),
    Rule("evasion.unblockable", "evasion", "oracle_text", r"can't be blocked", 0.95),
    Rule(
        "life.gain",
        "life-gain",
        "oracle_text",
        r"\b(?:you|target player) gains? (?:[0-9x]+|that much) life\b",
        0.95,
    ),
    Rule(
        "sacrifice.cost",
        "sacrifice-support",
        "oracle_text",
        r"sacrifice (?:a|an|another|one or more) (?:artifact|creature|permanent|token)",
        0.85,
    ),
    Rule(
        "artifact.reference",
        "artifact-synergy",
        "oracle_text",
        r"\bartifacts? (?:you control|spell|card|enters?|dies?|you own)\b",
        0.75,
    ),
    Rule(
        "equipment.reference",
        "equipment-synergy",
        "oracle_text",
        r"\b(?:equipment|equipped|equip cost)\b",
        0.90,
    ),
    Rule("cost.less", "cost-reduction", "oracle_text", r"costs? (?:\{[^}]+\}|[0-9x]+) less", 0.95),
    Rule(
        "tempo.bounce",
        "tempo",
        "oracle_text",
        r"return target (?:nonland )?permanent .* to (?:its|their) owner's hand",
        0.90,
    ),
    Rule(
        "tempo.tap",
        "tempo",
        "oracle_text",
        r"tap target (?:creature|permanent).*doesn't untap",
        0.85,
    ),
    Rule(
        "finisher.extra-combat",
        "finisher",
        "oracle_text",
        r"(?:an|one) additional combat phase",
        0.90,
    ),
    Rule(
        "finisher.team-double",
        "finisher",
        "oracle_text",
        r"creatures you control (?:gain|have) double strike",
        0.90,
    ),
)


class CapabilityError(RuntimeError):
    """A capability configuration or derivation failure."""


def _rules_checksum() -> str:
    payload = json.dumps([rule.__dict__ for rule in RULES], sort_keys=True, separators=(",", ":"))
    return sha256(payload.encode()).hexdigest()


def install_rules(connection: sqlite3.Connection) -> None:
    checksum = _rules_checksum()
    existing = connection.execute(
        "SELECT rules_checksum FROM capability_rule_sets WHERE version=?", (RULESET_VERSION,)
    ).fetchone()
    if existing and existing[0] != checksum:
        raise CapabilityError(f"Rule set {RULESET_VERSION} changed without a version bump")
    connection.execute(
        "INSERT OR IGNORE INTO capability_rule_sets(version,description,rules_checksum,status) "
        "VALUES (?,?,?,'active')",
        (RULESET_VERSION, "Initial narrow objective capability rules", checksum),
    )
    connection.execute(
        "UPDATE capability_rule_sets SET status=CASE WHEN version=? THEN 'active' ELSE 'retired' END",
        (RULESET_VERSION,),
    )
    for identifier, name, category, definition in CATALOG:
        connection.execute(
            "INSERT INTO capabilities(identifier,name,description,category,status) VALUES (?,?,?,?, 'active') "
            "ON CONFLICT(name) DO UPDATE SET identifier=excluded.identifier, "
            "description=excluded.description,category=excluded.category,status='active'",
            (identifier, name, definition, category),
        )
    for rule in RULES:
        capability_id = connection.execute(
            "SELECT id FROM capabilities WHERE identifier=?", (rule.capability,)
        ).fetchone()[0]
        expression = json.dumps(
            {"field": rule.field, "pattern": rule.pattern, "ruleset": RULESET_VERSION},
            sort_keys=True,
        )
        connection.execute(
            "INSERT INTO capability_rules(capability_id,rule_type,expression,active,rule_key,"
            "ruleset_version,rule_version,confidence,fields_read,exclusions,description) "
            "VALUES (?,?,?,1,?,?,1,?,?,?,?) ON CONFLICT(rule_key,ruleset_version,rule_version) "
            "DO UPDATE SET active=1,expression=excluded.expression,confidence=excluded.confidence,"
            "fields_read=excluded.fields_read,exclusions=excluded.exclusions,description=excluded.description",
            (
                capability_id,
                "regex",
                expression,
                rule.key,
                RULESET_VERSION,
                rule.confidence,
                json.dumps([rule.field]),
                json.dumps(rule.exclude),
                rule.description or rule.key,
            ),
        )
    keys = [rule.key for rule in RULES]
    placeholders = ",".join("?" for _ in keys)
    connection.execute(
        f"UPDATE capability_rules SET active=0 WHERE ruleset_version=? AND rule_key NOT IN ({placeholders})",
        (RULESET_VERSION, *keys),
    )


def _facts(
    connection: sqlite3.Connection, oracle_id: str
) -> list[tuple[str, str, str, int | None]]:
    card = connection.execute("SELECT * FROM cards WHERE oracle_id=?", (oracle_id,)).fetchone()
    if card is None:
        return []
    facts = [("oracle_text", card["oracle_text"] or "", "oracle_text", None)]
    facts.extend(
        ("keyword", row[0], "keyword", None)
        for row in connection.execute(
            "SELECT k.name FROM keywords k JOIN card_keywords ck ON ck.keyword_id=k.id "
            "WHERE ck.oracle_id=? ORDER BY k.name",
            (oracle_id,),
        )
    )
    for face in connection.execute(
        "SELECT face_number,oracle_text FROM card_faces WHERE oracle_id=? ORDER BY face_number",
        (oracle_id,),
    ):
        facts.append(("oracle_text", face["oracle_text"] or "", "face", face["face_number"]))
    return facts


def derive_capabilities(
    database: str | Path, *, fail_after: int | None = None
) -> dict[str, object]:
    initialize_database(database)
    now = datetime.now(UTC).isoformat()
    with connect(database) as connection, connection:
        install_rules(connection)
        import_row = connection.execute(
            "SELECT id FROM imports WHERE source='scryfall' AND status='succeeded' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if import_row is None:
            raise CapabilityError("A successful Scryfall import is required")
        run_id = connection.execute(
            "INSERT INTO capability_derivation_runs(ruleset_version,import_id,status,started_at) "
            "VALUES (?,?,'running',?)",
            (RULESET_VERSION, import_row[0], now),
        ).lastrowid
    try:
        with connect(database) as connection:
            connection.execute("BEGIN IMMEDIATE")
            install_rules(connection)
            cards = [
                row[0]
                for row in connection.execute("SELECT oracle_id FROM cards ORDER BY oracle_id")
            ]
            connection.execute("DELETE FROM capability_evidence")
            connection.execute("DELETE FROM card_capabilities")
            matches = 0
            for index, oracle_id in enumerate(cards, 1):
                for rule in RULES:
                    rule_row = connection.execute(
                        "SELECT r.id,c.id FROM capability_rules r JOIN capabilities c ON c.id=r.capability_id "
                        "WHERE r.rule_key=? AND r.ruleset_version=? AND r.active=1",
                        (rule.key, RULESET_VERSION),
                    ).fetchone()
                    for field, value, evidence_type, face_number in _facts(connection, oracle_id):
                        if field != rule.field or any(
                            re.search(x, value, re.I) for x in rule.exclude
                        ):
                            continue
                        match = re.search(rule.pattern, value, re.I)
                        if not match:
                            continue
                        connection.execute(
                            "INSERT OR IGNORE INTO card_capabilities(oracle_id,capability_id,rule_id,"
                            "confidence,derivation_run_id) VALUES (?,?,?,?,?)",
                            (oracle_id, rule_row[1], rule_row[0], rule.confidence, run_id),
                        )
                        connection.execute(
                            "INSERT INTO capability_evidence(oracle_id,capability_id,rule_id,"
                            "derivation_run_id,evidence_type,source_field,source_value,matched_value,"
                            "face_number,confidence) VALUES (?,?,?,?,?,?,?,?,?,?)",
                            (
                                oracle_id,
                                rule_row[1],
                                rule_row[0],
                                run_id,
                                evidence_type,
                                field,
                                value,
                                match.group(0),
                                face_number,
                                rule.confidence,
                            ),
                        )
                        matches += 1
                if fail_after is not None and index >= fail_after:
                    raise RuntimeError("injected derivation failure")
            result_count = connection.execute("SELECT COUNT(*) FROM card_capabilities").fetchone()[
                0
            ]
            connection.execute(
                "UPDATE capability_derivation_runs SET status='succeeded',completed_at=?,"
                "card_count=?,result_count=? WHERE id=?",
                (datetime.now(UTC).isoformat(), len(cards), result_count, run_id),
            )
            connection.commit()
        return {
            "run_id": run_id,
            "ruleset_version": RULESET_VERSION,
            "import_id": import_row[0],
            "card_count": len(cards),
            "result_count": result_count,
            "evidence_count": matches,
        }
    except Exception as error:
        with connect(database) as connection, connection:
            connection.execute(
                "UPDATE capability_derivation_runs SET status='failed',completed_at=?,error=? WHERE id=?",
                (datetime.now(UTC).isoformat(), str(error), run_id),
            )
        raise CapabilityError(str(error)) from error


def effective_capabilities(
    connection: sqlite3.Connection, oracle_id: str
) -> list[dict[str, object]]:
    conflicts = connection.execute(
        "SELECT capability_id FROM capability_overrides WHERE oracle_id=? AND active=1 "
        "GROUP BY capability_id HAVING COUNT(*) > 1",
        (oracle_id,),
    ).fetchall()
    if conflicts:
        raise CapabilityError("Conflicting active capability overrides")
    derived: dict[int, dict[str, object]] = {}
    for row in connection.execute(
        "SELECT c.id,c.identifier,c.name,MAX(cc.confidence) confidence FROM card_capabilities cc "
        "JOIN capabilities c ON c.id=cc.capability_id WHERE cc.oracle_id=? GROUP BY c.id ORDER BY c.identifier",
        (oracle_id,),
    ):
        derived[row["id"]] = {
            "identifier": row["identifier"],
            "name": row["name"],
            "confidence": row["confidence"],
            "source": "derived",
        }
    for row in connection.execute(
        "SELECT o.*,c.identifier,c.name FROM capability_overrides o JOIN capabilities c "
        "ON c.id=o.capability_id WHERE o.oracle_id=? AND o.active=1 ORDER BY c.identifier",
        (oracle_id,),
    ):
        if not row["rationale"].strip() or not row["evidence_context"].strip():
            raise CapabilityError("Active overrides require rationale and evidence context")
        if row["action"] == "remove":
            derived.pop(row["capability_id"], None)
        elif row["action"] == "add":
            confidence = row["confidence"] if row["confidence"] is not None else 1.0
            derived[row["capability_id"]] = {
                "identifier": row["identifier"],
                "name": row["name"],
                "confidence": confidence,
                "source": "override:add",
            }
        elif row["action"] == "adjust":
            if row["capability_id"] not in derived or row["confidence_delta"] is None:
                raise CapabilityError(
                    "Adjust override requires a derived capability and confidence delta"
                )
            value = float(derived[row["capability_id"]]["confidence"]) + row["confidence_delta"]
            derived[row["capability_id"]]["confidence"] = min(1.0, max(0.0, value))
            derived[row["capability_id"]]["source"] = "derived+override:adjust"
    return sorted(derived.values(), key=lambda item: str(item["identifier"]))


def inspect_card(database: str | Path, card: str) -> dict[str, object]:
    with connect(database) as connection:
        row = connection.execute(
            "SELECT * FROM cards WHERE oracle_id=? OR lower(name)=lower(?) ORDER BY oracle_id LIMIT 1",
            (card, card),
        ).fetchone()
        if row is None:
            raise CapabilityError(f"Card not found: {card}")
        effective = effective_capabilities(connection, row["oracle_id"])
        evidence = [
            dict(item)
            for item in connection.execute(
                "SELECT c.identifier,r.rule_key,e.evidence_type,e.source_field,e.matched_value,"
                "e.face_number,e.confidence FROM capability_evidence e JOIN capabilities c "
                "ON c.id=e.capability_id LEFT JOIN capability_rules r ON r.id=e.rule_id "
                "WHERE e.oracle_id=? ORDER BY c.identifier,r.rule_key,e.face_number",
                (row["oracle_id"],),
            )
        ]
        return {
            "oracle_id": row["oracle_id"],
            "name": row["name"],
            "capabilities": effective,
            "evidence": evidence,
        }


def engine_status(database: str | Path) -> dict[str, object]:
    with connect(database) as connection:
        run = connection.execute(
            "SELECT r.*,i.checksum import_checksum,i.source_updated_at FROM capability_derivation_runs r "
            "JOIN imports i ON i.id=r.import_id ORDER BY r.id DESC LIMIT 1"
        ).fetchone()
        counts = dict(
            connection.execute(
                "SELECT c.identifier,COUNT(DISTINCT cc.oracle_id) FROM capabilities c LEFT JOIN "
                "card_capabilities cc ON cc.capability_id=c.id GROUP BY c.id ORDER BY c.identifier"
            )
        )
        return {
            "latest_run": dict(run) if run else None,
            "counts": counts,
            "ruleset_version": RULESET_VERSION,
            "rules_checksum": _rules_checksum(),
        }
