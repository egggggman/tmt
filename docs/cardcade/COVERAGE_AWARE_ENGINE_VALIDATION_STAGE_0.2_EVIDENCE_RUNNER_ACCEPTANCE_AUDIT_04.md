# Coverage-Aware Engine Validation Stage 0.2 Evidence Runner Acceptance Audit #4

## Verdict

**REJECT — the independent execution-commitment architecture closes the substantive
result-body forgery, hidden-zone identity, and phase/step trust-boundary defects from Audits
#1–#3. However, commitment-channel inventory validation is incomplete: an orphan/partial
commitment sidecar can remain in the independently authenticated channel while the Stage 0.2
success artifact still validates.**

No Stage 0.2 game was executed. The frozen five-file candidate was not modified or committed
during this audit.

## Frozen target

- candidate fingerprint: `d20d68e98ecfa9134e28e7bafc75dc6ca5830d52`;
- manifest digest: `1982aa6814f45815633cdc4cfa74c96d38e29a91469b980295ceef58b89a1158`;
- historical rejected candidate: `0771d192e87708accdd433940a75ad104c855b0c`;
- Audit #1: `c3e88173ab94184a9ddb5d21bd1377c1a48d89cdb8cbabe6fd680c79c0e4988c`;
- Audit #2: `04ec8717e566b69840ee81017475a3874bc8e61aac0adf47fe46809b1c6561b4`;
- Audit #3: `9b300091faeeb4523c5276c9eb8ccabdd16186911d40a5e7d51e3afe7bda2323`.

The portable fingerprint and manifest reconstructed exactly from the five Git-clean candidate
identities. The matrix remained 45 pairings / 225 seed assignments / 450 distinct games / 900
executions, with seeds 9001–9225 and duplicate executions retaining distinct-game weight one.

## Independent commitment architecture

The candidate creates one independently atomic JSON artifact and SHA-256 sidecar per execution at:

`<results-filename>.commitments/execution-NNNN.json[.sha256]`

The commitment is written immediately after the authoritative execution snapshot exists and before
duplicate reconciliation or aggregate/result construction. Its canonical body binds execution/game
identity, pairing, seed, orientation, seats, duplicate member, complete canonical snapshot digest,
authoritative preimage digest, reconstructed engine fingerprint, terminal status/winner, turn,
authenticated step, and engine-derived phase. The complete snapshot digest therefore binds ordered
library identities, hand/graveyard identities, battlefield incarnations, Stack and provenance
evidence without exposing those identities to Pilot decisions.

The success and failure bodies retain only a channel description and commitment digests. Editing and
re-signing those bodies cannot replace the independently preserved records. Validation loads and
sidecar-authenticates the external records, reconstructs each expected commitment from its retained
snapshot, and requires exact execution ordinal/member/game identity.

## Closed findings from Audits #1–#3

Independent fixture-based attacks confirmed the intended boundary:

- coordinated mutation of terminal winner, player loss/lethal state, `player_lost`, authoritative
  preimage, claimed fingerprint, both duplicates, reports and outer result digests cannot reproduce
  the original independent snapshot commitment;
- same-count library identity substitution and library reordering fail;
- same-count hand and graveyard identity substitution fail;
- omission, duplication or cross-zone changes either fail the exact snapshot/preimage projection or
  the independent commitment join;
- battlefield incarnation substitution changes the committed canonical snapshot;
- all supported engine steps derive exactly one canonical phase through the engine's `STEP_PHASE`
  relation; an impossible phase/step pair fails even when result-body digests are recomputed;
- commitment omission, duplicate ordering changes, cross-game/member substitution and edits to
  result-body commitment references fail against ordinal sequencing and exact reconstructed records;
- legitimate life-loss, failed-Draw and nonterminal fixture states authenticate;
- inherited `SmokeGameFailure` snapshots are committed when available and preserved in failure
  evidence;
- a forced second-commitment persistence failure retains the first authenticated commitment, removes
  the partial current JSON/sidecar pair and emits an unmistakable failure artifact;
- late aggregate, final serialization, result-write and sidecar-write failures retain completed
  duplicate reports plus commitment references; success cleanup does not delete the commitment
  channel;
- original rules-event, semantic/context/witness, duplicate, balance-firewall and turn-cap contracts
  remain reconstructive.

## Blocking finding — channel inventory ignores orphan partial artifacts

The loader enumerates only `execution-*.json` files. It does not independently inventory every entry
in the commitment directory and require the directory to consist exclusively of the exact expected
JSON/sidecar pairs.

The audit constructed a valid fixture-only two-execution result, verified its two commitment pairs,
then added `execution-0003.json.sha256` with no corresponding `execution-0003.json`. The orphan
contained deliberately invalid partial content. `load_execution_commitments()` continued to return
the original two records and `load_and_validate_result()` accepted the success artifact. The
independently observed probe result was:

```json
{"orphan_exists":true,"orphan_path":"execution-0003.json.sha256","result_validated":true,"valid_commitment_count":2}
```

This violates the frozen Audit #4 requirement that a partially written commitment artifact must
never authenticate. It also leaves ambiguity about whether the channel is the complete execution
ledger or merely the subset of complete JSON files that happened to be discoverable.

This is a commitment-channel evidence defect, not a gameplay, matrix, Action, Pilot, deck,
classification or experiment-specification defect.

## Smallest correction

Keep the independent commitment design and all execution semantics unchanged. Strengthen only the
commitment-channel inventory validator:

1. enumerate every directory entry before accepting any result or failure artifact;
2. derive the exact required filename set from the authenticated commitment ordinals and required
   execution boundary;
3. require exactly one JSON and one `.sha256` sidecar for each required ordinal;
4. reject orphan JSON, orphan sidecar, temporary file, duplicate/alternate filename, unexpected
   entry, missing pair or out-of-range ordinal;
5. retain phase-appropriate failure semantics: an explicitly failed current persistence attempt may
   omit the current pair only after producer cleanup, while every previously committed ordinal must
   still have its exact complete pair;
6. add re-signed success and failure attacks for orphan JSON, orphan sidecar, temp residue, extra
   ordinal, missing partner, reordered/substituted names and unexpected files.

No new digest, gameplay truth model, network service, secret or signing infrastructure is needed.

## Validation reproduced

- focused Stage 0.2 plus inherited Smoke/Stage #002/conformance/Action #16: **193 passed**;
- full repository: **773 passed / 1 skipped**;
- Ruff check: PASS;
- Ruff format check: PASS;
- `git diff --check`: PASS;
- Stage 0.2 games executed: **zero**.

## Gate

- Stage 0.2 Evidence Runner Acceptance Audit #4: **REJECT**;
- Stage 0.2 execution: **BLOCKED**;
- Action #17, balance/calibration, Pilot/deck changes, Design Studio revisions and Prototype 0.3:
  **not authorized**.

Preserve this rejection, apply only the bounded commitment-directory inventory correction, freeze a
new candidate, and submit it for Stage 0.2 Evidence Runner Acceptance Audit #5.
