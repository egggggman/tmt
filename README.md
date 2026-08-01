# TMNT Design Studio

TMNT Design Studio is a knowledge-driven design system for creating **Sewer Decks**: 60-card, Standard-legal Magic: The Gathering decks that express a specific TMNT character through a clear Design Intent.

The project balances two goals:

1. The deck should feel unmistakably like the chosen TMNT character and Design Intent.
2. The deck should be as strong, coherent, and synergistic as reasonably possible within Standard.

## Core hierarchy

```text
Character
└── Design Intent
    └── Sewer Deck
        └── Deck Version
```

## Core components

- **SewerGraph** — SQLite knowledge database for Magic facts, TMNT knowledge, design decisions, overrides, deck history, and playtest evidence.
- **Scryfall Importer** — imports objective Magic card data.
- **Capability Engine** — derives what cards do from rules text, types, and keywords, with documented designer overrides for edge cases.
- **Deck Analysis Engine** — computes mana curve, capability balance, theme coverage, synergy, and deck health.
- **Context-Aware Recommendation Engine** — recommends cards based on the current deck, its Design Intent, and its unmet needs.
- **TMNT Design Encyclopedia** — human-readable reference material and dossiers.
- **Underground Press** — future publishing layer for design journals, card spotlights, deck development reports, and project updates.

## Architectural rule

> Store facts. Compute intelligence. Preserve decisions.

## Version 0.1 scope

- Standard only.
- Python and SQLite.
- Explainable recommendations.
- Capabilities derived automatically with documented overrides.
- Leonardo as the first reference implementation.

Current milestone: **v0.1.0 — Architecture and Database Foundation**.

## SewerGraph commands

Initialize or migrate a database:

```console
tmnt init tmnt-design-studio.db
```

Import Scryfall's `default_cards` bulk snapshot, or use a deterministic local JSON, gzip, or ZIP source:

```console
tmnt import scryfall --database tmnt-design-studio.db
tmnt import scryfall --database tmnt-design-studio.db --file cards.json
```

Inspect schema and latest import status:

```console
tmnt database status --database tmnt-design-studio.db
```

Import attempts retain source metadata, SHA-256 checksum, timestamps, counts, warnings, errors, and outcome. Fact changes commit transactionally; failed attempts remain auditable without exposing partial changes.

