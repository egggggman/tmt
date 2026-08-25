# Coverage-Aware Engine Validation Stage 0.2 Evidence Runner Acceptance Audit #3

## Verdict

**REJECT — the existing engine fingerprint is now exposed and exactly reconstructible, and the
Audit #2 attacks that leave that commitment unchanged are closed. However, the preimage and claimed
fingerprint remain mutually replaceable inside the same re-signable result. Coordinated replacement
of both, plus all joined mutable projections, is still accepted. Hidden-zone identity and phase
projection attacks expose the same missing independent execution-boundary trust anchor.**

No Stage 0.2 game was executed. The five candidate files were not modified or committed during this
audit.

## Frozen audit target

- candidate fingerprint: `0771d192e87708accdd433940a75ad104c855b0c`;
- manifest digest: `8d5dd1432035875d0c27c966c74b3bd90de60a8f2ec15f3b7bd13bc123089ab9`;
- evidence checkpoint: `7e87595039f8081eba9e5bc34deefb5536464999`;
- Audit #1 SHA-256: `c3e88173ab94184a9ddb5d21bd1377c1a48d89cdb8cbabe6fd680c79c0e4988c`;
- Audit #2 SHA-256: `04ec8717e566b69840ee81017475a3874bc8e61aac0adf47fe46809b1c6561b4`.

The portable fingerprint and manifest digest independently reconstructed exactly. The five-file
scope and Git-clean identities were:

| Path | Git-clean identity |
| --- | --- |
| `scripts/run_coverage_aware_engine_validation_02.py` | `0990c47f3573169c457f6bf7329f1cc803bfeb77` |
| `src/tmnt_design_studio/engine07.py` | `ccd8536387c77e79d0b822615f1a58148bb35bca` |
| `src/tmnt_design_studio/smoke01.py` | `af528c8a01de400cb2bc763f79e83b6791c0242a` |
| `src/tmnt_design_studio/stage02.py` | `1df854a06115dea7f48803409975e5dc3f96e7dc` |
| `tests/test_stage02_runner.py` | `928c99ca535254dc28975910f357f2ed273d6805` |

No Action, interpreter, Pilot, deck, card-data, matrix, or semantic-classification file changed.

## Engine fingerprint compatibility

The engine diff refactors the pre-existing fingerprint expression into one private canonical tuple
producer, hashes that exact tuple as before, and serializes a JSON-compatible representation of the
same tuple. It adds no state transition, legal action, RNG operation, trigger, Priority/Stack action,
SBA, combat rule, card semantic, Pilot decision, or terminal rule.

The old formula and the refactored method were independently evaluated on representative states:

| State | Old formula equals new fingerprint |
| --- | --- |
| Fresh nonterminal game | Yes |
| Terminal life-loss game | Yes |

The serialized representation reconstructs the tuple's ordering and tuple/list distinctions and
reproduces the same SHA-256. This is one representation of the existing authority contract, not a
second gameplay truth model.

## Audit #1 and Audit #2 improvements retained

The candidate continues to close the earlier basic attacks:

- changing only the winner in both duplicates fails against the retained preimage;
- coordinated winner/player/event substitution with the original preimage and commitment unchanged
  fails;
- preimage mutation with the old fingerprint fails;
- preimage plus fingerprint mutation that is inconsistent with retained snapshot projections fails;
- a retained `SmokeGameFailure.snapshot` is propagated with its preimage and commitment;
- substituting only the inherited snapshot/digest/last-state projection fails when its retained
  preimage is unchanged;
- completed late-failure reports are reconstructed from the frozen manifest and retained duplicate
  snapshots through `_report_for()` rather than trusted from their carried `report_digest`;
- stripped semantic, classification, context, witness, duplicate, balance, terminal, or membership
  fields therefore fail completed-report reconstruction;
- early failures remain valid without impossible game evidence;
- late aggregate/final failures preserve completed reports, duplicate snapshots/digests, the last
  authoritative snapshot, and phase/cause;
- atomic success cleanup and the success-versus-failure boundary remain strict.

