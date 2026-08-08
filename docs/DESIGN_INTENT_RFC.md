# Design Intent RFC

## Status and decision

- **RFC status:** Under Review
- **Target milestone:** v0.6.0
- **Issue:** #11
- **Authors:** project contributors
- **Approval authority:** project maintainers
- **Applicable engine context:** Capability rule set `2026.08.1`; Deck Analysis engine `2026.08.0`
- **Supersedes:** no accepted Design Intent RFC

This RFC specifies the first useful Design Intent model and a Leonardo reference instance. It does
not implement a runtime engine, persistence, Alignment, Recommendations, or scoring.

## Decision summary

> A Design Intent describes how a Character's philosophy should be experienced through
> gameplay—not how a deck must be constructed.

A Design Intent is a human-authored, evidenced, versioned interpretation of a Character. It defines
a flexible design space in which substantially different decks may be valid. It is not the
Character, a canonical claim about source material, a deck recipe, or an objective engine result.

The initial reasoning model is deliberately lean:

```text
Character interpretation
  ↓
Core Values
  ↓
Strategic Principles
  ↓
Gameplay Objectives
  ↓
Design Envelope
```

Evidence, provenance, Design Tensions, lifecycle, and governance support this model; they are not
additional computational stages. Relationships are many-to-many. A target needs a documented path
upward, not an artificial one-to-one mapping.

## Architectural boundaries

The Character is the subject being interpreted. A Design Intent is one authored interpretation of
that subject. A Character may therefore have multiple simultaneous or historical Design Intents.

Capabilities remain objective, evidence-backed descriptions of what Oracle cards do. Design Intent
does not change Capability rules, evidence, Confidence, or overrides. Deck Analysis remains an
objective description of one immutable Deck Version. A future Alignment layer compares that
objective analysis with one Accepted Design Intent version. Recommendations remain downstream of
Alignment and may never become inputs to Design Intent or Capability derivation.

The intended first gameplay loop is:

```text
Character → Accepted Design Intent → Candidate Deck → Deck Analysis
          → future Alignment → human adjustment → playtest
```

Automated Recommendations follow only after this loop has been exercised with a real Leonardo
prototype. This separation preserves the constitutional rule: **Store facts. Compute intelligence.
Preserve decisions.**

## Required components and ownership

### Identity and interpretation

Every intent identifies its Character, stable intent identifier, semantic version, title, concise
interpretation, lifecycle status, authors, reviewers, approvers, evidence basis, applicable rule and
Capability context where relevant, and supersession history. The interpretation states the specific
reading being explored without claiming objective truth.

### Core Values

Each intent has three to five descriptive Core Values answering, “What fundamentally motivates this
interpretation?” They contain neither Magic mechanics nor deck measurements, and receive no
personality or confidence scores.

### Strategic Principles

Normally four to six Strategic Principles answer, “How does this interpretation consistently solve
problems?” They describe reusable strategic behavior, not traits, mechanics, or a universal
fictional-character taxonomy. The initial vocabulary should remain small and may include
Preparation, Protection, Coordination, Adaptability, Persistence, Efficiency, Creativity, and
Restraint where those terms carry distinct meaning.

### Gameplay Objectives

Normally five to eight Gameplay Objectives answer, “What consistent behaviors should someone
observe when this deck is played?” They describe behavior without naming cards. Initial reusable
terms include Establish Position, Maintain Initiative, Preserve Resources, Coordinate Resources,
Control Critical Threats, Sustain Momentum, Recover, and Finish Decisively.

### Design Envelope

The Design Envelope is the measurable expression of the intent. An initial envelope should contain
roughly eight to twelve meaningful targets, preferring canonical Capabilities and then existing
objective Deck Analysis metrics. Each target records:

- the exact Capability identifier or Deck Metric key and field;
- a preferred range, minimum, maximum, preferred presence, or justified discouragement;
- rationale and upward trace to Gameplay Objectives, Strategic Principles, and Core Values;
- the applicable engine/rule context and validation state.

Ranges define a region of acceptable design space, not a recipe. Values are initial design
hypotheses until candidate construction and playtesting provide evidence. Exact card identities,
archetypes, colors, and curves are not implied unless an intent explicitly and evidentially needs
them.

