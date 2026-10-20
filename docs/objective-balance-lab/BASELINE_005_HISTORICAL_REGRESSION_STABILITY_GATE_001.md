# Baseline 005 Historical Regression and Stability Gate 001

Status: **READY for stability-checkpoint acceptance; BLOCKED for Calibration Attempt 7.**

Semantic runtime: `4978cdaa3c78d4e1f90498444d92850736c325df59c772e4bfaf8cc27ab27933`

## Historical failure registry

The permanent registry is `BASELINE_005_HISTORICAL_FAILURE_REGISTRY_001.json` (SHA-256 `01f0ab52b26b9479941826ed9adc08a9a6e12b8a4f59136daa51b4276c3d159c`). It records seven independently reproducible failures: two pilot P/T, two Food-search, two damage-target, and one counter-activation case. All seven replayed twice under the current runtime, completed without exceptions, and produced identical event digests. The original failed-control artifacts remain unchanged; the registry distinguishes reproducible failure records from raw artifacts classified as unrecoverable or excluded.

The published focused-test count of 25 is historical. The final focused run is 26 passed: the additional test is the negative token-provenance regression, which confirms malformed evidence is rejected. This count difference does not represent a failure.

## Deterministic replay gate

All seven registered seeds completed deterministically. Focused negative fixtures reject forged or malformed provenance and invalid actions. Full regression passed with 2,118 tests and 10 skips; Ruff, formatting, structural checks, and terminology validation passed.

## Bounded diagnostic stress batch

`OBL-BASELINE-005-STABILITY-STRESS-DIAGNOSTIC-001` used a separate 80-game schedule: the first 20 games from each of four interaction-heavy cells (Raphael/Donatello, Raphael/Michelangelo, Raphael/Krang, and Donatello/Bebop & Rocksteady), with 40 canonical and 40 reversed starts. All 80 games completed, with zero errors and zero draws. The artifact SHA-256 is `8178a591f3febf38cb084fa2fd852b46bdb39368b5ac0c01686751b92d38b7ea`; schedule SHA-256 is `2cd41ed03d447bb534ac2a16532636c6eba345e1180697c16f62a45ea64ffa8b`. Gzip integrity, schema, manifest, and durable read-back validation passed.

This batch is a simulator-stability diagnostic, not balance evidence, and does not alter the established calibration schedule.

## Preservation and gate

The ten frozen Baseline 005 deck identities and the original 172-row ledger remain unchanged. Attempt 6 and earlier fail-closed artifacts remain immutable and excluded from calibration evidence. No calibration run was launched, and no deck, historical result, or baseline was changed.

Recommendation: accept this stability checkpoint; keep Calibration Attempt 7 blocked pending HQ authorization.
