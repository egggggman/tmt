# TMNT Design Studio

TMNT Design Studio is a knowledge-driven system for creating **Sewer Decks**: 60-card,
Standard-legal Magic: The Gathering decks that express a TMNT Character through a clear Design
Intent. It stores objective facts, computes reproducible intelligence, and preserves human decisions
and history.

> Store facts. Compute intelligence. Preserve decisions.

## Current status

Current release: **v0.5.0 â€” Deck Analysis Engine**.

Implemented layers import Scryfall Magic Facts, derive Effective Capabilities with Evidence, and
compute deterministic Deck Metrics and Findings. Design Intent behavior begins in v0.6.0; Alignment,
Recommendations, and expanded Playtesting follow. See the [Roadmap](docs/ROADMAP.md) for confirmed
milestones and deliberately deferred work.

## Core hierarchy

```text
Character
â””â”€â”€ Design Intent
    â””â”€â”€ Sewer Deck
        â””â”€â”€ Deck Version
```

## Architecture at a glance

```text
Scryfall â†’ Magic Facts â†’ Capability Engine â†’ Deck Metrics â†’ Deck Analysis
         â†’ Design Intent â†’ Alignment â†’ Recommendations â†’ Playtesting â†’ iteration
```

The first three reasoning stages through Deck Analysis are implemented. Later stages are planned and
cannot be treated as current behavior. [Architecture](docs/ARCHITECTURE.md) defines layer boundaries,
implementation status, and invariants.

## Start here

1. [Project Constitution](docs/PROJECT_CONSTITUTION.md) â€” why the project exists.
2. [Design Principles](docs/DESIGN_PRINCIPLES.md) â€” how contributors make decisions.
3. [Glossary](docs/GLOSSARY.md) â€” canonical shared vocabulary.
4. [Architecture](docs/ARCHITECTURE.md) â€” technical responsibilities and dependency flow.
5. [Roadmap](docs/ROADMAP.md) â€” completed and future milestone direction.
6. [Contributing](CONTRIBUTING.md) â€” how to propose and validate changes.

## Governance

- [Project Constitution](docs/PROJECT_CONSTITUTION.md)
- [Design Principles](docs/DESIGN_PRINCIPLES.md)
- [Canonical Glossary](docs/GLOSSARY.md)
- [Vision-oriented Roadmap](docs/ROADMAP.md)
- [Repository Health checklist](docs/REPOSITORY_HEALTH.md)

Technical source-of-truth documents remain [Architecture](docs/ARCHITECTURE.md),
[Database](docs/DATABASE.md), [Accepted Decisions](docs/DECISIONS.md),
[Capabilities](docs/CAPABILITIES.md), and [Deck Analysis](docs/DECK_ANALYSIS.md).

## Community world and publishing

The [World Guide](docs/WORLD_GUIDE.md) defines the living underground community. The
[Underground Press](docs/UNDERGROUND_PRESS.md) is its in-universe newspaper, and Puzzle Dojo is its
playful learning section. These layers inform, connect, celebrate, and preserve community history;
they never change Magic Facts, engine behavior, or analytical results.

## Commands

Initialize or migrate SewerGraph:

```console
tmnt init tmnt-design-studio.db
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

See [Capabilities](docs/CAPABILITIES.md) and [Deck Analysis](docs/DECK_ANALYSIS.md) for complete
semantics, Provenance, validation, and limitations.

