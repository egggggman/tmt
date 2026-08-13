# Cardcade Engine 0.7 Rules Coverage Record

This record is regenerated from commit `a0ab301` (the Engine 0.7b validation checkpoint),
`src/tmnt_design_studio/engine07.py`, `tests/test_engine07.py`, the frozen roster, and deterministic
Acceptance Match #001 replays. Current Comprehensive Rules and current Oracle text take precedence
over this implementation record.

## Reconciliation result

The code at the recorded 0.7b checkpoint is still `cardcade-0.7.0-alpha.1`. Commit `a0ab301` is an
empty audit commit over `d62e7ab`; it adds no implementation. Contrary to the prior 0.7b report,
this branch contains no CR 500–514 phase/step state machine and no reusable token-creation,
counter, or power/toughness-modification `Action` classes. Those capabilities must not be counted
as implemented until code and deterministic tests exist on this branch.

## Code-derived coverage matrix

| Concept | Rules anchor | Actual status at `a0ab301` | Deterministic evidence | Unsupported boundary |
| --- | --- | --- | --- | --- |
| Zones, opening seven, 20 life | CR 103, 400 | Partial: library, hand, battlefield, graveyard | opening-state test | Mulligans, exile, command, stack, and ownership distinct from controller |
| Starting player draw | CR 103.8 | Implemented for runner-fixed two-player game one | first-player-draw test | Play/draw choice and multiplayer |
| Turn/phase/step structure | CR 500–514 | Partial string state only: `setup`, `beginning`, `precombat_main`, `combat`, `postcombat_main`, `ending`; `begin_turn()` jumps directly to main phase and `combat()` resolves combat monolithically | turn trace only | No step state machine, priority, stack, upkeep, draw step, declare-blockers window, end step, or cleanup sequencing |
| Land play | CR 305 | Implemented: one basic land during an active-player main phase | land-per-turn test | Nonbasic lands, permissions, additional land plays |
| Mana and casting | CR 106, 601 | Partial: untapped Plains/Mountain count, mono-color symbols, tap-to-pay | casting test | Stack, timing, generic mana choice, multiple colors, mana abilities, alternate/additional costs, cost changes |
| Creature permanents | CR 110, 302 | Partial: printed P/T, counters stored separately, additive continuous modifiers, tapped state, marked damage, summoning sickness, Haste | casting/combat/P/T tests | Tokens, non-additive/layer interactions, characteristic changes, control changes |
| Reusable P/T effects | CR 613, 611.3, 514.2 | Implemented for additive persistent derived modifiers and `until end of turn` modifiers; supports self-scaling static effects, Alliance creature-entry effects, conditional ETB team effects, and attack-triggered other-attacker team effects through generic Oracle patterns | deterministic separation, recomputation, team, trigger, cleanup, and invariant tests | No set/switch P/T, dependency/layer ordering beyond additive deltas, counters Action, or general trigger stack |
| Attack/block declarations | CR 508–509 | Partial: all chosen attackers tap; one blocker per attacker | sickness/combat tests | Restrictions, requirements, evasion, vigilance, menace, multiple blockers, attack costs, declare-blockers priority |
| Combat damage/state-based deaths | CR 510, 704 | Partial: simultaneous base damage for one-to-one blocks, lethal damage, unblocked player damage | combat/graveyard/win tests | First/double strike, trample, lifelink, deathtouch, damage assignment order, indestructible, regeneration |
| Targeted damage | CR 115, 120 | Partial named-card special case: Manhole Missile deals 3 to an opposing creature | dead-target test and acceptance trace | Optional hand-bottom/draw clause and general damage Action |
| Restricted destruction | CR 115, 701.7 | Partial named-card special case: Make Your Move destroys an opposing creature with power 4+ | acceptance trace | Artifact/enchantment targets and general destroy Action |
| Losing the game | CR 104 | Implemented for life <= 0 and drawing from an empty library | focused tests | Draws, concession, poison, and other loss conditions |
| Legend rule | CR 704.5j | Explicitly unsupported; a duplicate cast is skipped | limitation events | No keep-choice or graveyard transition; skipping the cast changes legal gameplay |
| Card abilities | Oracle text | Unsupported except Haste and the two named spell fragments above | `unsupported_semantics` events | One generic reason currently represents every unresolved keyword, trigger, static ability, activated ability, replacement effect, and spell clause |

