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
- **Deck Analysis Engine** — computes objective deck metrics and explainable threshold findings.
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

Current milestone: **v0.5.0 — Deck Analysis Engine**.

## SewerGraph commands

Initialize or migrate a database:

```console
tmnt init tmnt-design-studio.db
```

Import Scryfall's `default_cards` bulk snapshot, or use a deterministic local JSON array, JSON Lines, gzip, or ZIP source:

```console
tmnt import scryfall --database tmnt-design-studio.db
tmnt import scryfall --database tmnt-design-studio.db --file cards.json
```

Inspect schema and latest import status:

```console
tmnt database status --database tmnt-design-studio.db
```

Derive capabilities, inspect one Oracle card with its evidence, and report the active rule set:

```console
tmnt capabilities derive --database tmnt-design-studio.db
tmnt capabilities inspect "Card Name" --database tmnt-design-studio.db
tmnt capabilities status --database tmnt-design-studio.db
```

Confidence is evidence strength on a 0–1 scale, never card quality, theme fit, or a recommendation.
Derivation atomically replaces the computed layer. Overrides remain separate, explicit decisions.
See [`docs/CAPABILITIES.md`](docs/CAPABILITIES.md) for the complete vocabulary, evidence sources,
examples, negative controls, confidence semantics, and limitations.

Analyze one immutable Deck Version, inspect its current result, or report engine status:

```console
tmnt deck analyze 1 --database tmnt-design-studio.db
tmnt deck inspect 1 --database tmnt-design-studio.db
tmnt deck status --database tmnt-design-studio.db
```

Strict analysis requires exactly 60 legal main-deck cards and current Scryfall and Capability data.
`--diagnostic` permits incomplete deck sizes with an explicit warning. See
[`docs/DECK_ANALYSIS.md`](docs/DECK_ANALYSIS.md) for formulas, provenance, and limitations.

Import attempts retain source metadata, SHA-256 checksum, timestamps, counts, warnings, errors, and outcome. Fact changes commit transactionally; failed attempts remain auditable without exposing partial changes.
