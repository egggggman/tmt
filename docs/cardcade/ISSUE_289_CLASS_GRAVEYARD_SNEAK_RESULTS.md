# Issue #289 — Class-granted graveyard Sneak checkpoint

Stacked on draft PR #323. Baseline 005 and its historical simulation results remain frozen.

## Selection and rule execution

The #323 readiness ranking puts Ninja Teen first: five frozen copies across
Splinter and Shredder, represented by six open level-three and graveyard Sneak
rows. Does Machines, Shark Shredder, and Leader's Talent remain consequential
alternatives. Ninja Teen is a bounded intervention using the existing Class
level and Sneak transaction machinery. The
[official release notes](https://magic.wizards.com/en/news/feature/teenage-mutant-ninja-turtles-release-notes)
confirm that its level three grants creature cards in your graveyard sneak
{3}{B} and allows casting those cards using their sneak abilities. A card
with another sneak ability may use either cost.

The interpreter accepts the complete two-clause level-three effect only.
The generic Class activation pays {B} at sorcery timing and resolves through
priority; its static grant is evaluated from current battlefield control and
abilities. During your declare-blockers step, a creature card in your own
graveyard becomes a legal Sneak action only with a current grant, sufficient
legal mana, and an unblocked attacker you control. Multiple applicable Sneak
abilities produce separate legal cost choices. The cost transaction taps mana
sources, returns the attacker to its owner's hand, and moves the original
graveyard card incarnation to the stack. The spell casts with a source-zone
and Class-permission provenance event. The grant may leave afterward without
countering the spell; resolution puts the creature onto the battlefield tapped
and attacking the same defender. Incomplete or modified Class text fails
closed. The implementation does not dispatch on card or deck names.

Focused tests cover level timing/cost/priority, payment shortages, blocked
attackers, stale permissions and zone objects, control changes, alternative
printed/granted costs, spell-cast telemetry, source departure, state
invariants, and deterministic state/event replay. The recognized activation
roster is unchanged; the complete executable roster grows by Ninja Teen's
level-three activation from 46 to 47, with the previous digest retained in
the test.

Six [authenticated frozen-deck diagnostics](ISSUE_289_CLASS_GRAVEYARD_SNEAK_SMOKE.json)
cover Splinter–Shredder, Splinter–Michelangelo, and Michelangelo–Shredder
with balanced starts and exact replays. They contain four level-three
advancements, three graveyard Sneak announcements and three matching
spell-cast events, with zero runtime errors. They are execution evidence, not
balance measurements.

## Coverage and calibration risk

The [overlay](ISSUE_289_CLASS_GRAVEYARD_SNEAK_CHECKPOINT.json) is derived
from exact #323 predecessor SHA-256
`324ee6ffc5b2d45f3e3af3151b5fa6d8938370fe6a00e13f10d8c4aa81212593`.
It closes exactly six Ninja Teen rows in two decks. All 172 row identities
and the original ledger SHA-256
`56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100`
are preserved. All ten unchanged deck contents authenticate against the
Baseline 005 manifest SHA-256
`c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac`.
The semantic runtime identity is
`f292994b9a7b192f0d543297c6a15dc31d81fc25d9a8a4035c692e7850ed3b9d`,
different from #323. Historical games retain their original runtime identity.

The separate [readiness assessment](ISSUE_289_CLASS_GRAVEYARD_SNEAK_CALIBRATION_READINESS.json)
records zero critical gaps, **39 important gaps, 35 calibration blockers,
and four unbounded important entries**. Does Machines (four rows across
Donatello and Krang) and Shark Shredder (two rows across two decks) score
highest next at 42. Leader's Talent has five Leonardo rows at 39.
Rocksteady's blocking restriction and shared artifact-token engines remain
blockers. The four unbounded important entries retain their earlier status
without an unsupported impact claim.

Focused and affected tests: **76 passed** (46 Class/Sneak/identity and 30
activation-roster tests). Full regression: **1,940 passed, 10 skipped**.
Baseline 005 structural validation, repository Ruff check/format, and diff
check: **passed**. Final-head GitHub CI: **pending**.

**Checkpoint acceptance: pending final-head CI. Baseline 005 calibration:
BLOCKED.** No deck revision, calibration control, merge, or promotion occurred.
