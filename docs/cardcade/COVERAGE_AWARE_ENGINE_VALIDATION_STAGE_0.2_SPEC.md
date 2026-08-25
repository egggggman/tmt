# Coverage-Aware Engine Validation Stage 0.2 Specification

Status: **SPECIFICATION ONLY — IMPLEMENTATION AND EXECUTION NOT AUTHORIZED**

## Purpose

Coverage-Aware Engine Validation Stage 0.2 asks:

> Does Cardcade's accepted represented engine remain deterministic, invariant-clean,
> provenance-authentic, coverage-aware, and fail-closed across substantially broader frozen game
> trajectories?

Stage 0.2 is a bounded engine-validation experiment. It is not a balance experiment, a Pilot
evaluation, calibration, a deck study, or merely another execution of Smoke Stage 0.1.

The stage expands the accepted ten-deck cross-pairing environment from two to five deterministic
seeds per pairing, while preserving exact duplicate execution and the accepted prospective
conformance model. Its learning objective is broader trajectory and interaction coverage: rare
mechanical lifecycle combinations, evidence-system scalability, stability of known semantic
exposure, and discovery of new fail-closed defects or foundational interactions.

Known unsupported semantics are measurements. Their presence does not automatically fail the
mechanical experiment, provided they are positively classified, never silently approximated, and
structurally excluded from stronger claims.

The governing balance rule is:

> **Coverage-complete does not mean balance-valid.**

## Authorization boundary

This document specifies an experiment only. It does not implement a Stage 0.2 runner and does not
authorize a single Stage 0.2 execution.

Before execution, an independent **Stage 0.2 Specification / Readiness Audit #1** must verify the
complete matrix, frozen inputs, evidence contract, runner capability, stop enforcement, artifact
contract, and balance firewall. Any required tooling must be separately implemented, frozen,
adversarially audited, integrated, and validated before another readiness decision.

This specification does not authorize:

- Stage 0.2 implementation or execution;
- Action #17 or another semantic capability;
- balance analysis or calibration;
- Pilot changes or Pilot validation;
- deck changes;
- Design Studio revisions;
- Prototype 0.3;
- revival of the historical 900-game smoke.

## Frozen experiment universe

### Hashing contract

Stage 0.2 reuses the accepted platform-independent frozen-input contract:

- contract version: `smoke-frozen-input-hashing-v2`;
- tracked text: `git-clean-blob-oid-sha1-v1`;
- binary or non-Git input: `raw-bytes-sha256-v1`.

Tracked text identity must be derived through Git clean-filter/object semantics so LF and CRLF
checkout representations authenticate identically. The runner must also reject a dirty working
copy whose consumed bytes differ from the authenticated Git-clean representation. It may not hash
committed content while executing different working-tree content.

Binary inputs remain byte-sensitive. Missing, untracked, substituted, wrongly typed, or
unreconstructable inputs fail closed before game #1.

### Authoritative card data and roster

| Path | Scheme | Frozen identity |
| --- | --- | --- |
| `cardcade/roster-0.2.json` | `git-clean-blob-oid-sha1-v1` | `bad8104fcef826ef5cfd7fec1bdfe921cdd4c306` |
| `cardcade/scryfall-tmt-pza-tmc-2026-08-13.json` | `git-clean-blob-oid-sha1-v1` | `761376d5f932fe6cfbbe140d5c76793c9dd5b169` |
| `cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json` | `git-clean-blob-oid-sha1-v1` | `768d25bbed8392a2f92b7b7f06ae8a34e2602423` |

The catalog must reconstruct exactly 472 print records and 332 unique Oracle objects. Every frozen
deck slot must resolve through this catalog. No alternate card database, inferred errata, or
historical fact table may participate.

### Frozen decks

