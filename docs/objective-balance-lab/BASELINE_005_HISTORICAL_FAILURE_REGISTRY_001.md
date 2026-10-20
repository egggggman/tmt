# Baseline 005 historical failure-seed registry

The registry in `BASELINE_005_HISTORICAL_FAILURE_REGISTRY_001.json` records all
eleven preserved failure seeds that have independently reproducible records:

| Family | Original control | Seeds | Current result |
| --- | --- | ---: | --- |
| Pilot P/T projection | Repaired Control 001 | 2 | Complete, deterministic |
| ETB Food-search reconstruction | Repaired Pilot Control 001 | 2 | Complete, deterministic |
| Damage target legality | Food-search Control Attempt 005 | 2 | Complete, deterministic |
| Counter activation provenance | Damage-target Control Attempt 006 | 1 | Complete, deterministic |
| Spell-cast record contract | Historical Stability Control Attempt 007 | 1 | Complete, deterministic after repair |
| LTB Mutagen departure provenance | Telemetry Control Attempt 008 | 3 | Complete, deterministic after repair |

All eleven seeds completed twice under repaired runtime
`defefdce8a716ceef6dcedad1a6f50e2abc367bd3cb772a369853506d2f5398d`, with no
exceptions and matching event/snapshot digests. The associated negative tests
remain green, including forged activation, stale target, missing token-cease
event, and invalid timing cases.

The registry preserves the distinction between reproducible failure records
and raw historical artifacts. The two unrecoverable failed-control gzip files
remain byte-for-byte unchanged and classified `HISTORICAL_CORRUPT_EXCLUDED`;
the registry does not authenticate or replace them.
