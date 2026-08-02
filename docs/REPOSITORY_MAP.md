# Repository Map

## Purpose

This map helps contributors find the right source of truth before changing the repository. It
describes current directories and reserves sensible homes for future material without requiring
empty folders.

```text
tmt/
├── .github/workflows/       Continuous integration
├── docs/                    Governance, architecture, engine, world, and contributor guides
├── src/tmnt_design_studio/  Python package and ordered database migrations
├── tests/                   Automated tests and representative fixtures
│   └── fixtures/            Current home for test-only source-data fixtures
├── scripts/                 Reserved for maintained developer/operations utilities
├── assets/                  Reserved for repository-owned visual/editorial assets
├── examples/                Reserved for runnable or inspectable user examples
├── README.md                Front door and documentation navigation
├── CHANGELOG.md             Historical release record
├── pyproject.toml           Package metadata, dependencies, and tool configuration
└── uv.lock                  Reproducible dependency lock
```

Directories marked reserved do not yet need to exist. Create one only with its first maintained
artifact and document any narrower ownership rules at that time.

## `docs/`

Read here for the project’s source documents:

- governance and direction: Constitution, Design Principles, Glossary, and Roadmap;
- architecture and persistence: Architecture, Accepted Decisions, and Database;
- engine behavior: Capabilities and Deck Analysis;
- world and editorial work: World Guide and Underground Press Style Guide;
- contribution and maintenance: Contributor Journey, Repository Health, and this map.

Definitions shared across domains belong in the Glossary. Technical formulas remain in their engine
guide; prose elsewhere should link rather than repeat them.

## `src/`

`src/tmnt_design_studio/` is the runtime Python package. Import, Capability, Deck Analysis, database,
and CLI modules keep separate responsibilities. `src/tmnt_design_studio/migrations/` contains ordered,
checksum-verified SQL migrations. Released migrations are immutable; schema changes require a new
migration and are never part of a documentation-only PR.

## `tests/`

Tests mirror observable behavior and important architectural boundaries. Start here when learning how
an importer, engine, transaction, or CLI command is expected to behave. Tests should not become the
only documentation of a public rule.

## `fixtures/`

The current fixtures live at `tests/fixtures/` because they support automated tests. Use small,
representative fixtures for edge cases and neutral examples. A future top-level `fixtures/` directory
would be appropriate only for reusable data that serves more than tests; document provenance and
licensing before adding it.

## `scripts/`

Reserved for maintained utilities that support repeatable development, validation, import, release,
or repository-health work but do not belong in the installed runtime package. A script needs usage
documentation, safe defaults, and a clear owner; ad hoc local commands do not need permanent files.

## `assets/`

Reserved for project-owned images, diagrams, templates, and editorial media. Record origin, rights,
attribution, and intended use. Generated build output and third-party source material should not be
committed here by default.

## `examples/`

Reserved for runnable or inspectable user examples that would clutter tests or product documentation.
Examples must stay current, label sample data, and avoid implying fictional output is canonical fact.

## Where should I look?

| Question | Start here |
|---|---|
| Why does the project exist? | [Project Constitution](PROJECT_CONSTITUTION.md) |
| What does a term mean? | [Glossary](GLOSSARY.md) |
| How are decisions made? | [Design Principles](DESIGN_PRINCIPLES.md) and [Accepted Decisions](DECISIONS.md) |
| How does information move through the system? | [Architecture](ARCHITECTURE.md) |
| What is stored in SewerGraph? | [Database](DATABASE.md) and migrations under `src/` |
| How does an engine behave? | [Capabilities](CAPABILITIES.md) or [Deck Analysis](DECK_ANALYSIS.md), then tests |
| Where is the project heading? | [Roadmap](ROADMAP.md) |
| How does the surrounding world work? | [World Guide](WORLD_GUIDE.md) |
| How should an article be written? | [Underground Press Style Guide](UNDERGROUND_PRESS_STYLE_GUIDE.md) |
| How do I make a first contribution? | [Contributor Journey](CONTRIBUTOR_JOURNEY.md) |
| Is the repository healthy? | [Repository Health](REPOSITORY_HEALTH.md) |