All 16 accepted historical Stage #002 terminal snapshots continued to authenticate under their
accepted historical terminal-evidence contract.

## Material blocker 1 — hostile preimage and claimed fingerprint can be replaced together

The new validator independently recomputes a fingerprint from the serialized preimage, but both the
preimage and claimed fingerprint live inside each attacker-modifiable duplicate snapshot. The joins
to winner, player loss state, lethal state, and `player_lost` also use fields in the same modifiable
snapshot.

An independent fully re-signed attack changed, in both duplicates:

1. winner A to winner B;
2. player A to the sole lethal-life loser;
3. player B to the surviving player;
4. the `player_lost` event to player A;
5. the preimage player life/lost fields and winner index to the forged outcome;
6. the claimed authoritative-state fingerprint to the hash of the forged preimage;
7. both duplicate digests, the complete report, aggregate, and every producer-controlled outer
   digest.

`validate_stage02_result()` accepted the forged outcome.

The forged preimage is internally canonical and reconstructs its forged claimed fingerprint, but no
independent execution-boundary evidence proves that it is the preimage produced by the original
game. Agreement among preimage, fingerprint, player projection, event projection, duplicate member,
and rebuilt report remains a mutable consensus. This directly fails Audit #3's hostile-preimage
requirement.

The same trust gap applies to an inherited failure if the attacker substitutes the failure snapshot,
its preimage, its claimed fingerprint, digest, and last-state projection together. The current
validator proves internal agreement, not identity with the state crossing the original exception
boundary.

## Material blocker 2 — hidden-zone identities are committed but not independently joined

The fingerprint preimage contains exact library, hand, battlefield, and graveyard object-ID order.
The normal player snapshot exposes exact battlefield IDs, but exposes only library count, hand card
names, and graveyard card names for other zones. Stage 0.2 therefore joins hidden-zone preimages only
by length.

An independent attack replaced one library object ID in both preimages, recomputed both claimed
fingerprints and every report/outer digest, and left the equal library count unchanged.
`validate_stage02_result()` accepted it.

Omission, substitution, duplication, or reordering of hidden-zone identities can consequently become
self-authenticating when the claimed fingerprint is changed with the hostile preimage. The preimage
is complete, but the runner lacks an independent committed source against which to authenticate it.

## Material blocker 3 — phase projection is not joined to authoritative step

The existing engine fingerprint includes `step` and the engine derives `phase` from step. The Stage
0.2 validator compares the preimage step with `snapshot.step` but does not reconstruct and compare
the corresponding phase.

Changing `phase` from combat to ending in both duplicate snapshots while retaining
`end_of_combat`, then rebuilding every report and digest, was accepted. This does not alter the
engine's historical fingerprint formula, but it allows an impossible phase/step projection to enter
authoritative Stage 0.2 evidence.

Fields not included in the existing fingerprint contract—such as counters, damage, tapped state,
Priority, and diagnostic/event collections—were not misrepresented as fingerprint inputs during
this audit. They remain subject to their existing conformance/invariant joins. The rejection rests on
fields that are in the fingerprint contract or deterministically derived from it.

## Completed-report and failure-boundary assessment

The Audit #2 late-report defect is corrected: completed reports are regenerated from retained
duplicates and the retained frozen manifest, including semantic classifications, contexts,
witnesses, execution references, mechanical labels, balance records, terminal result, duplicate
metadata, identity, and `report_digest`. A carried or recomputed stripped report is not trusted.

Phase-appropriate failure preservation also remains coherent:

| Boundary | Assessment |
| --- | --- |
| Preflight/frozen input | Valid without game evidence |
| Mid-game inherited failure | Snapshot/preimage retained; internal reconstruction works, but full coordinated substitution remains possible |
| Invariant/provenance failure | Available duplicates retained and reconstructed |
| Duplicate mismatch | Both available members/digests retained; no success artifact |
| 120-turn incomplete game | No fabricated winner/draw; authoritative state retained |
| Aggregate reconstruction | Completed reports/duplicates and last state retained and reconstructed |
| Final serialization/results write/sidecar write | Partial success removed; completed evidence retained; failed artifact remains distinct |

