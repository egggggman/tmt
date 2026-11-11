# Diagnostic Launcher Safety Correction

## Source and scope

- Starting source: PR #415 at `188da5fabc231c91b222c642b6c9cf6fe4377c9f`.
- Correction branch: `fix/cardcade-diagnostic-launcher-safety`.
- Tested code before this report: `83d199658b058a3d2dfd8c192fc8d60974f8ce0b`.
- The code and tests are based on the exact PR #415 source. PR #415 and its branch were not changed.
- Python 3.12.10, pytest 8.4.2, Ruff 0.16.1; environment: `C:\projects\tmt\.cardcade-fidelity-correction\.venv`.
- No gameplay loop or complete game was executed. Synthetic executors construct initial state and snapshots only.

## Preserved RED findings

The reproductions were committed first as `bda3868` and executed against the uncorrected starting implementation. All three failed as expected:

1. `tests/test_cardcade_diagnostic_launcher_safety.py::test_exact_source_pin_rejects_approved_ancestor_descendant` showed that an approved ancestor could authorize a descendant checkout.
2. `tests/test_cardcade_diagnostic_launcher_safety.py::test_failed_reconciliation_persists_evidence_and_blocks_cli` showed that a normally returning executor could be reported as a successful command despite failed reconciliation.
3. `tests/test_cardcade_diagnostic_launcher_safety.py::test_cross_process_authorization_claim_is_exclusive` showed that separate launcher instances/processes could dispatch the same authorization.

The corrected implementation and those same cases now pass. Additional correction work surfaced a fourth persistence boundary: an `OSError` while writing the snapshot was being classified as a reconciliation blocker. It now raises `EvidencePersistenceError` and cannot be mistaken for complete persisted evidence. The existing `test_persistence_failure_after_synthetic_execution_is_never_retried` covers that path.

## Authorization contract

The command requires two explicit, separate JSON files:

- `cardcade-reviewed-implementation-v1`: `approval_id`, exact `implementation_sha`, and the exact `input_sha256` map.
- `cardcade-diagnostic-run-authorization-v1`: unique `authorization_id`, `source_approval_id`, the same exact implementation SHA and input map, and the fixed game ID, pairing, orientation, and seed.

The checked-out HEAD must equal both approved SHAs exactly. The launcher no longer treats ancestry from the old PR #415 source as implementation approval. It verifies the imported `engine07` and `stage002` paths are inside the checkout and share the same `Game` class. Accepted main must remain `10d2ac80ef5b81b3a209a3133eb0a84633a1f944`.

The launcher rehashes these six frozen inputs and compares them with both authorization documents and the compiled allowlist:

| Input | SHA-256 |
| --- | --- |
| `src/tmnt_design_studio/stage002.py` | `69ecb217234ac892509de0fbe6417601826909b3fceba77f4a865d4959db8f1b` |
| `decks/april_oneil/PROTOTYPE_0.1.txt` | `684c898760a39c5dfc584206ef4675c49d96cfe6bd419f03f86bd0b8358d09f4` |
| `decks/casey_jones/PROTOTYPE_0.1.txt` | `0fc0adbb370ecfddad03692a4229a04b23268739914a8f2a004b8e042ff3cebb` |
| `cardcade/scryfall-tmt-pza-tmc-2026-08-13.json` | `56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402` |
| `cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json` | `6b5271af75150a361f77e7b89306c709959dfdf497c448dfdc978e5dc9a17950` |
| `docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json` | `532bad7e489eb25f3184b5a90487e1361f7a2b19b8c02cac3c4115a0fc3e14bc` |

The approval documents are explicit inputs, are hashed into run metadata, and are not generated from the current checkout. This implementation does not cryptographically sign or verify the issuing authority; HQ must deliver the approval documents through its trusted process. Independent review should decide whether a signature/key-verification mechanism is required before a real run.

## Durable one-use claim

