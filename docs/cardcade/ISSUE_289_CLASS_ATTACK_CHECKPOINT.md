# Issue #289: level-one attack counter checkpoint

## Scope and authority

This checkpoint follows draft PR #330. The ten Baseline 005 deck lists, the original 172-row ledger, all earlier overlays, and historical game evidence remain unchanged. Its recoverable code checkpoint was published at `484b19ad188bb42c865e87fb14a6ec286883927c` before the extended regression run. No control or balance experiment was run.

The frozen four-copy Leonardo card **Leader's Talent** has the following complete printed sections in the authenticated catalog, consistent with the [official release notes](https://magic.wizards.com/en/news/feature/teenage-mutant-ninja-turtles-release-notes):

| Section | Oracle clause | Status after this checkpoint |
| --- | --- | --- |
| Level 1 | Whenever you attack, put a +1/+1 counter on target attacking creature. | Executed |
| Level 2 cost | `{2}{W}: Level 2` | Blocked; child effect incomplete |
| Level 2 effect | Whenever a creature you control leaves the battlefield, if it had a counter on it, you gain 2 life. | Blocked |
| Level 3 cost | `{3}{W}: Level 3` | Blocked; child effect incomplete |
| Level 3 effect | Whenever you cast a spell, put a +1/+1 counter on each creature you control. | Blocked |

The Level 1 clause is a complete, independently executable trigger. It reuses the declared-attack event, priority stack, legal targeting, counter placement, and state-based action paths. The interpreter requires the entire attack clause and its level-one placement; a moved or appended clause fails closed. The later Class levels remain unavailable through the normal activation planner because their full child semantics are not supported.

## Selection and mechanics

| Family | Frozen copies | Affected deck | Assessment |
| --- | ---: | --- | --- |
| Leader's Talent Class | 4 | Leonardo | Five identity clauses, all previously open. The Level 1 attack trigger is a bounded full clause with reuse across attack events. Selected. |
| Splinter tribal modifier | 4 | Splinter | Material continuous +1/+1 to other controlled Ninjas; separate continuous-effect work. |
| Ice Cream Kitty resource activations | 3 | B&R | Two activated abilities with sacrifice, payment, life, and draw; related clauses remain open. |
| Donatello artifact entry counter | 3 | Donatello | Shared artifact-entry provenance and counter trigger; remains open. |
| Mutagen Man artifact-token engine | 2 | B&R | Variable X creation and restricted cost reduction require a separate complete rules path. |

When at least one creature attacks, each authoritative permanent with an active matching printed ability creates a trigger. The source/controller and declared attackers are authenticated against the original rules event. The controller selects a legal attacking creature while the trigger goes on the stack. Both players get priority. The counter is placed only if the same target remains an attacking creature with legal targeting at resolution. The ability resolves independently if its source leaves. Current source ability loss and control changes prevent new triggers. The engine has no card-name or deck-name branch for this behavior.

## Validation and diagnostic evidence

- Six focused tests cover the exact frozen Oracle fixture, incomplete later levels, misplaced/extended text rejection, legal and illegal target choice, stack target identity, source departure, target departure, ability suppression, control change, empty attack, priority, state invariants, and replay equality. The three Class suites together report 19 focused passes.
- Full final-head regression: **1,985 passed, 10 skipped**. GitHub CI is a separate publication gate.
- Ruff check and format on touched Python files, structural Baseline 005 validation, and `git diff --check` passed. The structural validator retains a historical land-count message; this checkpoint neither alters deck inputs nor uses that prose as provenance.
- Six authenticated Baseline 005 diagnostic games, with both seating orders for Leonardo against Splinter, Raphael, and Donatello, had **six matching deterministic replays and zero errors**. They recorded **nine Leader's Talent casts, seven trigger resolutions, and seven counter applications**. Individual seed, seat, event counts, targets, and result digests are in `ISSUE_289_CLASS_ATTACK_SMOKE.json`. The small sample does not support balance conclusions.

Semantic runtime: `a117d25151d99eb19804e42a5873c3a59bf2be26ca49f9edfa63cdc50623e3cf` (predecessor `32dbafe9f3ef612ed49b988ca447af9e85264589574ad635b6c96e30f864e346`). Machine coverage overlay: `ISSUE_289_CLASS_ATTACK_CHECKPOINT.json`; independent calibration assessment: `ISSUE_289_CLASS_ATTACK_CALIBRATION_READINESS.json`. Both preserve row identities and frozen-deck hashes; the source report scripts verify predecessor, original ledger, and manifest digests before writing them.

## Separate gates

**Checkpoint acceptance: READY subject to final-head remote CI.** The full level-one clause is implemented and demonstrated. Later Leader's Talent levels remain deliberately unsupported.

**Baseline 005 calibration readiness: BLOCKED.** The 172-row overlay now has **0 critical, 29 important gaps, 25 calibration blockers, and 4 unbounded important entries**. The remaining Leader's Talent sections and Splinter, Kitty, Donatello, and Mutagen Man mechanics still materially affect deck behavior. The four unbounded entries remain Bebop's Rhino menace, Hamato Guardian Stance's complete effect, Michelangelo Improviser's hand-to-battlefield effect, and Michelangelo Mutant BFF's team blocking limit. The next intervention should assess the remaining Class levels and Splinter's tribal continuous modifier as complete semantic batches, with actual pilot usage measured before any calibration authorization.
