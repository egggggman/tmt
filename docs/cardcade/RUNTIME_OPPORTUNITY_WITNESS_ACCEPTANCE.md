# Runtime Opportunity-Witness Instrumentation Acceptance Audit #1

Status: **REJECT**  
Audit date: 2026-08-21  
Branch: `agent/cardcade-acceptance-stage-002`  
Audited candidate fingerprint: `ac99696379cee9254393579441532811d549bf22`

## Audit integrity

This was an evidence-only audit. No implementation, test, Stage #002, deck, Pilot, or gameplay file
was modified. This report is the only audit artifact created. The candidate fingerprint was
independently reproduced as SHA-1 over the newline-joined, path-sorted complete-file SHA-256 values
for:

- `src/tmnt_design_studio/conformance07.py`;
- `src/tmnt_design_studio/engine07.py`;
- `tests/test_conformance07.py`.

The Stage #002 documents remained byte-identical:

- design SHA-256:
  `d740d532f5e0c61d90b00c479c09100760b6353a23b18bc4621093ded826c624`;
- readiness-audit SHA-256:
  `30adad0540d11ef85de0f0a686f98cf401a42e133ec29a89783822c52fb44d97`.

No Stage #002 match was run.

## Reproduced Acceptance #001 evidence

Seeds 7001–7005 were each executed twice. Every duplicate pair was byte-identical. The candidate
reproduced:

- **18 unsupported registrations / 6 exact pairs**;
- **14 REACHED / UNSUPPORTED occurrences**;
- **4 PRESENT / UNREACHED occurrences**;
- **32 opportunity witnesses**;
- **27 references into existing authoritative Action evidence**;
- zero invariant violations in the five ordinary Acceptance runs;
- unchanged trajectories: Raphael T14, Raphael T18, Leonardo T19, Leonardo T43, Raphael T16.

| Seed | Unsupported | Reached | Present-only | Witnesses | Duplicate SHA-256 |
| ---: | ---: | ---: | ---: | ---: | --- |
| 7001 | 4 | 2 | 2 | 5 | `5f32283de2cb5a3702cff8070477ec40e784d806d5280b44a4f9e009debe10cc` |
| 7002 | 1 | 1 | 0 | 1 | `397a086bf3d09a3cf5ea19c1dcc81eb5b900f35ffdb92fdfa11c44d506713496` |
| 7003 | 3 | 3 | 0 | 5 | `6c694e2979fae6497363547999e66e3990a7ef74fd22130f92cd065c4c444a9d` |
| 7004 | 7 | 6 | 1 | 18 | `b934f8cc60ec07a9b2ea2ae91f362206741316133346eb7306a6beeca94d88f0` |
| 7005 | 3 | 2 | 1 | 3 | `026e9b5c03f0094443134cceb013e9e1a7adba4237b169cfe2134e8c237ccf98` |

## Conservative non-promotions

The four claimed non-promotions were independently reproduced from prospective output rather than
from expected game results:

1. **Raphael Menace, seed 7001** — the exact occurrence has no opportunity witness. Raphael's
   presence and attack do not establish that an authoritative blocker candidate was considered
   against that object.
2. **Raphael Menace, seed 7005** — likewise no block-candidate witness exists. It remains present
   rather than being inferred reached from combat participation.
3. **Raphael Alliance exile, seed 7001** — after the occurrence was registered, no joined typed
   controlled-creature entry event supplies a witness for that source object.
4. **Leonardo Sewer Samurai, seed 7004** — one of the four runtime occurrences has no represented
   main-phase legal-action context containing an authoritative qualifying graveyard creature.

The other three Sewer Samurai occurrences have positive main-phase/graveyard candidate witnesses.
The non-promotion is therefore occurrence-specific rather than a card-level assumption. These four
results are sound for the audited Acceptance runs.

## Structural audit of the emitted 32 witnesses

For each serialized witness, the audit joined seed from the enclosing game snapshot, turn and
phase/step, occurrence ID, runtime object ID, semantic key, exact Oracle fragment, cause kind and
cause ID. All emitted rules-event witnesses locate a typed event with identical subject IDs and
turn/phase/step. All opportunity keys are unique, and every reached occurrence has at least one
witness. Repeated processing of one event deduplicates by occurrence/cause identity, while distinct
event IDs remain distinct opportunities.

