# Cardcade Engine Validation Milestone Review #2

## Verdict

**CONDITIONAL ADVANCE — Cardcade is mechanically credible and coverage-aware enough to advance to
a larger bounded engine-validation stage despite known unsupported semantics. Isolated targeted
Action construction should no longer be the automatic critical path.**

The condition is strict experiment governance. The next stage must retain deterministic duplicates,
authenticated EXECUTED / REACHED / PRESENT evidence, immediate fail-closed stops, independently
reconstructable frozen inputs, and structural exclusion from balance claims.

This review does not authorize execution of that stage. It authorizes only its specification and an
independent readiness audit. It does not authorize Action #17, calibration, Pilot or deck changes,
Design Studio revisions, Prototype 0.3, or balance analysis.

## Central question

> Is Cardcade now sufficiently mechanically credible and coverage-aware to advance to a larger
> bounded engine-validation stage even though most games still reach unsupported semantics?

**Yes, conditionally.** Mechanical credibility is supported by deterministic, invariant-clean,
reconstructive evidence across the complete frozen ten-deck matrix and several successive semantic
versions. The remaining limitations materially constrain game fidelity, but they are explicitly
classified and excluded rather than silently approximated. Low coverage completeness therefore
limits what conclusions may be drawn; it does not invalidate the represented engine transactions.

## Evidence reviewed

This review covers the complete progression since the previous Engine Validation Milestone Review's
CONDITIONAL PASS:

1. Coverage-Aware Engine Smoke Stage 0.1 specification, runner, adversarial runner audits,
   cross-platform canonical-input correction, and readiness audits;
2. repeated fail-closed execution checkpoints and independently audited engine/runner corrections;
3. the accepted baseline 45-pairing, 180-game, 360-execution Smoke artifact;
4. accepted evidence interpretation and Actions #14, #15, and #16;
5. each Action's rejection history, corrected acceptance, merged-main validation, full coverage
   remeasurement, independent Results Audit, and delta interpretation;
6. unchanged Acceptance #001 deterministic trajectories throughout the Action program.

The four accepted full-matrix measurements contain 720 distinct deterministic game reports and
1,440 total executions across successive frozen engine checkpoints. These are repeated versions of
one fixed matrix, not 720 statistically independent balance samples. They are strong regression and
engine-validation evidence only.

## Mechanical credibility

### Deterministic duplicate execution

The accepted baseline Smoke and all three post-Action remeasurements preserve the exact
`45 pairings / 180 distinct games / 360 executions` contract. Every accepted run has 180/180
byte-identical duplicate pairs. Complete canonical snapshots, duplicate digests, RNG terminal-state
evidence, per-game reports, and aggregate memberships reconstruct independently.

Acceptance #001 seeds 7001–7005 also remain byte-identical across Actions #14–#16, with unchanged
Raphael T14, Raphael T18, Leonardo T19, Leonardo T43, and Raphael T16 trajectories.

**Judgment: credible.** No accepted evidence contains unexplained nondeterminism.

### Runner stops and invariant violations

All accepted 180-game artifacts report:

- zero mechanically invalid games;
- zero runner stops;
- zero invariant violations;
- zero duplicate mismatches.

Earlier Smoke attempts did stop on real lifecycle defects: semantic registration after lost runtime
authority, ETB event-cursor disagreement, terminal-combat progression, and runner combat/Priority
coordination. Those partial runs were rejected as aggregate evidence, preserved as failures, and
restarted from game #1 only after bounded corrections passed independent audits and merged-main
validation.

**Judgment: credible.** Clean accepted runs do not erase the failure history; the history demonstrates
that the stop system detects real defects before producing plausible success artifacts.

### Fail-closed behavior

The evidence pipeline has stopped on stale identities, malformed provenance, inappropriate event
joins, unresolved Stack work, duplicate combat resolution, terminal-state progression, token
identity mismatch, and frozen-input portability drift. Atomic failure artifacts and sidecars were
independently tested and then exercised in real failures.

