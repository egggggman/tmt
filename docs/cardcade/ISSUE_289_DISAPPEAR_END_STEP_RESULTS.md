# Issue #289 — end-step Disappear checkpoint

Stacked on draft PR #322 at `458bebbaf3f4a7ac6b3f09a7aefb21c35a199f8f`.

## Selection and semantics

The frozen Baseline 005 catalog has three copies each of Insectoid Exterminator
(Splinter) and Michelangelo, Game Master (Michelangelo). Both clauses say that at
the beginning of *your* end step, if a permanent left the battlefield under
your control this turn, an effect occurs. The former scries 1; the latter puts
a +1/+1 counter on itself. The prior checkpoint already records full-turn
departure-time controller history, including stolen permanents and departures
before the source entered. These six copies across two decks make one bounded,
shared trigger intervention.
The [official release notes](https://magic.wizards.com/en/news/feature/teenage-mutant-ninja-turtles-release-notes)
confirm Michelangelo's wording and the intervening-if creation rule; the
[mechanics article](https://magic.wizards.com/en/news/feature/teenage-mutant-ninja-turtles-mechanics)
confirms Disappear looks back through the entire turn.

The interpreter accepts the entire end-step sentence, verifies any recipient
is an Oracle self-reference, and rejects unsupported appended instructions.
The ordinary end-step event queues each ability only when the history condition
holds; the stack gives both players priority before resolution. The original
trigger controller rechecks the condition on resolution. Scry uses the existing
transactional library choice and provenance; counters use the ordinary
placement and state-based-action path on the original battlefield object. A
source leaving does not cancel the scry trigger; a departed source cannot
receive its self counter. Aura ability loss removes the printed ability from
the source's evaluated rules text. No card or deck name appears in dispatch.

Focused tests cover exact and incomplete parsing, prior departure under a
different owner, opponent departure, turn expiration, stack priority,
controller changes, source departure and replacement object identity, both
scry top/bottom choices, invalid transactional choices, resolution recheck,
counter P/T, invariants, and deterministic state/event replay. A synthetic
history removal tests the resolution guard because real within-turn departure
history is monotone. It is not treated as a legal game transition.
The scry coverage helper now reports the conditional parent executable as
well. The current-runtime scry roster assertion includes Insectoid while
retaining and checking the earlier two-card digest; recognized card and
payload membership are unchanged.

Six authenticated frozen-deck diagnostics (Splinter–Shredder,
Splinter–Michelangelo, Michelangelo–Shredder; balanced starts) and six replays
matched digests without runtime errors. Seeds are recorded individually in the
[smoke evidence](ISSUE_289_DISAPPEAR_END_STEP_SMOKE.json). The games recorded
59 permanent departures, five completed conditional end-step triggers, three
conditional scry resolutions, and two conditional self-counter placements.
These are execution diagnostics, not balance measurements.

## Coverage and readiness

The [overlay](ISSUE_289_DISAPPEAR_END_STEP_CHECKPOINT.json) derives from exact
#322 predecessor SHA `344c738abb1f59c73e21daa1e24feb6c32d43484a8f3a7dad24478aa1417807c`.
It closes precisely the two complete Disappear rows and preserves all 172
original row identities. The unchanged original ledger SHA-256 is
`56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100`;
the unchanged Baseline 005 manifest SHA-256 is
`c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac`.
All ten deck contents authenticate against the manifest. The new semantic
runtime is `36d552befdbe3f6ae227649644528fa5661532b92a95ee64d92b03982c2bc4dd`.

The independent [calibration assessment](ISSUE_289_DISAPPEAR_END_STEP_CALIBRATION_READINESS.json)
has zero critical gaps, **45 important gaps, 41 calibration blockers, and four
unbounded important entries**. Ninja Teen's level 3 and graveyard Sneak remain
six open rows across Splinter and Shredder; Does Machines has four open rows
across Donatello and Krang; Leader's Talent has five in Leonardo. Other
high-impact gaps include Shark Shredder's graveyard recursion, Rocksteady's
combat restriction, and artifact-token engines. Complete Class effects remain
blockers. The four unbounded entries retain their prior classification.

Focused and affected semantic suites: **73 passed**. Full regression:
**1,934 passed, 10 skipped**. Structural validation and repository Ruff
check/format: **passed**. Final-head GitHub CI: **pending**.

**Checkpoint acceptance: pending final-head CI. Baseline 005 calibration:
BLOCKED.** No deck revision, control, balance interpretation, merge, or
promotion occurred.
