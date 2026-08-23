# Coverage-Aware Smoke 0.1 Evidence Runner Acceptance Audit #2

Status: **ACCEPT**

## Audit target and history

- Evidence checkpoint: `102ac018…`
- Rejected runner candidate: `42d31d625637023b04aad2658d096f0611336815`
- Audit #1 REJECT commit: `f0d8855…`
- Audit #1 SHA-256:
  `7c7d82ead1249aa4294f3947ac70c161ca1380614a875e2d2f0f0684d52d8141`
- Corrected immutable candidate: `467b470962354ee82ef412221546a69eddacc410`
- Corrected runner SHA-256:
  `a2d6eb3e079fbf9f7c3f98ec5ed7c81c3e5ae4e736c6830bfaeb341d32d2e2b2`
- Corrected plan digest:
  `fe8a468348460addf7e8d815343e1294b1dfb2ad40b1a747a6a79f83510666e2`
- Candidate CI: **UNCONFIRMED**
- Smoke games executed during this audit: **0**

The corrected candidate is one bounded commit beyond the preserved Audit #1 rejection. Its diff
changes only `src/tmnt_design_studio/smoke01.py` and `tests/test_smoke01_runner.py`. No Engine, Card
Interpreter, conformance, Stage #002, Pilot, Action, deck, matchup, or Prototype behavior changed.

This audit independently reproduced the three rejected attacks with synthetic immutable snapshots.
It did not execute any member of the Smoke Stage 0.1 matrix.

## Re-audit 1 — balance-valid forgery

The audit produced a mechanically clean, coverage-limited synthetic game through the corrected
runner. It then changed the report-level smoke field to `balance_valid: true` and recomputed both
the aggregate digest and raw-artifact-body digest.

Independent validation rejected the re-signed artifact with:

`Smoke per-game balance boundary is not reconstructive`

The corrected contract derives each report's complete balance record from its independently
reconstructed mechanical label. The only accepted value for `balance_valid` is `false`, regardless
of whether the game is coverage-complete or coverage-limited.

The aggregate projection is also derived rather than trusted. Validation reconstructs the exact
coverage-complete membership, constructs the exact permitted projection, and requires equality.
Coverage-limited games are structurally absent, and every projected record still carries
`balance_valid: false` because Smoke 0.1 lacks accepted Pilot and statistical-design gates.

**Audit #1 blocker 1: resolved.**

## Re-audit 2 — aggregate classification substitution

Starting from the same authenticated coverage-limited result, the audit moved the game ID into the
aggregate `mechanically_clean_coverage_complete` bucket, left the per-game evidence intact, and
recomputed both outer digests.

Independent validation rejected the re-signed artifact with:

`Smoke aggregate mechanical labels are not reconstructive`

The validator now rebuilds every game's Stage #002 conformance report from its preserved duplicate
snapshot, recomputes its smoke mechanical label, and constructs the complete aggregate membership
from those labels. The serialized aggregate must equal that reconstruction exactly.

The audit also changed the distinct-game count, re-signed the outer digests, and confirmed rejection
as an inconsistent matrix count. Duplicate executions remain two evidence executions attached to
one distinct-game report; they cannot inflate the 180-game population into 360 game samples.

**Audit #1 blocker 2: resolved.**

## Re-audit 3 — atomic preflight failure evidence

The audit changed the frozen roster hash in memory before manifest construction and invoked the
public executor with fresh success and failure paths. No `Game` was instantiated.

The runner:

- rejected the frozen-input mismatch;
- wrote no success artifact;
- atomically wrote a failure JSON artifact;
- atomically wrote its `.sha256` sidecar;
- recorded stage `manifest_preflight`;
- recorded zero completed games and execution ordinal zero;
- recorded `accepted_aggregate: false` and no manifest digest;
- left no temporary artifact behind.

The audit independently hashed the final failure bytes and matched them to the sidecar. The failure
is therefore distinguishable from a missing launch, interrupted command, or accepted aggregate.

**Audit #1 blocker 3: resolved.**

## Post-duplicate failure path

The audit supplied two deterministic-format snapshots that differed in authoritative turn state.
The runner rejected the duplicate mismatch and wrote only the atomic failure artifact and sidecar.

That artifact permanently preserved:

- the exact active game, pairing, seed, orientation, duplicate member, and execution ordinal;
- zero accepted completed games;
- both genuinely obtained duplicate SHA-256 values;
- distinct digest values proving the mismatch;
- the available last authoritative state fingerprint and phase/step summary;
- `accepted_aggregate: false`.

Passing the failure artifact to success-result validation was rejected because it contains no
manifest/aggregate success structure. It cannot masquerade as completed Smoke evidence.

## Frozen matrix and architecture

Plan reconstruction remains exactly:

- 10 frozen decks;
- 45 unordered pairings;
- two assigned seeds per pairing, 8001–8090;
- canonical and reversed orientation;
- **180 collision-free distinct games**;
- **360 duplicate executions**.

The public executor refuses a matrix whose length is not 180. The manifest retains independent
hash reconstruction for the roster, card snapshot/manifest, decks, accepted runtime, runner, Pilot,
and execution commit. Plan mode does not instantiate a game or consume RNG.

The correction remains an evidence-only layer around accepted Stage #002 primitives. It adds no
card/deck dispatch, semantic execution, gameplay rule, Pilot decision, or matchup behavior.

## Regression gate

- Full suite: **618 passed / 1 skipped**
- Smoke plus Stage #002 focused suite: **58 passed**
- Ruff check: clean
- Ruff format: 55 files clean
- `git diff --check`: clean
- Audit #1 evidence hash: unchanged
- Smoke executions: **0**

## Verdict

**ACCEPT — corrected Coverage-Aware Smoke 0.1 evidence runner resolves all three Audit #1 blockers
and is suitable to bank for the independent Stage 0.1 Readiness Audit #2, subject to exact-SHA CI
confirmation.**

This verdict does not authorize Smoke Stage 0.1 execution. Readiness Audit #2 remains mandatory.
Action #14, the historical 900-game smoke, calibration, Pilot/deck changes, and Prototype 0.3
remain blocked.
