"""Strict, forward-only provenance validation for Baseline 005 inputs.

Historical manifests remain authoritative records.  The optional overlay only
documents an already-verified LF/CRLF serialization difference; it never
relaxes content, path, deck, or Git-object checks.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

OVERLAY_SCHEMA = "baseline005-provenance-overlay.v1"


class ProvenanceError(ValueError):
    """Raised when an input cannot be authenticated under its declared contract."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_text(data: bytes) -> bytes:
    """Return canonical UTF-8 text bytes, permitting only CRLF-to-LF conversion."""
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ProvenanceError("text input is not valid UTF-8") from exc
    if text.startswith("\ufeff"):
        raise ProvenanceError("UTF-8 BOM is not permitted")
    if "\r" in text.replace("\r\n", ""):
        raise ProvenanceError("bare carriage return is not permitted")
    return text.replace("\r\n", "\n").encode("utf-8")


def git_blob_sha1(root: Path, commit: str, relative: str) -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", f"{commit}:{relative}"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except subprocess.CalledProcessError as exc:
        raise ProvenanceError(f"Git object is missing: {commit}:{relative}") from exc


def parse_deck_rows(data: bytes) -> list[tuple[int, str]]:
    text = canonical_text(data).decode("utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "Deck":
        raise ProvenanceError("deck must begin with Deck header")
    rows: list[tuple[int, str]] = []
    for line in lines[1:]:
        if not line or line != line.strip():
            raise ProvenanceError("deck contains unexplained whitespace")
        try:
            count_text, name = line.split(" ", 1)
            count = int(count_text)
        except (ValueError, TypeError) as exc:
            raise ProvenanceError(f"invalid deck row: {line!r}") from exc
        if count < 0 or not name:
            raise ProvenanceError(f"invalid deck quantity/name: {line!r}")
        rows.append((count, name))
    if sum(count for count, _ in rows) != 60:
        raise ProvenanceError("deck does not contain exactly 60 cards")
    return rows


def verify_deck_record(root: Path, record: dict[str, Any], source_commit: str) -> dict[str, Any]:
    path = record.get("source_path")
    historical = record.get("historical_manifest_sha256")
    if not isinstance(path, str) or not isinstance(historical, str):
        raise ProvenanceError("deck record requires source_path and historical_manifest_sha256")
    if Path(path).is_absolute() or ".." in Path(path).parts:
        raise ProvenanceError(f"unsafe deck path: {path}")
    source = root / path
    if not source.is_file():
        raise ProvenanceError(f"deck source is missing: {path}")
    raw = source.read_bytes()
    canonical = canonical_text(raw)
    rows = parse_deck_rows(raw)
    raw_sha = _sha256(raw)
    canonical_sha = _sha256(canonical)
    crlf_sha = _sha256(canonical.replace(b"\n", b"\r\n"))
    observed_blob = git_blob_sha1(root, source_commit, path)
    if observed_blob != record.get("git_blob_sha1"):
        raise ProvenanceError(f"Git blob mismatch for {path}")
    expected_canonical = record.get("canonical_normalized_sha256")
    if expected_canonical != canonical_sha:
        raise ProvenanceError(f"canonical content mismatch for {path}")
    expected_lf = record.get("current_lf_sha256")
    if expected_lf != _sha256(canonical.replace(b"\r\n", b"\n")):
        raise ProvenanceError(f"LF content mismatch for {path}")
    if raw_sha == historical:
        method = "raw_bytes"
    elif record.get("serialization_convention") == "CRLF" and crlf_sha == historical:
        method = "authorized_crlf_equivalence"
    else:
        raise ProvenanceError(f"historical hash mismatch for {path}")
    return {
        "deck_key": record.get("deck_key"),
        "source_path": path,
        "method": method,
        "historical_manifest_sha256": historical,
        "observed_raw_sha256": raw_sha,
        "current_lf_sha256": _sha256(canonical.replace(b"\r\n", b"\n")),
        "canonical_normalized_sha256": canonical_sha,
        "crlf_equivalent_sha256": crlf_sha,
        "git_blob_sha1": observed_blob,
        "card_row_count": len(rows),
        "card_count": sum(count for count, _ in rows),
    }


def verify_overlay(root: Path, overlay_path: Path) -> dict[str, Any]:
    overlay = json.loads(overlay_path.read_text(encoding="utf-8"))
    if overlay.get("schema") != OVERLAY_SCHEMA:
        raise ProvenanceError("unsupported provenance overlay schema")
    if overlay.get("source_commit") is None:
        raise ProvenanceError("overlay is missing source_commit")
    records = overlay.get("decks")
    if not isinstance(records, list) or len(records) != 10:
        raise ProvenanceError("overlay must contain exactly ten deck records")
    results = [verify_deck_record(root, record, overlay["source_commit"]) for record in records]
    if {row["deck_key"] for row in results} != {record["deck_key"] for record in records}:
        raise ProvenanceError("overlay deck identities are inconsistent")
    return {"schema": OVERLAY_SCHEMA, "verified_decks": results}
