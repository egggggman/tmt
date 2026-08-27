# Mutants the Gathering

Mutants the Gathering is a community-driven tabletop Magic: The Gathering fan project building a cohesive starter/battle set of **ten fun, distinct, themed, Standard-legal 60-card TMNT decks** designed primarily to play against one another.

The project is larger than deck construction. It includes automated playtesting, physical products, printed materials, worldbuilding, publishing, project governance, and presentation.

> Playable first. Explainable increasingly.
>
> Build → Measure → Understand → Refine.

Theme, synergy, balance, character identity, mechanical coherence, and fun are first-class requirements.

Mutants the Gathering is an independent, non-commercial fan project. It is not affiliated with, endorsed by, sponsored by, or presented as authorized by the owners of Teenage Mutant Ninja Turtles, Magic: The Gathering, Scryfall, or any other referenced third-party property.

## Start here

If you are new to the project, read these in order:

1. [Outsider Continuity Guide](docs/OUTSIDER_CONTINUITY.md) — the ten-minute orientation to the complete project.
2. [HQ project map and current status](docs/HQ.md) — department ownership, dependencies, blockers, and immediate priorities.
3. [HQ Current State](docs/hq/CURRENT_STATE.md) — compact dispatch view synchronized to recent merged evidence.
4. [Project State](PROJECT_STATE.md) — durable software/product/validation state.
5. [Tool Resilience](docs/hq/TOOL_RESILIENCE.md) and [Recovery](docs/hq/RECOVERY.md) — how the project continues across tools and fresh machines.
6. [Roadmap](docs/ROADMAP.md) — major development direction.
7. [Accepted Decisions](docs/DECISIONS.md) — durable decisions and historical reasoning.
8. [Project Constitution](docs/PROJECT_CONSTITUTION.md) and [Design Principles](docs/DESIGN_PRINCIPLES.md) — how the project makes decisions.
9. [Contributing](CONTRIBUTING.md) — how to propose and validate changes.

GitHub is the durable source of truth and project bus. ChatGPT Project conversations and coding agents are working tools; durable decisions, task contracts, evidence, and handoffs should be promoted into the repository rather than surviving only in conversation history. Codex is an accelerator, not required infrastructure.

## Target product

The long-term target is a cohesive ten-deck Mutants the Gathering starter/battle set:

- Leonardo
- Raphael
- Donatello
- Michelangelo
- Splinter
- Shredder
- Krang
- Bebop & Rocksteady
- April O'Neil
- Casey Jones

The decks are supported by individual deck boxes, a master collector box, tokens and counters, life counter, Field Manual, dividers, quick-reference materials, matchup tracking, character/art cards, stickers and stamps, and other printed extras.

## Departments

### HQ
Coordinates roadmap, priorities, governance, project status, cross-department decisions, major milestones, and conflicts. HQ coordinates rather than duplicating specialist work.

### Design Studio
Owns the playable decks: Design Intent, deck construction, card selection, character identity, synergy, structural validation, prototype versions, interpretation of playtest evidence, and deck revisions.

### TMNT the Cardcade Game
Owns automated gameplay simulation, reproducible testing, telemetry, engine validation, matchup evidence, calibration artifacts, and consistency/balance analysis. Cardcade reports evidence and hypotheses; it does **not** redesign decks.

### Mr. Paperback
Owns physical products and production deliverables. If something does not print, cut, fold, fit, or play correctly, it is not finished.

### Canon / Source Material
Provides source-backed character research, relationships, flavor, setting, and thematic consistency to support Design Studio and Mr. Paperback.

### The Underground Press
An associated creative publication with a distinct editorial and production workflow. It remains separate from deck design and Cardcade unless work genuinely overlaps.

## Current development state

The ten-deck **Prototype 0.2 environment is frozen** while Cardcade establishes a mechanically credible baseline. **Prototype 0.3 is not authorized** until Cardcade evidence is sufficient and Design Studio explicitly decides what, if anything, should change.

Cardcade's Engine 0.8 architectural foundation has been accepted. Its Foundation Matrix reached **10 GREEN / 10 YELLOW / 0 RED / 0 UNKNOWN**, establishing the architectural baseline while preserving explicit unsupported mechanics rather than silently approximating them.

Post-foundation coverage has continued through accepted bounded Actions and engine corrections, including activated abilities/Priority, targeted Return, Trample, Lifelink, hand-bottom/Draw, Discard/Draw triggers, Sneak, Food, and Actions #13–#16. The latest accepted Action is **Action #16 — ETB artifact-condition Draw (PR #60)**.