| Deck ID | Path | Scheme | Frozen identity |
| --- | --- | --- | --- |
| `april_oneil` | `decks/april_oneil/PROTOTYPE_0.1.txt` | Git clean blob | `aa02bd4cd5ce78b182d78d2f4d1b819693e2e033` |
| `bebop_rocksteady` | `decks/bebop_rocksteady/PROTOTYPE_0.1.txt` | Git clean blob | `d12cb8dca2412eb5267496ef3530f9b95e3032a1` |
| `casey_jones` | `decks/casey_jones/PROTOTYPE_0.1.txt` | Git clean blob | `ebcddef99784da507055ff1bac84134e5d355ac6` |
| `donatello` | `decks/donatello/PROTOTYPE_0.2.txt` | Git clean blob | `ec05b95268ba72cd6f0d6b64d9a5dfa1ecd81317` |
| `krang` | `decks/krang/PROTOTYPE_0.2.txt` | Git clean blob | `ecdffa18463076503f5d338687041f42a3a599d9` |
| `leonardo` | `decks/leonardo/PROTOTYPE_0.1.txt` | Git clean blob | `99e082b2cbcc2446159b4a01c3ca9f89d59a2a3e` |
| `michelangelo` | `decks/michelangelo/PROTOTYPE_0.1.txt` | Git clean blob | `70e5104e109405b2ad0a3bdd93e16c5bf75f39e9` |
| `raphael` | `decks/raphael/PROTOTYPE_0.1.txt` | Git clean blob | `964ceb42e13fd0d60fd43346c0b2415bbbe19c30` |
| `shredder` | `decks/shredder/PROTOTYPE_0.1.txt` | Git clean blob | `306fd267482b72f188c69222d57fcc547d654091` |
| `splinter` | `decks/splinter/PROTOTYPE_0.1.txt` | Git clean blob | `354e56cf9dca8e84e8824afe20cd6239d076fd37` |

Each deck must independently reconstruct its exact ordered 60-card membership. No normalization,
reordering, substitution, regeneration, or deck edit is permitted for this stage.

### Accepted runtime, Pilot, and evidence-contract identities

| Role | Path | Scheme | Frozen identity |
| --- | --- | --- | --- |
| engine | `src/tmnt_design_studio/engine07.py` | Git clean blob | `1f0bceb95680b37eb4ef9dd6f9eea09ec5aac97e` |
| interpreter | `src/tmnt_design_studio/card_interpreter07.py` | Git clean blob | `ba2f2809bdd64e63c25088635141140c17af8ca6` |
| Pilot | `src/tmnt_design_studio/pilot07.py` | Git clean blob | `3eb8bfd8654294e1ef7e6137882651801bf1e2d6` |
| Stage #002 evidence model | `src/tmnt_design_studio/stage002.py` | Git clean blob | `98248213ab696ef6da2e33ef61f593c1ff9a323a` |
| conformance model | `src/tmnt_design_studio/conformance07.py` | Git clean blob | `f2fa5e1b3433a749b7b6e1a862a242f4940af1e6` |
| accepted Smoke runner | `src/tmnt_design_studio/smoke01.py` | Git clean blob | `5ab7a5c375b20decbdb65b791d93871cd98abdc6` |
| accepted Smoke launcher | `scripts/run_coverage_aware_smoke_01.py` | Git clean blob | `8f0fd91f7132f8816cd1980beccc029ea498b54c` |

The Pilot identity is `tmnt_design_studio.pilot07.AcceptancePilot`. Freezing it proves deterministic
legal interaction only; it does not validate strategic quality.

These identities define the accepted starting evidence contract. A future Stage 0.2 runner may
reuse or extract generic accepted components, but its own code identity, launcher identity,
execution commit, output schema version, and validation-tool identity must be frozen by readiness
audit. Historical Smoke 0.1 artifacts and the Stage #002 runner must remain reproducible.

No gameplay identity may change merely to implement the Stage 0.2 experiment. Any required engine,
interpreter, Pilot, deck, or semantic change invalidates this specification's frozen execution
universe and requires a new governed checkpoint.

## Frozen matrix

### Pairings

Use every unordered pair of distinct frozen decks exactly once. Deck IDs are sorted
lexicographically:

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

Enumerate combinations lexicographically by first deck and then second deck. This yields exactly
`C(10, 2) = 45` unordered cross-deck pairings. Mirror matches remain excluded.

### Seeds

Number pairings from `i = 0` through `44` in the deterministic order above. Pairing `i` receives
exactly five adjacent seeds:

- `9001 + (5 × i)`;
- `9002 + (5 × i)`;
- `9003 + (5 × i)`;
- `9004 + (5 × i)`;
- `9005 + (5 × i)`.

The complete seed range is therefore `9001–9225`. These seeds are disjoint from Smoke 0.1's
`8001–8090` range. No seed may be selected, removed, retried, or replaced after execution begins.

### Orientations

For every pairing and seed, execute both seat orientations:

- `canonical`: the lexicographically first deck occupies player/seat 0;
- `reversed`: the lexicographically second deck occupies player/seat 0.

### Exact arithmetic

The frozen experiment contains:

- 45 unordered pairings;
- 5 deterministic seeds per pairing;
- 2 seat orientations per seed;
- **450 distinct games**.

Each distinct game must execute twice from fresh engine state:

- exactly 2 executions per distinct game;
- exactly 1 duplicate pair per distinct game;
- **900 total executions**.

The experiment is unambiguously **450 distinct games / 900 executions**. Duplicate executions are
reproducibility evidence. They must never be reported, analyzed, or sampled as independent games.
This arithmetic reuses the historical number 900 without reviving the historical 900-game smoke.

### Game identity

Each game ID must deterministically bind:

- stage ID `coverage-aware-engine-validation-0.2`;
- pairing ID;
- seed;
- orientation;
- ordered seat/deck identities;
- frozen manifest digest.

All 450 IDs must be collision-free. Duplicate members must carry the same game ID plus an explicit
member identity such as `first` and `second`; duplicate identity may not alter gameplay inputs.

### Turn cap

The turn cap remains 120, matching the accepted Smoke driver. A game without a winner before that
cap is incomplete and stops the entire experiment fail closed. It is not silently classified as a
draw or substituted with another seed.

## Plan and manifest contract

Before gameplay, plan mode must reconstruct and serialize a deterministic manifest without
instantiating a `Game` or consuming RNG. It must contain:

- stage/schema/version identity;
- execution commit;
- hashing-contract version and per-input hashing method;
- every frozen path, expected identity, and independently reconstructed identity;
- catalog counts and snapshot identity;
- every deck's ordered membership and digest;
- all participating Oracle objects, faces, fragments, semantic keys, static `SemanticCoverage`
  state, and limitations;
- engine, interpreter, Pilot, conformance, evidence-model, runner, launcher, and validation-tool
  identities;
- the complete ordered 45-pairing/450-game matrix;
- exact seed, orientation, seats, and game ID for each game;
- duplicate policy and execution count;
- turn cap;
- success/failure artifact paths and storage policy;
- canonical manifest digest.

Plan output must explicitly state `authorized: false`. Generating a plan does not authorize
execution.

## Duplicate execution and deterministic evidence

Each duplicate member must begin with identical authenticated inputs: catalog, decks, runtime,
Pilot, runner options, seed, seat order, turn cap, and initial RNG state.

For every distinct game preserve independently:

- complete canonical snapshot for execution `first`;
- complete canonical snapshot for execution `second`;
- canonical-byte SHA-256 of each snapshot;
- explicit byte-equivalence result;
- RNG initial/terminal evidence and chain digest;
- authoritative terminal state fingerprint;
- terminal winner and turn;
- complete per-execution evidence collections.

The validator must compare the complete canonical execution evidence, not only winner, turn, or an
aggregate summary. Any mismatch stops the experiment. The runner may not choose one duplicate,
average them, retry either member, or replace the game.

## Mandatory per-game evidence

Every distinct game report must retain enough serialized evidence to independently reconstruct both
executions and the resulting mechanical/coverage classification.

### Terminal and mechanical state

- stage, game, pairing, seed, orientation, and duplicate-member identity;
- winner, ending turn, phase, step, active player, life totals, and terminal reason;
- complete zones and runtime object/incarnation lineage;
- counters, damage, combat state, Stack, Priority, pending triggers, and pending failed Draw state;
- invariant checks and violations;
- runner/conformance stops;
- legal/rejected action mutation evidence;
- RNG and state fingerprints.

### Semantic presence and occurrences

For every participating object/fragment preserve:

- authoritative card Oracle identity or deterministic runtime-token identity;
- face/fragment index, fragment hash, exact Oracle fragment, and semantic key;
- runtime object/incarnation ID, owner, controller, zone, and complete lineage;
- registration event cursor and authoritative presence facts;
- recognized, executable, fully-supported, and limitations state where applicable;
- every deterministic occurrence ID and exactly one runtime classification.

### EXECUTED

An EXECUTED occurrence requires an authoritative transaction or effect that actually executed. It
must reconstruct against mature typed Action/event evidence by exact evidence kind and ID, source
runtime identity, Oracle fragment, semantic key, transaction ordering, and object lineage.

