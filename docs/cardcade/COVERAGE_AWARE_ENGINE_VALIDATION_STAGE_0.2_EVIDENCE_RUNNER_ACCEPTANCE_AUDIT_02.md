# Coverage-Aware Engine Validation Stage 0.2 Evidence Runner Acceptance Audit #2

## Verdict

**REJECT — Audit #1's basic winner-substitution, snapshot-loss, late-evidence-loss, and top-level
stripping attacks are corrected, but coordinated terminal-state substitution, inherited-snapshot
substitution, and nested completed-report stripping remain self-authenticating.**

No Stage 0.2 game was created or executed. The corrected three-file candidate was not modified or
committed during this audit.

## Frozen audit target

- corrected candidate fingerprint: `4779853fbdd06dbf439f77f35310d82eabf1cc87`;
- expected manifest digest: `e3ecc53b339f800cd2d1a0fd9a06110ac59d2dc8574861d653b03481eb555fd9`;
- historical rejected candidate: `6b38719c72ed96d5ecbc2d34a6986f50a5f83ae4`;
- Audit #1 REJECT Git-blob SHA-256:
  `c3e88173ab94184a9ddb5d21bd1377c1a48d89cdb8cbabe6fd680c79c0e4988c`;
- repository evidence checkpoint: `8af4dcd9d58e936a89a0fe9af3d8b294c96dc44c`.

The corrected fingerprint independently reconstructed from the canonical sorted path-to-Git-clean-
blob map. The exact candidate scope remained:

| Candidate path | Git-clean blob identity |
| --- | --- |
| `scripts/run_coverage_aware_engine_validation_02.py` | `0990c47f3573169c457f6bf7329f1cc803bfeb77` |
| `src/tmnt_design_studio/stage02.py` | `c2403bc58570f79cb29af3e25b896b99a129ccd9` |
| `tests/test_stage02_runner.py` | `055a5e301cd9a1de906c9d63878b9c38c13b5767` |

The historical Audit #1 report independently reproduced its required SHA-256 unchanged.

## Audit #1 correction status

### Basic terminal-result substitution

The correction no longer trusts duplicate winner agreement alone. It reconstructs a terminal result
from two-player loss state, loss reason, lethal-life or failed-Draw state, and a matching
`player_lost` event.

The following now pass:

- legitimate life-loss terminal result;
- legitimate failed-Draw terminal result;
- changing only the winner consistently in both duplicates, regenerating reports and every outer
  digest, is rejected;
- all 16 accepted historical Stage #002 terminal snapshots authenticate with zero failures.

### Inherited `SmokeGameFailure.snapshot`

The correction explicitly catches `SmokeGameFailure` and retains its carried snapshot under the
active duplicate member. The failure artifact includes its canonical digest, full snapshot, and
last-authoritative-state projection. The prior total loss of inherited evidence is corrected.

### Late-failure evidence retention

Aggregate and final-write failures now retain completed reports, both duplicate snapshots and
digests inside those reports, the final authoritative snapshot, the final-state projection, and the
failure phase/cause. The prior digest-only late-failure record is corrected.

### Phase-aware failure completeness

The failure validator now derives broad requirements from the phase. Early preflight failures remain
valid without impossible game evidence; inherited game failures require an available snapshot; late
aggregate/final failures require completed evidence and a last snapshot. Top-level stripping of the
newly required evidence is rejected after re-signing.

These are material improvements and preserve the prior fail-closed success/failure distinction.

## Remaining blocker 1 — coordinated terminal evidence is still a mutable consensus

The new terminal validator cross-checks `winner` against `players` and `events`, but those three
structures are all mutable fields in the same serialized snapshot. It does not authenticate them
against the engine's independent authoritative-state commitment or a reconstructible authoritative
state preimage.

An independent fully re-signed attack:

1. changed the winner from player A to player B in both duplicate snapshots;
2. changed player A to the sole lost player with lethal life and `life_zero_or_less`;
3. changed player B to the surviving player;
4. relinked the serialized `player_lost` event to player A;
5. regenerated both duplicate digests;
6. reconstructed the complete per-game report and aggregate;
7. recomputed every producer-controlled outer digest.

`validate_stage02_result()` accepted the forged terminal outcome.

The duplicate members were reproducible and the mutable terminal structures agreed, but no
independent authoritative state authenticated that history. This fails Audit #2's explicit
coordinated terminal-evidence attack. The correction has moved beyond winner-only trust, but has not
yet established an independent terminal trust anchor.

## Remaining blocker 2 — an inherited failure snapshot can be substituted

The correction proves that some snapshot is retained, and that its recorded canonical digest and
last-state projection agree with it. Those are all derived from the same mutable serialized
snapshot.

