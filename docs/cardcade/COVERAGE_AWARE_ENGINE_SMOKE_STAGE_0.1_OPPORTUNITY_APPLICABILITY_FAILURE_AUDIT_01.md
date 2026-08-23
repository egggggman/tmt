# Coverage-Aware Engine Smoke Stage 0.1 Opportunity-Applicability Failure Audit #1

## Verdict

**VALID FAIL-CLOSED STOP — bounded engine semantic-registration/event-provenance ordering defect.**

The authoritative `CREATURE_ENTERED` event really establishes applicability for the self-ETB fragment. The validator correctly rejects the currently inconsistent registration cursor. Do not weaken the validator or bypass witness authentication.

No implementation or test changed during this audit. No Smoke game was rerun.

## Frozen evidence

- Execution baseline: `16c99daf778b13bb446231e4fe9dd3e1adcd8a8e`
- Manifest digest: `247169fa22f946682ef82408a9b18876637798504d624c63857a7026c735fcb0`
- Failure artifact SHA-256: `be47d78c62874e3fe8f73c1ffffe71d3270089be1440a211551bf907e77254b3`
- Failure sidecar: independently authenticated
- Accepted aggregate: false
- Success artifact: absent
- Game: `april_oneil--bebop_rocksteady:canonical:8001`
- Duplicate/execution: first / ordinal 1
- Completed games: zero
- Last state: turn 16, precombat main, empty Stack, no Priority
- Last state fingerprint: `d2e1a4f41195f2250f65ca61a637814fdeb2bc0d7d8439ec3a489074499f31a9`

The atomic-write environment gate passed before execution and the failure artifact was preserved correctly. Persistence is not implicated in this stop.

## Exact semantic path

The traceback proves the failing path:

`resolve_top_of_stack → _process_creature_entered_triggers → _new_rules_event(CREATURE_ENTERED) → _witness_from_event → _record_opportunity → _validate_opportunity_applicability`

The deterministic first-game context and the prior lifecycle failure identify the resolving card as **Mutagen Man, Living Ooze**, controlled by the Bebop & Rocksteady seat. Its relevant fragment is:

> When Mutagen Man enters, create X Mutagen tokens. (They're artifacts with "{1}, {T}, Sacrifice this token: Put a +1/+1 counter on target creature. Activate only as a sorcery.")

Mutagen Man is the first-game legendary creature whose supported ETB token path can reach an SBA boundary and make a newly resolved duplicate nonauthoritative, which caused the prior stop. The accepted ordering correction now registers this exact fragment while the new battlefield incarnation is authoritative.

The failure artifact intentionally preserves only the last state summary rather than the complete failing snapshot, so the exact allocated runtime object ID and event ID are not independently recoverable after process exit. This audit does not invent either identifier. Their structural relationship is reconstructive from the traceback and predicates: the occurrence source is the sole subject of the new `CREATURE_ENTERED` event.

## What the event proves

Before reaching the failing final predicate, the accepted validator proves all of the following:

- the occurrence source is a registered `Permanent`;
- its fragment index/hash/text matches authoritative Oracle data;
- the event ID resolves to a real stored rules event;
- event subject IDs exactly match the proposed witness subjects;
- `event.battlefield_authority` maps the occurrence object to its controller;
- event kind is `CREATURE_ENTERED`;
- the fragment matches the bounded self-ETB grammar `^When .+ enters,`;
- the occurrence object is an event subject;
- the live source zone is battlefield.

Those facts genuinely establish that the represented self-ETB opportunity occurred. The producer is not joining mere presence, an unrelated event, a different source, or a later ETB.

## Why validation rejects it

`SemanticOccurrence.registration_event_cursor` is frozen as `_next_event_number - 1` at registration time.

Historically, unsupported presence was registered after the ETB event. If that event was number `N`, the next counter was `N+1`, so the stored cursor was `N`. `_witness_from_existing_events()` and the validator therefore required the ETB event number to equal the cursor.

The accepted lifecycle correction moved registration before ETB creation so the source could not become stale during synchronous trigger/SBA processing. Immediately before event `N` is created, `_next_event_number` is `N`; registration therefore stores `N-1`. `_new_rules_event()` then sees the occurrence and proposes the truthful event `N`, but the validator still requires `N == N-1` and rejects it with:

`event does not establish semantic applicability`

Every substantive applicability fact passes. Only the cursor convention is inconsistent with the new truthful lifecycle order.

## Defect ownership

- Engine rules-event generation: **authoritative and correct**
- Event-to-occurrence producer: **correct to propose this exact self-ETB join**
- Applicability validator: **correct under its old post-event registration contract; must not be broadly weakened**
- Smoke reconciliation: **not reached and not implicated**
- Defect layer: **engine semantic-registration/event-provenance coordination**

Stage #002 carried the same latent cursor assumption, but its accepted paths registered self-ETB presence after the event and then used `_witness_from_existing_events()`. It therefore never exercised a pre-event occurrence joined prospectively by `_new_rules_event()`.

## Smallest correction

Preserve both required truths by ordering the lifecycle as:

**authoritative battlefield incarnation → authoritative CREATURE_ENTERED event → register semantic presence against that incarnation and just-completed event → detect/deliver ETB triggers → Stack/Priority/SBA processing**

This keeps registration before any synchronous trigger or SBA can remove the permanent while restoring the exact event cursor/occurrence relationship expected by the accepted validator. The event producer or creature-entry helper should expose the narrow registration point between event creation and trigger detection. Do not accept arbitrary `N+1` events, remove the cursor equality, or special-case Mutagen Man, legends, tokens, decks, or Smoke.

Required regressions:

1. the exact just-created self-ETB event authenticates the occurrence and witness;
2. a prior or later same-source/same-shape event cannot be borrowed;
3. a permanent removed during subsequent ETB/SBA processing retains the occurrence and authenticated witness;
4. surviving permanents remain unchanged;
5. stale/fabricated/relinked sources and events fail closed;
6. Alliance/later-entry and attack-event cursor rules remain unchanged;
7. direct Create Token and non-spell entry paths retain existing behavior.

## Gate

Preserve the raw failure JSON, sidecar, gate report, and this audit unchanged. Implement only the bounded registration/event ordering correction, freeze it for independent acceptance audit, and rerun Smoke Stage 0.1 from game #1 only after integration and merged-main validation.

Action #14, calibration, Pilot/deck changes, Prototype 0.3, and the historical 900-game smoke remain blocked.
