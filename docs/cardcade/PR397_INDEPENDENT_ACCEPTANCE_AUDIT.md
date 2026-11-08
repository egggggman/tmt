# PR #397 Independent Acceptance Audit

## Audit identity

- Candidate: [PR #397](https://github.com/egggggman/tmt/pull/397), reviewed as published.
- Candidate base: `review/cardcade-purple-dragon-mana` at `7ed476f4ded0ed59292f019320b3331688f2d2e4`.
- Tested code commit: `dd14b5b05ffd8d535c572deb749cfd2019be4b3f`.
- Candidate PR HEAD: `29aa3998e06ed1e6b1d399d4a65e18188d9481be`.
- Reviewer worktree: `C:\projects\tmt\.review-pr397-independent`.
- Audit branch: `review/cardcade-pr397-independent-audit`, based on the exact PR HEAD.
- Runtime: Python 3.12.10, pytest 8.4.2, Ruff 0.16.1.
- Accepted main observed in the checkout remains `10d2ac80ef5b81b3a209a3133eb0a84633a1f944`.

The review worktree was clean at PR HEAD before adding this report and one independent synthetic reproduction. No candidate source, deck, baseline, or historical artifact was changed. The candidate diff from PR #395 contains only its pilot, engine option metadata, Stage 002 driver, tests, and acceptance report; it contains no Baseline 005 or Smoke 001 artifact paths.

## Independent validation

The 54 node IDs enumerated in `PILOT_FIDELITY_CORRECTION_ACCEPTANCE.md` were independently run with the reviewer worktree's `src` set on `PYTHONPATH`:

```powershell
$env:PYTHONPATH='C:\projects\tmt\.review-pr397-independent\src'
& 'C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\python.exe' -B -m pytest -q <the 54 enumerated node IDs>
```

Result: **56 passed, 0 failed, 0 skipped**. The parameterized Pizza cast node expands the selected node count. These modules contain deterministic Game fixtures; a source scan found no complete-game runner invocation in the selected test files.

Nine additional named checks passed (**9 passed**):

- `tests/test_restricted_spell_payment.py::test_repeated_ledger_payment_planning_is_pure_and_deterministic`
- `tests/test_restricted_spell_payment.py::test_legal_action_planning_is_repeatable_and_does_not_authorize_payment`
- `tests/test_restricted_spell_payment.py::test_spell_payment_snapshot_reconciles_without_invented_execution_reference`
- `tests/test_restricted_ability_payment.py::test_activation_action_enumeration_is_repeatable_and_pure`
- `tests/test_restricted_ability_payment.py::test_activation_payment_snapshot_reconciles_exact_source_and_allocation`
- `tests/test_frog_butler_mana.py::test_frog_butler_produces_chosen_color_with_source_provenance`
- `tests/test_frog_butler_mana.py::test_frog_butler_mana_ability_rejects_summoning_sick_source`
- `tests/test_frog_butler_mana.py::test_frog_butler_mana_is_immediate_and_empties_at_step_end`
- `tests/test_spicy_oatmeal_pizza_trigger.py::test_pizza_trigger_with_illegal_target_does_not_deal_either_damage`

Three additional Pizza outcome cases passed: a win over a creature target, a draw over a loss from mandatory self-damage, and the least-damaging choice when every option still loses. Ruff format and lint passed on the independent reproduction file.

## Findings

### Pizza target scoring — ACCEPT

The scorer uses only engine-offered IDs and the controller's `GameViewV2`. The selected and supplemental cases confirm it accounts for four target damage and three mandatory controller damage, distinguishes win/draw/loss, prefers an available win, prefers a draw over a loss, and uses creature lethal damage when it preserves an equal-or-better terminal result. The runner wiring passes the current controller's view to the callback. No Pizza decision defect was reproduced within the represented target model.

The policy is an immediate-state heuristic. It is not a multi-turn search, and the engine still owns legality and resolution.

### Restricted mana purity, payment, and priority — ACCEPT WITH A MAIN-PHASE DEFECT

The independent purity tests confirm repeated legal-action and payment planning does not change authoritative state or mint payment authorization. Existing selected payment and reconciliation regressions pass. Frog Butler's immediate production, source provenance, summoning-sickness rejection, and step-end expiry also pass.

The priority synthetic case passes: Punks is offered when its restricted mana can enable Frog Butler's Reach activation during the defending player's priority window; after production, the engine re-enumerates the real action, marks its actual restricted-lot payment, and the pilot selects it. The three-attempt cap bounds the main-stage continuation. No complete game or priority loop ran.

### Blocking pilot defect: main-phase selection ignores the follow-up it advertised

The candidate attaches `mana_followups` to the Punks option and selects Punks because the descriptor says an artifact creature spell will become payable. After producing mana, `_run_main_action_stages` re-enters the generic `activate` stage. `AcceptancePilot` then selects the first legal activation, without matching it against the Punks option's follow-up descriptors. That action can consume the restricted mana before the artifact-cast stage.

The independent red reproduction is preserved as `tests/test_pr397_independent_audit_repro.py::test_pilot_executes_the_artifact_followup_that_justified_punks_mana`. Its fixture has Punks, one Forest, an already-legal synthetic `{1}` first-strike activation, and an artifact creature costing `{R}`. Before production, the artifact cast is absent from legal actions, while the Punks option advertises exactly that cast. After `_run_main_action_stages`:

- Punks produces one authenticated red mana.
- The unrelated first-strike ability is announced and consumes that exact production event under `activated_ability`.
- The Forest remains untapped.
- The artifact creature remains in hand because the remaining Forest cannot pay `{R}`.

The independent assertion that the artifact leaves the hand therefore fails at PR #397 HEAD (`artifact.zone == "hand"`, expected `"former"`). This is a synthetic partial-main-phase reproduction, not a complete game. It demonstrates that the claimed hypothetical follow-up can be displaced by an already-legal activation and that the pilot can lose the very artifact opportunity that justified Punks.

## Recommended correction boundary

Carry the selected engine-generated follow-up identity into the bounded recheck. Prefer still-legal matching actions before unrelated activations; when the described follow-up is a cast, advance to the existing cast-selection stage before paying another ability. Revalidate against freshly generated options and retain the current hard continuation cap. Do not execute the advisory descriptor itself or bypass engine payment validation.

## Verdict

**REWORK.** The full reported selection passes independently, Pizza selection and purity checks pass, and priority behavior is supported by the selected synthetic case. The main-phase follow-up mismatch is a reproducible acceptance failure for the requested Punks decision behavior. PR #397 should remain draft and unmerged until the follow-up ordering is corrected and the preserved red reproduction passes.

No complete games, Smoke 001 restart, calibration, deck revisions, merge, or unrestricted CI were run or authorized.
