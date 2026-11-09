# PR #415 Independent Diagnostic Launcher Audit

## Verdict

**REWORK.** The eight candidate synthetic tests pass, and the accepted capture/terminal source chain and historical Diagnostic Game 001 artifacts remain intact. Three additional no-game challenges show the launcher is not yet safe for the exact-one authorized-run gate:

1. Preflight accepts a source commit that is merely a descendant of PR #413's base, rather than requiring the exact approved candidate SHA.
2. A successful execution whose reconciliation fails still returns normally; the CLI exits `0` while the status says reconciliation did not complete.
3. A second launcher instance can invoke again with a different output directory. The current one-call counter is instance-local, not a durable one-run reservation.

No gameplay was executed during this audit. PR #415 was not modified.

## Source provenance

- PR #415 published HEAD audited in its own detached worktree: `188da5fabc231c91b222c642b6c9cf6fe4377c9f`.
- Tested implementation: `688a53b707b03c56dbc01225d4078df6bf28dc2f`.
- Diff from tested implementation to published HEAD: documentation only, `docs/cardcade/DIAGNOSTIC_LAUNCHER_DRY_RUN.md`; there are no post-test launcher or test code edits.
- Audit branch adds only audit tests and this report. Its test-source commit before this report was `5692dd67e5d52bd688c894b7008c60093b21c340`.
- PR #413 base `6612ba7ee36d7eeeb2b090a3a7664662d6fcdeac`, PR #407 terminal commits `a33f0369a4c56be8ce85f3863f3b7e2fbac220ba` / `fcbe5fbf9419f246663a29467797ed79df57433f`, and PR #411 capture lifecycle implementation `b1c089476b47f032b63d169b7dedcb69d85afaee` are ancestors of the candidate.
- Accepted `origin/main`: `10d2ac80ef5b81b3a209a3133eb0a84633a1f944`.
- Independent imports resolved to `C:\projects\tmt\.audit-pr415-launcher-independent\src\tmnt_design_studio\stage002.py` and the matching worktree `engine07.py`; `stage002.Game is engine07.Game`.
- Python 3.12.10, pytest 8.4.2, Ruff 0.16.1.

The candidate's actual deck, card-data, Baseline 005 manifest, and Stage 002 hashes match the identities recorded in its dry-run report. The launcher records current hashes but does not compare them against approved expected hash constants. Exact source pinning is needed so a later committed input change cannot pass only because it descends from the accepted base.

## Candidate regression selection

At the exact published HEAD, the eight named tests passed: **8 passed, 0 failed, 0 skipped**.

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; & C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\python.exe -B -m pytest -q `
  tests\test_cardcade_diagnostic_launcher.py::test_synthetic_success_serializes_reconciliation_and_integrity_hashes `
  tests\test_cardcade_diagnostic_launcher.py::test_injected_failure_preserves_original_exception_and_bound_snapshot `
  tests\test_cardcade_diagnostic_launcher.py::test_failure_before_binding_is_persisted_without_fabricated_snapshot `
  tests\test_cardcade_diagnostic_launcher.py::test_launcher_instance_cannot_be_reused_for_second_invocation `
  tests\test_cardcade_diagnostic_launcher.py::test_existing_output_directory_is_rejected_before_executor_call `
  tests\test_cardcade_diagnostic_launcher.py::test_persistence_failure_after_synthetic_execution_is_never_retried `
  tests\test_cardcade_diagnostic_launcher.py::test_committed_match_configuration_is_exact `
  tests\test_cardcade_diagnostic_launcher.py::test_output_directory_cannot_escape_isolated_diagnostic_root