The source contains no deck-name, source-card-name, Acceptance-seed, or Pilot-strategy dispatch in
the conformance module or opportunity hooks. EXECUTED references are derived from resolved mature
Action evidence; opportunity witnesses themselves never set EXECUTED.

The instrumentation hooks do not consume RNG, construct legal Actions, select Pilot options, pay
costs, alter Stack/Priority, move zones, assign combat damage, or change life. The accepted winners
and turns remained unchanged. Diagnostic events change the evidence serialization by design, not
authoritative gameplay state.

## Material blocker: applicability validation is not authoritative

The ordinary 32 witnesses happen to match the intended Acceptance opportunities, but the generic
creation and invariant boundary does not prove that a registered event is semantically applicable
to its occurrence. Two independent adversarial probes demonstrate the defect.

### Stale Alliance source

A generic permanent bearing
`Alliance — Whenever another creature you control enters, draw a card.` was registered, moved from
the battlefield to the graveyard (making the original permanent a former object), and followed by
a typed creature-entry event under its former controller. The candidate created one REACHED /
UNSUPPORTED witness even though the Alliance source no longer existed on the battlefield:

```text
source_zone former
witness_count 1
invariants PASS
```

`_record_opportunity` verifies only that the source is present in the runtime registry. It does not
require an Alliance source to be the authoritative battlefield permanent at the event, nor does it
validate its controller at that moment. `_witness_from_event` uses the controller frozen when the
semantic occurrence was registered. Consequently a stale source—or a source whose controller has
changed—can be joined to a later unrelated controlled-entry context.

This violates the required prohibition on witnesses derived from stale zone identities and makes
the candidate unsafe for prospective Stage #002 evidence.

### Semantically unrelated typed event

A generic attack-trigger occurrence was paired directly with a valid typed `LIFE_GAINED` event
whose subject happened to contain the source ID. `_record_opportunity` accepted the witness, and
`check_invariants()` passed:

```text
semantic Whenever Generic Attacker attacks, draw a card.
cause_kind life_gained
witness_count 1
invariants PASS
```

The creation boundary checks event existence and identical subject IDs, while the invariant checks
the same structural join. Neither independently validates that the event kind, semantic trigger
shape, source liveness/controller, and game step collectively establish applicability. The normal
dispatcher avoids this malformed call, but the required engine invariant does not detect malformed
authoritative witness state. A valid unrelated event can therefore authenticate a false reach
claim.

## Opposite failure mode and deduplication

The focused tests and Acceptance runs establish that valid self-ETB, Alliance, attack,
graveyard-permission, and block-candidate opportunities survive despite unsupported payloads.
Reobserving one occurrence/cause pair does not add a witness; separate typed event IDs do. The
rejection is not caused by missing valid witnesses or nondeterministic identity. It is caused by
insufficient validation of what may become a witness.

## Validation

- Full suite: **506 passed / 1 skipped**
- Conformance: **7 passed**
- Card data: **5 passed**
- Ruff format: clean
- Ruff check: clean
- `git diff --check`: clean before this report
- Candidate fingerprint after validation:
  `ac99696379cee9254393579441532811d549bf22`

Passing tests do not cover either rejected adversarial relationship.

## Smallest evidence-backed correction

Centralize a generic authoritative applicability validator and invoke it both when creating a
witness and from `check_invariants()`. For each currently represented witness shape it must verify:

- the exact Oracle trigger/permission/restriction shape is compatible with the cause kind and typed
  event kind;
- the source was an authoritative object in the required zone at the opportunity boundary;
- controller and subject relationships are evaluated from authoritative state/event provenance at
  that boundary rather than only from registration-time fields;
- the cause occurs no earlier than semantic involvement, except for the explicitly bounded self-ETB
  join during resolution;
- event kind and step are compatible with the semantic predicate.

Add adversarial regressions for a departed Alliance source, changed controller, a valid unrelated
event, and invariant inspection of each malformed witness. Preserve all current Acceptance
classifications unless the corrected authority checks expose a genuine false positive.

**REJECT — the witness boundary accepts stale-source and semantically unrelated-event provenance; add shared authoritative applicability validation at creation and invariant time.**