## Deterministic Acceptance Match #001 limitation replay

Replayed Leonardo Prototype 0.1 versus Raphael Prototype 0.1 with seeds 7001–7005. Counts below
are exact `unsupported_semantics` event occurrences, not the deduplicated `snapshot.limitations`
set. The engine emits one generic `non-foundation abilities do not resolve` event per resolved
creature even when that card has multiple unsupported semantics. Consequently, exact per-card event
counts are available, but exact per-semantic occurrence counts are **not recoverable** from current
telemetry. Assigning a creature event to one of its several abilities would be a silent
approximation, so this record does not do that.

### Seed 7001

Winner Raphael, turn 18; 12 occurrences, 10 distinct card/reason pairs.

| Occurrences | Card | Recorded reason |
| ---: | --- | --- |
| 2 | April O'Neil, Kunoichi Trainee | legend rule choice is not implemented; duplicate cast skipped |
| 2 | April O'Neil, Kunoichi Trainee | non-foundation abilities do not resolve |
| 1 each | Leonardo, Big Brother; Leonardo, Cutting Edge; Leonardo, Sewer Samurai; Mutant Town Musicians; Null Group Biological Assets; Raphael, Most Attitude; Raphael, Tough Turtle; Wingnut, Bat on the Belfry | non-foundation abilities do not resolve |

### Seed 7002

Winner Raphael, turn 24; 17 occurrences, 10 distinct card/reason pairs.

| Occurrences | Card | Recorded reason |
| ---: | --- | --- |
| 4 | Leonardo, Big Brother | legend rule choice is not implemented; duplicate cast skipped |
| 3 | Prehistoric Pet | non-foundation abilities do not resolve |
| 2 each | Leonardo, Big Brother; Leonardo, Leader in Blue | non-foundation abilities do not resolve |
| 1 each | Mighty Mutanimals; Mutant Town Musicians; Null Group Biological Assets; Raphael, Most Attitude; Raphael, Tough Turtle; Wingnut, Bat on the Belfry | non-foundation abilities do not resolve |

### Seed 7003

Winner Leonardo, turn 23; 31 occurrences, 14 distinct card/reason pairs.

| Occurrences | Card | Recorded reason |
| ---: | --- | --- |
| 8 | April O'Neil, Kunoichi Trainee | legend rule choice is not implemented; duplicate cast skipped |
| 5 | Leonardo, Big Brother | legend rule choice is not implemented; duplicate cast skipped |
| 3 | April O'Neil, Kunoichi Trainee | non-foundation abilities do not resolve |
| 3 | Raphael, Tough Turtle | legend rule choice is not implemented; duplicate cast skipped |
| 2 each | Leonardo, Leader in Blue; Raphael, Tough Turtle | non-foundation abilities do not resolve |
| 1 each | Casey Jones, Jury-Rig Justiciar; Leonardo, Big Brother; Leonardo, Sewer Samurai; Lita, Little Orphan Amphibian; Mutant Town Musicians; Null Group Biological Assets; Raphael, Most Attitude; Wingnut, Bat on the Belfry | non-foundation abilities do not resolve |

### Seed 7004

Winner Leonardo, turn 23; 14 occurrences, 12 distinct card/reason pairs.

