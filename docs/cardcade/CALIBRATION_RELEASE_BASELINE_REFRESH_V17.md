# Calibration Release Baseline Refresh V17

This is a non-authorizing runtime-identity checkpoint for merged main `60acd013b28dc9d8cb46c5c5520c11e9e3943627` after PR #181. It does not create a reservation, generate a launcher, consume seeds, or authorize Calibration Protocol V1 execution.

The existing release-baseline identity format is preserved: `main_commit` and `accepted_runtime` both bind to the exact merged commit. The prior accepted runtime was `d0b6b728c3cf0d6d883bb80a398c4b3d99a1259e`.

PR #181 changed only execution/diagnostic infrastructure: bounded diagnostic heartbeat replacement retry, reduced heartbeat durability work, run-start telemetry, cached frozen-deck authentication, and a Windows sharing-safe read-only monitor. Duplicate execution, deterministic comparison, authoritative evidence durability, fail-closed behavior, the 120-turn bound, decks, Pilot behavior, Protocol V1, and Seed Table V2 remain unchanged.

The V16 baseline remains immutable and is authenticated by its recorded SHA-256. The failed run `CALIBRATION_V1_20260922T003835Z_7b0b688c7051` remains preserved forensic evidence. Prototype 0.3 remains unauthorized.
