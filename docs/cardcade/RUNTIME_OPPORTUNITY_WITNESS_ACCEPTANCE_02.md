# Runtime Opportunity-Witness Instrumentation — Acceptance Audit #2

Candidate commit: `12b8bd64c9fe92d2a19b97213d873a889736b8d9`  
Parent conformance checkpoint: `491b196377c1e33fdbccde21870f8ae2790085de`  
Audit #1 SHA-256: `f5b35809b8ede664599a5e758b5d63d90f1bcde7e854707e3ff49b537b24a384`  
Status: **ACCEPT**

## Scope

This audit is limited to the corrected runtime opportunity-witness instrumentation. It does not authorize gameplay expansion, Action #13, Pilot changes, deck/prototype changes, smoke testing, calibration, or balance conclusions.

Audit #1 rejected the candidate for two provenance failures:

1. a departed former Alliance permanent could receive a witness from a later creature-entry event;
2. an attack semantic could be linked to an unrelated valid life-gain event.

The smallest requested correction was shared authoritative applicability validation at both witness creation and invariant time.

## Correction review

The corrected candidate uses the same applicability boundary at creation and invariant validation. Applicability is constrained by typed event kind, exact Oracle/fragment shape, chronology, source runtime identity, authoritative source zone/controller state, event subjects, active player/turn/step context, and semantic-specific requirements.

Typed events preserve the battlefield/controller authority required to reconstruct the applicability decision. A later event cannot retroactively make a departed or recontrolled Alliance source applicable. Likewise, an event that is valid in isolation cannot witness an unrelated semantic merely because both records exist in the same game.

The correction is conservative: evidence that cannot prove applicability remains PRESENT / UNREACHED rather than being promoted to REACHED / UNSUPPORTED.

## Audit #1 blocker disposition

### Stale Alliance source

**RESOLVED.** A creature-entry event must join to a source that is still the authoritative qualifying battlefield object under the required controller at the event boundary. Departed, recontrolled, stale, or mismatched source identities fail applicability and therefore cannot create or retain a valid opportunity witness.

### Semantically unrelated event

**RESOLVED.** Witness creation and invariants require the typed event kind and subjects required by the exact semantic. A valid but unrelated life-gain event cannot authenticate an attack semantic. Fabricated or mismatched event/semantic joins are rejected rather than counted as opportunities.

## Corrected Acceptance #001 classification

The correction removes false-positive witnesses from the rejected candidate without changing gameplay or unsupported registration telemetry:

- unsupported registrations: **18 occurrences / 6 exact pairs**;
- **11 REACHED / UNSUPPORTED** occurrences;
- **7 PRESENT / UNREACHED** occurrences;
- **18 authoritative opportunity witnesses**;
- invariant violations: **0**;
- duplicate Acceptance #001 executions: deterministic / byte-identical;
- accepted game trajectories: unchanged.

The reduction from the rejected prospective result (`14 reached / 4 present-only / 32 witnesses`) is expected and desirable. The instrumentation now refuses to promote an occurrence when authoritative applicability cannot be proven.

The seven PRESENT / UNREACHED occurrences are not engine failures. They are semantics present on involved objects for which the frozen Acceptance #001 execution does not provide an authoritative opportunity witness.

## Validation

The preserved candidate is committed at `12b8bd64c9fe92d2a19b97213d873a889736b8d9`. GitHub Actions run `32508262259` completed successfully on that exact head. The corrected candidate was also replayed locally under the Python 3.12 project environment after the earlier Windows Python 3.14 Application Control issue was isolated as an environment/tooling problem rather than a repository defect.

No Stage #002 match was used to validate this correction. No gameplay behavior was added to improve the conformance result.

## Evidence interpretation

`unsupported_semantics` registration remains a PRESENT observation only. REACHED / UNSUPPORTED requires a positive, applicable, authoritative opportunity witness. EXECUTED remains grounded in the mature Action/engine evidence ledgers and is not inferred merely from witness presence.

This preserves the coverage-aware conformance model's central rule: absence of proof is not converted into proof of reach, and unrelated or stale evidence cannot authenticate a semantic opportunity.

## Decision

**ACCEPT — corrected runtime opportunity-witness instrumentation is suitable to bank with the conservative 18-registration / 11-reached / 7-present-only / 18-witness Acceptance #001 classification.**

Next gate after banking/merge: rerun the Acceptance Stage #002 readiness audit against this accepted instrumentation. Stage #002 execution itself remains unauthorized until that readiness gate returns READY.
