# Design Principles

## Purpose

These principles translate the [Project Constitution](PROJECT_CONSTITUTION.md) into practical habits
for product, engineering, editorial, world-building, and deck-design decisions. They guide judgment;
they do not prescribe an implementation.

## Simplicity over cleverness

Prefer the smallest idea that can be understood, tested, and maintained. Novelty is valuable only
when it makes the work clearer.

**Apply it:** choose one explicit rule with a named threshold over a compact heuristic that hides
several judgments.

## Explainability over automation

Automation should increase understanding and agency. A slower result with inspectable reasoning is
better than a fast result whose logic cannot be followed.

**Apply it:** show evidence and provenance beside a derived Capability instead of returning only a
score.

## Foundations before features

Define vocabulary, boundaries, provenance, and success criteria before dependent behavior.

**Apply it:** settle Design Intent semantics and versioning before building Alignment against it.

## Small responsibilities

Give each document, component, rule, and layer one clear job. Compose bounded responsibilities.

**Apply it:** keep Scryfall import, Capability derivation, Deck Analysis, and recommendation logic in
separate layers even if one command coordinates them.

## Objective before subjective

Establish source facts and reproducible analysis before applying Character interpretation. Human
judgment is necessary; it becomes trustworthy when its inputs and rationale remain visible.

**Apply it:** compute color sources and Capability density before deciding whether they support a
Design Intent.

## Deterministic first

Begin with explicit rules and reproducible results. Probabilistic assistance needs a bounded job,
visible evidence, and deterministic guardrails; it never receives unearned authority.

**Apply it:** use a versioned Rule Set for Findings before considering assistive narrative summaries.

## Preserve history

Do not overwrite a past decision because the current answer differs. Keep versions, provenance,
rationale, supersession, and playtest context.

**Apply it:** create a new Deck Version and link the reason rather than editing an old snapshot.

## World supports software

Stories, publications, names, and rituals should make the system inviting without concealing its
boundaries or becoming analytical truth.

**Apply it:** let an Underground Press story explain a milestone, but never feed its narrative claims
into Alignment or recommendations.

## Reward curiosity

Let people ask â€œwhy?â€, follow evidence, compare versions, and discover more than a final answer.

**Apply it:** connect a Finding to its metric, formula, threshold, cards, and engine version.

## Leave room to grow

Keep initial definitions narrow and interfaces composable. Avoid speculative machinery while
refusing to treat todayâ€™s implementation as tomorrowâ€™s permanent limit.

**Apply it:** prove Standard end to end before generalizing format behavior.

## Community before ego

Credit sources and contributors, welcome correction, document context for newcomers, and judge ideas
by their contribution to the mission.

**Apply it:** preserve a contributorâ€™s rationale and discuss evidence rather than defending ownership
of an approach.

## Rule of Joy

Rigor and delight are partners. Responsible work should also be enjoyable to make, inspect, and
share.

**Apply it:** if a process adds ceremony without clarity, simplify it; if two sound presentations are
equal, choose the one that invites exploration.

## Resolving tension

Principles may pull in different directions. Use the Constitutionâ€™s decision framework, state the
tradeoff, and preserve durable choices in [Decisions](DECISIONS.md). Technical boundaries belong in
[Architecture](ARCHITECTURE.md); canonical terms belong in the [Glossary](GLOSSARY.md).

