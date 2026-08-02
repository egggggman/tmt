# Contributor Journey

## Purpose

This guide helps a new contributor become productively curious without requiring hidden project
history. You do not need to read the whole repository before asking a question or improving one
bounded thing.

## First 30 minutes

Read, in order:

1. [README](../README.md) for the project shape and documentation routes.
2. [Project Constitution](PROJECT_CONSTITUTION.md) for mission, values, scope, and the Rule of Joy.
3. [Roadmap](ROADMAP.md) for completed foundations and future dependency order.

Then choose the area that interests you. You should be able to explain in one sentence what the
project is for, what milestone is current, and why “Store Facts. Compute Intelligence. Preserve
Decisions.” matters.

## First day

Read:

- [Architecture](ARCHITECTURE.md) for layer responsibilities and the reasoning pipeline;
- [Glossary](GLOSSARY.md) for canonical terminology;
- [World Guide](WORLD_GUIDE.md) for the boundary between Software and World;
- [Design Principles](DESIGN_PRINCIPLES.md) for how tradeoffs are made;
- [Repository Map](REPOSITORY_MAP.md) for where work belongs.

Understand three things before proposing a feature:

1. **Reasoning pipeline:** objective source facts precede deterministic analysis; Design Intent,
   Alignment, and Recommendations add later responsibilities without rewriting earlier evidence.
2. **Governance:** the Constitution explains why, principles guide judgment, the Glossary owns shared
   definitions, Decisions preserve accepted durable choices, and the Roadmap sets direction rather
   than dates.
3. **Community philosophy:** Community First, respect for source material, visible evidence, credit,
   consent, and the Rule of Joy apply to code, design, and publishing alike.

## Explore by contribution type

- Runtime or engine work: read the relevant engine guide, module, migration history, tests, and
  Accepted Decisions.
- Documentation: identify the owning document and link to canonical definitions instead of copying
  them.
- World or editorial work: read the World Guide and Underground Press Style Guide; label canon,
  interpretation, reporting, and humor clearly.
- Data or research: document provenance, rights, scope, and the distinction between fact and opinion.
- Maintenance: use [Repository Health](REPOSITORY_HEALTH.md) to record a focused, evidence-backed
  finding rather than beginning an unbounded cleanup.

## First contribution

1. Review [Repository Health](REPOSITORY_HEALTH.md) and current issues.
2. Open or choose an issue that states the problem, evidence, scope, and relevant source documents.
3. Discuss architecture before implementation when work crosses layers, changes durable data,
   introduces canonical vocabulary, or affects multiple engines.
4. Create a focused branch and keep unrelated cleanup out of the change.
5. Preserve history: add migrations instead of changing released ones; create new versions instead
   of mutating immutable identities; document supersession rather than erasing decisions.
6. Add or update tests when behavior changes. Documentation-only work should verify links,
   terminology, navigation, and explicit non-change boundaries.
7. Open a draft pull request early enough for useful review and explain evidence, tradeoffs,
   validation, exclusions, and follow-up work.

## Repository expectations

- Use canonical terms from the Glossary and capitalize named domain concepts consistently.
- Keep Fact, analysis, interpretation, Recommendation, and presentation responsibilities distinct.
- Prefer explicit, deterministic, evidence-backed behavior and inspectable failure states.
- Do not modify released migrations, hide overrides, erase audit history, or claim unsupported canon.
- Keep fixtures representative and neutral; keep examples honest about what is sample data.
- Run the repository’s formatting, lint, test, terminology, and link checks appropriate to your scope.
- Treat review as collaborative reasoning. Respond to evidence, state uncertainty, and preserve the
  rationale behind material decisions.
- Credit help. Ask before fictionalizing, quoting, or publishing another contributor’s work.

## A good first pull request

A good first PR solves one understood problem, changes the smallest responsible surface, links its
source documents, includes proportional validation, and leaves a reader able to explain why the
change belongs. Size is less important than clarity.

If you are uncertain, ask a narrow question or propose an Open Table discussion. Curiosity is a valid
first contribution.
