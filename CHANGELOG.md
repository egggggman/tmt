# Changelog

## Prototype 0.2 design cycle

- Preserved all Prototype 0.1 decklists and created surgical Donatello and Krang Prototype 0.2
  candidates from Calibration 0.1 evidence.
- Froze roster 0.2 with the other eight decks unchanged and ran the exact balanced 20-game smoke
  protocol.
- Recorded a recalibration block: intended engine reliability moved, but aggregate strength and
  matchup polarity remain unresolved.

## Unreleased — Repository governance

### Documentation

- Consolidated canonical project philosophy, design principles, terminology, architecture, roadmap,
  onboarding, world governance, and repository-health review practices.
- Defined the complete reasoning pipeline and kept objective facts, computed intelligence, authored
  intent, recommendations, playtest observations, and community presentation in separate layers.
- Canonized The Underground Press mission, tagline, publication taxonomy, milestone policy, and
  relationship to the living world.
- Prepared governance and Design Intent RFC orientation without implementing v0.6.0 behavior.


## v0.5.0 — Deck Analysis Engine

### Added

- Deterministic Deck Metrics for composition, mana value, color requirements and sources, all 20
  effective Capabilities, densities, ratios, duplicates, and objective redundancy.
- Explainable findings with severity, metric, named rule, exact threshold, and minimal fact
  relationships.
- Transactional current results and durable successful/failed run history linked to Deck Version,
  Scryfall import, Capability run, and versioned checksums.
- Strict deck-size, Standard-legality, printing, copy-limit, and current-provenance validation plus
  an explicitly warned diagnostic-size mode.
- `tmnt deck analyze`, `tmnt deck inspect`, and `tmnt deck status` commands.

### Boundaries

- No TMNT or Design Intent judgment, recommendation, tuning, matchup prediction, deck-health grade,
  or AI heuristic is present.
- Mana-source reporting separates land production from nonland fixing/ramp and does not judge mana
  base quality.

## v0.4.0 — Capability Engine

### Added

- Canonical 20-item Capability catalog with stable identifiers, narrow definitions, categories, and status.
- Versioned, checksummed rules over Oracle text, keywords, and face-specific facts.
- Transactional derivation linked to the exact Scryfall import and rule set, with per-match evidence.
- Auditable add/remove/adjust overrides and effective Capability resolution.
- Derive, inspect, and status CLI commands plus offline edge-case and rollback coverage.
- Capability catalog/rule guide with evidence sources, examples, negative controls, and limitations.
- Release-review controls for opponent-only effects, owner-targeted removal, reminder text,
  temporary mana, multiface evidence duplication, and override field integrity.

### Boundaries

- Confidence is evidence strength only; rule matches combine by maximum and overrides remain distinct.
- No TMNT judgment, theme scoring, Deck Profile, recommendation, ranking, or deck analysis is present.

## v0.3.0 — Scryfall Import Pipeline

### Added

- Scryfall bulk-data download and deterministic local JSON, gzip, or ZIP fixture ingestion.
- Transactional Oracle cards, printings, ordered faces, Standard legality, keywords, card types,
  and subtypes normalization.
- Import audit metadata with SHA-256 checksum, source details, timestamps, counts, warnings,
  errors, and explicit outcomes.
- `tmnt import scryfall` and `tmnt database status` commands with human-readable summaries.
- Fixture integration coverage for fresh, repeated, changed, malformed, and injected-failure
  imports.
- Durable audit records for metadata and download failures.
- Strict ZIP validation for one safe, root-level JSON member.
- Compatibility with Scryfall's current gzipped JSON Lines bulk-data descriptor and payload.

### Validated

- Repeated imports preserve stable fact and natural-relationship counts.
- Failed fact transactions retain a failed audit record without partial fact mutations.
- Duplicate identities, expected printing counts, Standard legality, and foreign keys are checked.
- Only objective Magic facts are imported; computed intelligence remains outside canonical storage.

## v0.2.0 — Executable Foundation

### Added

- uv-managed Python 3.12 package for TMNT Design Studio.
- Typer CLI with repeatable `tmnt init` database initialization.
- SQLite connection layer with foreign keys enabled and verified.
- Transactional, deterministic, checksum-verified migration runner.
- Nine numbered SewerGraph migrations matching `docs/DATABASE.md`.
- Schema migration history, Standard-only constraints, and immutable Deck Version safeguards.
- Ruff, pytest, and GitHub Actions validation.

### Validated

- Fresh databases apply every migration exactly once.
- Repeated initialization is idempotent.
- Failed migrations roll back without being recorded.
- Invalid foreign keys, enumerations, quantities, and duplicate natural relationships are rejected.
- Character → Design Intent → Sewer Deck → Deck Version terminology is preserved.
- Computed Deck Profiles and recommendations are not stored as canonical truth.

## v0.1.0 — Architecture and Database Foundation

### Added

- Canonical TMNT Design Studio project identity.
- Sewer Deck terminology and Standard-only Version 1 scope.
- Character → Design Intent → Sewer Deck → Deck Version hierarchy.
- Separation of Magic facts, mechanics, Capabilities, and TMNT Themes.
- Hybrid Capability Engine design with documented designer overrides.
- Context-aware recommendation architecture.
- Canonical glossary, architecture specification, database specification, decisions summary, roadmap, and project state.
- Leonardo reference implementation milestone.
- Backup strategy and GitHub-as-canonical-source decision.

### Changed

- Replaced legacy deck-project wording with the Sewer Deck Project concept.
- Expanded the mission from documentation-only work into a knowledge-driven deck-design system.
- Clarified that recommendations and Deck Profiles are computed rather than canonical stored facts.
- Preserved older Encyclopedia terms as Encyclopedia-specific editorial vocabulary where appropriate.

### Repository cleanup

- Extracted release-package contents.
- Removed ZIP files from the active repository.
- Removed duplicate nested package directories.
- Promoted the current Foundation documents to the repository root.

### Not yet implemented

- Scryfall source-data import.
- Capability-rule execution.
- Leonardo deck construction and playtesting.
