# Acceptance Stage #002 Results-Evidence Serialization Acceptance Audit #1

## Verdict

**ACCEPT — the bounded Stage #002 duplicate/context serialization correction is suitable to bank and integrate.**

This acceptance applies only to evidence serialization and validation. It does not accept the
historical rejected Stage #002 result, change gameplay coverage, authorize Action #13, or authorize
a Stage #002 rerun before integration and merged-main validation.

## Audited checkpoint

- Candidate: `23e9eeece7f33d6b7306a58fa636b4519b8c5338`
- Candidate delta: `src/tmnt_design_studio/stage002.py` and
  `tests/test_stage002_runner.py` only
- Historical Results Audit #1 REJECT is preserved at commit
  `2be9cb0816b3182fa981545e7270678e5f91ac91`
- Exact-candidate CI: PASS, GitHub Actions run `32581455011`
- Local and remote candidate SHAs: exact match
- Candidate worktree before audit: clean

No implementation or test file was modified during this audit. The rejected raw artifact remained
immutable and Stage #002 was not rerun.

## Duplicate execution evidence

The producer independently canonicalizes the first and second execution snapshots and computes a
SHA-256 digest from each byte string. It stores both values under
`duplicate_execution_digests`, retains the first digest as the compatibility
`duplicate_sha256`, and records explicit `duplicate_byte_equivalent` state.

The runner compares the complete canonical first and second snapshots before reconciliation. A
mismatch raises `nondeterministic duplicate` and prevents a Stage result from being returned. The
durable validator independently requires:

- exactly `first` and `second` digest members;
- two valid lowercase SHA-256 strings;
- exact equality between them;
- agreement between the first digest and the legacy digest;
- an explicit true byte-equivalence claim.

The aggregate digest covers the serialized duplicate evidence. Independent probes altered each
digest separately, the legacy digest, and the equivalence claim. Every mutation failed validation.
The evidence is therefore reconstructive at the accepted digest boundary rather than a single
producer assertion.

## Opportunity-context reconstruction

Every per-game report now serializes the complete immutable `opportunity_contexts` collection used
by context-backed witnesses. Each record preserves:

- deterministic context ID and context key;
- bounded context kind;
- turn, phase, step, and active player;
- controller and source runtime identity;
- ordered subject identities and zones;
- typed immutable facts;
- event and Stack provenance where present;
- authoritative state fingerprint.

Both reconciliation and durable-result validation recompute every context key from those fields.
They require a valid state-fingerprint shape and equal subject/zone cardinality. For every witness
whose cause is an authoritative context, exactly one context must match its cause ID and agree on:

- source object;
- controller/source controller;
- turn, phase, and step;
- ordered subjects and zones;
- absence of an incompatible rules-event cause.

Unreferenced contexts remain an `unclassified_reach` stop. Missing, duplicate, malformed, or
mismatched referenced contexts produce a fail-closed `silent_approximation` stop. Complete contexts
are included in the per-game report digest and therefore in the aggregate digest.

## Independent adversarial probes

The audit constructed a valid deterministic one-game result in memory, independently recomputed
its context key and witness linkage, and passed it through the durable validator. It then challenged
separate copies with each mutation below. All were rejected:

- first duplicate digest;
- second duplicate digest;
- byte-equivalence flag;
- legacy duplicate digest;
- missing context;
- duplicate context ID/record;
- malformed context key;
- substituted/borrowed source;
- controller mismatch;
- turn mismatch;
- phase mismatch;
- step mismatch;
- subject-identity mismatch;
- subject-zone mismatch;
- witness referencing another context;
- per-game report digest tampering;
- aggregate digest tampering.

The valid result continued to pass. The tests also retain the original nondeterministic-runner stop,
so the new serialization does not replace the actual full-snapshot comparison.

## Classification and gameplay preservation

The correction adds evidence fields and validation only. It does not alter semantic interpretation,
classification precedence, legal actions, state mutation, RNG, Priority, Pilot choices, decks, or
gameplay Actions.

Acceptance #001 seeds 7001–7005 were independently replayed twice. Duplicate outputs were
byte-identical, conformance stops remained zero, and trajectories remained:

- 7001 — Raphael, turn 14;
- 7002 — Raphael, turn 18;
- 7003 — Leonardo, turn 19;
- 7004 — Leonardo, turn 43;
- 7005 — Raphael, turn 16.

The historical rejected Stage #002 artifact remains SHA-256
`0e1631f24fba87eca54566f9072a9e1651e00f9c9ca73e75e1bfaa7522fc66c7`.
It was not patched, reclassified, or rerun during this audit.

## Validation

- Full suite: `575 passed / 1 skipped`
- Stage #002 runner suite: `39 passed`
- Ruff format/check: clean
- `git diff --check`: clean before this report
- Exact-candidate CI: PASS
- Stage #002 executions during audit: `0`

## Gate

- Results-evidence serialization: **ACCEPTED**
- Eligible next sequence: bank this report, integrate the correction, validate merged `main`, then
  authorize a fresh Stage #002 run from game #1
- Historical Stage #002 results: remain **REJECTED** evidence
- Action #13, smoke, calibration, Prototype 0.3, Pilot changes, gameplay changes, and deck revisions:
  blocked

**ACCEPT — the corrected Stage #002 result format preserves independently auditable duplicate and authoritative-context evidence and is suitable to integrate.**
