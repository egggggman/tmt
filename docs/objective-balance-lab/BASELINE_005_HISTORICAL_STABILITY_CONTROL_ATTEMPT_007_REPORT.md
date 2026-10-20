# Baseline 005 Historical Stability Control — Attempt 7

Status: **BLOCKED — fail-closed runtime defect**

Control identity: `OBL-BASELINE-005-HISTORICAL-STABILITY-CONTROL-ATTEMPT-007`

Runtime: `4978cdaa3c78d4e1f90498444d92850736c325df59c772e4bfaf8cc27ab27933`

## Preflight

Preflight passed. The ten frozen Baseline 005 deck identities, 172-row Oracle ledger, 45-cell/4,500-game schedule, balanced orientations, seven historical seed replays, negative legality/provenance tests, historical exception, artifact safeguards, and prior-control exclusions were authenticated. Focused regression tests passed (57 selected tests), and the runner passed Ruff and format checks.

## Control result

The single authorized control began with the unchanged schedule and stopped fail-closed after **2,200 completed games**. No games were retried and no schedule or deck input was changed. The finalized artifact is:

`BASELINE_005_HISTORICAL_STABILITY_CONTROL_ATTEMPT_007.json.gz`

SHA-256: `5e3ade2c11f9b2be9444dd6680072f15e10930e4cf359b7426f5d1b81f986590`

It passed gzip, schema, manifest, hash, and durable read-back validation as a `FAIL_CLOSED` artifact. It contains 22 completed cells, 3 replay digests, and the exact failure record.

## Exact failure

- Pair: `donatello|april_oneil`
- Orientation: canonical
- Block: 45
- Seed: `90856440471641210079667413299657723063525178810879778610267403494681052196929`
- Seats: April O'Neil, then Donatello
- Exception: `KeyError: 'player_index'`

The failure occurred before a game result, with no winner, turn, runtime fingerprint, or event summary recorded for that game. Because the runner failed closed on a material runtime exception, the 2,200 completed games are not balance evidence and are not combined with any earlier control.

## Gate decision

This is a simulator/pilot reliability failure, not a deck-balance result. Attempt 7 is **BLOCKED**. No replacement control, deck revision, merge, promotion, or Prototype 0.3 authorization is made here. The exact failed artifact is preserved for root-cause investigation.
