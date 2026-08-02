# Glossary

## Purpose

This is the canonical vocabulary for TMNT Design Studio. Definitions here state what a term means
across the project; linked specifications provide implementation detail.

Related governance: [Project Constitution](PROJECT_CONSTITUTION.md),
[Design Principles](DESIGN_PRINCIPLES.md), and [Roadmap](ROADMAP.md).

### Alignment

An explainable assessment of how evidence from a card, relationship, or Deck Version supports a
specific Design Intent. Alignment is interpretation, not an objective card fact or universal quality
score. It is planned for v0.7.0.

### Audit

A durable record sufficient to reconstruct what happened, when, with which inputs, rules, outcome,
and error where applicable. Audit history is preserved even when current computed results are safely
replaced.

### Capability

A narrow, canonical description of what a Magic card accomplishes in gameplay. Capabilities are
derived at the Oracle-card level from explicit rules and evidence. The catalog lives in
[Capabilities](CAPABILITIES.md).

### Community First

The commitment to prefer shared understanding, welcome, credit, participation, and community benefit
over status, control, or growth for its own sake.

### Confidence

A bounded statement of evidence strength for a specific derived result. Confidence is not card
quality, Character fit, recommendation strength, or certainty about future play. Engine-specific
semantics belong in that engine’s documentation.

### Deck Metrics

Objective, reproducible measurements of one immutable Deck Version, such as counts, mana-value
distribution, color requirements, Capability totals, densities, and ratios. Metrics do not say
whether the deck is good, authentic, or recommended.

### Deck Version

An immutable snapshot of a Sewer Deck’s card identities, quantities, section assignments, status,
and notes at a point in its history. New changes produce a new Deck Version rather than rewriting an
old one.

### Design Intent

A human-authored interpretation of how a Character should be expressed through play. It may describe
themes, priorities, desired experiences, and accepted weaknesses. One Character may have multiple
valid Design Intents.

### Determinism

The property that identical versioned inputs and rules produce identical outputs. Determinism enables
reproduction, comparison, testing, and meaningful audit.

### Engine Version

The stable identity of a particular engine behavior. A behavior change requires a new identity or
checksum so historical results remain reproducible.

### Evidence

A specific source fact, observation, citation, or explicit human rationale supporting a derived
result or decision. Evidence should be attributable and inspectable.

### Explainability

The ability to trace a result through its inputs, evidence, rules, thresholds, confidence, versions,
and human decisions in language a person can inspect.

### Fact

Objective information imported from an authoritative source or directly observed and recorded
without project-specific interpretation. Examples include Oracle text, Standard legality, card
quantity, and a recorded playtest result.

### Finding

An explainable statement produced by applying a named deterministic rule or threshold to one or more
Deck Metrics. A Finding identifies its severity, source metric, and triggering condition; it is not a
recommendation.

### Knowledge

The project’s organized body of facts, evidence, interpretations, relationships, decisions, and
history, with their classes kept distinct so each can be evaluated appropriately.

### Override

An explicit, documented, auditable human decision that changes an effective derived result for an
edge case. An Override supplies rationale and evidence, follows defined precedence, and never erases
the underlying derivation.

### Provenance

The traceable identity and lineage of a result’s source data, rules, versions, checksums, and relevant
decisions.

### Puzzle Dojo

A future educational space or publishing format for guided puzzles, rules questions, deck-design
exercises, and explainable problem solving. It is a community-learning concept, not a current engine.

### Recommendation

A contextual, explainable proposal to consider a card or change for a specific Design Intent and Deck
Version. Recommendations are planned for v0.8.0; they are not canonical facts or commands.

### Relationship

A typed, evidence-backed connection between two facts or subjects. A Relationship may record
co-occurrence, support, conflict, replacement, upgrade, or combo context, but its type must not imply
more than its evidence establishes.

### Rule Set

A stable, versioned collection of deterministic rules evaluated together. Its checksum covers
behaviorally meaningful content so a result can identify the exact rules that produced it.

### SewerGraph

The project’s SQLite knowledge database. It stores durable facts, intent, decisions, overrides,
versions, provenance, and audit history while keeping reproducible computed intelligence distinct.
See [Database](DATABASE.md).

### Store Facts. Compute Intelligence. Preserve Decisions.

The project’s architectural rule: retain objective source material; derive reproducible analysis;
and keep human judgment, overrides, rationale, and history auditable. See the
[Project Constitution](PROJECT_CONSTITUTION.md).

### Surface Report

A future Underground Press reporting format that translates a bounded piece of project work for a
general audience while linking back to evidence and deeper technical or design material. It is a
presentation concept, not canonical analysis.

### Underground Press

The project’s community publishing layer. It exists to inform, connect, celebrate, and preserve
community history through transparent editorial work such as design journals, card spotlights,
interviews, and reports.