Immediately before executor dispatch, the launcher atomically creates a claim using exclusive file creation (`O_CREAT | O_EXCL`). Claims live in `.cardcade-diagnostic-claims` beside the Git common directory, so linked worktrees, output directories, launcher instances, and separate processes share the same authorization namespace. The claim records the authorization ID and the implementation/approval identities and is never removed after execution failure, crash, or incomplete reconciliation. Existing claims reject dispatch. The invocation has a local one-call guard and no retry path.

## Acceptance status and failure handling

A normal executor return is accepted only when the snapshot is terminal, has presence and event evidence, contains no invariant-violation or acceptance-incomplete event, and reconciliation exists with empty stop-record and invariant-violation lists. Otherwise `run_status.json` records `BLOCKED` and the CLI exits nonzero. Reconciliation exceptions and invalid/missing evidence are retained in the output. Snapshot evidence write errors raise `EvidencePersistenceError`; the durable claim remains consumed.

Output must be a fresh direct child of `.cardcade-diagnostic-runs`; symlinks and overwrites are rejected. The command remains pinned to April vs. Casey, canonical orientation, seed 7231. It has no retry, pairing expansion, seed expansion, batch, or calibration path.

## Synthetic validation

Exact combined selection, run from the clean correction worktree:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; & C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\python.exe -B -m pytest -q `
  tests\test_cardcade_diagnostic_launcher.py::test_synthetic_success_serializes_reconciliation_and_integrity_hashes `
  tests\test_cardcade_diagnostic_launcher.py::test_injected_failure_preserves_original_exception_and_bound_snapshot `
  tests\test_cardcade_diagnostic_launcher.py::test_failure_before_binding_is_persisted_without_fabricated_snapshot `
  tests\test_cardcade_diagnostic_launcher.py::test_launcher_instance_cannot_be_reused_for_second_invocation `
  tests\test_cardcade_diagnostic_launcher.py::test_existing_output_directory_is_rejected_before_executor_call `
  tests\test_cardcade_diagnostic_launcher.py::test_persistence_failure_after_synthetic_execution_is_never_retried `
  tests\test_cardcade_diagnostic_launcher.py::test_committed_match_configuration_is_exact `
  tests\test_cardcade_diagnostic_launcher.py::test_output_directory_cannot_escape_isolated_diagnostic_root `
  tests\test_cardcade_diagnostic_launcher_safety.py::test_exact_source_pin_rejects_approved_ancestor_descendant `
  tests\test_cardcade_diagnostic_launcher_safety.py::test_source_approval_and_run_authorization_are_separate_exact_records `
  tests\test_cardcade_diagnostic_launcher_safety.py::test_unapproved_frozen_input_hash_fails_before_executor_call `
  tests\test_cardcade_diagnostic_launcher_safety.py::test_cross_process_authorization_claim_is_exclusive `
  tests\test_cardcade_diagnostic_launcher_safety.py::test_claim_survives_execution_failure_and_blocks_fresh_instance `
  tests\test_cardcade_diagnostic_launcher_safety.py::test_failed_reconciliation_persists_evidence_and_blocks_cli `
  tests\test_cardcade_diagnostic_launcher_safety.py::test_blocking_reconciliation_findings_produce_blocked_status `
  tests\test_cardcade_diagnostic_launcher_safety.py::test_missing_reconciliation_report_is_not_accepted `
  tests\test_cardcade_diagnostic_launcher_safety.py::test_nonterminal_normal_return_is_incomplete_and_not_accepted `
  tests\test_cardcade_diagnostic_launcher_safety.py::test_nonterminal_cli_result_exits_nonzero `
  tests\test_cardcade_diagnostic_launcher_safety.py::test_missing_presence_evidence_blocks_normal_return `
  tests\test_diagnostic_capture.py::test_nested_failure_uses_explicit_runner_binding_not_innermost_game_local `
  tests\test_diagnostic_capture.py::test_run_game_exception_capture_preserves_presence_and_authenticates_token `
  tests\test_diagnostic_capture.py::test_missing_or_ambiguous_runner_binding_fails_closed_without_hiding_error `
  tests\test_diagnostic_capture.py::test_capture_finalizes_a_copy_of_presence_without_mutating_live_ledger `
  tests\test_diagnostic_capture.py::test_reused_capture_does_not_attach_previous_game_to_unbound_failure `
  tests\test_diagnostic_capture.py::test_unprintable_snapshot_capture_error_does_not_mask_original_exception `
  tests\test_diagnostic_capture.py::test_non_game_success_after_failure_clears_stale_failure_and_binding `
  tests\test_diagnostic_capture.py::test_run_game_without_capture_preserves_setup_exception `
  tests\test_diagnostic_capture.py::test_presence_finalization_and_traceback_format_failures_keep_original_exception `
  tests\test_diagnostic_capture.py::test_failure_inside_capture_bookkeeping_cannot_replace_execution_exception `
  tests\test_strike_damage_steps.py::test_lethal_first_strike_damage_ends_without_advancing_terminal_combat `
  tests\test_strike_damage_steps.py::test_lethal_regular_damage_ends_without_terminal_transition_or_duplicate_damage `
  tests\test_strike_damage_steps.py::test_lethal_first_strike_sba_removes_blocker_before_regular_step `
  tests\test_strike_damage_steps.py::test_no_strike_combat_retains_one_regular_damage_step `
  tests\test_strike_damage_steps.py::test_combat_damage_steps_cannot_be_skipped_repeated_or_resolved_out_of_order `
  tests\test_strike_damage_steps.py::test_failed_transition_does_not_clear_or_fabricate_live_combat_state
```

