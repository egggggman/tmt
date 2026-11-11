# Diagnostic Game 001 Evidence-Capture Correction

## Handoff status

Implementation candidate is ready for independent synthetic audit. This change does not authorize another diagnostic game.

- Starting source: PR #407 HEAD `fcbe5fbf9419f246663a29467797ed79df57433f`.
- Tested implementation SHA: `c1f889c4fe9ae0db44940ab36fcdb192626d8ba2`.
- Branch: `fix/cardcade-diagnostic-evidence-capture`.
- Accepted `main`: `10d2ac80ef5b81b3a209a3133eb0a84633a1f944`.
- Python 3.12.10; pytest 8.4.2; Ruff 0.16.1.
- Imported runner during tests: `C:\projects\tmt\.cardcade-diagnostic-evidence-capture\src\tmnt_design_studio\stage002.py` (set with `PYTHONPATH` before test execution).

The historical one-shot wrapper and PR #406 artifacts were not modified. A reusable capture owner now lives with the Stage 002 runner, which owns both the authoritative `Game` and the matching presence ledger.

## Preserved RED reproduction

Before implementation, `tests/test_diagnostic_capture.py::test_exception_capture_selects_outer_game_with_matching_presence_ledger` reproduced the old traceback selection rule: retain the last traceback frame with a local named `game`. The test failed because the selected nested frame contained a shadow `game` object and no matching `presence` local. This matches the independently diagnosed PR #406 capture omission.

The correction removes traceback-local discovery. `run_game(..., diagnostic_capture=capture)` explicitly binds its constructed `Game` and matching `_initial_presence` ledger. `capture_diagnostic_call(capture, operation)` records the original exception type, message, and traceback, snapshots that bound game, finalizes a deep copy of its matching presence ledger, and then re-raises the same original exception. Failure to bind state, repeated/ambiguous binding, or snapshot errors are recorded as capture errors; they do not invent a snapshot or replace the original raised exception. If formatting the exception itself fails, the report uses a placeholder and still re-raises the original exception.

## Synthetic validation

All selected test bodies were inspected. The capture integration test monkeypatches the runner immediately after state binding, creates one authenticated token, and raises before the Stage 002 gameplay loop. It verifies the same game fingerprint, exact preexisting ledger preservation, token creation/source identity, authoritative execution indexing, and a reconciliation report without stops. No complete game or runner loop was executed.

Command used at the tested SHA:

```powershell
$env:PYTHONPATH = 'C:\projects\tmt\.cardcade-diagnostic-evidence-capture\src'
$env:PYTHONDONTWRITEBYTECODE = '1'
python -B -m pytest -q <the individually listed nodes below>
```

The 32 named nodes (36 cases including the five provenance parameter cases) were:

- `tests/test_diagnostic_capture.py`: `test_nested_failure_uses_explicit_runner_binding_not_innermost_game_local`, `test_run_game_exception_capture_preserves_presence_and_authenticates_token`, `test_missing_or_ambiguous_runner_binding_fails_closed_without_hiding_error`, `test_capture_finalizes_a_copy_of_presence_without_mutating_live_ledger`.
- `tests/test_strike_damage_steps.py`: `test_lethal_first_strike_damage_ends_without_advancing_terminal_combat`, `test_lethal_regular_damage_ends_without_terminal_transition_or_duplicate_damage`, `test_lethal_first_strike_sba_removes_blocker_before_regular_step`, `test_no_strike_combat_retains_one_regular_damage_step`, `test_combat_damage_steps_cannot_be_skipped_repeated_or_resolved_out_of_order`, `test_failed_transition_does_not_clear_or_fabricate_live_combat_state`.
- `tests/test_stage002_ordinary_priority_windows.py`: `test_empty_beginning_of_combat_offers_both_players_priority`, `test_empty_end_step_offers_both_players_priority_before_cleanup`, `test_existing_open_empty_window_is_not_reopened`, `test_empty_window_does_not_create_stack_objects`, `test_attacker_declaration_waits_for_both_players_to_pass`, `test_blocker_declaration_and_sneak_decline_preserve_priority_before_damage`, `test_legacy_combat_adapter_keeps_explicit_diagnostic_transitions`, `test_postcombat_main_has_ordinary_priority_before_end_step`, `test_defending_player_receives_priority_before_block_choices`, `test_legacy_direct_attacker_action_keeps_original_transition`, `test_legacy_direct_block_action_keeps_original_transition`.
- `tests/test_stage002_runner.py`: `test_runner_drains_damage_created_trigger_without_repeating_damage`, `test_terminal_combat_stops_before_new_trigger_priority_or_resolution`, `test_shared_driver_does_not_drain_priority_after_terminal_state`, `test_nonterminal_combat_with_same_trigger_pattern_drains_normally`, `test_missing_runtime_presence_is_a_silent_approximation_stop`, `test_created_token_presence_uses_authoritative_runtime_namespace`, `test_created_token_presence_is_deterministic_and_definition_distinct`, `test_created_token_presence_preserves_zone_lineage_after_token_ceases`, `test_runtime_token_namespace_reconciles_without_frozen_oracle_identity`, `test_food_token_execution_authenticates_against_exact_runtime_presence`, and `test_food_token_execution_rejects_mismatched_runtime_provenance` (five parameter cases).

Result at `c1f889c4fe9ae0db44940ab36fcdb192626d8ba2`: **36 passed, 0 failed, 0 skipped**. Ruff format check, Ruff lint, and `git diff --check` passed on the three changed Python files.

One existing terminal wrapper test expected the game to advance to `END_OF_COMBAT` after lethal damage. PR #407's accepted invariant intentionally leaves the terminal game at `COMBAT_DAMAGE` and rejects post-terminal transitions. The test expectation was aligned with that accepted behavior and now calls `check_invariants()`; engine combat behavior was not changed in this correction.

## Historical evidence replay

Read-only replay used the original PR #404 source at `67b9bb3083c9f4b2fe02e7fed258c4739581225f`, imported from `C:\projects\tmt\.diag001-pr404-67b9bb3\src\tmnt_design_studio\stage002.py`, with the preserved canonical spec `april-casey:canonical:7231`, saved snapshot, manifest, and reconciliation under:

`C:\projects\tmt\.cardcade-diagnostic001-report\docs\cardcade\diagnostic_game_001\evidence`

Recomputed Stage 002 manifest equaled the saved manifest; `reconcile_snapshot()` returned an object exactly equal to the saved report. All nine files listed in `artifact_sha256.json` matched. The three stop records remain, in order: `illegal_mutation`, `silent_approximation`, `silent_approximation`. No historical artifact or protected archive was changed.

## Remaining limitation and acceptance request

The new capture API must be used by the next authorized diagnostic wrapper: create one `DiagnosticExecutionCapture`, pass it to `run_game`, and wrap that call with `capture_diagnostic_call`. The capture object exposes the exception details and snapshot for persistence while preserving normal exception propagation. The old PR #406 one-shot remains historical evidence and must not be reused as the capture implementation.

Independent acceptance should verify the RED reproduction, exact game/presence binding under nested exceptions, fail-closed missing/ambiguous binding, authentic reconciliation, preservation of the three historical stops, and PR #407 terminal behavior. No complete game, smoke restart, calibration, merge, deck change, or baseline promotion was performed.
