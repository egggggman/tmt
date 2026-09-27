# Donatello Prototype 0.3a: Way with Machines Coverage

Status: capability milestone; not a balance authorization.

## Authority and exact card text

The canonical card-data source is `cardcade/card-model-0.6.json`. The complete
Oracle text is:

> Flying
> Whenever an artifact you control enters, put a +1/+1 counter on Donatello.

The trigger is unrestricted by turn, triggers once for each qualifying artifact
entry, and applies only to an artifact controlled by the entering permanent's
controller. It puts one `+1/+1` counter on the named Donatello permanent. The
card has no optional choice, target selection, level clause, or additional
artifact-entry restriction. An artifact token qualifies by type and controller;
Donatello entering itself does not qualify because it is not an artifact.

## Semantic support verified

The existing reusable Action #21 permanent-entry event path recognizes the exact
self-counter fragment, records the entering permanent's controller and type,
queues one trigger per qualifying entry, and resolves it against the still-
authoritative source permanent. Existing `place_counters` and characteristic-layer
evaluation provide persistent `+1/+1` counters and updated power/toughness.
Existing stack and rules-event logging records the trigger and
`artifact_entry_counter_resolved` payload deterministically.

The generic combat legality surface now also recognizes the card's authoritative
`Flying` keyword. A flying attacker may be blocked only by a blocker with
`Flying` or `Reach`; ordinary blockers are filtered from legal block options and
rejected by direct combat validation. Static card-data keywords and existing
temporary Reach/Flying effects use the same reusable predicate. AcceptancePilot
receives the filtered legal options and requires no Donatello-specific change.

No new Pilot policy or target chooser is required: the ability names its own
source rather than asking the Pilot to select a target. Existing artifact typing
also covers normal artifact creatures and recovered artifact permanents. Token
support was not broadened in this slice.

## Regression evidence

Focused tests cover recognition, controller/type filtering, multiple entries,
counter persistence and P/T, deterministic event records, and recovered artifact
re-entry. Donatello P0.3a versus Shredder seed 3004 completes without an error;
Way with Machines enters before two qualifying artifact entries, and both produce
the exact counter-resolution event.

The prior representation audit recorded the same artifact-entry text as absent
from the executable surface. This change demonstrates the previously missing
before/after state transition without requiring a winner change.

## Remaining gaps

This artifact does not claim support for:

- Donatello, Gadget Master's combat-damage artifact-copy trigger;
- Donatello, Mutant Mechanic activation/transfer behavior;
- Sewer-veillance Cam abilities;
- Bespoke Bō remaining semantics;
- Does Machines level 3 artifact animation/counters; or
- any other unsupported Donatello card text.

Donatello remains a semantic-coverage and balance question. This is not a balance
claim and does not authorize a smoke rerun by itself.
