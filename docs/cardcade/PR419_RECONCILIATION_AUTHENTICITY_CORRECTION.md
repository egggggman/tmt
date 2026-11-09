# PR #419 Reconciliation Authenticity Correction

## Source identity

- Authorized starting source: PR #419 `98e7a3a3e7247bb685d82f7200c791365d592365`.
- Isolated branch/worktree: `fix/cardcade-reconciliation-authenticity` / `.cardcade-reconciliation-authenticity`.
- Preserved RED reproduction commit: `cda79924df0023c8917fe267be8677b04f6c0071`.
- Tested implementation commit: `d0dcf247a7ef0fc78e3e34f6841433dfb7903b6a`.
- Runtime: Python 3.12.10, pytest 8.4.2, cryptography 46.0.7, Ruff 0.16.1.
- Tests imported `tools.cardcade_diagnostic_launcher` and `tmnt_design_studio.stage002` from this exact worktree. No complete game, gameplay loop, real permit, or production signing key was used.

## Preserved RED / corrected GREEN

The PR #420 reproduction was added and committed before implementation. On the unchanged PR #419 code, the synthetic setup-only test

`tests/test_cardcade_diagnostic_auth_reconciliation.py::test_fabricated_complete_report_with_recomputed_digest_cannot_return_ready`

failed as expected: the falsified `transaction_counts` report returned CLI exit code 0, so the test's required exit code 2 assertion failed. The fixture creates initial game state and a snapshot, marking the snapshot terminal only to reach the acceptance check; it never enters gameplay.

The same test passes on `d0dcf247a7ef0fc78e3e34f6841433dfb7903b6a`. The supplied falsified report remains in `reconciliation.json`; the trusted report is preserved separately in `reconciliation_expected.json`; status is `BLOCKED`; CLI exit is 2; the durable authorization is consumed; and the invocation count remains one with zero retries.

## Trusted reference contract

The launcher resolves the repository `src` directory before importing Stage 002. At module initialization it captures the source-pinned `stage002.reconcile_snapshot` function object as `_TRUSTED_RECONCILE_SNAPSHOT`. The diagnostic source authorization still checks the exact approved implementation SHA and frozen inputs, including the Stage 002 source hash.

For a captured snapshot, verified Stage 002 manifest, and fixed `GameSpec`, the launcher invokes the captured trusted function and the ordinary report seam separately, passing independent deep copies of the inputs to each calculation. It compares canonical JSON for the complete reports, not only the digest or selected fields. This covers every derived field and distinguishes JSON types. A changed, omitted, added, or fabricated report field therefore becomes a reconciliation blocker even if its `report_digest` is recomputed correctly.

Both calculations are retained as evidence. A successful binding records the report digest and trusted-reference digest; a mismatch preserves the supplied report, trusted expected report, snapshot, reconciliation error, and final blocked status. The pinned calculation does not consume or reuse the supplied report object and is not obtained by looking up the replaceable `stage002.reconcile_snapshot` module attribute after initialization.

## Synthetic regression results

The prior 49-case selection was rerun unchanged:

- Launcher and authorization safety: **20 passed**.
- Capture lifecycle and terminal combat: **16 passed**.
- Authorization and reconciliation closure: **13 passed**.
- Total: **49 passed, 0 failed, 0 skipped**.

The prior named nodes are recorded in `DIAGNOSTIC_LAUNCHER_SAFETY_CORRECTION.md` and `DIAGNOSTIC_AUTHENTICATION_RECONCILIATION_CLOSURE.md`. The first batch ran the eight launcher nodes and eleven launcher-safety nodes listed in the former report; the second ran its ten capture-lifecycle nodes and six listed terminal-combat nodes; the third ran the nine authentication/reconciliation nodes listed in the latter report. Each used the existing environment and this command form:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; & 'C:\projects\tmt\.cardcade-diagnostic-auth-reconciliation-correction\.venv\Scripts\python.exe' -B -m pytest -q <individually named nodes from the cited prior selections>
```

Six focused cases passed (**6 passed, 0 failed, 0 skipped**):

- `tests/test_cardcade_diagnostic_auth_reconciliation.py::test_fabricated_complete_report_with_recomputed_digest_cannot_return_ready`
- `tests/test_cardcade_diagnostic_auth_reconciliation.py::test_rehashed_derived_report_fields_are_blocked_and_preserved[transaction_counts-forged_value0]`
- `tests/test_cardcade_diagnostic_auth_reconciliation.py::test_rehashed_derived_report_fields_are_blocked_and_preserved[engine_boundary_counts-forged_value1]`
- `tests/test_cardcade_diagnostic_auth_reconciliation.py::test_rehashed_derived_report_fields_are_blocked_and_preserved[classification_sets-forged_value2]`
- `tests/test_cardcade_diagnostic_auth_reconciliation.py::test_rehashed_derived_report_fields_are_blocked_and_preserved[presence-forged_value3]`
- `tests/test_cardcade_diagnostic_auth_reconciliation.py::test_rehashed_derived_report_fields_are_blocked_and_preserved[authenticated_executed_references-forged_value4]`

Each focused adversarial case recomputes a valid report digest after changing the named field, then verifies nonzero exit, `BLOCKED`, preserved supplied and trusted reports, one execution, and no retry. The combined evidence is **55 passed, 0 failed, 0 skipped** across the prior and focused selections.

Quality checks on the tested implementation:

- `ruff format --check tools/cardcade_diagnostic_launcher.py tests/test_cardcade_diagnostic_auth_reconciliation.py`: passed.
- `ruff check tools/cardcade_diagnostic_launcher.py tests/test_cardcade_diagnostic_auth_reconciliation.py`: passed.
- `git diff --check 98e7a3a3e7247bb685d82f7200c791365d592365..d0dcf247a7ef0fc78e3e34f6841433dfb7903b6a`: passed.

## Preservation

- All six frozen input hashes match the existing allowlist: Stage 002 source, April and Casey decks, card-data JSON and manifest, and Baseline 005 manifest.
- All nine PR #406 artifacts match the preserved `artifact_sha256.json` values.
- The three historical PR #406 reconciliation stops remain unchanged: `stop-000001` (`illegal_mutation`, turn 16 / `combat_damage`), `presence_evidence_missing`, and the trample/combat event and object references.
- No decks, accepted main, Baseline 005, PR #406 evidence, or prior implementation branch were modified.

## Handoff

The candidate closes the recomputed-digest forgery demonstrated by PR #420 while retaining Ed25519 checks, source pinning, persistent one-use claims, exception capture, and terminal-combat behavior. Independent review should verify the reference function binding, the complete-report comparison, the five adversarial report mutations, and the exact tested source identity. The production trust-anchor registry remains empty; this candidate does not provision keys or authorize gameplay.
