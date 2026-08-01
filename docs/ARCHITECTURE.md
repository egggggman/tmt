# Architecture

## Purpose

TMNT Design Studio is a knowledge-driven deck design system. It combines objective Magic card data, curated TMNT design intent, derived card capabilities, deck analysis, explainable recommendations, and preserved design history.

## Golden rule

> Store facts. Compute intelligence. Preserve decisions.

## Information classes

### Facts

Objective information that can be imported or directly recorded.

Examples:

- Card name
- Mana cost
- Oracle text
- Types and keywords
- Standard legality
- Deck card quantities
- Playtest date and result

Facts are stored.

### Intent

Human-authored design direction.

Examples:

- Character
- Design Intent manifesto
- Theme priorities
- Desired capabilities
- Experience goals
- Accepted weaknesses

Intent is stored and versioned when it changes meaningfully.

### Analysis

Results that can be recreated from facts and intent.

Examples:

- Deck Profile
- Mana curve
- Capability balance
- Theme coverage
- Identity drift
- Deck health
- Recommendation score

Analysis is computed. Cached results may be stored only when needed for performance and must remain reproducible.

### Presentation

Human-readable views over facts, intent, and analysis.

Examples:

- Card Dossier
- Character Dossier
- Deck Dossier
- Underground Press article

Presentation is generated rather than treated as canonical data.

## Domain hierarchy

```text
Character
└── Design Intent
    └── Sewer Deck
        └── Deck Version
```

A Character may own multiple Design Intents directly. This supports multiple authentic playstyles for multifaceted characters without overwriting prior work.

## Engines

### Scryfall Importer

Imports objective Magic facts and records import history. It does not make TMNT judgments.

### Capability Engine

Derives gameplay Capabilities from card facts, mechanics, and rules text. It uses explicit, testable rules and supports documented designer overrides.

### Deck Analysis Engine

Reads one immutable Deck Version plus current imported Magic facts and effective Capabilities. Its
metrics layer computes objective composition, curve, color, Capability, density, and redundancy
facts. Its analysis layer emits deterministic observations and warnings from named thresholds.
Every run identifies the deck checksum, Scryfall import, Capability run and checksum, and analysis
engine version and checksum.

This engine does not build a Deck Profile, judge theme or Character fit, recommend cards, predict
matchups, or label a deck good or bad. Minimal relationships report only co-occurring objective
facts. Failed runs preserve audit history while leaving the prior successful current result intact.

### Context-Aware Recommendation Engine

Ranks candidate cards for a specific Design Intent and current deck state. It considers:

- Standard legality
- Character and Design Intent fit
- Current capability gaps
- Mana curve needs
- Theme coverage
- Synergy and redundancy
- Competitive value
- Playtest evidence
- Designer overrides

Every recommendation must expose its evidence.

## System flow

```text
Scryfall
  ↓
Magic Facts
  ↓
Capability Engine
  ↓
Effective Card Capabilities
  ↓
Deck Analysis Engine
  ↓
Deck Profile
  ↓
Recommendation Engine
  ↓
Explainable Recommendations
```

## Component boundaries

- **SewerGraph** stores durable facts, intent, decisions, overrides, decks, versions, and playtest evidence.
- **Engines** compute analysis and recommendations.
- **CLI/UI** presents results and gathers designer input.
- **Encyclopedia** publishes durable reference material and dossiers.
- **Underground Press** publishes design journals, card spotlights, development reports, and project updates.

## Version 1 constraints

- Standard only.
- 60-card Sewer Decks.
- Python implementation.
- SQLite database.
- CLI before graphical UI.
- Leonardo as the first reference implementation.


## Capability Engine execution

The Oracle card is the analysis unit. Ordered card faces and normalized keywords may contribute
attributed evidence, but never become independent capability owners. Narrow, versioned rules read
named objective fields. Every match records its source fact, matched value, face number when
applicable, rule identity and version, confidence, derivation run, and Scryfall import.

Derivation replaces the current computed and evidence layers inside one immediate transaction. A
failure rolls back those changes and records a failed run, leaving the prior successful results
visible. Identical facts and the same rule-set checksum produce identical results. The engine contains
no Character, Design Intent, Theme, Deck Profile, recommendation, ranking, or deck-analysis logic.

Effective capabilities resolve at read time. Matching derived rules combine by maximum confidence
while retaining every evidence row. One active override may then add, remove, or adjust a capability.
Remove suppresses without deleting evidence; add supplies override confidence; adjust applies a
signed delta clamped to 0–1. Conflicting active overrides are rejected, never last-write-wins.

The initial `2026.08.1` rule set strips parenthetical reminder text, evaluates face text instead of
duplicated card-level text for multiface cards, excludes controller-owned removal targets and
opponent-only benefits, and treats temporary mana as fixing rather than permanent ramp. The full
catalog and rule-quality controls are specified in `docs/CAPABILITIES.md`.
