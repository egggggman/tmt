# Diagnostic Capture Lifecycle Correction

## Handoff

Bounded implementation candidate for independent audit. This change does not authorize a diagnostic game.

- Starting source: PR #411 HEAD `b0c5097d56574321200e210a139a58d0ba320648`.
- Tested implementation SHA: `b1c089476b47f032b63d169b7dedcb69d85afaee`.
- Implementation commit: `fc65e3f1715d670c28a6176c254683b64c100eaf`; final test-only commit is `b1c0894`.
- Branch/worktree: `fix/cardcade-diagnostic-capture-lifecycle` / `C:\projects\tmt\.cardcade-diagnostic-capture-lifecycle`.
- Python 3.12.10; pytest 8.4.2; Ruff 0.16.1.
- Test import path: `C:\projects\tmt\.cardcade-diagnostic-capture-lifecycle\src\tmnt_design_studio\stage002.py`, confirmed with `PYTHONPATH` pinned to this worktree.
- Accepted `main`: `10d2ac80ef5b81b3a209a3133eb0a84633a1f944`.

Only the capture helper and its synthetic tests changed. The PR #407 terminal engine source is unchanged. No complete game or gameplay loop was run.

## Preserved RED

At the starting SHA `b0c5097d56574321200e210a139a58d0ba320648`, these new deterministic regressions failed before the implementation change:

```powershell
$env:PYTHONPATH = 'C:\projects\tmt\.cardcade-diagnostic-capture-lifecycle\src'
$env:PYTHONDONTWRITEBYTECODE = '1'
python -B -m pytest -q `
  tests/test_diagnostic_capture.py::test_reused_capture_does_not_attach_previous_game_to_unbound_failure `
  tests/test_diagnostic_capture.py::test_unprintable_snapshot_capture_error_does_not_mask_original_exception
```

Result: **2 failed**. The first found the previous game's snapshot attached to a later unbound error. The second showed an unprintable snapshot exception's `__str__` raising from capture-error formatting, replacing the original execution exception and leaving `capture.failure` unset.

## Correction

`capture_diagnostic_call` now starts and finishes a fresh lifecycle for every invocation. Starting a call clears the previous failure and any bound game/presence references. `DiagnosticExecutionCapture.bind()` is permitted only during that call; a second binding is marked ambiguous, cleared, and rejected. On failure, a missing or duplicate binding yields exception details with no snapshot. On successful non-game calls, no binding is required and prior failure state remains cleared.

Capture formatting is fail-safe. Message and traceback formatting have guarded fallbacks; snapshot and presence-finalization errors are recorded using safe formatting; and the wrapper has a final fallback if capture bookkeeping itself raises. The original execution exception is re-raised by identity in every tested failure path. Game/presence references are cleared on exit so they cannot be reused by a later invocation.

## Synthetic validation

All selected tests are deterministic, named, and non-game. The injected `run_game` test raises immediately after runner state binding and before the gameplay loop. It validates the authoritative game fingerprint, exact live-ledger preservation, token event/source identity, execution indexing, and successful reconciliation authentication. A separate no-capture runner test injects a setup exception before the loop and verifies ordinary exception propagation.

The existing PR #411 selection contained 32 named nodes and 36 cases. This run executed those nodes plus six new lifecycle/error-boundary nodes: **38 named nodes, 42 cases**.

The command used at `b1c089476b47f032b63d169b7dedcb69d85afaee` was:

