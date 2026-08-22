# Acceptance Stage #002 Runner Acceptance Audit #2

Candidate: `8741163f6c24d9099e389f486e848e2687efeb31`  
Rejected candidate: `6f2fbdf7a802b7efd065610aba71e555bbd20ac4`  
Audit #1 evidence SHA-256: `d413be99d6d0df53d9b5818d5484a2bd6d70ec7390976c649c49dd6d876fefe2`  
Verdict: **ACCEPT**

## Scope

This was an independent evidence-only audit of the immutable corrected Stage #002 runner. No
Stage #002 match was run. No gameplay, Action, Pilot, deck, prototype, calibration, or smoke
behavior was added or changed.

The audit re-examined the Runner Audit #1 blocker: a claimed EXECUTED occurrence had been accepted
from semantic-key and source-lineage agreement without authenticating the referenced transaction.
It also rechecked the Linux CI parity-fixture failure attached to the rejected candidate.

## Execution-evidence authentication

The corrected runner constructs a bounded index from authoritative transaction and typed-event
collections serialized in the game snapshot. An `executed_reference` is authenticated only when:

- its exact evidence kind and evidence ID resolve to an authoritative record;
- that record agrees with the claimed source runtime identity;
- the authoritative Oracle fragment agrees exactly;
- the manifest and runtime semantic keys agree; and
- the represented source belongs to the occurrence's authoritative runtime lineage.

Only authenticated references contribute to EXECUTED classification or transaction aggregation.
A malformed reference cannot promote PRESENT / UNREACHED or REACHED / UNSUPPORTED evidence. It
instead produces a fail-closed `silent_approximation` conformance stop.

## Adversarial result

Executable regressions prove that:

- a fabricated evidence ID is rejected;
- an incorrect evidence kind is rejected;
- semantic-key and source-lineage agreement without a transaction is insufficient;
- a genuine transaction cannot be borrowed by another source;
- a correctly linked authoritative transaction still promotes its occurrence to EXECUTED; and
- reconciliation uses only the authenticated reference set.

The evidence index remains bounded to existing serialized Action, combat, Stack, and typed-event
records. It does not infer execution from opportunity witnesses or introduce a new semantic path.
Existing mature Action-specific transaction evidence remains authoritative.

## Determinism and regression integrity

The cross-platform Acceptance #001 parity fixture now loads its runner by explicit file location
rather than assuming `scripts` is an importable package. This is a test-harness correction and does
not alter runtime behavior.

Local validation of the corrected immutable candidate reproduced:

- full suite: **557 passed / 1 skipped**;
- Stage #002 runner: **23 passed**;
- runtime conformance: **35 passed**;
- card-data integrity: **5 passed**;
- Ruff format/check: clean;
- `git diff --check`: clean;
- frozen manifest digest:
  `58788be5bc4322ba7ffc5aa36b1df61fd3f487d6b2ea539b3129a998d4cdf771`.

Acceptance #001 seeds 7001–7005 were replayed twice with byte-identical duplicate artifacts and
unchanged trajectories. The prospective conformance result remained:

- **18 unsupported registrations / 6 exact pairs**;
- **11 REACHED / UNSUPPORTED**;
- **7 PRESENT / UNREACHED**;
- **18 authoritative opportunity witnesses**;
- **126 / 126 EXECUTED references authenticated**;
- **0 invariant violations**.

No Stage #002 game was executed during implementation or audit.

## Immutable-candidate CI

GitHub Actions push run `32550499188` completed successfully against the exact candidate SHA
`8741163f6c24d9099e389f486e848e2687efeb31`. This resolves the outstanding immutable-candidate CI
gate and independently confirms the corrected cross-platform fixture.

## Verdict

**ACCEPT — the corrected Stage #002 conformance runner reconstructively authenticates EXECUTED
evidence, fails closed on malformed references, preserves deterministic gameplay and conformance
classification, and is suitable to bank and integrate. Stage #002 execution remains blocked until
the accepted runner is merged and a merged-main readiness re-audit returns READY.**
