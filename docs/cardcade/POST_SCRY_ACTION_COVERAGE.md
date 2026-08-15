# Cardcade Post-Scry Action Coverage

## Status

- Evidence date: 2026-08-14
- Audited branch: `main`
- Audited HEAD: `6492ab472e3bc87ee0bb3b05fd9d6a9ef7fa8998`
- Source integration: PR #32, squash-merged as
  `6492ab472e3bc87ee0bb3b05fd9d6a9ef7fa8998`
- Scope: evidence-only Action coverage re-ranking after accepted Create Token,
  Deal Damage, and Scry
- Recommendation: **First Strike / Double Strike combat damage steps** is the
  single highest-leverage Action #4.

This report does not implement an Action. It does not modify engine behavior,
decks, prototypes, pilots, calibration, or smoke evidence.

## Merged-baseline verification

PR #32 had no intervening `main` change: its base and merge base were both
`3b8cc7a5d764408d3977dd1c59955e66414adac6`. Its diff contained only the
post-Deal-Damage evidence checkpoint, accepted bounded Scry implementation and
tests, acceptance-runner/pilot wiring, and Scry acceptance evidence. GitHub
reported green checks and `MERGEABLE / CLEAN` before the squash merge.

Merged-main validation:

| Check | Result |
| --- | --- |
| Full suite | `281 passed, 1 skipped` |
| Focused Scry | `19 passed` |
| Generic SemanticCoverage | `5 passed` |
| Card-data integrity | `5 passed` |
| Ruff format/check | clean |
| `git diff --check` | clean |
| Duplicate Acceptance Match seeds 7001–7005 | byte-equivalent |

`SCRY_ACTION_ACCEPTANCE.md` is preserved byte-for-byte: its merged blob is
`9856dc3bdecacddd30aa66fce741ec1c5fe94490`, identical to the accepted evidence
commit.

## Evidence universe

The ranking reconciles:

- Acceptance Match #001: 69 unsupported events / 21 exact card–Oracle-fragment
  pairs, six block-restriction rejections, and zero invariant violations;
- frozen roster: 102 unique cards across ten decks, with 600/600 slots resolving;
- authoritative TMT/PZA/TMC snapshot: 472 prints / 332 unique Oracle objects;
- accepted Create Token: 66 objects / 71 fragments recognized, 49 / 50 bounded
  payload executable, and 6 / 6 fully supported;
- accepted Deal Damage: 28 / 29 recognized, 12 / 12 bounded executable, and
  2 / 2 fully supported;
- accepted Scry: 7 / 7 recognized and bounded executable, and 2 / 2 fully
  supported;
- generic `SemanticCoverage` separation of payload, parent/context, follow-up,
  full-fragment support, and explicit limitations.

Accepted Action membership remains locked by the existing executable tests and
digests. Already-supported token creation, damage, and Scry payloads are not
counted as missing merely because a surrounding ability remains incomplete.

## Acceptance replay after Scry

| Seed | Winner / ending turn | Unsupported events / seed pairs | Scry transactions |
| ---: | --- | ---: | ---: |
| 7001 | Raphael / 16 | 12 / 12 | 2 |
| 7002 | Leonardo / 17 | 14 / 8 | 0 |
| 7003 | Leonardo / 17 | 15 / 12 | 3 |
| 7004 | Leonardo / 21 | 18 / 16 | 2 |
| 7005 | Raphael / 16 | 10 / 7 | 1 |

Aggregate evidence remains:

- 69 unsupported events / 21 exact pairs;
- eight Scry transactions, all April O'Neil;
- 16 Deal Damage transactions;
- six block-restriction rejections;
- zero invariant violations;
- unchanged winners and ending turns.

## Exact residual acceptance attribution

Each exact pair is assigned once to the capability that is actually missing.
Supported child payloads are excluded from the missing-family counts.

| Primary missing capability | Events | Pairs | Exact pressure |
| --- | ---: | ---: | --- |
| First/double strike damage-step semantics | 13 | 4 | activated first strike, turn-scoped first strike, intrinsic double strike, and attack-scoped double strike grant |
| Other combat keywords/choices | 12 | 4 | trample 5/1, Wingnut keyword choice 3/1, lifelink 2/1, menace 2/1 |
| Sneak casting transaction | 20 | 5 | alternate/additional cost, Declare Blockers timing, return cost, tapped-and-attacking entry |
| Return/exile/play-from-zone | 13 | 4 | activated bounce 6/1, graveyard casting/finality 3/1, exile-top 2/1, play-exiled permission 2/1 |
| Discard or hand-bottom followed by Draw | 8 | 2 | Null Group rummage 4/1 and Manhole Missile filtering follow-up 4/1 |
| Casey top-four artifact selection | 2 | 1 | look/reveal/choose/hand movement/random bottom ordering; not Scry |
| Food activation/use | 1 | 1 | activation, tap/sacrifice cost, and life gain; not Create Token |
| **Total** | **69** | **21** | |

