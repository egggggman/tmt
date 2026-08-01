# Changelog

## v0.2.0 â€” Executable Foundation

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
- Character â†’ Design Intent â†’ Sewer Deck â†’ Deck Version terminology is preserved.
- Computed Deck Profiles and recommendations are not stored as canonical truth.

## v0.1.0 â€” Architecture and Database Foundation

### Added

- Canonical TMNT Design Studio project identity.
- Sewer Deck terminology and Standard-only Version 1 scope.
- Character â†’ Design Intent â†’ Sewer Deck â†’ Deck Version hierarchy.
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