Rejected candidates were preserved rather than retrospectively relabeled. No failed partial Smoke
was resumed or counted toward a completed aggregate.

**Judgment: strong.** Fail-closed behavior is an observed engine-validation property, not merely a
test assertion.

### Provenance and authentication integrity

The accepted evidence chain authenticates execution references by exact evidence kind/ID, source
runtime identity, Oracle fragment, semantic key, and object lineage. Opportunity witnesses require
source and event/state applicability. Contexts, typed events, Stack objects, triggers, costs,
targets, zone transitions, token definitions, and source incarnations cannot be freely borrowed.

Results audits have re-signed altered duplicate evidence, classifications, aggregate memberships,
execution references, source links, opportunity contexts, frozen inputs, and `balance_valid`
claims. The modified artifacts failed reconstruction even after outer digests were recomputed.

Actions #14–#16 materially deepened these boundaries:

- Action #14 froze trigger controller identity and deferred child triggers until parent resolution;
- Action #15 authenticated departure LKI, `another`, source absence, and reincarnation identity;
- Action #16 separated historical trigger-time artifact characteristics from current resolution-time
  characteristics and anchored both downstream trigger/Stack records to independent original event
  evidence.

**Judgment: strong for represented semantics.** No accepted execution claim rests only on producer
agreement or card-name inference.

### Stack, Priority, triggers, and SBAs

Accepted games exercise cast and trigger Stack objects, Priority grants/passes, all-pass resolution,
child-trigger deferral, damage-created triggers, First Strike to Priority to regular damage,
simultaneous triggers, failed Draw, lethal life loss, legend handling, token cessation, combat damage,
and post-resolution advancement.

The terminal-combat corrections establish SBAs before exposing trigger work and prevent all shared
drivers from continuing Stack/Priority/combat processing after a winner exists. Nonterminal trigger
paths continue through the ordinary Stack and Priority lifecycle.

**Judgment: credible for the implemented bounded lifecycle.** This is not a claim of complete Magic
response timing or every trigger/replacement form.

### Historical event evidence

Action #16 introduced an immutable original rules-event evidence record containing event identity,
cursor, type, subject incarnation, controller, turn/step, battlefield authority, and evaluated
historical characteristics. Invariants and Results Audit #1 reconstruct downstream ETB trigger and
Stack evidence against that independent original ledger.

The fully re-signed decoy-artifact attack fails even when mutually mutable downstream records agree.
Legitimate historical evidence remains valid after later type, controller, zone, and source changes.

**Judgment: credible and materially stronger than the previous milestone.** Historical authority and
current game state are now explicitly separate evidence domains.

### Authoritative battlefield characteristics

Printed `CardDefinition.type_line` is no longer substituted where rules depend on evaluated
battlefield characteristics. Creature-death LKI and Action #16 artifact qualification authenticate
the authoritative battlefield incarnation and evaluated `Permanent.type_line` at the relevant time.
Resolution-time conditions reevaluate current authoritative state for the frozen trigger controller.

**Judgment: credible for represented characteristic predicates.** A general continuous-effect/layer
system is still outside the current claim.

### Cross-platform frozen-input reconstruction

Smoke uses versioned canonical Git-clean identities for tracked text, raw byte identities for binary
inputs, and rejects dirty/missing/untracked substitutions. The contract was independently attacked
for LF/CRLF portability and the critical `hash committed A, execute dirty B` boundary. Linux exact-SHA
CI and Windows execution reconstruct the same frozen manifest.

**Judgment: credible.** The prior checkout-line-ending defect was an evidence-contract failure and is
closed without weakening input authentication.

### Mechanical credibility conclusion

No accepted artifact establishes a current silent mutation, unauthenticated execution claim,
nondeterministic replay, invariant leak, source-incarnation substitution, or frozen-input ambiguity.
Cardcade is mechanically credible for its explicitly represented scope.

## Coverage progress

