# Cast Isolation Proof Packet — Revision 3

**Status:** Design/proof only; production implementation remains blocked pending independent acceptance.  
**PR:** #434 (draft)  
**Base design:** `2cb458df73e82e8384d20103b8fa34e924d6e00f`  
**Gameplay/calibration:** Not authorized.

This revision closes the three review gaps identified by HQ: reader isolation, object identity preservation, and ledger authority. It does not change simulator semantics.

## 1. Reader isolation proof

### Isolation state

Each `Game` has a cast guard with:

- owner transaction token;
- phase: `idle | preparing | committing | publishing | aborted | committed`;
- re-entry depth, required to remain zero for public entry points;
- staged transaction view;
- observer policy: `BLOCK` while committing/publishing, `TX_VIEW` only for allowlisted private helpers.

The guard is acquired before the first authoritative mutation and released only after commit or abort.

### Cast-reachable readers

The following readers are allowlisted:

| Reader | During prepare | During commit |
|---|---|---|
| payment/timing/priority/target validation | authoritative pre-state | transaction view only |
| `FloatingManaLedger.validate_payment` | authoritative ledger snapshot | staged ledger |
| `_objects`, `is_authoritative`, zone containers | authoritative identity map | transaction identity map |
| `_authenticate_original_rules_event` | not called | staged event/evidence only |
| interpreter/token semantic coverage | read-only | staged transaction view |
| invariant/fingerprint functions | pre-state | staged post-state |
| public action generation, pilot, serializer, telemetry | permitted before prepare | rejected while provisional state exists |

Any unlisted reader fails closed. There is no fallback to live `Game` state during commit.

### Proof condition

A reader-isolation test installs an observer at every mutation seam (payment, move, event, trigger, evidence, log, and publication). Each observer must either be rejected by the guard or receive the transaction view; it must never observe a partially mutated authoritative `Game`. The test records an observation trace and asserts no provisional fingerprint is emitted.

This is stronger than rollback: the pre-state is never exposed as a contradictory intermediate state.

## 2. Object-identity proof

### Identity rules

1. Every pre-existing authoritative runtime object has an immutable identity key: `object_id` plus Python object identity for the lifetime of the transaction.
2. Prepare records an identity map for all touched cards, permanents, Stack objects, events, and trigger sources.
3. Staging never deep-copies or replaces a pre-existing authoritative object.
4. Mutable scalar changes (zone, tapped, controller, damage, counters) and container membership are staged as deltas against the same object instance.
5. New Stack objects, RulesEvents, triggers, and evidence receive transaction-local IDs and remain unpublished until the publication gate.
6. A publication identity audit asserts that every pre-existing object still satisfies `published_object is pre_object`; only explicitly new objects may be newly registered.
7. An incarnation change (zone departure/re-entry) uses a new object identity and cannot alias a stale reference.

### Proof tests

- Successful cast: pre-existing source, target, and payment permanents pass `is` identity checks after publication.
- Failed cast at every seam: all pre-existing object identities, zones, ordering, and object-number cursor match the pre-state.
- Forged or stale object reference: rejected without mutation.
- New Stack/event/trigger objects: absent before publication, present exactly once after publication.

The proof therefore preserves both object identity and Magic incarnation identity; it does not rely on equal-valued copies.

## 3. Ledger-authority proof

### Authority contract

The authoritative ledger is a single `FloatingManaLedger` owned by `Game`. A transaction may not mutate it directly during staging.

Prepare captures:

- base ledger revision;
- exact lot IDs and remaining amounts;
- payment-plan ID and allocation map;
- controller and restriction scope.

The transaction owns a staged ledger copy and a provisional `LedgerCommitReceipt`. The receipt contains the base revision, consumed lot IDs, post-allocation amounts, and a unique transaction ID.

### Commit and abort rules

- A ledger commit is accepted only when the authoritative revision still equals the receipt base revision and every lot ID is still authoritative.
- The commit operation is single-writer and idempotent by transaction ID; a second commit or duplicate allocation fails closed.
- Ledger publication occurs only inside the final publication bundle, after all trigger/evidence/invariant work succeeds.
- Abort discards the staged ledger and receipt; authoritative lots, allocations, committed-payment IDs, revision, and payment-plan authority remain byte-for-byte unchanged.
- A stale receipt, forged lot ID, mismatched controller, or duplicate transaction ID is rejected before publication.
- Successful publication advances the revision exactly once and consumes each authorized lot exactly once.

### Proof tests

- Restricted-mana cast consumes the expected lot IDs once.
- Repeated commit cannot consume again.
- Stale-revision commit fails closed.
- Forged/missing lot IDs fail closed.
- Injected failures after provisional payment leave the authoritative ledger fingerprint and revision unchanged.
- Successful publication contains exactly one authoritative payment evidence record.

## 4. Publication sequence

The bounded sequence is:

```
acquire cast guard
  -> prepare read-only snapshot
  -> stage payment/zones/Stack/events/triggers/evidence
  -> run staged callbacks and invariants
  -> identity + ledger receipt audits
  -> compute staged post-fingerprint
  -> guarded synchronous publication bundle
  -> mark committed
  -> release guard
```

No public reader, pilot, serializer, or nested cast may run during staging or bundle publication. If the runtime cannot enforce that guard, the implementation must fail closed rather than fall back to live-state journaling.

Abort is idempotent and publishes no gameplay-success delta.

## 5. Independent review gate

This packet recommends authorization of a **synthetic-only proof implementation** based on this exact packet SHA. It does not authorize production gameplay semantics, simulations, calibration, deck changes, or historical artifact changes.

Required acceptance evidence is the synthetic seam-test report for:

- reader blocking/transaction-view routing;
- identity preservation and stale-incarnation rejection;
- single-authority ledger commit/abort;
- failure injection at each mutation seam;
- exact pre-state restoration and zero contradictory publication.

