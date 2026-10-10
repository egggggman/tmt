# Issue 289 — land entry and payment checkpoint

**HQ recommendation: BLOCKED** for the unchanged Baseline 005 45-cell / 4,500-game control. This checkpoint stacks on CI-green draft [PR #294](https://github.com/egggggman/tmt/pull/294), itself stacked on validated #293 and the preceding #290–#292. No accepted deck list, historical simulation, catalog, or prior ledger was changed.

## Immutable inputs and runtime

The [original 172-row ledger](ISSUE_289_COVERAGE_LEDGER.csv) retains SHA-256 `56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100`. The [#294 checkpoint](ISSUE_289_CRITICAL_SEMANTICS_CHECKPOINT.json) retains SHA-256 `dae33999c1e1bc6351b3c120ce32ad1b4675288c42c5c1575180b6b292d6cd1d` and runtime `57b01e4af5cd15a995e527da26cc7f017441a8df030d66a64bb189159198d72f`. The [new full-row overlay](ISSUE_289_LAND_SEMANTICS_CHECKPOINT.json) preserves both and records the new runtime `26a20e23ec621f492a7e4cf980ec431b0349bd520816baafbd9e9b72150a4c11`. Neither historical Combined 007 nor #293/#294 control evidence is runtime-compatible.

| Execution judgment | #294 | This checkpoint |
|---|---:|---:|
| Critical P0 | 50 | **46** |
| Important P1 | 71 | **71** |
| Partial | 3 | **2** |
| Gap | 118 | **115** |
| Supported by overlays | 11 | **15** |
| Prior covered / annotation | 33 / 7 | **33 / 7** |

Four B&R Illegitimate Business ledger entries close: its unconditional tapped entry, two scanner reasons for the same one-life ETB clause, and the partial black/green mana output. This is **three distinct printed clauses across two frozen copies**, not four independent cards. The code recognizes generic printed permanent entry and land mana clauses, with no land/card/deck name dispatch beyond the engine's existing basic-land mana mapping. Tapped status is applied on battlefield entry before the land can pay a cost. The life trigger is authenticated against a permanent-entry event and resolves after both players pass; source departure after triggering does not erase it. Payment can select any one printed color, backtracks over alternative lands/floating mana, and taps each selected source once. It does not claim standalone mana-pool activation outside the established payment abstraction.

Focused tests cover frozen and renamed land facts, tapped availability, life and priority ordering, departed source, black and green casting, a case where greedy dual-land spending would falsely reject `{B}{G}`, state invariants, and exact snapshot/event replay. The stage manifest's semantic coverage now recognizes the generic paid mana clause, preserving the invariant that a clause without limitations is reported as fully supported. The two mirrored frozen B&R/April diagnostic games and replays matched exactly without runtime errors ([machine smoke record](ISSUE_289_LAND_SEMANTICS_SMOKE.json)); neither seed played Illegitimate Business, so actual execution proof comes from the focused frozen-card tests. Full regression **1,686 passed, 10 skipped**; Ruff check/format, diff check, and unchanged Baseline 005 structural validation passed. That validator still prints stale land-count prose; its text is not used as provenance.

## Remaining material gaps

The 46 P0 rows are still concentrated in shared interaction/combat, resource selection, and deck identity. The next intervention should address shared high-copy spells with executable targeting and resolution, especially **Stomped by the Foot** across Splinter/Shredder/B&R and **Cowabunga!** across Michelangelo/B&R, then the common Mutant Chain Reaction and Spicy Oatmeal Pizza effects. Raphael's linked exile under source departure, Cool but Rude, B&R's attack/block discard-or-sacrifice obligation, and April Hacktivist's end-step draw remain severe identity gaps. The complete machine overlay retains all P0/P1 rows and the two remaining partial cases.

No new balance claim follows from these diagnostics. Design Studio owns deck decisions; Cardcade must close or otherwise prove immaterial the remaining gameplay-bearing gaps before HQ considers a new unchanged control.