| Checkpoint | Coverage-complete | Coverage-limited | REACHED / UNSUPPORTED |
| --- | ---: | ---: | ---: |
| baseline Smoke 0.1 | 5/180 | 175/180 | 692 |
| post-Action #14 | 10/180 | 170/180 | 599 |
| post-Action #15 | 17/180 | 163/180 | 562 |
| post-Action #16 | 18/180 | 162/180 | 548 |

Actions #14–#16 each completed the full evidence loop:

- **Action #14:** Dream Beavers' exact ETB drain/gain/Scry fragment moved to authenticated execution;
  the static five-game clearance prediction was observed.
- **Action #15:** Super Shredder departures produced authenticated trigger/counter transactions,
  including legitimate source-absent resolutions; five predicted direct clearances plus two changed
  trajectories produced seven newly complete games.
- **Action #16:** Donatello's intervening-if ETB Draw produced eight authenticated executions; all 14
  former unsupported reaches disappeared, the one predicted solo game cleared, and no new
  unsupported reach appeared.

The residual post-Action #16 graph contains:

- 25 exact Oracle-fragment clusters;
- 548 reached/unsupported occurrences;
- 160 nonzero cluster overlaps;
- 14/25 clusters with zero solo clearance;
- only 18/180 coverage-complete games.

The reduction from 692 to 548 is 144 occurrences, approximately 20.8%. Coverage-complete games rose
from 5 to 18, but 90% of games remain coverage-limited.

This disparity is not a mechanical failure. It shows that a relatively small number of successfully
implemented generic semantics removed many occurrences while most games still contain overlapping
unsupported fragments. The graph is increasingly controlled by dependency breadth rather than by
one high-frequency bounded omission.

## Action-construction economics

### 1. Bounded semantics still appropriate for targeted construction

- **Paramecia ETB mill three:** clear grammar, reusable ETB and zone machinery, but zero solo
  clearance.
- **Stockman Draw then discard:** existing Draw/discard infrastructure, ordered compound boundary,
  zero solo clearance.
- **Donatello artifact-entry self-counter:** strong reuse of Action #15/#16 event and counter
  machinery, only eight games and zero solo clearance.
- **Frog Butler temporary Reach:** narrow activation, only five games and zero solo clearance.
- **Tunnel Rats graveyard self-return tapped:** one solo clearance, but broader zone/source-permission
  requirements than its text length suggests.

These remain valid future Actions when their validation value justifies them. None currently
dominates the project critical path.

### 2. Dependency chains requiring prerequisite infrastructure

The leading example is Ray Fillet:

> `{2}, Remove a +1/+1 counter from a creature you control: Draw a card.`

Measured exposure is 30 occurrences across 29 games, 14 matchups, and two decks. It has two solo
clearances, predicting `18 → 20` if supported alone. Mana activation, counters, controller identity,
Stack/Priority, Draw, and failed-Draw handling already exist.

The missing boundary is not merely another Draw Action. It is a generic, authoritative selected-
creature `+1/+1` counter removal encoded as an atomic nonmana activation cost, including legality,
payment evidence, rollback, source/subject identity, and subsequent revalidation. Only after that
prerequisite is independently accepted does the exact Ray Fillet transaction become a small Action.

Other prerequisite chains include optional constrained artifact targeting for Rock Soldiers,
disjunctive live target predicates for Make Your Move, and color choice/mana-ability treatment for
Frog Butler.

**Economic judgment:** Ray Fillet is the strongest next targeted sequence, but it is not evidence
that Action #17 should begin immediately. It would consume at least two governed checkpoints to
clear two additional games statically.

### 3. Compound semantics

High-exposure clusters such as Courier of Comestibles, Zoo Escapees, Shredder deathtouch, Casey's
top-four selection, Ravenous Robots, Wingnut, Fugitive Droid, delayed random discard, Paramecia's
reflexive death transaction, Raphael's linked exile/play pair, and Ooze Spill combine several missing
actions, choices, targets, permissions, or temporary effects.

