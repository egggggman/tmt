# Coverage-Aware Engine Smoke Stage 0.1 Specification

Status: **SPECIFICATION ONLY — EXECUTION NOT AUTHORIZED**

## Purpose

Coverage-Aware Engine Smoke Stage 0.1 asks:

> Does the accepted Cardcade engine remain deterministic, invariant-clean, fail-closed, and
> evidence-authentic across every cross-deck pairing in the frozen ten-deck environment?

The stage measures engine robustness and semantic exposure. It is not calibration, a win-rate
study, a Pilot evaluation, or authorization to revise decks.

The governing rule is:

> **A completed game is not automatically a balance-valid game.**

A game that reaches unsupported semantics remains valuable engine-validation evidence. It must be
classified as coverage-limited and cannot silently enter balance conclusions as though Cardcade
executed the complete cards.

## Authorization boundary

This specification authorizes no execution. Before any smoke game runs, an independent readiness
audit must verify the matrix, hashes, evidence contract, runner capability, stop enforcement, and
artifact determinism.

This specification does not authorize:

- Action #14 or another semantic implementation;
- engine, interpreter, Pilot, runner, or deck behavior changes;
- the historical 900-game smoke;
- balance calibration or Pilot tuning;
- deck or Prototype revisions;
- Prototype 0.3.

## Frozen source universe

### Authoritative data

| Artifact | SHA-256 |
|---|---|
| `cardcade/roster-0.2.json` | `fdbc141b1119227d71dbf0a41a7f3970c1548f6fff1884f1173f9d018b5eb4ed` |
| `cardcade/scryfall-tmt-pza-tmc-2026-08-13.json` | `56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402` |
| `cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json` | `6b5271af75150a361f77e7b89306c709959dfdf497c448dfdc978e5dc9a17950` |

The catalog must independently reproduce 472 print records and 332 unique Oracle objects. Every
deck slot must resolve through the catalog. No alternate card-data source or historical fact table
may participate.

### Frozen decks

| Deck ID | Prototype | SHA-256 |
|---|---|---|
| `leonardo` | `decks/leonardo/PROTOTYPE_0.1.txt` | `d49d155858938d6fc64127c1678e591ee77abad3b7da8302880f16379476fb08` |
| `raphael` | `decks/raphael/PROTOTYPE_0.1.txt` | `07eed928ef6c47aea1f8fb2df2c494d0fae12c10bee8836e7aa9cf2a8784a834` |
| `donatello` | `decks/donatello/PROTOTYPE_0.2.txt` | `8c7ac3bf72e9c8f44e89906567b5fca2c59200f695ba43608c5a91842beb9ce2` |
| `michelangelo` | `decks/michelangelo/PROTOTYPE_0.1.txt` | `f5dd228b6e3636bd0de367b9d1a2bd836c0388bf37b00f0c0c047a932973ebf9` |
| `splinter` | `decks/splinter/PROTOTYPE_0.1.txt` | `74b6d7f4cab4bcda9eeb80ffc7a779529115c98c161345f13ac1251d85163b0a` |
| `april_oneil` | `decks/april_oneil/PROTOTYPE_0.1.txt` | `684c898760a39c5dfc584206ef4675c49d96cfe6bd419f03f86bd0b8358d09f4` |
| `casey_jones` | `decks/casey_jones/PROTOTYPE_0.1.txt` | `0fc0adbb370ecfddad03692a4229a04b23268739914a8f2a004b8e042ff3cebb` |
| `shredder` | `decks/shredder/PROTOTYPE_0.1.txt` | `d0c6479ef2df6d3c64911e8f93465310760f6509282b018fb1c8319cc2c3d6a1` |
| `krang` | `decks/krang/PROTOTYPE_0.2.txt` | `5a52bc59b5de1034721ba17d1c1d4f12c493ec70681c1a910c8230808e4e4f96` |
| `bebop_rocksteady` | `decks/bebop_rocksteady/PROTOTYPE_0.1.txt` | `3875706a76ffab14d2a82ba836da9e59bce49de2f990a348941490e78a61ef9d` |

No deck may be normalized, reordered, regenerated, or edited for this stage.

### Accepted runtime fingerprint

