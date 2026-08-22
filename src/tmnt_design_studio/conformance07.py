"""Action-neutral runtime conformance evidence for Cardcade.

This module records semantic presence and positive opportunity witnesses.  It deliberately
does not interpret or execute an Action; mature Action-specific evidence remains authoritative
for EXECUTED classifications.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256


class RuntimeConformanceClass(Enum):
    EXECUTED = "executed"
    REACHED_UNSUPPORTED = "reached_unsupported"
    PRESENT_UNREACHED = "present_unreached"


def fragment_digest(fragment: str) -> str:
    return sha256(fragment.encode("utf-8")).hexdigest()


def semantic_key(oracle_id: str, face_index: int, fragment_index: int, fragment: str) -> str:
    """Return a stable key without relying on card names or Python hash behavior."""
    identity = oracle_id or f"definition:{fragment_digest(fragment)}"
    return f"{identity}:{face_index}:{fragment_index}:{fragment_digest(fragment)}"


def opportunity_context_key(*parts: object) -> str:
    """Digest immutable typed-context provenance without Python hash behavior."""
    return fragment_digest("|".join(str(part) for part in parts))


@dataclass(frozen=True)
class SemanticOccurrence:
    occurrence_id: str
    semantic_key: str
    oracle_id: str
    face_index: int
    fragment_index: int
    fragment_hash: str
    object_id: str
    controller: int
    zone: str
    oracle_fragment: str
    limitations: tuple[str, ...]
    turn: int
    phase: str
    step: str
    registration_event_cursor: int


@dataclass(frozen=True)
class OpportunityWitness:
    witness_id: str
    opportunity_key: str
    occurrence_id: str
    semantic_key: str
    object_id: str
    controller: int
    oracle_fragment: str
    turn: int
    phase: str
    step: str
    cause_kind: str
    cause_id: str
    cause_subject_ids: tuple[str, ...]
    source_zone: str
    source_controller: int
    cause_subject_zones: tuple[str, ...]
    cause_event_kind: str | None
    classification: RuntimeConformanceClass = RuntimeConformanceClass.REACHED_UNSUPPORTED


@dataclass(frozen=True)
class AuthoritativeOpportunityContext:
    """Immutable, Action-neutral proof that a rules context was reached.

    ``context_kind`` is deliberately a rules boundary rather than an Action name.  The
    engine creates these records from authoritative state transitions; conformance code
    may join an unsupported Oracle fragment to one only when its bounded applicability
    grammar and every subject identity agree.
    """

    context_id: str
    context_key: str
    context_kind: str
    turn: int
    phase: str
    step: str
    active_player: int
    controller: int
    source_id: str
    subject_ids: tuple[str, ...]
    subject_zones: tuple[str, ...]
    facts: tuple[tuple[str, str], ...]
    event_id: str | None = None
    stack_object_id: str | None = None
    state_fingerprint: str = ""


@dataclass(frozen=True)
class ConformanceStopRecord:
    """Canonical evidence for a mechanically enforced Stage conformance stop."""

    stop_id: str
    kind: str
    turn: int
    phase: str
    step: str
    before_fingerprint: str
    after_fingerprint: str
    detail: str
