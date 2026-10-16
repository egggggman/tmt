# Issue #289: complete Class level-two departure life

## Authority and selected batch

This checkpoint is stacked on draft PR #331. The ten Baseline 005 decks, original 172-row ledger, all earlier overlays, and historical game results are untouched. Recoverable code was published at `f35701d650d004bb3c0a6cb45cfbdc5f6af21f83` before extended validation. No calibration control was run.

The authenticated frozen catalog and [Wizards' release notes](https://magic.wizards.com/en/news/feature/teenage-mutant-ninja-turtles-release-notes) agree on the four-copy Leonardo **Leader's Talent**: its second section is `{2}{W}: Level 2`, followed by “Whenever a creature you control leaves the battlefield, if it had a counter on it, you gain 2 life.” Its third section is `{3}{W}: Level 3`, followed by a spell-cast +1/+1 counter on each creature you control. The third section remains unimplemented and its level activation remains unavailable.

| Family | Frozen copies | Affected deck | Reason for this selection |
| --- | ---: | --- | --- |
| Leader's Talent level 2 | 4 | Leonardo | Existing Class cost, priority, and permanent-leave paths support one complete activation plus its conditional effect. Selected. |
| Leader's Talent level 3 | 4 | Leonardo | Needs spell-cast team counters and progression through level 2; remains blocked. |
| Splinter's other-Ninja +1/+1 | 4 | Splinter | Separate static tribal combat layer. |
| Ice Cream Kitty activations | 3 | Bebop & Rocksteady | Sacrifice, mana, draw, and life paths; separate resource batch. |
| Donatello artifact-entry counter | 3 | Donatello | Separate shared artifact-entry trigger. |
| Mutagen Man variable X tokens | 2 | Bebop & Rocksteady | Separate variable cost and token batch. |

The new generic parser requires the complete level-two section. The existing Class activation planner handles `{2}{W}` payment, sorcery timing, one-step progression, stack priority, and source state. A creature leave event records its controller, source authority, counter snapshot, and destination. A qualifying active watcher creates a trigger only when the leaving creature had any counter. The trigger retains its original controller and resolves for exactly two life even if its source subsequently leaves or changes control. Ability suppression prevents new triggers. An incomplete or extra Class clause leaves the level closed.

## Validation and observed pilot use

- Focused tests cover authenticated frozen Oracle text, renamed generic fixtures, incomplete section rejection, payment and timing, priority, no counter, any counter type, creature control changes, ability suppression, source departure, a creature Class leaving itself, simultaneous departures, immutable event history, state invariants, and deterministic replay. The activation membership lock was updated for exactly the new frozen Class activation; its previous digests remain in the test history.
- Six authenticated Baseline 005 diagnostic games paired Leonardo's seating against Splinter, Raphael, and Donatello. All six replay digests matched with zero runtime errors. The pilot cast Leader's Talent six times and advanced it to level two four times. **No qualifying countered-creature departure life trigger resolved in this six-game sample.** The focused frozen-card fixture demonstrates that the life effect executes. The diagnostic sample is not balance evidence.
- Full regression: **1,992 passed, 10 skipped**. Ruff, structural validation, and diff checks passed. Final-head GitHub CI remains a publication gate. The structural validator retains historical land-count prose; deck contents and hashes were independently authenticated by the report and smoke scripts.

Semantic runtime: `09fb8cc3eca9944df04109605c39d63a477803bda8d92bff0a93cde3a912af49` (preceding runtime `a117d25151d99eb19804e42a5873c3a59bf2be26ca49f9edfa63cdc50623e3cf`). Reproducible scripts and machine evidence: `report_issue289_class_level_two_life.py`, `run_issue289_class_level_two_smoke.py`, `ISSUE_289_CLASS_LEVEL_TWO_CHECKPOINT.json`, `ISSUE_289_CLASS_LEVEL_TWO_CALIBRATION_READINESS.json`, and `ISSUE_289_CLASS_LEVEL_TWO_SMOKE.json`.

## Separate gates

**Checkpoint acceptance: READY subject to final-head GitHub CI.** Two previously open Oracle rows close: level-two activation and its conditional life effect. The new departure counter snapshot is a general event-provenance correction supporting that coverage; it is not a retroactive balance claim.

**Baseline 005 calibration readiness: BLOCKED.** The 172 rows now include **0 critical, 27 important gaps, 23 calibration blockers, and 4 unbounded important entries**. Leader's Talent level three, Splinter's tribal modifier, Ice Cream Kitty, Donatello, Mutagen Man, and other ranked rows remain unresolved. The four unbounded entries are unchanged: Bebop's Rhino menace, Hamato Guardian Stance's complete effect, Michelangelo Improviser's hand-to-battlefield effect, and Michelangelo Mutant BFF's team blocking restriction. Reassess the complete level-three spell-cast counter batch against Splinter's static tribal effect next, with pilot use measured. Do not infer deck balance from these diagnostics.