Opportunity evidence cannot substitute for an executed transaction. Generic telemetry cannot
replace mature Action-specific evidence.

### REACHED / UNSUPPORTED

A REACHED / UNSUPPORTED occurrence requires positive authoritative evidence that a known
unsupported semantic became applicable and Cardcade explicitly did not execute it. The record must
authenticate source applicability and event/state applicability. Unknown applicability remains
PRESENT / UNREACHED.

Mere text registration, card or deck name, battlefield presence, thematic expectation, unrelated
event, or Pilot choice cannot establish reach.

### PRESENT / UNREACHED

The fragment participates in the game, but no authoritative opportunity witness proves
applicability. Library-only or otherwise dormant text remains here. Absence of proof may not be
promoted heuristically.

### Opportunity contexts and typed-event witnesses

Serialize every context and witness required to authenticate REACHED / UNSUPPORTED, including:

- deterministic context/witness/opportunity identity and deduplication key;
- turn, phase, step, source, subject, controller, zones, facts, costs, candidates, targets, and
  choices where represented;
- exact typed event or state boundary causing relevance;
- event cursor/order and immutable event identity;
- Stack/trigger/instruction occurrence linkage where applicable;
- exact Oracle fragment identity and applicability-validator result.

Repeated observation of one opportunity must not inflate counts; distinct opportunities must not
collapse.

### Original immutable rules-event evidence

Where an execution, trigger, opportunity, or historical condition depends on a typed rules event,
preserve the independent original event-evidence anchor and reconstruct every downstream join:

`original event evidence → typed RulesEvent → TriggerInstance/context → Stack ability/transaction`

The anchor must retain event identity/type/cursor, turn/step, battlefield subject/incarnation,
controller, battlefield authority, evaluated historical characteristics, and any qualifying object
facts required by the semantic. Mutually edited downstream registries cannot authenticate history
when they disagree with the original ledger.

### Trigger, Stack, and Priority joins

For every relevant Stack object preserve source incarnation, frozen controller, trigger/event or
spell provenance, Oracle fragment, parent/child resolution boundary, Priority grants/passes, and
resolution/terminal ordering. Child triggers generated during resolution remain pending until the
parent transaction completes. Terminal state prevents post-game Priority or Stack progression.

## Mechanical classification contract

Every distinct game must receive exactly one reconstructed label after duplicate authentication.

### MECHANICALLY CLEAN / COVERAGE-COMPLETE

All conditions hold:

- both executions finish with an authoritative winner before turn 120;
- complete duplicate evidence is byte-identical;
- no runner stop, invariant violation, illegal mutation, malformed lineage, or authentication
  failure occurs;
- every occurrence reconstructs to exactly one accepted runtime class;
- zero REACHED / UNSUPPORTED occurrences remain;
- no reached applicability boundary remains unknown.

PRESENT / UNREACHED text does not alone make a game coverage-limited.

### MECHANICALLY CLEAN / COVERAGE-LIMITED

The game completes deterministically and passes every mechanical/evidence gate, but contains at
least one authenticated REACHED / UNSUPPORTED occurrence.

The represented portions of its trajectory remain legitimate engine-validation evidence. The game
does not prove that unsupported semantics executed correctly, and its outcome is not complete-card
or balance evidence.

### MECHANICALLY INVALID

Any fail-closed condition occurs. The experiment stops immediately and preserves atomic failure
evidence. No partial aggregate is accepted.

Aggregate labels and memberships must be reconstructed from the per-game records. Serialized
producer labels are never authoritative by themselves. Every game must appear once in exactly one
membership, and the three memberships must be disjoint and exhaustive over the planned matrix only
after successful completion.

## Fail-closed gates

Stop the entire experiment immediately on the first occurrence of:

- duplicate mismatch or RNG-chain inconsistency;
- runner exception, runner stop, or explicit conformance stop;
- invariant violation;
- illegal, partial, or silent mutation;
- incomplete game or missing authoritative winner at turn cap;
- frozen-input, execution-commit, Pilot, runner, matrix, or manifest drift;
- malformed, missing, duplicated, stale, borrowed, mismatched, impossible, or unauthenticated
  execution/context/witness/event/trigger/Stack/source/lineage evidence;
- unclassified or multiply classified semantic occurrence;
- classification or aggregate reconstruction failure;
- silent approximation or execution of unsupported semantics;
- failure to authenticate original event evidence where required;
- deterministic identity or deduplication failure;
- evidence serialization, digest, sidecar, atomic-write, storage, or artifact-validation failure;
- any other condition that invalidates the experiment contract.

