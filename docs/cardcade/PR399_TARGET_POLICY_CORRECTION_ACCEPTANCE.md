# PR #399 Punks Target-Policy Correction

## Source identity

- Starting PR #399 HEAD: `beb5e24e38384b1b0ca0d055240c70e1833e1858`.
- Implementation branch: `review/cardcade-punks-target-policy-correction`.
- Worktree: `C:\projects\tmt\.cardcade-punks-target-policy-correction`.
- Tested code commit: `d7a99aced66cd94998298356315d335f307017fe`.
- Target/base branch: `review/cardcade-punks-followup-correction` (PR #399).
- The implementation commit contains `[skip ci]`.
- PRs #397, #398, #399, and #400 source branches were not changed.

## Preserved PR #400 failure

The reviewer reproduction was copied from PR #400's committed branch with matching blob
`8cdaeea2b8c9af7d409abe1a33d5971ce7747b46`:

`tests/test_pr399_independent_audit_repro.py::test_punks_followup_preserves_existing_target_policy_for_targeted_casts`

It failed at the exact starting PR #399 HEAD. The control fixture activated Punks, then asked
the existing damage-stage policy to choose among two legal target options. That policy selected
the 1/1, which died to three damage. Through the PR #399 Stage 002 driver, the first-listed 5/5
was damaged instead and the 1/1 remained. The PR #400 report retains the original REWORK
finding and audit history.

## Correction

Stage 002 now keeps the advertised follow-up descriptors across the existing cast stages and
collects all currently legal options matching the first available descriptor. It still obtains
the options from `Game.legal_main_actions` and executes only a returned engine option.

- A single legal cast option is executed directly; there is no target choice to make.
- If an advertised cast has several legal target variants, Stage 002 defers it from the
  activation stage. At the existing damage, destroy, or creature stage, it passes only those
  matching cast variants and the legal PASS option to the existing pilot policy. A selected
  matching variant executes normally; an unrelated spell or ability cannot preempt it.
- If the pilot declines at one cast stage, the descriptor remains pending for the next existing
  cast stage. If no current legal action still matches, the hint is discarded and the normal
  pilot policy resumes.
- Matching activated-ability follow-ups remain selected as before. The immediate mana ability,
  three-attempt activation bound, payment validation, and priority/Stack flow are unchanged.

The code adds no card-name, deck, or opponent-specific target policy. The copied PR #400
reproduction now passes, as do the original PR #398 artifact-cast reproduction and the
activated-ability follow-up regression.

## Synthetic validation

Environment: Python 3.12.10, pytest 8.4.2, Ruff 0.16.1, using the existing environment at
`C:\projects\tmt\.cardcade-fidelity-correction\.venv`. `PYTHONPATH` pointed to this worktree's
`src` directory. The environment was not rebuilt or modified.

The run retained the original 68 named nodes (72 parameter-expanded cases): the 54 nodes listed
in `PILOT_FIDELITY_CORRECTION_ACCEPTANCE.md` plus these 14 supplemental nodes:

- `tests/test_pr397_independent_audit_repro.py::test_pizza_target_policy_ranks_terminal_outcomes`
- `tests/test_pr397_independent_audit_repro.py::test_pilot_executes_the_artifact_followup_that_justified_punks_mana`
- `tests/test_restricted_spell_payment.py::test_repeated_ledger_payment_planning_is_pure_and_deterministic`
- `tests/test_restricted_spell_payment.py::test_legal_action_planning_is_repeatable_and_does_not_authorize_payment`
- `tests/test_restricted_spell_payment.py::test_spell_payment_snapshot_reconciles_without_invented_execution_reference`
- `tests/test_restricted_ability_payment.py::test_activation_action_enumeration_is_repeatable_and_pure`
- `tests/test_restricted_ability_payment.py::test_activation_payment_snapshot_reconciles_exact_source_and_allocation`
- `tests/test_frog_butler_mana.py::test_frog_butler_produces_chosen_color_with_source_provenance`
- `tests/test_frog_butler_mana.py::test_frog_butler_mana_ability_rejects_summoning_sick_source`
- `tests/test_frog_butler_mana.py::test_frog_butler_mana_is_immediate_and_empties_at_step_end`
- `tests/test_spicy_oatmeal_pizza_trigger.py::test_pizza_trigger_with_illegal_target_does_not_deal_either_damage`
- `tests/test_pilot_fidelity_correction.py::test_main_action_driver_prefers_advertised_activated_ability_followup`
- `tests/test_pilot_fidelity_correction.py::test_unavailable_advertised_followup_is_ignored_in_favor_of_current_options`
- `tests/test_pilot_fidelity_correction.py::test_main_action_followup_rechecks_stop_after_three_mana_activations`

Three further nodes were added for this correction:

- `tests/test_pr399_independent_audit_repro.py::test_punks_followup_preserves_existing_target_policy_for_targeted_casts`
- `tests/test_pilot_fidelity_correction.py::test_punks_targeted_artifact_followup_executes_when_one_legal_target_exists`
- `tests/test_pilot_fidelity_correction.py::test_followup_identity_ignores_unrelated_legal_cast_options`

At tested code SHA `d7a99aced66cd94998298356315d335f307017fe`, the 71 named nodes returned
**75 passed, 0 failed, 0 skipped**. Coverage includes the preserved multi-target failure,
single-target and untargeted casts, matching activated abilities, stale descriptors, unrelated
legal cast filtering, the original PR #398 follow-up, bounded continuation, planning purity,
restricted-mana lineage, priority, Pizza, April, Ravenous Robots, Frog Butler, and snapshot/
reconciliation checks.

Commands, run from the implementation worktree:

```powershell
$env:PYTHONPATH='C:\projects\tmt\.cardcade-punks-target-policy-correction\src'
# $nodes is the named selection documented above and in the referenced acceptance reports.
& 'C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\python.exe' -B -m pytest -q @nodes
& 'C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\ruff.exe' format --check src/tmnt_design_studio/stage002.py tests/test_pilot_fidelity_correction.py tests/test_pr397_independent_audit_repro.py tests/test_pr399_independent_audit_repro.py
& 'C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\ruff.exe' check src/tmnt_design_studio/stage002.py tests/test_pilot_fidelity_correction.py tests/test_pr397_independent_audit_repro.py tests/test_pr399_independent_audit_repro.py
git diff --check HEAD^ HEAD
```

Ruff format check passed (4 files already formatted), Ruff lint passed, and `git diff --check`
passed. No complete games, smoke runs, calibration, deck changes, merges, or historical evidence
modifications were performed.

## Changed files

- `src/tmnt_design_studio/stage002.py`
- `tests/test_pilot_fidelity_correction.py`
- `tests/test_pr399_independent_audit_repro.py` (copied audit reproduction, now passing)
- `docs/cardcade/PR399_TARGET_POLICY_CORRECTION_ACCEPTANCE.md`

## Handoff

This is an implementation candidate and evidence report for independent HQ re-audit. No
self-acceptance is claimed.