| Occurrences | Card | Recorded reason |
| ---: | --- | --- |
| 2 each | April O'Neil, Kunoichi Trainee; Leonardo, Cutting Edge | non-foundation abilities do not resolve |
| 1 | Leonardo, Cutting Edge | legend rule choice is not implemented; duplicate cast skipped |
| 1 each | Casey Jones, Jury-Rig Justiciar; Leonardo, Big Brother; Leonardo, Leader in Blue; Leonardo, Sewer Samurai; Lita, Little Orphan Amphibian; Null Group Biological Assets; Prehistoric Pet; Raphael, the Nightwatcher; Wingnut, Bat on the Belfry | non-foundation abilities do not resolve |

### Seed 7005

Winner Raphael, turn 16; 16 occurrences, 8 distinct card/reason pairs.

| Occurrences | Card | Recorded reason |
| ---: | --- | --- |
| 5 | Raphael, Tough Turtle | legend rule choice is not implemented; duplicate cast skipped |
| 3 | Leonardo, Big Brother | legend rule choice is not implemented; duplicate cast skipped |
| 2 each | Mutant Town Musicians; Prehistoric Pet | non-foundation abilities do not resolve |
| 1 each | April O'Neil, Kunoichi Trainee; Leonardo, Big Brother; Raphael, Most Attitude; Raphael, Tough Turtle | non-foundation abilities do not resolve |

### Aggregate

Across five games: 90 occurrences and 19 distinct card/reason pairs. Legend-rule skips account for
31 occurrences; generic unresolved-ability events account for 59.

| Occurrences | Card | Recorded reason |
| ---: | --- | --- |
| 12 | Leonardo, Big Brother | legend rule choice is not implemented; duplicate cast skipped |
| 10 | April O'Neil, Kunoichi Trainee | legend rule choice is not implemented; duplicate cast skipped |
| 8 | Raphael, Tough Turtle | legend rule choice is not implemented; duplicate cast skipped |
| 8 | April O'Neil, Kunoichi Trainee | non-foundation abilities do not resolve |
| 6 each | Leonardo, Big Brother; Prehistoric Pet | non-foundation abilities do not resolve |
| 5 each | Leonardo, Leader in Blue; Mutant Town Musicians; Raphael, Tough Turtle | non-foundation abilities do not resolve |
| 4 each | Null Group Biological Assets; Raphael, Most Attitude; Wingnut, Bat on the Belfry | non-foundation abilities do not resolve |
| 3 each | Leonardo, Cutting Edge; Leonardo, Sewer Samurai | non-foundation abilities do not resolve |
| 2 each | Casey Jones, Jury-Rig Justiciar; Lita, Little Orphan Amphibian | non-foundation abilities do not resolve |
| 1 each | Mighty Mutanimals; Raphael, the Nightwatcher | non-foundation abilities do not resolve |
| 1 | Leonardo, Cutting Edge | legend rule choice is not implemented; duplicate cast skipped |

## Engine 0.7c legend-rule and telemetry validation

The follow-on 0.7c implementation adds a reusable state-based-action pass with separate legend-rule
and lethal-damage checks. A configurable deterministic chooser selects which same-name legendary
permanent to keep; every other one is put into its controller's graveyard and attributed to the
`legend_rule` SBA. Duplicate legendary spells now resolve instead of being silently refused.

Unsupported telemetry is emitted once per exact nonempty Oracle-text line (or uncovered keyword),
with `card`, `oracle_fragment`, `player`, `turn`, `phase`, and categorical `reason`. This changes the
unit being counted: the pre-change count is one generic event per resolved card plus repeated
legend-cast skips, while the post-change count is one event per unresolved Oracle fragment. Raw
totals therefore measure different things and must not be interpreted as a regression.

| Seed | Before: events / unique card-reasons | After: events / unique card-fragments | Legend choices after | Winner / turn before | Winner / turn after |
| ---: | ---: | ---: | ---: | --- | --- |
| 7001 | 12 / 10 | 19 / 17 | 1 | Raphael / 18 | Raphael / 16 |
| 7002 | 17 / 10 | 30 / 19 | 1 | Raphael / 24 | Raphael / 24 |
| 7003 | 31 / 14 | 34 / 24 | 4 | Leonardo / 23 | Leonardo / 21 |
| 7004 | 14 / 12 | 31 / 26 | 1 | Leonardo / 23 | Leonardo / 23 |
| 7005 | 16 / 8 | 20 / 12 | 3 | Raphael / 16 | Raphael / 16 |
| **Total** | **90 / 19 aggregate pairs** | **134 / 34 aggregate card-fragments** | **10** | — | — |

