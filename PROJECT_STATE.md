# Project State

For the cross-department Master Project Map, active milestones, blockers, and immediate priorities,
see [Mutants the Gathering HQ](docs/HQ.md). This file retains the software release-state view.

Current release: **v0.5.0 — Deck Analysis Engine**.

## Implemented

- v0.1.0 architecture and database foundation.
- v0.2.0 executable Python, SQLite migration, CLI, test, lint, and CI foundation.
- v0.3.0 transactional Scryfall Magic Fact import and import audit.
- v0.4.0 deterministic Capability Engine, Evidence, Confidence, Overrides, and audit runs.
- v0.5.0 objective Deck Metrics and deterministic Deck Analysis Findings.

## Current focus

- Consolidate governance, terminology, onboarding, architecture, roadmap, and world documentation.
- Prepare the Design Intent RFC without implementing v0.6.0 behavior.

## Next architectural layer

**v0.6.0 — Design Intent** will define a rigorous, versionable human interpretation of a Character.
It must not alter imported Magic Facts or current analytical behavior.

See the [Roadmap](docs/ROADMAP.md) for direction and [Architecture](docs/ARCHITECTURE.md) for exact
implementation status and boundaries.
