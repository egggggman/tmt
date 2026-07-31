# Changelog

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

- Replaced the older “Casual Deck Project” wording with the Sewer Deck Project concept.
- Expanded the mission from documentation-only work into a knowledge-driven deck-design system.
- Clarified that recommendations and Deck Profiles are computed rather than canonical stored facts.
- Preserved older Encyclopedia terms as Encyclopedia-specific editorial vocabulary where appropriate.

### Repository cleanup

- Extracted release-package contents.
- Removed ZIP files from the active repository.
- Removed duplicate nested package directories.
- Promoted the current Foundation documents to the repository root.

### Not yet implemented

- Python package scaffold.
- Executable SQLite migrations.
- Scryfall source-data import.
- Capability-rule execution.
- Leonardo deck construction and playtesting.