The 31 pre-change legend-rule limitation events fall to zero. Ten actual legend-rule choices occur
post-change; the difference exists because the old runner retried a refused duplicate on later
turns, whereas the corrected spell resolves and the SBA immediately restores a legal battlefield.

### Exact post-change semantic/card aggregate

| Occurrences | Card | Exact unresolved Oracle fragment |
| ---: | --- | --- |
| 9 | Leonardo, Big Brother | Sneak `{W}` (full Oracle line) |
| 9 | Leonardo, Big Brother | Leonardo gets +1/+0 for each other creature you control. |
| 8 | April O'Neil, Kunoichi Trainee | When April O'Neil enters, scry 2. (full Oracle line) |
| 8 | April O'Neil, Kunoichi Trainee | April O'Neil can't be blocked by creatures with power 3 or greater. |
| 7 | Raphael, Tough Turtle | Alliance — Whenever another creature you control enters, Raphael deals 1 damage to target opponent. |
| 6 | Prehistoric Pet | This creature can't be blocked by creatures with greater power. |
| 6 | Prehistoric Pet | `{1}{W}, {T}`: Return another target creature you control to its owner's hand. Activate only during your turn. |
| 5 | Mutant Town Musicians | Trample |
| 5 | Mutant Town Musicians | Alliance — another creature enters; this creature gets +1/+0 until end of turn. |
| 5 | Leonardo, Leader in Blue | Sneak `{3}{W}{W}` (full Oracle line) |
| 5 | Leonardo, Leader in Blue | Sneak-paid ETB: creatures you control get +2/+0 until end of turn. |
| 5 | Leonardo, Leader in Blue | `{1}{W}`: Leonardo gains first strike until end of turn. |
| 4 | Wingnut, Bat on the Belfry | Alliance — Wingnut gains flying, menace, or haste until end of turn. |
| 4 | Wingnut, Bat on the Belfry | Whenever Wingnut attacks, each other attacking creature gets +1/+0 until end of turn. |
| 4 | Null Group Biological Assets | During your turn, this creature has first strike. |
| 4 | Null Group Biological Assets | Whenever this creature attacks, you may discard a card; if so, draw a card. |
| 3 each | Raphael, Most Attitude | Menace; Alliance exile-top-card; attack permission to play a card exiled with Raphael. |
| 3 each | Leonardo, Sewer Samurai | Sneak `{2}{W}{W}`; Double strike; graveyard-casting/finality-counter ability. |
| 2 each | Mighty Mutanimals | ETB create a 2/2 Mutant token; Alliance put a +1/+1 counter on a target creature. |
| 2 | Casey Jones, Jury-Rig Justiciar | ETB look at four/reveal an artifact/reorder the rest. |
| 2 each | Lita, Little Orphan Amphibian | Alliance choice header; +1/+1-counter mode; Food-token mode; scry mode. |
| 2 each | Leonardo, Cutting Edge | Sneak `{W}`; Lifelink; life-gain trigger putting a +1/+1 counter on Leonardo. |
| 1 each | Raphael, the Nightwatcher | Sneak `{1}{R}{R}`; attacking creatures have double strike. |

Where a row says "full Oracle line," telemetry retains the complete unabridged `oracle_fragment`;
the table abbreviates only repeated reminder text for readability.

## Remaining-gap ranking after semantic telemetry

Counts are distinct card names matched transparently against the frozen ten-deck roster (102 names)
and the complete versioned `card-model-0.6.json` pool (103 names). A card can appear in multiple
rows; a primitive alone does not necessarily make the whole card executable. Complexity is a
relative implementation estimate, not an outcome-derived score.

