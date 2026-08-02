# Architecture

## Purpose

TMNT Design Studio is a layered, knowledge-driven system for designing explainable Character Sewer
Decks. This document defines technical responsibilities, dependency order, implementation status,
and invariants. Project values live in the [Constitution](PROJECT_CONSTITUTION.md).

## Golden rule

> Store facts. Compute intelligence. Preserve decisions.

## Information classes

### Facts

Authoritative imports or direct observations: Oracle text, types, Standard legality, card quantities,
and recorded play outcomes. Facts are stored with Provenance.

### Intent and decisions

Human-authored direction such as Character, Design Intent, priorities, experience goals, accepted
weaknesses, Override rationale, and design decisions. Intent is stored and meaningfully versioned.

### Computed intelligence

Reproducible results such as Effective Capabilities, Deck Metrics, Findings, future Alignment, and
future Recommendations. Current results may be persisted for inspection and performance only with
their exact inputs, rules, versions, and audit history.

### Presentation

Human-readable views such as dossiers, reports, and Underground Press articles. Presentation is
generated or authored communication; it is never a hidden analytical input.

## Domain hierarchy

```text
Character
â””â”€â”€ Design Intent
    â””â”€â”€ Sewer Deck
        â””â”€â”€ Deck Version
```

A Character may own multiple Design Intents. Each represents an authentic but distinct gameplay
interpretation without overwriting the others.

## Master reasoning flow

```text
Scryfall
  â†“
objective Magic Facts                         [implemented: v0.3.0]
  â†“
Capability Engine                             [implemented: v0.4.0]
  â†“
Effective Capabilities + Evidence
  â†“
Deck Metrics
  â†“
Deck Analysis + Findings                      [implemented: v0.5.0]
  â†“
Design Intent                                 [planned: v0.6.0]
  â†“
Alignment                                     [planned: v0.7.0]
  â†“
Recommendations                               [planned: v0.8.0]
  â†“
Playtesting                                   [planned expansion: v0.9.0]
  â†“
iteration through a new immutable Deck Version
```

Arrows indicate allowed reasoning dependencies, not automatic execution. A later layer reads the
outputs and Provenance of earlier layers; it does not rewrite them.

## Implemented layers

### SewerGraph and migrations â€” v0.2.0

SQLite stores durable facts, intent foundations, decisions, overrides, immutable Deck Versions,
Provenance, and run history. Migrations are ordered, checksummed, transactional, and immutable after
release. Foreign keys are enabled and verified by the application connection layer. See
[Database](DATABASE.md).

### Scryfall Importer â€” v0.3.0

Imports objective Oracle Cards, Printings, ordered Card Faces, Standard legality, keywords, types,
and subtypes. Import attempts retain source metadata, checksums, counts, warnings, errors, timing,
and outcome. Failed fact transactions do not expose partial changes.

### Capability Engine â€” v0.4.0

The Oracle Card is the analysis unit. Card Faces and normalized fields contribute attributed
Evidence. Narrow, versioned rules read named objective fields; each match records source fact,
matched value, face, rule, Confidence, Rule Set, run, and source import.

Derivation atomically replaces the current computed layer while preserving run history. Effective
Capabilities resolve derived rules plus one active, documented add/remove/adjust Override. Conflicts
are invalid rather than last-write-wins. Full semantics live in [Capabilities](CAPABILITIES.md).

### Deck Analysis Engine â€” v0.5.0

Reads one immutable Deck Version, current Magic Facts, and Effective Capabilities. It computes
objective composition, curve, color, Capability, density, ratio, duplicate, and redundancy Deck
Metrics, then emits deterministic Findings from named thresholds.

Every run identifies the deck checksum, Scryfall import, Capability run and checksum, Engine Version,
and checksum. It does not judge Character fit, build a profile, recommend cards, predict matchups, or
label a deck good or bad. See [Deck Analysis](DECK_ANALYSIS.md).

## Planned layers

### Design Intent â€” v0.6.0

Preserves a versionable human interpretation of a Character. It cannot alter imported Magic Facts,
Capability Evidence, or Deck Metrics.

### Alignment â€” v0.7.0

Interprets how evidence supports a specific Design Intent. It is contextual and explainable, never a
universal card-quality score.

### Recommendations â€” v0.8.0

Proposes contextual changes using a Deck Version, Design Intent, Alignment, objective needs, and
constraints. Every Recommendation must cite Evidence, rules, tradeoffs, and versions.

### Playtesting and iteration â€” v0.9.0

Connects structured sessions and observations to immutable Deck Versions. Learning informs later
decisions and new versions without rewriting prior evidence.

## Component boundaries

- **SewerGraph** stores durable state and auditable computed run outputs.
- **Engines** derive one bounded class of reproducible intelligence.
- **CLI/UI** coordinates services, presents results, and gathers explicit human input.
- **TMNT Design Encyclopedia** publishes durable research and editorial outputs.
- **The Underground Press** reports, connects, celebrates, and preserves community history.

The world and publication layers can explain analytical work but cannot affect engine results.

## Architectural invariants

1. Imported facts remain objective and retain source Provenance.
2. Computed intelligence is reproducible from exact versioned inputs and rules.
3. Human intent, Overrides, rationale, and decisions are explicit and preserved.
4. Layers do not bypass one another or silently rewrite upstream meaning.
5. Recommendations must cite Evidence and expose constraints and tradeoffs.
6. Design Intent cannot alter imported Magic Facts.
7. Community and in-universe content cannot affect analytical results.
8. Presentation never becomes canonical truth merely because it is persuasive.
9. Failed runs preserve audit history without replacing the prior successful current result.
10. Planned behavior is labeled planned until implementation and release evidence exist.

## Version 1 constraints

- Standard only.
- Exactly 60 main-deck cards for strict analysis.
- Python and SQLite.
- CLI before graphical UI.
- Leonardo as the first end-to-end reference Character.

