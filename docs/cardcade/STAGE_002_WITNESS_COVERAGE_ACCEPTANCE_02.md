# Stage #002 Witness Coverage — Acceptance Audit #2

Frozen candidate: `0390e5ff0dd023d61609ecc1908211d47788ca32`  
Audit #1 evidence checkpoint: `a53d918d0cd8bc4ec03e32198df27e969f83995c`  
CI at audit time: **UNCONFIRMED**  
Status: **REJECT**

## Scope and retained improvements

This independent evidence-only audit examined the correction made after Audit #1. No gameplay,
Pilot, deck, prototype, Action, calibration, smoke, or Stage #002 execution change was authorized.

The correction materially improves the candidate. Incompatible target/choice forms now have
explicit adversarial rejection coverage for player, artifact, spell, graveyard, color, constrained
creature, `up to`, and multiple-target cases. Artifact applicability is also materially narrower
than the Audit #1 candidate. These improvements are retained.

Two remaining provenance gaps prevent acceptance.

## Blocker 1 — target linkage is not occurrence-level

`target_choice_available` retains an `instruction_context_id`, but validation proves only that the
referenced context is `instruction_reached`, has the same source, and occurred during the same turn
and step. The instruction context does not bind the semantic occurrence ID, fragment index/hash,
instruction ordinal, or another exact immutable instruction identity.

Two unsupported instructions belonging to the same resolving source at one resolution boundary
can therefore share provenance. The positive regression proves source-level linkage, not exact
instruction-occurrence linkage.

Smallest correction: bind every `instruction_reached` context to its exact immutable
`SemanticOccurrence` and Oracle fragment identity. A target/choice context must reference that
same instruction context and exact occurrence. Cross-instruction reuse must fail at creation and
under persisted invariant validation.

## Blocker 2 — artifact-count characteristic evidence is incomplete

The accepted artifact grammar includes both:

- `Equipped creature gets … for each artifact you control.`
- `<source> gets … for each other artifact you control.`

The context currently proves only that an authoritative artifact entered under the source
controller's control. It does not freeze or validate the relevant authoritative artifact count.
For the Equipment form, it also does not prove that the Equipment was attached to an authoritative
equipped creature at that occurrence.

An artifact entry can therefore promote the Equipment characteristic even when no equipped
creature exists, and neither characteristic is reconstructive from the persisted context.

Smallest correction: freeze and validate the complete counted artifact identity set and resulting
count. For the self-specific `each other artifact` form, prove the exact source and its exclusion
from the set. For Equipment, prove the authoritative attachment relationship or, if that state is
not represented, leave the form PRESENT / UNREACHED.

## Required regressions

- two eligible instructions on one source/resolution cannot exchange target provenance;
- fragment/occurrence identity survives serialization and is invariant-validated;
- artifact counts reconstruct from immutable authoritative event state;
- the source-specific count excludes the exact source object;
- unequipped Equipment does not receive an artifact-count witness;
- intended entry-trigger and source-specific positive cases remain valid;
- Acceptance #001 behavior and conservative classification remain unchanged.

## Verdict

**REJECT — the first correction narrows both grammars, but target evidence is not bound to the
exact semantic occurrence and artifact-count characteristic evidence does not reconstruct count or
Equipment attachment state. Make only the bounded provenance correction and re-audit.**

Stage #002 and Action #13 remain blocked. Prototype 0.3, calibration, smoke testing, Pilot/gameplay
changes, and deck revisions remain unauthorized.