| Rank | Gap / candidate primitive | Exact post-change match evidence | Current-roster cards | Full model cards | Complexity | Rationale |
| ---: | --- | --- | ---: | ---: | --- | --- |
| 1 | P/T modification with duration/continuous-effect support | 19 direct fragments: Big Brother 9, Mutant Town Musicians 5, Leader in Blue 5; plus 4 Wingnut attack fragments that also modify P/T | 16 | 16 | Medium–high | Largest observed cluster addressable by a focused effect family; requires duration expiry and continuous/derived P/T rather than mutating base facts |
| 2 | Counter placement/state | 6 direct fragments: Mighty Mutanimals 2, Lita 2, Leonardo Cutting Edge 2 | 25 | 25 | Medium | Greatest roster reach among remaining concrete Actions; finality counters additionally require a replacement effect |
| 3 | Token creation | 4 direct fragments: Mighty Mutanimals 2, Lita 2 | 21 | 21 | Medium | Broad reusable board primitive; needs token identity/ownership and correct disappearance outside the battlefield |
| 4 | Draw/discard/selection Actions | 16 direct fragments: April scry 8, Casey selection 2, Lita scry 2, Null Group rummage 4 | 26 raw matches | 26 raw matches | Medium | Strong exact match evidence, but triggers and modal/conditional sequencing gate several callers |
| 5 | Combat keywords/restrictions | 41 direct fragments across blocking restrictions, trample, first/double strike, menace, lifelink, and Wingnut's keyword choice | 22 | 22 | Medium–high | Highest broad semantic count, but it is multiple rules families rather than one Action |
| 6 | Trigger/event framework | 59 roster cards; many exact fragments above are triggered | 59 | 59 | High | Broadest dependency layer, but not a single card Action and requires event ordering/choice infrastructure |
| 7 | Sneak alternate cost and declare-blockers casting window | 20 direct fragments | 18 | 18 | High | Central set mechanic, blocked by the absent step/priority/stack state machine |
| 8 | Equipment attach/equip | No Equipment resolved in these seeds; 2 acceptance cards in decklists | 6 | 6 | High | Requires attachment legality, continuous effects, activated costs, and state tracking |

### Highest-leverage next target

