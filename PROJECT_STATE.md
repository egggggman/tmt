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

Cardcade Engine 0.8's architectural foundation remains accepted at **10 GREEN / 10 YELLOW / 0 RED / 0 UNKNOWN**. Post-foundation work is banked through **Action #32** where repository evidence supports acceptance; Action #33 remains **NOT AUTHORIZED**. The Action #32 packet is validation evidence, not balance evidence.

The governing preparation state is:

- Pilot Fitness V3 bounded pass completed and recorded in `docs/cardcade/PILOT_FITNESS_V3_*`;
- Calibration Protocol V1 is the governing calibration design;
- Seed Table V2 is frozen and immutable;
- authenticated calibration release and execution preparation progressed through V16;
- PR #172, merged as `58a8bac85600318ccd727959770b60869003c017`, established the fail-closed run-ID reservation contract.

V16 run `CALIBRATION_V1_20260919T012117Z_65775003` reached **121,808 / 184,320 distinct games (66.09%)** before failing closed because local storage was exhausted. V16 is classified as an incomplete storage/evidence failure, not balance evidence and not a demonstrated gameplay-engine failure. It must never be resumed, combined with later calibration results, or used for partial balance conclusions. Historical calibration evidence and its verified archive migration remain preserved.

The migrated execution host is qualified for prospective V17 evidence: `C:\Projects\tmt` is code/runtime and `G:\` is the live evidence target. G: is NTFS with **976.56 GiB capacity**, **874.66 GiB free**, and **2,000/2,000** atomic write/replace/read-back cycles successful with zero failures. V17 has not been reserved or executed.

These results establish infrastructure and engine-validation evidence, not competitive balance conclusions. Cardcade reports evidence and hypotheses; Design Studio owns deck revisions; HQ owns authorization gates.

## Current Gate

The current gate is **durable GitHub state synchronization**. After independent review and merge of this documentation synchronization, the critical path is: **reserve a fresh V17 identity → render/authenticate exact run-specific artifacts → separately authorize execution → run the complete 184,320-game Protocol V1 dataset → integrity audit → statistical analysis → Design Studio review**.

Prototype 0.2 remains frozen. Prototype 0.3, balance analysis, V17 reservation, wrapper generation, and calibration execution are not authorized by this state document.

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

**Independently review and merge the documentation synchronization.** Only then should HQ decide whether to authorize the separate V17 reservation step. Other departments may continue work that does not alter frozen decks, seeds, Protocol V1, or Cardcade authorization state.

See the [Roadmap](docs/ROADMAP.md) for long-term direction and [Architecture](docs/ARCHITECTURE.md) for Design Studio software-layer boundaries.
