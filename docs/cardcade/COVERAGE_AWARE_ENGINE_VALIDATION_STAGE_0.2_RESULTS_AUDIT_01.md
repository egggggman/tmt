# Coverage-Aware Engine Validation Stage 0.2 Results Audit #1

## Verdict

**ACCEPT — the frozen Stage 0.2 results reconstruct under the accepted evidence contract.**

Audit date: 2026-08-27. This is an evidence-only results audit, not coverage interpretation,
balance analysis, a runner-construction audit, or authorization for downstream implementation.
Zero games were executed or rerun. No implementation, deck, Pilot, raw result, sidecar, or
independent commitment was changed.

## Frozen target and integrity

Execution baseline: `609765a4886b506dca9cf9776e771cdd6528b763`.

Raw artifact:

`C:\Projects\tmt-evidence-archive\stage02\COVERAGE_AWARE_ENGINE_VALIDATION_STAGE_0.2_RESULTS.json`

The artifact is 1,224,997,062 bytes. Its independently streamed file SHA-256 matches the sidecar
and the frozen execution checkpoint:

`ff8f682b67d80981aac83dcbc4e7dad1ef93f13403a353927f8864f8d7833f96`

The file hash was checked before contents were used and checked again after the first audit
pass. All subsequent adversarial operations used disposable in-memory copies, never archive writes.

Independently reconstructed digests:

| Layer | SHA-256 |
| --- | --- |
| Manifest | `f8a4c531f12f739f8964e31bb52fc9913398869bbe108e0f3695145da0f03449` |
| Aggregate | `fe35ef43648622adf8eb32bc5efa062fae6a3ddc545bf862ae6c4743bda0aa18` |
| Raw artifact body | `5c7d32f9597aae58aac90bc5df7e38a4b1abe7840b9306b7c3e84cafd1f11ea8` |

Canonical JSON was independently serialized with sorted keys, compact separators and UTF-8
without ASCII escaping. Each digest excludes only its own digest field.

## Matrix and frozen inputs

The manifest was rebuilt against the execution baseline and required to equal the serialized
manifest in full. This includes the accepted `smoke-frozen-input-hashing-v2` contract, catalog,
ordered deck membership, frozen input identities, Pilot, runner/launcher, policies and execution
commit. No changed working-tree implementation participated.

Separately enumerating lexicographic combinations of the ten frozen decks, assigning pairing
index i the five seeds 9001 + 5i through 9005 + 5i, and emitting both seat orientations reproduces
every manifest row and every report identity in order:

- 45 unordered pairings;
- 225 unique pairing/seed assignments, seeds 9001–9225;
- 450 distinct games;
- 900 executions, exactly two per distinct game;
- distinct-game weight 1 for each report.

The integrated identities are those accepted by Runner Audit #5 and Readiness Audit #2. In
particular, the later accepted evidence-serialization engine identity is
`e98960d0e09b6816befe97c8c0461ae5b46b17bb`; the older engine identity printed in the original
specification is not silently substituted for the integrated execution identity.

## Independent commitment and terminal authentication

The directory adjacent to the raw artifact, with suffix `.commitments`, contains exactly 1,800
regular files: `execution-0001.json` through `execution-0900.json`, each with its corresponding
`.json.sha256` sidecar. Actual inventory equals the canonical expected inventory. There are no
missing pairs, extra ordinals, orphan sidecars, unexpected files, directories or residue.

All 900 sidecars and commitment-body digests authenticate. Ordinals, game/pairing/seed/orientation,
ordered seats and duplicate-member identities match the expected execution sequence. Every
snapshot digest, authoritative-preimage digest, state fingerprint, terminal flag and terminal
projection matches its independently preserved commitment.

For all 450 games, independently serialized complete first/second snapshots have equal canonical
byte digests, and the complete validator also requires snapshot equality. Both execution digests
are preserved; duplicate executions do not increase the distinct-game count.

The authoritative-state tuple was independently rebuilt from its canonical preimage, including
ordered hidden-zone identities, battlefield identities, life/loss/failed-Draw state, combat,
Stack, turn/step, active player, RNG digest and winner index. SHA-256 of its Python tuple
representation reproduces the engine fingerprint. Terminal winners agree with surviving/lost
player state and the original `player_lost` evidence. All games have a rules-established terminal
result within the accepted turn cap; none is a fabricated turn-cap completion.

The trust boundary is the accepted preserved external commitment channel. This audit does not
claim protection against simultaneous replacement of the entire independent archive and all its
trusted checkpoint hashes, nor does it claim a cryptographic third-party execution signature.

## Semantic evidence and classifications

The complete accepted reconstructive validator passed on the preserved result and independent
commitments. It reconstructs every report from snapshots, authenticates execution references,
runtime-token normalization and lineage, contexts/witness links, original rules-event evidence,
authoritative state and terminal outcomes, then rebuilds the aggregate.

