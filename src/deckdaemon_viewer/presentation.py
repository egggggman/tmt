"""Inspection-only presentation model; no Tk imports or filesystem writes."""

from __future__ import annotations

from pathlib import Path

from .reader import (
    BASELINE_PATH,
    DECK_SLUGS,
    EvidenceReadError,
    InspectedEvidence,
    read_baseline_005,
    read_prototype_01,
)

ROSTER = tuple(sorted(DECK_SLUGS))
TITLE = "DECKDAEMON 0.1 — INSPECTION ONLY — NO GAMEPLAY"


def describe(evidence: InspectedEvidence) -> tuple[str, str]:
    """Return inert text for the UI without interpreting evidence as code."""
    status = (
        "VERIFIED AGAINST SUPPLIED DIGEST" if evidence.verified else "UNVERIFIED LOCAL SNAPSHOT"
    )
    header = (
        f"{evidence.classification}\n"
        f"Path: {evidence.relative_path}\n"
        f"Provenance: {evidence.provenance}\n"
        f"Observed SHA-256: {evidence.observed_sha256}\n"
        f"Trust: {status}\n"
        "\n"
    )
    return status, header + evidence.content


class InspectionSession:
    """Selection adapter, deliberately limited to Gate A reader APIs."""

    def __init__(self, snapshot_root: str | Path):
        self.snapshot_root = Path(snapshot_root)

    def deck(self, slug: str) -> tuple[str, str]:
        if slug not in DECK_SLUGS:
            raise EvidenceReadError("deck not in frozen allowlist")
        return describe(read_prototype_01(self.snapshot_root, slug))

    def baseline(self) -> tuple[str, str]:
        return describe(read_baseline_005(self.snapshot_root))


__all__ = ["BASELINE_PATH", "ROSTER", "TITLE", "InspectionSession", "describe"]