The first/double-strike row is split from the former heterogeneous “combat
abilities” umbrella because it has one coherent rules boundary: combatants deal
damage in the first-strike combat damage step and, for double strike, again in
the regular combat damage step. Lifelink, trample, menace, flying/haste choice,
and general permission effects remain distinct semantics.

## Supported-child dependency pressure

The previously audited incomplete contexts remain dependency evidence, not
automatic credit for delivery shells:

- Create Token has executable child payloads under 19 trigger contexts, four
  activation contexts, six conditions, three choices, three preceding effects,
  five follow-ups, and 28 token-use limitations; overlaps exist.
- Deal Damage has executable child payloads under three trigger contexts, three
  activation contexts, one choice context, and four follow-ups.
- Scry has five bounded payloads whose full fragments remain incomplete: Dream
  Beavers, Insectoid Exterminator, Nobody, and Path of Ancestry require broader
  trigger/condition/preceding-effect delivery; Hamato Guardian Stance requires
  its preceding spell effect.

An activated-ability or trigger-delivery checkpoint cannot claim those children
unless the particular event, condition, cost, target/choice, and effect are all
represented. `SemanticCoverage` must continue to prevent supported children
from upgrading unsupported parents.

## Re-ranked missing reusable Actions

Roster/full-pool counts are exposure counts, not claims that every matching
fragment becomes executable in one checkpoint. Family rows overlap and must not
be summed.

| Rank | Missing reusable Action | Direct acceptance leverage | Frozen reach | Full-pool reach | Dependency leverage and gameplay impact | Complexity / required YELLOW extensions |
| ---: | --- | --- | --- | --- | --- | --- |
| **1** | **First Strike / Double Strike combat damage steps** | **13 events / 4 pairs**; **8 / 3** are reachable without activated-ability delivery, and another **5 / 1** becomes reachable when activation exists | **7 cards / 5 decks** | **12 Oracle objects** | Highest bounded residual effect leverage; changes actual combat outcomes and supplies the semantics needed by intrinsic, conditional, granted, and later activated instances | Medium–high. Extend **Combat State**, **Events**, **State-Based Actions**, and **Invariants** for first-strike and regular damage steps; **Continuous Effects/Durations** only for granted or turn-scoped instances. No new Priority or zone Action is required for intrinsic/static cases. |
| 2 | Draw Cards | 8 / 2 compound pairs contain Draw, but Draw alone clears neither pair | 17 / 7 | 54 | Broad reusable child effect; existing opening/turn draw and empty-library-loss seams reduce risk; unlocks Null Group and Manhole filtering once their movement/choice parents exist | Low–medium. Extend **Zones**, **Events**, and **Invariants** with an Action transaction and `SemanticCoverage`; replacement effects remain explicit. |
| 3 | Activated-ability announcement/delivery | 12 / 3 fragments have an activation parent: Prehistoric bounce 6/1, Leonardo first strike 5/1, Food use 1/1; announcement alone executes none | 46 / 10 | 127 | After Action #4 it could unlock Leonardo's five first-strike events; it also fronts token-use and damage activation contexts | High. Extend **Priority**, **Choices vs Targets**, **Costs**, **Stack**, and **Invariants**; each effect Action, timing restriction, tap/sacrifice cost, and target still requires evidence. |
| 4 | Discard / hand-to-library filtering | 8 / 2 compound pairs; Null Group is Discard→Draw, Manhole is optional hand→library-bottom→Draw | Discard 10 / 6; hand-bottom 1 / 2 | Discard 16; represented hand-bottom shape 1 | Direct partner for Draw and meaningful hand/graveyard play, but two destination semantics must not be conflated | Medium. Extend **Choices vs Targets**, **Zones**, **Events**, and **Invariants**; optional sequencing and the attack-trigger parent remain separate. |
| 5 | Trigger-delivery expansion | Null Group 4/1 and Raphael attack permission 2/1 expose broader attack triggers; no missing child becomes executable from a generic shell alone | 60 / 10 | 190 | Largest cross-cutting dependency reach: token, damage, and Scry payloads sit under incomplete trigger contexts | High. Existing Triggers is GREEN only for represented shapes; extend **Events**, **Priority**, **Choices vs Targets**, **State-Based Actions**, and condition/LKI handling one trigger family at a time. |
| 6 | Return / exile / play-from-zone Actions | 13 / 4 | 13 / 10 | 56 | High direct pressure and broad deck reach; enables bounce, recursion, impulse access, finality, and Sneak costs | High. This is several destination-specific Actions requiring **Zones**, **Choices vs Targets**, **Events**, **Invariants**, permissions, replacement effects, and sometimes Stack/Costs. |
| 7 | Sneak casting transaction | 20 / 5 | 18 / 6 | 27 | Largest named acceptance family and major Turtle/Ninja gameplay impact | Very high. Requires **Priority**, alternative/additional **Costs**, **Combat State**, **Zones**, **Choices**, stack permissions, return cost, Declare Blockers timing, and tapped-and-attacking entry together. |
| 8 | Casey-style top-card selection | 2 / 1 | broader search/reveal family 6 / 5 | 26 | Reuses Scry's private ordered-library choice boundary, but has distinct look-four, typed selection, reveal, hand movement, and random bottoming | High. Extend **Choices vs Targets**, **Zones**, **Deterministic RNG** consumption, **Events**, and **Invariants**. It must not route through Scry. |
| 9 | Sacrifice / artifact-token use | Food use 1 / 1 | 23 / 9 | 61 | Central to Food, Mutagen, Treasure, Clue, creature, and artifact costs | High. Extend transactional **Costs**, **Zones**, **Events**, **Triggers**, **State-Based Actions**, **Choices**, and effect-specific Actions such as life gain. |
| 10 | Remaining combat keyword/effect slices | 12 / 4 residual after first/double strike | broad combat family 55 / 10 | 150 | High gameplay pressure, but trample, lifelink, menace, and modal keyword grants are separate rules families | Medium–very high by slice. Extend **Combat State**, **Continuous Effects**, **Durations**, **Choices**, **Layers**, and event/SBA handling only as each keyword requires. |

