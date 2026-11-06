# PRs #381, #382, and #385 — Combined Synthetic Validation

## Candidate identity

This local integration candidate is isolated on branch
`integration/cardcade-pr381-382-385` in
`C:\projects\tmt\.combined-cardcade-pr381-382-385`. It starts from corrected
PR #381 `6a4a1ce21ebd939a4ec0a3e1fb376c2b263c387c` and combines the unchanged
draft heads:

- PR #382 `013248622442d58246274f90291be74ede9a2c23`
- PR #385 `fdb4cac195bc0f1032eefd4aa14787d4e5dab866`

Integration order: #381, then #382, then #385. Local merge commits are
`093cbe3` and `d64037d`. No PR branch was merged into `main`, and the three
source PR identities remain separate and unchanged.

## Combined correction and reproduction

The first combined reproduction passed Tunnel Rats' naturally opened empty
end-step priority window, but failed Frog Butler Reach after attacker
declaration: in #385's empty-stack priority window the defender had only a
Pass option. PR #382's action enumerator required a nonempty stack, and its
announcement path rejected the non-active player when the stack was empty.

The integration-only engine correction keeps the existing priority-state,
priority-owner, resolution-pending, supported-semantics, and payment checks. It
allows the Reach action in an empty-stack window and permits the player holding
that window to announce the ability. It does not create priority windows; #385
continues to control when the ordinary windows open. The regression reproduces
the natural sequence: declare attackers with deferred step transition, offer
the defender priority, activate and resolve Reach, then advance to blockers and
verify the Frog can block the flyer.

The paired integration test exercises Tunnel Rats through the Stage 002
ordinary-priority driver at an empty-stack end step, pays `{4}{B}`, preserves
the graveyard object through activation, resolves exactly once, and returns a
tapped new object. The isolated #381 engine test remains useful for legality;
this combined test establishes driver reachability.

## Selected synthetic tests

