# Coverage-Aware Engine Smoke Stage 0.1 Readiness Audit #1

## Verdict

**NOT READY — the specification is evidence-backed, but the bounded smoke manifest, execution
runner, mechanical-label computation, and atomic success/failure evidence machinery do not yet
exist. No Smoke 0.1 game may run.**

This is a tooling/readiness blocker, not an engine defect and not evidence for Action #14. The
accepted Stage #002 runner supplies reusable conformance primitives, but it cannot execute or
serialize the Smoke 0.1 contract unchanged.

## Frozen audit target

- Specification: `docs/cardcade/COVERAGE_AWARE_ENGINE_SMOKE_STAGE_0.1_SPEC.md`
- Audited SHA-256: `cdf17e0a13c9aaa57e04df84460fa557c144203db0012d7bf964709e0cb66c90`
- Milestone decision: **CONDITIONAL PASS**
- Specification modified during audit: none
- Engine, interpreter, Pilot, runner, decks, or tests modified during audit: none
- Smoke games executed: zero

## Frozen-input reconstruction

All ten deck files exist at the exact specified paths and reproduce their specified SHA-256 values.
The roster, authoritative card snapshot, manifest, and five accepted runtime/conformance files also
reproduce their specified hashes.

The authoritative catalog remains the accepted 472-print / 332-Oracle-object snapshot. The roster
still identifies ten frozen decks. No Prototype 0.3 path or alternate data source is required by the
specification.

**Input-hash finding: PASS.** The specification records reconstructable files, not unattached hash
assertions.

One implementation requirement remains: the current Stage #002 plan manifest does not serialize
the new complete ten-deck smoke universe or all runtime/Pilot hashes. A Smoke 0.1 plan producer must
derive and validate those facts before execution rather than copying them from the specification.

## Matrix reconstruction

Independent enumeration of the lexicographically sorted ten deck IDs produces:

- `C(10, 2) = 45` unordered distinct-deck pairings;
- pair index 0: `april_oneil--bebop_rocksteady`, seeds 8001/8002;
- pair index 44: `shredder--splinter`, seeds 8089/8090;
- 90 pairing/seed combinations;
- canonical and reversed orientation for each combination;
- **180 distinct games**;
- two executions per game;
- **360 total executions**.

All generated pairing/seed/orientation tuples are unique. Duplicates are correctly excluded from
the distinct-game count.

**Matrix-design finding: PASS.** No arithmetic or identity ambiguity was found in the specification.

The current `stage002.PAIRINGS` remains intentionally hard-coded to four Acceptance Stage #002
pairings. Its `build_stage_manifest()` and `stage_games()` cannot produce this 45-pair matrix.
Passing arbitrary games to `execute_stage()` does not fix the manifest: the manifest still derives
its decks and authorized game list from the old four-pair constant.

## Duplicate determinism and evidence authentication

The accepted Stage #002 machinery already provides strong reusable components:

- fresh game construction per execution;
- canonical JSON and SHA-256;
- exact duplicate comparison;
- mature execution-reference authentication;
- opportunity-context and typed-event witness authentication;
- per-game and aggregate digests;
- fail-closed invariant and conformance-stop checks.

Those components passed the accepted 16-game Stage #002 Results Audit after independently
authenticating 70 post-Action execution references and all opportunity provenance.

The Smoke 0.1 contract is stronger than the current serialized form. It requires both complete
canonical duplicate snapshots, both hashes, RNG and authoritative-state terminal digests, and
independent reconstruction from the artifact. Current `execute_stage()` serializes one reconciled
report plus the two hashes; it does not serialize both source snapshots. A fabricated pair of equal
digest strings inside a tampered artifact cannot be checked against two absent canonical byte
streams by an independent consumer.

**Duplicate-policy design finding: PASS.**

**Current executable/serialized readiness: FAIL.** A bounded smoke artifact schema and validator
must preserve and authenticate exactly the evidence promised by the specification.

## Completed-game classification

The specification defines three mutually exclusive mechanical outcomes:

1. MECHANICALLY CLEAN / COVERAGE-COMPLETE;
2. MECHANICALLY CLEAN / COVERAGE-LIMITED;
3. MECHANICALLY INVALID.

Their intended boundaries are unambiguous:

- explicit REACHED / UNSUPPORTED makes a mechanically clean game coverage-limited;
- PRESENT / UNREACHED alone does not;
- a mechanical/evidence failure makes the execution invalid and stops the stage.

The current Stage #002 report does not compute or serialize those labels. It serializes the
underlying classifications, stops, and invariants, leaving the label implicit. It also logs a
turn-limit game as `acceptance_incomplete` without making `execute_stage()` reject `winner is None`
as required by Smoke 0.1.

