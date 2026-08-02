# Contributing

TMNT Design Studio welcomes careful technical, design, research, editorial, and community
contributions.

## Start here

Read, in order:

1. [Project Constitution](docs/PROJECT_CONSTITUTION.md)
2. [Design Principles](docs/DESIGN_PRINCIPLES.md)
3. [Canonical Glossary](docs/GLOSSARY.md)
4. [Architecture](docs/ARCHITECTURE.md)
5. The specification relevant to your change

Use canonical terminology and label planned concepts as planned. Do not collapse Magic Facts,
computed intelligence, human intent, decisions, or presentation.

## Proposing work

- State the problem, evidence, scope, boundaries, and validation plan.
- Prefer one clear responsibility per change.
- Cross-reference canonical documents rather than duplicating definitions.
- Preserve meaningful history and record durable architectural decisions.
- Explain how the change remains inspectable and reproducible.

## Validation

Run the checks relevant to the touched layer. Runtime changes normally require Ruff format/lint,
the full pytest suite, fresh database initialization, foreign-key verification, and GitHub Actions.
Documentation-only changes also require a diff-scope audit, terminology scan, and relative-link check.

Use the [Repository Health checklist](docs/REPOSITORY_HEALTH.md) after major milestones.

