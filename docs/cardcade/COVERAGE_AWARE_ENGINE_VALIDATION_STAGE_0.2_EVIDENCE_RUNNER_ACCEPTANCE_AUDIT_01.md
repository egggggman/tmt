# Coverage-Aware Engine Validation Stage 0.2 Evidence Runner Acceptance Audit #1

## Verdict

**REJECT — the matrix, frozen-input, duplicate, semantic-reconciliation, balance-firewall,
external-artifact, and success-write foundations are strong, but terminal-result evidence is not
independently reconstructive and several failure paths discard authoritative diagnostic state.**

No Stage 0.2 game was created or executed during this audit. The three candidate files were not
modified or committed.

## Frozen audit target

- candidate fingerprint: `6b38719c72ed96d5ecbc2d34a6986f50a5f83ae4`;
- manifest digest: `bb92989fda4026b703ffcf72d9057339468836feb0317c6d6fbb41b761178401`;
- accepted specification SHA-256:
  `a623eb13defa0f52a1ecf0e9ca670ae772381a2b27e929e4e57c8b023e866c60`;
- Readiness Audit #1 SHA-256:
  `59c59cabcc2148666a7b0eedb9d8f2d079001392fa917251913592f50b42de4c`;
- repository checkpoint: `0b424287278f0c57bf8f348c8c78644aaae34bc0`.

The candidate fingerprint was independently reconstructed as SHA-1 over the canonical JSON form of
the sorted path-to-Git-clean-blob map. The exact scope and blob identities were:

| Candidate path | Git-clean blob identity |
| --- | --- |
| `scripts/run_coverage_aware_engine_validation_02.py` | `0990c47f3573169c457f6bf7329f1cc803bfeb77` |
| `src/tmnt_design_studio/stage02.py` | `85ffc4d21bea0e055c31f2205f36d4cc37a6dd12` |
| `tests/test_stage02_runner.py` | `bf611691705232c356e7d4a8042ea8f68fc45128` |

No engine, interpreter, Action, Pilot, deck, card-data, or accepted Smoke/Stage #002 file was in the
candidate scope.

## Plan and matrix reconstruction

Plan mode was instrumented so `Game.__init__` and `random.Random.__init__` would fail if called. It
completed without either call. It therefore creates no Game and consumes no gameplay RNG.

Independent reconstruction reproduced:

- 45 unordered pairings;
- 225 unique pairing/seed assignments;
- contiguous unique seeds `9001–9225`;
- exactly five seeds per pairing;
- canonical and reversed orientations for every pairing/seed assignment;
- 450 unique distinct-game identities;
- 900 executions;
- exactly two duplicate members per distinct game.

The first pairing receives `9001–9005`; the final pairing receives `9221–9225`. Candidate validation
compares the complete ordered matrix to an independently regenerated matrix, so a missing,
duplicated, substituted, reordered, cross-pairing, or orientation-altered row cannot be accepted by
merely recomputing manifest or outer result digests.

## Frozen inputs and canonical identities

The manifest reconstructed under `smoke-frozen-input-hashing-v2`. The inherited accepted machinery
hashes tracked text through Git clean-filter semantics, compares working content with fixed expected
identities, rejects dirty/missing/untracked required inputs, and preserves raw-byte sensitivity for
binary/non-Git inputs. Its inherited adversarial regressions passed.

The following identities reconstructed exactly:

- Engine: `1f0bceb95680b37eb4ef9dd6f9eea09ec5aac97e`;
- Interpreter: `ba2f2809bdd64e63c25088635141140c17af8ca6`;
- Pilot: `3eb8bfd8654294e1ef7e6137882651801bf1e2d6`;
- Stage #002: `98248213ab696ef6da2e33ef61f593c1ff9a323a`;
- Conformance: `f2fa5e1b3433a749b7b6e1a862a242f4940af1e6`.

## Accepted portions of the candidate

The following candidate boundaries survived inspection and re-signed attacks:

