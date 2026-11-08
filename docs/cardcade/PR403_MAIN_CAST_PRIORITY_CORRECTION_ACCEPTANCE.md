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

For the 41 supplemental nodes, the exact selection was:

```text
C:\projects\tmt\.audit-pr401-independent\tests\test_pr401_independent_audit_repro.py::test_followup_defers_after_pass_and_selects_same_spell_at_later_cast_stage
C:\projects\tmt\.audit-pr401-independent\tests\test_pr401_independent_audit_repro.py::test_pilot_passes_do_not_speculatively_spend_preferred_followup_mana
tests/test_pr386_final_fidelity_gate.py::test_transition_rejects_open_empty_priority_window_before_passes
tests/test_pr386_final_fidelity_gate.py::test_transition_rejects_open_empty_priority_window_after_one_pass
tests/test_pr386_final_fidelity_gate.py::test_transition_rejects_two_passes_until_empty_window_closure_is_processed
tests/test_pr386_final_fidelity_gate.py::test_priority_action_from_closed_epoch_is_rejected_without_mutation
tests/test_pr386_final_fidelity_gate.py::test_stack_resolution_and_legacy_combat_transitions_remain_valid
tests/test_pr386_final_fidelity_gate.py::test_natural_tunnel_rats_execution_authenticates_through_reconciler
tests/test_pr386_final_fidelity_gate.py::test_frog_mana_action_produces_pays_and_expires_with_authenticated_lineage
tests/test_pr386_final_fidelity_gate.py::test_frog_mana_ability_is_an_immediate_priority_action_with_color_choice
tests/test_pr386_final_fidelity_gate.py::test_defender_reach_execution_authenticates_before_block_declaration
tests/test_pr386_final_fidelity_gate.py::test_fugitive_droid_controller_specific_entry_restriction_survives_reconcile
tests/test_pr386_final_fidelity_gate.py::test_follow_on_empty_priority_after_resolution_can_execute_reach
tests/test_pr386_final_fidelity_gate.py::test_existing_main_action_policy_runs_during_postcombat_main
tests/test_pr386_final_fidelity_gate.py::test_full_combat_priority_and_sneak_sequence_uses_fresh_epochs
tests/test_pr386_final_fidelity_gate.py::test_priority_driver_stops_prompting_after_winner
tests/test_combined_pr381_pr382_pr385_integration.py::test_stage002_naturally_offers_tunnel_rats_at_empty_end_step_priority
tests/test_combined_pr381_pr382_pr385_integration.py::test_frog_reach_is_available_after_attackers_before_blockers_on_empty_stack
tests/test_cardcade_stage002_silent_stop_ledger.py::test_raw_stops_keep_exact_indices_and_derived_stops_keep_distinct_identity
tests/test_cardcade_stage002_silent_stop_ledger.py::test_inserted_reconciler_stop_before_raw_suffix_is_rejected
tests/test_cardcade_stage002_silent_stop_ledger.py::test_reordered_reconciler_raw_stops_are_rejected
tests/test_cardcade_stage002_silent_stop_ledger.py::test_omitted_reconciler_raw_stop_is_rejected
tests/test_food_action.py::test_food_activation_uses_atomic_cost_stack_priority_and_life_result
tests/test_food_action.py::test_insufficient_mana_or_tapped_food_generates_no_activation
tests/test_food_action.py::test_wrong_controller_and_nonfood_source_are_not_legal
tests/test_food_action.py::test_fabricated_equal_valued_and_stale_sources_fail_without_mutation
tests/test_food_action.py::test_duplicate_activation_and_payment_are_rejected
tests/test_smoke001_semantic_triage.py::test_casey_witness_marker_can_coexist_with_authenticated_resolving_etb
tests/test_flying_action.py::test_vigilance_attacker_remains_untapped_after_attack
tests/test_flying_action.py::test_flying_vigilance_keyword_line_is_not_reported_as_unsupported
tests/test_vigilante_upkeep_action.py::test_both_priority_windows_and_first_subsequent_upkeep[False-1]
tests/test_token_haste_action.py::test_exact_recognizer_and_neighbor
tests/test_token_haste_action.py::test_payment_stack_and_resolution_time_recipient
tests/test_token_haste_action.py::test_source_leaving_does_not_cancel_effect_and_filters_recipients
tests/test_token_haste_action.py::test_insufficient_mana_or_tapped_source_fails_without_mutation
tests/test_token_haste_action.py::test_exclusions_and_cleanup
tests/test_token_haste_action.py::test_tapped_source_cannot_activate
tests/test_integrated_readiness_audit.py::test_announce_spell_composes_punks_payment_robot_trigger_and_pizza_etb
tests/test_integrated_readiness_audit.py::test_main_cast_action_composes_punks_followup_robot_trigger_and_pizza_etb
tests/test_integrated_readiness_audit.py::test_trigger_free_main_cast_still_resolves_with_legacy_compatibility
tests/test_integrated_readiness_audit.py::test_game_cast_direct_caller_keeps_immediate-resolution-contract
```

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
