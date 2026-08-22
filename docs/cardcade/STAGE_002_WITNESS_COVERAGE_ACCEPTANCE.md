# Stage #002 Witness Coverage — Acceptance Audit #1

Candidate audited: `68bd3a43bef9024eabae9fd9205b4c7bf6685c97`  
Parent readiness checkpoint: `3047db6f88d3fdd8b7d6cdba66b07d7df4001a09`  
Status: **REJECT**

## Audit scope

This was an independent evidence-only audit of the preserved four-file candidate. The candidate is
exactly one commit beyond the banked readiness checkpoint and contains only the Stage #002 witness
inventory, Action-neutral conformance model, engine instrumentation, and focused tests. No Stage
#002 game was run and no gameplay, Pilot, deck, prototype, calibration, smoke, or Action behavior
was authorized or changed by this audit.

## Sound properties

The candidate's immutable context model is Action-neutral and retains source, subject, controller,
turn/step, typed fact, event, Stack, and state provenance. Context identities and deduplication are
deterministic and do not use Python process hashes. Creation requires registered identities, exact
fact sets, and authoritative event/Stack references, and invariant validation rechecks persisted
context/witness joins. Existing tests reject fabricated contexts, invalid zones, missing resources,
stale departure identities, malformed Stack response provenance, and registration-only instruction
claims.

These properties are retained. The rejection concerns two semantic joins, not the shared evidence
architecture or gameplay behavior.

## Blocker 1 — artifact-dependency applicability is overbroad

The candidate permits an `artifact_dependency` context to join any unsupported fragment containing
the word `artifact`. Its later validation proves an artifact entry and authoritative subjects, but
does not prove that the Oracle fragment's actual applicability grammar is an artifact-entry or
artifact-count predicate reconstructed by those facts.

Consequently, unrelated artifact text can be promoted from PRESENT / UNREACHED to REACHED /
UNSUPPORTED by an artifact-entry context. The positive trigger fixture does not establish rejection
of unrelated artifact semantics.

Smallest correction: restrict the join and shared validator to explicit bounded Oracle-derived
artifact-entry/dependency shapes whose predicates the context facts reconstruct. Unrelated
artifact costs, targets, activations, copies, attachment, removal, and other artifact text must not
join that context.

## Blocker 2 — target/choice applicability is overbroad

The candidate permits a `target_choice_available` context to join any fragment containing
`target`, `choose`, or `up to`, while its facts prove only that one or more battlefield creature
candidates exist.

That evidence cannot authenticate target player, artifact, spell, cards in other zones, color or
mode choices, constrained creature targets, multiple targets, or generic `up to` instructions. A
battlefield creature's existence is not proof that those materially different grammars became
applicable.

Smallest correction: restrict this producer and shared validator to exact bounded
battlefield-creature target/choice shapes whose complete represented constraints are proved by the
frozen candidate identities. All other target and choice grammars remain PRESENT / UNREACHED.

## Required regressions

- artifact-entry evidence cannot promote unrelated artifact text;
- battlefield-creature candidates cannot promote player, artifact, spell, nonbattlefield, color,
  modal, multiple-target, or otherwise incompatible choice text;
- the intended artifact-entry and bounded battlefield-creature positive cases still promote;
- creation-time validation and persisted invariants reject incompatible joins;
- Acceptance #001 remains deterministic and unchanged;
- the frozen inventory and Stage #002 design remain unchanged unless exact corrected bounded
  membership evidence requires a reported change.

## Verdict

**REJECT — bounded context provenance is structurally sound, but artifact-dependency and
target/choice joins are semantically overbroad; tighten only those two applicability grammars and
re-audit before Stage #002.**

Stage #002 remains blocked. Action #13, gameplay/Pilot changes, deck revisions, Prototype 0.3,
smoke testing, and calibration remain unauthorized.
