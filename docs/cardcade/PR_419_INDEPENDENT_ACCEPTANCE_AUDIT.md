# PR #419 Independent Acceptance Audit

## Verdict: REWORK

The Ed25519 authorization correction closes the unsigned-approval defect, and the selected launcher, capture, terminal-combat, and authorization regressions pass independently. PR #419 does not yet establish reconciliation authenticity: a structurally complete report with a valid recomputed digest can contain falsified derived reconciliation data and still be accepted as `READY`.

## Source and environment

- Audited PR #419 published HEAD: `98e7a3a3e7247bb685d82f7200c791365d592365`.
- Its implementation parent: `8e6fd7e74b4f76c992bc30b4f4e231184d2f5b84`.
- PR #417 historical source: `6ded938a7680e767f9ac5e231774591ef461a27b`.
- Reviewer worktree: `.audit-pr419-independent`; tests imported `tools.cardcade_diagnostic_launcher` from that worktree.
- Runtime: Python 3.12.10, pytest 8.4.2, cryptography 46.0.7.
- No gameplay loop, complete game, or real authorization was run or issued.

## Historical RED and candidate GREEN

On PR #417, the two PR #418 behaviors were reproduced with setup-only synthetic execution: unsigned caller-created approval JSON passed source verification; and a terminal-marked synthetic snapshot paired with the incomplete report `{"stop_records": [], "invariant_violations": []}` was reported `READY` with exit code 0.

On PR #419, `test_unsigned_authorization_documents_are_rejected` and `test_incomplete_stage002_reconciliation_cannot_return_ready` pass. The full selected regression selection also passed (details below). These tests establish correction of those two original cases; they do not establish authenticity of all derived fields in a complete report.

## Independent 49-case selection

