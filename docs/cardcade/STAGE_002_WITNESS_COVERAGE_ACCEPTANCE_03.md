# Stage #002 Witness Coverage — Acceptance Audit #3

Accepted candidate: `e89edb7c31808b96903d722b043a6c40d6f8a525`  
Audit #2 evidence checkpoint: `c1336c741d4c1173981f3ca14595e36ba229f2b6`  
Status: **ACCEPT**

## Scope

This independent evidence-only audit addresses the two provenance blockers preserved by Audit #2.
It does not authorize or implement gameplay semantics, Action #13, Equipment, Stage #002 matches,
Pilot/deck changes, Prototype 0.3, smoke testing, or calibration.

## Instruction-occurrence provenance

**RESOLVED.** Every `instruction_reached` context now freezes the exact semantic occurrence ID,
semantic key, Oracle fragment hash, and fragment index. A target-choice context freezes the same
instruction occurrence ID and the referenced instruction-context ID. Applicability requires all of
those identities to agree with the occurrence being promoted.

The adversarial two-instruction regression proves that two eligible instructions belonging to the
same source and resolution boundary receive distinct immutable provenance and cannot borrow one
another's context.

## Artifact-count provenance

**RESOLVED.** The accepted source-specific `each other artifact you control` form freezes:

- the exact affected source object;
- the complete counted artifact identity set;
- the resulting count;
- the exact excluded source identity;
- the typed artifact-entry event that caused reevaluation.

Invariant validation reconstructs the controlled artifact set from the authoritative event's
battlefield snapshot and verifies the source exclusion and count. The generic artifact-entry
trigger remains independently bounded to its exact Oracle-derived shape.

## Equipment boundary

**CONSERVATIVELY DEFERRED.** The engine does not yet represent an authoritative Equipment
attachment relationship sufficient to prove that `Equipped creature gets … for each artifact you
control` is applicable. That form is therefore no longer eligible for artifact-dependency
promotion. The regression proves an unequipped Equipment remains PRESENT / UNREACHED.

No Equipment behavior was added merely to satisfy the evidence gate.

## Validation and regression result

- Full suite: **534 passed / 1 skipped**
- Runtime conformance suite: **35 passed**
- Card-data integrity: **5 passed**
- Ruff format/check: clean
- `git diff --check`: clean
- Acceptance #001: unchanged at **18 registrations / 6 pairs**
- Prospective classification: **11 REACHED / UNSUPPORTED + 7 PRESENT / UNREACHED**
- Authoritative witnesses: **18**
- Duplicate seeds 7001–7005: byte-identical
- Trajectories: unchanged
- Invariant violations: **0**

GitHub push CI for the accepted candidate subsequently completed successfully as run
`32547530876`.

## Verdict

**ACCEPT — the bounded Stage #002 opportunity-witness instrumentation has reconstructive exact
instruction-occurrence and artifact-count provenance, conservatively defers unrepresented
Equipment attachment, and is suitable to bank and integrate.**

This is not a claim of complete Magic semantic coverage. Stage #002 remains blocked until the
accepted instrumentation is merged and Readiness Audit #03 independently returns READY.
