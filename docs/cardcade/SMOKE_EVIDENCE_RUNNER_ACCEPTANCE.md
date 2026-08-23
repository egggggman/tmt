# Coverage-Aware Smoke 0.1 Evidence Runner Acceptance Audit #1

Status: **REJECT**

## Audit target and scope

- Evidence checkpoint: `102ac018…`
- Frozen runner candidate: `42d31d625637023b04aad2658d096f0611336815`
- Runner SHA-256: `e76c6367ae3ddf7f0f24d6144f3ad1260436aa9b791ff2b88efea3078164733a`
- Specification SHA-256:
  `cdf17e0a13c9aaa57e04df84460fa557c144203db0012d7bf964709e0cb66c90`
- Readiness Audit #1 SHA-256:
  `509d90c4b8811c94539201921c318f8e8d9a4613b05041eef886d3bb6c16cc8d`
- Candidate CI: **UNCONFIRMED**
- Smoke games executed during this audit: **0**

The candidate is exactly one commit beyond the evidence checkpoint and adds only the smoke CLI,
runner, and runner tests. No Engine, Card Interpreter, conformance, Stage #002, Pilot, Action, deck,
or Prototype file changed.

The audit inspected the immutable candidate, independently rebuilt its plan, ran the complete
regression gate, and used synthetic snapshots only to attack result validation and failure
serialization. It did not execute the Smoke 0.1 matrix.

## Findings that passed

### Frozen plan and inputs

The runner reconstructs and verifies the frozen roster, card snapshot and manifest, all ten deck
files, and the five accepted runtime files. It independently reproduces 472 print records and 332
Oracle objects. Hash drift is detected before gameplay.

Plan mode does not instantiate `Game`. The deterministic matrix reproduces:

- 45 unordered cross-deck pairings;
- two seeds per pairing, exactly 8001 through 8090;
- canonical and reversed orientation for every seed;
- 180 collision-free distinct game IDs;
- 360 duplicate executions.

The immutable candidate plan digest is
`eae6519c9c75744adee5367ffef68ff6762897829b17774f01c8963b4cae5e04`.

### Duplicate evidence and conformance reconstruction

For every game, the producer retains both complete canonical snapshots, both SHA-256 values, and
an explicit byte-equivalence assertion. Independent result validation recomputes both snapshot
digests and rejects altered duplicate evidence even when outer digests are recomputed.

The validator reruns the accepted Stage #002 reconciliation from the serialized first snapshot.
It therefore reconstructs EXECUTED authentication, opportunity contexts and witnesses,
PRESENT/REACHED/EXECUTED occurrence classification, lineage, stops, and invariants instead of
trusting the report's classification rows. A forged occurrence classification is rejected after
outer digests are recomputed.

The public executor requires the complete matrix. Duplicate executions are recorded as two
executions but produce one distinct-game report, so the data model does not treat 360 executions
as 360 game samples.

### Gameplay isolation and successful artifact mechanics

The smoke module reuses the accepted Game, Pilot, Stage #002 action guards, Priority draining,
combat progression, presence model, and reconciliation. It adds no semantic execution. Ordinary
Stage #002 remains unchanged and reproducible.

Success and failure writes use a temporary file plus atomic replacement. Successful output has an
explicit digest-over-body field and an external whole-file SHA-256 sidecar, avoiding a
self-referential file digest.

### Regression gate

- Full suite: **614 passed / 1 skipped**
- Smoke plus Stage #002 focused suite: **54 passed**
- Ruff check: clean
- Ruff format: 55 files clean
- `git diff --check`: clean

These passing tests do not override the independently reproduced acceptance blockers below.

## Material blocker 1 — balance isolation is not independently enforced

Each game report contains a producer-supplied `future_balance_candidate` object. The independent
validator reconstructs the Stage #002 report fields, but it does not authenticate this additional
smoke field.

