# Coverage-Aware Engine Validation Stage 0.2 Specification / Readiness Audit #1

## Verdict

**NOT READY — TOOLING — the Stage 0.2 experimental and evidence contract is sound, but the
accepted Smoke 0.1 runner cannot execute it unchanged. A bounded Stage 0.2 evidence-runner
parameterization, complete Stage 0.2 artifact schema, and adversarial runner acceptance audit are
required before another readiness decision.**

The specification does not require correction. No Stage 0.2 game was run during this audit.

## Audited artifact

- specification: `docs/cardcade/COVERAGE_AWARE_ENGINE_VALIDATION_STAGE_0.2_SPEC.md`;
- expected SHA-256: `a623eb13defa0f52a1ecf0e9ca670ae772381a2b27e929e4e57c8b023e866c60`;
- independently reproduced SHA-256:
  `a623eb13defa0f52a1ecf0e9ca670ae772381a2b27e929e4e57c8b023e866c60`.

The specification remained unchanged.

## Matrix reconstruction

The ten deck IDs are lexicographically ordered and produce exactly `C(10, 2) = 45` unordered
cross-deck pairings. Independent application of the specified seed formula produced:

- 45 pairings;
- 225 pairing/seed assignments;
- exactly five seeds for every pairing;
- 225 unique seed values;
- minimum seed `9001`;
- maximum seed `9225`;
- a contiguous `9001–9225` sequence with no omission or reuse;
- two orientations for every pairing/seed assignment;
- 450 generated game identities;
- 450 unique game identities;
- 900 executions after one exact duplicate per distinct game.

The first pairing, `april_oneil--bebop_rocksteady`, receives `9001–9005`. The final pairing,
`shredder--splinter`, receives `9221–9225`. Pairing `i` receives only
`9001 + 5i` through `9005 + 5i`; adjacent pairing ranges do not overlap.

The seed range is disjoint from Smoke 0.1's `8001–8090` range. Reusing a seed number across seat
orientations is intentional because orientation is a separate frozen game dimension; it does not
create a game-ID collision.

The arithmetic is therefore exactly:

`45 pairings × 5 seeds × 2 orientations = 450 distinct games`

`450 distinct games × 2 exact executions = 900 executions`

The specification repeatedly identifies duplicate members as reproducibility evidence and forbids
counting them as independent games or samples. No field in the proposed matrix arithmetic inflates
450 distinct games into 900 games.

## Frozen-input authentication

The specification uses the accepted platform-independent contract:

- version `smoke-frozen-input-hashing-v2`;
- tracked text `git-clean-blob-oid-sha1-v1`;
- binary/non-Git `raw-bytes-sha256-v1`.

Each of the 20 listed tracked inputs was independently required to be tracked by Git and hashed
through explicit Git clean-filter semantics. All 20 reconstructed exactly:

| Input group | Count | Result |
| --- | ---: | --- |
| roster and card-data artifacts | 3 | exact |
| frozen deck manifests | 10 | exact |
| engine/interpreter/Pilot/evidence model | 5 | exact |
| accepted Smoke runner and launcher | 2 | exact |

The catalog/deck requirements match the accepted Smoke contract: 472 print records, 332 unique
Oracle objects, and exact ordered 60-card deck membership. The specification also preserves the
critical boundary that authenticated Git-clean bytes must be the bytes consumed; a dirty working
copy may not execute while a committed blob is authenticated instead.

The current accepted input reconstruction machinery can be reused. A Stage 0.2 runner and launcher
do not yet exist, so their Git identities, execution commit, schema identity, and validation-tool
identity cannot yet be frozen. The specification correctly delegates those identities to readiness
audit after implementation rather than inventing them now.

## Readiness matrix