- complete manifest equality is reconstructed from current authenticated frozen inputs and the
  complete matrix, not trusted from serialized counts;
- both duplicate snapshots and both canonical snapshot digests are retained;
- duplicate membership, byte equivalence, count `2`, and distinct-game weight `1` reconstruct;
- malformed duplicate members cannot emit a success artifact;
- per-game EXECUTED / REACHED / PRESENT classifications are regenerated through accepted
  `reconcile_snapshot()` rather than trusted from producer labels;
- opportunity contexts, typed-event witnesses, transaction evidence, source/incarnation lineage,
  and accepted execution authentication remain delegated to the accepted Stage #002 conformance
  machinery rather than forked;
- the original rules-event evidence list is compared with the serialized rules-event ledger for
  identity, cursor, type, controller/player, subject/source, turn/step, battlefield authority,
  evaluated characteristics, and LKI fields;
- every successful report is rebuilt from its authoritative duplicate snapshots;
- aggregate mechanical memberships, semantic memberships, occurrence counts, coverage dimensions,
  and counts are rebuilt from reconstructed reports;
- `balance_valid: false` is derived per game and in the aggregate; a fully re-signed `true`
  substitution is rejected;
- a nonterminal snapshot at the 120-turn cap fails closed without fabricating a winner or draw;
- output and failure paths inside the repository are rejected by the external-artifact policy;
- final success write failure removes incomplete success JSON/sidecar material and attempts the
  predeclared failure transaction.

The existing re-signed tests rejected altered matrix seeds, duplicate members, mechanical labels,
aggregate memberships, semantic classifications, original-event linkage, balance eligibility, and
frozen inputs. Independent inspection also confirmed that report identity must equal the complete
manifest ordering and that aggregate counts are not independent producer assertions.

## Blocker 1 — terminal result is mutually reconstructive, not independently authenticated

The result validator requires duplicate snapshots to agree and then rebuilds the report and
aggregate from those snapshots. It does not independently authenticate the serialized terminal
`winner` against authoritative terminal evidence.

An independent adversarial probe performed this fully re-signed substitution:

1. produce a valid synthetic completed duplicate pair with winner `0`;
2. change `winner` to `1` in both duplicate snapshots;
3. regenerate both duplicate digests;
4. reconstruct the complete per-game report from the altered snapshots;
5. reconstruct the aggregate and every producer-controlled outer digest;
6. invoke `validate_stage02_result()`.

The forged result was accepted. Duplicate equality proves reproducibility of the substituted claim;
it does not prove that the claimed winner follows from authoritative game-ending state. This fails
the required re-signed terminal winner/state attack and the specification's requirement to preserve
and reconstruct terminal game state.

This does not establish a gameplay defect. It is an evidence-authentication gap in the Stage 0.2
success schema.

## Blocker 2 — inherited mid-game failure state is discarded

The accepted Smoke driver raises `SmokeGameFailure` with an authoritative snapshot when gameplay
stops before returning normally. `execute_stage02()` catches the exception as a generic exception
but never extracts its `snapshot` field. Because assignment into the local duplicate map never
completed, the Stage 0.2 failure artifact contains:

- no available duplicate snapshot;
- no available duplicate digest;
- `last_authoritative_state: null`.

An independent forced `SmokeGameFailure` reproduced exactly that result. The stage was correctly
marked failed and no success artifact remained, but the authoritative state carried by the accepted
driver was lost. This violates the Stage 0.2 requirement that a pre-completion runner/game failure
preserve the last authoritative game state for diagnosis.

## Blocker 3 — post-duplicate failures discard available duplicate evidence

Aggregate reconstruction and final success serialization occur after completed reports already
contain both authoritative snapshots and their digests. Their failure handlers pass no snapshots to
the failure-artifact builder and serialize completed games only as `game_id` plus `report_digest`.

Independent forced final-write failure produced:

- one completed game digest;
- zero available duplicate snapshots;
- zero available duplicate digests;
- `last_authoritative_state: null`.

