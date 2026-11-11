# Pilot Fidelity Correction Acceptance

## Source and scope

- Repository: `egggggman/tmt`.
- Parent source / PR #395: `review/cardcade-purple-dragon-mana` at `7ed476f4ded0ed59292f019320b3331688f2d2e4`.
- Isolated worktree: `C:\projects\tmt\.cardcade-pilot-fidelity-correction`.
- Implementation branch: `review/cardcade-pilot-fidelity-correction`.
- Code and test commit: `dd14b5b05ffd8d535c572deb749cfd2019be4b3f` (`[skip ci]`).
- Accepted main observed locally: `10d2ac80ef5b81b3a209a3133eb0a84633a1f944`.
- No changes were made to PR #395, PR #396, accepted main, decks, Baseline 005, or Smoke 001 evidence.

## Corrections

### Spicy Oatmeal Pizza

`AcceptancePilot.choose_damage_target` scores only the target IDs supplied by the engine and reads life totals plus public creature controller, toughness, marked damage, and power from `GameViewV2`. It applies the target's four damage and the controller's mandatory three damage together when ranking terminal outcomes. A win ranks above an ongoing game, an ongoing game above a draw, and a draw above a loss. Among equivalent outcomes it favors a lethal removal of an opposing creature, then opposing player damage, with offered order as the deterministic tie-breaker.

The Stage 002 runner wires the chooser to `Game.damage_target_chooser`; target legality, trigger creation, damage ordering, and resolution remain engine-owned. A pilot without the optional chooser retains the engine's prior default behavior.

### Restricted mana decisions

The engine attaches immutable hypothetical follow-up descriptors to legal mana-ability options. It derives the mana color and allowed spending contexts from the interpreted ability. The pure preview uses the existing floating-mana snapshot and deterministic mana-source selector with one virtual mana; it does not add a lot, issue a payment, or mutate the game. It considers represented artifact casts, supported graveyard artifact-creature casts, and supported activated abilities available in the current main or priority window.

The pilot selects a restricted mana ability only when a preview identifies an action it could enable. Main-phase activation selection is re-enumerated after that immediate mana action, with a three-attempt cap. The existing priority loop re-enumerates engine actions after mana production; the pilot chooses a useful restricted-mana activation and then an offered ability whose real payment plan consumes restricted mana. Unrestricted mana behavior, including Frog Butler, remains available under the previous pilot policy.

## Validation

Environment: Python 3.12.10, pytest 8.4.2, Ruff 0.16.1. Tests ran at code commit `dd14b5b05ffd8d535c572deb749cfd2019be4b3f`, with the isolated worktree `src` on `PYTHONPATH`.

PowerShell set `$env:PYTHONPATH='C:\projects\tmt\.cardcade-pilot-fidelity-correction\src'`, then ran `& 'C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\python.exe' -B -m pytest -q` with the 54 explicit node IDs listed below. Parameterized nodes expanded to 56 cases; result: **56 passed, 0 failed, 0 skipped**. No complete game ran.

### New pilot tests (12 nodes)

- `tests/test_pilot_fidelity_correction.py::test_pizza_pilot_chooses_only_an_engine_offered_lethal_target`
- `tests/test_pilot_fidelity_correction.py::test_pizza_pilot_prefers_a_win_to_a_creature_target`
- `tests/test_pilot_fidelity_correction.py::test_pizza_pilot_prefers_a_draw_to_a_loss_from_mandatory_self_damage`
- `tests/test_pilot_fidelity_correction.py::test_pizza_pilot_removes_a_lethal_opposing_creature_before_nonlethal_player_damage`
- `tests/test_pilot_fidelity_correction.py::test_pizza_pilot_returns_none_when_engine_offers_no_targets`
- `tests/test_pilot_fidelity_correction.py::test_stage_runner_wires_pizza_selection_through_engine_offered_targets`
- `tests/test_pilot_fidelity_correction.py::test_punks_is_selected_only_when_pure_hypothetical_payment_enables_artifact_cast`
- `tests/test_pilot_fidelity_correction.py::test_punks_activation_makes_artifact_cast_available_for_reconsidered_main_actions`
- `tests/test_pilot_fidelity_correction.py::test_main_action_driver_rechecks_after_useful_punks_mana_activation`
- `tests/test_pilot_fidelity_correction.py::test_punks_is_not_activated_for_a_nonartifact_spell_without_an_ability_followup`
- `tests/test_pilot_fidelity_correction.py::test_unrestricted_frog_mana_choice_remains_available_to_the_pilot`
- `tests/test_pilot_fidelity_correction.py::test_punks_priority_hint_enables_and_reselects_frog_reach_activation`

### Existing regression nodes (42 nodes)

`tests/test_purple_dragon_mana.py`:

- `test_frozen_purple_dragon_punks_mana_ability_is_offered_and_activates`
- `test_summoning_sick_punks_cannot_tap_for_mana_without_mutation`
- `test_haste_allows_summoning_sick_punks_mana_activation`
- `test_tapped_punks_cannot_activate_again_or_duplicate_mana`
- `test_punks_mana_is_immediately_available_during_priority_without_epoch_change`
- `test_restricted_punks_mana_pays_artifact_spell_with_exact_lineage`
- `test_restricted_punks_mana_cannot_pay_nonartifact_spell`
- `test_restricted_punks_mana_pays_supported_activated_ability`
- `test_restricted_punks_mana_combines_with_land_and_leaves_payment_provenance`
- `test_unspent_punks_mana_expires_at_step_boundary_with_source_history`
- `test_produced_restricted_mana_remains_spendable_after_source_leaves`
- `test_punks_activation_and_following_ability_reconcile_without_fabricated_execution`
- `test_frozen_card_identity_and_interpreter_contract_are_not_name_dispatched`

`tests/test_spicy_oatmeal_pizza_trigger.py`:

- `test_pizza_etb_target_damage_then_controller_damage_has_authenticated_priority`
- `test_pizza_trigger_resolves_after_source_leaves_and_simultaneous_lethal_effects`
- `test_ordinary_life_loss_remains_a_terminal_win`
- `test_normal_pizza_cast_auto_stacks_and_resolves_one_authenticated_trigger`
- `test_pizza_damage_semantics_are_card_name_independent_and_fully_supported`

`tests/test_april_end_step_draw.py`:

- `test_april_creates_authenticated_trigger_at_its_controllers_end_step`
- `test_zero_spell_types_draw_zero`
- `test_distinct_card_types_count_once_with_multitype_spell_and_repeated_casts`
- `test_april_departure_before_trigger_and_after_trigger_boundaries`
- `test_april_entering_after_end_step_begins_does_not_trigger_retroactively`
- `test_april_execution_reconciles_with_authenticated_spell_cast_lineage`
- `test_countered_spell_remains_in_april_cast_history`
- `test_spell_type_cast_during_response_is_counted_at_resolution`
- `test_opponent_cast_during_april_priority_is_excluded`
- `test_previous_turn_spell_events_are_excluded_after_turn_boundary`
- `test_rejected_spell_announcement_creates_no_cast_event`
- `test_sneak_announcement_creates_one_authenticated_cast_event`

`tests/test_ravenous_robots_artifact_cast.py`:

- `test_ravenous_robots_triggers_for_normally_cast_spicy_oatmeal_pizza`
- `test_ravenous_artifact_spell_trigger_resolves_to_exact_robot_token`
- `test_artifact_creature_spell_triggers_and_nonartifact_spell_does_not`
- `test_opponent_artifact_cast_does_not_trigger_controller_robots`
- `test_artifact_cast_trigger_reconciles_with_original_spell_event`
- `test_artifact_cast_event_keeps_april_cast_history_compatible`
- `test_trigger_uses_cast_event_once_even_when_event_delivery_is_repeated`
- `test_countered_artifact_spell_keeps_original_cast_event_and_trigger_result`

`tests/test_restricted_spell_payment.py`:

- `test_artifact_spell_uses_restricted_mana_and_snapshots_exact_cast_linkage`
- `test_nonartifact_cannot_spend_artifact_only_mana_but_can_use_unrestricted_mana`

`tests/test_restricted_ability_payment.py`:

- `test_activation_mana_plan_rejects_stale_and_forged_ledger_allocations`
- `test_hand_landcycling_uses_activation_context_and_authenticated_allocation`

Quality commands on the changed files:

```powershell
& 'C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\ruff.exe' format --check src/tmnt_design_studio/engine07.py src/tmnt_design_studio/pilot07.py src/tmnt_design_studio/stage002.py tests/test_pilot_fidelity_correction.py
& 'C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\ruff.exe' check src/tmnt_design_studio/engine07.py src/tmnt_design_studio/pilot07.py src/tmnt_design_studio/stage002.py tests/test_pilot_fidelity_correction.py
git diff --check
```

Results: Ruff format check passed (4 files already formatted); Ruff lint passed; `git diff --check` passed.

## Limits for independent review

- Pizza target quality is deterministic immediate-state evaluation, not multi-turn strategy search. It values lethal removal of opposing creatures and does not model unsupported protection, ward, planeswalker, or replacement-effect mechanics.
- Punks previews are limited to action families already represented by the engine. They do not expose hypothetical response spells or unimplemented activation/cast paths. The main-stage continuation is capped at three selections.
- No gameplay, deck, telemetry, or engine-semantics changes were made beyond attaching pilot-facing metadata to engine-generated options and re-evaluating the existing supported action paths.

**Recommendation: READY FOR INDEPENDENT HQ ACCEPTANCE REVIEW.**
