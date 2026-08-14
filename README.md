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

Current software release: **v0.5.0 — Deck Analysis Engine**.

Implemented layers import Scryfall Magic Facts, derive Effective Capabilities with Evidence, and
compute deterministic Deck Metrics and Findings. The Design Intent RFC and Leonardo Prototype 0.1
are accepted; Design Intent runtime behavior begins in v0.6.0. Alignment, Recommendations, and
expanded Playtesting follow.

The product target is a complete ten-deck TMNT battle set. The ten-deck Prototype 0.1 baseline,
bounded Prototype 0.2 candidates, and Cardcade through Engine 0.6 are preserved on `main` following
merged PR #15. Engine 0.6 still fails its stability gate, so its findings remain hypotheses and
Prototype 0.3 is not authorized. See [Project State](PROJECT_STATE.md), [HQ](docs/HQ.md), and the
[Roadmap](docs/ROADMAP.md) for the distinct software, product, and validation views.

Completed releases:

- **v0.1.0** — Architecture Foundation
- **v0.2.0** — Executable Foundation
- **v0.3.0** — Scryfall Import Pipeline
- **v0.4.0** — Capability Engine
- **v0.5.0** — Deck Analysis Engine

## Core hierarchy

```text
Character
└── Design Intent
    └── Sewer Deck
        └── Deck Version
```

## Architecture at a glance

```text
Scryfall → Magic Facts → Capability Engine → Deck Metrics → Deck Analysis
         → Design Intent → Alignment → Recommendations → Playtesting → iteration
```

The first three reasoning stages through Deck Analysis are implemented. Later stages are planned and
cannot be treated as current behavior. [Architecture](docs/ARCHITECTURE.md) defines layer boundaries,
implementation status, and invariants.

## Start here

1. [Project Constitution](docs/PROJECT_CONSTITUTION.md) — why the project exists.
2. [Design Principles](docs/DESIGN_PRINCIPLES.md) — how contributors make decisions.
3. [Glossary](docs/GLOSSARY.md) — canonical shared vocabulary.
4. [Architecture](docs/ARCHITECTURE.md) — technical responsibilities and dependency flow.
5. [Roadmap](docs/ROADMAP.md) — completed and future milestone direction.
6. [Contributing](CONTRIBUTING.md) — how to propose and validate changes.

## Governance

- [HQ project map and current status](docs/HQ.md)
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

## License and third-party material

Original work authored by this project's contributors is made available under the
[Apache License 2.0](LICENSE). This includes original software and infrastructure, project tooling,
architecture, schemas, workflows, governance and validation systems, original documentation, and
original project-created design systems and production materials where the project has the rights to
license them.

The project-wide original foundation includes work across HQ, Design Studio, TMNT the Cardcade Game,
Mr. Paperback, Canon/Source Material, and The Underground Press. For The Underground Press this can
include original editorial systems, newspaper design language, templates, component and layout
systems, production workflow, original writing, and independently created worldbuilding.

**Third-party intellectual property is not licensed under Apache 2.0.** TMNT and Magic: The
Gathering names, characters, trademarks, card content, artwork, and other protected materials remain
the property of their respective rights holders. Scryfall material and other third-party data,
software, fonts, artwork, and assets remain subject to their applicable rights, licenses, policies,
and terms. Their presence in this repository does not imply ownership, affiliation, endorsement, or
an Apache license grant.

See [NOTICE](NOTICE) for the project-wide licensing boundary and third-party exclusions.