The readiness audit must reproduce these complete-file SHA-256 values before execution:

| Runtime file | SHA-256 |
|---|---|
| `src/tmnt_design_studio/engine07.py` | `501c3af019c0ac123a2589e6652f49931dfff23d86670d7451dcb25369bc4be9` |
| `src/tmnt_design_studio/card_interpreter07.py` | `2407cb6bf72c638036c8d2b7ffbb720f2abe2921fe82696827c88b01449109ab` |
| `src/tmnt_design_studio/pilot07.py` | `8b1365cf58794c9df0045d6aaf8024c5f67dd41dea5bdd80b4f07569adbbc883` |
| `src/tmnt_design_studio/stage002.py` | `c2b17ad738d3dc9fa29fc0c080f86af00e5329d31cad63ac32847be792b75250` |
| `src/tmnt_design_studio/conformance07.py` | `cd3f4ef06c7c423e317978e52abad1ace988f26dcfe2df682c8f1d342727ad29` |

The eventual smoke runner may be a new evidence/tooling file. It may parameterize the accepted
runtime but may not change these files or introduce gameplay behavior. The execution commit SHA
and runner SHA-256 must be frozen by the readiness audit.

## Frozen matrix

### Pairings

Use every unordered pair of distinct frozen decks exactly once as a base pairing.

Deck IDs are sorted lexicographically:

1. `april_oneil`
2. `bebop_rocksteady`
3. `casey_jones`
4. `donatello`
5. `krang`
6. `leonardo`
7. `michelangelo`
8. `raphael`
9. `shredder`
10. `splinter`

Enumerate pairs lexicographically by first deck, then second deck. This yields exactly
`C(10, 2) = 45` base pairings. Mirror matches are excluded because the purpose is cross-deck
interaction diversity, not matchup calibration.

### Seeds

Number the 45 base pairings from zero through 44 in that deterministic order. Pairing index `i`
uses exactly two seeds:

- `8001 + (2 × i)`;
- `8002 + (2 × i)`.

The complete seed range is therefore 8001–8090, with exactly two adjacent seeds assigned to each
pairing. No seed may be substituted after execution begins.

### Orientations

For each pairing and seed, execute both orientations:

- `canonical`: lexicographically first deck in seat/player 0;
- `reversed`: lexicographically second deck in seat/player 0.

### Counts

The exact frozen matrix is:

- 45 base pairings;
- 2 seeds per pairing;
- 2 orientations per seed;
- **180 distinct games**.

Each distinct game is executed twice from a fresh engine instance, producing:

- **360 total executions**;
- exactly one duplicate pair per distinct game;
- duplicates are evidence checks, not additional games or sample size.

## Duplicate and deterministic execution policy

Each execution must begin from identical frozen deck bytes, catalog bytes, runtime bytes, Pilot,
seed, seating, and initial options.

For every distinct game, preserve:

- the complete canonical snapshot from execution A;
- the complete canonical snapshot from execution B;
- SHA-256 of each canonical byte stream;
- explicit byte-equivalence result;
- RNG terminal-state digest for each execution;
- authoritative state fingerprint for each execution.

Any duplicate mismatch stops the entire stage immediately. The runner must not keep the first run,
average differences, retry a seed, or replace a failed execution.

## Static semantic manifest

Before gameplay, the runner must freeze a manifest containing:

- execution commit and complete runtime hashes;
- authoritative card-data and roster hashes;
- every deck hash and resolved 60-card membership;
- every unique participating Oracle object and exact fragment identity;
- static `SemanticCoverage` state and limitations for each fragment;
- exact matrix membership and deterministic game IDs;
- Pilot identity/fingerprint;
- manifest digest.

The manifest must be emitted in plan mode before execution. Plan mode may not instantiate a game or
consume RNG.

## Per-game conformance evidence

Every execution must prospectively classify involved object/fragment occurrences using the
accepted three-way model.

### EXECUTED

An authoritative transaction or effect changed represented game state. The claim must authenticate
against mature typed Action/event evidence by exact evidence kind/ID, source runtime identity,
Oracle fragment, semantic key, and object lineage.

Opportunity witnesses alone cannot prove EXECUTED.

### REACHED / UNSUPPORTED

