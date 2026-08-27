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

The earlier Engine 0.6 stability failure and the PR #33 telemetry checkpoint remain preserved historical evidence, not the current Cardcade state.

Cardcade Engine 0.8's architectural foundation remains accepted at **10 GREEN / 10 YELLOW / 0 RED / 0 UNKNOWN**. Post-foundation work has continued through bounded Actions and generic engine corrections, including activated abilities/Priority, targeted Return, Trample, Lifelink, hand/library operations, attack/death/ETB triggers, Sneak, Food, and Actions #13–#16.

Recent accepted milestones include:

- PR #58 — Action #14, bounded ETB drain/gain/Scry;
- PR #59 — Action #15, bounded permanent-leaves +1/+1 counter trigger;
- PR #60 — Action #16, bounded ETB artifact-condition Draw;
- PR #61 — accepted Coverage-Aware Engine Validation Stage 0.2 evidence runner and plan-only launcher.

PR #61's accepted contract covers **45 pairings / 225 distinct planned games / 450 executions / 900 per-execution commitment artifacts**. It preserves explicit `balance_valid: false` engine-validation evidence, reported **784 passed / 1 skipped** locally, and passed exact-head CI before merge.

**PR #61 did not authorize or execute Stage 0.2 gameplay.** Final execution authorization remained subject to a merged-main readiness audit.

These results establish engine-validation evidence, not competitive balance conclusions.

## Current Gate

The current critical path is **Cardcade engine validation toward a credible controlled calibration gate**.

The architectural foundation and many bounded mechanics are accepted, but calibration and Prototype 0.3 review remain gated. The immediate Cardcade decision is whether merged-main evidence now authorizes Engine Validation Stage 0.2 execution. Do not skip readiness gates, and do not change decks to hide unsupported engine behavior.

## Cross-project operating views

- [HQ](docs/HQ.md) — project map, current Critical Path, department status, and Next Move.
- [The Sewer Status Board](docs/SEWER_STATUS_BOARD.md) — operational visual-dashboard standard.
- **The Sewer Board Text** — detailed text counterpart used in working conversations.
- [THERECORD](docs/THERECORD.md) — append-only weekly usage/efficiency instrumentation archive.
- [HQ Current State](docs/hq/CURRENT_STATE.md) — compact dispatch view.
- [Tool Resilience](docs/hq/TOOL_RESILIENCE.md) — GitHub-centered continuity policy.
- [Recovery Guide](docs/hq/RECOVERY.md) — fresh-clone restart procedure.
- [Work Packet Specification](docs/hq/WORK_PACKET_SPEC.md) — portable task/handoff contract.

## Next Move

**Complete the merged-main readiness decision for Cardcade Engine Validation Stage 0.2 while HQ completes Resilience 0.1 — GitHub Can Run the Project.** Other departments may continue actionable work that does not pretend to unblock Cardcade's gate.

See the [Roadmap](docs/ROADMAP.md) for long-term direction and [Architecture](docs/ARCHITECTURE.md) for Design Studio software-layer boundaries.