```

The successful fixture built an initial game state and presence ledger, then serialized it; it did not call `stage002.run_game` or enter the loop. Its state was nonterminal at setup, turn 0. Snapshot, events, trace, manifest, and reconciliation were persisted. The test recomputed SHA-256 for every artifact listed in `artifact_sha256.json`. Reconciliation completed with no stop records for this synthetic initial state. Exception cases retained the original exception identity, and the tested snapshot-write failure did not cause a second executor call.

Independent output directory:

`.cardcade-diagnostic-runs/diagnostic-game-test-pytest-18-test_synthetic_success_seriali0`

Independent artifact hashes:

| Artifact | SHA-256 |
| --- | --- |
| `events.json` | `ba66ea73fda4ea377387f3f3e7ee6e92e766a50ea5a9a6df26a7fae1bef53794` |
| `priority_stack_combat_trace.json` | `37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570` |
| `reconciliation.json` | `e0d9e585393841ebfdf585f86bc8df2a7716d35a4b4017baea704fcef583ffbc` |
| `run_metadata.json` | `5b3ce7152e51bfd9de01039b3bc07ca0826bc3fd2550718dd09ce76faaa50834` |
| `run_status.json` | `3eb0590ba28cbe155895c15d34a9af5a2d8fa1e86cc80d808b45d65f1597b0f7` |
| `snapshot.json` | `6ffb044515e4137ee037f3f3e7ee6e92e766a50ea5a9a6df26a7fae1bef53794` |
| `stage_manifest.json` | `e8fefc0bd0defb31478efcab4b51c5bb77da0d4839d730572a4fa1a19d5f5db6` |

## Adversarial synthetic challenges

Five supplemental tests passed as reproductions/assertions of observed behavior; three expose acceptance gaps:

| Test node | Result and finding |
| --- | --- |
| `test_audit_preflight_accepts_unapproved_pretest_descendant` | Passed as a defect reproduction. With Git reporting the real descendant `5cf4a0c6cd631ddeac9dbf8123a4197c25bac66f`, preflight accepts it because it checks ancestry from `6612ba7...`, not equality with `188da5f...` or `688a53b...`. |
| `test_audit_success_path_returns_normally_when_reconciliation_fails` | Passed as a defect reproduction. Injected reconciliation failure writes `reconciliation_error.json`, but `run_once()` returns a snapshot normally and status records `run_returned_normally: true`, `reconciliation_completed: false`. |
| `test_audit_cli_returns_success_code_when_reconciliation_fails` | Passed as a defect reproduction. With only `stage002.run_game` replaced by the synthetic fixture, the launcher CLI returns exit code `0` despite failed reconciliation. No game entrypoint ran. |
| `test_audit_new_launcher_instances_can_each_invoke_executor` | Passed as a defect reproduction. Two fresh instances and distinct output directories each invoke their executor once; the per-instance guard does not enforce a single authorized run across invocations. |
| `test_audit_original_exception_survives_failure_to_persist_exception_record` | Passed. An exception-record write failure preserves the original exception object and traceback path, attaches a storage-failure note, and does not retry. |

Command for the supplemental selection at audit source `5692dd67e5d52bd688c894b7008c60093b21c340`:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; & C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\python.exe -B -m pytest -q `
  tests\test_pr415_independent_launcher_audit.py::test_audit_preflight_accepts_unapproved_pretest_descendant `
  tests\test_pr415_independent_launcher_audit.py::test_audit_success_path_returns_normally_when_reconciliation_fails `
  tests\test_pr415_independent_launcher_audit.py::test_audit_cli_returns_success_code_when_reconciliation_fails `
  tests\test_pr415_independent_launcher_audit.py::test_audit_new_launcher_instances_can_each_invoke_executor `
  tests\test_pr415_independent_launcher_audit.py::test_audit_original_exception_survives_failure_to_persist_exception_record
```

Result: **5 passed, 0 failed, 0 skipped**. All supplemental executors construct only synthetic initial state. No selected test enters the gameplay loop.

## Historical evidence preservation

The nine files in the preserved Diagnostic Game 001 evidence directory were rehashed against its own `artifact_sha256.json`; all nine matched. The preserved reconciliation still contains the same three stops, in order: `illegal_mutation` at turn 16 / combat damage, `silent_approximation` for `presence_evidence_missing`, and the original disputed execution-reference stop. No historical record was edited or reclassified.

## Quality checks and requested corrections

- Ruff format check: passed on the launcher and both test files.
- Ruff lint: passed on the launcher and both test files.
- `git diff --check`: passed.
- No PR #415 implementation files were modified by this audit.

Before authorizing a game, the launcher should:

1. Require an exact, explicit approved source SHA (and validate the frozen deck/card-data/Baseline identities against the approved manifest) rather than accepting any descendant of PR #413.
2. Treat reconciliation failure as a failed diagnostic command while preserving all collected evidence; the CLI must not exit zero for unauthenticated results.
3. Bind invocation to a durable one-use authorization/reservation so a new launcher process cannot start another game under the same one-game authorization. Keep automatic retry disabled.

**Independent verdict: REWORK.** The launcher is not ready for Diagnostic Game 002 authorization. PR #415 remains unchanged and unmerged; no complete game, Smoke restart, calibration, merge, deck edit, or baseline promotion was performed.