An absent target is **UNCONSTRAINED**. It does not mean zero, prohibited, or undesirable. When the
current system cannot measure an important idea honestly, the intent records the limitation and
keeps it narrative rather than inventing a proxy or pseudo-metric.

### Design Tensions

Every intent documents meaningful trade-offs. In v0.6 these are human-readable statements, not
scores or optimization rules. They help reviewers understand why a deck may sit at different valid
points within the envelope.

### Evidence

Evidence is classified conceptually as:

- **Character Evidence:** why the interpretation reflects the Character;
- **Design Evidence:** why the proposed gameplay behavior expresses that interpretation;
- **Validation Evidence:** what later deck review and playtesting teach about the interpretation.

Character and Design Evidence make an intent reviewable. Validation Evidence accumulates without
silently rewriting an Accepted version; a meaningful changed conclusion produces a new version.
Evidence should be attributable enough for another contributor to inspect or challenge it. The first
version uses a small durable evidence record: evidence class, source title or description, source
locator, contributor, and rationale. A URI and accessed date are optional when applicable. This is
an inspectable citation contract, not a universal bibliography schema.

## Explainability contract

Every meaningful envelope target must be explainable as:

```text
target → Gameplay Objective(s) → Strategic Principle(s) → Core Value(s)
       → Character interpretation
```

One target may support several objectives, and several targets may jointly express one objective.
The contract forbids unexplained conceptual jumps; it does not demand artificial uniqueness.

## Lifecycle, versions, and governance

The lifecycle is **Draft → Under Review → Accepted → Superseded or Retired**.

- **Draft:** editable and non-authoritative.
- **Under Review:** structurally complete, but not production-authoritative.
- **Accepted:** versioned, authoritative for applicable downstream analysis, and immutable.
- **Superseded:** replaced for future use by a newer Accepted version; historical references remain valid.
- **Retired:** not recommended for future use, but preserved historically.

An Accepted intent is never mutated in place. A meaningful change creates a new version. Major
versions change the interpretation or model incompatibly; minor versions change Core Values,
Strategic Principles, Gameplay Objectives, Design Tensions, or the Design Envelope meaningfully;
patch versions clarify wording or correct metadata without changing meaning. Evidence and playtest
observations may accumulate beside an Accepted version, but may not silently alter it. Historical
analyses identify the exact Accepted Design Intent version they used and remain reproducible. A
Design Intent becomes Accepted only after documented maintainer review and approval. Community
proposals and feedback may inform the decision, but current project authority rests with maintainers.
Future governance changes do not rewrite historical acceptance records.

## Leonardo reference Design Intent

### Identity

- **Character:** Leonardo
- **Intent identifier:** `leonardo-disciplined-coordination`
- **Version:** `0.1.0`
- **Status:** Under Review
- **Interpretation:** Leonardo seeks sustainable advantage through disciplined preparation,
  coordinated action, protection of his team, and measured commitment rather than reckless or
  overwhelming force.
- **Evidence state:** Character and Design Evidence require sourced review before Acceptance;
  Validation Evidence awaits deck construction and playtesting.

This reference proves model shape and current measurability. It does not claim that its wording or
numerical hypotheses are final.

### Core Values

- **Leadership:** accept responsibility for giving the team direction and a path to success.
- **Discipline:** favor deliberate choices and prepared action over impulse.
- **Responsibility:** protect people and resources entrusted to the leader.
- **Teamwork:** create advantage through coordinated contributions rather than individual excess.

### Strategic Principles

- **Preparation:** establish the resources and options needed before committing.
- **Coordination:** make separate resources contribute to a coherent plan.
- **Protection:** prevent avoidable loss and preserve the team's ability to act.
- **Adaptability:** retain useful responses when the original plan is disrupted.
- **Restraint:** apply sufficient force at the important moment without overcommitting.

### Gameplay Objectives

- **Establish Position:** develop a stable base from which later choices remain available.
- **Coordinate Resources:** make multiple cards and functions contribute to the same evolving plan.
- **Preserve Resources:** protect important resources and avoid unnecessary exchanges.
- **Maintain Initiative:** answer critical interference while continuing to advance.
- **Recover:** rebuild useful options after disruption.
- **Finish Decisively:** convert a prepared advantage into a clear conclusion when the moment arrives.

