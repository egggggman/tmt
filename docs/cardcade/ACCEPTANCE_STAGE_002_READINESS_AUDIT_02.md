# Acceptance Stage #002 Readiness Re-Audit

Audit baseline: merged `main` `923403cb6ddf8d9fb082501da743c50ae0a5e4a0`
Merged PR: #43 — accepted runtime opportunity-witness instrumentation
Design under audit: `ACCEPTANCE_STAGE_002_DESIGN.md`
Status: **NOT READY**

## Audit integrity

This is an evidence-only readiness re-audit. No Stage #002 game was run. No engine, conformance,
test, Pilot, deck, prototype, gameplay, calibration, or smoke file was modified.

Repository-blob SHA-256 values remain:

- Stage #002 design:
  `d740d532f5e0c61d90b00c479c09100760b6353a23b18bc4621093ded826c624`;
- Stage #002 readiness audit #1:
  `30adad0540d11ef85de0f0a686f98cf401a42e133ec29a89783822c52fb44d97`;
- opportunity-witness Audit #1 REJECT:
  `f5b35809b8ede664599a5e758b5d63d90f1bcde7e854707e3ff49b537b24a384`;
- opportunity-witness Audit #2 ACCEPT:
  `8d24260f4e210d36a7cb7a37b7eb31d0a671aba45b83683dae520fae1520b814`.

PR #43 was squash-merged only after both branch workflows passed and GitHub reported
MERGEABLE/CLEAN. The merge commit and resulting local/remote `main` are
`923403cb6ddf8d9fb082501da743c50ae0a5e4a0`.

## Merged-main validation

- GitHub Actions on merged `main`: **PASS**, run `32543406635`
- Full suite: **509 passed / 1 skipped**
- Runtime conformance suite: **10 passed**
- Card-data integrity: **5 passed**
- Ruff format/check: clean
- Worktree: clean before this report

The accepted prospective Acceptance #001 classification remains:

- **18 unsupported registrations / 6 exact pairs**;
- **11 REACHED / UNSUPPORTED** occurrences;
- **7 PRESENT / UNREACHED** occurrences;
- **18 authoritative opportunity witnesses**;
- zero invariant violations and deterministic duplicate replay;
- unchanged accepted trajectories.

## What the accepted correction resolves

Readiness audit #1 rejected Stage #002 because registration telemetry could not distinguish
generic PRESENT from REACHED. The merged instrumentation establishes a sound, conservative path
for the bounded applicability shapes it recognizes:

1. self-ETB triggers joined to the source's authoritative creature-entry event;
2. Alliance triggers joined to a later qualifying controlled-creature entry while the source is
   authoritative;
3. attack triggers joined to authoritative attacker declaration;
4. represented graveyard-casting permissions joined to a qualifying main-phase graveyard option;
5. Menace relevance joined to an authoritative block-candidate context.

The shared validator is applied at witness creation and by invariants. Typed events freeze
battlefield/controller authority, and Audit #2 proves stale Alliance sources and unrelated event
types cannot authenticate reach. Existing Action evidence remains authoritative for EXECUTED.

This is a material readiness improvement. It closes the exact evidence defect demonstrated by
Acceptance #001 and provides the correct conservative behavior when proof is absent.

## Remaining Stage #002 mismatch

The unchanged Stage #002 design has a stronger universal gate: **every unsupported actionable
occurrence must be explicit and tied to an opportunity witness**, and silent approximation or an
unclassified reached opportunity must stop the stage. The accepted instrumentation does not yet
produce opportunity witnesses for several semantic boundaries intentionally concentrated by the
four pairings.

### Donatello vs. Krang

Witnessable today: self-ETB/Alliance/attack shapes if exact supported witness grammar matches, plus
core EXECUTED evidence.

Not prospectively witnessable: generic artifact-entry triggers, Affinity/cost-reduction
applicability, artifact-count characteristic evaluation opportunities, unsupported sacrifice
activations, Cycling, counterspell opportunities, token-copy predicates, and compound Draw. This
pairing remains dominated by precisely the unsupported artifact contexts the design wants to
measure. Registration alone cannot say whether they were reached.

### Michelangelo vs. Bebop & Rocksteady

Witnessable today: represented attack triggers, exact self-ETB/Alliance shapes, Menace block
contexts, and mature Trample/Sneak execution evidence where reached.

Not prospectively witnessable: generic leaves-battlefield triggers, variable token quantities,
token replacement predicates, unsupported Food/Mutagen activation opportunities, sacrifice-or-
discard cost/choice availability, and compound follow-up reach. Static presence cannot determine
which of these mattered during a game.

### Splinter vs. Shredder

