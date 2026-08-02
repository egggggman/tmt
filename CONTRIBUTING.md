# Contributing

TMNT Design Studio welcomes careful technical, design, research, editorial, and community
contributions. Community before ego: be respectful, credit sources and collaborators, welcome
questions, and critique ideas without diminishing people.

## Orient yourself

Read, in order:

1. [Project Constitution](docs/PROJECT_CONSTITUTION.md) — why the project exists.
2. [Design Principles](docs/DESIGN_PRINCIPLES.md) — how tradeoffs are resolved.
3. [Canonical Glossary](docs/GLOSSARY.md) — the vocabulary contributors must share.
4. [Architecture](docs/ARCHITECTURE.md) — layer responsibilities and invariants.
5. The specification relevant to the proposed change.

The [Database](docs/DATABASE.md), [Capabilities](docs/CAPABILITIES.md), and
[Deck Analysis](docs/DECK_ANALYSIS.md) documents own implementation semantics. The
[World Guide](docs/WORLD_GUIDE.md) owns in-universe continuity and publication policy. Use canonical
terminology and label planned concepts as planned.

## Architectural expectations

Keep imported facts, computed intelligence, human intent, preserved decisions, and presentation
distinct. One layer may consume an earlier layer but may not silently perform another layer's
responsibility. New computed behavior must identify its inputs, rules or thresholds, version,
Provenance, failure behavior, and inspection path.

Evidence and explainability are requirements, not optional polish. State what supports a claim, how a
result can be reproduced, what uncertainty remains, and which decision is human-authored.

## Proposing work

Every proposal should state the problem, Evidence, scope, boundaries, affected canonical documents,
and validation plan. Prefer one clear responsibility per change and cross-reference canonical
definitions rather than copying them.

- **New Capability:** propose a narrow identifier and definition, objective Evidence sources,
  Confidence semantics, positive examples, negative controls, limitations, and deterministic rules.
- **New Deck Metric:** define inputs, formula, units, multiface and edge-case treatment, Provenance,
  and deterministic fixtures.
- **New Finding:** identify the source metrics, named threshold or rule, severity meaning, negative
  controls, and human-readable explanation. A Finding must not become a Recommendation.
- **New world element:** explain its community purpose, source-material boundaries, continuity
  impact, consent needs, and canonical home under the World Guide.
- **Architectural change:** use an ADR or RFC for a hard-to-reverse boundary, data-model, engine, or
  terminology decision. Record alternatives, consequences, compatibility, and migration strategy
  before implementation.

## Documentation expectations

Update the canonical document that owns a concept and link to it elsewhere. Keep current behavior,
planned behavior, and historical records distinguishable. Check headings, capitalization, relative
links, examples, CLI output, migration lists, terminology, and release status. Do not silently erase
useful history.

## Testing and validation

Run checks appropriate to the touched layer:

- Ruff format and lint for Python changes;
- the full pytest suite for runtime behavior;
- fresh database initialization, migration count, and foreign-key checks for persistence changes;
- deterministic, idempotence, rollback, negative-control, and Provenance tests for engine changes;
- CLI help and documented command walkthroughs for interface changes;
- Markdown formatting, link, terminology, duplicate-heading, and documentation-map checks for docs;
- the [Repository Health](docs/REPOSITORY_HEALTH.md) audit after major milestones.

Report skipped, unavailable, or environment-blocked checks honestly. Documentation-only work must
confirm that runtime, schema, migrations, tests, workflows, and license are unchanged.

## Pull requests and review

Keep pull requests focused and explain why the change belongs in its layer. Summarize decisions,
files, terminology, validation, limitations, and follow-up work. Reviewers should be able to trace
every behavioral claim to Evidence and every durable judgment to an ADR, RFC, or canonical document.

When several technically valid solutions exist, follow the Design Principles: favor simplicity,
explainability, determinism, preserved history, and community benefit.
