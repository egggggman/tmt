# Issue #289 — generic Class level-two creature anthem checkpoint

Stacked on draft PR #321 at `1b3fa5d3e86fb726dab0dc3a2b810763ae1161cd`.

## Selection and rule authority

| Family | Frozen copies / decks | Existing support | Remaining work / judgment |
| --- | ---: | --- | --- |
| Ninja Teen | 5 / 2 | Level 1 departure trigger | Level 2 is one complete sorcery-speed paid activation and one static +1/+0/menace clause. This checkpoint closes both. Level 3 requires graveyard permission plus Sneak costs and remains open. |
| Does Machines | 4 / 2 | Entry setup and level 2 recovery | Level 3 artifact counters, animation, base P/T and activation remain open. |
| Shark Shredder, Killer Clone | 4 / 2 | Other combat semantics | Combat-damage graveyard recursion remains open; hidden-zone choice and timing add complexity. |
| Leader's Talent | 4 / 1 | Class infrastructure | Level 1 attack, level 2 conditional departure, and level 3 cast triggers remain distinct unsupported payloads. |
| Rocksteady / artifact-token engines | 4 / 1 each | Partial combat / artifact entry | Blocking restriction and token-production consequences remain material. |

The [official TMNT release notes](https://magic.wizards.com/en/news/feature/teenage-mutant-ninja-turtles-release-notes)
confirm Ninja Teen's level 2 costs, +1/+0 and menace grant, level 3 graveyard Sneak text,
and the interaction of menace with a one-blocker maximum. The
[mechanics article](https://magic.wizards.com/en/news/feature/teenage-mutant-ninja-turtles-mechanics)
confirms that gaining a level is a sorcery-speed paid activation, levels are gained
in order, and bonuses from multiple Class permanents stack. The catalog's frozen
Oracle text was used as the acceptance fixture.

## Implementation and validation

- Generic Class parsing requires the complete clause “Creatures you control get
  +N/+M and have menace.” The level activation is executable only if its entire
  relevant child clause executes. Appended unsupported text does not silently
  enable a partially executable Class. The child must occur within its own
  level's Oracle section. No card or deck name is in engine dispatch.
- The existing mana planner, legal-action path, sorcery-speed timing and priority
  stack handle level 2 costs. The level changes only on resolution. Source
  departure before resolution prevents the level change.
- The static modifier is recalculated from currently controlled Class sources
  in the power/toughness modify sublayer, including after creature entry,
  control change, Class source departure, and Aura suppression. Menace uses the
  same block-assignment legality check as other granted keywords. Its layer-6
  grant respects relative timestamps when an Aura removes the recipient's
  abilities. Sources are independent and multiple +1/+0 modifiers stack.
- Focused tests cover payment failure, legal timing, priority, incomplete text,
  a renamed Class, single/two-blocker assignments, unblocked combat damage,
  entering creatures, control and zone changes, overlapping Class sources,
  Aura removal and source ability loss, and deterministic state/event replay.
- A later level advancement keeps the level-2 keyword grant's original
  timestamp. A focused regression proves that an intervening Aura ability-loss
  effect remains authoritative after the Class reaches level 3.
- Six authenticated frozen-deck games (Splinter–Shredder, Splinter–Bebop &
  Rocksteady, Shredder–Bebop & Rocksteady; both starts) replayed to matching
  digests with no runtime errors. At seed 323 they recorded 55 departures,
  three level-1 life-loss resolutions, **six Ninja Teen level-2 advances**, and
  **14 static P/T applications**. These games diagnose execution only; they
  are not balance evidence.

## Coverage and calibration

The unchanged original 172-row ledger and all earlier overlays remain preserved.
The [new overlay](ISSUE_289_CLASS_ANTHEM_CHECKPOINT.json) derives from the exact
#321 predecessor SHA `a9c1a4617bfe039e347d7448eb97639febd84f9586cde7cce5413b4964d2d720`.
It closes exactly four Ninja Teen rows: the level 2 activation and the complete
static modifier, each in Splinter and Shredder. Earlier level-1 dispositions
receive an explanatory text update only; no stale classification is credited.
The separate [risk assessment](ISSUE_289_CLASS_ANTHEM_CALIBRATION_READINESS.json)
records **zero critical, 47 important, 43 calibration blockers, and four
unbounded important gaps**. Ninja Teen level 3's activation and both graveyard
Sneak clauses are still gaps in both decks; the pilot cannot activate level 3
or cast through that missing permission.

Insectoid Exterminator and Michelangelo, Game Master's end-step Disappear rows
remain blockers. They share the existing turn-long departure history and the
end-step intervening-if timing rule, but need trigger-condition checks at both
creation and resolution, with distinct scry and self-counter payloads. Six
frozen copies across two decks justify a **separate bounded checkpoint**.
No residual risk bound was invented for the same four unbounded entries:
Bebop, Warthog Warrior; Hamato Guardian Stance; Michelangelo, Improviser; and
Michelangelo, Mutant BFF.

All ten deck contents authenticate against the unchanged Baseline 005 manifest.
Splinter and Michelangelo have LF checkout line endings and reproduce the
manifest's CRLF hash under normalization; the other eight match byte for byte.
No deck or historical game file changed. Semantic runtime:
`55b75f5adea030cb307dfb3a2bd212d579dce67abe71e98d8452fbf9460ee277`.

Focused semantic suites: **60 passed**. Full regression: **1,928 passed,
10 skipped**.
Repository Ruff check/format and Baseline 005 structural validation passed.
Final-head GitHub CI: **pending**.

**Checkpoint acceptance: pending final-head CI. Baseline 005 calibration:
BLOCKED.** No control, balance experiment, merge, deck revision, or promotion.

## Later publication status (documentation-only addendum)

The preceding “pending” line records the checkpoint's state when this report
was written. GitHub Actions [Test run 38673029398](https://github.com/egggggman/tmt/actions/runs/38673029398)
subsequently completed successfully on PR #322's final published head
`458bebbaf3f4a7ac6b3f09a7aefb21c35a199f8f` (run number 1544).
This addendum changes no test result, runtime, ledger row, deck, or historical
game evidence. Checkpoint acceptance passed its CI gate; Baseline 005
calibration remained **BLOCKED**.
