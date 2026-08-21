# Runtime Opportunity-Witness Instrumentation

Candidate baseline: `491b196377c1e33fdbccde21870f8ae2790085de`  
Stage #002 status: blocked pending independent audit  
Action #13 status: stopped

## Purpose and boundary

This instrumentation supplies prospective, reconstructive evidence for the three conformance
classes defined by `COVERAGE_AWARE_CONFORMANCE_SPEC.md`:

- **EXECUTED**: an accepted Action's authoritative transaction/effect evidence proves execution;
- **REACHED / UNSUPPORTED**: a positive game-state opportunity witness proves an unsupported exact
  semantic became relevant, while no effect is executed;
- **PRESENT / UNREACHED**: an exact semantic was registered on an involved runtime object, but no
  authoritative opportunity proves applicability.

The generic layer does not interpret or execute Actions. Existing typed Action evidence remains the
authority for EXECUTED. The conformance snapshot contains references into that evidence where an
exact source/fragment join is available; it does not replace richer Action-specific ledgers.

## Identity contract

A semantic key is derived deterministically from:

`Oracle ID (or deterministic definition fallback) + face index + fragment index + SHA-256(fragment)`

An occurrence adds the authoritative runtime object ID, controller, observed zone, turn, phase,
step, and exact limitations. Re-registering the same semantic key on the same runtime object does
not create another occurrence.

An opportunity key is SHA-256 over:

`occurrence ID + cause kind + cause ID`

Thus one typed event or one exact legal-action/block context can establish at most one opportunity
for one occurrence. Distinct creature-entry or attack events remain distinct real opportunities.
Python hashes, deck names, card-name dispatch, Pilot decisions, and thematic inference are absent
from both identities.

## Positive opportunity sources

The bounded candidate recognizes only applicability conditions it can prove from represented
authority:

| Opportunity | Required authority |
| --- | --- |
| Self ETB trigger | exact self-ETB Oracle shape plus typed `CREATURE_ENTERED` event containing the source runtime ID |
| Alliance trigger | exact Alliance entry shape plus a later typed entry event for another creature controlled by the source's controller |
| Attack trigger | exact attack-trigger shape plus typed `ATTACKERS_DECLARED` containing the source runtime ID |
| Graveyard casting permission | active player's represented main phase, authoritative source permanent, parsed P/T limit, and at least one matching authoritative creature object in that player's graveyard |
| Menace relevance | authoritative attacker in current combat plus an authoritative untapped creature considered as a block candidate during Declare Blockers |

Historical events are never retrospectively joined to an Alliance or attack occurrence registered
later. The sole historical join is the source's own just-created ETB event, because semantic
registration follows creature-entry processing during resolution. Unknown triggers, costs,
targets, choices, replacement predicates, and unsupported timing conditions remain PRESENT /
UNREACHED until a specific positive witness is implemented and audited.

## Reconstructive record and invariants

Every witness preserves game seed through the snapshot, turn/phase/step, runtime object and exact
fragment identity, controller, cause kind/ID, cause subjects, and unsupported classification.
Rules-event witnesses retain the typed event in the engine's immutable event registry.

Invariants reject duplicate opportunity keys, nonexistent semantic sources, fragment/index/hash or
Oracle-key mismatch, nonexistent/mismatched typed events, incompatible event steps, and unknown
cause kinds. Witness creation additionally rejects fabricated events, nonexistent event subjects,
non-graveyard legal-action subjects, nonbattlefield block subjects, and incompatible game steps.

`authoritative_state_fingerprint()` supplies the minimum normalized illegal-mutation boundary for
Stage #002. It deterministically hashes turn/step authority, Stack membership, combat membership,
ordered zones, life/loss state, RNG state, and winner while excluding diagnostic/evidence ledgers.
An invalid submitted operation can therefore be required to raise while leaving this fingerprint
unchanged. This is not a new mutation or gameplay subsystem.

## Scope freeze

The candidate adds evidence only. It does not add an Action, execute unsupported Oracle text,
change the Pilot, alter a deck or prototype, or run Stage #002. The accepted Stage #002 design and
readiness audit remain byte-identical.

