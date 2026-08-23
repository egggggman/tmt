# Cardcade Engine Validation Milestone Review

## Decision

**CONDITIONAL PASS — Cardcade is mechanically credible enough to leave targeted Action
construction as the critical path and advance to a bounded, coverage-aware engine smoke-testing
stage.**

The condition is scope discipline: broader testing may measure deterministic engine robustness,
semantic exposure, and represented gameplay diversity, but it may not treat games containing
explicit unsupported semantics as complete-Magic simulations or use their results for balance,
calibration, Pilot tuning, or deck revision.

No remaining evidence establishes a foundational engine defect. Action #14 is not authorized by
this review. Prototype 0.3 and the historical 900-game/calibration workflow remain blocked.

## Central question

> Is Cardcade now mechanically credible enough to leave targeted engine construction as the
> critical path and advance to broader empirical testing?

**Yes, conditionally.** Cardcade has demonstrated that represented mechanics execute through
authoritative state, fail closed when evidence or state is invalid, and remain deterministic across
all ten frozen decks. Its limitations are now predominantly explicit semantic omissions and known
bounded architecture surfaces, rather than silent approximation or corrupt state.

## Evidence reviewed

### Engine 0.8 foundation

The Foundation Acceptance Audit accepted the architectural baseline at 10 GREEN / 10 YELLOW /
0 RED / 0 UNKNOWN. The YELLOW rows were explicit extension boundaries, not concealed failures.
Authoritative card data covered 472 print records, 332 unique Oracle objects, and all 600 frozen
deck slots.

The core authority model was already established for:

- runtime object identity and new-object zone transitions;
- authoritative Hand, Library, Stack, Battlefield, Graveyard, and former-object state;
- turn-step succession and unresolved-Stack advancement guards;
- engine-owned actions, legality, mutation, and revalidation;
- interpreter-owned Oracle-derived semantics;
- Pilot selection only among immutable legal options;
- deterministic RNG, snapshots, invariants, and typed evidence.

### Independently accepted implemented capabilities

The validation program subsequently added and independently audited bounded reusable capabilities:

1. Create Token and token cessation;
2. Deal Damage;
3. Scry;
4. First Strike / Double Strike damage steps;
5. activated-ability announcement/delivery and represented Priority/pass;
6. Targeted Return to owner's Hand;
7. Trample assignment;
8. Lifelink damage results;
9. optional hand-bottom filtering followed by conditional Draw;
10. optional Discard followed by conditional Draw under an attack trigger;
11. Sneak casting;
12. canonical Food activation;
13. creature-dies → Draw-one trigger delivery.

The audit history preserves rejections as well as accepts. Defects in semantic composition,
provenance, Priority, stale combat state, evidence reconstruction, failed-Draw timing, Stack/source
linkage, and last-known creature state were rejected before integration rather than silently fixed
or reclassified.

### Acceptance Match #001

Acceptance #001 contributed five distinct deterministic Leonardo/Raphael games, each duplicated.
It established stable represented gameplay for zones, costs, Stack/Priority, combat, triggers,
damage, actions, and invariants. Its residual semantics were classified conservatively rather than
treated as runtime failures. The post-Food assessment found zero foundational blockers.

Acceptance #001 remains conformance evidence, not balance evidence.

### Acceptance Stage #002

Stage #002 expanded deterministic coverage to the other eight frozen decks through four pairings,
two seeds, and both orientations:

- 16 distinct games;
- 32 duplicate executions;
- 0 duplicate mismatches;
- 0 runner stops in the accepted post-Action run;
- 0 invariant violations;
- 70 authenticated execution references;
- 46 authoritative opportunity contexts;
- 60 context-backed and 32 typed-event-backed opportunity witnesses.

Together, Acceptance #001 and Stage #002 provide 21 distinct deterministic games and 42 total
executions over all ten frozen decks. This remains a deliberately small conformance sample, but it
is materially broader than a single matchup.

### Empirical Action-selection loop

Stage #002 first exposed Buzz Bots' dies→Draw semantic as 13 REACHED / UNSUPPORTED occurrences
across eight games. That evidence selected Action #13. After independent implementation audits and
integration, the fresh Stage run authenticated exactly 13 executions across the same eight games
and left zero unsupported reaches for the fragment.

The new semantics exercised combat damage, lethal SBAs, last-known information, trigger creation,
Stack placement, Priority/pass, resolution, Draw, and subsequent game progression. They exposed a
real engine coordination defect and a runner coordination defect. Both stopped fail closed, were
independently diagnosed, minimally corrected, audited, integrated, and then retested from game #1.

This complete loop is strong evidence that Cardcade can both discover and safely absorb a new
represented capability without weakening its trust boundaries.

## Mechanical credibility assessment

| Area | Evidence result | Milestone judgment |
|---|---|---|
| Card data and frozen decks | checksum-verified authoritative snapshot; all frozen slots resolve | Credible |
| Identity and zones | runtime IDs, stale/fabricated rejection, new objects, token cessation, immutable lineage | Credible for represented zones |
| Turn/phase structure | deterministic successor graph; illegal and unresolved-Stack advancement rejected | Credible for represented turn model |
| Stack and Priority | casts, triggers, activations, all-pass resolution, combat-created trigger pause/resume | Credible for represented lifecycle |
| Combat | declarations, damage, strike steps, Trample, Lifelink, SBAs, postcombat cleanup | Credible for bounded combat model |
| Triggers and events | typed ETB, attack, departure/death provenance; Stack delivery and resolution | Credible for implemented trigger shapes |
| Costs/resources | mana, tap, sacrifice and bounded compound costs with rollback and evidence | Credible for implemented costs |
| Targets/choices | authoritative runtime target identity and bounded immutable choices | Credible but deliberately narrow |
| SBAs/invariants | lethal, legend, token cessation, failed Draw; repeated fail-closed checks | Credible for represented SBA set |
| Determinism | duplicate Acceptance #001 and all 16 Stage reports byte-identical | Credible |
| Conformance evidence | EXECUTED / REACHED / PRESENT provenance and authentication audited | Credible |
| Engine/Interpreter/Pilot boundary | preserved across Actions and both runners | Credible |

