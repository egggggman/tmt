# Issue 289 — deathtouch semantic checkpoint and Baseline 005 gate

**Cardcade verdict: BLOCKED** for the unchanged 45-cell / 4,500-game control. This checkpoint stacks on the independent acceptance record in draft PR #292, which in turn stacks on #291 and #290. None is merged. There is no new balance sample, deck change, or promotion.

## Authenticated scope

- The [independent review](ISSUE_289_INDEPENDENT_ACCEPTANCE_REVIEW.md) accepted the bounded generic semantics of #290 (`c0ea09ff…`) and #291 (`98a9bf58…`) in order. Historical Combined 007 remains under `d4466241f0ffeaca809cd6a05210ad53b9af1011a1d7f833de88657c1cf00924`.
- This checkpoint's runtime identity is `08a7705c385daf2b1c3e8cfd0da6a303eb7a52ac54aec9dff734a78d76798e3b`. It is incompatible with that historical control. The [machine coverage report](ISSUE_289_READINESS_CHECKPOINT.json) records the full SHA-256 identities of the frozen catalog and Baseline 005 manifest, all 172 original rows, and current execution judgments. The previous ledger remains byte for byte unchanged.
- Only the engine/interpreter, focused tests, a fixed-seed smoke assertion, and reporting files changed. No frozen deck, catalog, schedule, historical evidence, or acceptance PR changed.

## General semantic change

Positive damage to a creature from a source with printed or temporarily granted deathtouch now marks that fact independently of ordinary damage. The state-based action destroys the damaged creature even when damage is below toughness. Cleanup removes the mark. Deathtouch with trample assigns one damage to a blocker before assigning excess to the defending player, including multiple blockers. Damage source characteristics are evaluated at damage time; the recorded lethal result and immutable assignment evidence include the deathtouch fact. A source's name never participates in this calculation. A creature whose abilities have been removed does not contribute printed deathtouch.

The [official rules glossary](https://magic.wizards.com/en/keyword-glossary) describes any positive damage to a creature by a deathtouch source as lethal. [Official Foundations rules notes](https://magic.wizards.com/en/news/feature/foundations-release-notes) confirm the one damage per blocker assignment when trample and deathtouch coexist. This implementation is bounded by the engine's existing deterministic combat assignment policy; it does not claim complete implementation of every possible damage prevention, indestructible, or player-choice combat assignment interaction.

Focused tests use renamed synthetic sources, all four printed deathtouch sources in the frozen roster, larger blockers, two blockers with menace/trample, temporary grants, an ordinary source, cleanup, and replay-equal snapshots. The existing Shredder grant and trample tests pass. The original Donatello–Shredder seed `3004` no longer reaches two artifact entries after the combat correction; seed `3006` deterministically exercises the same payoff. Historical game evidence was not modified.

## Verification and remaining work

- Focused combat group: **51 passed**, including zero-toughness, source-departure, and frozen-card checks. Full regression after the state-based-action correction: **1,663 passed, 10 skipped**; the final five additional checks passed in the focused group afterward. Ruff check and format, diff check, and the Baseline 005 structural validator pass.
- [Diagnostic smoke](ISSUE_289_DEATHTOUCH_DIAGNOSTIC_SMOKE.json): two mirrored frozen Baseline 005 B&R–Shredder games at seed `289`, each replayed exactly; zero runtime errors. These four executions test reproducibility only and do not estimate a matchup rate.
- Six prior P0 entries now have executable deathtouch behavior: five printed keyword rows and the previously partial temporary grant. The remaining original 172-row inventory contains **55 P0**, **71 P1**, **3 partial**, **123 gap**, **33 covered scanner artifacts**, and **7 annotations**. Rows are not distinct mechanics. The report preserves per-row disposition and makes no claim that the remaining important mechanics are immaterial.

Next closure priorities are generic response casting and stack interactions (including Negate), mana abilities and land entry/resource effects, combat legality and required attack drawbacks, and meaningful draw/removal/selection clauses. Then cover class/attachment/token/zone identity effects. The linked Raphael trigger still fails after its source leaves; Illegitimate Business still has tapped-entry/life/multi-color defects. The fixed priority pilot also has unproven nonresponse Flash utilization. These are explicit mechanical blockers, not deck balance findings.

**Readiness threshold:** the four criteria in the independent acceptance review remain in force: no unresolved P0/P1 unless independently proven unreachable in an authenticated schedule, rule and pilot fidelity with deterministic cases, one frozen regression-validated semantic runtime, and separate HQ authorization for a new unchanged balanced-start control. Do not interpret Combined 007 rates under this runtime or run 4,500 games now. Return mechanical findings to Design Studio; it retains deck-design authority.
