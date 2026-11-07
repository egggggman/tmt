# Restricted Spell Payment Integration Acceptance

## Source identity

- Authorized parent: `aa15c76e4e270562e317716866e0fd22b35ee873` (PR #392, `review/cardcade-restricted-mana-ledger`).
- Isolated branch: `review/cardcade-restricted-spell-payments`.
- Isolated worktree: `C:`projects`tmt`.cardcade-restricted-mana-spell-payments`.
- Tested implementation: `e4e29d27b8f7c3e8d72333c584b4b93c87e9eee5`.
- Regression-first test commit: `f5f0b93c912b831eac81cb3519437656b45b7de0`.
- Accepted main at audit: `10d2ac80ef5b81b3a209a3133eb0a84633a1f944`.

## Findings and correction

On the authorized parent, a second payment-plan request using the same payment identity failed because planning mutated an issued-plan registry. A plan also remained committable after unrelated mana state changed. The regression-first tests captured both behaviors.

The ledger now creates pure, deterministic plans bound to a ledger capability and revision. Commit revalidates the exact current lots and allocations, and successful payment identities cannot be reused. Production history remains immutable while live lots carry remaining quantity, allowed spending contexts, and expiration evidence. Expired lots cannot be allocated.

Spell announcements derive `artifact_spell` or `nonartifact_spell` from the actual card type line. The existing source-selection logic still handles colored, generic, and hybrid costs, land tapping, and unrestricted floating mana. When a spell uses floating mana, its payment plan contains exact lot allocations. The shared hand, response, graveyard, and supported Raphael exile spell paths use this contract. The announcement validates all allocations and lands before irreversible mutation; failed zone movement rolls back land taps, and mana is committed only after a successful move. Cast event and payment evidence are recorded after that point.

Snapshots include spell-payment evidence. Stage 002 reconciliation verifies the payment-to-cast relationship, card identity and type line, spending context, exact production lots and source events, controller/color/quantity, and remaining/consumed/expired conservation. It emits a provenance stop on inconsistency and does not fabricate an `EXECUTED` reference.

## Validation

Environment: Python 3.12.10, pytest 8.4.2, Ruff 0.16.1, using `C:`projects`tmt`.cardcade-fidelity-correction`.venv`Scripts`python.exe` and `ruff.exe`.

Exactly 38 individually selected synthetic nodes passed: 38 passed, 0 failed, 0 skipped. No complete-game runner was selected.

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONPATH='C:`projects`tmt`.cardcade-restricted-mana-spell-payments`src'
& 'C:`projects`tmt`.cardcade-fidelity-correction`.venv`Scripts`python.exe' -B -m pytest -q `
  tests/test_restricted_spell_payment.py::test_repeated_ledger_payment_planning_is_pure_and_deterministic `
  tests/test_restricted_spell_payment.py::test_ledger_payment_plan_is_stale_after_any_mana_state_change `
  tests/test_restricted_spell_payment.py::test_committed_payment_identity_cannot_be_reused_by_another_controller `
  tests/test_restricted_spell_payment.py::test_artifact_spell_uses_restricted_mana_and_snapshots_exact_cast_linkage `
  tests/test_restricted_spell_payment.py::test_nonartifact_cannot_spend_artifact_only_mana_but_can_use_unrestricted_mana `
  tests/test_restricted_spell_payment.py::test_mixed_restricted_unrestricted_and_land_payment_preserves_partial_lot `
  tests/test_restricted_spell_payment.py::test_multicolor_and_hybrid_spending_uses_typed_lots_and_land_sources `
  tests/test_restricted_spell_payment.py::test_expired_forged_wrong_purpose_and_duplicate_spell_plans_fail_atomically `
  tests/test_restricted_spell_payment.py::test_reusing_a_successful_spell_payment_plan_cannot_consume_or_cast_twice `
  tests/test_restricted_spell_payment.py::test_zone_failure_rolls_back_land_and_restricted_mana_payment `
  tests/test_restricted_spell_payment.py::test_legal_action_planning_is_repeatable_and_does_not_authorize_payment `
  tests/test_restricted_spell_payment.py::test_graveyard_and_exile_spell_paths_share_typed_payment_contract `
  tests/test_restricted_spell_payment.py::test_spell_payment_snapshot_reconciles_without_invented_execution_reference `
  tests/test_restricted_spell_payment.py::test_reconciler_rejects_payment_evidence_that_disagrees_with_cast_or_lot `
  tests/test_engine08e_costs.py::test_typed_cost_construction_is_exact_and_rejects_unrepresented_symbols `
  tests/test_engine08e_costs.py::test_payment_plan_uses_colored_sources_first_then_deterministic_generic_source `
  tests/test_engine08e_costs.py::test_announcement_atomically_commits_payment_and_stack_movement `
  tests/test_engine08e_costs.py::test_stale_or_fabricated_payment_plan_is_rejected_before_mutation `
  tests/test_engine08e_costs.py::test_zone_failure_rolls_back_every_payment_source `
  tests/test_engine08e_costs.py::test_hybrid_cost_pays_with_blue `
  tests/test_engine08e_costs.py::test_hybrid_cost_pays_with_red `
  tests/test_engine08e_costs.py::test_hybrid_cost_rejects_insufficient_mana `
  tests/test_restricted_mana_ledger.py::test_expiration_does_not_reuse_an_older_same_color_production_lot `
  tests/test_restricted_mana_ledger.py::test_context_restrictions_and_unrestricted_lots_are_distinct `
  tests/test_restricted_mana_ledger.py::test_mixed_lots_and_partial_payment_preserve_exact_remaining_quantity `
  tests/test_restricted_mana_ledger.py::test_payment_rejections_are_atomic_for_forged_duplicate_and_wrong_context_allocations `
  tests/test_restricted_mana_ledger.py::test_expired_or_incorrect_controller_allocations_cannot_be_committed `
  tests/test_restricted_mana_ledger.py::test_lifecycle_evidence_preserves_consumption_expiration_and_boundary `
  tests/test_restricted_mana_ledger.py::test_legacy_payment_can_consume_multiple_colors_under_one_payment_id `
  tests/test_restricted_mana_ledger.py::test_game_snapshot_and_fingerprint_include_authenticated_frog_mana_lifecycle `
  tests/test_mana_ledger07.py::test_production_and_exact_lineage_consumption `
  tests/test_mana_ledger07.py::test_invalid_or_duplicate_consumption_fails_closed `
  tests/test_mana_ledger07.py::test_unused_mana_empties_deterministically `
  tests/test_frog_butler_mana.py::test_frog_butler_produces_chosen_color_with_source_provenance `
  tests/test_frog_butler_mana.py::test_frog_butler_mana_ability_rejects_summoning_sick_source `
  tests/test_frog_butler_mana.py::test_frog_butler_mana_is_immediate_and_empties_at_step_end `
  tests/test_pr386_final_fidelity_gate.py::test_frog_mana_action_produces_pays_and_expires_with_authenticated_lineage `
  tests/test_pr386_final_fidelity_gate.py::test_frog_mana_ability_is_an_immediate_priority_action_with_color_choice
```

Quality checks at the tested implementation HEAD:

- Ruff format check on the four changed source/test files: passed, already formatted.
- Ruff lint on the four changed source/test files: passed.
- `git diff --check`: passed.

## Audited boundaries and limitations

Payment consumers audited include ordinary hand casts, response casts, shared graveyard casts, and the supported Raphael-authorized exile cast path. The same shared spell announcement commits payment, the cast event, and Stack entry. Existing tests cover unrestricted and land payments and Frog Butler's immediate mana behavior.

Restricted payment for ordinary activated abilities and Sneak-specific paths is intentionally outside this checkpoint. Purple Dragon Punks' ability has not been implemented. These paths must not consume artifact-restricted lots until a later explicit integration checkpoint. No complete games, decks, protected archives, or historical diagnostic artifacts were modified.

## Recommendation

**READY FOR HQ REVIEW**
