# TMNT Design Studio

TMNT Design Studio is a knowledge-driven system for creating **Sewer Decks**: 60-card,
Standard-legal Magic: The Gathering decks that express a TMNT Character through a clear Design
Intent. It stores objective facts, computes reproducible intelligence, and preserves human decisions
and history. It exists to make deck-building reasoning inspectable, preserve the path from source
material to design decisions, and help a community learn together.

TMNT Design Studio is an independent, non-commercial fan project created to celebrate the TMNT and
Magic communities. It is not affiliated with, endorsed by, or presented as authorized by any rights
holder.

> Store facts. Compute intelligence. Preserve decisions.

## Current status

Current release: **v0.5.0 â€” Deck Analysis Engine**.

Implemented layers import Scryfall Magic Facts, derive Effective Capabilities with Evidence, and
compute deterministic Deck Metrics and Findings. Design Intent behavior begins in v0.6.0; Alignment,
Recommendations, and expanded Playtesting follow. See the [Roadmap](docs/ROADMAP.md) for confirmed
milestones and deliberately deferred work.

Completed releases:

- **v0.1.0** — Architecture Foundation
- **v0.2.0** — Executable Foundation
- **v0.3.0** — Scryfall Import Pipeline
- **v0.4.0** — Capability Engine
- **v0.5.0** — Deck Analysis Engine

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
[Capabilities](docs/CAPABILITIES.md), [Deck Analysis](docs/DECK_ANALYSIS.md), and the
[Design Intent RFC](docs/DESIGN_INTENT_RFC.md).

## Community world and publishing

The [World Guide](docs/WORLD_GUIDE.md) defines the living underground community. The
[Underground Press](docs/UNDERGROUND_PRESS.md) is its in-universe newspaper, and Puzzle Dojo is its
playful learning section. These layers inform, connect, celebrate, and preserve community history;
they never change Magic Facts, engine behavior, or analytical results.

## Quick start

Install the project with [uv](https://docs.astral.sh/uv/), then initialize or migrate SewerGraph:

```console
uv sync
uv run tmnt init tmnt-design-studio.db
```

The commands below assume the environment is active; prefix them with `uv run` when appropriate.

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

## Contribution philosophy

Contributions should be small in responsibility, evidence-backed, explainable, and respectful of
source material and one another. Start with [Contributing](CONTRIBUTING.md), use the
[Glossary](docs/GLOSSARY.md), preserve architectural boundaries, and propose hard-to-reverse changes
through an ADR or RFC before implementation. Community before ego; always leave room for the Rule of
Joy.

