"""Transactional import of objective Scryfall card facts."""

from __future__ import annotations

import gzip
import json
import sqlite3
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from io import BytesIO
from pathlib import Path, PurePosixPath
from typing import Any

from tmnt_design_studio.database import connect, initialize_database

BULK_DATA_URL = "https://api.scryfall.com/bulk-data"
USER_AGENT = "TMNTDesignStudio/0.3.0 (+https://github.com/egggggman/tmt)"
REQUEST_HEADERS = {"User-Agent": USER_AGENT, "Accept": "application/json"}
LEGALITY_VALUES = {"legal", "not_legal", "restricted", "banned"}
CARD_TYPES = {
    "Artifact",
    "Battle",
    "Boss",
    "Card",
    "Conspiracy",
    "Creature",
    "Dungeon",
    "Emblem",
    "Enchantment",
    "Instant",
    "Event",
    "Hero",
    "Kindred",
    "Land",
    "Phenomenon",
    "Plane",
    "Planeswalker",
    "Scheme",
    "Sorcery",
    "Sticker",
    "Stickers",
    "Summon",
    "Token",
    "Universewalker",
    "Vanguard",
}


class ScryfallImportError(RuntimeError):
    """An actionable source or validation failure."""


@dataclass(frozen=True)
class ImportSummary:
    import_id: int
    checksum: str
    processed_count: int
    oracle_count: int
    printing_count: int
    standard_legal_count: int
    warning_count: int
    source_updated_at: str | None


def _request_json(url: str) -> Any:
    request = urllib.request.Request(url, headers=REQUEST_HEADERS)
    try:
        with urllib.request.urlopen(request, timeout=120) as response:  # noqa: S310
            return json.loads(response.read())
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as error:
        raise ScryfallImportError(
            f"Could not read Scryfall metadata from {url}: {error}"
        ) from error


def _download(url: str) -> bytes:
    request = urllib.request.Request(url, headers=REQUEST_HEADERS)
    try:
        with urllib.request.urlopen(request, timeout=300) as response:  # noqa: S310
            return response.read()
    except (OSError, urllib.error.URLError) as error:
        raise ScryfallImportError(
            f"Could not download Scryfall bulk data from {url}: {error}"
        ) from error


