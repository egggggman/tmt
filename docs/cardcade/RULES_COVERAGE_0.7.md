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
| Creature permanents | CR 110, 302 | Partial: base P/T, tapped state, marked damage, summoning sickness, Haste | casting/combat tests | No counters, tokens, continuous effects, characteristic changes, control changes |
| Reusable Actions | various | Not implemented | none | No Action abstraction; token creation, counters, and P/T modification are absent |
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

## Remaining-gap ranking

Counts are distinct card names matched transparently against the frozen ten-deck roster (102 names)
and the complete versioned `card-model-0.6.json` pool (103 names). A card can appear in multiple
rows; a primitive alone does not necessarily make the whole card executable. Complexity is a
relative implementation estimate, not an outcome-derived score.

| Rank | Gap / candidate primitive | Match evidence | Current-roster cards | Full model cards | Complexity | Rationale |
| ---: | --- | --- | ---: | ---: | --- | --- |
| 1 | Legend-rule state-based Action | 31 exact skips; 3 cards observed, 12 legendary acceptance cards | 35 | 35 | Low–medium | Highest measured current-match disruption and broad applicability; current behavior illegally refuses otherwise castable cards |
| 2 | Trigger/event framework | Generic events on 16 acceptance cards; semantic occurrences unavailable | 59 | 59 | High | Broadest coverage, prerequisite for ETB, Alliance, attack/block, damage, life-gain, and step triggers |
| 3 | Counter placement/state | 5 acceptance cards | 25 | 25 | Medium | High roster reach and prerequisite for Leader's Talent, Lita, Mighty Mutanimals, and Leonardo, Cutting Edge; finality needs replacement handling |
| 4 | Token creation | 4 acceptance cards | 21 | 21 | Medium | Broad, reusable board-state primitive; requires token identity/ownership and zone-exit handling |
| 5 | P/T modification with duration/layers | 8 acceptance cards | 16 | 16 | Medium–high | Strong match relevance, but correct duration and continuous-effect handling are prerequisites |
| 6 | Combat keywords/restrictions | 7 acceptance cards | 22 | 22 | Medium–high | Menace, trample, double strike, lifelink, blocking restrictions, and must-block materially affect combat |
| 7 | Card draw/discard/selection | 8 acceptance cards across draw and selection | 26 raw matches | 26 raw matches | Medium | Reusable zones primitive; modal/conditional clauses and target-player semantics remain separate |
| 8 | Sneak alternate cost and declare-blockers casting window | 8 acceptance cards | 18 | 18 | High | Central set mechanic, but blocked by the absent step/priority/stack state machine |
| 9 | Equipment attach/equip | 2 acceptance cards | 6 | 6 | High | Requires attachment legality, continuous effects, activated costs, and state tracking |

### Highest-leverage next target

The reconciliation selects a **legend-rule state-based Action** as the next isolated target: it
would remove 31 of 90 observed limitation occurrences (34.4%) at relatively low complexity and
applies to 35 current-roster/full-model cards. This is a selection only; no Action is implemented
in this reconciliation. Before broader triggered abilities or Sneak, the engine also needs the
reported-but-absent phase/step and Action architecture established and tested on this branch.

## Governance boundary

All Prototype files and Engine 0.1–0.6 code, models, reports, and run artifacts remain preserved.
This reconciliation makes no deck revision, creates no Prototype 0.3, performs no calibration, and
runs no 900-game smoke. Unsupported semantics remain explicit; no gameplay meaning is inferred
from the generic limitation events.
