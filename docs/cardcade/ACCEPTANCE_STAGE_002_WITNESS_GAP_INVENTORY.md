# Acceptance Stage #002 Witness-Gap Inventory

Parent baseline: `923403cb6ddf8d9fb082501da743c50ae0a5e4a0`  
Evidence checkpoint: `3047db6f88d3fdd8b7d6cdba66b07d7df4001a09`  
Status: bounded instrumentation candidate; Stage #002 remains blocked

## Frozen evidence universe

This inventory was derived from the unchanged Prototype 0.1/0.2 manifests named by the Stage
#002 design and the authoritative TMT/PZA/TMC snapshot. It contains 78 unique cards, 127 unique
Oracle-fragment/limitation members, and 243 deck/Oracle-fragment/limitation memberships. The
stable deck-membership digest is:

`57ab1be61f03606003345a5cd1aa1a8f8f7f5a98d162476666582dbe2ab6365c`

The counts below overlap deliberately because a compound fragment can require more than one
applicability proof. A producer may prove that its boundary was reached; it never proves that an
unsupported effect executed.

| Gap family | Frozen memberships | Membership digest | Required authoritative boundary |
| --- | ---: | --- | --- |
| Activation/cost availability | 94 | `082b741878eef4f42c4b3e4c313d5ec821831d3edb7824dd4be43119e84c9c7d` | Controlled source, timing, fixed represented mana and tap availability |
| Permanent departure | 17 | `1eceb43ff60b4cba1bef2e14ff062b89c1e51b8a81ca9e89a7ef60c29275187e` | Exact battlefield object leaving and qualifying watcher/source |
| Replacement evaluation | 6 | `882120d618354d215bc57fb86f7ed714fe3db2f4169ae89df60d0577b7e9b61b` | Represented counter placement or other exact replaceable event |
| Artifact dependency | 86 | `fef714564cd951b9da11fa1c7dbf45035b63eb709cad5f439fc0a19dc31eb0b2` | Authoritative artifact entry or battlefield predicate evaluation |
| Stack response | 7 | `63bc0df421590db17c91595df6abfc6106a4c5cd93ec0a3771c0f86cf47cc7c4` | Matching spell on Stack, response card in Hand, payable represented mana |
| Target/choice availability | 85 | `0789cf0b215b0dca598c982302541c0aeda028be855e7c809451843d8c0d46c5` | Reached instruction plus authoritative candidate identities |
| Compound/sequential instruction | 13 | `15a2c66bb26f829a7c07fb14245d60ed837acc31e642f22e2f5723d58b8f6efa` | Actual resolving-object instruction point, never registration alone |

## Leverage ranking

1. **Shared immutable opportunity context.** All seven families need the same identity,
   state-boundary, deterministic serialization, deduplication, and invariant contract. This is the
   highest-leverage correction and avoids seven Action-specific telemetry paths.
2. **Activation and artifact contexts.** They dominate Donatello/Krang and occur in every frozen
   pairing. Only fixed, provably payable costs and actual artifact-entry/state boundaries qualify;
   complex costs remain unpromoted.
3. **Departure contexts.** These are exact zone transitions already owned by the engine and unlock
   the principal Michelangelo/Bebop and Splinter/Shredder negative-boundary measurements.
4. **Resolution instruction plus target/choice contexts.** These distinguish a resolving compound
   instruction from merely present text in April/Casey without executing its unsupported child.
5. **Stack response contexts.** Narrow corpus reach, but high pair-specific value for April/Casey;
   a witness requires a matching authoritative Stack object and payable response in Hand.
6. **Replacement evaluation.** Smallest corpus family and safely witnessable only at represented
   replaceable events. Unknown replacement shapes remain PRESENT / UNREACHED.

## Bounded candidate contract

`AuthoritativeOpportunityContext` is Action-neutral. It freezes turn/phase/step, active player,
controller, source and subject runtime identities and zones, optional typed-event/Stack linkage,
and the authoritative pre-context state fingerprint. Its stable context digest makes later
tampering independently detectable. Existing `OpportunityWitness` records join to this context;
existing Action-specific evidence remains the sole authority for EXECUTED.

The candidate installs bounded producers only at existing engine-owned boundaries:

- fixed-cost unsupported activation availability during represented main-phase option generation;
- exact permanent departure during authoritative zone movement;
- artifact-entry/dependency evaluation at a typed entry event;
- represented counter replacement evaluation before counter mutation;
- counterspell response availability at the engine-owned Priority window;
- reached unsupported instruction and represented target/choice availability after actual spell
  resolution.

Repeated observation of the same source/subjects/boundary in one turn step deduplicates. Separate
events, objects, Stack identities, or turns remain separate contexts.

## Conservative exclusions

This checkpoint does not claim applicability for variable or unpayable costs, hidden-zone search
results, arbitrary target grammars, unsupported timing permissions, nonrepresented replacement
events, multiple-blocker/deathtouch assignment, Equipment attachment, Cycling resolution, token
copies, or a compound condition whose truth is not established by an authoritative boundary.
Those remain PRESENT / UNREACHED unless a bounded producer proves them. Static inventory alone can
never promote them.

The canonical conformance stop record normalizes `illegal_mutation`, `unclassified_reach`, and
`silent_approximation` outcomes for the future parameterized runner. It is evidence tooling only;
it does not authorize or execute Stage #002.

## Gate

The candidate must pass an independent instrumentation acceptance audit before Readiness Audit
#03. The Stage #002 design, Readiness Audits #1/#2, decks, Pilot, and gameplay remain unchanged.
No Stage #002 match has been run.