Authoritative game state reached an opportunity where a known unsupported semantic was relevant,
and Cardcade explicitly did not execute it. The witness must reconstruct source applicability and
event/state applicability from immutable game evidence.

Mere card presence, registration, deck membership, name matching, or thematic assumptions cannot
prove reach.

### PRESENT / UNREACHED

The semantic exists on a participating object, but no authoritative opportunity witness proves it
became relevant. Unknown applicability remains here; it must never be promoted heuristically.

### Required provenance

Each classified record must preserve, as applicable:

- stage/game/seed/orientation identity;
- turn, phase, and step;
- runtime object identity and complete zone lineage;
- owner/controller;
- Oracle ID or authoritative runtime-token identity;
- face/fragment index and fragment hash;
- exact Oracle fragment;
- limitations;
- authoritative transaction, typed event, Stack object, or opportunity-context identity;
- deterministic witness/context key;
- classification.

Multiple observations of one opportunity must deduplicate deterministically; genuinely distinct
opportunities must remain distinct.

## Mechanical game classifications

Every distinct game receives one of these mechanical labels after duplicate authentication.

### MECHANICALLY CLEAN / COVERAGE-COMPLETE

All of the following hold:

- both executions completed with a winner before the frozen turn cap;
- duplicates are byte-identical;
- no runner stop, invariant violation, illegal mutation, malformed lineage, or evidence failure;
- every runtime semantic opportunity is either authenticated EXECUTED or an explicit supported
  legal decline/no-op;
- zero REACHED / UNSUPPORTED occurrences;
- no applicability remains UNKNOWN at a reached decision boundary.

PRESENT / UNREACHED text does not by itself make a game coverage-limited.

### MECHANICALLY CLEAN / COVERAGE-LIMITED

The engine completed deterministically with no mechanical/evidence failure, but one or more exact
REACHED / UNSUPPORTED semantics occurred. The game remains valid engine-conformance evidence. Its
winner, turn length, life totals, and gameplay trajectory are not complete-card or balance evidence.

### MECHANICALLY INVALID

Any fail-closed condition occurs. The stage stops immediately; the failure is preserved and no
aggregate gameplay result is accepted.

## Fail-closed conditions

The runner must stop the complete stage on the first occurrence of:

- engine/runner exception or explicit conformance stop;
- invariant violation;
- illegal or partial mutation during a rejected operation;
- duplicate nondeterminism;
- RNG-chain inconsistency;
- malformed, missing, duplicated, borrowed, or unauthenticated EXECUTED evidence;
- malformed, stale, mismatched, impossible, duplicated, or unauthenticated opportunity context or
  witness;
- semantic reach that cannot be assigned exactly one accepted class;
- source/subject identity, controller, zone, event, Stack, fragment, or lineage mismatch;
- silent execution/approximation of an unsupported semantic;
- deck, card-data, runtime, Pilot, matrix, or manifest hash mismatch;
- turn-cap/incomplete game;
- failure to serialize the complete failure checkpoint.

An explicit REACHED / UNSUPPORTED occurrence is not itself a stop. Measuring such occurrences is a
primary purpose of the stage.

## Failure artifact contract

Unlike early Stage #002 failures, the smoke runner must preserve the active game identity before
each execution begins. On failure, atomically write a deterministic artifact containing:

- frozen manifest digest;
- distinct game ID, pairing, seed, orientation, and duplicate member;
- execution ordinal and completed distinct-game count;
- exact exception/stop kind and traceback where applicable;
- pre-operation authoritative fingerprint;
- last accepted turn/phase/step;
- current Stack/Priority summary where serializable;
- all already completed per-game digests;
- confirmation that no aggregate result was accepted.

Failure serialization must not mutate the engine or attempt a retry.

## Successful raw artifact contract

Only after all 360 executions pass mechanical gates may the runner atomically write the complete
raw result. It must contain:

- frozen manifest and digest;
- all 180 per-game reports;
- both duplicate execution digests and byte-equivalence claims;
- classifications, presences, occurrences, transactions, contexts, witnesses, events, lineage,
  stops, invariants, RNG and state digests;
- per-game mechanical/coverage label;
- exact unions/intersections and counts by game, deck, pairing, orientation, and aggregate;
- raw artifact digest and aggregate digest.

