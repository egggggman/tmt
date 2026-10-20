# Baseline 005 historical failure-seed registry

The registry in `BASELINE_005_HISTORICAL_FAILURE_REGISTRY_001.json` records all
eight preserved failure seeds that have independently reproducible records:

| Family | Original control | Seeds | Current result |
| --- | --- | ---: | --- |
| Pilot P/T projection | Repaired Control 001 | 2 | Complete, deterministic |
| ETB Food-search reconstruction | Repaired Pilot Control 001 | 2 | Complete, deterministic |
| Damage target legality | Food-search Control Attempt 005 | 2 | Complete, deterministic |
| Counter activation provenance | Damage-target Control Attempt 006 | 1 | Complete, deterministic |
| Spell-cast record contract | Historical Stability Control Attempt 007 | 1 | Complete, deterministic after repair |

All eight seeds completed twice under repaired runtime
`0b73c2283aaa28f013867d2b3c1e2b3aa287f326dfcddb22f81f05505370169a`, with no
exceptions and matching event/snapshot digests. The associated negative tests
remain green, including forged activation, stale target, missing token-cease
event, and invalid timing cases.

The registry preserves the distinction between reproducible failure records
and raw historical artifacts. The two unrecoverable failed-control gzip files
remain byte-for-byte unchanged and classified `HISTORICAL_CORRUPT_EXCLUDED`;
the registry does not authenticate or replace them.
