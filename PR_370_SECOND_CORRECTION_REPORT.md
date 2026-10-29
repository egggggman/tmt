# PR #370 Second Correction Report

**Recommendation: READY FOR INDEPENDENT RE-AUDIT.** The validated correction is pushed to draft PR #370 on the existing `review/fresh900-live-adapter` branch, preserving its stack on PR #369.

## Identity and scope

- First-correction head: `110e44577df09ff595d44930a9514113e53574d4`.
- Current pushed head: `059ee7362ca4df9f96a3b8393a6bd35361b889c2`.
- Original audited head: `8e0cf697cd3bd28679665d00dad08d6ab5533d11`.
- Frozen gameplay, decks, schedule, memory threshold, and Durable 001 data were not changed.
- No gameplay or production checkpoint operation was run.

## Corrections

The callable binding now checks the default tuple shape and verifies its value with `is None`, so an object with an overloaded equality method cannot satisfy the frozen executor contract.

Native validation now derives phase from the frozen engine's `phase_for_step` mapping for snapshot and event records, rejects unknown or inconsistent phase/step values, and requires the nested combat damage evidence fields emitted by the frozen snapshot schema.

The full-plan probes initially stopped at `authenticate_source` because Windows CRLF checkout bytes differed from the committed Git blob. A writable-metadata clone with `core.autocrlf=false` was used, and the adapter plus frozen input inventory were restored byte-for-byte from their exact Git blobs. With the required startup flags and `PYTHONHASHSEED=0`, the probes reached the mock executor. No authentication check or frozen identity was changed.

The three artificial fixtures that paired `precombat_main` with `main` were updated to the frozen engine's canonical `precombat_main` phase. Predicate assertion ASTs were compared against the preserved probe source: all six test functions (nine parametrized cases) retain identical assertions.

## Changed files

- `src/tmnt_design_studio/fresh900_native.py`
- `tests/fresh900_native_fixtures.py`
- `tests/test_fresh900_live.py`
- `tests/test_pr370_second_correction_boundaries.py`
- `PR_370_SECOND_CORRECTION_REPORT.md`

## Validation

- Nine independent adversarial probes: **9 passed**.
- Focused boundary and fixture checks: **12 passed**.
- Windows C: correction suite: **255 passed, 1 skipped**.
- Windows G: correction suite: **255 passed, 1 skipped**, exit code **0**; durable log at `.pr370-g-suite.log` and exit code at `.pr370-g-suite.exitcode`. A pytest cache warning reflected an unwritable cache path; test results were unaffected.
- Ruff lint: **passed** across the repository.
- Ruff formatting check: **passed**, 734 files already formatted.
- Git whitespace check: **passed** for the correction diff.
- Exact-head Linux CI for `059ee7362ca4df9f96a3b8393a6bd35361b889c2`: workflow run **40939236447**, **success**. It reported **235 passed, 21 skipped** in 78.32 seconds on Python 3.13.15; the separate full-repository regression step was skipped by the workflow for this restricted Fresh 900 review.

The previously inaccessible G: directory was owned by `CARDCADE\cowabunga`; its nested pytest temp ACL granted access only to owner rights, SYSTEM, and Administrators. No Python/pytest process was active, and the directory was preserved without cleanup. The successful rerun used a new uniquely named G: directory with an explicitly selected basetemp.

No unresolved implementation or validation blockers remain. No real calibration launch authority is requested.
