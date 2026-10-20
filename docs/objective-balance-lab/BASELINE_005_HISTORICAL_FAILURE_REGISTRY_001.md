# Baseline 005 historical failure-seed registry

The registry in `BASELINE_005_HISTORICAL_FAILURE_REGISTRY_001.json` records all
seven preserved failure seeds that have independently reproducible records:

| Family | Original control | Seeds | Current result |
| --- | --- | ---: | --- |
| Pilot P/T projection | Repaired Control 001 | 2 | Complete, deterministic |
| ETB Food-search reconstruction | Repaired Pilot Control 001 | 2 | Complete, deterministic |
| Damage target legality | Food-search Control Attempt 005 | 2 | Complete, deterministic |
| Counter activation provenance | Damage-target Control Attempt 006 | 1 | Complete, deterministic |

All seven seeds completed twice under runtime
`4978cdaa3c78d4e1f90498444d92850736c325df59c772e4bfaf8cc27ab27933`, with no
exceptions and matching event/snapshot digests. The associated negative tests
remain green, including forged activation, stale target, missing token-cease
event, and invalid timing cases.

The registry preserves the distinction between reproducible failure records
and raw historical artifacts. The two unrecoverable failed-control gzip files
remain byte-for-byte unchanged and classified `HISTORICAL_CORRUPT_EXCLUDED`;
the registry does not authenticate or replace them.
