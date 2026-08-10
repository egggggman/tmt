# Project Constitution

## Purpose

This Constitution explains why TMNT Design Studio exists and how contributors protect its identity
as it grows. It governs judgment and direction. Implementation boundaries live in
[Architecture](ARCHITECTURE.md), durable technical choices in [Decisions](DECISIONS.md), and shared
language in the [Glossary](GLOSSARY.md).

## Mission

TMNT Design Studio explores how a 60-card, Standard-legal Magic deck can express a specific TMNT
Character through a clear Design Intent. It combines source research, reproducible software,
explainable design, and community storytelling so the path to a Sewer Deck matters as much as the
finished list.

Another person should be able to trace, question, reproduce, and improve the work without guessing
at hidden reasoning.

## Core values

### Explainability

Results expose the inputs, evidence, rules, thresholds, versions, and human decisions that produced
them. “The system says so” is never sufficient. A feature that cannot explain its conclusion is not
ready to influence design.

### Evidence before opinion

Source facts and observations come before judgment. Interpretation is welcome when identified as
interpretation and supported with rationale. New evidence may change a conclusion, but never erases
the context in which an earlier decision was made.

### Determinism

Identical versioned inputs and rules produce identical computed results. Where judgment cannot be
deterministic, preserve it as an explicit human decision instead of disguising it as computation.

### Respect for source material

Treat both TMNT and Magic as works worth understanding on their own terms. Do not bend objective
rules facts to force a theme, flatten a Character into a slogan, or present fan interpretation as
canon. Research, attribution, and context are part of design quality.

### Community first

The project serves players, readers, contributors, artists, researchers, and fans. Welcome
good-faith questions, credit contributions, and make expertise inviting rather than exclusionary.
Community benefit matters more than status, reach, or personal ownership.

## Engineering philosophy

> Store facts. Compute intelligence. Preserve decisions.

- **Store facts.** Keep authoritative imports and direct observations separate from interpretation.
- **Compute intelligence.** Derive reproducible results from named inputs and versioned rules.
- **Preserve decisions.** Retain overrides, rationale, authorship, supersession, and history.

Every proposed data field should be classified before it is stored. Every computed output should be
reconstructable. Every human exception should be visible and auditable.

## Architectural philosophy

One responsibility belongs to each layer. Importers collect objective facts. The Capability Engine
describes what cards do. Deck Analysis computes objective Deck Metrics and deterministic Findings.
Design Intent and future Alignment interpret meaning. Recommendations may propose choices only after
their inputs exist and remain explainable. Presentation communicates the work without becoming a
hidden analytical input.

Layers do not bypass one another for convenience. See [Architecture](ARCHITECTURE.md) for the
canonical boundaries and implementation status.

## World philosophy

Community comes first. The living underground world makes the project welcoming, memorable, and
human without changing analytical results. The Underground Press exists to inform, connect,
celebrate, and preserve community history. The world layer reports and interprets; it does not
manufacture evidence.

The [World Guide](WORLD_GUIDE.md) governs in-universe continuity. The
[Underground Press guide](UNDERGROUND_PRESS.md) governs publication.

## Project scope

### Included

- Objective Magic facts with source provenance.
- Explainable, versioned Capability and Deck Analysis systems.
- Character research, Design Intent, Alignment, and contextual recommendations.
- Immutable Deck Versions, design decisions, overrides, and playtest history.
- Educational and editorial work that helps the community understand and participate.
- A Standard-first path to one complete, explainable Character Sewer Deck.

### Not included

- Claims of official affiliation, endorsement, or canon authority.
- Opaque scoring, untraceable automation, or hidden AI judgment.
- Automated replacement of human creative responsibility.
- Competitive certainty, matchup guarantees, or a universal “best deck.”
- Monetization or growth that weakens community trust.
- Unrelated franchises or additional Magic formats before Standard is proven.
- Features added only because they are technically possible.

## Fan project statement

TMNT Design Studio is an independent, non-commercial fan project. Teenage Mutant Ninja Turtles and
Magic: The Gathering belong to their respective rights holders. The project does not claim
affiliation with, sponsorship by, or endorsement from those rights holders. Contributors must
respect applicable rights, licenses, attribution requirements, and source terms. This statement
supplements; it does not replace or change the repository license.

## Decision framework

For a material choice, ask in order:

1. Is it consistent with the mission and respectful of source material?
2. Does it help the community understand, create, or participate?
3. Are fact, analysis, interpretation, recommendation, and presentation kept distinct?
4. Is the evidence visible and the result explainable?
5. Can behavior be deterministic, or must a human decision be preserved?
6. Does the proposal have one clear responsibility and the smallest useful scope?
7. Does it preserve history and leave an honest path to grow?
8. Is it still joyful?

Durable choices belong in [Decisions](DECISIONS.md) or an architecture decision record. This
Constitution should change rarely and only through explicit review.

## Long-term vision

The project aims to produce one fully explainable Character Sewer Deck whose lineage can be followed
from source facts through Capabilities, Deck Metrics, Design Intent, Alignment, recommendations,
playtesting, iteration, and preserved decisions. Around that foundation, it may grow into a useful
body of research, educational tools, and community publishing without sacrificing clarity or trust.

The [Roadmap](ROADMAP.md) describes direction, not dates.

## Rule of Joy

Rigor serves curiosity, connection, and delight. When two responsible paths are otherwise equal,
choose the one that is more welcoming, expressive, and fun to explore. If complexity stops serving
people, pause, simplify, and remember why the project exists.

