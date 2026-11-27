# Cast-Scoped Isolation Proof Packet

**Status:** Design-only proof packet; implementation remains blocked.  
**Purpose:** Give independent review an exact seam inventory and publication proof for the post-payment cast atomicity defect.  
**Repository:** `egggggman/tmt`  
**Branch:** `review/cardcade-postpayment-cast-event-atomicity-repro`  
**Accepted base:** `66fb857272365c1427450797ffdf69003365192c`  
**Design revision under review:** `2cb458df73e82e8384d20103b8fa34e924d6e00f`  
**Gameplay/calibration:** Not authorized.

## 1. Boundary under review

One cast announcement is one transaction:

```
prepare (read-only) -> commit against isolated state -> final gate -> publish once
                                      \-> abort (publish nothing)
```

The transaction begins before the first payment, zone, object, event, trigger, evidence, or log mutation. It ends only after cast-event creation, trigger delivery, invariant checks, and the post-state fingerprint pass.

The synthetic RED is an injected downstream failure after restricted payment has committed. It demonstrates an atomicity defect in the current path, not incorrect ordinary spell resolution.

## 2. Cast-reachable seam inventory

The following inventory is the proof scope. Any reader or writer not in an allowlist must fail closed while the cast transaction owns the writer guard.

### Readers used by prepare and commit

| Seam | Read contract | Isolation requirement |
|---|---|---|
| `payment_plan` / cast legality | timing, priority, source, target, cost and payment-plan authority | read-only prepare; revalidate against the same pre-state |
| `FloatingManaLedger.validate_payment` | lots, amounts, restrictions, allocations and revision | read-only; staged ledger only after prepare |
| `_objects`, authoritative containers, `is_authoritative` | card/source/target incarnation and zone authority | transaction view; no live provisional lookup |
| Zones, battlefield, stack, priority | membership, ordering, controller and legal targets | snapshot/staged view only |
| `_authenticate_original_rules_event` | event schema, source and provenance | consume staged event; never publish an intermediate event |
| interpreter fragments / token semantic coverage | applicable trigger fragments and token characteristics | evaluate against staged view; no callback to live observers |
| invariant and fingerprint functions | pre/post identity and authority checks | pre-state and staged post-state; public reads blocked during commit |
| serializer / telemetry / pilot view callbacks | externally visible state | prohibited during provisional phase; post-commit only |

### Writers in the current path

| Writer | Current mutation | Required transaction owner |
|---|---|---|
| source/permanent tap state | payment-source `tapped` fields | staged scalar/journal entry |
| `move_object` | zone lists, card zone, object registration, Stack and log effects | staged zone/object bundle |
| `FloatingManaLedger.commit_payment` | lot consumption, allocations, committed IDs, revision | staged ledger with commit receipt |
| `_new_rules_event` | `_rules_events`, evidence and event counters | staged event map/evidence/counters |
| `_enqueue_trigger` | trigger map, trigger IDs and pending queue | staged trigger map/queue |
| `_put_pending_triggers_on_stack` | Stack ordering and pending-trigger publication | staged Stack |
| spell-payment/cast evidence | `spell_payment_evidence` and related arrays | staged evidence lists |
| `Game.log` | `events` gameplay log | staged log; success records published last |
| semantic witness/context writers | occurrences, opportunity witnesses/contexts, stop records | staged append-only records |

### Re-entrancy and callback boundary

The cast path reaches `_record_spell_cast_event`, `_process_artifact_spell_cast_triggers`, interpreter/token-fragment evaluation, trigger enqueue/delivery, invariant/fingerprint calls, and potentially serialization/telemetry or pilot observers.

The current source does not prove an isolation barrier: `move_object`, ledger commit, event creation, trigger delivery, evidence append, and logging mutate live state. Therefore a journal on live objects alone is insufficient. During the proposed transaction, all listed callbacks must either:

