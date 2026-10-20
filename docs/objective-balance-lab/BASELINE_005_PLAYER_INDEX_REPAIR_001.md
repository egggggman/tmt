# Baseline 005 `player_index` Contract Repair 001

Status: **READY for independent repair acceptance; BLOCKED for Calibration Attempt 8.**

## Root cause

The Attempt 7 failure was a simulator telemetry-contract defect. April's end-step spell-type draw resolver consumed every `spell_cast` event and required `record["player_index"]`. The generic hand-response casting path `_announce_hand_response` created a valid `spell_cast` event but omitted both `player_index` and `card_types`. The resulting `KeyError` occurred in `engine07.py:_resolve_triggered_ability`, before the spell-type draw could resolve.

This was not an illegal cast, target, payment, or gameplay state. The spell was a valid response spell; its event record was differently shaped from ordinary and Sneak casts. The consumer was correct to require controller identity, but the producer violated the shared record contract.

Traceback: `stage002.py:_drain_priority` → `engine07.py:process_priority_resolution` → `resolve_top_of_stack` → `_resolve_triggered_ability`, failing at `record["player_index"]`.

## Repair

The hand-response producer now emits the same generic `spell_cast` contract as every other casting path: integer `player_index` and `card_types`. A strict reusable validator rejects malformed records rather than inventing a default or skipping them.

## Validation

- Attempt 7 seed replayed twice after repair with matching digest `004167902e7a633dd802cf66aa0f0ac2fff2fbe9f8a408fd2e3e56bdfe3a34b1`.
- Eight historical failure seeds replayed twice: complete, deterministic, zero exceptions.
- Contract tests: 3 passed; focused historical suite: 60 passed.
- Donatello/April diagnostic: 100/100 games, balanced 50/50 starts, zero errors; excluded from balance interpretation.
- Diagnostic artifact SHA-256: `6ecd704af19dc3c19eb40817c80de17cfadc7f52d1be784bdd0b06578e7258aa`.
- New semantic runtime: `0b73c2283aaa28f013867d2b3c1e2b3aa287f326dfcddb22f81f05505370169a`.

No calibration control was launched. Attempt 7 remains immutable and fail-closed.