An independent attack changed the inherited snapshot's terminal turn from 120 to 119, regenerated
the available snapshot digest and last-state projection, recomputed the failure body digest, and
passed `validate_failure_artifact()`.

This means the failure transaction prevents stripping but does not authenticate that the retained
snapshot is the exact snapshot carried across the inherited exception boundary. The runner needs an
independent authoritative-state commitment that the validator can reconstruct rather than another
digest computed from the substituted snapshot.

## Remaining blocker 3 — completed late-failure reports are only partially authenticated

`validate_failure_artifact()` authenticates duplicate snapshots and their digests inside each
completed report. It compares the reported `game_id` and `report_digest` with the separate completed
digest list, but does not reconstruct `report_digest` from the report body and does not rerun report
reconciliation.

An independent aggregate-failure attack removed these fields from the retained completed report:

- `occurrences`;
- `classification_sets`;
- `opportunity_contexts`;
- `opportunity_witnesses`.

The asserted `report_digest` was retained, the failure body digest was recomputed, and
`validate_failure_artifact()` accepted the stripped report. Thus the artifact can claim that complete
late-game evidence was preserved while omitting the semantic evidence required by the contract.

This is a narrower nested-completeness gap than Audit #1's top-level stripping defect, but it remains
material for an aggregate or final-write failure after successful execution.

## Prior contract re-audit

The candidate continues to satisfy the previously passing boundaries:

- exact `45 / 225 / 450 / 900` matrix;
- 225 unique contiguous seeds `9001–9225`, five per pairing and both orientations;
- exactly two independently retained duplicate executions per distinct game;
- plan mode instantiates no Game and consumes no gameplay RNG;
- `smoke-frozen-input-hashing-v2` and dirty/missing/untracked/raw-byte fail-closed behavior;
- duplicate mismatch detection and preservation;
- reconstructive mechanical classification and aggregate membership;
- inherited EXECUTED / REACHED / PRESENT, opportunity-context, typed-event, execution-transaction,
  source/incarnation, and original rules-event evidence validation;
- structural `balance_valid: false` derivation;
- 120-turn nonterminal failure without fabricated winner or draw;
- external raw-artifact exclusion from ordinary repository history;
- incomplete success JSON/sidecar cleanup and unambiguous failed-artifact status.

Representative re-signed matrix, duplicate, label, aggregate, semantic, original-event, balance, and
frozen-input attacks continue to fail through independent reconstruction rather than stale outer
checksums. The new corrections did not change gameplay, Actions, Pilot, decks, card data, the matrix,
or semantic classification rules.

## Validation reproduced

- corrected Stage 0.2 plus inherited Smoke/Stage #002/conformance/Action #16 suites:
  `170 passed`;
- historical accepted Stage #002 terminal authentication: `16/16`, zero failures;
- full repository suite: `750 passed / 1 skipped`;
- Ruff check: pass;
- Ruff format check: pass (`61 files already formatted`);
- `git diff --check`: pass;
- candidate scope: exactly the three frozen files before this audit report.

Green repository tests do not overturn the three independent attacks because those coordinated and
nested substitutions are not covered by the candidate suite.

## Smallest bounded correction

Do not change gameplay semantics or the Stage 0.2 experiment. Correct only evidence serialization
and reconstruction:

1. expose the complete preimage required to independently reconstruct the engine's existing
   `authoritative_state_fingerprint` at terminal and inherited-failure boundaries, and verify the
   preimage/fingerprint before trusting winner, player-loss state, event linkage, or a carried
   snapshot; this may require an evidence-only snapshot extension because current serialization
   omits zone object identities used by the engine fingerprint;
2. retain that independently reconstructible authoritative-state commitment across
   `SmokeGameFailure` translation so a substituted snapshot cannot be legitimized by recomputing
   only Stage 0.2 wrapper digests;
3. reconstruct each completed late-failure report's accepted Stage #002 `report_digest` from its
   complete report body, require the complete schema, and preferably rerun report reconciliation
   from its retained duplicate snapshots and frozen manifest before accepting the failure artifact;
4. add exact coordinated terminal, inherited-snapshot substitution, and nested completed-report
   stripping regressions with every wrapper/outer digest recomputed.

Do not add a second mutually mutable terminal assertion or another digest over the substituted
snapshot. Preserve all strict matrix, conformance, balance, duplicate, turn-cap, and artifact-policy
boundaries.

## Authorization boundary

This audit authorizes no correction or execution. Stage 0.2 gameplay, Action #17, balance analysis,
calibration, Pilot/deck changes, Design Studio revisions, and Prototype 0.3 remain blocked.

## Final decision

**REJECT.** All four original blockers improved and their basic attacks are closed, but the complete
Stage 0.2 evidence contract still fails coordinated terminal-state, inherited-snapshot substitution,
and nested late-failure completeness attacks.
