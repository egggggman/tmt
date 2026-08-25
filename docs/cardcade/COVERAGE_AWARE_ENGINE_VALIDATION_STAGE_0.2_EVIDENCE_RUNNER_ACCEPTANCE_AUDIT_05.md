# Coverage-Aware Engine Validation Stage 0.2 Evidence Runner Acceptance Audit #5

## Verdict

**ACCEPT — the commitment directory is now authenticated as an exact canonical inventory. The
Audit #4 orphan-sidecar defect is closed, and the bounded inventory correction does not reopen the
substantive trust-boundary closures from Audits #1–#3.**

No Stage 0.2 game was executed. The frozen five-file candidate was not modified or committed during
this audit.

## Frozen target

- candidate fingerprint: `c00ed8cf427d5507b28c779bb7cbd45b517822d9`;
- manifest digest: `9a8894750e5d57170398827e66bfb4ac7e289f17d29a88fea5a806eed4a7585a`;
- Audit #1 REJECT: `c3e88173ab94184a9ddb5d21bd1377c1a48d89cdb8cbabe6fd680c79c0e4988c`;
- Audit #2 REJECT: `04ec8717e566b69840ee81017475a3874bc8e61aac0adf47fe46809b1c6561b4`;
- Audit #3 REJECT: `9b300091faeeb4523c5276c9eb8ccabdd16186911d40a5e7d51e3afe7bda2323`;
- Audit #4 REJECT: `d82f17614885932c2ea74deeecf8680fd5eee99b12d050b3729bbd742f8a78bf`.

The portable fingerprint reconstructed from the exact five Git-clean identities. Plan-only manifest
reconstruction produced exactly 45 pairings, 225 pairing/seed assignments, 450 distinct games and
900 executions, with seeds 9001–9225. Plan reconstruction created no Game and consumed no gameplay
RNG.

## Audit #4 blocker reproduced and closed

The Audit #4 attack added `execution-0003.json.sha256` without a corresponding JSON commitment to an
otherwise valid two-execution fixture channel. The corrected loader rejected the directory before
the result could authenticate.

The validator now enumerates every directory entry and compares the actual set against the exact
canonical set derived from recognized four-digit execution JSON names:

- `execution-NNNN.json`;
- `execution-NNNN.json.sha256`.

It then authenticates every file/sidecar pair, commitment body digest, contiguous ordinal sequence,
result-body channel reference and snapshot-derived expected commitment. Nothing outside the exact
pair inventory is ignored.

## Independent inventory attacks

A clean two-execution fixture channel authenticated. Fresh independent copies were then attacked one
at a time. Every altered channel failed closed:

| Attack | Result |
| --- | --- |
| Audit #4 orphan sidecar | Rejected |
| Orphan JSON | Rejected |
| Missing JSON | Rejected |
| Missing sidecar | Rejected |
| Temporary/residue file | Rejected |
| Alternate ordinal encoding | Rejected |
| Alternate filename | Rejected |
| Unexpected regular file | Rejected |
| Unexpected directory | Rejected |
| Fully sidecar-authenticated extra ordinal | Rejected by execution-sequence join |
| Re-signed commitment with substituted game identity | Rejected |
| Sidecar substituted between commitment filenames | Rejected |

The committed regressions additionally cover incomplete pair cleanup. A forced failure while
persisting the second execution removes the partial current pair, retains and authenticates the
first pair, and preserves an unmistakable failure artifact. Late failures retain all prior complete
commitments. Successful result validation retains the independent channel for later Results Audit.

## Audits #1–#3 regression boundary

The correction changes only directory inventory validation and its tests. Independent inspection and
the inherited adversarial suite confirmed that the accepted architecture remains intact:

- the external commitment channel remains outside the re-signable result/failure body;
- coordinated winner, loser/life/lethal state, `player_lost`, preimage, claimed fingerprint,
  duplicate snapshot, report and outer-digest substitutions cannot reproduce the original execution
  commitment;
- ordered library identity and same-count library substitution remain bound;
- hand and graveyard object identities remain bound rather than count-only;
- battlefield incarnation substitutions remain bound by the complete snapshot commitment;
- authenticated step continues to derive phase through the engine's canonical turn structure;
- commitment swaps, omissions, duplicates, reorderings and cross-game/member substitutions fail;
- original rules-event evidence, semantic/context/witness provenance and Trigger/Stack/Priority joins
  remain reconstructive;
- legitimate terminal life-loss, failed-Draw, nonterminal, inherited `SmokeGameFailure`, duplicate
  mismatch, turn-cap and late-failure evidence paths remain valid;
- `balance_valid: false` remains structural for every Stage 0.2 game.

No new gameplay truth model, secret, signature, network service, Action, Pilot decision, deck branch,
card interpretation, matrix rule, seed, classification rule or balance authorization was introduced.

## Canonical identities

- engine: `e98960d0e09b6816befe97c8c0461ae5b46b17bb`;
- interpreter: `ba2f2809bdd64e63c25088635141140c17af8ca6`;
- Pilot: `3eb8bfd8654294e1ef7e6137882651801bf1e2d6`;
- Stage #002: `98248213ab696ef6da2e33ef61f593c1ff9a323a`;
- conformance: `f2fa5e1b3433a749b7b6e1a862a242f4940af1e6`.

## Validation reproduced

- focused Stage 0.2 and inherited Smoke/Stage #002/conformance/Action #16: **204 passed**;
- full repository: **784 passed / 1 skipped**;
- Ruff check: PASS;
- Ruff format check: PASS;
- `git diff --check`: PASS;
- Stage 0.2 games executed: **zero**.

## Decision

**Stage 0.2 Evidence Runner Acceptance Audit #5: ACCEPT.**

The Evidence Runner construction gate is complete. This acceptance authorizes banking and
integration of the accepted runner, exact-head CI, merged-main validation and a final Stage 0.2
readiness audit. It does not itself authorize Stage 0.2 execution, Action #17, balance/calibration,
Pilot/deck changes, Design Studio revisions or Prototype 0.3.
