"""Bounded, allowlisted, inspection-only reader; never execute project code.

This module cannot certify a mutable file by itself. A SHA-256 is merely an
observed digest unless independently supplied by a reviewed, immutable source.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DECK_SLUGS = frozenset(
    {
        "leonardo", "raphael", "donatello", "michelangelo", "splinter",
        "april_oneil", "casey_jones", "shredder", "krang", "bebop_rocksteady",
    }
)
BASELINE_PATH = "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json"
_MAX_DECK_BYTES = 1_048_576
_MAX_MANIFEST_BYTES = 262_144
_SHA256_RE = re.compile(r"[a-fA-F0-9]{64}\Z")


class EvidenceReadError(ValueError):
    """Reject a missing, unapproved, malformed, or untrusted evidence input."""


@dataclass(frozen=True)
class InspectedEvidence:
    relative_path: str
    content: str
    observed_sha256: str
    verified: bool
    provenance: str
    classification: str
    parsed: dict[str, Any] | None = None


def _duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceReadError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _nonfinite(value: str) -> None:
    raise EvidenceReadError(f"nonfinite JSON number forbidden: {value}")


def _check_digest(expected_sha256: str | None) -> str | None:
    if expected_sha256 is None:
        return None
    if not isinstance(expected_sha256, str) or not _SHA256_RE.fullmatch(expected_sha256):
        raise EvidenceReadError("expected SHA-256 must be 64 hexadecimal characters")
    return expected_sha256.lower()


def _read_allowed(
    root: Path | str, parts: tuple[str, ...], *, max_bytes: int, expected_sha256: str | None
) -> tuple[str, str, bool]:
    expected = _check_digest(expected_sha256)
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise EvidenceReadError("snapshot root must exist and be a non-symlink directory")
    resolved_root = root.resolve(strict=True)
    current = resolved_root
    for part in parts:
        if not part or part in {".", ".."} or "/" in part or "\\" in part:
            raise EvidenceReadError("unsafe evidence path component")
        current = current / part
        if current.is_symlink():
            raise EvidenceReadError("symlink evidence path is forbidden")
    try:
        canonical = current.resolve(strict=True)
        if not canonical.is_relative_to(resolved_root):
            raise EvidenceReadError("evidence path escaped snapshot root")
        # O_NOFOLLOW prevents final-component symlink substitution on systems
        # where supported. Inspection of intermediate components is also done
        # above; immutable snapshot roots are still required for real trust.
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(canonical, flags)
        try:
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode):
                raise EvidenceReadError("evidence must be a regular file")
            if metadata.st_size > max_bytes:
                raise EvidenceReadError("evidence exceeds byte limit")
            with os.fdopen(descriptor, "rb", closefd=False) as handle:
                blob = handle.read(max_bytes + 1)
            if len(blob) > max_bytes:
                raise EvidenceReadError("evidence exceeds byte limit")
        finally:
            os.close(descriptor)
    except EvidenceReadError:
        raise
    except (OSError, RuntimeError) as error:
        raise EvidenceReadError("evidence cannot be read") from error
    digest = hashlib.sha256(blob).hexdigest()
    if expected is not None and digest != expected:
        raise EvidenceReadError("evidence SHA-256 mismatch")
    try:
        text = blob.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise EvidenceReadError("evidence must be UTF-8") from error
    return text, digest, expected is not None


def read_prototype_01(
    snapshot_root: Path | str, slug: str, *, expected_sha256: str | None = None
) -> InspectedEvidence:
    """Read only an explicit roster member's preserved Prototype 0.1 deck."""
    if not isinstance(slug, str) or slug not in DECK_SLUGS:
        raise EvidenceReadError("deck slug not in frozen inspection allowlist")
    parts = ("decks", slug, "PROTOTYPE_0.1.txt")
    text, digest, verified = _read_allowed(
        snapshot_root, parts, max_bytes=_MAX_DECK_BYTES, expected_sha256=expected_sha256
    )
    if not text.strip():
        raise EvidenceReadError("empty deck source")
    return InspectedEvidence(
        "/".join(parts), text, digest, verified,
        "independently supplied SHA-256 matched" if verified else "unverified local snapshot",
        "Preserved Prototype 0.1 (not a current legal-deck certification)",
    )


def _validate_baseline(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise EvidenceReadError("baseline JSON root must be an object")
    expected = {
        "schema": "objective-balance-lab-official-baseline-v1",
        "environment_id": "OBL-BASELINE-005",
        "state": "OFFICIAL_BASELINE",
    }
    for key, value in expected.items():
        if data.get(key) != value:
            raise EvidenceReadError(f"unexpected baseline {key}")
    if not isinstance(data.get("repository_sha"), str) or not re.fullmatch(
        r"[a-fA-F0-9]{40}", data["repository_sha"]
    ):
        raise EvidenceReadError("baseline repository SHA missing or invalid")
    metrics = data.get("per_deck_metrics")
    if not isinstance(metrics, dict) or set(metrics) != DECK_SLUGS:
        raise EvidenceReadError("baseline roster mismatch")
    for slug, item in metrics.items():
        if not isinstance(item, dict):
            raise EvidenceReadError(f"invalid metric group for {slug}")
        rate = item.get("win_rate")
        if isinstance(rate, bool) or not isinstance(rate, (int, float)) or not 0 <= rate <= 1:
            raise EvidenceReadError(f"invalid win rate for {slug}")
        opponents = item.get("matchup_win_rates")
        if not isinstance(opponents, dict) or set(opponents) != (DECK_SLUGS - {slug}):
            raise EvidenceReadError(f"invalid matchup roster for {slug}")
        for opponent, value in opponents.items():
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not 0 <= value <= 1
            ):
                raise EvidenceReadError(f"invalid matchup {slug}/{opponent}")
    return data


def read_baseline_005(
    snapshot_root: Path | str, *, expected_sha256: str | None = None
) -> InspectedEvidence:
    """Inspect an existing baseline manifest; never generate new game metrics."""
    text, digest, verified = _read_allowed(
        snapshot_root, tuple(BASELINE_PATH.split("/")),
        max_bytes=_MAX_MANIFEST_BYTES, expected_sha256=expected_sha256,
    )
    try:
        decoded = json.loads(text, object_pairs_hook=_duplicate_keys, parse_constant=_nonfinite)
    except (json.JSONDecodeError, TypeError, ValueError) as error:
        raise EvidenceReadError("invalid baseline JSON") from error
    parsed = _validate_baseline(decoded)
    return InspectedEvidence(
        BASELINE_PATH, text, digest, verified,
        "independently supplied SHA-256 matched" if verified else "unverified local snapshot",
        "Historical Baseline 005 — not a live or newly calibrated result", parsed,
    )
