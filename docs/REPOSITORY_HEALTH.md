# Repository Health

## Purpose

A Repository Health Pass is a deliberate review of whether the project remains understandable,
coherent, testable, welcoming, and faithful to its architectural boundaries. It is maintenance, not a
feature milestone and not a search for cosmetic perfection.

## When to run a health pass

Run a focused pass before a major new responsibility, after a milestone that changes architecture or
canonical vocabulary, when contributor onboarding repeatedly exposes the same confusion, after a
large dependency or tooling change, or when documentation and behavior appear to disagree. Hold a
broader Repository Review Day at least once per major milestone cycle or when accumulated cleanup can
no longer be handled safely inside ordinary work.

## Documentation audit

- Confirm the README provides an intuitive path into current documents.
- Verify links, headings, version references, and ownership of definitions.
- Replace repeated definitions with links to the canonical source.
- Identify missing, stale, contradictory, orphaned, or prematurely promised material.
- Confirm changelog history remains historical rather than silently modernized.

## Terminology audit

- Compare shared terms with the [Glossary](GLOSSARY.md).
- Check capitalization and distinctions such as Fact, Capability, Deck Metrics, Finding, Alignment,
  and Recommendation.
- Flag a new term that duplicates an existing concept or crosses a layer boundary.
- Update the Glossary before allowing multiple incompatible meanings to spread.

## Architecture audit

- Confirm each layer has one responsibility.
- Trace facts, computed intelligence, interpretation, decisions, and presentation through the system.
- Verify engines do not absorb Character judgment or recommendation behavior prematurely.
- Compare current behavior with [Architecture](ARCHITECTURE.md), [Decisions](DECISIONS.md), and the
  [Roadmap](ROADMAP.md).
- Escalate irreversible or cross-layer changes for an explicit architectural decision.

## Code audit

- Look for unclear ownership, hidden state, unsafe transactions, dead paths, duplicated logic, and
  behavior without provenance.
- Check dependency, configuration, error-handling, and data-boundary assumptions.
- Prefer focused findings with evidence over broad rewrites.
- Do not combine unrelated cleanup with a feature merely because the files are nearby.

## Test audit

- Ensure tests cover deterministic output, failure rollback, provenance, negative controls, and
  important boundary cases.
- Check that fixtures remain representative, neutral, readable, and appropriately sized.
- Identify behavior that is tested only indirectly or assertions coupled to incidental formatting.
- Run the same validation path used by GitHub Actions where practical.

## World consistency audit

- Compare stories and recurring details with the [World Guide](WORLD_GUIDE.md).
- Keep official canon, project interpretation, world continuity, humor, and reporting distinct.
- Verify names, roles, published history, corrections, consent, and attribution.
- Confirm world material enriches presentation without changing analytical results.

## User experience audit

- Follow the [Contributor Journey](CONTRIBUTOR_JOURNEY.md) as a newcomer would.
- Check command examples, error messages, inspection paths, prerequisites, and next steps.
- Ask whether a reader can find evidence and understand why a result exists.
- Include accessibility, privacy, welcome, and recovery from mistakes—not only speed.

## Repository Review Day

A Repository Review Day is a bounded community maintenance session. Publish the scope beforehand,
assign one facilitator, record evidence-backed findings, and separate immediate low-risk cleanup from
work requiring architectural review. Do not turn the day into an unplanned rewrite. Close with an
audit summary, owners or issues for accepted follow-up, deferred items with rationale, and appreciation
for maintenance work.

## Health classifications

### Healthy

Canonical documents agree, navigation and tests work, layer boundaries remain clear, and any cleanup
is small enough for focused ordinary changes. Healthy does not mean finished.

### Needs Cleanup

The repository works, but bounded drift exists: stale links, duplicated prose, inconsistent names,
minor dead code, fixture debt, or confusing onboarding. Create focused issues or a documentation-only
cleanup PR; do not block unrelated safe work unless the drift creates material risk.

### Architectural Review Required

A contradiction affects responsibilities, durable data, provenance, public contracts, security,
irreversible history, or multiple dependent engines. Pause implementation of the affected area,
document the conflict and evidence, and reach an explicit decision before proceeding.

## Recording the pass

Record the date, scope, participants, checks run, classification, findings, decisions, and follow-up
links. A health pass produces evidence for action; it is not a score, leaderboard, or judgment of a
contributor.