Result on code HEAD `83d199658b058a3d2dfd8c192fc8d60974f8ce0b`: **36 passed, 0 failed, 0 skipped**. The cross-process test launches two spawned worker processes; exactly one can claim the authorization. The synthetic acceptance fixture never invokes gameplay.

Quality checks on the same source:

- `ruff format --check` on the launcher and its two named test files: passed.
- `ruff check` on those three Python files: passed.
- `git diff --check` and commit-range whitespace check: passed.

## Historical evidence preservation

The nine preserved PR #406 Diagnostic Game 001 artifacts were rehashed read-only. All full SHA-256 values match the retained manifest:

- `events.json`: `e25d42bb57d75bc9ae0d1400d3abc840a67c9908f28c35e0d26a6ff31b245bec`
- `exception.json`: `d9c2de38b2604a149eec2b693e337bc7ed36713f202f8d4050bb16660b2dd3d3`
- `priority_stack_combat_trace.json`: `94d7f067506ce754479b5a718153c8fc1b354f37b5c0dd0c826b0561717754b5`
- `reconciliation.json`: `7e943b7cde607cff0bea4018447a4b33f6a74244d2efb997a6fd7be875a65425`
- `run_metadata.json`: `9ad906f7339f2e72b4f8321b4eef47abb8992ff862bfee344915eea5edbc3272`
- `run_once.py`: `aa2004aff460142ee20114466f9bb291d78d24283cadf855afc12aaf7a49bae0`
- `run_status.json`: `532ac90c2c82dbd9dbc3ddbe6ce9b047133afdc2bca3c02a1a1a222f102c5cf8`
- `snapshot.json`: `53092f2e688c6b6f158d5012419a95fa31f948bbcb115184a13809e65962142a`
- `stage_manifest.json`: `414b6ec1482c0e1874f8685479781071786f3ab1bb27448a5a5161bd1152fcbb`

The historical three reconciliation stop records remain untouched. No deck, Baseline 005, accepted-main, or Smoke 001 artifact was modified.

## Limitations and handoff

Synthetic tests establish the launcher contracts but do not establish gameplay completion, and no gameplay was run. The approval files rely on an external HQ issuance channel rather than a cryptographic signature. Independent review should inspect the authority trust model, persistence-failure behavior, and claim lifecycle before any authorization is issued for a complete game.

**Recommendation: READY FOR INDEPENDENT ACCEPTANCE REVIEW.** No authorization for Diagnostic Game 002 is included in this change.
