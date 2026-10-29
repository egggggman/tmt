# Fresh 900 frozen-gameplay adapter — draft, not execution authority

## Four-defect correction addendum (supersedes initial boundary assumptions)

The original audited head was `82729fa5e18848110d3ace5fc725223854d4cf79`.
Its five failing independent predicates are preserved byte-for-byte in
`tests/evidence/pr370_independent_adapter.py.txt` (SHA-256
`fc8d0df270e0ed3f82486d2539be5eeb3705f2e290c07a56fafa11553e02b8a3`).
The runnable wrapper changes fixture checkout/commit/platform identities only and
explicitly supplies a test-only mock binding for native/error probes; the executor
substitution predicate always uses the real binding verifier. Predicate bodies,
negative snapshots and assertions are not rewritten. Controlled monkeypatching in
tests is not an execution option in the production API.

Successful native snapshots must now contain every field emitted by the frozen
`Game.snapshot` plus the frozen runner's presence evidence. Structural, terminal,
participant, zone, RNG and authority consistency checks run before reconciliation.
The existing fingerprint tuple is reconstructed from its exposed preimage and
SHA-256 checked; winner/player/turn/stack/RNG disagreements are rejected. Reconciled
identity and authoritative evidence must agree with the unchanged raw snapshot.
This validates serialized evidence, not a newly implemented game/state model.

The adapter authenticates the actual callable's code object against a compile-only
read of fd28 `run_smoke_game`, including module/globals/origin/default/closure
constraints. The verified function reference is pinned and checked before every
dispatch. Mock, wrapper, replaced code/defaults and foreign-origin callables are
refused without invocation. This detects cooperative-process substitution; it is
not an OS sandbox against code able to patch the verifier or its trusted globals.

Gameplay errors are established before attempting snapshot copies. Copy/access
errors are separate cleanup evidence. A copy failure retains the original snapshot
reference where available and reports `REFERENCE_ONLY_COPY_FAILED`; a failed JSON
publication remains a separate error. The initiating cause/type/message survive,
and none of these paths permits completion.

The C: baseline rerun reproduced all five failures. Replacement mock/Windows/Linux
results and exact replacement SHA are recorded in the PR and local
`PR_370_FOUR_DEFECT_CORRECTION_REPORT.md`. CI uses an actual Python 3.13.15 and
resolved interpreter path for original full-identity probes; Linux resource fixtures
read real counters through the existing measurement seam. No interpreter identity,
resource threshold or production Windows provider is falsified or relaxed.

Production authorization independent of a caller-controlled pin, compatible live
monitoring, full gameplay-path resource profiling, #363 integration, Design Studio
confirmation and final execution preflight remain separate gates, not implemented
by this correction. The approved approximately 393 GB budget and memory threshold
remain unchanged. No real game or production checkpoint access is authorized.

Stack: this branch → accepted synthetic PR #369 at
`0b3f9040f3d18a3ab5fd20df310c4abcbad5c665` → draft PR #363 at
`fd28f68915c4e7cb6af3444bf41b96608dee712c` → main.
PR #363 remains unmerged and its current description/candidate document do not
constitute Design Studio promotion or approval to run the candidate. HQ must
resolve its integration and independently confirm Bad Guys 0.2's structural,
card-provenance, legality and simulator-readiness gates. No merge occurred here.

## Binding and persistence

The library-only `fresh900_live.run_authorized_live` maps each authenticated row to
the frozen `stage002.GameSpec`/`DeckSpec`, then calls
`tmnt_design_studio.smoke01.run_smoke_game(root, spec)` with its existing default
Pilot. This is the per-game interface used by the frozen
`tools/run_bad_guys_initial_calibration.py`; its old schedule/persistence launcher
is not invoked. No mechanics, deck list, RNG policy or Pilot is changed.

The candidate file is derived with the frozen launcher's `_candidate_text` and
written only after fresh-root reservation, resource checks and writer acquisition.
The original document remains immutable. Opponent paths come from the authenticated
Baseline 005 manifest. Game ID, pairing ID, seed, orientation and seat identities
are copied exactly and checked; the native RNG seed must match the schedule row.

The frozen `stage002.reconcile_snapshot` processes the complete native snapshot
against deck evidence constructed by its existing `load_catalog` and
`build_deck_manifest` functions. Native fields are retained unchanged. Missing
derived game ID, execution label, invariant and stop-record fields are added only
after checking any supplied values for contradiction. Complete reconciliation
evidence is also retained. Common accepted result validation refuses incomplete,
contradictory, invalid or stopped records before append.

The original synthetic API is still synthetic-only. Its persistence body is shared
as `_run_fresh`; live mode has an explicit separate action and truthful
`synthetic: false` labels. No live result is laundered through a synthetic label.
The existing path guards, full checkpoint writer, eight bounded replacement
attempts, expected-byte/read-back binding, final ordered record authentication and
primary/cleanup error handling remain in that one implementation. No second
checkpoint format, resume path or alternative persistence architecture is added.

The adapter wraps frozen immutable `SmokeGameFailure` exceptions while retaining
the original exception as cause, original type and entire partial snapshot.
The shared failure path writes `failures/game-snapshot.json` when available.
Publication errors are separate cleanup evidence and do not mask the initiating
failure. Interruptions stop for review; occupied roots cannot be reused or replayed.

## Authorization boundary