Their occurrence totals and pair-clearance arithmetic overstate their readiness. Implementing a
partial child does not make the exact parent fragment coverage-complete.

### 4. Broad engine-system gaps

- Utrom Scientists combines optional targeting, tap state, stun counters, and a rules-wide untap
  replacement.
- Menace changes blocker legality and Pilot choice across combat.
- Leonardo Sewer Samurai combines alternate-zone casting, characteristic qualification, entry
  state, and a death replacement.
- Reactive counterspell forms require response timing, Stack targeting, and target-of-target
  validation beyond one card transaction.

These are engine-system programs, not bounded Actions. They should be separately specified if
selected, not hidden inside an Action number.

### 5. Low-exposure semantics safe to remain unsupported next stage

Donatello artifact-entry self-counter, Raphael linked exile/play, Frog Butler's two activations,
Krang's variable Draw, and Ooze Spill each affect eight or fewer games in the current matrix. Their
opportunities are explicit and fail closed. Unless a broader stage establishes new leverage or a
foundational interaction, they can remain unsupported without invalidating represented mechanics.

## Targeted construction versus broader validation

### Continue targeted Action construction

Advantages:

- reduces known unsupported exposure;
- deepens reusable cost/target/zone primitives;
- produces precise acceptance contracts;
- Ray Fillet offers a concrete prerequisite hypothesis and two static clearances.

Disadvantages:

- the best candidate is now a prerequisite-plus-Action sequence;
- 14 clusters clear no game alone;
- every cluster clearing three or more games is compound or broad;
- repeated execution of the same 180-game matrix has diminishing ability to expose new engine
  interactions;
- optimizing the coverage-complete counter risks making telemetry, rather than engine trust, the
  development objective.

### Advance to another bounded engine-validation stage

Advantages:

- tests accepted mechanics over more seeds and rare state combinations;
- measures whether fail-closed/provenance guarantees survive scale;
- distinguishes stable residual exposure from artifacts of the current two-seed matrix;
- may reveal whether prerequisite systems such as counter-removal cost or optional targeting have
  broader empirical leverage;
- can discover new lifecycle defects without claiming complete-card or balance fidelity.

Risks:

- most games will remain coverage-limited;
- larger artifacts increase storage and independent-audit cost;
- game outcomes remain unsuitable for deck or balance decisions;
- a stage without frozen learning goals could become an expensive repetition of Smoke 0.1.

**Conclusion:** broader coverage-aware engine validation now has higher marginal validation value
than automatically beginning the Ray Fillet prerequisite sequence.

## Next validation stage

### Intended question

Define **Coverage-Aware Engine Validation Stage 0.2** to answer:

> Does Cardcade's accepted represented engine remain deterministic, invariant-clean, provenance-
> authentic, and fail-closed across a larger set of frozen seeds, and does that larger sample expose
> new foundational interactions or materially change the residual semantic-priority graph?

It must not ask which deck is strongest.

### Intended learning

The stage should measure:

- mechanical failure and fail-closed-stop incidence over new seeds;
- duplicate determinism and RNG-chain reconstruction at larger scale;
- new versus previously seen event/trigger/cost/combat/zone interaction shapes;
- execution frequency of accepted Actions #1–#16;
- exact REACHED / UNSUPPORTED and PRESENT / UNREACHED exposure;
- stability of the 25-cluster graph and Ray Fillet prerequisite leverage;
- whether any residual semantic becomes a foundational blocker under newly reached state;
- evidence-system scalability and artifact auditability.

### Required gates before execution

1. **Specification only first.** Freeze purpose, matrix, seeds, orientations, turn cap, duplicate
   policy, inputs, output schema, stop rules, storage, and acceptance criteria.
2. **Use new deterministic seeds.** Do not treat repeated Smoke 0.1 games as expanded evidence.
3. **Retain exact duplicates.** Duplicate executions prove reproducibility and do not increase the
   distinct-game sample.
