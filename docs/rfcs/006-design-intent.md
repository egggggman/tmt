# RFC 006 — Design Intent

Status: Accepted

## Decision summary

Design Intent is a small, versionable, human-authored design envelope for expressing one Character through a playable Sewer Deck. It records what the deck is trying to feel like and do; it does not score cards, derive Capabilities, perform Alignment, recommend changes, or postpone playtesting.

The project adopts a **Playable first. Explainable increasingly.** workflow. A bounded Design Intent is sufficient to build Prototype 0.1. Later Alignment and Recommendation work must learn from real prototypes and playtest evidence rather than become prerequisites for them.

## Problem

Objective Magic Facts, Capabilities, Deck Metrics, and Findings can describe cards and decks, but cannot decide what an authentic Leonardo deck should feel like. That judgment must be explicit and preserved without disguising it as objective truth or requiring a large ontology before a deck can be played.

## Goals

A Design Intent must:

- distinguish Character source truth from one gameplay interpretation;
- give a designer enough direction to build and revise a legal 60-card prototype;
- preserve rationale and evidence without rewriting objective upstream data;
- permit multiple authentic intents for one Character;
- be inspectable, versionable, supersedable, and usable by future Alignment;
- express fun for both pilot and opponent as a first-class design requirement;
- remain small enough that completing it does not delay useful playtesting.

## Non-goals

Design Intent does not:

- derive or override Capabilities;
- calculate Character fit, theme coverage, Alignment, or a universal score;
- rank or recommend cards;
- predict matchups;
- guarantee competitive strength;
- require future engines before a prototype can be built or played.

## Boundary

Character research asks: **Who is this Character?**

Design Intent asks: **Which authentic parts of that Character are we deliberately expressing through this deck and play pattern?**

Deck Analysis asks: **What objectively appears in this Deck Version?**

Future Alignment asks: **How does deck evidence support this Design Intent?**

Playtesting asks: **What actually happened, and was the intended experience fun?**

These responsibilities remain separate.

## Minimum design envelope

A prototype-ready Design Intent contains the following authored targets. They are deliberately qualitative or range-based where false precision would add no value.

1. **Identity statement** — one short description of the Character expression.
2. **Gameplay thesis** — the deck's intended repeatable play pattern.
3. **Primary themes** — usually 2–4 Character themes that must be visible in play.
4. **Capability priorities** — usually 3–6 existing canonical Capabilities the deck should emphasize.
5. **Experience goals** — what should be fun and satisfying for the pilot.
6. **Opponent experience** — what interaction, counterplay, and variety should remain available to the opponent.
7. **Distinctiveness** — what must make this deck play differently from the other Sewer Decks.
8. **Functional envelope** — broad expectations for curve, mana, interaction, threats, resilience, or other objective deck needs that can be checked with existing analysis.
9. **Accepted weaknesses** — deliberate shortcomings that preserve identity or healthy battle-box play.
10. **Guardrails / anti-patterns** — strategies or behaviors that would technically function but violate the intended identity or fun target.

Each target may carry rationale and source Evidence. Missing evidence is visible; it does not silently become fact.

## Fun as a first-class requirement

A successful Sewer Deck should:

- clearly express its Turtle/theme;
- be fun to pilot;
- be fun to play against the other decks;
- have a distinct play pattern;
- function as a solid Magic deck;
- be explainable without requiring excessive complexity.

These are design goals, not deterministic engine scores. Before sufficient playtest evidence exists, they are hypotheses. Playtesting may confirm, challenge, or refine them.

## Versioning and lifecycle

A Character may own multiple Design Intents. Each intent has a stable identity and revisions are preserved rather than overwritten.

Suggested lifecycle:

`draft → prototype-ready → active → superseded | retired`

- **draft**: incomplete and not yet suitable to drive a prototype.
- **prototype-ready**: the minimum design envelope is complete enough to build and play.
- **active**: currently guiding deck iteration.
- **superseded**: replaced by a newer revision while remaining inspectable.
- **retired**: intentionally abandoned without erasing history.

Prototype readiness is a human decision, not an Alignment score.

## Provenance and audit

Design Intent is authored judgment. For each durable claim or priority, preserve where practical:

- author or responsible designer;
- rationale;
- source citation or Evidence reference;
- revision identity and timestamp;
- supersession relationship;
- design decisions that materially changed the intent.

Objective Magic Facts, Raw/Effective Capabilities, Deck Metrics, and Findings remain unchanged.

## Failure and ambiguity behavior

- Unsupported Character claims remain explicitly unsupported or provisional.
- Conflicting priorities are recorded as a design tension; they are not silently averaged into a score.
- Missing Evidence does not prevent exploratory drafting, but blocks claims of strong source support.
- A Design Intent may reference existing Capabilities but may not create Capability truth by assertion.
- It may describe desired deck behavior but may not claim Alignment until that later layer evaluates evidence.
- Revisions never rewrite prior intent history.

## Leonardo reference intent

### Identity statement

Leonardo is the disciplined field leader: coordinated, prepared, protective of the team, and capable of turning orderly development into decisive action.

### Gameplay thesis

Develop a coordinated board, make efficient tactical exchanges, protect important pieces, and convert accumulated positioning into a deliberate attack. The deck should reward sequencing and planning rather than reckless speed or passive inevitability.