| Specification requirement | Existing accepted machinery | Missing Stage 0.2 tooling | Independently testable readiness condition |
| --- | --- | --- | --- |
| 45/5/2 matrix and 450 game IDs | Smoke enumerates the same 45 pairings, orientations, and deterministic IDs, but only two seeds and 180 games | Stage 0.2 matrix/stage identity, five-seed formula, 450-game guard, and 900-execution guard | Independently generate all IDs; prove exact ordered membership, collision freedom, seed allocation, and counts |
| Frozen-input reconstruction | Accepted canonical hashing, dirty/missing/untracked rejection, catalog and deck reconstruction | Bind the Stage 0.2 runner/launcher/schema/validator and execution commit into its manifest | Cross-platform LF/CRLF reconstruction; dirty-tree, missing, untracked, wrong-method, and substituted-input attacks fail before game #1 |
| Plan mode | Smoke builds a manifest without creating a game or consuming RNG | Stage 0.2 manifest and plan entry point with the new matrix and artifact contract | Instrument constructors/RNG; plan must emit `authorized: false`, instantiate zero games, and consume zero RNG |
| Complete duplicate snapshots | Smoke serializes full `first` and `second` snapshots, canonical digests, and byte-equivalence | Parameterize for 450 games and ensure Stage 0.2 schema carries all required terminal/original-event fields | Tamper either member and re-sign outer digests; validation must reject; exact duplicates must not increment distinct-game counts |
| Duplicate mismatch detection | Smoke compares complete canonical JSON and stops on mismatch | Stage 0.2 failure identity/counts and complete partial duplicate evidence | Force first/second divergence; preserve obtained member evidence, write failed artifact/sidecar, emit no success artifact |
| EXECUTED authentication | `reconcile_snapshot()` authenticates mature evidence kind/ID, semantic/source identity, fragment, lineage, and transaction records | No new semantic logic; Stage 0.2 runner must serialize and validate the complete accepted evidence | Fabricated ID/kind/source/fragment/transaction and borrowed evidence fail after re-signing outer digests |
| REACHED / PRESENT authentication | Accepted contexts, applicability validator, typed-event witnesses, conservative nonpromotion, and deterministic deduplication | Stage 0.2 schema/validator must retain every referenced context and typed event for the larger artifact | Missing, duplicate, stale, borrowed, impossible, or mismatched context/event fails; dormant unsupported text remains PRESENT |
| Source/incarnation provenance | Accepted object lineage, zone transition, token identity, LKI, frozen controller, and reincarnation checks | Carry all lineage records for both duplicates and validate them at Stage 0.2 scale | Old/new incarnation substitution, relinking, owner/controller/zone mismatch, or borrowed token identity fails |
| Immutable original rules-event evidence | Engine snapshots serialize the independent original ledger; Stage #002 reconciliation includes `rules_event_evidence`; Action #16 audits authenticate downstream joins | Stage 0.2 result validator must explicitly preserve/reconstruct all applicable original-event joins, not merely carry the list | Fully re-sign typed event, trigger, Stack, qualifier, and registries; disagreement with the original ledger must fail |
| Trigger/Stack/Priority joins | Accepted engine snapshots and conformance records preserve trigger IDs, Stack objects, source/controller, events, passes, parent/child boundaries, and terminal guards | Stage 0.2 artifact validation must make these joins mandatory where referenced | Corrupt event→trigger, trigger→Stack, controller/source, parent/child, pass order, or terminal progression and require fail-closed rejection |
| Exactly one mechanical label | Smoke reconstructs labels from authenticated reports and verifies disjoint/exhaustive aggregate memberships | Stage 0.2 count/membership guard for the planned 450-game universe and its invalid/failure boundary | Re-sign altered label/count/membership; reconstruction must reject missing, duplicated, substituted, or multiply classified games |
| Coverage aggregates | Per-game reports contain reconstructive semantic evidence; accepted audits calculate cluster graphs externally | The specification requires deterministic memberships/counts by semantic, game, pairing, seed, orientation, deck, class, and mechanical label; current Smoke success aggregate does not serialize all of these | Recompute every aggregate from individual reports; substituted membership/count must fail even with valid outer digests |
| Balance firewall | Smoke derives per-game `balance_valid: false` inside its balance record and reconstructs aggregate candidates | Stage 0.2 must derive an explicit false value for every one of 450 games and every projection under the new schema | Forge true for a limited or complete game and re-sign; validator must reject and no success artifact may expose a balance-eligible projection |
| 120-turn incomplete-game boundary | Smoke driver stops iteration at turn 120, logs `acceptance_incomplete`, returns no winner, and `_mechanical_label()` rejects it; `execute_smoke()` writes failure evidence | Stage 0.2 schema must identify this as failed/incomplete and preserve the exact active execution without creating an accepted invalid-game aggregate | Run a bounded synthetic nonterminal game to cap; require no fabricated winner/draw, failed artifact/sidecar, no success artifact, and no later execution |
| Terminal-game boundary | Smoke loop exits when `winner` is set; accepted terminal combat/Stack guards prevent continued work | Reuse unchanged; Stage 0.2 regression must ensure the generalized driver does not pad games to 120 turns | Establish a winner before cap; prove no later action, Priority, Stack resolution, turn increment, or duplicate-input mutation occurs |
| Atomic preflight/mid-game failure | Accepted `_atomic_write()` uses temporary files, replacement, and SHA-256 sidecars; Smoke preserves preflight and per-game failures | Stage 0.2 failure schema requires additional explicit status/balance/body/storage fields and complete 450-game identity | Induce preflight and mid-game failures; independently verify artifact and sidecar, diagnostic state, failed status, no accepted aggregate, and clean temporary-file behavior |
| Atomic duplicate/provenance/invariant failure | Smoke catches failures inside each game's duplicate/reconcile block and preserves obtained digests/state | Parameterize execution ordinals/counts for 900 executions and preserve every required context without accepting partial progress | Attack each boundary after one/both duplicates; artifact must remain unmistakably failed and no game may be skipped or retried |
| Atomic final serialization failure | Success JSON/sidecar writing exists, but final aggregate construction and success `_atomic_write()` are not wrapped by a Stage 0.2 failure contract | Bounded outer execution transaction that prevents a partial/plausible success artifact and attempts the predeclared failure artifact when final validation/write fails | Fail aggregate serialization, JSON replacement, and sidecar creation separately; no valid success pair may remain, and the environment write probe must prove failure storage is available |
| Complete success artifact | Smoke writes full reports, duplicates, manifest, mechanical labels, digests, and sidecar | Stage 0.2 schema, 450-game aggregate dimensions, external storage path, size policy, raw-body/file validation, and independent durable validator | Construct a synthetic complete matrix; validate every report/member/aggregate/digest, then re-sign tampering attacks and require rejection |
| Fail on first material defect | Smoke aborts current execution and does not resume partial runs | Stage 0.2 driver must enforce no retry, replacement, continuation, or partial aggregate across all 900 executions | Inject a failure at a known ordinal; prove later runner calls are zero and completed evidence is diagnostic only |

