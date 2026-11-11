# Purple Dragon Punks Mana Ability Acceptance

## Source identity and frozen card record

- Authorized starting commit: `0d6f77ebcb39c4a58ddc74f388de58a309ce08e2` (`review/cardcade-restricted-ability-payments`, PR #394).
- Isolated worktree: `C:\projects\tmt\.cardcade-purple-dragon-mana`.
- Working branch: `review/cardcade-purple-dragon-mana`.
- Preserved failing reproduction: `ca6e7f5486125052e842e96f3410c38914b42070`.
- Tested implementation commit: `cae259fc07228dd96fa59d109b4103dca0ba212e`.
- Final report commit: recorded in the follow-on PR body.
- Frozen authoritative snapshot: `cardcade/scryfall-tmt-pza-tmc-2026-08-13.json`, SHA-256 `56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402`.
- Frozen snapshot manifest SHA-256: `6b5271af75150a361f77e7b89306c709959dfdf497c448dfdc978e5dc9a17950`.
- Card: Purple Dragon Punks; Scryfall ID `bbe1d7e5-68e2-4458-aa3f-5e97fa8e7cae`; Oracle ID `d1edb950-a118-4b4d-a0ef-9a6683d74c9f`.
- Frozen type line / cost: `Creature — Human Rogue`, `{1}{R}`.
- Frozen Oracle text: `{T}: Add {R}. Spend this mana only to cast an artifact spell or to activate an ability.`

Accepted main remains `10d2ac80ef5b81b3a209a3133eb0a84633a1f944`. The implementation starts from PR #394 and leaves prior draft refs, frozen decks, Baseline 005, and Smoke 001 artifacts unchanged.

## Behavior implemented

The interpreter recognizes the bounded fixed-color restricted-mana instruction from its Oracle grammar; it does not dispatch on card name. The parsed program records one red mana and the two spending contexts `artifact_spell` and `activated_ability`.

The engine uses its existing tap-source legality, including summoning sickness and haste. Activation taps the source, creates the existing authenticated activation identity, and immediately adds one red production lot to `FloatingManaLedger`. The ability never enters the Stack and does not open a new priority epoch. A repeated activation is rejected while the source remains tapped.

The production lot preserves controller, source object, production event/activation object, color, quantity, allowed contexts, and step-end expiration. The existing typed payment planner accepts it for artifact spells and supported activated abilities, rejects it for nonartifact spells, and supports mixed floating mana plus lands. Expiry invalidates the lot while preserving production and expiration history. Mana remains spendable in an allowed context if the producing permanent leaves after activation.

`floating_mana_produced` records include source Oracle identity/type line, Oracle fragment, controller, output, and allowed contexts. Snapshot serialization retains the ledger restrictions and exact consumption allocations. The selected reconciler test confirms legitimate activation and payment provenance without stop records or invented references; the authenticated mana-ability execution is present with its actual source and Oracle fragment.

## Preserved reproduction

At `ca6e7f5486125052e842e96f3410c38914b42070`, the individually selected test
`tests/test_purple_dragon_mana.py::test_frozen_purple_dragon_punks_mana_ability_is_offered_and_activates`
failed because the frozen card's legal activation was absent from `legal_main_actions`.

## Validation

Environment: Python `3.12.10`, pytest `8.4.2`, Ruff `0.16.1`. Python executable: `C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\python.exe`. The exact tested source was `cae259fc07228dd96fa59d109b4103dca0ba212e`.

The final explicit pytest selection contained 27 individually named nodes:

```text
tests/test_purple_dragon_mana.py::test_frozen_purple_dragon_punks_mana_ability_is_offered_and_activates
tests/test_purple_dragon_mana.py::test_summoning_sick_punks_cannot_tap_for_mana_without_mutation
tests/test_purple_dragon_mana.py::test_haste_allows_summoning_sick_punks_mana_activation
tests/test_purple_dragon_mana.py::test_tapped_punks_cannot_activate_again_or_duplicate_mana
tests/test_purple_dragon_mana.py::test_punks_mana_is_immediately_available_during_priority_without_epoch_change
tests/test_purple_dragon_mana.py::test_restricted_punks_mana_pays_artifact_spell_with_exact_lineage
tests/test_purple_dragon_mana.py::test_restricted_punks_mana_cannot_pay_nonartifact_spell
tests/test_purple_dragon_mana.py::test_restricted_punks_mana_pays_supported_activated_ability
tests/test_purple_dragon_mana.py::test_restricted_punks_mana_combines_with_land_and_leaves_payment_provenance
tests/test_purple_dragon_mana.py::test_unspent_punks_mana_expires_at_step_boundary_with_source_history
tests/test_purple_dragon_mana.py::test_produced_restricted_mana_remains_spendable_after_source_leaves
tests/test_purple_dragon_mana.py::test_punks_activation_and_following_ability_reconcile_without_fabricated_execution
tests/test_purple_dragon_mana.py::test_frozen_card_identity_and_interpreter_contract_are_not_name_dispatched
tests/test_frog_butler_mana.py::test_frog_butler_produces_chosen_color_with_source_provenance
tests/test_frog_butler_mana.py::test_frog_butler_mana_ability_rejects_summoning_sick_source
tests/test_frog_butler_mana.py::test_frog_butler_mana_is_immediate_and_empties_at_step_end
tests/test_pr386_final_fidelity_gate.py::test_frog_mana_action_produces_pays_and_expires_with_authenticated_lineage
tests/test_pr386_final_fidelity_gate.py::test_frog_mana_ability_is_an_immediate_priority_action_with_color_choice
tests/test_restricted_ability_payment.py::test_activation_mana_plan_rejects_stale_and_forged_ledger_allocations
tests/test_restricted_ability_payment.py::test_hand_landcycling_uses_activation_context_and_authenticated_allocation
tests/test_tunnel_rats_graveyard_return.py::test_tunnel_rats_spends_floating_black_mana_and_four_generic_sources
tests/test_tunnel_rats_graveyard_return.py::test_tunnel_rats_can_activate_at_priority_and_remains_in_graveyard_until_resolution
tests/test_restricted_spell_payment.py::test_artifact_spell_uses_restricted_mana_and_snapshots_exact_cast_linkage
tests/test_restricted_spell_payment.py::test_nonartifact_cannot_spend_artifact_only_mana_but_can_use_unrestricted_mana
tests/test_restricted_spell_payment.py::test_mixed_restricted_unrestricted_and_land_payment_preserves_partial_lot
tests/test_restricted_spell_payment.py::test_multicolor_and_hybrid_spending_uses_typed_lots_and_land_sources
tests/test_restricted_spell_payment.py::test_spell_payment_snapshot_reconciles_without_invented_execution_reference
```

Result: **27 passed, 0 failed, 0 skipped**. The compatibility selection includes Frog Butler, activated payment object identity, hand landcycling, Tunnel Rats, hybrid spell payment, and spell evidence reconciliation. No complete games or game runners were executed.

Quality checks:

```powershell
& 'C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\ruff.exe' format --check src/tmnt_design_studio/card_interpreter07.py src/tmnt_design_studio/engine07.py tests/test_purple_dragon_mana.py
& 'C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\ruff.exe' check src/tmnt_design_studio/card_interpreter07.py src/tmnt_design_studio/engine07.py tests/test_purple_dragon_mana.py
git diff --check 0d6f77ebcb39c4a58ddc74f388de58a309ce08e2
```

Ruff format reported the files already formatted; Ruff lint passed; `git diff --check` passed.

## Remaining limitations

- The interpreter supports the exact restricted fixed-color mana instruction shape used by this frozen Oracle clause. Other restricted-mana sentence grammars remain unsupported and fail closed.
- Pilot priority choice was not changed; this checkpoint validates engine legal-action exposure and execution directly.
- Purple Dragon Punks is implemented through the generic parsed instruction and existing mana ledger, not through a card-name-specific payment exception.
- No merges, complete games, smoke tests, calibration, or deck changes were made.

**Recommendation: READY FOR HQ REVIEW.**
