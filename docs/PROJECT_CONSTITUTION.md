# Project Constitution

## Purpose

This Constitution explains why TMNT Design Studio exists and how contributors should protect its
identity as it grows. It governs direction and judgment; implementation details remain in
[Architecture](ARCHITECTURE.md), [Database](DATABASE.md), and accepted
[Decisions](DECISIONS.md).

Related governance: [Design Principles](DESIGN_PRINCIPLES.md), [Glossary](GLOSSARY.md), and
[Roadmap](ROADMAP.md).

## Mission

TMNT Design Studio exists to explore how a 60-card, Standard-legal Magic deck can express a specific
TMNT Character through a clear Design Intent. It combines careful source research, reproducible
software, explainable design work, and community storytelling so that the path to a deck matters as
much as the finished list.

The project should help people understand why a card, capability, relationship, or design decision is
present. It should preserve enough evidence and history for another person to question, reproduce,
or improve the work without guessing at hidden reasoning.

## Core values

### Explainability

A result is useful only when a person can understand where it came from. Engines expose rules,
inputs, evidence, confidence, and provenance. Editorial work distinguishes sourced fact from
interpretation. “The system says so” is not an explanation.

### Evidence before opinion

Facts and citations come before judgment. Opinions remain welcome, but they are identified as
interpretation and supported with rationale. When evidence changes, conclusions may change without
erasing the earlier decision or its context.

### Determinism

The same versioned inputs and rules should produce the same computed result. Determinism makes work
reproducible, testable, and open to meaningful disagreement. Where judgment cannot be deterministic,
the project records the human decision explicitly.

### Respect for source material

The project treats both Magic and TMNT as bodies of work worth understanding on their own terms. It
does not bend objective rules facts to force a theme, flatten a Character into a slogan, or present
fan interpretation as canon. Research, attribution, and context are part of design quality.

### Community first

The project is made for people: players, readers, contributors, artists, researchers, and fans.
Choices should invite learning and participation, credit contributions, welcome good-faith questions,
and avoid turning expertise into a gate. Community benefit matters more than personal status.

## Engineering philosophy

> Store facts. Compute intelligence. Preserve decisions.

- **Store facts.** Keep imported or directly observed information separate from interpretation.
- **Compute intelligence.** Derive repeatable analysis from named inputs and versioned rules.
- **Preserve decisions.** Retain human judgment, overrides, rationale, and history instead of
  rewriting the past to resemble the present.

This rule is expanded in [Architecture](ARCHITECTURE.md) and defined term by term in the
[Glossary](GLOSSARY.md).

## Architectural philosophy

One responsibility belongs to each layer. Importers collect objective source facts. Capability rules
describe what cards do. Deck analysis describes measurable deck properties. Design Intent and future
alignment layers interpret meaning. Recommendation systems may propose choices only after their
inputs exist and remain explainable. Presentation layers communicate the work without becoming its
hidden source of truth.

Boundaries are a design feature. A convenient shortcut is not worth collapsing fact, analysis,
interpretation, and recommendation into an answer nobody can audit.

## World philosophy

Community comes first. The surrounding world—language, publishing, stories, recurring formats, and
shared rituals—exists to make the software more human and the design work easier to enter. It must
support the project rather than obscure it.

The **Underground Press** exists to inform, connect, celebrate, and preserve community history. Its
work may include design journals, card spotlights, interviews, field reports, and archival pieces. It
does not convert promotion into evidence or erase the distinction between reporting and analysis.

## Project scope

### Included

- Objective Magic card facts and source provenance.
- Explainable, versioned Capability and deck-analysis systems.
- Character research, Design Intent, alignment, and eventually contextual recommendations.
- Immutable Deck Versions, design decisions, overrides, and playtest history.
- Educational and editorial work that helps the community understand and participate.
- A Standard-first path to one complete, explainable Character deck.

### Not included

- Claims of official affiliation, endorsement, or canon authority.
- Hidden scoring, untraceable automation, or opaque AI judgment.
- Automated replacement of human creative responsibility.
- Competitive certainty, matchup guarantees, or a universal definition of the “best” deck.
- Extraction, harassment, gatekeeping, or growth pursued at the community’s expense.
- Features added only because they are technically possible.

## Fan project statement

TMNT Design Studio is an independent fan project. Teenage Mutant Ninja Turtles and
Magic: The Gathering belong to their respective rights holders. The project does not claim
affiliation with, sponsorship by, or endorsement from those rights holders. Contributors must respect
applicable rights, licenses, attribution requirements, and source terms. This statement supplements;
it does not replace the repository license.

## Decision framework

When a material choice is unclear, ask in order:

1. Is it consistent with the mission and respectful of source material?
2. Does it help the community understand, create, or participate?
3. Are facts, analysis, interpretation, and recommendation kept distinct?
4. Is the evidence visible and the result explainable?
5. Can the behavior be deterministic, or must a human decision be preserved?
6. Does the proposal have one clear responsibility and the smallest useful scope?
7. Does it leave an honest path for future growth?
8. Is it still joyful?

Material, durable choices belong in [Decisions](DECISIONS.md) or a future architecture decision
record. The Constitution should change rarely and only through explicit community review.

## Long-term vision

The project aims to produce an explainable Character deck whose full lineage can be followed from
source facts through Capabilities, Deck Metrics, Design Intent, Alignment, recommendations,
playtesting, and preserved decisions. Around that foundation, it can grow into a useful body of
research, educational tools, and community publishing without sacrificing clarity or trust.

The [Roadmap](ROADMAP.md) describes direction, not a promise of dates.

## Rule of Joy

The work should create curiosity, connection, and delight. Rigor serves the experience; it does not
exist to make participation joyless. When two responsible paths are otherwise equal, choose the one
that is more welcoming, more expressive, and more fun to explore. If the project stops being joyful,
pause, simplify, and remember why it exists.