## Prospective evidence assessment

The core conformance model is already implemented and accepted. Existing snapshots expose semantic
presence and occurrences, opportunity contexts, typed events, execution references, source lineage,
original rules-event evidence, triggers, Stack objects, Priority, zones, transactions, and
invariants. `reconcile_snapshot()` and accepted Results Audits demonstrate reconstructive validation
for the represented semantics.

Stage 0.2 does not require a new semantic engine to meet its specification. It does require a new
bounded experiment layer because the accepted Smoke code is intentionally hard-coded to:

- stage ID `coverage-aware-engine-smoke-0.1`;
- two seeds per pairing in `8001–8090`;
- `REQUIRED_GAME_COUNT = 180`;
- 180-game/360-execution manifest assertions;
- Smoke-specific success and failure schemas.

Calling that runner unchanged cannot produce the specified 450-game manifest, Stage 0.2 identities,
aggregate dimensions, or 900-execution gate. Editing only constants would also be insufficient
because Stage 0.2 adds explicit original-event, aggregate, balance, failure-status, body-digest,
external-storage, and final-serialization requirements that must be independently enforced.

## Turn-cap audit

The 120-turn cap is correctly specified as an experiment resource boundary, not a Magic outcome.
If `winner` remains unset at the cap:

- no draw is declared;
- no winner is fabricated;
- the game is not mechanically complete;
- no success classification or aggregate membership is accepted;
- execution stops the entire stage as incomplete/invalid evidence;
- the active game's authoritative state and failure identity are atomically preserved;
- the game is not retried or replaced.

This matches existing accepted driver behavior: iteration occurs only while `winner is None` and
`turn < 120`; cap exhaustion records `acceptance_incomplete`, and mechanical-label reconstruction
rejects a snapshot without a winner. Conversely, a rules-established winner terminates the loop
immediately. The accepted terminal-state guards prevent Priority, Stack, combat, or turn progression
afterward. The runner must not continue a terminal game merely to reach turn 120.

