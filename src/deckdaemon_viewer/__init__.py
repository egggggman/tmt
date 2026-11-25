"""DECKDAEMON Gate A: read-only, historical evidence inspection primitives."""

from .reader import (
    BASELINE_PATH,
    DECK_SLUGS,
    EvidenceReadError,
    InspectedEvidence,
    read_baseline_005,
    read_prototype_01,
)

__all__ = [
    "BASELINE_PATH",
    "DECK_SLUGS",
    "EvidenceReadError",
    "InspectedEvidence",
    "read_baseline_005",
    "read_prototype_01",
]
