# Action #21 Continuity Audit

Baseline: `2a6137f1546886357d66ba0588a53b409f3756c2`
Accepted Action #21 merge: `00cc29ca541b3d1cc9534d952f8600602ebd1120`

## Finding

Action #21 production code and focused tests are still present. The current authoritative card snapshot
contains Donatello, Way with Machines with the exact Oracle fragment:

`Whenever an artifact you control enters, put a +1/+1 counter on Donatello.`

The accepted recognizer in `card_interpreter07.py` only accepts a source reference equal to `this creature`,
`this permanent`, or the full card name (`Donatello, Way with Machines`). For the current fragment,
`artifact_entry_self_counter_semantic_coverage(...)` returns `fully_supported=False` with
`artifact_entry_counter_unsupported`. The trigger registration path requires `fully_supported`, so it
correctly enqueues no Action #21 trigger.

A direct production reproduction with the authoritative catalog and a controlled artifact entry produced zero
`ARTIFACT_ENTRY_SELF_COUNTER` stack objects. The first failure is therefore current Oracle/source-reference
recognition; Stack/Priority resolution and counter delivery are never reached.

## Stage #002 witnesses

The fresh post-Action #24 artifact reports the same semantic as REACHED / UNSUPPORTED in these two distinct
games (duplicate reports are present for the 32-execution matrix):

- `donatello-krang:canonical:7201`
- `donatello-krang:reversed:7202`

Both carry `oracle_ability_not_implemented` and the current fragment above.

## Validation

- `tests/test_artifact_entry_counter_action.py`: **3 passed**
- Fresh post-Action #24 Stage #002 artifact: 16 games / 32 executions, duplicate-equivalent, 0 invariant
  violations, 0 runner stops.
- No gameplay, deck, pilot, calibration, or measurement code was changed by this audit.

## Resolution

This is a production/evidence continuity mismatch caused by the accepted Action #21 recognizer's overly narrow
source-reference handling relative to the authoritative current Oracle wording. It is not evidence that the
artifact-entry engine path was deleted or overwritten. Action #25 remains unauthorized pending independent
review of this audit and any separately scoped continuity correction.
