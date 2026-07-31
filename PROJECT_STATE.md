# Project State

Version: **v0.1.0 — Architecture and Database Foundation**

## Current status

- Repository online and structurally flattened.
- GitHub confirmed as the canonical project home.
- Product scope frozen to Standard-legal Sewer Decks for Version 1.
- Canonical hierarchy accepted: Character → Design Intent → Sewer Deck → Deck Version.
- Sewer Deck terminology accepted; these are not Commander decks.
- Design goal accepted: balance character fidelity with competitive Standard strength.
- Mechanics, Capabilities, and Themes separated into distinct concepts.
- Capability Engine approach accepted: rules-based derivation plus documented designer overrides.
- Context-aware recommendation model accepted.
- Python, SQLite, uv, migrations, tests, and CLI selected for implementation.
- Leonardo selected as the first reference implementation.
- Encyclopedia and Underground Press retained as components of the broader Studio ecosystem.

## Foundation work in progress

- Synchronize repository documents with the accepted architecture.
- Add the canonical architecture and database specifications.
- Add architectural decision records.
- Add the Python project scaffold.
- Implement executable database migrations.
- Validate a fresh database build.

## Next executable milestone

```bash
tmnt init
```

The command must create a valid SewerGraph database, apply all migrations exactly once, enable foreign keys, and verify the resulting schema.

## Next product milestone

Complete the Leonardo reference implementation:

- Character record
- First Design Intent
- Theme and capability priorities
- First complete Standard-legal Sewer Deck
- Context-aware recommendation support
- Initial playtest evidence