Lower immediate-leverage families remain explicit: counters, destroy, equip,
control change, copy, mill, search/shuffle outside Casey, and counterspell. Raw
pool breadth does not outrank a bounded Action when its executable delivery
requires several missing Actions.

## Why Action #4 outranks the prior runners-up

### Versus Activated-ability announcement/delivery

Activated delivery has much larger raw exposure, but it is a cross-cutting
protocol, not a self-contained effect. None of its three acceptance pairs can
execute from announcement alone: Prehistoric Pet still needs target selection
and Return-to-Hand, Food needs tap/sacrifice costs and life gain, and Leonardo
needs first-strike semantics. Implementing first/double strike first supplies a
real reusable effect and makes Leonardo's activation a concrete later delivery
win instead of an empty shell.

### Versus Trigger-delivery expansion

The generic event→trigger→stack architecture is already accepted for represented
shapes. Broader trigger text spans attacks, conditions, mana-spent events,
preceding effects, modes, targets, and missing child Actions. A broad expansion
would either remain non-executable or overclaim support. First/double strike has
three currently reachable static/conditional pairs without needing new generic
trigger delivery.

### Versus Draw Cards

Draw is broader and cheaper, but its eight acceptance events are locked behind
two different compound parents. Null Group still requires an attack trigger,
optional discard choice, and Discard transaction; Manhole still requires an
optional hand choice and hand-to-library-bottom movement. First/double strike
has eight immediately reachable events across three pairs, plus five more once
activated delivery is added, and it directly affects combat rather than merely
establishing another blocked child payload.

### Versus Discard / hand-to-library filtering

This is not one movement transaction: Discard moves Hand→Graveyard, while
Manhole moves Hand→Library bottom. Both then require Draw and optional sequencing;
Null Group additionally requires attack-trigger delivery. Treating them as one
Action to clear telemetry would repeat the prohibited compound-family shortcut.

## Exact first/double-strike exposure

The authoritative full-pool set contains 12 Oracle objects:

- Baxter Stockman
- Casey Jones, Asphalt Hooligan
- Hard-Won Jitte
- Leonardo, Leader in Blue
- Leonardo, Sewer Samurai
- Leonardo, Worldly Warrior
- Mouser Attack!
- Null Group Biological Assets
- Raphael, the Nightwatcher
- Shark Shredder, Killer Clone
- Ticked Off
- Tokka & Rahzar, Unsupervised

The frozen intersection is seven cards across Casey Jones, Leonardo, Raphael,
Shredder, and Splinter decks:

- Hard-Won Jitte
- Leonardo, Leader in Blue
- Leonardo, Sewer Samurai
- Mouser Attack!
- Null Group Biological Assets
- Raphael, the Nightwatcher
- Shark Shredder, Killer Clone

Before implementation, Action #4 must independently classify intrinsic keywords,
turn-scoped static conditions, attack-scoped grants, activated grants, Equipment
effects, and compound effects. The checkpoint should execute only contexts whose
delivery and duration are already represented. Recognition of a first/double
strike child must not suppress an unsupported activation, attachment, trigger,
condition, or preceding/follow-up limitation.

## UNKNOWN preservation

The seven context-sensitive Oracle objects remain UNKNOWN:

- Arcane Signet
- Chromatic Lantern
- Command Tower
- Double Jump // Flying Kick
- Exotic Orchard
- Fast Forward
- Plague of Vermin

Accepted Scry supplies no evidence to change them. Double Jump // Flying Kick's
counter/P/T-setting and creature-damage semantics remain UNKNOWN because split
faces and Fuse require a multi-half casting/resolution contract; it is not part
of the first/double-strike family. Plague of Vermin remains recognized for token
grammar but non-executable for variable quantity and iterative choices.

## Recommendation

**Implement First Strike / Double Strike combat damage steps as Action #4.**

The future checkpoint should be bounded to authoritative first-strike and
regular combat damage-step participation, including double strike, with typed
combat evidence and SBA timing after each damage step. Intrinsic/static contexts
should be proved first. Activated delivery, Equipment attachment, unrelated
keyword grants, trample, lifelink, menace, Sneak, Draw, Discard, and other Actions
must remain explicit and separate.