An authenticated REACHED / UNSUPPORTED occurrence is not itself a stop. It is a primary Stage 0.2
measurement.

No failed game may be skipped, replaced, retried, or resumed. No later game may run after the first
material stop. A correction requires a new frozen baseline and a complete restart from game #1.

## Atomic failure artifact

Before each execution, retain the active game and duplicate-member identity. On any failure,
atomically write a deterministic failure JSON and matching SHA-256 sidecar to predeclared external
evidence storage. The artifact must contain:

- schema/stage and execution baseline;
- complete frozen manifest and digest, or preflight evidence available before manifest completion;
- planned game ID, pairing, seed, orientation, seats, duplicate member, and execution ordinal;
- completed distinct-game/execution counts without treating them as accepted partial results;
- exact stop/exception type, message, traceback where applicable, and failing validation boundary;
- last accepted turn/phase/step and pre-operation state fingerprint;
- current zones, Stack, Priority, pending triggers, winner, and invariant state where serializable;
- all duplicate/per-game digests genuinely obtained before failure;
- explicit `status: failed`, `aggregate_accepted: false`, and `balance_valid: false`;
- artifact-body digest and independently verifiable file sidecar.

Preflight failure before game #1 must still produce this artifact. Failure serialization may not
mutate gameplay, mask the primary failure, or masquerade as a successful Stage result.

## Successful raw artifact

Only after all 900 executions pass every gate may the runner atomically write the complete raw JSON
and SHA-256 sidecar. Preserve the raw artifact outside ordinary Git history if its size approaches
repository-hosting limits.

The successful artifact must contain:

- complete frozen manifest and digest;
- all 450 per-game reports;
- both complete duplicate snapshots/digests and byte-equivalence evidence for every game;
- terminal, RNG, state, invariant, stop, lineage, zone, transaction, event, original-event,
  trigger, Stack, Priority, context, witness, presence, and occurrence evidence;
- exactly one reconstructed mechanical/coverage label per game;
- deterministic membership/count aggregates by semantic, game, pairing, seed, orientation, deck,
  runtime class, and mechanical classification;
- explicit `balance_valid: false` for every game and every future-candidate record;
- manifest, aggregate, raw-body, and file digests.

The raw artifact and sidecar must be frozen before interpretation. No aggregate claim is accepted
until an independent Results Audit reconstructs it from the individual evidence.

## Coverage-analysis boundary

After an accepted Results Audit, Stage 0.2 may measure:

- coverage-complete and coverage-limited counts;
- exact unsupported-fragment clusters;
- occurrence, game, pairing, seed, orientation, matchup, and deck exposure;
- sparse overlap structure and solo/pair counterfactual clearances;
- newly reached versus previously observed semantics;
- accepted Action execution diversity and frequency;
- trajectory sensitivity across the larger seed set;
- stability or change of the current 25-cluster priority graph;
- whether a previously bounded omission becomes foundational under newly reached state.

These are engine and semantic-coverage measurements. They must not be interpreted as deck strength,
matchup quality, first-player advantage, mana performance, strategic competence, or balance.

## Balance firewall

Stage 0.2 derives:

`balance_valid: false`

for **all 450 distinct games**. The field is reconstructed, not trusted from producer serialization,
and any attempt to set it true invalidates the artifact.

Even a mechanically clean / coverage-complete Stage 0.2 game is not automatically balance-valid.
Coverage completeness does not establish:

- complete Magic semantics outside reached represented opportunities;
- strategic Pilot quality;
- a balance-suitable sampling plan;
- matchup independence or representativeness;
- permission to inspect outcomes for design decisions.

Promotion of any future games into balance evidence requires, at minimum, a separately accepted
Pilot review and a separately specified, predeclared statistical/balance experiment. Stage 0.2
cannot satisfy or authorize those gates.

No Stage 0.2 win rate, matchup result, seat effect, ending turn, mana observation, deck rank, or card
performance may drive calibration, deck revision, Design Studio work, or Prototype 0.3.

## Mechanical success criteria

Stage 0.2 succeeds mechanically only if:

- the exact 45-pairing / 450-distinct-game / 900-execution matrix completes from game #1;
- all 450 duplicate pairs are byte-identical and independently reconstructible;
- every game finishes with a winner before turn 120;
- runner stops, unexplained exceptions, invariant violations, illegal mutations, duplicate
  mismatches, and evidence-authentication failures are zero;
- all frozen inputs and the complete manifest reconstruct exactly;
- every semantic occurrence has exactly one authenticated runtime classification;
- every execution and opportunity claim reconstructs from authoritative provenance;
- original rules-event evidence authenticates historical claims where applicable;
- all per-game and aggregate classifications reconstruct exactly;
- success/failure serialization, digests, sidecars, and atomic persistence satisfy the contract;
- broader trajectories complete without a foundational mechanical or evidence defect;
- all 450 games retain `balance_valid: false`.

There is no predetermined required percentage of coverage-complete games and no maximum permitted
count of authenticated REACHED / UNSUPPORTED occurrences. Unsupported semantics discovered by the
stage are measurements, not automatic mechanical failures.

Mechanical success likewise does not require the residual 25-cluster graph to remain unchanged.
New exposure is valuable if it is authenticated and interpreted only after Results Audit.

## Independent readiness requirements

Before execution, Stage 0.2 Specification / Readiness Audit #1 must independently verify at least:

1. this specification's SHA-256 and immutable text;
2. every frozen input identity, hashing method, dirty-tree boundary, catalog count, and deck
   membership;
3. exact lexicographic pairing enumeration and seed formula;
4. exact arithmetic: 45 pairings × 5 seeds × 2 orientations = 450 distinct games, duplicated once
   = 900 executions;
5. collision-free game/member identities and complete manifest membership;
6. plan mode consumes no RNG and instantiates no game;
7. the runner reuses the accepted evidence model without changing gameplay;
8. complete duplicate serialization and byte-level validation;
9. prospective EXECUTED / REACHED / PRESENT authentication, original-event joins, and
   deterministic deduplication;
10. exactly one reconstructed mechanical label per game and reconstructed aggregate membership;
11. structural derivation of `balance_valid: false` for every game;
12. every fail-closed gate is mechanically enforceable;
13. atomic preflight, mid-execution, and post-duplicate failure artifacts plus sidecars;
14. atomic complete success artifact plus external size/storage handling;
15. tamper rejection after outer digests are recomputed;
16. full tests, focused runner/conformance/card-data tests, Ruff, format check, and
   `git diff --check`;
17. no Stage 0.2 game has run during specification, implementation, or readiness work.

The readiness verdict must be exactly one of:

- **READY — the frozen Stage 0.2 experiment is independently auditable and may execute unchanged.**
- **READY WITH CORRECTION — identify the smallest specification or tooling correction required.**
- **NOT READY — identify the evidence/tooling/frozen-input blocker; execute no game.**

An ACCEPT of this specification alone is not execution authorization.

## Required post-stage gates

After a mechanically successful run:

1. preserve raw JSON and sidecar before interpretation;
2. perform an independent Results Audit reconstructing frozen inputs, all 450 duplicate pairs,
   provenance, classifications, contexts, transactions, aggregates, balance exclusion, and artifact
   integrity;
3. only after Results Audit ACCEPT, perform a separate Coverage/Engine Interpretation;
4. keep observations, hypotheses, and recommendations distinct.

The interpretation may recommend, but cannot automatically authorize:

- further bounded Action construction;
- prerequisite infrastructure;
- a bounded engine or evidence correction;
- additional engine validation;
- readiness to begin specifying a separate Pilot/balance-validation gate.

Stage completion authorizes none of those downstream paths by itself.

## Historical 900-game smoke

The historical 900-game smoke remains retired. Stage 0.2 deliberately uses the same numeric scale
only because its predeclared coverage-aware matrix yields 450 distinct games and exact duplication
yields 900 executions.

It is incorrect to call Stage 0.2 a 900-game sample. Its effective distinct-game count is 450, and
even those games remain engine-validation evidence rather than balance samples. Historical output
must not be combined with Stage 0.2 or used for calibration.

## Current gate

**Coverage-Aware Engine Validation Stage 0.2 is specified but BLOCKED.**

Next permitted work is an independent **Stage 0.2 Specification / Readiness Audit #1**. No Stage
0.2 implementation or execution, Action #17, balance analysis, calibration, Pilot/deck change,
Design Studio revision, or Prototype 0.3 is authorized by this specification.
