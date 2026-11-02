# Cardcade CI Recovery — Exact-Commit Readiness Report

**Status: BLOCKED — formatting is repaired, but lint and safe CI gates remain unresolved.**

## Provenance

- PR #374 remains draft; reviewed starting head: `03aa78cfa0f761a263a5030170679456a3beedf8`.
- Isolated writable checkout: `.ci-review-pr374-depth1-20261102`.
- Correction commit: `5623c72eb07643004dd97f75f437b55b99037fde`.
- Branch: `fix/cardcade-300-wrapper-integrity`.
- No merge, signing, grants, wrapper execution, or gameplay occurred.

## Changes

1. Added format-only Ruff exclusions for the three preserved, byte-pinned review artifacts that caused CI run `41482761209` to fail:
   - `.diag003-memory-independent-review/verifier-trust-review/corrected/verify_completed_batch.py`
   - `.diag003-memory-independent-review/verifier-trust-review/test_corrected_verifier_integrity.py`
   - `.diag003-memory-independent-review/verifier-trust-review/test_verify_completed_batch_trust.py`

   The files were not reformatted or edited. The correction uses `[tool.ruff.format].exclude`; Ruff lint still analyzes them.

2. Added narrow `.gitattributes` `-text` rules for the identity-pinned verifier/dependency source copies and integrity helper. In the new Windows clone, global `core.autocrlf=true` initially converted these copies to CRLF and caused their raw SHA-256 guards to reject the checkout. The committed blobs were restored byte-for-byte; dependency identity tests then passed. No historical source blobs were changed.

3. Removed an unused import and imported `Mapping` from `collections.abc` in the synthetic chain test. Test predicates were unchanged.

## Validation

- Ruff format check: **pass**, 687 files checked; the three preserved paths are narrowly excluded.
- Ruff lint on the new synthetic chain candidate and its test: **pass**.
- Synthetic receipt chain: **10 passed**.
- Corrected verifier trust regressions: **14 passed, 1 skipped**. Windows denied symlink creation (`WinError 1314`); junction escape validation passed.
- Historical verifier characterization: **9 passed**. These tests intentionally document acceptance of the original known attack cases; they are not security passes for the old verifier.
- Safe test total: **34 run, 33 passed, 1 skipped**.
- Full Ruff lint: **13 findings remain** across preserved verifier candidate/source copies and their tests. They include `B905` on `zip()` without `strict=`, import ordering, line-length, and an unused local. No lint exclusions were added; in particular, `B905` was not suppressed.
- Pytest: not run. The qualified isolated Python has no pytest package; `.venv\Scripts\pytest.exe` is an unusable uv trampoline. The repository workflow's full pytest step can call `run_smoke_game`, which is outside this authorization.
- Repository-wide GitHub Actions was not triggered. Thus there is no exact-head CI success claim.

## Recommendation

**BLOCKED.** The formatter failure is resolved in the correction commit, but the full Ruff lint step still fails with 13 findings. The full pytest workflow cannot be run safely because it may execute gameplay. The complete integrated trust chain also still lacks production supervisor attestation, stable Windows evidence capture, atomic receipt publication, and approved production trust anchors; this synthetic work does not establish those safeguards or independent acceptance.

**Smallest next move:** address the 13 lint findings in a new review identity while preserving the original artifacts, add a synthetic-only CI test selection that cannot invoke full-game tests, then request independent review. Keep PR #374 in draft and gameplay at 0/300.