### Initial Design Envelope

All ranges below are hypotheses for a 60-card main deck. Capability targets use the `copy_count`
field under the existing `capability_totals` Deck Metric; they select existing Capability meaning and
do not change derivation. Metric targets use existing scalar Deck Analysis metrics directly.

| # | Existing target | Kind | Initial target | Why and trace |
|---|---|---|---|---|
| 1 | `targeted-removal` / `copy_count` | Capability | Preferred 5–9 | Selective answers maintain initiative without indiscriminate force. → Maintain Initiative; Preparation, Restraint; Discipline, Responsibility. |
| 2 | `protection` / `copy_count` | Capability | Preferred 3–7 | Protecting committed resources expresses responsibility while preserving future action. → Preserve Resources, Maintain Initiative; Protection, Preparation; Responsibility, Leadership. |
| 3 | `card-draw` / `copy_count` | Capability | Preferred 5–9 | Renewable options sustain coordinated action and recovery. → Coordinate Resources, Recover; Preparation, Adaptability, Coordination; Discipline, Teamwork. |
| 4 | `card-selection` / `copy_count` | Capability | Preferred 3–7 | Selection rewards prepared, measured access to the right tool without prescribing that tool. → Establish Position, Maintain Initiative; Preparation, Adaptability, Restraint; Discipline, Leadership. |
| 5 | `recursion` / `copy_count` | Capability | Preferred 2–5 | Recovering spent or lost resources gives disruption a survivable cost. → Recover, Preserve Resources; Adaptability, Protection; Responsibility, Teamwork. |
| 6 | `tempo` / `copy_count` | Capability | Preferred 2–6 | Temporary setbacks create time to advance without requiring overwhelming removal. → Maintain Initiative, Establish Position; Restraint, Adaptability; Discipline, Leadership. |
| 7 | `finisher` / `copy_count` | Capability | Preferred 2–4 | A bounded closing package rewards choosing the prepared moment to commit. → Finish Decisively; Preparation, Coordination, Restraint; Leadership, Discipline, Teamwork. |
| 8 | `interaction_density` | Deck Metric | Preferred 0.18–0.32 | Meaningful but non-dominant interaction supports protection and initiative without making reaction the whole plan. → Maintain Initiative, Preserve Resources; Protection, Restraint; Responsibility, Discipline. |
| 9 | `average_nonland_mana_value` | Deck Metric | Preferred 2.0–3.5 | A broad initial band discourages a consistently slow hand while leaving archetype and curve shape open. → Establish Position, Maintain Initiative; Preparation, Adaptability; Discipline, Leadership. |
| 10 | `creature_ratio` | Deck Metric | Preferred 0.30–0.55 | A visible team should participate in the plan, but the range permits control, tempo, and synergy variants. → Coordinate Resources, Finish Decisively; Coordination, Protection; Teamwork, Responsibility. |

Capability counts may overlap on multifunction cards. They are not independent deck slots, package
sizes, or card recommendations. Confidence-weighted totals remain inspectable but are intentionally
not targeted: Confidence measures evidence strength, not gameplay expression or quality.

### Unconstrained and narrative characteristics

No current metric objectively measures leadership, discipline, teamwork quality, restraint,
coordination quality, protection of a specifically important permanent, flexibility of lines,
resource efficiency, or recovery quality. These concepts remain narrative and are evaluated later
through explainable Alignment and playtest evidence. Color identity, exact land count, individual
card choices, archetype, token use, ramp, counterspells, board wipes, and all other unlisted
Capabilities and Deck Metrics are initially UNCONSTRAINED.

### Design Tensions

- **Protection vs Initiative:** holding a protective response can preserve the team but delay useful
  development; valid builds may choose different moments to expose resources.
- **Coordination vs Speed:** assembling complementary roles can produce sustainable advantage while
  a faster line may require fewer dependencies.
- **Resilience vs Immediate Tempo:** recovery tools improve endurance but can compete with cards that
  affect the current turn.

