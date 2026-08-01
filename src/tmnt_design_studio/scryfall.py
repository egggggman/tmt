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
from pathlib import Path
from typing import Any

from tmnt_design_studio.database import connect, initialize_database

BULK_DATA_URL = "https://api.scryfall.com/bulk-data"
USER_AGENT = "TMNTDesignStudio/0.3.0 (+https://github.com/egggggman/tmt)"
LEGALITY_VALUES = {"legal", "not_legal", "restricted", "banned"}
CARD_TYPES = {
    "Artifact",
    "Battle",
    "Conspiracy",
    "Creature",
    "Dungeon",
    "Enchantment",
    "Instant",
    "Kindred",
    "Land",
    "Phenomenon",
    "Plane",
    "Planeswalker",
    "Scheme",
    "Sorcery",
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
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=120) as response:  # noqa: S310
            return json.loads(response.read())
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as error:
        raise ScryfallImportError(
            f"Could not read Scryfall metadata from {url}: {error}"
        ) from error


def _download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
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
                json_files = sorted(name for name in archive.namelist() if name.endswith(".json"))
                if len(json_files) != 1:
                    raise ScryfallImportError(
                        f"{source_name} archive must contain exactly one JSON file; "
                        f"found {len(json_files)}"
                    )
                raw = archive.read(json_files[0])
        decoded = json.loads(raw)
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
    if match is None or not isinstance(match.get("download_uri"), str):
        raise ScryfallImportError(f"Scryfall did not advertise bulk data type {bulk_type!r}")
    return _download(match["download_uri"]), match


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
            _required(face, "type_line", position)
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
    raw, metadata = _source(file, bulk_type)
    checksum = sha256(raw).hexdigest()
    source_uri = str(metadata.get("download_uri") or metadata.get("uri") or "")
    source_type = str(metadata.get("type") or bulk_type)
    source_updated_at = metadata.get("updated_at")
    source_date = str(source_updated_at)[:10] if source_updated_at else None
    metadata_json = json.dumps(metadata, sort_keys=True, separators=(",", ":"))
    started_at = datetime.now(UTC).isoformat()

    with connect(database) as connection, connection:
        cursor = connection.execute(
            "INSERT INTO imports(source, source_date, status, source_uri, source_type, "
            "source_updated_at, checksum, source_size, source_metadata, started_at) "
            "VALUES ('scryfall', ?, 'running', ?, ?, ?, ?, ?, ?, ?)",
            (
                source_date,
                source_uri,
                source_type,
                source_updated_at,
                checksum,
                len(raw),
                metadata_json,
                started_at,
            ),
        )
        import_id = int(cursor.lastrowid)

    try:
        records = _decode_payload(raw, source_uri or "Scryfall source")
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
            placeholders = ",".join("?" for _ in oracle_ids)
            for relationship in ("card_faces", "card_keywords", "card_types", "card_subtypes"):
                connection.execute(
                    f"DELETE FROM {relationship} WHERE oracle_id IN ({placeholders})", oracle_ids
                )
            if scryfall_ids:
                printing_placeholders = ",".join("?" for _ in scryfall_ids)
                connection.execute(
                    f"DELETE FROM card_printings WHERE oracle_id IN ({placeholders}) "
                    f"AND scryfall_id NOT IN ({printing_placeholders})",
                    [*oracle_ids, *scryfall_ids],
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
                            face["type_line"],
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
            printing_parameters = ",".join("?" for _ in scryfall_ids)
            actual_printings = connection.execute(
                f"SELECT COUNT(*) FROM card_printings WHERE scryfall_id IN ({printing_parameters})",
                scryfall_ids,
            ).fetchone()[0]
            if actual_printings != len(records):
                raise ScryfallImportError(
                    f"Expected {len(records)} imported printings but found {actual_printings}"
                )
            legal_count = connection.execute(
                f"SELECT COUNT(*) FROM legalities WHERE format='standard' AND legality='legal' "
                f"AND oracle_id IN ({placeholders})",
                oracle_ids,
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