The exact named nodes were run in three batches to keep output bounded. All commands used:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; & 'C:\projects\tmt\.cardcade-diagnostic-auth-reconciliation-correction\.venv\Scripts\python.exe' -B -m pytest -q <the explicit node IDs below>
```

The exact node selection was:

```text
tests/test_cardcade_diagnostic_launcher.py::test_synthetic_success_serializes_reconciliation_and_integrity_hashes
tests/test_cardcade_diagnostic_launcher.py::test_injected_failure_preserves_original_exception_and_bound_snapshot
tests/test_cardcade_diagnostic_launcher.py::test_failure_before_binding_is_persisted_without_fabricated_snapshot
tests/test_cardcade_diagnostic_launcher.py::test_launcher_instance_cannot_be_reused_for_second_invocation
tests/test_cardcade_diagnostic_launcher.py::test_existing_output_directory_is_rejected_before_executor_call
tests/test_cardcade_diagnostic_launcher.py::test_persistence_failure_after_synthetic_execution_is_never_retried
tests/test_cardcade_diagnostic_launcher.py::test_committed_match_configuration_is_exact
tests/test_cardcade_diagnostic_launcher.py::test_output_directory_cannot_escape_isolated_diagnostic_root
tests/test_cardcade_diagnostic_launcher_safety.py::test_exact_source_pin_rejects_approved_ancestor_descendant
tests/test_cardcade_diagnostic_launcher_safety.py::test_source_approval_and_run_authorization_are_separate_exact_records
tests/test_cardcade_diagnostic_launcher_safety.py::test_unapproved_frozen_input_hash_fails_before_executor_call
tests/test_cardcade_diagnostic_launcher_safety.py::test_cross_process_authorization_claim_is_exclusive
tests/test_cardcade_diagnostic_launcher_safety.py::test_claim_survives_execution_failure_and_blocks_fresh_instance
tests/test_cardcade_diagnostic_launcher_safety.py::test_failed_reconciliation_persists_evidence_and_blocks_cli
tests/test_cardcade_diagnostic_launcher_safety.py::test_blocking_reconciliation_findings_produce_blocked_status
tests/test_cardcade_diagnostic_launcher_safety.py::test_missing_reconciliation_report_is_not_accepted
tests/test_cardcade_diagnostic_launcher_safety.py::test_nonterminal_normal_return_is_incomplete_and_not_accepted
tests/test_cardcade_diagnostic_launcher_safety.py::test_nonterminal_cli_result_exits_nonzero
tests/test_cardcade_diagnostic_launcher_safety.py::test_missing_presence_evidence_blocks_normal_return
tests/test_diagnostic_capture.py::test_nested_failure_uses_explicit_runner_binding_not_innermost_game_local
tests/test_diagnostic_capture.py::test_run_game_exception_capture_preserves_presence_and_authenticates_token
tests/test_diagnostic_capture.py::test_missing_or_ambiguous_runner_binding_fails_closed_without_hiding_error
tests/test_diagnostic_capture.py::test_capture_finalizes_a_copy_of_presence_without_mutating_live_ledger
tests/test_diagnostic_capture.py::test_reused_capture_does_not_attach_previous_game_to_unbound_failure
tests/test_diagnostic_capture.py::test_unprintable_snapshot_capture_error_does_not_mask_original_exception
tests/test_diagnostic_capture.py::test_non_game_success_after_failure_clears_stale_failure_and_binding
tests/test_diagnostic_capture.py::test_run_game_without_capture_preserves_setup_exception
tests/test_diagnostic_capture.py::test_presence_finalization_and_traceback_format_failures_keep_original_exception
tests/test_diagnostic_capture.py::test_failure_inside_capture_bookkeeping_cannot_replace_execution_exception
tests/test_strike_damage_steps.py::test_lethal_first_strike_damage_ends_without_advancing_terminal_combat
tests/test_strike_damage_steps.py::test_lethal_regular_damage_ends_without_terminal_transition_or_duplicate_damage
tests/test_strike_damage_steps.py::test_lethal_first_strike_sba_removes_blocker_before_regular_step
tests/test_strike_damage_steps.py::test_no_strike_combat_retains_one_regular_damage_step
tests/test_strike_damage_steps.py::test_combat_damage_steps_cannot_be_skipped_repeated_or_resolved_out_of_order
tests/test_strike_damage_steps.py::test_failed_transition_does_not_clear_or_fabricate_live_combat_state
tests/test_cardcade_diagnostic_auth_reconciliation.py::test_unsigned_authorization_documents_are_rejected
tests/test_cardcade_diagnostic_auth_reconciliation.py::test_valid_synthetic_signature_is_bound_to_both_documents
tests/test_cardcade_diagnostic_auth_reconciliation.py::test_altered_authorization_content_fails_signature_verification
tests/test_cardcade_diagnostic_auth_reconciliation.py::test_source_and_run_authorization_must_use_same_trusted_signer
tests/test_cardcade_diagnostic_auth_reconciliation.py::test_unknown_signer_and_unconfigured_trust_anchor_fail_closed
tests/test_cardcade_diagnostic_auth_reconciliation.py::test_duplicate_json_authorization_fields_are_rejected
tests/test_cardcade_diagnostic_auth_reconciliation.py::test_incomplete_stage002_reconciliation_cannot_return_ready
tests/test_cardcade_diagnostic_auth_reconciliation.py::test_actual_reconciliation_digest_and_manifest_binding_are_preserved
tests/test_cardcade_diagnostic_auth_reconciliation.py::test_incomplete_or_altered_stage002_report_is_blocked
```

Results:

- Launcher and authorization safety: 20 passed, 0 failed, 0 skipped. Parameterization accounts for the 20th case.
- Capture lifecycle and terminal combat: 16 passed, 0 failed, 0 skipped.
- Authorization and reconciliation closure: 13 passed, 0 failed, 0 skipped. Parameterization accounts for four additional cases.

Total: **49 passed, 0 failed, 0 skipped**. Test fixtures use synthetic setup and snapshots only.

## Authorization security findings

Ed25519 validation is correctly bound to canonical document contents, signer identity, exact source SHA, frozen-input hashes, and the run authorization fields. The tests reject unsigned, altered, duplicate-key, unknown-signer, cross-signer, mismatched, and unconfigured-trust-anchor documents. The production `TRUSTED_HQ_AUTHORIZATION_KEYS` registry imports as `{}` and fails closed. Test-only private keys are generated in memory by `tests/cardcade_auth_test_support.py`; no signing private key material was found in the launcher or repository search. Cross-process single-use claim coverage passed. Production trust-anchor provisioning remains a separate HQ step and is not part of this verdict.

## Reconciliation authenticity defect

The validator verifies the report digest, exact top-level fields, game identity, manifest binding, authoritative evidence projection, conformance references, invariant events, and collection types. However, it only type-checks `occurrences`, `presence`, `classification_sets`, `transaction_counts`, and `engine_boundary_counts`; it does not verify that those derived contents equal an authoritative reconciliation result.

Adversarial setup-only reproduction: the real `stage002.reconcile_snapshot` was called, then `transaction_counts` was replaced with `{"forged_execution": 1}` and `report_digest` recomputed with `stage002.stable_digest`. The launcher persisted that report with a valid digest, returned CLI exit code **0**, and wrote `diagnostic_status: READY` with no blocking findings. The synthetic executor constructed initial state and marked its snapshot terminal only to exercise acceptance; it did not enter gameplay. This shows a digest authenticates the serialized bytes, not the truth of derived report fields.

Required correction: derive the expected report from the authoritative captured snapshot and verified manifest using the pinned Stage 002 reconciler, then compare the complete canonical report (including all derived fields) before accepting or binding it. Preserve any supplied report and mismatch details as evidence, and return `BLOCKED` with nonzero exit on any divergence. The recomputation path must not simply trust an externally supplied report or only rehash it.

## Preservation checks

- All six frozen input hashes matched the candidate allowlist: Stage 002 source, April deck, Casey deck, frozen card-data JSON and manifest, and Baseline 005 manifest.
- All nine PR #406 artifacts matched the preserved `artifact_sha256.json` manifest.
- The three original reconciliation stops remain present and unchanged: `stop-000001` (`illegal_mutation`, turn 16 / `combat_damage`), `presence_evidence_missing`, and the preserved trample/combat event and object references.
- Accepted main, frozen inputs, PR #417 source, and PR #406 artifacts were not modified.

## Handoff

The source-approval signature design and one-use claim protections are suitable for continued review, subject to HQ provisioning a reviewed public trust anchor before any real authorization. Reconciliation must close the derived-field authenticity gap before launcher acceptance. No authorization for a game or real permit is recommended.