There is no CLI, automatic startup, default live mode or approval generator.
The caller must explicitly invoke the live library API and supply an authorization
document plus its independently trusted SHA-256 pin. The document must bind the
entire plan and use action `fresh900-live-execution`, identify its external issuer,
and reference independently approved review, Design Studio and preflight records
by SHA-256. Synthetic approvals and wrong/missing pins/actions/gates are refused
before output reservation. Actual Python 3.13.15 is required for this path.

Hashes are references, not proof that governance has happened. A future trusted
issuer/operator must authenticate those records and deliver the pin out of band;
it cannot be taken from the same untrusted plan/checkpoint. This library is not an
OS authorization sandbox against an arbitrary Python caller and does not implement
a cryptographic issuer, ACL deployment or approval-verification service. Existing
frozen entrypoints can already be called by a process with code execution. No
real execution document or trusted pin was issued during this implementation.

Runtime verification checks actual imported module origins/hashes and the entire
approved inventory. The integration source commit must retain fd28 gameplay;
only the known persistence/adapter/preflight files may differ under src/tools.
The committed adapter bytes, its version and its manifest hash must match. A changed
engine/Pilot, unapproved dependency payload or foreign project import fails closed.
The production inventory must include the lazily loaded gameplay/reconciler modules
and candidate-preparation dependencies, not merely preflight-only imports.

## Proposed immutable production manifest — NOT AUTHORIZED

The separately reviewed, final integration head must be frozen before issuing any
real manifest. A report/PR SHA is a proposal until HQ independently approves it.

| Field | Proposed requirement |
| --- | --- |
| Protocol | `fresh900-plan-v1`, 900 games, no resume |
| Runtime source commit | Exact independently reviewed adapter/integration head; re-attest after any integration change |
| Frozen gameplay commit | `fd28f68915c4e7cb6af3444bf41b96608dee712c` |
| Adapter | `fresh900-live-adapter-v1`, exact committed file SHA-256 and integration commit |
| Inputs | All 17 `fresh900_identity.FROZEN_INPUTS` raw identities; no deck changes |
| Candidate | Bad Guys 0.2 document SHA-256 `cacc77648a4d1659b8ae640d95ac2672694e6951553980246e6d001e5152bfb4`; exact derived UTF-8 deck bytes |
| Card snapshot | `56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402` |
| Schedule | `4da440bc83b9790876d1020ae83cf2147c4e60a67feba8bb7181421e196b303e`, seeds 1000000–1000899, 50 games per orientation/opponent |
| Python | CPython 3.13.15 AMD64; exact executable, base executable, standard library and startup settings |
| Dependencies | Frozen `uv.lock` SHA-256 `0c9863fb82c65e8c457b6903b13ab978e1012dc9252e9cca3e95807ef3ded11a`, all 13 wheels/741 payload checks, loaded-module paths/hashes |
| Proposed new run ID | `FRESH_900_BAD_GUYS_0_2_NEXT_HQ_001`; unused status must be checked in final preflight, not reserved now |
| Proposed destination | `G:\cardcade\calibration-runs\FRESH_900_BAD_GUYS_0_2_NEXT_HQ_001`; never Durable 001's directory |
| Protected roots | Historical storage and source checkouts explicitly listed and disjoint |
| Persistence | Same per-game full checkpoints, atomic replacement/read-back validation, single writer, stop/review on any ambiguity |
| Memory gate | Unchanged 2,997,492,240 bytes minimum free physical and commit headroom |
| Authorization | Separate external approval pin binding plan, review, Design Studio and preflight records |

Manifest materialization and pin issuance are not part of this implementation.
Source/interpreter/wheel/import hashes must be independently reverified from a
fresh shell at the final reviewed integration head. No historical interpreter
equivalence exception is implied.

## Mock validation and remaining execution gates

Tests replace the gameplay/reconciliation boundary and use disposable files only.
They cover all 900 parameter mappings without calling a game, complete small mock
checkpoints, malformed native results, missing/wrong authority, interpreter mismatch,
resource and runtime rejection, competing writers, interrupted execution, partial
evidence and immutable frozen failure types. The original four adversarial predicate
files remain unchanged and run alongside these tests.

Mock tests exercise live-protocol labels in disposable fixtures; they are not real
game evidence or an execution permit. The real entrypoint is only imported for
binding checks, never called. CI for `review/fresh900-*` branches runs only the
explicit no-game/mock suite; it cannot fall through to the gameplay-containing
repository suite.

HQ has approved the approximately 393 GB projected full-checkpoint write budget.
The prior 2.533/2.536 GB peaks and 11.8-hour estimate remain synthetic baseline
measurements. The adapter additionally loads card/deck evidence and retains native
and reconciliation evidence; its actual record sizes, catalog/engine allocations,
gameplay transients and full-path peaks have not been measured. The old projection
is not a certified bound on this expanded path; any material budget increase must
be reported before execution. No new memory or throughput claim is made here.

The synthetic-only monitor rejects `synthetic: false` telemetry as UNKNOWN. A
compatible live status observer/handshake must be accepted in final preflight; it
must remain status-only and cannot grant authority or hold checkpoint handles.
No production monitor was changed.

Before any real game: separate-session independent review; #363 integration decision;
Design Studio confirmation; live-adapter acceptance; full gameplay-path memory and
evidence-size assessment under separately approved authority; final Windows/G:
resource, locking, replacement, monitoring and recovery preflight; final immutable
manifest and independently issued execution approval; explicit HQ launch authority.
Do not autonomously advance between those gates.
