# PR #421 Independent Acceptance Audit

## Verdict: ACCEPT

PR #421 prevents the PR #420 complete-report forgery from being accepted. The trusted report is calculated from the authoritative snapshot, verified manifest, and fixed game specification through a captured source-pinned reconciler reference. The entire canonical report is compared with the supplied report. The historical attack and additional seam, input-mutation, and trusted-reference-failure challenges behaved as required.

## Source and environment

- Published candidate HEAD tested: `92a29a3263d8555029904e8d4c9f097f38c50605`.
- Tested implementation parent: `d0dcf247a7ef0fc78e3e34f6841433dfb7903b6a`.
- PR #419 base/source: `98e7a3a3e7247bb685d82f7200c791365d592365`.
- Fresh reviewer worktree: `.audit-pr421-independent-acceptance`, clean at the published candidate HEAD before audit.
- Imported launcher: this worktree's `tools/cardcade_diagnostic_launcher.py`.
- Imported Stage 002: this worktree's `src/tmnt_design_studio/stage002.py`.
- Runtime: Python 3.12.10, pytest 8.4.2, cryptography 46.0.7.
- No gameplay, complete game, production key, real permit, or Smoke run was used.

## Historical RED / corrected GREEN

Against exact PR #419 source `98e7a3a3e7247bb685d82f7200c791365d592365`, a setup-only synthetic launcher invocation changed `transaction_counts` to `{"forged_execution": 1}` and recomputed `report_digest` using Stage 002's valid digest function. The PR #419 launcher returned exit code 0, `READY`, and no blockers while preserving the falsified count.

The same attack against PR #421 returned exit code 2 and `BLOCKED` with `reconciliation_failed`. It preserved `snapshot.json`, the supplied forged `reconciliation.json`, `reconciliation_expected.json` from the trusted calculation, and `reconciliation_error.json`. The authorization remained consumed; `run_game_call_count` was 1 and `retry_count` was 0. The synthetic fixture constructed initial state and snapshot only; it did not enter gameplay.

The preserved RED test is `tests/test_cardcade_diagnostic_auth_reconciliation.py::test_fabricated_complete_report_with_recomputed_digest_cannot_return_ready`. It passes on PR #421.

## Independent 55-case regression selection

All cases passed on the exact published candidate HEAD:

- Launcher and authorization safety: **20 passed, 0 failed, 0 skipped**.
- Capture lifecycle and terminal combat: **16 passed, 0 failed, 0 skipped**.
- Authorization and reconciliation closure: **13 passed, 0 failed, 0 skipped**.
- Forgery-specific regressions: **6 passed, 0 failed, 0 skipped**.
- Total: **55 passed, 0 failed, 0 skipped**.

The prior 49 named nodes were run in the same groups recorded in `DIAGNOSTIC_LAUNCHER_SAFETY_CORRECTION.md` and `DIAGNOSTIC_AUTHENTICATION_RECONCILIATION_CLOSURE.md`. Commands used the existing environment, with each node passed explicitly:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; & 'C:\projects\tmt\.cardcade-diagnostic-auth-reconciliation-correction\.venv\Scripts\python.exe' -B -m pytest -q <explicit named nodes from those two reports>
```

The six forgery-specific cases were:

- `tests/test_cardcade_diagnostic_auth_reconciliation.py::test_fabricated_complete_report_with_recomputed_digest_cannot_return_ready`
- `tests/test_cardcade_diagnostic_auth_reconciliation.py::test_rehashed_derived_report_fields_are_blocked_and_preserved[transaction_counts-forged_value0]`
- `tests/test_cardcade_diagnostic_auth_reconciliation.py::test_rehashed_derived_report_fields_are_blocked_and_preserved[engine_boundary_counts-forged_value1]`
- `tests/test_cardcade_diagnostic_auth_reconciliation.py::test_rehashed_derived_report_fields_are_blocked_and_preserved[classification_sets-forged_value2]`
- `tests/test_cardcade_diagnostic_auth_reconciliation.py::test_rehashed_derived_report_fields_are_blocked_and_preserved[presence-forged_value3]`
- `tests/test_cardcade_diagnostic_auth_reconciliation.py::test_rehashed_derived_report_fields_are_blocked_and_preserved[authenticated_executed_references-forged_value4]`

The 20 launcher/authentication cases retain Ed25519, exact source and frozen-input binding, and cross-process one-use claim coverage. The 16 capture/terminal cases retain exception/presence capture and terminal-combat behavior.

## Reference-integrity challenges

1. **Replaced report function:** The tested forgery replaces `stage002.reconcile_snapshot` with a wrapper that modifies the result and recomputes a valid digest. The launcher still uses its previously captured `_TRUSTED_RECONCILE_SNAPSHOT` reference for the expected result. All five derived-field cases were blocked.
2. **Mutated input objects:** A synthetic reporting wrapper appended an event to its supplied snapshot copy and removed games from its supplied manifest copy before reconciliation. The launcher blocked the disagreement; persisted authoritative `snapshot.json` and the trusted report remained free of those mutations. The supplied report and mismatch evidence were preserved; one invocation and zero retries were recorded.
3. **Trusted-reference failure:** Replacing the captured trusted callable with one that raises produced exit code 2 and `BLOCKED`, with `reconciliation_failed` and `reconciliation_missing`. The snapshot and reconciliation error were preserved; one invocation and zero retries were recorded.
4. **Complete-report comparison:** Validly rehashed changes to transaction counts, engine-boundary counts, classification sets, presence, and authenticated execution references all failed canonical whole-report agreement. The supplied and trusted reports remained available for review.

The reference calculation is not derived from the supplied report object or a later lookup of the replaceable Stage 002 reporting attribute. Both calculations receive independent deep copies of the authoritative snapshot and verified manifest. The exact Stage 002 source hash and approved implementation source are checked by the existing launcher authorization path.

## Historical preservation and limitations

- All six frozen-input hashes matched the candidate allowlist: Stage 002, April and Casey decks, card-data JSON and manifest, and Baseline 005 manifest.
- All nine PR #406 artifacts matched their preserved `artifact_sha256.json` values.
- All three original stops remain unchanged: `stop-000001` (`illegal_mutation`, turn 16 / `combat_damage`), `presence_evidence_missing`, and the preserved trample/combat event and object references.
- The production Ed25519 public-key registry remains empty. No real permit can be accepted until HQ provisions a reviewed trust anchor and issues approvals for the exact authorized implementation SHA.
- This audit establishes synthetic evidence and reconciliation authenticity only; it does not establish gameplay readiness or authorize Diagnostic Game 002.

## Handoff

PR #421 is **ACCEPTED** for the bounded reconciliation-authenticity correction. The candidate remains draft and unmerged. No production trust anchor, real authorization, gameplay, or integration permission is included in this verdict.
