# Cardcade Menace Fidelity Correction

## Scope and preservation

This checkpoint is a separate review branch from frozen source `fd28f68915c4e7cb6af3444bf41b96608dee712c`. The frozen source, Diagnostic 001/RUN_STOP state, Durable 001 evidence, decks, and historical artifacts were not modified.

The correction is telemetry-only. No gameplay simulation was run.

## Demonstrated engine behavior

The frozen engine already applies the Menace rule at both action generation and execution validation:

- a non-empty assignment with fewer than two blockers is rejected for a Menace attacker;
- blocker object IDs cannot be reused across attackers;
- each blocker must be an untapped authoritative creature controlled by the defender and pass flying/reach and other block restrictions;
- legal multi-block assignments are carried into combat-damage resolution in attacker/blocker order;
- stale or fabricated block actions are rejected on execution.

The frozen synthetic Menace suite passed 18 tests before this correction. Those tests cover one/two/multiple blockers, no-block choices, multiple attackers, combined single-block restrictions, trample, deathtouch, first strike, double strike, and deterministic option ordering.

## Demonstrated evidence gap

The authoritative pilot path calls `legal_block_options()`. Before this correction, that path generated and returned legal blocker choices but did not call the existing opportunity-witness hook. The hook was only reached by the compatibility `generate_blocks()` adapter. Consequently, a real pilot decision could be legal and recorded as `blockers_declared` without a corresponding Menace blocker-opportunity witness.

The correction invokes the existing generic witness hook for each authoritative blocker candidate considered by `legal_block_options()`. Duplicate witnesses remain idempotent through the existing opportunity key. The legacy adapter keeps its rejection telemetry and now witnesses only authoritative creature candidates, preserving its existing behavior.

The selected blocking action remains recorded by the existing `blockers_declared` event. No new inference is made about a choice that was not present in preserved evidence.

## Diagnostic 001 interpretation

The preserved Diagnostic 001 material available at this checkpoint is a fail-closed preflight record: zero games entered the valid smoke matrix because Michelangelo and Splinter deck identities did not authenticate. It contains no authoritative Raphael-vs-Shredder combat state, blocker-option list, selected block assignment, or Menace damage trace. Therefore Diagnostic 001 cannot be interpreted more confidently as evidence for or against a Menace legality defect. The correction improves future evidence capture only.

## Changed files and source identity

- `src/tmnt_design_studio/engine07.py`: witness authoritative blocker candidates from the legal block-option path; retain legacy rejection behavior.
- `tests/test_menace_action.py`: deterministic regression for opportunity witnessing through `legal_block_options()`.
- `CARDCade_MENACE_FIDELITY_CORRECTION.md`: this checkpoint.

Parent source identity: `fd28f68915c4e7cb6af3444bf41b96608dee712c`.

## Validation

- Focused combat/conformance tests: **87 passed**.
- Full regression: **1720 passed, 10 skipped**.
- Ruff: **passed**.
- Ruff format check: **passed**.
- Gameplay simulations: **not run**.

## Remaining limitations

The preserved Diagnostic 001 does not expose the requested combat state, so no retrospective blocker-selection claim is possible. This branch does not add a complete pilot-choice payload or alter combat semantics; it only connects the existing generic witness mechanism to the authoritative legal-action generator. Independent review should verify the resulting witness schema against a separately authorized synthetic or live diagnostic before using Menace outcomes as gameplay evidence.

## Recommendation

**READY FOR INDEPENDENT REVIEW** — Menace legality is supported and regression-tested; the demonstrated gap is bounded to missing blocker-opportunity telemetry. Gameplay remains unauthorized.
