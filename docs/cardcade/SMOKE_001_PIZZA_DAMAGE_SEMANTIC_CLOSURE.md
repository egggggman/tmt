# Smoke 001 — Spicy Oatmeal Pizza Damage Closure

## Source and preserved inputs

- Authorized starting source: `0c322b6ee75aa1da13b90d64cfe16e84ad632370` on `review/cardcade-smoke001-semantic-closure`.
- Isolated implementation branch: `review/cardcade-smoke001-pizza-closure` in `C:\projects\tmt\.smoke001-pizza-semantic-closure`.
- Validated code commit: `28b40104df7ef7fb200f2d8f85316cdc04e287cf`.
- Frozen Smoke 001 source: PR #386 at `8f9ed012fc367118d457fa0b0629598b7f03c15e`; PR #386 remains draft, open, unmerged, and unchanged.
- Accepted `origin/main`: `10d2ac80ef5b81b3a209a3133eb0a84633a1f944`; unchanged.
- Frozen Stage 002 card snapshot SHA-256: `56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402`.
- Frozen card-data manifest SHA-256: `6b5271af75150a361f77e7b89306c709959dfdf497c448dfdc978e5dc9a17950`.
- Pizza Oracle ID: `9665f940-c0a4-4d3e-b889-8049cf549a4f`. Exact ETB fragment: “When this artifact enters, it deals 4 damage to any target and 3 damage to you.” The separate Food ability remains outside this correction.
- All eight files listed in Smoke 001's `artifact_sha256.json` were rehashed and matched. The index SHA-256 remains `37302c21af43531ad43b91f559f0bf8ba44fe8cc079f32435e9a1a0c27d2a8d5`. The frozen diagnostic was read only.

## Audit and correction

The existing engine already supplied authenticated permanent-entry RulesEvents, triggered ability stack objects, all-pass priority resolution, typed damage transactions, state-based actions, and the Stage 002 execution evidence index. The gaps were Oracle interpretation for “any target” and the ordered self-damage clause, ETB trigger detection/target capture, post-resolution handling when the source had left, and simultaneous life-loss outcome calculation.

The implementation extends those paths:

- Interprets the bounded ETB damage sentence from Oracle grammar, independent of the card name. Other `any target` damage remains unsupported unless its full context is represented.
- Captures a legal player or creature target when the trigger is put on the stack. Both players then receive priority before it resolves.
- On resolution, deals four damage to the chosen target, then three damage to the trigger controller. State-based actions and the life check run after both ordered damage events.
- If the selected target is illegal on resolution, the trigger does not deal either part of the effect. The trigger retains its original source and entry event if that source leaves the battlefield.
- Damage events keep the original source object ID and exact Oracle fragment. The existing authoritative execution index authenticates both event IDs; the synthetic snapshot reconciler classifies the source as executed without stop records.
- Corrects `check_life()` to recognize simultaneous life loss as a draw instead of assigning a winner from player iteration order.
- Routes existing Alliance damage triggers through priority as stack objects too. Their original fixed player damage path remains intact and has a selected regression test.

The pre-correction selected synthetic run had four failures: the engine did not accept a target chooser, and the interpreter reported the any-target/follow-up semantics unsupported. The frozen run itself records Pizza entering without a trigger or damage. The failing synthetic cases were retained and now pass.

## Validation

Code source tested: `28b40104df7ef7fb200f2d8f85316cdc04e287cf`.

- **20 passed, 0 failed, 0 skipped** across individually selected synthetic nodes. The selection includes the four Pizza cases, the revised Stage 002 Pizza reproduction, damage and state-based-action regressions, direct spell and Alliance damage cases, frozen semantic coverage locks, and two ETB stack/source-departure cases.
- Python 3.12.10; pytest 8.4.2; Ruff 0.16.1.
- Ruff format check passed; Ruff lint passed; `git diff --check` passed.
- No complete games, smoke runs, CI workflows, calibration, or deck changes were executed.

The exact test selection was:

```powershell
$env:PYTHONPATH='C:\projects\tmt\.smoke001-pizza-semantic-closure\src'
$env:PYTHONDONTWRITEBYTECODE='1'
& 'C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\python.exe' -B -m pytest -q `
  tests\test_spicy_oatmeal_pizza_trigger.py `
  tests\test_deal_damage_action.py::test_fixed_damage_program_is_oracle_derived_and_card_name_independent `
  tests\test_deal_damage_action.py::test_explicit_payload_exclusions `
  tests\test_deal_damage_action.py::test_fixed_damage_spell_uses_stack_transaction_and_retains_followup_limitation `
  tests\test_deal_damage_action.py::test_player_damage_is_transactional_and_emits_typed_evidence `
  tests\test_deal_damage_action.py::test_lethal_player_damage_uses_existing_life_loss_boundary `
  tests\test_deal_damage_action.py::test_creature_damage_is_marked_and_lethal_is_applied_only_by_sba `
  tests\test_deal_damage_action.py::test_alliance_damage_executes_only_through_supported_parent `
  tests\test_deal_damage_action.py::test_authoritative_memberships_and_digests_are_locked `
  tests\test_deal_damage_action.py::test_frozen_roster_memberships_are_locked `
  tests\test_smoke001_semantic_triage.py::test_spicy_pizza_damage_trigger_waits_for_priority_and_resolves_in_oracle_order `
  tests\test_etb_drain_gain_scry_action.py::test_source_can_leave_after_trigger_without_losing_entry_provenance `
  tests\test_etb_drain_gain_scry_action.py::test_simultaneous_triggers_remain_distinct_and_deterministic