The raw artifact must be banked unchanged before interpretation.

## Reporting and aggregation rules

Report at minimum:

- mechanically clean coverage-complete game count;
- mechanically clean coverage-limited game count;
- exact reached-unsupported semantic membership and occurrence/witness frequency;
- exact executed semantic membership and authenticated transaction frequency;
- present-unreached membership without treating library-only text as runtime coverage;
- games/decks/pairings exposing each semantic;
- distribution of runner stops/invariants (expected zero for acceptance);
- duplicate and RNG determinism;
- winners and turn lengths as descriptive engine outputs only;
- separate results for canonical and reversed orientations;
- comparison with Acceptance #001 and Stage #002 semantic exposure.

Do not aggregate duplicate members as additional games. Do not convert unsupported occurrence
counts into generic engine-failure counts.

## Balance and deck-observation boundary

### Evidence permitted from this smoke stage

The stage may support statements about:

- engine completion and deterministic robustness;
- semantic opportunities and Action execution diversity;
- which pairings expose unsupported mechanics;
- candidate engine capabilities for later review;
- whether additional engine validation is required.

### Evidence not permitted automatically

The stage may not support claims that a deck is too strong/weak, that a matchup is balanced, that a
card should change, or that win rate represents intended gameplay.

A completed game becomes a **future balance-candidate game** only if:

1. it is MECHANICALLY CLEAN / COVERAGE-COMPLETE;
2. its paired duplicate is exact;
3. no reached applicability is unknown;
4. both seat orientations are represented under the frozen matrix;
5. the game completed normally before the turn cap;
6. its Pilot/version and decision policy are separately accepted for the intended balance question;
7. a later, predeclared statistical design includes it without post-result selection.

This smoke stage does not satisfy condition 6 or 7. Therefore **zero games become balance-valid
merely by completing Smoke Stage 0.1**, even if some are tagged as future balance candidates.

Coverage-limited games are categorically excluded from later balance aggregates unless the missing
semantics are implemented and the games are rerun under a newly frozen accepted baseline.

## Acceptance criteria for the smoke execution

The eventual smoke execution passes only if:

- all 180 distinct games / 360 executions complete;
- all duplicate pairs are byte-identical;
- runner stops, invariant violations, illegal mutations, and authentication failures are zero;
- manifest, runtime, decks, card data, Pilot, and matrix match their frozen hashes;
- every involved semantic is classified exactly once at each authoritative occurrence;
- all EXECUTED references and opportunity provenance independently authenticate;
- coverage-complete and coverage-limited games are separated exactly;
- the raw artifact is independently reproduced/audited before interpretation.

There is no maximum allowed number of explicit REACHED / UNSUPPORTED occurrences for engine-smoke
acceptance. Their membership and frequency determine later interpretation, not mechanical pass or
failure.

## Required readiness audit

Before execution, an independent readiness audit must verify:

1. all listed hashes and corpus/deck counts;
2. exact 45 × 2 × 2 = 180 game membership and 360-execution duplicate policy;
3. collision-free deterministic game IDs and seed assignment;
4. plan mode does not instantiate games or consume RNG;
5. the runner changes no gameplay file and reuses accepted engine/Pilot/conformance boundaries;
6. prospective three-way classification and evidence authentication work for the larger matrix;
7. mechanical labels are computed rather than asserted;
8. every fail-closed condition is mechanically enforceable;
9. failure and success artifact writes are deterministic and atomic;
10. coverage-limited games cannot enter future balance-candidate aggregates;
11. full validation, card-data integrity, Ruff, and `git diff --check` pass;
12. no smoke game has run during design/readiness work.

The readiness verdict must be one of:

- **READY — specification and runner are mechanically auditable; execute unchanged.**
- **READY WITH CORRECTION — identify the smallest specification/tooling correction.**
- **NOT READY — identify the blocker; execute no smoke game.**

## Current gate

**Coverage-Aware Engine Smoke Stage 0.1 is specified but remains BLOCKED pending independent
readiness audit and any bounded runner/tooling work that audit authorizes.**

Action #14, the historical 900-game smoke, calibration, Pilot/deck changes, and Prototype 0.3
remain blocked.