No later failure path was found to erase already existing evidence, and no early phase was forced to
invent unavailable evidence. The remaining inherited-failure problem is authentication against an
independent boundary commitment, not preservation quantity.

## Prior Stage 0.2 contract

The candidate continues to reconstruct:

- 45 unordered pairings;
- 225 pairing/seed assignments;
- five contiguous unique seeds per pairing, exactly `9001–9225`;
- both seat orientations;
- 450 distinct games;
- 900 executions;
- exactly two duplicate executions per distinct game;
- plan mode with zero Game construction and zero gameplay RNG consumption;
- `smoke-frozen-input-hashing-v2` and frozen-input drift rejection;
- duplicate mismatch detection;
- EXECUTED / REACHED / PRESENT reconstruction;
- opportunity context, typed-event witness, execution transaction, source/incarnation, and original
  rules-event authentication;
- exactly one mechanical label per successful distinct game;
- structural `balance_valid: false`;
- 120-turn incomplete-game fail-closed behavior;
- external large-artifact policy;
- atomic success/failure separation.

The expected identities all reconstructed exactly:

- Engine: `ccd8536387c77e79d0b822615f1a58148bb35bca`;
- Smoke runner: `af528c8a01de400cb2bc763f79e83b6791c0242a`;
- Stage 0.2: `1df854a06115dea7f48803409975e5dc3f96e7dc`;
- Launcher: `0990c47f3573169c457f6bf7329f1cc803bfeb77`;
- Interpreter: `ba2f2809bdd64e63c25088635141140c17af8ca6`;
- Pilot: `3eb8bfd8654294e1ef7e6137882651801bf1e2d6`;
- Stage #002: `98248213ab696ef6da2e33ef61f593c1ff9a323a`;
- Conformance: `f2fa5e1b3433a749b7b6e1a862a242f4940af1e6`.

## Validation reproduced

- focused Stage 0.2 plus inherited Smoke/Stage #002/conformance/Action #16:
  `175 passed`;
- historical Stage #002 terminal corpus: `16/16`, zero authentication failures;
- full repository suite: `755 passed / 1 skipped`;
- Ruff check: pass;
- Ruff format check: pass (`61 files already formatted`);
- `git diff --check`: pass;
- frozen candidate scope remained exactly five files before this report.

Green tests do not overturn the independent hostile-preimage attacks because those exact coordinated
mutations are not present in the candidate suite.

## Smallest bounded correction

Do not change gameplay or the existing fingerprint definition. Add only an evidence-boundary trust
chain and missing deterministic joins:

1. atomically preserve each execution's engine-produced authoritative-state fingerprint commitment
   outside the re-signable aggregate/result body—such as a separately authenticated per-execution
   commitment journal/sidecar established before report construction—and require result/failure
   validation to receive and match that frozen commitment;
2. bind the retained complete preimage and duplicate snapshot to that independent commitment, so
   changing preimage plus claimed in-body fingerprint cannot authenticate without changing the
   separately frozen execution evidence;
3. retain or independently commit the complete hidden-zone object-ID ordering required by the
   fingerprint, rather than joining those identities by count alone;
4. derive phase deterministically from the authenticated step and reject phase/step disagreement;
5. add the exact coordinated hostile-preimage, hidden-zone omission/duplication/reordering, inherited
   failure preimage substitution, and phase/step attacks with all in-body digests recomputed.

Do not add a parallel gameplay model or another digest inside the same mutually mutable artifact.
Preserve the completed-report reconstruction, failure completeness, conformance, matrix, balance,
turn-cap, and external-storage checks already accepted in structure.

## Authorization boundary

This audit authorizes no correction or execution. Stage 0.2 gameplay, Action #17, balance analysis,
calibration, Pilot/deck changes, Design Studio revisions, and Prototype 0.3 remain blocked.

## Final decision

**REJECT.** The pre-existing fingerprint is exposed faithfully and Audit #2's basic attacks are
closed, but the complete Stage 0.2 evidence contract still lacks an independent execution-boundary
commitment capable of authenticating a hostile preimage and its claimed fingerprint.
