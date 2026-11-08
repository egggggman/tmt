# Diagnostic Game 001 — Terminal Combat Fix

## Source and scope

- Starting source: `67b9bb3083c9f4b2fe02e7fed258c4739581225f` (PR #404).
- Worktree: `C:\projects\tmt\.diag001-terminal-recovery`.
- Branch: `fix/cardcade-terminal-combat-advance`.
- Engine source imported for validation: this worktree's `src/tmnt_design_studio/engine07.py` (enforced with `PYTHONPATH=src`).
- Python 3.12.10; pytest 8.4.2; Ruff 0.16.1.
- No complete game, Stage 002 runner, or gameplay launcher was executed.

## Preserved red reproduction

The existing deterministic synthetic regression was first run against this checkout after confirming the imported module path:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
python -B -m pytest -q tests/test_strike_damage_steps.py::test_first_step_game_end_is_coherent_without_postcombat_transition
```

Result: **1 failed**. `Game.resolve_combat_damage()` applied lethal first-strike damage, marked the defender lost, and then raised `ValueError: cannot advance a terminal game` from `_advance_after_combat_damage()` → `transition_to(END_OF_COMBAT)`. This is the same post-lethal control-flow defect present in the preserved turn-16 PR #406 traceback. The historical name was changed to describe the corrected terminal behavior; the RED result and original source identity remain documented here.

A preliminary invocation without the `PYTHONPATH` override imported an editable install from another worktree and passed. It was discarded as invalid source evidence. All subsequent commands verified the module path under this worktree.

## Correction

`Game._advance_after_combat_damage()` now returns when the game is terminal, after confirming combat damage is resolved and no Stack/Priority work remains. This prevents a post-terminal step transition while preserving `Game.transition_to()`'s rejection of all terminal-game advances.

The terminal branch leaves the current damage-step kind as `FIRST_STRIKE` or `REGULAR`. A first correction attempt marked it `COMPLETE`; synthetic invariant checks showed that `COMBAT_DAMAGE` requires an active damage-step kind. The final correction preserves that invariant and records no extra transition or event.

Two deterministic synthetic regressions cover lethal first-strike and regular damage. They verify winner and life totals, terminal state, damage/loss/resolution event order, empty Stack, no priority, one evidence record, invariant validity, duplicate-resolution rejection, and unchanged fingerprint after a rejected terminal transition.

## Final synthetic validation

Command: `python -B -m pytest -q` followed by these individually selected nodes, with `PYTHONPATH` set to this worktree's `src`:

- `tests/test_strike_damage_steps.py::test_lethal_first_strike_damage_ends_without_advancing_terminal_combat`
- `tests/test_strike_damage_steps.py::test_lethal_regular_damage_ends_without_terminal_transition_or_duplicate_damage`
- `tests/test_strike_damage_steps.py::test_combat_damage_steps_cannot_be_skipped_repeated_or_resolved_out_of_order`
- `tests/test_strike_damage_steps.py::test_postcombat_main_clears_current_combat_state_but_preserves_evidence`
- `tests/test_strike_damage_steps.py::test_following_turn_and_later_combat_start_without_residual_state`
- `tests/test_strike_damage_steps.py::test_failed_transition_does_not_clear_or_fabricate_live_combat_state`
- `tests/test_strike_damage_steps.py::test_lethal_first_strike_sba_removes_blocker_before_regular_step`
- `tests/test_strike_damage_steps.py::test_no_strike_combat_retains_one_regular_damage_step`
- `tests/test_calibration_terminal_contract.py::test_game_snapshot_contract_is_authoritative_for_both_winners`
- All 11 named tests in `tests/test_stage002_ordinary_priority_windows.py`: `test_empty_beginning_of_combat_offers_both_players_priority`, `test_empty_end_step_offers_both_players_priority_before_cleanup`, `test_existing_open_empty_window_is_not_reopened`, `test_empty_window_does_not_create_stack_objects`, `test_attacker_declaration_waits_for_both_players_to_pass`, `test_blocker_declaration_and_sneak_decline_preserve_priority_before_damage`, `test_legacy_combat_adapter_keeps_explicit_diagnostic_transitions`, `test_postcombat_main_has_ordinary_priority_before_end_step`, `test_defending_player_receives_priority_before_block_choices`, `test_legacy_direct_attacker_action_keeps_original_transition`, and `test_legacy_direct_block_action_keeps_original_transition`.
- All four named tests in `tests/test_integrated_readiness_audit.py`: `test_announce_spell_composes_punks_payment_robot_trigger_and_pizza_etb`, `test_main_cast_action_composes_punks_followup_robot_trigger_and_pizza_etb`, `test_trigger_free_main_cast_still_resolves_with_legacy_compatibility`, and `test_game_cast_direct_caller_keeps_immediate_resolution_contract`.
- `tests/test_pr397_independent_audit_repro.py::test_pizza_target_policy_ranks_terminal_outcomes` (three parameter cases) and `::test_pilot_executes_the_artifact_followup_that_justified_punks_mana`.
- `tests/test_april_end_step_draw.py::test_april_execution_reconciles_with_authenticated_spell_cast_lineage`.
- `tests/test_ravenous_robots_artifact_cast.py::test_artifact_cast_event_keeps_april_cast_history_compatible`.

Result: **30 passed, 0 failed, 0 skipped** across 28 named nodes (the Pizza outcome node has three cases). All are synthetic fixtures; the integrated composition test exercises Punks → Pizza → Ravenous Robots without a complete game.

Quality checks on the two Python files:

- `ruff format --check src/tmnt_design_studio/engine07.py tests/test_strike_damage_steps.py` — passed.
- `ruff check src/tmnt_design_studio/engine07.py tests/test_strike_damage_steps.py` — passed.
- `git diff --check` — passed.

## Remaining acceptance boundary

The PR #406 evidence findings are separately classified in the evidence-only triage report. This correction addresses only the terminal combat continuation. It does not repair or reclassify historical reconciliation records, change the Stage 002 exception-capture wrapper, or establish integrated gameplay readiness. Independent acceptance is required before another complete game is authorized.