No specification correction is required for this boundary. The Stage 0.2 runner needs explicit
adversarial tests for both cap exhaustion and early terminal completion.

## Failure atomicity audit

The specification correctly requires preflight, mid-game, duplicate, provenance, invariant,
turn-cap, incomplete-game, serialization, and artifact-validation failures to stop the experiment
and preserve diagnostic evidence without producing a valid success artifact.

Accepted Smoke machinery supplies a strong base: atomic temporary-file replacement, sidecars,
preflight failure handling, active execution identity, completed report digests, available duplicate
digests, and last authoritative turn/phase/step/state/Stack/Priority evidence.

It is not sufficient unchanged for Stage 0.2:

- failure records do not currently carry every Stage 0.2 required status/balance/body/storage field;
- the current execution function is hard-coded to Smoke counts and identities;
- final aggregate construction and success serialization are outside the per-game failure wrapper;
- a success JSON write followed by sidecar failure must not leave a plausible accepted artifact;
- Stage 0.2 external evidence paths, capacity, permissions, and atomic-write probe are not frozen;
- the complete Stage 0.2 validator and re-signed tamper suite do not exist.

These are bounded evidence-runner gaps, not flaws in the experiment contract.

## Balance firewall audit

The specification derives `balance_valid: false` for all 450 distinct games, including every
coverage-complete game. It also requires the false value in failure evidence and every future
projection, rejects attempts to promote it, and reserves future promotion for a separate accepted
Pilot review plus a separate predeclared statistical/balance experiment.

The specification explicitly forbids win-rate, matchup-strength, first-player, deck-ranking,
mana-performance, Pilot-performance, calibration, and balance conclusions. Winner and turn may be
retained as terminal engine evidence but cannot cross the balance firewall.

Existing Smoke balance derivation is reusable, but Stage 0.2 must extend and adversarially validate
it over the complete new schema. Coverage completeness alone cannot set any eligibility field true.

## Boundedness judgment

The proposed size is appropriate for the stated engine-validation question:

- it preserves all 45 cross-deck pairings;
- five new deterministic seeds per pairing broaden trajectories without post-result selection;
- both orientations preserve seat-path diversity;
- exact duplicates directly test reproducibility at scale;
- 450 distinct games are 2.5 times Smoke 0.1's distinct-game matrix;
- the 900 executions are operational load and evidence volume, not a balance sample.

The size is substantial but bounded, fully enumerable, and tied to the learning objective. This
audit does not optimize it for statistical balance power and makes no claim that 450 games are
sufficient for balance inference.

## Smallest required correction

Implement a bounded **Coverage-Aware Engine Validation Stage 0.2 evidence runner** that reuses the
accepted Smoke/Stage #002 gameplay and conformance machinery while adding only:

1. Stage 0.2 identity and the exact 45/5/2 matrix;
2. a reconstructed 450-game/900-execution manifest and count guards;
3. Stage 0.2 runner/launcher/schema/validator identities;
4. the complete specified per-game and aggregate serialization, including original-event and
   Trigger/Stack/Priority joins already present in snapshots;
5. explicit derived balance exclusion for every game/projection;
6. complete preflight-through-final-write fail-closed transaction and external artifact policy;
7. an independent durable result validator and adversarial tamper regressions.

Do not fork or weaken the accepted conformance model, alter gameplay, add an Action, or modify decks
or Pilot behavior. Preserve historical Smoke 0.1 reproducibility. Freeze the runner candidate for a
dedicated acceptance audit, then perform Readiness Audit #2 against the complete frozen experiment.

## Authorization boundary

This `NOT READY — TOOLING` verdict authorizes no implementation by itself. It identifies the
smallest bounded work that a subsequent explicit authorization may permit.

The following remain unauthorized:

- Stage 0.2 implementation or execution;
- Action #17;
- balance analysis or calibration;
- Pilot changes;
- deck changes;
- Design Studio revisions;
- Prototype 0.3.

## Final gate

**NOT READY — TOOLING.** The specification is accepted as internally coherent for readiness
purposes, but execution remains blocked until bounded Stage 0.2 evidence tooling is implemented,
independently accepted, integrated, and the complete experiment receives a READY verdict.