def _decode_payload(raw: bytes, source_name: str) -> list[dict[str, Any]]:
    try:
        if raw.startswith(b"\x1f\x8b"):
            raw = gzip.decompress(raw)
        elif raw.startswith(b"PK\x03\x04"):
            with zipfile.ZipFile(BytesIO(raw)) as archive:
                json_members = sorted(
                    (member for member in archive.infolist() if member.filename.endswith(".json")),
                    key=lambda member: member.filename,
                )
                if len(json_members) != 1:
                    raise ScryfallImportError(
                        f"{source_name} archive must contain exactly one JSON file; "
                        f"found {len(json_members)}"
                    )
                member = json_members[0]
                member_path = PurePosixPath(member.filename)
                if (
                    "\\" in member.filename
                    or member_path.is_absolute()
                    or len(member_path.parts) != 1
                    or ".." in member_path.parts
                    or member.is_dir()
                ):
                    raise ScryfallImportError(
                        f"{source_name} archive JSON must be one safe root-level file"
                    )
                raw = archive.read(member)
        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError as array_error:
            text = raw.decode("utf-8")
            if text.lstrip().startswith("["):
                raise array_error
            decoded = []
            for line_number, line in enumerate(text.splitlines(), 1):
                if not line.strip():
                    continue
                try:
                    decoded.append(json.loads(line))
                except json.JSONDecodeError as line_error:
                    raise ScryfallImportError(
                        f"Malformed Scryfall JSONL in {source_name} at line {line_number}: "
                        f"{line_error}"
                    ) from line_error
    except (
        gzip.BadGzipFile,
        zipfile.BadZipFile,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as error:
        raise ScryfallImportError(f"Malformed Scryfall JSON in {source_name}: {error}") from error
    if not isinstance(decoded, list):
        raise ScryfallImportError(f"Scryfall bulk data in {source_name} must be a JSON array")
    if not all(isinstance(record, dict) for record in decoded):
        raise ScryfallImportError(f"Every Scryfall record in {source_name} must be an object")
    return decoded


def _source(file: Path | None, bulk_type: str) -> tuple[bytes, dict[str, Any]]:
    if file is not None:
        try:
            raw = file.read_bytes()
        except OSError as error:
            raise ScryfallImportError(f"Could not read fixture file {file}: {error}") from error
        return raw, {"type": "local_fixture", "name": file.name, "uri": str(file.resolve())}

    metadata = _request_json(BULK_DATA_URL)
    entries = metadata.get("data") if isinstance(metadata, dict) else None
    match = next(
        (
            entry
            for entry in entries or []
            if isinstance(entry, dict) and entry.get("type") == bulk_type
        ),
        None,
    )
    download_uri = (match.get("jsonl_download_uri") if isinstance(match, dict) else None) or (
        match.get("download_uri") if isinstance(match, dict) else None
    )
    if match is None or not isinstance(download_uri, str):
        raise ScryfallImportError(f"Scryfall did not advertise bulk data type {bulk_type!r}")
    return _download(download_uri), match


def _required(record: dict[str, Any], field: str, position: int) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ScryfallImportError(f"Record {position} is missing required field {field!r}")
    return value


def _type_parts(type_line: str) -> tuple[list[str], list[str]]:
    normalized = type_line.replace("—", "-")
    left, separator, right = normalized.partition("-")
    types = [token for token in left.split() if token in CARD_TYPES]
    subtypes = right.split() if separator else []
    return types, subtypes


def _canonicalize_record(record: dict[str, Any], position: int) -> dict[str, Any]:
    if record.get("oracle_id"):
        return record
    faces = record.get("card_faces")
    if record.get("layout") != "reversible_card" or not isinstance(faces, list) or not faces:
        _required(record, "oracle_id", position)
    face_oracle_ids = {
        face.get("oracle_id") for face in faces if isinstance(face, dict) and face.get("oracle_id")
    }
    if len(face_oracle_ids) != 1:
        raise ScryfallImportError(
            f"Record {position} reversible faces must share exactly one Oracle id"
        )
    first_face = faces[0]
    if not isinstance(first_face, dict):
        raise ScryfallImportError(f"Record {position} face 0 must be an object")
    canonical = dict(record)
    canonical["oracle_id"] = face_oracle_ids.pop()
    for field in ("name", "mana_cost", "cmc", "oracle_text", "type_line"):
        if first_face.get(field) is not None:
            canonical[field] = first_face[field]
    return canonical


def _validate(records: list[dict[str, Any]]) -> list[str]:
    if not records:
        raise ScryfallImportError("Scryfall bulk data contains no records")
    scryfall_ids: set[str] = set()
    printing_keys: set[tuple[str, str]] = set()
    warnings: list[str] = []
    for position, record in enumerate(records, 1):
        scryfall_id = _required(record, "id", position)
        _required(record, "oracle_id", position)
        _required(record, "name", position)
        type_line = _required(record, "type_line", position)
        set_code = _required(record, "set", position)
        collector_number = _required(record, "collector_number", position)
        if scryfall_id in scryfall_ids:
            raise ScryfallImportError(f"Duplicate Scryfall id {scryfall_id!r}")
        scryfall_ids.add(scryfall_id)
        printing_key = (set_code, collector_number)
        if printing_key in printing_keys:
            raise ScryfallImportError(
                f"Duplicate printing identifier {set_code}/{collector_number}"
            )
        printing_keys.add(printing_key)
        legality = record.get("legalities", {}).get("standard")
        if legality not in LEGALITY_VALUES:
            raise ScryfallImportError(
                f"Record {position} has invalid or missing Standard legality {legality!r}"
            )
        types, _ = _type_parts(type_line)
        if not types:
            warnings.append(f"Record {position} has no recognized card type: {type_line}")
        faces = record.get("card_faces", [])
        if faces is not None and not isinstance(faces, list):
            raise ScryfallImportError(f"Record {position} card_faces must be an array")
        for face_number, face in enumerate(faces or []):
            if not isinstance(face, dict):
                raise ScryfallImportError(f"Record {position} face {face_number} must be an object")
            _required(face, "name", position)
            if not face.get("type_line"):
                warnings.append(
                    f"Record {position} face {face_number} uses its card-level type line"
                )
    return warnings


def _upsert_vocabulary(
    connection: sqlite3.Connection, table: str, relationship: str, oracle_id: str, values: list[str]
) -> None:
    for value in sorted(set(values)):
        connection.execute(f"INSERT OR IGNORE INTO {table}(name) VALUES (?)", (value,))
        connection.execute(
            f"INSERT OR IGNORE INTO {relationship}(oracle_id, {table[:-1]}_id) "
            f"SELECT ?, id FROM {table} WHERE name = ?",
            (oracle_id, value),
        )


def import_scryfall(
    database: str | Path, *, file: Path | None = None, bulk_type: str = "default_cards"
) -> ImportSummary:
    """Import one bulk snapshot and return its recorded outcome."""
    initialize_database(database)
    started_at = datetime.now(UTC).isoformat()
    initial_uri = str(file.resolve()) if file is not None else BULK_DATA_URL
    initial_type = "local_fixture" if file is not None else bulk_type

    with connect(database) as connection, connection:
        cursor = connection.execute(
            "INSERT INTO imports(source, status, source_uri, source_type, started_at) "
            "VALUES ('scryfall', 'running', ?, ?, ?)",
            (initial_uri, initial_type, started_at),
        )
        import_id = int(cursor.lastrowid)

    try:
        raw, metadata = _source(file, bulk_type)
        checksum = sha256(raw).hexdigest()
        source_uri = str(
            metadata.get("jsonl_download_uri")
            or metadata.get("download_uri")
            or metadata.get("uri")
            or initial_uri
        )
        source_type = str(metadata.get("type") or initial_type)
        source_updated_at = metadata.get("updated_at")
        source_date = str(source_updated_at)[:10] if source_updated_at else None
        metadata_json = json.dumps(metadata, sort_keys=True, separators=(",", ":"))
        with connect(database) as connection, connection:
            connection.execute(
                "UPDATE imports SET source_date=?, source_uri=?, source_type=?, "
                "source_updated_at=?, checksum=?, source_size=?, source_metadata=? WHERE id=?",
                (
                    source_date,
                    source_uri,
                    source_type,
                    source_updated_at,
                    checksum,
                    len(raw),
                    metadata_json,
                    import_id,
                ),
            )
        records = [
            _canonicalize_record(record, position)
            for position, record in enumerate(
                _decode_payload(raw, source_uri or "Scryfall source"), 1
            )
        ]
        warnings = _validate(records)
        oracle_ids = sorted({str(record["oracle_id"]) for record in records})
        scryfall_ids = sorted(str(record["id"]) for record in records)
        with connect(database) as connection:
            connection.execute("BEGIN IMMEDIATE")
            for record in sorted(
                records, key=lambda item: (str(item["oracle_id"]), str(item["id"]))
            ):
                oracle_id = str(record["oracle_id"])
                colors = "".join(sorted(str(color) for color in record.get("color_identity", [])))
                connection.execute(
                    "INSERT INTO cards(oracle_id, name, mana_cost, mana_value, oracle_text, "
                    "color_identity, type_line) VALUES (?, ?, ?, ?, ?, ?, ?) "
                    "ON CONFLICT(oracle_id) DO UPDATE SET name=excluded.name, "
                    "mana_cost=excluded.mana_cost, mana_value=excluded.mana_value, "
                    "oracle_text=excluded.oracle_text, color_identity=excluded.color_identity, "
                    "type_line=excluded.type_line",
                    (
                        oracle_id,
                        record["name"],
                        record.get("mana_cost"),
                        float(record.get("cmc", 0)),
                        record.get("oracle_text"),
                        colors,
                        record["type_line"],
                    ),
                )
                connection.execute(
                    "INSERT INTO card_printings("
                    "scryfall_id, oracle_id, set_code, collector_number, "
                    "rarity, artist, released_at) VALUES (?, ?, ?, ?, ?, ?, ?) "
                    "ON CONFLICT(scryfall_id) DO UPDATE SET oracle_id=excluded.oracle_id, "
                    "set_code=excluded.set_code, collector_number=excluded.collector_number, "
                    "rarity=excluded.rarity, artist=excluded.artist, "
                    "released_at=excluded.released_at",
                    (
                        record["id"],
                        oracle_id,
                        record["set"],
                        record["collector_number"],
                        record["rarity"],
                        record.get("artist"),
                        record.get("released_at"),
                    ),
                )
                connection.execute(
                    "INSERT INTO legalities(oracle_id, format, legality) VALUES (?, 'standard', ?) "
                    "ON CONFLICT(oracle_id, format) DO UPDATE SET legality=excluded.legality",
                    (oracle_id, record["legalities"]["standard"]),
                )
            connection.execute(
                "CREATE TEMP TABLE current_import_oracle_ids(oracle_id TEXT PRIMARY KEY)"
            )
            connection.execute(
                "CREATE TEMP TABLE current_import_scryfall_ids(scryfall_id TEXT PRIMARY KEY)"
            )
            connection.executemany(
                "INSERT INTO current_import_oracle_ids(oracle_id) VALUES (?)",
                ((oracle_id,) for oracle_id in oracle_ids),
            )
            connection.executemany(
                "INSERT INTO current_import_scryfall_ids(scryfall_id) VALUES (?)",
                ((scryfall_id,) for scryfall_id in scryfall_ids),
            )
            for relationship in ("card_faces", "card_keywords", "card_types", "card_subtypes"):
                connection.execute(
                    f"DELETE FROM {relationship} WHERE oracle_id IN "
                    "(SELECT oracle_id FROM current_import_oracle_ids)"
                )
            connection.execute(
                "DELETE FROM card_printings WHERE oracle_id IN "
                "(SELECT oracle_id FROM current_import_oracle_ids) AND scryfall_id NOT IN "
                "(SELECT scryfall_id FROM current_import_scryfall_ids)"
            )
            for record in sorted(
                records, key=lambda item: (str(item["oracle_id"]), str(item["id"]))
            ):
                oracle_id = str(record["oracle_id"])
                for face_number, face in enumerate(record.get("card_faces") or []):
                    connection.execute(
                        "INSERT OR REPLACE INTO card_faces("
                        "oracle_id, face_number, name, mana_cost, "
                        "oracle_text, type_line) VALUES (?, ?, ?, ?, ?, ?)",
                        (
                            oracle_id,
                            face_number,
                            face["name"],
                            face.get("mana_cost"),
                            face.get("oracle_text"),
                            face.get("type_line") or record["type_line"],
                        ),
                    )
                types, subtypes = _type_parts(str(record["type_line"]))
                _upsert_vocabulary(
                    connection,
                    "keywords",
                    "card_keywords",
                    oracle_id,
                    record.get("keywords", []),
                )
                _upsert_vocabulary(connection, "types", "card_types", oracle_id, types)
                _upsert_vocabulary(connection, "subtypes", "card_subtypes", oracle_id, subtypes)
            foreign_key_errors = connection.execute("PRAGMA foreign_key_check").fetchall()
            if foreign_key_errors:
                raise ScryfallImportError(
                    f"Foreign-key validation found {len(foreign_key_errors)} error(s)"
                )
            actual_printings = connection.execute(
                "SELECT COUNT(*) FROM card_printings WHERE scryfall_id IN "
                "(SELECT scryfall_id FROM current_import_scryfall_ids)"
            ).fetchone()[0]
            if actual_printings != len(records):
                raise ScryfallImportError(
                    f"Expected {len(records)} imported printings but found {actual_printings}"
                )
            legal_count = connection.execute(
                "SELECT COUNT(*) FROM legalities WHERE format='standard' AND legality='legal' "
                "AND oracle_id IN (SELECT oracle_id FROM current_import_oracle_ids)"
            ).fetchone()[0]
            connection.execute(
                "UPDATE imports SET status='succeeded', imported_count=?, processed_count=?, "
                "warning_count=?, warnings=?, completed_at=? WHERE id=?",
                (
                    len(oracle_ids),
                    len(records),
                    len(warnings),
                    json.dumps(warnings),
                    datetime.now(UTC).isoformat(),
                    import_id,
                ),
            )
            connection.commit()
    except Exception as error:
        with connect(database) as connection, connection:
            connection.execute(
                "UPDATE imports SET status='failed', error=?, error_count=1, "
                "completed_at=? WHERE id=?",
                (str(error), datetime.now(UTC).isoformat(), import_id),
            )
        if isinstance(error, ScryfallImportError):
            raise
        raise ScryfallImportError(f"Scryfall import failed: {error}") from error

    return ImportSummary(
        import_id=import_id,
        checksum=checksum,
        processed_count=len(records),
        oracle_count=len(oracle_ids),
        printing_count=len(records),
        standard_legal_count=legal_count,
        warning_count=len(warnings),
        source_updated_at=str(source_updated_at) if source_updated_at else None,
    )
