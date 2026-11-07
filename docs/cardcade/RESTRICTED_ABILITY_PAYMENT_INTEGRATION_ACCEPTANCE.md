# Restricted Ability Payment Integration Acceptance

## Source identities

- Authorized starting source: `19a8fbd933ff199ebbe2821c6901c68d0f6eb148` on `review/cardcade-restricted-spell-payments` (PR #393).
- Isolated worktree: `C:\projects\tmt\.cardcade-restricted-mana-activated-payments`.
- Working branch: `review/cardcade-restricted-ability-payments`.
- Preserved failing reproduction: `cdf753b1754e4c33295591178b436d23b3d03edf`.
- Tested implementation: `196194eb2146416260ffd0d1186ba9f646b3aaf5`.
- Final report commit: recorded in the PR body after publication.
- Accepted main remains `10d2ac80ef5b81b3a209a3133eb0a84633a1f944`.

## Finding and correction

At the starting source, a supported `{R}` battlefield activation could not plan a payment from a red mana production lot whose allowed context was `activated_ability`. The isolated test was committed first and failed on the original implementation because the action had no valid payment plan.

The correction routes the supported battlefield, hand landcycling/discard, and Tunnel Rats graveyard activation paths through one activation-payment planner. The planner uses the existing `FloatingManaLedger`, requests `activated_ability` eligibility, and preserves exact production-lot allocations alongside land sources. It binds allocations to the resulting activated ability object identity; offsets account for destination objects created by discard and sacrifice costs. The legacy Tunnel Rats payment identity contract is preserved.

Each caller validates the complete payment and activation before irreversible mutation. Existing staged rollback protects taps, discards, sacrifices, counters, object identity, and Stack state if a later transaction stage fails. The mana ledger commits only after activation placement succeeds. Immediate mana abilities remain immediate; Stack-using abilities retain their existing priority and resolution behavior. No spell payment context was widened, and no Purple Dragon Punks or Sneak-specific behavior was added.

Committed activation evidence now carries the payment identity, cost, and exact mana allocations through resolution. The snapshot serializes that evidence. The Stage 002 reconciliation check authenticates each allocation against the producing lot/event, controller, allowed context, payment, land source/cost, announced activation, source, and Oracle fragment; missing or inconsistent links produce a stop instead of an invented execution reference.

## Validation

Environment: Python `3.12.10`, pytest `8.4.2`, Ruff `0.16.1`; interpreter at `C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\python.exe`. The tested code HEAD was `196194eb2146416260ffd0d1186ba9f646b3aaf5`.

The exact individually selected test command was:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONPATH='C:\projects\tmt\.cardcade-restricted-mana-activated-payments\src'
& 'C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\python.exe' -B -m pytest -q -p no:cacheprovider `
  tests/test_restricted_ability_payment.py::test_supported_battlefield_ability_uses_activated_ability_restricted_mana `
  tests/test_restricted_ability_payment.py::test_wrong_context_is_rejected_without_mutating_activation_state `
  tests/test_restricted_ability_payment.py::test_mixed_restricted_unrestricted_and_land_activation_payment `
  tests/test_restricted_ability_payment.py::test_activation_mana_plan_rejects_stale_and_forged_ledger_allocations `
  tests/test_restricted_ability_payment.py::test_activation_action_enumeration_is_repeatable_and_pure `
  tests/test_restricted_ability_payment.py::test_hand_landcycling_uses_activation_context_and_authenticated_allocation `
  tests/test_restricted_ability_payment.py::test_tunnel_rats_can_spend_activation_restricted_black_mana_at_end_step `
  tests/test_restricted_ability_payment.py::test_food_sacrifice_activation_rolls_back_restricted_payment_on_stack_failure `
  tests/test_restricted_ability_payment.py::test_food_sacrifice_activation_commits_restricted_payment_before_resolution `
  tests/test_restricted_ability_payment.py::test_activation_payment_snapshot_reconciles_exact_source_and_allocation `
  tests/test_restricted_spell_payment.py::test_artifact_spell_uses_restricted_mana_and_snapshots_exact_cast_linkage `
  tests/test_restricted_spell_payment.py::test_nonartifact_cannot_spend_artifact_only_mana_but_can_use_unrestricted_mana `
  tests/test_restricted_spell_payment.py::test_mixed_restricted_unrestricted_and_land_payment_preserves_partial_lot `
  tests/test_restricted_spell_payment.py::test_multicolor_and_hybrid_spending_uses_typed_lots_and_land_sources `
  tests/test_restricted_spell_payment.py::test_graveyard_and_exile_spell_paths_share_typed_payment_contract `
  tests/test_mana_ledger07.py::test_unused_mana_empties_deterministically `
  tests/test_restricted_mana_ledger.py::test_mixed_lots_and_partial_payment_preserve_exact_remaining_quantity `
  tests/test_frog_butler_mana.py::test_frog_butler_mana_is_immediate_and_empties_at_step_end `
  tests/test_frog_butler_reach.py::test_frog_butler_reach_exact_activation_and_payment `
  tests/test_tunnel_rats_graveyard_return.py::test_tunnel_rats_can_activate_at_priority_and_remains_in_graveyard_until_resolution `
  tests/test_tunnel_rats_graveyard_return.py::test_tunnel_rats_is_offered_in_empty_stack_end_step_priority `
  tests/test_tunnel_rats_graveyard_return.py::test_tunnel_rats_spends_floating_black_mana_and_four_generic_sources `
  tests/test_food_action.py::test_food_activation_uses_atomic_cost_stack_priority_and_life_result `
  tests/test_food_action.py::test_food_evidence_is_reconstructive_and_serialization_is_deterministic `
  tests/test_activated_abilities.py::test_failed_payment_is_atomic_and_does_not_create_stack_state `
  tests/test_engine08e_costs.py::test_hybrid_cost_pays_with_blue `
  tests/test_engine08e_costs.py::test_hybrid_cost_pays_with_red
```

Result: **27 passed, 0 failed, 0 skipped**. These are individually named deterministic tests; no complete-game runner was selected.

Quality checks on the implementation files:

```powershell
& 'C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\ruff.exe' format --check src/tmnt_design_studio/engine07.py src/tmnt_design_studio/stage002.py tests/test_restricted_ability_payment.py
& 'C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\ruff.exe' check src/tmnt_design_studio/engine07.py src/tmnt_design_studio/stage002.py tests/test_restricted_ability_payment.py
git diff --check 19a8fbd933ff199ebbe2821c6901c68d0f6eb148..196194eb2146416260ffd0d1186ba9f646b3aaf5
```

Ruff format reported all three files formatted; Ruff lint passed; `git diff --check` passed. Tests and checks produced no complete-game execution.

## Scope and limitations

- Supported payment families covered: battlefield activated abilities, hand landcycling/discard abilities, and Tunnel Rats graveyard activation.
- Sneak-specific payment handling remains explicitly outside this checkpoint.
- The activated-ability interpreter still does not support hybrid activation costs; no new hybrid ability grammar was introduced. Existing hybrid spell payment remains covered by the two selected compatibility tests.
- Purple Dragon Punks' mana-production ability remains unimplemented.
- This report and implementation are for independent HQ review; no merge is requested.

**Recommendation: READY FOR HQ REVIEW.**
