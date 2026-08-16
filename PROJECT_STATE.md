# Project State

For the cross-department Master Project Map, active milestones, blockers, and immediate priorities, see [Mutants the Gathering HQ](docs/HQ.md). For a newcomer-oriented map of the complete project, see [Outsider Continuity](docs/OUTSIDER_CONTINUITY.md).

This file distinguishes the released Design Studio analysis software from the broader product and Cardcade validation state.

## Released analytical software

Current released Design Studio analysis layer: **v0.5.0 — Deck Analysis Engine**.

Implemented released layers:

- v0.1.0 architecture and database foundation;
- v0.2.0 executable Python, SQLite migration, CLI, test, lint, and CI foundation;
- v0.3.0 transactional Scryfall Magic Fact import and import audit;
- v0.4.0 deterministic Capability Engine, Evidence, Confidence, Overrides, and audit runs;
- v0.5.0 objective Deck Metrics and deterministic Deck Analysis Findings.

That release number is not the Cardcade engine version and should not be read as the status of the entire Mutants the Gathering project.

## Product state

- The accepted product target is a complete ten-deck Mutants the Gathering starter/battle set.
- Leonardo Prototype 0.1 and the Design Intent RFC are accepted and preserved.
- All ten Prototype 0.1 decks and the bounded Prototype 0.2 environment are preserved on `main`.
- **Prototype 0.2 is currently frozen.**
- **Prototype 0.3 is not authorized.** A future revision requires sufficient Cardcade evidence plus an explicit Design Studio decision.
- Cardcade evidence is not a deck-edit instruction; Design Studio owns all deck revisions.

## Cardcade validation state

The earlier Engine 0.6 stability failure is historical evidence, not the current Cardcade state.

PR #27 established and accepted Cardcade's Engine 0.8 architectural foundation. The final Foundation Matrix reached:

- **10 GREEN**
- **10 YELLOW**
- **0 RED**
- **0 UNKNOWN**

The accepted foundation includes authoritative runtime identity and zone movement, Engine/Interpreter/Pilot responsibility boundaries, explicit turn/phase/step state, Stack, fixed mana Costs, represented Triggers, P/T Layers, and deterministic RNG foundations. Unsupported mechanics remain explicit rather than silently approximated.

Post-foundation mechanical coverage has been merged incrementally:

- PR #30 — Create Token;
- PR #31 — Deal Damage;
- PR #32 — Scry;
- PR #33 — First Strike / Double Strike combat damage steps.

At PR #33 the full validation suite reported **314 passed / 1 skipped**, Acceptance Match #001 remained deterministic, invariant violations remained zero, and unsupported telemetry was **61 events / 18 exact pairs**.

Those results establish engine evidence, not competitive balance conclusions.

## Current Gate

The current critical path is **Cardcade mechanical coverage and validation**.

The architectural foundation is accepted, but broad calibration, large smoke batches, and Prototype 0.3 review remain gated until the represented mechanics used by the ten-deck environment are sufficiently trustworthy.

The next Cardcade work should continue to use the smallest reusable, rules-grounded correction or Action supported by current evidence. Do not change decks to hide unsupported engine behavior.

## Cross-project operating views

- [HQ](docs/HQ.md) — project map, current Critical Path, department status, and Next Move.
- [The Sewer Status Board](docs/SEWER_STATUS_BOARD.md) — operational visual-dashboard standard.
- **The Sewer Board Text** — detailed text counterpart used in working conversations.
- [THERECORD](docs/THERECORD.md) — append-only weekly usage/efficiency instrumentation archive.

## Next Move

**Continue Cardcade mechanical-coverage validation until the simulator can support a credible calibration gate.** Other departments may continue actionable work that does not pretend to unblock that critical path.

See the [Roadmap](docs/ROADMAP.md) for long-term direction and [Architecture](docs/ARCHITECTURE.md) for Design Studio software-layer boundaries.
