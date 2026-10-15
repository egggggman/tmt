# Issue #289 — controlled-creature departure trigger checkpoint

Stacked on draft PR #320 at `85aeaeac1e3a855590b853db9ece14825ab9bf58`.

## Selection and scope

| Family | Frozen copies / decks | Current missing behavior | Intervention judgment |
| --- | ---: | --- | --- |
| Ninja Teen | 5 / 2 | Level 1 creature-departure life loss; level 2 power/menace; level 3 graveyard Sneak | Shared departure trigger is a complete, bounded rule using existing event provenance and stack handling. Levels 2 and 3 require separate Class activation, continuous effects, and graveyard casting. |
| Does Machines | 4 / 2 | Level 3 activation, counter placement, artifact animation | Larger continuous type/base-stat intervention despite partial existing Class and level 2 support. |
| Shark Shredder, Killer Clone | 4 / 2 | Combat-damage recursion | Two remaining rows but hidden-zone/target and combat timing complexity. |
| Leader's Talent | 4 / 1 | Level 1 attack trigger, level 2 departure/counter life gain, level 3 cast trigger | High impact, multiple distinct effect families and Class activations. |
| Rocksteady / Mouser Foundry / Ravenous Robots | 4 / 1 each | Blocking restrictions or artifact-token engines | Material identity gaps still open. |

The selected complete intervention is the Oracle sentence: “Whenever a creature
you control leaves the battlefield, each opponent loses 1 life.” The actual
[TMNT release notes](https://magic.wizards.com/en/news/feature/teenage-mutant-ninja-turtles-release-notes)
identify Ninja Teen's three levels. Execution parses the effect's amount and
controller relationship from generic Oracle text; card and deck names are not
used for engine dispatch. The engine supports **only this level 1 sentence**:
its level 2 activation and modifier, and level 3 activation and graveyard Sneak
remain explicitly unsupported. The pilot cannot activate those levels.

## Semantic evidence

- A creature leaving the battlefield for graveyard, hand, or exile qualifies
  when its controller at departure controls the watcher. A noncreature or an
  opponent-controlled creature does not. A source creature can trigger from its
  own exit.
- The trigger is placed on the stack with the departing creature's prior
  battlefield identity and the watcher's identity/controller. It waits for
  priority passes; source departure after triggering does not counter it. Each
  opponent loses the Oracle amount on resolution. Simultaneous departures use
  predeparture battlefield snapshots and distinct events.
- Typed event and stack-object provenance is authenticated at trigger creation,
  resolution, and invariant checks. The renamed synthetic fixture executes
  identically; an appended unsupported instruction is rejected.
- **50 focused tests passed** across the new family and neighboring leave-history
  / conditional-entry regressions. Six authenticated frozen-deck diagnostics
  each replayed to an identical digest with zero runtime errors: Splinter–
  Shredder, Splinter–Bebop & Rocksteady, and Shredder–Bebop & Rocksteady, both
  starting positions. They recorded 63 departures and four life-loss executions.
  This is mechanical diagnostic evidence, not balance evidence.

## Coverage and calibration

The [172-row overlay](ISSUE_289_CLASS_DEPARTURE_CHECKPOINT.json) is derived from
the unchanged [prior overlay](ISSUE_289_DISAPPEAR_ENTRY_CHECKPOINT.json) and
closes exactly the two Ninja Teen level 1 rows, one each in Splinter and
Shredder. The separate [calibration assessment](ISSUE_289_CLASS_DEPARTURE_CALIBRATION_READINESS.json)
now records **zero critical gaps, 51 important gaps, 47 blockers, and four
unbounded consequential entries**. No stale row was reclassified without new
execution evidence. The unbounded rows remain Bebop, Warthog Warrior's Rhino
menace grant, Hamato Guardian Stance's combat effect/scry, Michelangelo,
Improviser's combat-damage hand deployment, and Michelangelo, Mutant BFF's
blocking constraint.

Insectoid Exterminator and Michelangelo, Game Master's end-step Disappear
intervening-if rows remain blockers. They share existing full-turn departure
history but need a generic end-step trigger that checks its condition at
trigger creation **and again at resolution**, then executes scry or counter
placement. That is a plausible separate bounded checkpoint, not a closure here.
The next highest scoring gaps are Ninja Teen's unimplemented level 2/3 clauses,
Does Machines' level 3 artifact animation, and Shark Shredder's recursion.

All ten deck contents are authenticated against the frozen Baseline 005 manifest.
Splinter and Michelangelo have LF working-tree line endings but their exact
manifest hashes match after CRLF normalization. No deck, original ledger, earlier
overlay, or historical game file changed. Semantic runtime:
`f24a3c15bbe71ab2e1200bb0685f3dab1ba07908de320a28d49597c674e6ee90`.

Full regression: **1,921 passed, 10 skipped**. Repository Ruff check/format, Baseline 005
structural validation and deterministic diagnostics passed. Final-head CI:
**pending**.

**Checkpoint acceptance: pending final-head CI. Baseline 005 calibration:
BLOCKED.** No 4,500-game control, deck revision, merge, or promotion.