### Primary themes

1. Leadership
2. Discipline
3. Teamwork / coordination
4. Protection / responsibility

### Capability priorities

Use the existing Capability catalog rather than inventing Leonardo-only mechanics. During prototype construction, prefer capabilities representing:

- protection or resilience;
- interaction / tactical answers;
- card selection or other planning tools;
- coordinated creature development / support;
- a credible way to convert board position into pressure.

Exact canonical identifiers are selected from the implemented catalog during Prototype 0.1 construction.

### Experience goals

The pilot should frequently feel that good sequencing matters, that creatures operate as a team, and that Leonardo can stabilize a messy situation before leading a purposeful attack.

### Opponent experience

The opponent should have meaningful windows to interact. Leonardo should not rely on hard locks, repetitive denial, or a single fragile combo that makes games binary. Games should create visible tactical decisions on both sides.

### Distinctiveness

Leonardo is not Raphael. Leonardo's advantage should come from coordination, protection, and sequencing—not maximum aggression, impulsive damage racing, or all-in combat. Raphael Prototype 0.1 will be used as the first contrast test.

### Functional envelope

Prototype 0.1 should be a legal 60-card Standard deck with a functional mana base, enough early plays to participate in the game, sufficient interaction to avoid goldfishing, a coherent creature/threat plan, and a curve that existing Deck Analysis does not flag as obviously dysfunctional.

### Accepted weaknesses

Leonardo may sacrifice some raw speed and individual-card explosiveness to preserve coordinated play and meaningful sequencing. It need not be optimized for the broader tournament metagame; the immediate environment is the future ten-deck Sewer Deck battle box.

### Guardrails

Avoid:

- pure aggro whose decisions mostly reduce to attacking every turn;
- draw-go control with little visible team presence;
- solitaire combo;
- oppressive locks or repeated resource denial;
- mechanically strong inclusions that dominate the deck while contributing little to Leonardo's play identity.

## Negative controls

The following would violate this intent even if Standard-legal and statistically competent:

- a burn-heavy race deck with minimal coordination;
- a creatureless control shell using Leonardo only as flavor text;
- a combo deck that ignores board development;
- a pile selected only from generic card-quality rankings;
- a deck whose main identity is better suited to Raphael than Leonardo.

## Future Alignment contract

Alignment may consume the Design Intent's explicit themes, capability priorities, experience hypotheses, guardrails, and evidence references. It must return explainable support/conflict evidence. It may not mutate the Design Intent, and this RFC does not prescribe an Alignment scoring formula.

## Prototype/playtest loop

The canonical near-term loop is:

`Design Intent → Prototype 0.1 → Deck Analysis → Playtest → Observations → Design decision → new Deck Version`

Playtest observations can expose missing or misleading Design Intent targets. Updating the intent creates preserved revision history. Alignment and Recommendations should improve from this evidence rather than gate the loop.

## Alternatives considered

### Build Alignment and Recommendations first

Rejected for the current phase. It delays the first useful playtest and risks encoding assumptions before the project has real deck evidence.

### Large universal intent ontology

Rejected. It increases authoring and implementation cost without demonstrated benefit for the first prototypes.

### Single numerical Character-fit or fun score

Rejected. It creates false precision, hides tradeoffs, and collapses distinct human judgments into an opaque target.

### Unstructured prose only

Rejected as the canonical model. Prose is useful for rationale, but a small repeated envelope makes intents easier to inspect, compare, revise, and eventually consume downstream.

## Compatibility and implementation guidance

The existing schema already contains foundational `characters`, `design_intents`, themes, capability priorities, and experience goals. Implementation after acceptance should prefer additive changes and reuse those foundations. Do not create a migration merely to mirror every RFC heading. Add storage only when a field must be queried, versioned, or preserved independently in real use.

The first implementation should support Leonardo and Prototype 0.1 with the minimum schema/CLI work necessary. Generalize only after Leonardo and Raphael reveal repeated needs.

## Security, privacy, consent, and source material

Store only project-relevant authorship and evidence metadata. Do not require personal information for Design Intent. Clearly distinguish source citations from project interpretation. Community contributions must preserve attribution and consent expectations defined by project governance.

## Acceptance checklist

- [x] One bounded responsibility: human-authored target.
- [x] Character and Design Intent are distinct.
- [x] Authored intent and computed Alignment are distinct.
- [x] Multiple intents and preserved history are supported conceptually.
- [x] Evidence, rationale, provenance, and revisions remain inspectable.
- [x] Objective upstream layers cannot be rewritten by intent.
- [x] Leonardo reference case is concrete enough to build Prototype 0.1.
- [x] Alternatives and tradeoffs are documented.
- [x] Existing canonical terminology is preserved.
- [x] No runtime, schema, migration, engine, or license behavior is changed by this RFC.
- [x] Maintainer explicitly accepted the RFC through the playable-first course correction.

## Acceptance record

RFC 006 is accepted as the Design Intent contract. Leonardo Prototype 0.1 was authorized by the
owner's explicit **COWABUNGA** course correction: finish the RFC, build the prototype, play it, and
learn from it. No Alignment or Recommendation engine is required before the prototype is built and
played.