Environment: Python 3.12.10, pytest 8.4.2, Ruff 0.16.1. Test bodies were
inspected. The explicit selection below contains direct synthetic `Game`
fixtures and step/priority transitions; it does not call `run_game`, a launcher,
the runner suite, or calibration.

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONPATH=(Resolve-Path src).Path
& 'C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\python.exe' -B -m pytest -q `
  tests/test_cardcade_stage002_silent_stop_ledger.py::test_raw_stops_keep_exact_indices_and_derived_stops_keep_distinct_identity `
  tests/test_cardcade_stage002_silent_stop_ledger.py::test_inserted_reconciler_stop_before_raw_suffix_is_rejected `
  tests/test_cardcade_stage002_silent_stop_ledger.py::test_reordered_reconciler_raw_stops_are_rejected `
  tests/test_cardcade_stage002_silent_stop_ledger.py::test_omitted_reconciler_raw_stop_is_rejected `
  tests/test_tunnel_rats_graveyard_return.py::test_tunnel_rats_exact_graveyard_semantics `
  tests/test_tunnel_rats_graveyard_return.py::test_tunnel_rats_can_activate_at_priority_and_remains_in_graveyard_until_resolution `
  tests/test_tunnel_rats_graveyard_return.py::test_tunnel_rats_is_offered_in_empty_stack_end_step_priority `
  tests/test_tunnel_rats_graveyard_return.py::test_tunnel_rats_main_action_exposes_only_when_five_lands_include_black `
  tests/test_tunnel_rats_graveyard_return.py::test_tunnel_rats_requires_a_black_source_even_with_five_available_lands `
  tests/test_tunnel_rats_graveyard_return.py::test_tunnel_rats_spends_floating_black_mana_and_four_generic_sources `
  tests/test_tunnel_rats_graveyard_return.py::test_tunnel_rats_does_not_return_if_graveyard_object_leaves_before_resolution `
  tests/test_frog_butler_mana.py::test_frog_butler_produces_chosen_color_with_source_provenance `
  tests/test_frog_butler_mana.py::test_frog_butler_mana_ability_rejects_summoning_sick_source `
  tests/test_frog_butler_mana.py::test_frog_butler_mana_is_immediate_and_empties_at_step_end `
  tests/test_fugitive_droid_unblockability.py::test_fugitive_droid_cannot_be_blocked_after_controlled_artifact_entry_even_if_it_left `
  tests/test_fugitive_droid_unblockability.py::test_fugitive_droid_does_not_get_unblockability_from_artifact_entering_for_opponent `
  tests/test_fugitive_droid_unblockability.py::test_artifact_token_entry_is_recorded_once_and_uses_entry_controller `
  tests/test_fugitive_droid_unblockability.py::test_direct_battlefield_placement_records_a_noncreature_artifact_once `
  tests/test_fugitive_droid_unblockability.py::test_artifact_moved_from_graveyard_enters_as_a_new_tracked_object `
  tests/test_fugitive_droid_unblockability.py::test_fugitive_droid_artifact_entry_condition_expires_at_next_turn `
  tests/test_does_machines_level_three.py::test_animated_artifact_can_block_as_a_creature `
  tests/test_frog_butler_reach.py::test_frog_butler_reach_exact_activation_and_payment `
  tests/test_frog_butler_reach.py::test_frog_butler_reach_is_offered_during_stack_priority `
  tests/test_frog_butler_reach.py::test_summoning_sick_frog_can_use_non_tap_reach_ability_at_priority `
  tests/test_frog_butler_reach.py::test_reach_priority_action_requires_both_generic_mana `
  tests/test_frog_butler_reach.py::test_reach_changes_defensive_flying_block_legality `
  tests/test_frog_butler_reach.py::test_reach_expires_at_end_of_turn `
  tests/test_frog_butler_reach.py::test_reach_source_departure_fails_closed `
  tests/test_frog_butler_reach.py::test_reach_repeated_activation_is_deterministic `
  tests/test_stage002_ordinary_priority_windows.py::test_empty_beginning_of_combat_offers_both_players_priority `
  tests/test_stage002_ordinary_priority_windows.py::test_empty_end_step_offers_both_players_priority_before_cleanup `
  tests/test_stage002_ordinary_priority_windows.py::test_existing_open_empty_window_is_not_reopened `
  tests/test_stage002_ordinary_priority_windows.py::test_empty_window_does_not_create_stack_objects `
  tests/test_stage002_ordinary_priority_windows.py::test_attacker_declaration_waits_for_both_players_to_pass `
  tests/test_stage002_ordinary_priority_windows.py::test_blocker_declaration_and_sneak_decline_preserve_priority_before_damage `
  tests/test_stage002_ordinary_priority_windows.py::test_legacy_combat_adapter_keeps_explicit_diagnostic_transitions `
  tests/test_stage002_ordinary_priority_windows.py::test_postcombat_main_has_ordinary_priority_before_end_step `
  tests/test_stage002_ordinary_priority_windows.py::test_defending_player_receives_priority_before_block_choices `
  tests/test_stage002_ordinary_priority_windows.py::test_legacy_direct_attacker_action_keeps_original_transition `
  tests/test_stage002_ordinary_priority_windows.py::test_legacy_direct_block_action_keeps_original_transition `
  tests/test_combined_pr381_pr382_pr385_integration.py::test_stage002_naturally_offers_tunnel_rats_at_empty_end_step_priority `
  tests/test_combined_pr381_pr382_pr385_integration.py::test_frog_reach_is_available_after_attackers_before_blockers_on_empty_stack
