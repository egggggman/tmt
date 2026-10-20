# Baseline 005 — Telemetry Control Attempt 8

Control `OBL-BASELINE-005-TELEMETRY-CONTROL-ATTEMPT-008` was authorized under semantic runtime `0b73c2283aaa28f013867d2b3c1e2b3aa287f326dfcddb22f81f05505370169a`.

## Result

The control failed closed after **2,400/4,500 games** and 24/45 cells. No game was retried, no schedule entry was changed, and the partial artifact was finalized and read back successfully. The partial run is **not balance evidence**.

The first failing cell was Michelangelo / Splinter. Three games failed with the same generic simulator exception:

`ValueError: LTB Mutagen departure provenance is stale or relinked`

The exact first seed was `52602875548163369144134008259635487845293317286481406726252498296187974632476`. The traceback reaches combat-damage state-based actions, permanent movement to the graveyard, trigger enqueue, and `_validate_ltb_mutagen_departure` in `engine07.py`. This is a simulator provenance defect, not a balance result.

## Evidence

- Artifact: `BASELINE_005_TELEMETRY_CONTROL_ATTEMPT_008.json.gz`
- Artifact SHA-256: `3ac2dacfea88bddb0152ec90b394ac52157522f4149d7cf44c92cadef7b584e7`
- Schedule SHA-256: `b5fd8ab57016b15662fca420d508c9aab3633ad14b7f7515d667492b0f8abf27`
- Eight historical failure seeds replayed deterministically during preflight.
- Focused repair/negative tests: 65 passed.
- Full regression: 2,121 passed, 10 skipped.
- Ruff format/check and structural checks passed.
- Ten frozen deck hashes and the 172-row ledger remained unchanged.
- The two narrowly excluded historical corrupt artifacts remain preserved and excluded.

## Gate decision

**BLOCKED by a newly exposed generic LTB Mutagen departure-provenance defect.** No Attempt 8 balance interpretation, additional control, deck revision, merge, promotion, or Prototype 0.3 authorization is made. The next authorized step must separately reproduce and repair this provenance failure before another calibration request.