4. **Retain the three-way conformance model.** Every participating fragment remains EXECUTED,
   REACHED / UNSUPPORTED, or PRESENT / UNREACHED through authenticated provenance.
5. **Fail closed on the first material defect.** No retry, seed replacement, partial aggregate, or
   mid-run correction.
6. **Preserve atomic success/failure evidence externally.** Predeclare artifact paths, sidecars,
   size handling, and independent validation tooling.
7. **Cross-platform frozen-input reconstruction.** Reproduce the versioned canonical hashing
   contract and exact execution baseline.
8. **Structural balance exclusion.** `balance_valid: false` remains derived for every game,
   including coverage-complete games.
9. **Independent readiness audit.** No game runs until the complete experiment and runner contract
   are accepted.
10. **Independent results audit before interpretation.** Authenticate duplicates, classifications,
    contexts, transactions, aggregates, and artifacts before drawing engine-validation conclusions.

A reasonable design candidate is 45 pairings with five new seeds per pairing and both orientations:
450 distinct games and 900 total executions after exact duplication. That arithmetic is a design
hypothesis, not authorization; the specification and readiness audit must determine whether it is
the smallest sample that answers the stated question.

## Historical 900-game smoke

The historical 900-game smoke should remain **retired in its original form**. Its scale does not
repair a contract lacking authenticated coverage classes, exact duplicate policy, fail-closed atomic
evidence, cross-platform frozen-input reconstruction, and structural balance exclusion.

The number 900 may reappear only as a consequence of a newly specified coverage-aware experiment.
For example, 450 distinct games duplicated exactly would produce 900 executions, not 900 independent
games. Calling those duplicates additional games would violate the accepted evidence model.

Therefore:

- do not revive or run the historical workflow;
- do not use its old output for calibration or deck conclusions;
- design Stage 0.2 under the current evidence contract;
- choose sample size from the learning objective, not nostalgia for the historical count.

## Coverage-complete versus balance-valid

**Coverage-complete does not mean balance-valid.**

A coverage-complete game proves that no known represented semantic opportunity was explicitly left
unsupported in that game. It does not prove strategic Pilot quality, statistical design adequacy,
complete Magic semantics, matchup representativeness, or freedom from PRESENT / UNREACHED text.

All current games correctly retain `balance_valid: false`. Stage 0.2 must preserve that boundary.
No win-rate, turn-length, or matchup result from these artifacts may drive calibration, deck revision,
or Design Studio work.

## Why the verdict is not CONTINUE TARGETED ACTION CONSTRUCTION

Targeted Actions remain useful, but the residual graph no longer offers a clearly dominant bounded
transaction. The strongest near-bounded candidate needs a prerequisite and statically clears only
two games. Continuing automatically would optimize a coverage counter while repeatedly sampling the
same game matrix. That is not the highest-leverage engine-validation strategy now.

## Why the verdict is not HOLD / REMEDIATE

HOLD requires evidence that represented gameplay cannot be trusted: silent approximation,
unauthenticated execution, state corruption, nondeterminism, invariant failure, or a foundational
semantic omission. Accepted evidence establishes none of those. Known omissions are explicit and
coverage-limited games are structurally excluded from stronger claims.

## Why the verdict is conditional rather than unconditional

Cardcade still omits material targeting, response, replacement, continuous-effect, combat-legality,
choice, search, and alternate-zone semantics. Larger execution will mostly produce coverage-limited
games and larger evidence artifacts. Without a predeclared question and independent readiness audit,
scale would add expense rather than trust.

## Decision and authorization boundary

**CONDITIONAL ADVANCE — define and independently audit Coverage-Aware Engine Validation Stage 0.2.
Do not automatically begin Action #17.**

- Action #17: not authorized;
- historical 900-game smoke: retired;
- Stage 0.2 execution: not authorized by this review;
- next authorized work: Stage 0.2 specification and readiness audit only;
- calibration and balance analysis: blocked;
- Pilot/deck/Design Studio changes: blocked;
- Prototype 0.3: not authorized.
