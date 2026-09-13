# Calibration Release Addendum V1

Status: **release-readiness candidate only**. This document does not authorize calibration execution.

- Main commit: `011d7ad6a3ea1e11301c1db6dbf6d7da27b05e8c`.
- Card corpus: `cardcade/card-model-0.6.json`, frozen by main.
- Decks: ten accepted frozen prototype files under `decks/*`; identities must be recorded in the release manifest.
- Pilot: accepted Pilot Fitness V3 bounded PASS; privacy and filtering remain inconclusive.
- Calibration Protocol V1: `96fc43ec3203938eb385618f6187f8496b93ecd3`.
- Seed table: not generated; path and hash must be frozen before execution.

All five mandatory gameplay families are closed. The four deferred risks are closed: Tunnel Rats graveyard self-return tapped, Frog Butler mana of any color, Frog Butler temporary Reach, and Michelangelo extra +1/+1 replacement. Historical runs contribute zero calibration observations.

The protocol requires 45 cross-deck matchups, paired orientations, whole-roster independent blocks, duplicate replay only for authentication, simultaneous uncertainty across 56 endpoints, fixed thresholds, fail-closed invalid handling, and no adaptive sampling.

Capacity must be demonstrated for 184,320 distinct games / 368,640 executions, with raw evidence, normalized outputs, authentication, and checksums. Record OS, Python/uv, CPU, memory, storage, runner identity, tool versions, seed table, source hashes, and deck hashes. Any resource shortfall, invalid game, missing evidence, seed deviation, or determinism mismatch stops the run.

Separate HQ execution authorization remains mandatory. No calibration execution, Action #33, deck revision, or Prototype 0.3 is authorized here.