The same structure applies to aggregate reconstruction failure. It does prevent a partial success
artifact from surviving, but it does not satisfy the explicit requirement to retain available
authoritative duplicate evidence and the last authoritative game state after duplicate state exists.

## Blocker 4 — failure validation does not authenticate diagnostic completeness

`validate_failure_artifact()` authenticates its body digest and five top-level failure/success/balance
flags. It does not require or reconstruct active execution identity, the exception record, completed
report evidence, duplicate snapshots/digests, or last authoritative state.

An independent attack deleted all of those diagnostic fields, recomputed the failure body digest,
and the stripped artifact still passed validation. It could not masquerade as success, but it could
masquerade as a valid Stage 0.2 failure transaction while omitting the evidence the contract requires
for diagnosis.

## Failure-transaction matrix

| Forced boundary | Fail-closed success exclusion | Required diagnostic preservation | Audit result |
| --- | --- | --- | --- |
| Frozen-input manifest reconstruction | Yes | No game state exists; failure JSON/sidecar retained | Pass |
| Mid-game `SmokeGameFailure` | Yes | Carried authoritative snapshot is discarded | **Fail** |
| Post-return invariant/provenance failure | Yes | Both returned snapshots/digests retained | Pass |
| Duplicate mismatch | Yes | Both returned snapshots/digests and last state retained | Pass |
| 120-turn incomplete game | Yes | Both snapshots and cap state retained; no draw/winner fabricated | Pass |
| Aggregate reconstruction | Yes | Completed duplicate snapshots and last state omitted | **Fail** |
| Final success serialization | Yes | Incomplete success pair removed, but completed duplicate state omitted | **Fail** |
| Success JSON/sidecar write failure | Yes | Failure artifact attempted, but completed duplicate state omitted | **Fail** |

The external-artifact policy itself is sound: execution requires success and failure paths outside
the repository, and successful artifacts use authenticated SHA-256 sidecars. The defects above are
about the completeness and authentication of failure evidence, not where it is stored.

## Validation reproduced

- Stage 0.2 plus inherited Smoke/Stage #002/conformance/Action #16 suites:
  `163 passed`;
- full repository suite: `743 passed / 1 skipped`;
- Ruff check: pass;
- Ruff format check: pass (`61 files already formatted`);
- `git diff --check`: pass;
- frozen candidate worktree scope: exactly the three expected candidate files before this report.

The green existing tests do not overturn the adversarial failures because those exact attacks are
not represented by the candidate suite.

## Smallest bounded correction

Do not alter gameplay, Actions, Pilot, decks, the matrix, or the accepted specification. Correct
only the Stage 0.2 evidence layer:

1. bind terminal winner/state to independently reconstructible authoritative terminal evidence and
   make the validator reject a mutually re-signed duplicate winner/state substitution;
2. catch the accepted `SmokeGameFailure` type explicitly and preserve its carried authoritative
   snapshot/digest and last-state projection;
3. for aggregate and final-write failures, retain the completed reports' available authoritative
   duplicate snapshots/digests—at minimum through an authenticated complete diagnostic collection
   plus the final authoritative state, rather than report digests alone;
4. make `validate_failure_artifact()` reconstruct the required active-execution, completed-evidence,
   duplicate-digest, last-state, status, and stage-specific completeness contract;
5. add adversarial regressions for the accepted terminal substitution, stripped/re-signed failure
   evidence, real `SmokeGameFailure` snapshot propagation, aggregate failure, success JSON failure,
   and sidecar failure independently.

The strict duplicate, conformance, original-event, balance, turn-cap, and external-storage boundaries
should remain unchanged.

## Authorization boundary

This audit authorizes no correction or execution. Stage 0.2, Action #17, balance analysis,
calibration, Pilot/deck changes, Design Studio revisions, and Prototype 0.3 remain blocked.

## Final decision

**REJECT.** The runner is close and structurally conservative, but it does not yet satisfy the
complete Stage 0.2 evidence contract under terminal-state substitution and required failure-state
preservation attacks.