Witnessable today: attack, exact ETB, Menace block, and mature Sneak/strike/Lifelink evidence. This
remains the strongest pairing for represented execution.

Not prospectively witnessable: generic permanent-departure triggers, Disappear or other
unsupported token-delivery predicates, unsupported activated/cost contexts, and compound
Draw/life-loss instruction reach. A departure can occur without the current conformance layer
classifying the associated unsupported semantic as reached.

### April O'Neil vs. Casey Jones

Witnessable today: Casey's exact self-ETB filter opportunity, represented attack triggers, and
mature Deal Damage/filter/Draw/discard/strike/Trample evidence.

Not prospectively witnessable: unsupported counterspell response opportunities, Cycling,
Equipment/equip activation, artifact-copy or artifact-leaves contexts, broader target/choice
availability, and unsupported sequential-instruction boundaries. These are primary negative
targets of this pairing, not incidental text.

## Major-system readiness matrix

Legend: **R** = bounded prospective REACHED witness exists; **E** = mature EXECUTED evidence exists;
**P** = presence only for important Stage #002 semantics; **—** = not a targeted exposure.

| Pairing | Core engine | ETB/Alliance/attack | Menace block | Graveyard permission | Unsupported activations/costs | Departure/replacement | Artifact dependency | Target/choice/compound |
| --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Donatello / Krang | E | R/P | — | — | P | P | P | P |
| Michelangelo / Bebop & Rocksteady | E | R/P | R | — | P | P | — | P |
| Splinter / Shredder | E | R/P | R | — | P | P | — | P |
| April / Casey | E | R/E | R | — | P | P | P | P/E |

The matrix shows that the games would still be useful, but usefulness is not readiness under the
design's stated pass contract. Important targeted semantics could become relevant while remaining
classified PRESENT / UNREACHED solely because no corresponding opportunity producer exists.

## Stop-condition re-evaluation

| Stop condition | Merged mechanical status |
| --- | --- |
| Invariant violation | **Enforceable.** Existing engine and conformance invariants fail malformed state/evidence. |
| Nondeterminism | **Enforceable.** Duplicate canonical artifacts and RNG ledgers can be compared. |
| Illegal mutation | **Foundation available, runner integration missing.** `authoritative_state_fingerprint()` supplies a normalized boundary, but no Stage #002 runner yet records a canonical stop result around every rejected action. |
| Silent approximation | **Enforceable only for the five bounded witness shapes.** It is not enforceable for the important unwitnessed Stage #002 contexts listed above. |

The accepted instrumentation therefore removes the broad architectural uncertainty but does not
yet satisfy the Stage-specific universal silent-approximation gate.

## Runtime class readiness

- **EXECUTED:** ready where mature Action/engine evidence carries exact identity and result; no
  opportunity witness is allowed to manufacture this class.
- **REACHED / UNSUPPORTED:** ready for the five audited applicability shapes; not ready for the
  Stage #002 activation, departure, replacement, artifact-dependency, response, and compound
  contexts above.
- **PRESENT / UNREACHED:** deterministic and conservative, but currently conflates genuinely
  unreached text with reached contexts for which no producer exists. That ambiguity is acceptable
  for Acceptance #001's audited scope and unacceptable for Stage #002's universal gate.

## Smallest readiness correction

Do not alter the four pairings, decks, Pilot, or gameplay. Before executing Stage #002, add one
bounded evidence-only instrumentation checkpoint driven by the frozen static inventories:

1. enumerate every unsupported exact fragment in the 16-game Stage semantic universe and map it to
   either an existing witness producer or an explicit `opportunity_not_observable` readiness error;
2. add only the missing generic opportunity producers required by that universe: unsupported
   activation/cost availability, typed permanent departure, represented replacement evaluation,
   artifact-entry/count predicates, response/counterspell timing, target/choice availability, and
   sequential-instruction reach;
3. apply the same creation/invariant provenance validation and deterministic deduplication contract;
4. add the parameterized runner's canonical illegal-mutation and unclassified-reach stop records;
5. re-audit focused synthetic fixtures before authorizing any of the 16 games.

This is evidence architecture, not Action #13 and not permission to execute the unsupported
semantics. If the project instead narrows the design gate to the five currently witnessable shapes,
that would be a material design change and requires an explicit governance decision; it must not be
assumed during execution.

## Verdict

**NOT READY — accepted opportunity instrumentation makes Acceptance #001 prospectively trustworthy, but Stage #002 still targets actionable unsupported activation, departure, replacement, artifact-dependency, response, target/choice, and compound contexts that cannot yet produce authoritative witnesses; complete the bounded Stage-specific evidence layer before running the 16-game matrix.**
