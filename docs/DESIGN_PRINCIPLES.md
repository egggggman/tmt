# Design Principles

## Purpose

These principles guide how contributors make product, engineering, editorial, and deck-design
decisions. They translate the values in the [Project Constitution](PROJECT_CONSTITUTION.md) into
habits of judgment without prescribing a specific implementation.

Related governance: [Project Constitution](PROJECT_CONSTITUTION.md), [Glossary](GLOSSARY.md), and
[Roadmap](ROADMAP.md).

## Simplicity over cleverness

Prefer the smallest idea that can be understood, tested, and maintained. Cleverness is useful only
when it makes the work clearer; novelty alone is not a benefit.

## Explainability over automation

Automation should increase a person’s understanding and agency. A slower answer with visible
evidence is better than a fast answer whose reasoning cannot be inspected. Keep a human-authorable
path for exceptions and interpretation.

## Foundations before features

Define vocabulary, boundaries, provenance, and success criteria before building dependent behavior.
Each milestone should leave a stable foundation for the next rather than borrowing correctness from
future work.

## Small responsibilities

Give each document, component, rule, and layer one clear job. Compose small responsibilities instead
of creating one system that imports facts, interprets meaning, ranks choices, and presents conclusions
at once.

## Objective before subjective

Establish source facts and reproducible analysis before applying Character interpretation or design
judgment. Subjective work is legitimate and necessary; it becomes trustworthy when its inputs and
rationale remain visible.

## Deterministic first

Begin with explicit rules and reproducible results. Introduce probabilistic or generative assistance
only when it has a defined responsibility, visible evidence, deterministic guardrails where possible,
and no pretense of authority.

## Preserve history

Do not overwrite a past decision merely because the current answer differs. Keep versions,
provenance, rationale, supersession, and playtest context so learning remains visible.

## World supports software

Names, stories, publications, and recurring formats should make the system inviting and memorable.
They should clarify the project’s purpose, not conceal architectural boundaries or turn presentation
into canonical data.

## Reward curiosity

Design inspection paths that let a person ask “why?”, follow evidence, compare versions, and discover
more than the final answer. Questions and well-supported disagreement are contributions.

## Leave room to grow

Keep initial definitions narrow and interfaces composable. Avoid speculative machinery, but do not
make today’s implementation the permanent limit of tomorrow’s project. Expand after evidence shows a
real need.

## Community before ego

Credit sources and contributors. Prefer shared understanding over personal ownership, welcome
correction, document context for newcomers, and judge proposals by their contribution to the mission.

## Rule of Joy

Rigor and delight are partners. Prefer work that is responsible, understandable, and enjoyable to
make and share. If complexity stops serving curiosity or community, simplify it.

## Applying the principles

Principles can pull in different directions. Use the Constitution’s decision framework, state the
tradeoff, and preserve durable choices in [Decisions](DECISIONS.md). Technical boundaries belong in
[Architecture](ARCHITECTURE.md); canonical terms belong in the [Glossary](GLOSSARY.md).