```powershell
$env:PYTHONPATH = 'C:\projects\tmt\.cardcade-diagnostic-capture-lifecycle\src'
$env:PYTHONDONTWRITEBYTECODE = '1'
$nodes = @(
  'tests/test_diagnostic_capture.py',
  'tests/test_strike_damage_steps.py::test_lethal_first_strike_damage_ends_without_advancing_terminal_combat',
  'tests/test_strike_damage_steps.py::test_lethal_regular_damage_ends_without_terminal_transition_or_duplicate_damage',
  'tests/test_strike_damage_steps.py::test_lethal_first_strike_sba_removes_blocker_before_regular_step',
  'tests/test_strike_damage_steps.py::test_no_strike_combat_retains_one_regular_damage_step',
  'tests/test_strike_damage_steps.py::test_combat_damage_steps_cannot_be_skipped_repeated_or_resolved_out_of_order',
  'tests/test_strike_damage_steps.py::test_failed_transition_does_not_clear_or_fabricate_live_combat_state',
  'tests/test_stage002_ordinary_priority_windows.py::test_empty_beginning_of_combat_offers_both_players_priority',
  'tests/test_stage002_ordinary_priority_windows.py::test_empty_end_step_offers_both_players_priority_before_cleanup',
  'tests/test_stage002_ordinary_priority_windows.py::test_existing_open_empty_window_is_not_reopened',
  'tests/test_stage002_ordinary_priority_windows.py::test_empty_window_does_not_create_stack_objects',
  'tests/test_stage002_ordinary_priority_windows.py::test_attacker_declaration_waits_for_both_players_to_pass',
  'tests/test_stage002_ordinary_priority_windows.py::test_blocker_declaration_and_sneak_decline_preserve_priority_before_damage',
  'tests/test_stage002_ordinary_priority_windows.py::test_legacy_combat_adapter_keeps_explicit_diagnostic_transitions',
  'tests/test_stage002_ordinary_priority_windows.py::test_postcombat_main_has_ordinary_priority_before_end_step',
  'tests/test_stage002_ordinary_priority_windows.py::test_defending_player_receives_priority_before_block_choices',
  'tests/test_stage002_ordinary_priority_windows.py::test_legacy_direct_attacker_action_keeps_original_transition',
  'tests/test_stage002_ordinary_priority_windows.py::test_legacy_direct_block_action_keeps_original_transition',
  'tests/test_stage002_runner.py::test_runner_drains_damage_created_trigger_without_repeating_damage',
  'tests/test_stage002_runner.py::test_terminal_combat_stops_before_new_trigger_priority_or_resolution',
  'tests/test_stage002_runner.py::test_shared_driver_does_not_drain_priority_after_terminal_state',
  'tests/test_stage002_runner.py::test_nonterminal_combat_with_same_trigger_pattern_drains_normally',
  'tests/test_stage002_runner.py::test_missing_runtime_presence_is_a_silent_approximation_stop',
  'tests/test_stage002_runner.py::test_created_token_presence_uses_authoritative_runtime_namespace',
  'tests/test_stage002_runner.py::test_created_token_presence_is_deterministic_and_definition_distinct',
  'tests/test_stage002_runner.py::test_created_token_presence_preserves_zone_lineage_after_token_ceases',
  'tests/test_stage002_runner.py::test_runtime_token_namespace_reconciles_without_frozen_oracle_identity',
  'tests/test_stage002_runner.py::test_food_token_execution_authenticates_against_exact_runtime_presence',
  'tests/test_stage002_runner.py::test_food_token_execution_rejects_mismatched_runtime_provenance'
)
python -B -m pytest -q $nodes
```

The ten named nodes in the expanded `tests/test_diagnostic_capture.py` are:

- `test_nested_failure_uses_explicit_runner_binding_not_innermost_game_local`
- `test_run_game_exception_capture_preserves_presence_and_authenticates_token`
- `test_missing_or_ambiguous_runner_binding_fails_closed_without_hiding_error`
- `test_capture_finalizes_a_copy_of_presence_without_mutating_live_ledger`
- `test_reused_capture_does_not_attach_previous_game_to_unbound_failure`
- `test_unprintable_snapshot_capture_error_does_not_mask_original_exception`
- `test_non_game_success_after_failure_clears_stale_failure_and_binding`
- `test_run_game_without_capture_preserves_setup_exception`
- `test_presence_finalization_and_traceback_format_failures_keep_original_exception`
- `test_failure_inside_capture_bookkeeping_cannot_replace_execution_exception`

Result: **42 passed, 0 failed, 0 skipped**. Ruff format check, Ruff lint, and `git diff --check` passed on `src/tmnt_design_studio/stage002.py`, `tests/test_diagnostic_capture.py`, and the unchanged `tests/test_stage002_runner.py`.

## Historical preservation

Read-only replay used the recorded PR #404 source `67b9bb3083c9f4b2fe02e7fed258c4739581225f`, imported from `C:\projects\tmt\.diag001-pr404-67b9bb3\src\tmnt_design_studio\stage002.py`, with the preserved canonical game spec and artifacts in `C:\projects\tmt\.cardcade-diagnostic001-report\docs\cardcade\diagnostic_game_001\evidence`.

The recomputed Stage 002 manifest exactly matched the saved manifest; reconciliation exactly matched the saved report. All nine files listed in `artifact_sha256.json` verified. The same three original stop records remain: `illegal_mutation` for terminal combat, `silent_approximation` for `presence_evidence_missing`, and `silent_approximation` for the original disputed execution references. No historical presence was reconstructed and no stop/reference was deleted or reclassified.

## Independent acceptance request and limitations

Independently verify the two preserved RED cases become GREEN, stale state is cleared between calls, missing/duplicate binding is fail-closed, snapshot/finalization/formatting/bookkeeping failures cannot mask the original exception, the non-game success and no-capture paths remain compatible, and authenticated presence reconciles.

The future one-shot diagnostic launcher must create a fresh capture object per invocation, call `run_game(..., diagnostic_capture=capture)` within `capture_diagnostic_call`, persist `capture.failure` before reusing the object, and keep its existing single-run/no-retry safeguards. This PR does not modify that historical launcher and does not authorize another game, calibration, merge, deck change, or baseline promotion.