### Evidence plan

Before Acceptance, maintainers should attach Character Evidence for the interpretation and each Core
Value, then review the Design Evidence encoded in the objective, target, and tension rationales.
Leonardo `0.1.0` remains Under Review until that evidence review is complete. Candidate-deck or
playtest Validation Evidence is not a prerequisite for initial Acceptance; it is the next mechanism
for testing and, when necessary, superseding the hypotheses.
Candidate-deck analysis should record every metric against Capability rule set `2026.08.1` and Deck
Analysis engine `2026.08.0`. Later playtests should record Validation Evidence for whether the deck
actually establishes, coordinates, preserves, recovers, and finishes as intended. Evidence that
changes the meaning or envelope materially creates a successor version rather than editing an
Accepted `0.1.0`.

## Conflicts and repository reconciliation

The canonical production baseline is v0.5.0. The inspected `main` branch agrees across
`pyproject.toml`, `README.md`, `PROJECT_STATE.md`, `CHANGELOG.md`, package version constants, and the
Scryfall user agent. No v0.5.1 release or tag is evidenced, so this RFC does not invent one.

Several requested root documents do not exist: `PROJECT_CHARTER.md`, `PROJECT_STATE.md`, `ROADMAP.md`,
`GLOSSARY.md`, and `STYLE_GUIDE.md`. Their current canonical responsibilities are mostly covered by
`docs/PROJECT_CONSTITUTION.md`, `docs/ROADMAP.md`, `docs/GLOSSARY.md`,
`docs/DESIGN_PRINCIPLES.md`, and the world-specific `docs/UNDERGROUND_PRESS_STYLE_GUIDE.md`. No
duplicate root documents are introduced.

The database specification and migration `004_tmnt_knowledge.sql` predate this model and use Themes,
direct Capability priorities, and experience goals. They demonstrate that Character and Design
Intent are distinct, but are not accepted as the v0.6 persistence design. Reconciling schema shape
requires a new migration during implementation; no released migration is changed here.

Architecture currently names a future Recommendation Engine immediately after Deck Analysis in one
component description, while its system flow correctly places future Design Intent and Alignment
before Recommendations. This RFC makes the latter dependency authoritative for v0.6 planning.

## Implementation contract and resolved first-pass decisions

Implementation may begin once this RFC is Accepted, but v0.6 remains incomplete until code and
persistence satisfy lifecycle, immutable-version, provenance, evidence, envelope, and trace
contracts. The first pass deliberately chooses the smallest useful representation:

1. Character Evidence uses the bounded evidence record defined above. Rich bibliography formats wait
   for demonstrated need.
2. Semantic versions follow the major/minor/patch meaning policy above; Accepted versions remain
   immutable.
3. The first persistence pass stores a validated, versioned Design Intent document plus immutable
   acceptance metadata. Trace relationships are normalized only after real query or reuse needs
   demonstrate value.
4. Leonardo `0.1.0` remains Under Review until Character and Design Evidence receive documented
   maintainer review. Initial deck or playtest Validation Evidence is not required to accept the
   hypothesis.
5. v0.5.0 is the canonical repository baseline. No v0.5.1 release is assumed.

These are architectural defaults, not new runtime behavior. They preserve a reversible path while
allowing a Leonardo prototype to reach the table quickly.

## RFC acceptance review

This RFC defines Design Intent and its distinction from Character; assigns ownership to every
component; defines envelope, UNCONSTRAINED behavior, explanation, evidence, lifecycle, supersession,
and maintainer approval; and represents Leonardo using only current Capabilities and Deck Metrics.
Every Leonardo target has an upward trace. The bounded first-pass decisions above are resolved, so
implementation can begin without inventing new gameplay philosophy. The immediate validation path
is Leonardo Prototype 0.1: construct a legal candidate deck, run existing Deck Analysis, play it,
and record observations before building Alignment or Recommendations.

## Out of scope

This RFC does not implement or design algorithms for a Design Intent runtime engine, database
migration, Alignment, Recommendations, scoring, authenticity, AI/ML, deck generation or tuning,
playtest simulation, matchup prediction, personality scoring, or Design Tension optimization.
