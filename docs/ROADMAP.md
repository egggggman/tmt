# Roadmap

## Vision

TMNT Design Studio will make one complete, explainable Character deck whose lineage can be followed
from objective Magic facts to Capability evidence, Deck Metrics, Design Intent, Alignment,
recommendations, playtesting, and preserved design decisions. The same foundation should support
future decks, research, educational experiences, and community publishing without becoming opaque.

Related governance: [Project Constitution](PROJECT_CONSTITUTION.md),
[Design Principles](DESIGN_PRINCIPLES.md), and [Glossary](GLOSSARY.md).

## Guiding philosophy

The roadmap follows the [Project Constitution](PROJECT_CONSTITUTION.md) and
[Design Principles](DESIGN_PRINCIPLES.md): foundations before features, objective before subjective,
deterministic first, and community before ego. Milestones add one bounded responsibility at a time.

## Milestone history

### v0.1.0 — Architecture and Database Foundation

Established the project identity, Sewer Deck terminology, Standard-only Version 1 scope, domain
hierarchy, architectural boundaries, and initial database design.

### v0.2.0 — Executable Foundation

Introduced the Python package, SQLite migration runner, CLI foundation, immutable Deck Versions,
foreign-key enforcement, tests, Ruff, and GitHub Actions.

### v0.3.0 — Scryfall Import Pipeline

Added transactional import of objective Oracle cards, printings, faces, legality, keywords, types,
subtypes, and durable source audit metadata.

### v0.4.0 — Capability Engine

Added the canonical Capability catalog, versioned deterministic rules, per-match evidence,
confidence semantics, explicit overrides, effective resolution, and derivation audit.

### v0.5.0 — Deck Analysis Engine

Established the objective Deck Metrics and explainable deterministic Finding layer over an immutable
Deck Version, with strict source provenance and transactional history.

## Future milestones

### v0.6.0 — Design Intent

Create a rigorous, versionable way to express one interpretation of a Character: themes, priorities,
desired experiences, accepted weaknesses, source evidence, and authored rationale. Prove the model
with one bounded reference intent before broad expansion.

### v0.7.0 — Alignment

Compute explainable evidence for how cards, Capabilities, relationships, and Deck Versions support a
specific Design Intent. Keep objective inputs separate from subjective interpretation, expose every
factor, and avoid collapsing alignment into universal card quality.

### v0.8.0 — Recommendations

Produce contextual card and change proposals from a specific Deck Version, Design Intent, Alignment,
and objective deck needs. Every recommendation must expose constraints, evidence, tradeoffs, and
confidence; none is an automatic command.

### v0.9.0 — Playtesting

Record structured sessions and observations, connect findings to immutable Deck Versions, and use
real play evidence to challenge prior assumptions. Preserve both measurements and human observations
without rewriting history.

### v1.0 — Explainable Character Deck

Deliver one complete 60-card, Standard-legal Character deck with an inspectable path through source
facts, Capabilities, Deck Metrics, Design Intent, Alignment, recommendations, decisions, and playtest
evidence. Publish the story of its development for the community.

## Beyond v1

Possible future directions include:

- additional Characters and multiple Design Intents per Character;
- richer playtest and metagame evidence without matchup guarantees;
- the Underground Press as a durable community publication and archive;
- Puzzle Dojo educational exercises and interactive explainability tools;
- Surface Reports that make bounded project work accessible to broader audiences;
- visual inspection tools and contributor workflows;
- additional Magic formats only after Standard-first experience demonstrates a need;
- carefully bounded assistive AI that never hides evidence or replaces accountable judgment.

These are possibilities, not commitments.

## Deliberately deferred

- Supporting every Character before one end-to-end reference deck works.
- Supporting formats beyond Standard in Version 1.
- Opaque scoring, autonomous deck construction, or unexplained recommendations.
- Matchup prediction, competitive guarantees, and universal deck-health grades.
- A graphical interface before the underlying responsibilities and inspection paths are stable.
- Publishing scale, monetization, or audience growth at the expense of community trust.
- Speculative features without evidence of a real contributor or user need.

## Success criteria

The roadmap is succeeding when:

- a newcomer can understand the project’s vocabulary and boundaries;
- every important output can be traced to evidence, rules, versions, and decisions;
- identical inputs reproduce identical deterministic analysis;
- subjective interpretation is visible and challengeable rather than disguised as fact;
- each milestone has a clear responsibility and leaves prior history intact;
- contributors can participate without hidden knowledge or status gates;
- the resulting deck is legal, playable, recognizable, explainable, and enjoyable;
- the project creates useful community knowledge in addition to software.

## Living document

This roadmap is vision-oriented, not schedule-oriented. Version numbers describe a dependency order
and learning path, not delivery dates. It should evolve through explicit review as evidence changes,
while preserving milestone history and the constitutional mission.