```

Result: **42 passed, 0 failed, 0 skipped**. The preserved Reach reproduction
failed on the uncorrected combined tree because its option list contained only
Pass; it passes with the integration correction.

Ruff format check covered all 12 changed Python files and passed. Ruff lint
passed on the same files. `git diff --check` passed. No games, smoke, or
calibration were run.

## Historical ledger and boundaries

PR #381's separately rebuilt read-only ledger remains byte-identical to the
committed CSV at SHA-256
`4476cc931b91354c076dedc543c9fea89ef5c43c62c0cf786a889a3bc7b884c5`: 485
unique rows, 303 indeterminate / 126 provenance / 56 unsupported, 201 affected
games. Its source-prefix assertion and inserted/reordered-stop regressions are
included in this combined tree. The protected archive was not modified.

This branch is a local review candidate, not a merge or gameplay restart.
Outstanding limits include broader end-to-end provenance validation and HQ
review of the combined engine diff. No complete games, smoke batches,
calibration, deck revisions, or unrestricted CI were authorized or run.

## Final fidelity gate — 2026-11-06

**Starting validated HEAD:** `b885d545d07031162e7e12169ce586cd22788bf6`.
**Validated code and test source:**
`4af1f08aa18b9a164160ddb0cfba328535a85464`, parent `b885d545d07031162e7e12169ce586cd22788bf6`.
The final PR head will be a documentation-only child that records this source
identity; no engine or test files change after this validated commit.

### Priority transitions

- `Game.transition_to` previously rejected an unresolved Stack but permitted a
  step change while an ordinary empty-stack priority window was open. It now
  rejects any live `priority_state` before changing state or logging events.
  The rejection preserves the authoritative fingerprint, event sequence, and
  step. Tests cover no passes, one pass, both passes before closure, and valid
  closure followed by turn progression.
- `check_invariants` now accepts empty-stack priority in ordinary steps and
  rejects it in Setup, Untap, and Cleanup. Stack-backed priority and resolution
  retain their existing behavior. Legacy `Game.combat()` and direct combat
  transition tests pass.
- Generated Frog Butler mana actions now carry each explicit color choice.
  The same immediate, no-Stack options are available to the current priority
  holder. This closes the gap where a legal ability was listed without an
  executable choice.

### Execution and provenance traces

Controlled synthetic `Game` fixtures use the actual CardInterpreter, engine
action entry points, serialized `Game.snapshot()`, runtime `stage002_presence`,
`_authoritative_execution_index`, and `reconcile_snapshot`. Each fixture's
static synthetic manifest is frozen from its initial CardFact presence before
actions; it does not derive semantic identity or execution attribution from
runtime evidence.

- Tunnel Rats was offered and activated through the ordinary Stage 002
  empty-stack end-step driver, paid `{4}{B}`, resolved once, and was
  authenticated against its original graveyard source lineage.
- Two Frog Butler mana activations selected blue and green. The blue mana paid
  for a blue synthetic spell with consumption linked to its production event
  and hand-object payment identity; the remaining green mana emptied at the
  step boundary. Both activations authenticated by source and fragment.
- Frog Butler Reach activated for the defending player after attackers and
  resolved before blockers; the Frog then legally blocked the flyer. The
  resolved source/fragment pair authenticated through the reconciler.
- Fugitive Droid remained unblockable after its controller's artifact entered
  and left. An opponent's artifact entry followed by a controller change did
  not grant the restriction. The snapshot reconciled with no invented
  execution references or stop records.
- A second Reach activation was offered in a fresh empty-stack follow-on window
  after the first Reach Stack object resolved. The two activations had distinct
  priority epochs and source evidence; both authenticated.

### Second main and combat sequence

The engine already generates the same land, supported activation, and spell
actions in precombat and postcombat main. Stage 002 previously ran the existing
five stages (`land`, `activate`, `damage`, `destroy`, `creature`) only before
combat, omitting all of those legal postcombat actions from the pilot. The
runner now applies the same existing `AcceptancePilot` stage policy in
postcombat main before its ordinary priority window. This is a bounded policy
reuse, not a new decision model. It can change second-main land drops, activations,
and casts in the frozen ten-deck environment; the size or outcome impact is not
measured because complete games are outside this gate.

An explicit synthetic sequence covers beginning of combat, attack declaration,
defender priority, block declaration, Sneak decline, combat damage, end of
combat, postcombat main, and end step. Every consecutive-pass pair belongs to
one epoch; stale priority options are rejected without mutation; the winner
terminates priority dispatch. The legacy combat adapter remains intact.

### Final selected validation

The exact final selection is the 42 node IDs above plus these 14 individually
selected nodes in `tests/test_pr386_final_fidelity_gate.py`:

```text
test_transition_rejects_open_empty_priority_window_before_passes
test_transition_rejects_open_empty_priority_window_after_one_pass
test_transition_rejects_two_passes_until_empty_window_closure_is_processed
test_priority_action_from_closed_epoch_is_rejected_without_mutation
test_stack_resolution_and_legacy_combat_transitions_remain_valid
test_natural_tunnel_rats_execution_authenticates_through_reconciler
test_frog_mana_action_produces_pays_and_expires_with_authenticated_lineage
test_frog_mana_ability_is_an_immediate_priority_action_with_color_choice
test_defender_reach_execution_authenticates_before_block_declaration
test_fugitive_droid_controller_specific_entry_restriction_survives_reconcile
test_follow_on_empty_priority_after_resolution_can_execute_reach
test_existing_main_action_policy_runs_during_postcombat_main
test_full_combat_priority_and_sneak_sequence_uses_fresh_epochs
test_priority_driver_stops_prompting_after_winner
```

All selected test bodies were inspected; no complete-game runner, launcher,
smoke, or calibration path is called. Under Python 3.12.10 and pytest 8.4.2,
the combined selection passed **56 tests, 0 failed, 0 skipped**. Ruff 0.16.1
format and lint checks passed, as did `git diff --check`. The exact corrected
source SHA is the PR head. No Baseline 005 deck, historical game artifact, or
protected G: archive content was modified.

This closes the bounded synthetic fidelity gate only. It does not validate
full-game behavior, quantify the second-main impact, settle broader historical
provenance questions, authorize a smoke test, or authorize merge. PR #386
remains draft for HQ acceptance. The separate evidence-only commit is excluded
from the tested code source; the PR description identifies both its final head
and the exact validated source commit.
