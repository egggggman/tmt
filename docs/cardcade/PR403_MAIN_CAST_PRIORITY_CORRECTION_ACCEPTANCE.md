# PR #403 Main-Action Cast / Priority Correction

## Status

**READY FOR independent HQ re-audit.** This is a bounded engine correction candidate only. It does not authorize a complete game, Smoke 001 restart, calibration, merge, deck revision, or baseline promotion.

## Source identity and preservation

- Authorized starting source: PR #401 HEAD `ad2034026d6d37904f66da7ef71874f2306e1571`.
- Worktree: `C:\projects\tmt\.fix-pr403-artifact-cast-priority`.
- Branch: `fix/cardcade-artifact-cast-priority`.
- Accepted `origin/main` observed at `10d2ac80ef5b81b3a209a3133eb0a84633a1f944`.
- PR #403 historical audit source and report were not modified. Its original `tests/test_integrated_readiness_audit.py` blob (`25989bcb14836d7b9908144286814c56b2377620`) was copied into this branch and preserved in the parent commit `a75f3d9157d279f3befd7fe29b9feba3e4aac788` before correction.
- No deck, Baseline 005, Smoke 001 artifact, frozen card-data, or historical evidence was changed.

## Reproduction and correction

The preserved PR #403 characterization reproduced the original state: a legal Pizza CAST action reached `Game.execute_main_action` -> `Game.cast` -> `resolve_top_of_stack`, which raised `ValueError: artifact-cast token trigger requires Priority resolution` after payment and cast announcement. The copied characterization passed by asserting that failure at the unmodified starting source.

Before editing the engine, the new positive acceptance regression failed with the same exception. It is now `tests/test_integrated_readiness_audit.py::test_main_cast_action_composes_punks_followup_robot_trigger_and_pizza_etb`.

`Game.execute_main_action` now calls the existing `announce_spell` contract directly. It finds the authenticated `SPELL_CAST` event for that exact announced stack object and checks whether a `TriggeredAbilityObject` on the Stack references that same event object. If so, it opens the existing priority window and returns without resolving the trigger. If announcement created no cast trigger, it preserves the former immediate main-action resolution behavior. `Game.cast()` itself is unchanged and retains its immediate-resolution compatibility contract. The dispatch contains no card or deck name checks and introduces no priority system.

The positive composition verifies Purple Dragon Punks' single authenticated restricted-red production, Pizza's legal `execute_main_action` cast and exact restricted payment allocation, one Ravenous Robots trigger bound to Pizza's cast event, priority for both players at each successive Stack object, Robot token resolution before Pizza's ETB trigger, the authenticated Pizza trigger, four damage to the chosen opponent and three to the controller, empty final Stack and mana, game invariants, and snapshot/reconciler acceptance without stop records or fabricated damage references.

## Synthetic validation

Environment: Python 3.12.10, pytest 8.4.2, Ruff 0.16.1; reused `C:\projects\tmt\.cardcade-fidelity-correction\.venv`. `PYTHONPATH` pointed to this worktree's `src`; bytecode writes were disabled.

The run included the prior 110 individually named nodes/cases selection, with the PR #403 exception characterization replaced by the positive composition regression. It also included two additional compatibility nodes, for **112 named nodes and 117 reported cases**:

- The 71 accepted pilot/restricted-mana regression nodes listed in `PILOT_FIDELITY_CORRECTION_ACCEPTANCE.md` and `PR399_TARGET_POLICY_CORRECTION_ACCEPTANCE.md`.
- The two PR #402 external reviewer probes: `test_followup_defers_after_pass_and_selects_same_spell_at_later_cast_stage` and `test_pilot_passes_do_not_speculatively_spend_preferred_followup_mana` (from `C:\projects\tmt\.audit-pr401-independent\tests\test_pr401_independent_audit_repro.py`).
- The 14 PR #386 final-fidelity nodes, two combined PR #381/#382/#385 driver nodes, four stop-ledger identity/order nodes, five Food atomicity/payment nodes, the Casey ETB witness node, two Flying/Vigilance nodes, `test_both_priority_windows_and_first_subsequent_upkeep[False-1]`, and all six token-haste nodes.
- The two retained composition nodes, the new positive main-action case and the existing lower-level `announce_spell` composition.
- Two additional casting compatibility nodes: `test_trigger_free_main_cast_still_resolves_with_legacy_compatibility` and `test_game_cast_direct_caller_keeps_immediate_resolution_contract`.

Exact test command form:

```powershell
$env:PYTHONPATH=(Resolve-Path src).Path
$env:PYTHONDONTWRITEBYTECODE='1'
& 'C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\python.exe' -B -m pytest -q --rootdir=. $nodes
```

The explicit `$nodes` selection was assembled from the named nodes above and the 71 nodes in the two referenced acceptance reports. Result at the final tested source commit: **117 passed, 0 failed, 0 skipped**. The 4-node focused composition/compatibility file also passed independently during development. No game runner, complete game, smoke, or calibration path was invoked.

Quality checks on `src/tmnt_design_studio/engine07.py` and `tests/test_integrated_readiness_audit.py`:

```powershell
& 'C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\ruff.exe' format --check src/tmnt_design_studio/engine07.py tests/test_integrated_readiness_audit.py
& 'C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\ruff.exe' check src/tmnt_design_studio/engine07.py tests/test_integrated_readiness_audit.py
git diff --check
```

Ruff format passed, Ruff lint passed, and `git diff --check` passed.

## Limits and handoff

The public `Game.cast()` compatibility wrapper remains immediate-resolution by design; the corrected priority dispatch is specifically the engine-issued `execute_main_action` cast path used by Stage 002. Trigger-free main-action casts retain immediate resolution. The selected synthetic coverage exercises the supported artifact-cast token trigger and Pizza ETB composition, not every possible future cast-trigger family.

This candidate is ready for independent re-audit. It makes no claim of complete-game validation or simulator calibration.
