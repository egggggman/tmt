# Repository Health

## Purpose

This checklist supports repeatable governance reviews. It evaluates outcomes, not activity volume.
Record evidence for every result.

## Outcomes

- **Healthy** â€” boundaries and documentation agree; validation passes; no material cleanup is known.
- **Needs Cleanup** â€” localized inconsistencies or debt exist but architecture remains trustworthy.
- **Architectural Review Required** â€” a conflict crosses layers, changes canonical meaning, weakens
  reproducibility, or cannot be corrected safely as routine maintenance.

The highest-severity applicable outcome governs the review.

## Checklist

### Documentation consistency

- Canonical documents are identifiable and cross-linked.
- Current behavior and release status are accurate.
- Historical material is labeled; duplicate sources do not compete.
- Relative links resolve, every referenced file exists, and headings remain readable.
- Stale TODOs, placeholders, missing-file references, outdated diagrams, and duplicate headings are
  either corrected or recorded as findings.

### Terminology

- Public terms match [the canonical Glossary](GLOSSARY.md).
- Capitalization is consistent.
- Retired vocabulary is absent except in clearly labeled historical quotations when essential.
- Planned terms are not presented as implemented.

### Architecture boundaries

- Facts, computed intelligence, human intent, decisions, and presentation remain distinct.
- Layers do not bypass one another.
- Recommendations cite Evidence and community content cannot affect analytical outputs.

### Code health

- Ruff format and lint checks pass.
- Responsibilities are small and names match the domain.
- No hidden behavior or unexplained dependency is introduced.

### Migration health

- Released migrations are unchanged and ordered.
- Fresh initialization succeeds; checksums and transaction behavior remain valid.
- Every application connection enables foreign keys.

### Test health

- The full suite passes from a clean environment.
- Tests cover boundaries, failures, idempotence, and Provenanceâ€”not only happy paths.
- Fixtures remain deterministic and offline where practical.

### CLI consistency

- Help, names, output, and documentation agree.
- Commands preserve transactional and error-reporting guarantees.
- No command implies support for a planned layer.

### World consistency

- In-universe content follows the [World Guide](WORLD_GUIDE.md).
- The Underground Press follows its [publication guide](UNDERGROUND_PRESS.md).
- Software stays invisible in-universe and narrative never becomes analytical Evidence.

### User experience

- CLI and documentation use actionable language and expose failure context.
- Navigation, inspection output, and world presentation do not obscure source Evidence or current
  implementation status.

### User onboarding

- README â€œStart Hereâ€ guidance is current.
- A newcomer can install, initialize, inspect status, and find deeper specifications.
- Contribution expectations are explicit and welcoming.

### Philosophy compliance

- Work follows the [Constitution](PROJECT_CONSTITUTION.md) and
  [Design Principles](DESIGN_PRINCIPLES.md).
- Explainability, determinism, source respect, Community First, and the Rule of Joy remain visible in
  decisions.

### Release hygiene

- Version, changelog, tag, release notes, and implementation status agree.
- CI is green and validation evidence is recorded.
- License and attribution are unchanged unless an explicitly scoped legal decision authorizes change.
- Meaningful milestone history is preserved.

## Repository Review Day

After every major milestone, hold a **Repository Review Day** before starting the next architectural
layer. Review this checklist, current issues and PR language, release history, canonical docs, links,
runtime validation, and deferred work. Record the outcome, evidence, cleanup owners, and decisions
requiring architectural review. A review is complete when findings are visibleâ€”not when every minor
cleanup item is immediately solved.

