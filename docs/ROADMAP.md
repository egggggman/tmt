# Roadmap

## Vision

TMNT Design Studio will deliver one fully explainable Character Sewer Deck whose lineage can be
followed from objective Magic Facts through Capabilities, Deck Metrics, Deck Analysis, Design Intent,
Alignment, Recommendations, Playtesting, iteration, and preserved decisions. The same foundation may support
future decks, research, education, and community publishing without becoming opaque.

## Guiding philosophy

This roadmap follows the [Project Constitution](PROJECT_CONSTITUTION.md) and
[Design Principles](DESIGN_PRINCIPLES.md): foundations before features, objective before subjective,
deterministic first, and community before ego. It is vision-oriented, not schedule-oriented.

## Milestone history

Completed status is based on `CHANGELOG.md`, tagged releases, and current implementationâ€”not the
aspirations of older roadmap drafts.

### v0.1.0 â€” Architecture foundation â€” Complete

Established project identity, Sewer Deck terminology, Standard-only Version 1 scope, domain
hierarchy, architectural boundaries, and initial database design.

### v0.2.0 â€” Executable foundation â€” Complete

Added the Python package, SQLite migration runner, CLI foundation, immutable Deck Versions,
foreign-key enforcement, tests, Ruff, and GitHub Actions.

### v0.3.0 â€” Scryfall import pipeline â€” Complete

Added transactional Magic Fact import, normalized Oracle Cards, Printings, Card Faces, Standard
legality, and durable source audit metadata.

### v0.4.0 â€” Capability Engine â€” Complete

Added the canonical Capability catalog, versioned deterministic rules, Evidence, Confidence,
Overrides, Effective Capability resolution, and derivation audit.

### v0.5.0 â€” Deck Analysis Engine â€” Complete

Added objective Deck Metrics and deterministic Findings for an immutable Deck Version, with strict
source Provenance and transactional current/run history.

## Confirmed future milestones

### v0.6.0 â€” Design Intent

Create a rigorous, versionable expression of one Character interpretation: source Evidence, themes,
priorities, desired experiences, accepted weaknesses, and authored rationale. Prove one bounded
reference intent before broad expansion.

The [Design Intent RFC](DESIGN_INTENT_RFC.md) is the Under Review architecture milestone for this
work. Its presence does not mark the v0.6.0 runtime or persistence implementation complete.

Immediately after RFC acceptance, build Leonardo Prototype 0.1 with the existing Capability and Deck
Analysis engines, then playtest it. Use that evidence to challenge the envelope before adding
Alignment, Recommendations, or generalized Character machinery.

### v0.7.0 â€” Alignment

Compute explainable evidence for how cards, Capabilities, Relationships, and Deck Versions support a
specific Design Intent. Keep objective inputs separate from interpretation.

### v0.8.0 â€” Recommendations

Produce contextual proposals from a Deck Version, Design Intent, Alignment, and objective deck needs.
Every Recommendation exposes constraints, Evidence, tradeoffs, and Confidence; none is a command.

### v0.9.0 â€” Playtesting and iteration

Record structured Playtest Sessions and observations, connect learning to immutable Deck Versions,
and use real play Evidence to challenge assumptions without rewriting history.

### v1.0.0 â€” First fully explainable Character Sewer Deck

The system can design, analyze, align, recommend, version, and explain one complete Standard-legal
Leonardo Sewer Deck from end to end.

That means one complete 60-card Deck has an inspectable path through Magic Facts, Capabilities, Deck
Metrics, Design Intent, Alignment, Recommendations, decisions, and Playtesting, with its development
story preserved for the community.

## Beyond v1

Aspirational possibilitiesâ€”not commitmentsâ€”include additional Characters and Design Intents, richer
playtest evidence, interactive explainability tools, Puzzle Dojo learning experiences, durable
Underground Press archives, visual inspection tools, and carefully bounded assistive AI that never
hides Evidence or replaces accountable judgment.

Additional Magic formats may be considered only after Standard-first experience demonstrates a real
need and the architecture can preserve explainability.

## Deliberately deferred and out of scope

- Opaque AI scoring or non-explainable automation.
- Autonomous deck construction presented as authority.
- Monetization or publishing scale at the expense of community trust.
- Unrelated franchises.
- Additional Magic formats until Standard is proven.
- Matchup guarantees and universal deck-quality grades.
- A graphical interface before underlying responsibilities and inspection paths are stable.
- Speculative features without evidence of a real contributor or user need.

## Success criteria

The roadmap is succeeding when a newcomer understands the vocabulary and boundaries; important
outputs trace to Evidence, rules, versions, and decisions; deterministic analysis reproduces;
interpretation remains visible and challengeable; each milestone has one clear responsibility; and
the resulting deck is legal, playable, recognizable, explainable, and joyful.

## Living document

Version numbers describe dependency order and a learning path, not delivery dates. This roadmap may
evolve through explicit review as evidence changes, while preserving completed history and the
constitutional mission.