There is therefore no currently executable proof that every completed or failed smoke execution
receives exactly one label. The smoke layer must derive labels from authenticated evidence and
reject missing, multiple, or contradictory labels.

**Classification-design finding: PASS.**

**Current label-enforcement readiness: FAIL.**

## Balance-boundary isolation

The specification correctly states that completion is insufficient for balance validity. A
coverage-limited game is excluded, and even a coverage-complete game remains only a future balance
candidate until Pilot and statistical-design gates exist.

This boundary is conceptually sound, but no current artifact field or aggregation function enforces
it. `_coverage_summary()` groups semantic classes; it does not produce separate mechanically clean
coverage-complete, coverage-limited, future-balance-candidate, and excluded collections. A later
consumer could aggregate winners without consulting the required label because the protected
balance projection does not yet exist.

The smallest safe design is positive inclusion: a future-balance-candidate list must be generated
only from authenticated coverage-complete labels and must still carry `balance_valid: false` for
Smoke 0.1 because Pilot/statistical gates are absent. Coverage-limited games must be structurally
absent from that collection, not merely accompanied by prose.

**Balance-boundary specification finding: PASS.**

**Current mechanical enforcement readiness: FAIL.**

## Fail-closed and artifact writing

Current Stage #002 operations use `_checked_action()` and stop on engine exceptions,
nondeterministic duplicates, invariant violations, and conformance stops. These are appropriate
reusable foundations.

The current command writes output with `Path.write_text()` only after `execute_stage()` returns:

- success output is not written through a temporary file plus atomic replacement;
- an exception produces no structured failure artifact;
- active game/duplicate identity and completed-game count are not durably checkpointed before the
  failing operation;
- incomplete games are not a stage-level failure;
- the required Stack/Priority/fingerprint failure summary is absent.

Earlier Stage #002 failures demonstrated why these facts matter: tracebacks alone did not preserve
pairing, seed, orientation, or completed-game count.

The specification also asks the successful artifact to contain a "raw artifact digest." A file
cannot naively include the SHA-256 of its own final bytes. The runner contract must define that as
either an external sidecar digest or a digest over an explicitly named body that excludes the
digest field. This is the one smallest wording/schema clarification required by the specification.

**Fail-closed policy finding: PASS.**

**Current atomic evidence readiness: FAIL.**

## Plan-mode finding

The existing Acceptance Stage #002 plan path builds a manifest without creating a `Game`; this is a
useful pattern. No Smoke 0.1 plan function exists, so the audit cannot verify:

- exact 180-game membership in serialized plan evidence;
- the smoke runner/Pilot/runtime hashes;
- plan digest stability;
- no RNG construction/consumption in the new plan path.

**Reusable architecture: present. Smoke-specific readiness: FAIL.**

## Smallest authorized correction

Do not change gameplay. Implement only a bounded Smoke Stage 0.1 tooling layer that:

1. deterministically derives the ten frozen decks and exact 45×2×2 matrix from the specification;
2. emits a plan manifest with all frozen hashes, 180 collision-free game IDs, Pilot/runtime
   fingerprints, and a stable digest without instantiating `Game`;
3. reuses accepted `run_game()`, reconciliation, `_checked_action()`, Priority handling, and
   evidence validators without changing Engine/Interpreter/Pilot semantics;
4. executes each game twice and preserves independently verifiable duplicate evidence;
5. computes exactly one mechanical/coverage label from authenticated evidence;
6. emits an explicit future-balance-candidate projection containing only coverage-complete games
   and marking every entry `balance_valid: false`;
7. rejects incomplete games;
8. writes deterministic atomic success or failure artifacts with exact active execution identity;
9. defines the artifact digest as an external sidecar or an explicit digest-over-body field;
10. adds tamper and boundary regressions for hashes, matrix membership, duplicate evidence,
    classifications, balance leakage, incomplete games, and atomic failure evidence.

This correction may add smoke-specific runner/tooling/tests and documentation. It must not modify
the five accepted runtime files whose hashes are frozen by the specification. If reuse requires
refactoring `stage002.py`, the specification hash boundary must be deliberately revised and
re-audited rather than silently changed.

## Gate decision

- Specification purpose and matrix: **evidence-backed**
- Frozen input reconstructability: **PASS**
- Smoke-specific plan/runner: **missing**
- Independent duplicate serialization: **insufficient for the stronger contract**
- Mechanical label enforcement: **missing**
- Balance-leak prevention: **not mechanically encoded**
- Atomic success/failure evidence: **missing**
- Engine/gameplay blocker established: **none**
- Smoke games executed: **0**

**NOT READY — preserve this audit, implement only the bounded smoke evidence/tooling layer, then
perform Readiness Audit #2 before authorizing any of the 180 games.**

Action #14, the historical 900-game smoke, calibration, Pilot/deck changes, and Prototype 0.3
remain blocked.
