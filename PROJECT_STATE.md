# Project State

For the cross-department Master Project Map, active milestones, blockers, and immediate priorities,
see [Mutants the Gathering HQ](docs/HQ.md). This file retains the software release-state view.

Current software release: **v0.5.0 — Deck Analysis Engine**.

## Implemented

- v0.1.0 architecture and database foundation.
- v0.2.0 executable Python, SQLite migration, CLI, test, lint, and CI foundation.
- v0.3.0 transactional Scryfall Magic Fact import and import audit.
- v0.4.0 deterministic Capability Engine, Evidence, Confidence, Overrides, and audit runs.
- v0.5.0 objective Deck Metrics and deterministic Deck Analysis Findings.

## Product state

- The accepted product target is a complete ten-deck TMNT battle set, not a single Leonardo deck.
- Leonardo Prototype 0.1 and the Design Intent RFC are accepted on `main`.
- The ten-deck Prototype 0.1 baseline, bounded Prototype 0.2 candidates, and Cardcade through Engine
  0.6 are preserved on `main` following merged PR #15. Prototype 0.3 is not authorized.

## Validation gate

Cardcade is an experimental evidence system, separate from the released v0.5.0 analysis layer. Its
Engine 0.6 stability gate currently fails, so its results are hypotheses rather than deck-edit
instructions. Larger calibration and further Design Studio revisions remain blocked until Cardcade
behavior is credible and the Design Studio explicitly authorizes a bounded revision.

## Next architectural layer

**v0.6.0 — Design Intent implementation** will turn the accepted RFC into a rigorous, versionable
human interpretation of a Character. It must not alter imported Magic Facts or current analytical
behavior.

See the [Roadmap](docs/ROADMAP.md) for direction and [Architecture](docs/ARCHITECTURE.md) for exact
implementation status and boundaries.