An additional independent pass derived occurrence labels from execution/source-lineage matches
and positive witness membership, checked classification sets, reconstructed mechanical labels,
and rebuilt semantic occurrence/game/pairing/seed/orientation/deck memberships. It reproduced
all union/intersection calculations globally and by pairing, seed, orientation and deck.

| Reconstructed measure | Count |
| --- | ---: |
| Mechanically clean / coverage-complete | 29 |
| Mechanically clean / coverage-limited | 421 |
| Mechanically invalid | 0 |
| EXECUTED occurrences | 539 |
| REACHED / UNSUPPORTED occurrences | 1,482 |
| PRESENT / UNREACHED occurrences | 4,118 |
| Total semantic occurrences | 6,139 |
| Executed references | 5,905 |
| Opportunity contexts | 1,102 |
| Opportunity witnesses | 3,158 |
| Original rules-event ledger records | 17,592 |

Witness causes comprise 1,355 authoritative-context links, 1,560 rules-event links, 46 legal-action
context links and 197 legal-block context links. These counts are per distinct game, not doubled
by duplicate execution. Execution-reference counts are not semantic-occurrence counts.

Every occurrence has exactly one classification. Semantic-key sets may overlap across different
object occurrences without violating occurrence-level exclusivity. All aggregate memberships and
counts match the reconstructed individual records.

All conformance/report stop records and serialized invariant violations are empty: zero runner
stops and zero invariant violations. Every game balance record, aggregate balance record and
aggregate flag has `balance_valid: false`, including all 29 coverage-complete games.

## Adversarial results

Twenty-two disposable-copy probes were rejected. The first nine challenged report labels,
balance eligibility, seed membership, duplicate substitution, false winners, hidden-zone order,
phase, occurrence classification and incomplete terminal state.

The strengthened pass challenged:

| Alteration | Rejection boundary |
| --- | --- |
| Coordinated winner, life/loss state, original loss event, preimage, fingerprint and both duplicates | Preserved independent execution commitment |
| Coordinated ordered-library identity, preimage and fingerprint | Preserved independent execution commitment |
| Historical battlefield characteristics | Original rules-event ledger disagreement |
| Executed source provenance | Reconstructive mechanical/evidence validation |
| Opportunity-context controller | Reconstructive mechanical/evidence validation |
| Witness event linkage | Reconstructive mechanical/evidence validation |
| Same-count hand identity | Authoritative-state projection disagreement |
| Battlefield incarnation | Authoritative-state projection disagreement |
| Aggregate execution count | Per-game aggregate reconstruction |
| Aggregate coverage membership | Per-game aggregate reconstruction |
| Aggregate balance eligibility | Per-game aggregate reconstruction |
| Frozen execution baseline | Frozen manifest reconstruction |
| Result-body commitment reference | Independent channel disagreement |

For the strengthened snapshot attacks, report fields and report-controlled digests were rebuilt
from the altered snapshots wherever reconstruction was possible. Outer checksum checks were
deliberately bypassed, so rejection could not depend on a stale outer checksum. The coordinated
winner and hidden-zone attacks reached the preserved-commitment comparison and failed there.
Aggregate and manifest substitutions were explicitly re-digested before comparison with their
independently reconstructed expected values. No claim is made that a full 1.22 GB forged file was
written for each probe.

## Audit execution and preservation

Two independent local audit scripts completed successfully: the full integrity/arithmetic/
reconstruction pass and the strengthened adversarial pass. Their SHA-256 identities are:

- `audit_stage02_results.py`: `8f593b4b2fea685ebd19db583f9c213ea3f8f206ea8cfcad211c68c85eb95866`;
- `audit_stage02_attacks.py`: `fa824f5c4c0e2211796db5ddbf1a8723b50d07539b16b6ac338b699d98a24748`.

These audit helpers reside outside the repository and are not promoted to production tooling.
The full pytest gameplay suite was not rerun as part of this results-only audit. The accepted
runner's construction/CI validation is historical evidence, not represented as a new audit run.

Tracked implementation and index were unchanged, and `git diff --check` passed before this report.
Git reported an unreadable historical `.pytest-stage02-focused/` directory during an untracked
inventory scan. It was not modified or used; this does not affect frozen tracked inputs or the
external evidence authentication. No assertion of a complete scan inside that directory is made.

## Decision and next gate

**Stage 0.2 Results Audit #1: ACCEPT.** No evidence-backed correction is required.

Bank this report unchanged. The raw JSON, sidecar and all independent commitments remain in the
external evidence archive, outside ordinary Git history.

The next gate is separate Stage 0.2 Coverage/Engine Interpretation. This acceptance does not
interpret residual coverage, rank Actions, assess deck strength, or authorize Action #17,
calibration, Pilot/deck changes, Design Studio revisions or Prototype 0.3. Coverage-complete
continues not to mean balance-valid.
