# Issue #289: generic subtype team P/T modifier

## Authority and selection

This checkpoint is stacked on draft PR #333. Baseline 005, the original 172-row ledger, earlier overlays, and historical game evidence are untouched. Recoverable code was published at `e846bf2e8d792b5156172f4390457d6546d50340` before extended validation. No calibration control was run.

The authenticated frozen catalog has four copies of **Splinter, Hamato Yoshi** in the Splinter deck. His complete clause is “Other Ninjas you control get +1/+1.” The general static P/T engine already recalculated controlled “other artifact creatures” from authoritative battlefield state. Extending the parser and recipient predicate to a regular creature subtype makes this one complete clause executable in the ordinary P/T modification layer.

| Family | Frozen copies | Affected deck | Decision |
| --- | ---: | --- | --- |
| Splinter controlled Ninja modifier | 4 | Splinter | Selected: one complete static clause through an existing recalculation path, with meaningful combat and toughness effects. |
| Ice Cream Kitty resource activations | 3 | Bebop & Rocksteady | Open: separate sacrifice costs, timing, draw, tap, and life effects. |
| Donatello artifact-entry counter | 3 | Donatello | Open: an existing generic trigger executes in some cases, but wrongly requires the entering artifact to remain on the battlefield at resolution. Reproduced by removing that artifact before resolving the trigger; no counter was placed. This is incomplete Oracle coverage, not a newly closed row. |
| Mutagen Man variable-X token engine | 2 | Bebop & Rocksteady | Open: variable payment and token quantity; separate intervention. |

The new parser derives a regular subtype from the Oracle plural; ambiguous irregular plurals fail closed. A static source buffs only **other** controlled creatures whose current battlefield type line contains that subtype. It does not target or use the stack. Recalculation follows entry, departure, subtype changes, Aura ability suppression, and control changes. The latter required a small general engine correction: `change_controller` now refreshes continuous P/T immediately. Each contribution remains in the normal additive P/T layer alongside counters and other static modifiers; departure can expose lethal damage to state-based actions.

## Tests and pilot observation

- Focused tests include the actual frozen card and renamed fixtures, exact complete parsing, irregular or extra-clause rejection, Ninja and non-Ninja recipients, source exclusion, stacking, type and control changes, Aura suppression/removal, source exit/reentry, combat blocking legality, lethal damage after lost toughness, and deterministic replay. Earlier artifact-team and Class continuous-effect tests pass.
- Six authenticated Baseline 005 diagnostic games pair Splinter against Leonardo, Raphael, and Donatello with balanced seats. All six replays matched and had zero runtime errors. The pilot cast Splinter **eight** times. Its specific modifier recorded **13 applications and 9 removals**. These are usage and provenance observations, not balance measurements.
- Full regression: **2,002 passed, 10 skipped**. Ruff, structural validation, and diff checks passed locally. Final-head GitHub CI is a separate publication gate. The historical Baseline 005 validator still prints old land-count prose; the machine report and smoke script independently authenticate all ten frozen deck hashes.

Semantic runtime: `bd3262a9787b5568ce6f9208d95c3e89eefbe5792319eab21e110c069eadb018` (previous `402aeb7a5a2c1cb574fcc455f7eef229c9516794050cd7814fd76cf6e69d3ee4`). Reproduce with `tools/report_issue289_static_subtype_team.py` and `tools/run_issue289_static_subtype_smoke.py`. The separate machine files are `ISSUE_289_STATIC_SUBTYPE_CHECKPOINT.json`, `ISSUE_289_STATIC_SUBTYPE_CALIBRATION_READINESS.json`, and `ISSUE_289_STATIC_SUBTYPE_SMOKE.json`.

## Separate gates

**Checkpoint acceptance: subject to final-head CI.** One important row closes: Splinter's complete controlled Ninja modifier. The control-change refresh is a general simulator defect correction and does not retroactively validate balance results.

**Baseline 005 calibration readiness: BLOCKED.** All 172 ledger identities remain; **0 critical, 24 important, 20 calibration blockers, and 4 unbounded important entries** remain. Ice Cream Kitty, Donatello, Mutagen Man, and other ranked mechanics remain open. The same four unbounded entries remain open: Bebop's Rhino menace, Hamato Guardian Stance's complete effect, Michelangelo Improviser's hand-to-battlefield effect, and Michelangelo Mutant BFF's team blocking restriction. No deck revision, control, merge, or promotion follows from this checkpoint.
