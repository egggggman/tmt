# Baseline 005 — Damage-target repair control Attempt 6

## Decision

**BLOCKED.** The fresh control failed closed before completion because a generic
counter-activation provenance invariant raised during the 2,101st scheduled
game. No game was retried, no schedule entry was changed, and no historical
artifact was overwritten.

This artifact is incomplete calibration evidence only. It is not a balance
baseline and must not be combined with any previous control.

## Authenticated configuration

- Control ID: `OBL-BASELINE-005-DAMAGE-TARGET-CONTROL-ATTEMPT-006`
- Runtime: `ee8d37b192a6eb37526283a458e54fb243e17d5e4dad68bd60cd863bfcf1a194`
- Schedule: unchanged 45-cell / 4,500-game schedule; 50/50 starting-player assignments
- Deck environment: unchanged frozen Baseline 005; ten deck hashes authenticated
- Coverage ledger: unchanged 172-row Oracle ledger
- Artifact: `BASELINE_005_ISSUE289_DAMAGE_TARGET_CONTROL_ATTEMPT_006.json.gz`
- Artifact SHA-256: `6f950648b1edd20052bb30c0982faf9bb82a1a979fd69271d2b6a97b8eac169a`
- Artifact size: 1,848,963 bytes

The artifact passed gzip decompression, schema/manifest validation, hash
authentication, and durable read-back. Its status is explicitly `FAIL_CLOSED`.

## Execution result

- Completed games: 2,100 / 4,500
- Completed cells: 21 / 45
- Runtime errors in completed game records: 0
- Failure point: scheduled game 2,101
- Failed cell: `donatello|bebop_rocksteady`
- Orientation: canonical
- Block: 47
- Seats: Bebop & Rocksteady / Donatello
- Seed: `12506277166433065153407346632076121278501225696392466898823914761107207299783`
- Exception: `ValueError: counter activation provenance is invalid`
- Replays recorded before failure: 3; no replay mismatch was observed before the stop

The failure is a simulator/provenance defect, not evidence of deck balance.
The damage-target repair itself passed the focused preflight suite; this is a
new neighboring generic provenance failure exposed by the full control.

## Governance

The two historical artifacts classified `HISTORICAL_CORRUPT_EXCLUDED` remain
excluded only under the previously authorized exception. All prior failed
controls and repair diagnostics remain immutable and excluded. This Attempt 6
artifact is also excluded from balance interpretation pending a separate
root-cause repair and new HQ authorization.

**Recommendation:** BLOCKED pending investigation and repair of the generic
counter-activation provenance defect. No replacement control, deck revision,
merge, promotion, or Prototype 0.3 authorization is requested by this report.
