# Glossary

## Purpose

This is the canonical public vocabulary for TMNT Design Studio. Definitions state project meaning;
linked specifications contain implementation detail. A planned term is labeled as planned and must
not be read as an implementation claim.

### Alignment

A planned, explainable assessment of how evidence from a card, Relationship, or Deck Version
supports a specific Design Intent. Alignment is interpretation, not an objective card fact or
universal quality score. Planned for v0.7.0.

### Audit Run

A durable record of one attempted engine or import execution: inputs, versions, checksums, timing,
outcome, counts, and errors. Successful and failed runs remain available for reconstruction.

### Capability

A narrow canonical description of what an Oracle Card accomplishes in gameplay. Capabilities are
derived from explicit rules and Evidence. See [Capabilities](CAPABILITIES.md).

### Card Face

One ordered face of a multifaced Oracle Card. A Card Face contributes attributed facts and Evidence;
it is not an independent Capability owner.

### Character

A TMNT person, ally, villain, team, or faction that may own one or more Design Intents.

### Community First

The commitment to prefer shared understanding, welcome, credit, participation, safety, and community
benefit over status, control, audience growth, or personal ownership.

### Confidence

A bounded statement of Evidence strength for a specific derived result. Confidence is not card
quality, Character fit, recommendation strength, or certainty about future play.

### Deck Analysis

The implemented deterministic process that computes Deck Metrics and Findings for one immutable Deck
Version. It does not judge Character fit or recommend changes. See [Deck Analysis](DECK_ANALYSIS.md).

### Deck Metric

One objective, reproducible measurement of a Deck Version. Examples include a count, mana-value
distribution, color requirement, Capability total, density, ratio, or duplicate count. â€œDeck
Metricsâ€ refers to the collection.

### Deck Version

An immutable snapshot of a Sewer Deckâ€™s card identities, quantities, sections, status, and notes.
Changes create a new Deck Version rather than rewriting history.

### Design Intent

A planned, human-authored interpretation of how a Character should be expressed through play. It may
describe themes, priorities, desired experiences, source Evidence, and accepted weaknesses. The
storage foundation exists; the v0.6.0 behavior is not yet implemented.

### Determinism

The property that identical versioned inputs and rules produce identical outputs.

### Effective Capability

The Capability result visible after deterministic derivation and the defined precedence of one
active documented Override. It preserves underlying Evidence rather than rewriting it.

### Engine Version

The stable identity and checksum of behaviorally meaningful engine content. Historical results cite
the exact Engine Version that produced them.

### Evidence

A specific attributable source fact, observation, citation, or explicit human rationale supporting
a derived result or decision.

### Explainability

The ability to trace a result through inputs, Evidence, rules, thresholds, Confidence, versions,
Provenance, and human decisions in inspectable language.

### Finding

An explainable statement produced by applying a named deterministic rule or threshold to one or more
Deck Metrics. A Finding is not a Recommendation.

### Knowledge

The organized body of facts, Evidence, interpretations, Relationships, decisions, and history, with
their classes kept distinct.

### Magic Fact

Objective Magic card information imported from Scryfall without project-specific interpretation,
such as name, mana cost, Oracle text, type, keyword, Card Face, Printing, or Standard legality.

### Oracle Card

The canonical rules identity shared by all Printings of a card. It is the Capability Engineâ€™s unit of
analysis.

### Override

An explicit, documented, auditable human decision that adds, removes, or adjusts an Effective
Capability for an edge case. It requires rationale and context and never erases derivation history.

### Playtest Session

A planned structured record of play involving one Deck Version, with observations kept distinct from
later interpretation. Expanded playtesting behavior is planned for v0.9.0.

### Printing

One physical or digital publication of an Oracle Card, identified separately by set, collector
number, art, rarity, release date, and Scryfall printing identity.

### Provenance

The traceable lineage of source data, rules, versions, checksums, relationships, and relevant
decisions behind a result.

### Puzzle Dojo

The Underground Pressâ€™s community puzzle and learning section. It may use crosswords, Sudoku,
ciphers, mazes, logic puzzles, word searches, and recurring hidden elements. It is not an engine.

### Recommendation

A planned contextual proposal to consider a card or change for a specific Design Intent and Deck
Version. It must expose evidence, constraints, and tradeoffs. Planned for v0.8.0.

### Relationship

A typed, evidence-backed connection between facts or subjects. Its name must not imply more than its
Evidence establishes.

### Rule Set

A stable, versioned collection of deterministic rules evaluated together. Its checksum covers
behaviorally meaningful content.

### Sewer Deck

A 60-card, Standard-legal Magic deck built to express a Character through one Design Intent while
remaining coherent and as strong as reasonably possible within that intent.

### SewerGraph

The projectâ€™s SQLite knowledge database. It stores durable facts, intent, decisions, overrides,
versions, Provenance, and audit history while keeping reproducible computed intelligence distinct.
See [Database](DATABASE.md).

### Store Facts. Compute Intelligence. Preserve Decisions.

The architectural rule: retain objective source material; derive reproducible analysis; and keep
human judgment, overrides, rationale, and history auditable.

### Surface Report

An Underground Press section reporting bounded news from the surface or translating a project
milestone for a general in-universe audience. It is presentation, not canonical analysis.

### The Underground Press

The in-universe community newspaper that informs, connects, celebrates, and preserves underground
community history. See [The Underground Press](UNDERGROUND_PRESS.md).

### TMNT Design Studio

The complete knowledge-driven system for researching, designing, analyzing, playtesting, explaining,
and preserving Standard-legal TMNT Character Sewer Decks and their community history.

## Encyclopedia-specific vocabulary

These terms remain useful inside TMNT Design Encyclopedia editorial work. They are not database
entities or engine outputs unless a future accepted decision explicitly says otherwise.

### Core Truth

An Encyclopedia editorial statement of a foundational Character insight.

### Design Echo

An Encyclopedia observation that a mechanic, image, or theme reinforces a larger design idea.

### Character Suite

An Encyclopedia presentation collecting editorial analysis about a Character. It is not the
Character entity, Design Intent, or Sewer Deck.