Cardcade has also moved into coverage-aware engine validation. **PR #61** merged the accepted Stage 0.2 evidence runner and plan-only launcher with a 45-pairing / 225-distinct-game contract, independent duplicate commitments, explicit `balance_valid: false` evidence, **784 passed / 1 skipped** local validation, and passing exact-head CI. PR #61 integrated tooling only; Stage 0.2 gameplay execution remained subject to a merged-main readiness decision.

These are simulator-credibility milestones, not balance conclusions. The current critical path remains **Cardcade engine validation toward a credible controlled calibration gate**. Prototype 0.3 remains unauthorized until Cardcade evidence is sufficient and Design Studio explicitly decides what, if anything, should change.

## Development discipline

The project follows a few hard rules:

- Preserve meaningful historical prototypes, simulation results, and accepted decisions.
- Distinguish simulator problems from deck-construction, balance, theme, physical-product, and subjective-fun problems.
- Do not modify decks to compensate for simulator defects.
- Do not tune simulator assumptions merely to force win rates toward 50%.
- Prefer the smallest evidence-backed change capable of testing a hypothesis.
- Automated simulation establishes a credible baseline; humans remain the authority on subjective fun.

Testing progresses from structural validation → smoke testing → engine validation → calibration → Design Studio review → revised prototype → repeat. Do not increase simulation volume while simulator behavior itself remains questionable.

## Project dashboards

### The Sewer Status Board
HQ's operational eye-in-the-sky dashboard. It shows what changed, the current Gate, Blockers, Holds, Actionable work, Risks, Milestones, and the Next Move.

`PIZZAGRIND` is only the conversation invocation codeword for rendering the board; the word does not appear inside the board itself. See [Sewer Status Board specification](docs/SEWER_STATUS_BOARD.md).

**The Sewer Board Text** is the detailed text-only counterpart.

### THERECORD
THERECORD is the separate append-only weekly instrumentation archive for usage, efficiency, output, plan pressure, and trend analysis. Detailed usage analytics belong there rather than on the Sewer Status Board. See [THERECORD](docs/THERECORD.md).

## Design Studio technical foundation

The original TMNT Design Studio software remains an important project subsystem. Its knowledge pipeline stores objective Magic facts, computes reproducible intelligence, and preserves human decisions and history.

```text
Character
└── Design Intent
    └── Sewer Deck
        └── Deck Version
```

```text
Scryfall → Magic Facts → Capability Engine → Deck Metrics → Deck Analysis
         → Design Intent → Alignment → Recommendations → Playtesting → iteration
```

Technical source-of-truth documents include [Architecture](docs/ARCHITECTURE.md), [Database](docs/DATABASE.md), [Capabilities](docs/CAPABILITIES.md), and [Deck Analysis](docs/DECK_ANALYSIS.md).

## Quick start

Install the project with [uv](https://docs.astral.sh/uv/):

```console
uv sync
uv run tmnt init tmnt-design-studio.db
```

Import Scryfall data and inspect database status:

```console
tmnt import scryfall --database tmnt-design-studio.db
tmnt database status --database tmnt-design-studio.db
```

Derive and inspect Capabilities:

```console
tmnt capabilities derive --database tmnt-design-studio.db
tmnt capabilities inspect "Card Name" --database tmnt-design-studio.db
tmnt capabilities status --database tmnt-design-studio.db
```

Analyze and inspect one immutable Deck Version:

```console
tmnt deck analyze 1 --database tmnt-design-studio.db
tmnt deck inspect 1 --database tmnt-design-studio.db
tmnt deck status --database tmnt-design-studio.db
```

## Community world and publishing

The [World Guide](docs/WORLD_GUIDE.md) defines the living underground community. The [Underground Press](docs/UNDERGROUND_PRESS.md) is its in-universe newspaper, and Puzzle Dojo is its playful learning section. These layers may inform and celebrate the project, but they do not change Magic facts or Cardcade evidence.

## Contribution philosophy

Contributions should be small in responsibility, evidence-backed, explainable, respectful of source material, and explicit about uncertainty. Preserve architectural and department boundaries, and use an ADR or RFC for hard-to-reverse changes.

## License and third-party material

Original work authored by this project's contributors is made available under the [Apache License 2.0](LICENSE) only where the contributors have the rights to license that work. This can include original software, systems, tooling, architecture, schemas, workflows, governance, documentation, editorial systems, templates, design systems, and production infrastructure.

**Third-party intellectual property is not licensed under Apache 2.0.** Teenage Mutant Ninja Turtles and Magic: The Gathering names, characters, likenesses, logos, trademarks, artwork, stories, card content, game materials, and other protected intellectual property remain solely with their respective rights holders. Scryfall and other third-party data/assets remain subject to their applicable rights, licenses, policies, and terms.

See [NOTICE](NOTICE) for the formal project-wide licensing boundary and third-party exclusions.
