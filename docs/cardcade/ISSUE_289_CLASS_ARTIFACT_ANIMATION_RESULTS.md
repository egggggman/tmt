# Issue #289 — Class combat artifact-animation checkpoint

Stacked on draft PR #324. Baseline 005 decks and historical evidence remain frozen.

## Selection

The #324 172-row assessment ranks Does Machines and Shark Shredder at 42
each: both have four frozen copies across two decks. Does Machines has two
open clauses in Donatello (three copies) and Krang (one): the level-three
activation and beginning-of-combat targeted artifact effect. Shark
Shredder's two rows affect Shredder and Splinter, but require a selected
opponent graveyard card to enter tapped and attacking after either combat
damage step, including first-strike timing. Does Machines reuses the
existing Class payment/progression, counter placement, targeting, type
effects, P/T layers, and Equipment attachment rules. It is the smaller
complete implementation among the tied high-impact families.

Leader's Talent (four copies, five open clauses) ranks 39 and needs several
distinct Class triggers. Rocksteady's four-copy blocking constraint and the
four-copy artifact-token engines in Casey rank 36. They remain open. The
[official release notes](https://magic.wizards.com/en/news/feature/teenage-mutant-ninja-turtles-release-notes)
confirm Does Machines's exact effect, lasting 0/0 animation, retained
types/abilities, Equipment detachment, and continuous-control attack timing.

## Generic execution and evidence

The interpreter accepts the entire level-three section and rejects extra
or misplaced clauses. The normal payable Class action advances to level 3
at sorcery timing through the stack. At the beginning of its controller's
combat, the active level-three Class creates a triggered ability; a legal
artifact that controller controls is targeted when it goes on the stack.
Both players receive priority. On resolution, the target is checked again.
The effect places three +1/+1 counters. If the artifact is not already a
creature, a persistent layer-four Creature/Robot addition and layer-7b
base 0/0 effect apply. Existing types, abilities, and counters remain.
An animated Equipment becomes unattached; the effect survives its Class
source leaving and survives cleanup, but a zone change creates a new
object. The pilot's deterministic target ordering favors a noncreature
artifact and otherwise uses stable object IDs. No card-name or deck-name
execution branch was added.

The accepted smoke and Stage 002 drivers now drain the beginning-of-combat
priority window before attacker declaration. An affected frozen Donatello
seed exposed that runner requirement; it passes after the correction.
Focused tests cover exact/incomplete parsing, activation payment and
timing, trigger targeting and priority, source departure, target loss and
control change, already-creature behavior, layer/counter ordering,
Equipment detachment, persistent duration and zone identity, opponent
combat exclusion, invariants, and deterministic state/event replay.
The historical activation roster digest remains recorded; this runtime
adds one complete Does Machines activation, bringing the executable
catalog entries from 47 to 48.

Six [authenticated frozen-deck diagnostics](ISSUE_289_CLASS_ARTIFACT_ANIMATION_SMOKE.json)
cover Donatello–Shredder, Krang–Shredder, and Donatello–Krang with balanced
starts. Six exact replays matched. They observed seven level-three
advancements, 19 legal combat targets and resolutions, two persistent
animations, and zero runtime errors. These are execution diagnostics,
not balance results.

## Coverage and readiness

The [overlay](ISSUE_289_CLASS_ARTIFACT_ANIMATION_CHECKPOINT.json) derives
from exact #324 predecessor SHA-256
`d0d5b21dba7bea6854520b67d5affbb365e009bb9f1aeed7be7bcfeb26e5a2a0`.
It closes exactly four Does Machines rows. All 172 original row identities
and the original ledger SHA-256
`56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100`
are preserved. All ten frozen deck contents authenticate against the
Baseline 005 manifest SHA-256
`c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac`.
The new semantic runtime is
`a95807a7bf0a8a87b78155c425fe275da8b223190941e167d859ecf9f90902d9`.
Earlier checkpoint and game runtime identities are unchanged.

The separate [calibration assessment](ISSUE_289_CLASS_ARTIFACT_ANIMATION_CALIBRATION_READINESS.json)
records zero critical gaps, **35 important gaps, 31 calibration blockers,
and four unbounded important entries**. Shark Shredder is next at 42,
followed by Leader's Talent at 39. Rocksteady and shared artifact-token
engines remain at 36. The four unbounded entries retain their prior
classification until their impact is established; none was closed by
reclassification.

Focused and affected suites: **58 passed**. Full regression: **1,946
passed, 10 skipped**. Baseline 005 structural validation, repository Ruff
check/format, and diff check: **passed**. Final-head GitHub CI: **pending**.

**Checkpoint acceptance: pending final-head CI. Baseline 005 calibration:
BLOCKED.** No deck revision, 4,500-game control, merge, or promotion occurred.