After implementing the legend rule, the semantic evidence selects **P/T modification with explicit
duration/continuous-effect support** as the next card Action. It is directly present in 19 observed
fragments (23 when Wingnut's team modification is included), affects 16 current-roster/full-model
cards, and forms a reusable prerequisite for several Alliance, ETB, attack, Class, and combat
effects. This is a ranking decision only; that Action is not implemented in 0.7c.

## Engine 0.7d P/T modification validation

Engine `cardcade-0.7.0-alpha.2` keeps printed P/T immutable on `CardFact`, counter state separate on
each permanent, and continuous P/T modifiers as auditable effect records. Persistent derived
modifiers are recomputed after battlefield changes. `Until end of turn` modifiers expire during an
explicit cleanup transition, when marked damage is also removed. Invariants reject invalid counter
quantities, unknown durations, future-dated effects, illegal legend states, controller/zone
mismatches, and surviving creatures with nonpositive toughness.

No card name selects behavior. Four reusable Oracle shapes are recognized: self gets +P/+T per
other creature, Alliance gives this creature +P/+T until end of turn, a sneak-paid ETB gives the
team +P/+T until end of turn, and an attack trigger gives other attackers +P/+T until end of turn.
The sneak-paid condition is evaluated as false while Sneak remains unsupported and is logged as
`pt_effect_condition_not_met`; no bonus is invented.

### Exact 0.7c-to-0.7d replay comparison

| Seed | 0.7c events / pairs | 0.7d events / pairs | 0.7c result | 0.7d result |
| ---: | ---: | ---: | --- | --- |
| 7001 | 19 / 17 | 16 / 14 | Raphael / turn 16 | Raphael / turn 16 |
| 7002 | 30 / 19 | 19 / 11 | Raphael / turn 24 | Leonardo / turn 19 |
| 7003 | 34 / 24 | 22 / 14 | Leonardo / turn 21 | Leonardo / turn 17 |
| 7004 | 31 / 26 | 28 / 23 | Leonardo / turn 23 | Leonardo / turn 21 |
| 7005 | 20 / 12 | 16 / 10 | Raphael / turn 16 | Raphael / turn 16 |
| **Aggregate** | **134 / 34** | **101 / 30** | — | — |

Exactly four baseline fragment pairs leave unsupported telemetry. Three pairs representing 19
baseline events are exercised directly by the five new trajectories. Wingnut's handler is covered
by a deterministic attack regression, but Wingnut does not attack in these changed acceptance
trajectories, so its four baseline events are not claimed as acceptance-executed.

| Baseline events removed | Card | Validation status |
| ---: | --- | --- |
| 9 | Leonardo, Big Brother | Persistent +1/+0 per other creature executed in acceptance |
| 5 | Mutant Town Musicians | Alliance +1/+0 until end of turn executed in acceptance |
| 5 | Leonardo, Leader in Blue | Sneak-paid condition evaluated in acceptance; false because Sneak was not paid |
| **19** | **3 direct pairs** | **Expected direct P/T fragments actually exercised by seeds 7001–7005** |
| 4 | Wingnut, Bat on the Belfry | Generic other-attacker team modifier regression-tested; trigger not encountered post-change |
| **23** | **4 supported pairs** | **All scoped P/T fragments removed from unsupported telemetry** |

The aggregate event reduction is 33 rather than 23 because executed P/T changes alter combat,
deaths, legal power-based targets, game length, and which later cards resolve. Seed 7002 changes
winner and seeds 7002–7004 finish earlier. These are deterministic execution consequences, not
balance evidence.

### Exact post-0.7d unsupported aggregate

| Events | Card | Exact unresolved fragment |
| ---: | --- | --- |
| 9 | Leonardo, Big Brother | Sneak `{W}` (full Oracle line) |
| 8 each | April O'Neil, Kunoichi Trainee | ETB scry 2; can't be blocked by creatures with power 3+ |
| 7 | Raphael, Tough Turtle | Alliance deals 1 damage to target opponent |
| 6 each | Prehistoric Pet | Can't be blocked by creatures with greater power; activated self-bounce of another creature |
| 5 | Mutant Town Musicians | Trample |
| 5 each | Leonardo, Leader in Blue | Sneak `{3}{W}{W}`; activated first strike until end of turn |
| 4 each | Null Group Biological Assets | During-your-turn first strike; attack rummage trigger |
| 3 | Wingnut, Bat on the Belfry | Alliance keyword choice |
| 3 each | Leonardo, Sewer Samurai | Sneak `{2}{W}{W}`; Double strike; graveyard casting/finality counter ability |
| 2 each | Raphael, Most Attitude | Menace; Alliance exile; attack play-from-exile permission |
| 2 | Casey Jones, Jury-Rig Justiciar | ETB artifact selection |
| 2 each | Leonardo, Cutting Edge | Sneak `{W}`; Lifelink; life-gain +1/+1-counter trigger |
| 1 each | Mighty Mutanimals | ETB Mutant token; Alliance +1/+1 counter |
| 1 each | Raphael, the Nightwatcher | Sneak `{1}{R}{R}`; attacking-team double strike |
| 1 each | Lita, Little Orphan Amphibian | Alliance choice header; +1/+1-counter mode; Food-token mode; scry mode |

All table entries retain full unabridged Oracle lines in telemetry; a few repeated reminder clauses
are abbreviated here only for readability.

### New rules dependencies exposed

- Generic event/trigger ordering is now the principal architectural dependency. The supported
  creature-entry and attack hooks execute deterministically, but priority, the stack, APNAP order,
  optional choices, and intervening-if handling remain unsupported.
- Additive P/T is sufficient for these four shapes; set/base P/T, switching power/toughness,
  copy effects, dependency ordering, and the full CR 613 layer system remain explicit gaps.
- Counter storage is separate and invariant-checked, but placing/removing counters is still an
  unsupported Action; finality also requires a replacement effect and exile zone.
- Power changes affect restricted targets and combat legality, exposing the need for broader target
  revalidation and combat keyword/restriction support.
- Sneak-paid team effects cannot become true until the declare-blockers casting window and alternate
  cost machinery exist.

### Post-0.7d ranking and next Action

1. **Blocking-restriction/evasion legality** — 14 exact events (April 8, Prehistoric Pet 6), direct
   combat impact, 12 current-roster/full-model cards, medium complexity, and no trigger prerequisite.
2. **Counter placement/state Action** — 7 exact events across Cutting Edge, Mighty Mutanimals,
   Lita, and Sewer Samurai; 25 roster/model cards; medium complexity, with finality deferred.
3. **Draw/discard/selection Actions** — 15 exact events across April, Casey, Lita, and Null Group;
   26 raw roster/model matches; medium complexity but several callers require triggers or choices.
4. **Sneak alternate cost/window** — 20 exact events and 18 roster/model cards, but high complexity
   because phase steps, priority, stack handling, attacker return, and alternate costs are absent.
5. **Token creation** — 2 exact events in these replays and 21 roster/model cards; medium complexity.

The next selected Action is **blocking-restriction/evasion legality**. It is ranked only; it is not
implemented in 0.7d.

## Engine 0.7e blocking-restriction/evasion validation

Engine `cardcade-0.7.0-alpha.3` implements a reusable Oracle-derived blocker-legality predicate
for the two power-based restriction forms exercised by Acceptance Match #001: a blocker-power
threshold ("power N or greater") and blocker power greater than the attacking creature's current
power. No card name selects either rule. Printed P/T, counters, persistent modifiers, and
until-end-of-turn modifiers continue to feed the current power queried by combat legality.

Both deterministic block generation and explicit block validation call the same predicate.
Automatic block assignment occurs inside combat after attack-triggered P/T effects resolve; the
acceptance runner no longer zips attackers and blockers itself. Combat validation also rejects a
blocker used twice and mappings for permanents that were not declared as attackers. The combat
model remains intentionally one blocker per attacker.

### Exact 0.7d-to-0.7e replay comparison

| Seed | 0.7d events / pairs | 0.7e events / pairs | 0.7d result | 0.7e result |
| ---: | ---: | ---: | --- | --- |
| 7001 | 16 / 14 | 14 / 13 | Raphael / turn 16 | Raphael / turn 16 |
| 7002 | 19 / 11 | 14 / 8 | Leonardo / turn 19 | Leonardo / turn 17 |
| 7003 | 22 / 14 | 19 / 13 | Leonardo / turn 17 | Leonardo / turn 17 |
| 7004 | 28 / 23 | 25 / 21 | Leonardo / turn 21 | Leonardo / turn 21 |
| 7005 | 16 / 10 | 13 / 8 | Raphael / turn 16 | Raphael / turn 16 |
| **Aggregate** | **101 / 30** | **85 / 26** | — | — |

The two targeted exact fragment pairs are absent from 0.7e unsupported telemetry: April O'Neil's
power-3 threshold accounts for eight 0.7d events and Prehistoric Pet's greater-power restriction
accounts for six, so all **14 targeted events** disappear. These semantics are exercised by
deterministic legality regressions and by six actual rejected block candidates in the acceptance
replays: Prehistoric Pet rejects five greater-power candidates across seeds 7002 and 7005, and
April rejects one power-3 candidate in seed 7004.

The aggregate decreases by 16 rather than 14 because legal block changes alter subsequent combat,
deaths, game length, and cards resolved. Seed 7002 ends two turns earlier; winners are unchanged.
These are execution consequences only and are not balance evidence.

### Exact post-0.7e unsupported aggregate

| Events | Card | Exact unresolved fragment |
| ---: | --- | --- |
| 9 | Leonardo, Big Brother | Sneak `{W}` (full Oracle line) |
| 8 | April O'Neil, Kunoichi Trainee | ETB scry 2 |
| 7 | Raphael, Tough Turtle | Alliance deals 1 damage to target opponent |
| 6 | Prehistoric Pet | Activated self-bounce of another creature |
| 5 | Mutant Town Musicians | Trample |
| 5 each | Leonardo, Leader in Blue | Sneak `{3}{W}{W}`; activated first strike until end of turn |
| 4 each | Null Group Biological Assets | During-your-turn first strike; attack rummage trigger |
| 3 | Wingnut, Bat on the Belfry | Alliance keyword choice |
| 3 each | Leonardo, Sewer Samurai | Sneak `{2}{W}{W}`; Double strike; graveyard casting/finality counter ability |
| 2 each | Raphael, Most Attitude | Menace; Alliance exile; attack play-from-exile permission |
| 2 | Casey Jones, Jury-Rig Justiciar | ETB artifact selection |
| 2 each | Leonardo, Cutting Edge | Sneak `{W}`; Lifelink; life-gain +1/+1-counter trigger |
| 1 each | Mighty Mutanimals | ETB Mutant token; Alliance +1/+1 counter |
| 1 each | Raphael, the Nightwatcher | Sneak `{1}{R}{R}`; attacking-team double strike |
| 1 each | Lita, Little Orphan Amphibian | Alliance choice header; +1/+1-counter mode; Food-token mode; scry mode |

Full unabridged Oracle fragments and player/turn/phase/reason context remain in every emitted
`unsupported_semantics` event; descriptions above are abbreviated only for readability.

### New rules dependencies exposed

- Menace and similar blocking requirements require multi-block assignment and whole-declaration
  legality, not another per-pair restriction.
- Flying, reach, shadow, and protection require reusable creature characteristics and keyword
  interaction predicates; none is silently inferred by the two power patterns.
- Declare-blockers priority and Sneak remain absent. Automatic blocker selection is deterministic
  execution scaffolding, not a defending-player strategy or choice model.
- Full combat still lacks blocking requirements, multiple blockers, damage assignment order,
  first/double strike, trample, lifelink, and deathtouch.

### Post-0.7e ranking and next Action/rules capability

1. **Counter placement/state Action** — 7 exact current events across Cutting Edge, Mighty
   Mutanimals, Lita, and Sewer Samurai; 25 roster/model cards; medium complexity. It unlocks a
   reusable state representation already separated from P/T modifiers, while finality replacement
   and exile remain deferred.
2. **Draw/discard/selection Actions** — 15 current events across April, Casey, Lita, and Null Group;
   26 raw roster/model matches; medium complexity, but several call sites require triggers,
   optional choices, ordering, or random-bottom semantics.
3. **Sneak alternate cost/window** — 20 current events and 18 roster/model cards; high complexity
   due to alternate costs, declare-blockers timing, returning an unblocked attacker, and entering
   tapped and attacking.
4. **Combat keyword framework** — 25 current events across first strike, double strike, trample,
   menace, lifelink, and Wingnut's keyword choice; broad combat impact but high complexity because
   multiple combat-damage steps, multi-block declarations, life gain, and duration interact.
5. **Token creation** — 2 current events and 21 roster/model cards; medium complexity, with token
   characteristics and zone-exit behavior required.

The next selected capability is **counter placement/state Action**. This is a telemetry-derived
ranking only; it is not implemented in 0.7e.

## Governance boundary

All Prototype files and Engine 0.1–0.6 code, models, reports, and run artifacts remain preserved.
This reconciliation makes no deck revision, creates no Prototype 0.3, performs no calibration, and
runs no 900-game smoke. Unsupported semantics remain explicit; no gameplay meaning is inferred
from the generic limitation events.