The audit changed a coverage-limited game's per-game field to `{"balance_valid": true}`, then
recomputed the aggregate and raw-body digests. `validate_smoke_result()` accepted the forged
artifact.

The aggregate projection check is also incomplete. It rejects a listed coverage-limited game and
rejects `balance_valid: true` in the aggregate candidate list, but it does not prove that:

- every projection member is an exact coverage-complete game;
- the projection is exactly the computed coverage-complete membership;
- every report-level `future_balance_candidate` record has `balance_valid: false`;
- report-level eligibility agrees with the reconstructed label.

Therefore it is not yet structurally impossible for a Smoke 0.1 artifact to claim balance-valid
evidence. This violates the milestone's central governance boundary.

## Material blocker 2 — aggregate mechanical labels are not reconstructive

The validator proves each report's own `mechanical_label` by rerunning reconciliation. It separately
checks that aggregate label memberships contain every game ID exactly once. It does not prove that
an ID appears in the aggregate bucket matching that reconstructed report label.

The audit moved a genuinely `mechanically_clean_coverage_limited` game into the aggregate
`mechanically_clean_coverage_complete` membership, recomputed both outer digests, and independent
validation accepted the artifact.

Thus every game has one aggregate label syntactically, but the label is not yet semantically bound
to its reconstructed per-game classification. This can contaminate later coverage and candidate
selection without altering mature Action evidence.

## Material blocker 3 — frozen-input failures do not serialize atomically

`execute_smoke()` calls `build_smoke_manifest()` before entering its per-game failure boundary. A
frozen hash mismatch raises immediately. No failure artifact or sidecar is written.

The audit changed the expected roster hash in memory and invoked the executor with explicit success
and failure paths. The runner correctly raised `ValueError`, executed no game, and wrote no success
artifact—but the required failure artifact also did not exist.

This is a fail-closed execution result but not a fail-closed evidence result. Frozen-input drift is
an explicit stage stop and must be durably distinguished from a missing run, launcher failure, or
operator interruption.

The same ownership issue affects some post-run validation failures: when both duplicate snapshots
already exist but nondeterminism, reconciliation, or incomplete-game validation then fails, the
generic exception path discards the available snapshot from `last_authoritative_state`. The active
game identity remains preserved, but reconstructive failure state is unnecessarily lost.

## Smallest evidence-backed correction

Do not change gameplay, Actions, Pilot strategy, decks, the Stage #002 evidence model, or the smoke
matrix.

Correct only the smoke evidence layer:

1. Reconstruct exact aggregate label memberships from each independently reconstructed per-game
   label and require membership equality.
2. Reconstruct the exact future-balance-candidate projection from authenticated coverage-complete
   games. Require all aggregate and per-report balance fields to agree, and require
   `balance_valid: false` everywhere in Smoke 0.1.
3. Put frozen manifest/input validation inside an atomic top-level execution failure boundary and
   emit a deterministic pre-game failure artifact identifying manifest construction as the active
   stage, with zero completed games and no accepted aggregate.
4. Where duplicate snapshots already exist, retain their available authoritative state/digests in
   the failure artifact for nondeterminism, incomplete games, or reconciliation failure.
5. Add adversarial regressions that recompute outer digests after each forged label/projection and
   still fail, plus a frozen-input-drift probe that proves an atomic failure artifact is written.

Preserve all passing matrix, duplicate, conformance, frozen-input, and Stage #002 behavior.

## Verdict

**REJECT — duplicate and semantic evidence are substantially reconstructive, but balance-boundary
claims and aggregate mechanical labels can be forged after re-signing outer digests, and frozen-input
drift produces no required atomic failure artifact. Apply only the bounded smoke evidence-layer
correction, then perform Smoke Evidence Runner Acceptance Audit #2.**

Smoke Stage 0.1 remains blocked. Action #14, the historical 900-game smoke, calibration, Pilot or
deck changes, and Prototype 0.3 remain unauthorized.
