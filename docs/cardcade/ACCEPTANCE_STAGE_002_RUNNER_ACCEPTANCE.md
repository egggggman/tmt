# Acceptance Stage #002 Runner Acceptance Audit #1

Candidate: `6f2fbdf7a802b7efd065610aba71e555bbd20ac4`  
Evidence baseline: `48eff0a54c5cf32c7c8ad47c4e4aabcdf1e10418`  
Verdict: **REJECT**

## Scope and preserved strengths

This was an independent evidence-only audit of the immutable Stage #002 runner candidate. No
Stage #002 match was run.

The candidate correctly freezes the four pairings, two seeds, and both orientations as 16 distinct
games and 32 duplicate executions. It records frozen deck hashes, static SemanticCoverage,
observability, Acceptance #001 overlap/novelty, runtime identity lineages, deterministic
per-game/aggregate evidence, and canonical fail-closed conditions. The CLI requires an explicit
`--execute` flag. Tests cover nondeterminism, invariant and conformance stops, rejected-action
mutation, lineage, and Acceptance #001 regression.

## Material blocker: EXECUTED authentication

`reconcile_snapshot()` authenticates an `executed_reference` only by matching its semantic key and
source object lineage. It does not prove that the reference's `evidence_kind` and `evidence_id`
resolve to the authoritative Action transaction/event serialized in the same snapshot.

The positive fixture demonstrates the defect by inventing `evidence_kind = "bounded-action"` and
`evidence_id = "e-1"`. Because the source and semantic key are genuine, the candidate promotes the
occurrence from PRESENT / UNREACHED to EXECUTED despite there being no authoritative transaction
with that identity.

This permits a malformed or fabricated EXECUTED reference to overclaim runtime conformance and
violates the Stage #002 requirement that unauthenticated execution evidence fail closed.

## Smallest correction

Do not change gameplay or Action support. Build a bounded execution-evidence index from the
authoritative serialized transaction collections and typed event records already carried by the
snapshot. Every executed reference must resolve by evidence kind and ID and agree with the
transaction's source and semantic provenance.

Required adversarial evidence:

- fabricated evidence ID is rejected;
- wrong evidence kind is rejected;
- a real transaction cannot be borrowed by another source;
- semantic key and source lineage alone are insufficient;
- a genuinely linked transaction still classifies EXECUTED.

## Immutable-candidate CI

GitHub subsequently attached push run `32549796816` to the audited SHA. It **FAILED** with
`552 passed / 1 failed / 1 skipped`: the Acceptance #001 parity test imported
`scripts.run_acceptance_match_001`, but `scripts` is not an importable package in the Linux CI
environment. This is a cross-platform test-harness defect, not a gameplay result. The correction
must make the parity fixture import-independent and rerun the complete gate.

## Gate

**REJECT — EXECUTED evidence is not reconstructively authenticated against its claimed
authoritative transaction, and immutable-candidate CI also fails on a cross-platform test import.
Correct only those runner/evidence defects, then submit the uncommitted corrected candidate for
Runner Acceptance Audit #2.**

Stage #002, Action #13, smoke testing, calibration, Prototype 0.3, Pilot changes, and deck changes
remain blocked.