```

Ruff checks covered the two engine modules and the three selected/added test modules listed in the PR diff. The tests call deterministic synthetic engine and reconciliation paths only; none invokes a game runner.

## Scope and limitation

The engine currently models player and creature damage targets but has no planeswalker target state. The frozen TMNT card/game model used for Smoke 001 contains no planeswalker target object; support for a future planeswalker target would require that engine model first. This correction does not alter the Pizza Food ability or any other unsupported Pizza semantics.

Changed files: `src/tmnt_design_studio/card_interpreter07.py`, `src/tmnt_design_studio/engine07.py`, `tests/test_spicy_oatmeal_pizza_trigger.py`, `tests/test_deal_damage_action.py`, `tests/test_smoke001_semantic_triage.py`, and this report.

## PR #388 acceptance closure (2026-11-06)

The independent review found that simultaneous life loss left `winner` unset, while the engine, Stage 002 runner, and snapshot serializer treated an unset winner as an unfinished game. The effect could therefore be reported as turn-limit incomplete, and continuation code did not have a reliable terminal predicate.

The bounded correction adds `Game.terminal`, derived from an assigned winner or a player's recorded loss. `check_life()` now clears priority when it records either an ordinary win or simultaneous loss. Terminal games reject step advancement, stack resolution, and new priority windows, and expose no main, priority, attack, block, or Sneak choices. Stage 002 continuation checks use the terminal state, so a draw is not continued or marked `acceptance_incomplete`. Snapshots and reconciliation reports carry the explicit terminal field while retaining `winner: null` for a draw.

The authenticated cast test now casts Pizza through `legal_main_actions` and `execute_main_action`. It verifies exactly one automatically stacked ETB trigger with its original source card, entry event, and event registry identity. The test then checks both priority passes share the same epoch; four damage precedes three controller damage; player and creature targets work; lethal creature state actions follow both damage events; a target removed before resolution gets no damage; and source departure does not remove trigger provenance. Both damage event IDs resolve through the authoritative execution index and the reconciler reports executed semantics without stop records. Separate checks cover simultaneous loss as terminal draw and preserve the ordinary single-winner outcome.

- Starting PR head: `d60a0e0319af2acf2f146a19bb15a31e62e0a1fa`.
- Code commit validated: `d49b04aee19b905c897d252074ea7ace32cc6dca` (`[skip ci]`).
- The report is a separate documentation commit; the final PR head is the report commit's SHA.
- Validation: **24 passed, 0 failed, 0 skipped**; Python 3.12.10, pytest 8.4.2, Ruff 0.16.1.
- Ruff formatting check, Ruff lint, and `git diff --check` passed for `engine07.py`, `stage002.py`, and `test_spicy_oatmeal_pizza_trigger.py`.
- No complete games, CI workflows, calibration, deck changes, or archive writes were performed.

The selected synthetic command used these individually named nodes (the parameterized Pizza cast node exercises self, opponent, and creature targets):

```powershell
$env:PYTHONPATH='C:\projects\tmt\.smoke001-pizza-semantic-closure\src'
$env:PYTHONDONTWRITEBYTECODE='1'
& 'C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\python.exe' -B -m pytest -q `
  tests\test_spicy_oatmeal_pizza_trigger.py::test_pizza_etb_target_damage_then_controller_damage_has_authenticated_priority `
  tests\test_spicy_oatmeal_pizza_trigger.py::test_pizza_trigger_resolves_after_source_leaves_and_simultaneous_lethal_effects `
  tests\test_spicy_oatmeal_pizza_trigger.py::test_ordinary_life_loss_remains_a_terminal_win `
  tests\test_spicy_oatmeal_pizza_trigger.py::test_normal_pizza_cast_auto_stacks_and_resolves_one_authenticated_trigger `
  tests\test_spicy_oatmeal_pizza_trigger.py::test_pizza_trigger_with_illegal_target_does_not_deal_either_damage `
  tests\test_spicy_oatmeal_pizza_trigger.py::test_pizza_damage_semantics_are_card_name_independent_and_fully_supported `
  tests\test_deal_damage_action.py::test_fixed_damage_program_is_oracle_derived_and_card_name_independent `
  tests\test_deal_damage_action.py::test_explicit_payload_exclusions `
  tests\test_deal_damage_action.py::test_fixed_damage_spell_uses_stack_transaction_and_retains_followup_limitation `
  tests\test_deal_damage_action.py::test_player_damage_is_transactional_and_emits_typed_evidence `
  tests\test_deal_damage_action.py::test_lethal_player_damage_uses_existing_life_loss_boundary `
  tests\test_deal_damage_action.py::test_creature_damage_is_marked_and_lethal_is_applied_only_by_sba `
  tests\test_deal_damage_action.py::test_alliance_damage_executes_only_through_supported_parent `
  tests\test_deal_damage_action.py::test_authoritative_memberships_and_digests_are_locked `
  tests\test_deal_damage_action.py::test_frozen_roster_memberships_are_locked `
  tests\test_smoke001_semantic_triage.py::test_spicy_pizza_damage_trigger_waits_for_priority_and_resolves_in_oracle_order `
  tests\test_etb_drain_gain_scry_action.py::test_source_can_leave_after_trigger_without_losing_entry_provenance `
  tests\test_etb_drain_gain_scry_action.py::test_simultaneous_triggers_remain_distinct_and_deterministic
```

Remaining limitation: planeswalkers are not represented as damage targets in the current engine. No planeswalker behavior was added.