1. receive the transaction view and write only to its staging area; or
2. be rejected by the writer guard until publication is complete.

A nested cast announcement, second writer, serializer, pilot read, or public action-generation call during commit must fail closed.

## 3. Exact publication mechanism

Use a cast-scoped `CastIsolationContext` with an exclusive writer token and a transaction-owned publication bundle.

### Prepare

`prepare` performs no authoritative mutation. It validates source/card/target identity, timing, priority, payment authority, and preconditions; captures an immutable pre-state fingerprint/snapshot; and reserves transaction-local IDs. It must not tap, consume mana, move cards, register Stack objects, append events/evidence/logs, or enqueue triggers.

### Commit against isolated state

All fallible work executes against staged/copy-on-write state:

- retain references to pre-existing card/permanent objects; stage their mutable scalar changes and container membership;
- stage new Stack objects, RulesEvents, triggers, counters, evidence and logs with transaction-local IDs;
- stage a ledger copy carrying the same lot IDs, allocations and revision, then produce a commit receipt;
- route every mutation through the context so no direct live write is possible;
- keep the writer token held; reject re-entry and public observation.

Object identity rule: pre-existing authoritative objects are never replaced or cloned. The staged bundle carries references to those same objects plus journaled scalar/container deltas. Newly created objects are unpublished until the final gate.

### Final gate and publication

After payment, zone movement, cast-event creation, trigger delivery, evidence construction, and all invariants succeed:

1. compute the staged post-state fingerprint;
2. verify the pre-state fingerprint still matches the guarded owner and the ledger receipt is consistent;
3. build one publication bundle containing only transaction-owned deltas;
4. while the exclusive writer token remains held, synchronously publish that bundle (swap staged containers/maps/counters/ledger/evidence/logs as one guarded operation);
5. mark the transaction committed and release the token.

Python-level container swaps are not treated as magically atomic. The proof requirement is that the single writer guard blocks every public observer and callback for the entire synchronous publication window; no thread, pilot, serializer, or re-entrant action path may observe between swaps. If that cannot be demonstrated, the design is rejected and must use a stronger isolation mechanism.

### Abort

Any exception before publication discards the staged bundle and releases the token. Authoritative state remains the exact pre-state: zones/order, object identities and counters, Stack, ledger lots/allocations/revision, RulesEvents/evidence, triggers/queue, semantic witnesses, payment evidence, and gameplay logs. Abort is idempotent. No compensating success event is written.

This proves a failed cast cannot publish contradictory combinations such as spent mana with card in hand, a Stack spell without a cast event, or a trigger without authenticated provenance.

## 4. Proof obligations for independent review

Synthetic-only tests must demonstrate:

- exclusive writer contention fails closed;
- nested/re-entrant cast and public observer access fail closed;
- prepare is mutation-free;
- injected failures at payment, after payment, after move/Stack creation, after cast-event creation, during trigger delivery, and during evidence/log publication leave the authoritative pre-state fingerprint unchanged;
- existing Stack, trigger queue, event log, ledger, and evidence remain byte-for-byte unchanged after abort;
- pre-existing card/source object identity is preserved by successful publication (`is` checks);
- ledger lot IDs, revision and allocations are authoritative exactly once; failed casts consume nothing;
- successful casts publish exactly one payment, event, trigger set and evidence record;
- repeated abort is harmless;
- the successful Punks -> Pizza -> Ravenous composition matches the pre-transaction path byte-for-byte;
- forged, stale, or cross-transaction provenance is rejected.

No gameplay simulation, calibration, deck change, baseline change, or historical artifact rewrite is part of this packet.

## 5. Recommendation and gate

**Recommendation:** authorize only a separately reviewed, synthetic proof implementation after independent acceptance of this packet. Do not authorize production semantics, gameplay, smoke tests, or calibration yet.

Any implementation branch must be based on the exact packet/design revision accepted by HQ, not directly on main or the earlier probe head.