No area contains evidence of a current silent mutation, unauthenticated execution claim,
nondeterministic replay, invariant leak, or state-authority bypass.

## Remaining unsupported semantics

The accepted post-Action Stage artifact contains 15 unique REACHED / UNSUPPORTED semantics and 53
classified occurrences. Their nature matters more than their count.

### High-frequency but compound

- Utrom Scientists: optional constrained target, tap, stun counter, untap replacement;
- Dream Beavers: life loss, life gain, sequencing, supported Scry child;
- Fugitive Droid: response timing, sacrifice cost, Stack target, predicate, counterspell.

These can materially alter gameplay, but none reveals corruption in the represented engine. Their
explicit nonexecution prevents false conformance claims.

### Clean extension candidates with narrower exposure

- Super Shredder departure/counter trigger;
- Donatello artifact-conditional ETB Draw;
- Donatello artifact-entry counter trigger;
- Ravenous Robots temporary token haste;
- Stockman Draw then Discard;
- Rock Soldiers constrained artifact destruction.

These have credible implementation seams but no single candidate combines enough reach, deck
exposure, and low dependency depth to make Action construction the obvious next critical path.

### Disproportionate or low-leverage dependencies

- Ray Fillet counter-removal cost;
- Casey top-four artifact selection;
- Casey delayed random Discard;
- Shredder temporary deathtouch;
- Courier search/reveal/shuffle branch;
- Zoo Escapees compound Mutagen fragment.

These are safe to keep explicit while broader testing gathers better prioritization evidence.

None of the 15 is a foundational blocker under the current represented-scope claim. They can cause
Cardcade outcomes to differ from complete Magic. That is a fidelity limitation, not an authority or
determinism failure, provided every relevant opportunity remains classified and no unsupported
child is silently executed.

## Conditions attached to the pass

Broader empirical testing is trustworthy only under all of these conditions:

1. **Coverage-aware output remains mandatory.** Every game must preserve EXECUTED,
   REACHED / UNSUPPORTED, and PRESENT / UNREACHED evidence with exact semantic membership.
2. **Fail closed immediately.** Any runner stop, invariant violation, illegal mutation,
   nondeterminism, unauthenticated evidence, unclassified reach, or silent approximation aborts the
   stage and becomes evidence.
3. **Unsupported reach is not erased.** Games may continue through explicitly omitted semantics,
   but reports must identify which outcomes were produced under incomplete semantic fidelity.
4. **No balance inference.** Win rates, turn lengths, and matchup outcomes cannot drive deck
   revisions or calibration while material unsupported semantics are reached.
5. **Pilot scope remains explicit.** The deterministic Pilot proves legal engine interaction, not
   strategic competence or human-representative play.
6. **The frozen decks remain unchanged.** Broader engine testing may vary pairings and seeds, not
   deck contents.
7. **No automatic Action queue.** New capability work requires repeated empirical leverage or a
   newly established foundational defect.
8. **The next sample must be bounded and predeclared.** Pairings, orientations, seeds, stop rules,
   artifacts, and acceptance criteria must be frozen before execution.

These conditions are mechanically enforceable using the accepted Stage runner/conformance
architecture. They are limitations to measure and stratify, not reasons to HOLD the engine.

## What this pass authorizes

This review authorizes the **definition and readiness audit of a bounded Coverage-Aware Engine
Smoke Stage 0.1**.

That next checkpoint should test broader deterministic robustness and pairing diversity across the
unchanged frozen ten-deck environment. Its purpose is to learn:

- whether accepted engine systems remain stable over more games and interactions;
- how often each unsupported semantic is actually reached;
- which accepted Actions execute across decks and pairings;
- whether new fail-closed defects emerge;
- whether the current Action ranking changes under a broader sample.

The smoke-stage design must be reviewed before execution. This review does **not** itself authorize
running the historical 900-game smoke, measuring balance, calibrating pilots, changing decks, or
creating Prototype 0.3.

## Why the outcome is not HOLD

HOLD would require evidence that represented gameplay cannot be trusted: silent approximation,
state corruption, invalid authority, nondeterminism, invariant failure, or a remaining semantic
whose absence makes the represented transactions themselves unsound.

The accepted artifacts show the opposite. Broader games repeatedly exercised authoritative state
and exposed coordination defects through deliberate fail-closed stops. After correction, the same
frozen matrix completed deterministically with independently authenticated evidence. Remaining
semantics are visible and bounded rather than silently approximated.

## Why the outcome is not unconditional PASS

Cardcade is not complete Magic. It still has bounded combat, response, targeting, choice, zone,
replacement, attachment, continuous-effect, and cost surfaces. Its Pilot has not been validated as
a strategic agent, and 21 distinct conformance games are not enough for statistical confidence.
Unsupported semantics can materially alter trajectories.

Those limitations prevent balance/calibration claims, but they do not prevent a carefully scoped
engine smoke stage from gathering more useful conformance evidence.

## Final gate

**CONDITIONAL PASS — targeted engine construction is no longer the Cardcade critical path. Define
and independently audit a bounded Coverage-Aware Engine Smoke Stage 0.1 before running it.**

- Action #14: stopped
- Deck revisions: stopped
- Pilot tuning: stopped
- Historical 900-game smoke/calibration: blocked
- Prototype 0.3: not authorized
- Next authorized work: smoke-stage specification and readiness audit only
