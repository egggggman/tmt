# Baseline 005 — LTB Mutagen Departure Provenance Repair

The three Michelangelo/Splinter failures from Control Attempt 8 were reproduced under runtime `0b73c2283aaa28f013867d2b3c1e2b3aa287f326dfcddb22f81f05505370169a`.

## Root cause

Each failure involved `Zoo Escapees` leaving the battlefield as a lethal-damage state-based action. The transition, source incarnation, controller, last-known battlefield data, attachment-independent card identity, and destination object were valid. However, `move_object` captured `events[-2]` as the departure record after a `creature_died` rules event had already been appended. The saved record was therefore the death rules event, not the preceding `zone_changed` record. The strict validator correctly rejected that mismatch as stale or relinked provenance.

## Repair

The generic engine now captures `zone_changed` and `permanent_departed` records by their event names and source object identity. It retains strict rejection of forged, stale, relinked, or incorrectly attributed evidence.

All three exact seeds now complete twice deterministically and produce the LTB Mutagen token. A forged leave-event fixture still fails closed.

## Validation

- Focused LTB tests: 4 passed.
- Full regression: 2,121 passed, 10 skipped.
- Historical registry expanded from 8 to 11 entries; all 11 replay twice with no exceptions.
- Michelangelo/Splinter diagnostic: 100/100 games, 50/50 starts, 0 errors; excluded from balance interpretation.
- New runtime: `defefdce8a716ceef6dcedad1a6f50e2abc367bd3cb772a369853506d2f5398d`.
- Attempt 8 artifact remains immutable and excluded as failed calibration evidence.

## Gate decision

**Checkpoint READY for independent repair acceptance. Baseline calibration remains BLOCKED pending separate HQ authorization.** Attempt 9 was not launched.
