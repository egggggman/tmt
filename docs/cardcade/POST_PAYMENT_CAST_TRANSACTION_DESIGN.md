# Post-Payment Cast Transaction Interface Design

**Status:** Design only — review required before implementation  
**Scope:** `Game._commit_announcement_payment` and downstream spell-cast event/trigger delivery  
**Baseline:** Main `66fb857272365c1427450797ffdf69003365192c`  
**Probe source:** PR #434 head `415cd2762b8c6435c314dd1c51619dd46c8b451f`  
**Gameplay:** Not authorized

## 1. Confirmed failure boundary

The synthetic RED injects an exception in `_process_artifact_spell_cast_triggers` after restricted mana payment has committed. The first failed assertion is the authoritative fingerprint:

- expected: `ba7e935962638d85384802f7819e264b410dc5fa78e866e7368373ef5d2eb506`
- observed: `d1661fdac7f8bdde29ea0fc3763866318335e5332cbacc0fae21e6f688b59cb1`

This is a confirmed atomicity defect for downstream failure injection. It is not evidence that ordinary successful spell resolution is incorrect.

## 2. Transaction boundary

One cast announcement is one transaction:

```text
prepare -> commit (all-or-nothing) -> success
                     \-> abort (exact pre-state) -> exception
```

The transaction starts before any payment, zone, object, event, evidence, trigger, stack, or log mutation. It ends only after cast-event creation and trigger delivery complete and post-commit invariants pass.

No caller may publish a payment, spell-cast event, trigger, or stack object outside this boundary.

## 3. Proposed interfaces

Illustrative interfaces; names are intentionally implementation-neutral.

```python
@dataclass(frozen=True)
class CastTransactionPlan:
    card_id: str
    controller: int
    cast_kind: CastKind
    target_id: str | None
    payment_plan: PaymentPlan
    precondition_fingerprint: str
    reserved_object_ids: tuple[str, ...]
    reserved_event_ids: tuple[str, ...]


@dataclass
class CastTransaction:
    plan: CastTransactionPlan
    snapshot: CastPreState
    journal: CastMutationJournal
    phase: Literal["prepared", "committing", "committed", "aborted"]


def prepare_cast(game, card, plan, *, cast_kind, target_id) -> CastTransaction:
    ...


def commit_cast(game, tx: CastTransaction) -> SpellCastEvidence:
    ...


def abort_cast(game, tx: CastTransaction, error: BaseException) -> None:
    ...
```

### prepare

`prepare` is read-only with respect to authoritative game state. It may:

- validate card/source identity, controller, zone, target, timing, priority, and payment-plan authority;
- read hand, library, graveyard, exile, battlefield, stack, rules events, evidence, trigger queues, and the floating-mana ledger;
- calculate the exact payment and cast deltas;
- capture an immutable pre-state snapshot and pre-length/cursor markers;
- reserve transaction-local IDs without publishing them to game state.

It must not tap lands, consume mana, move the card, create a stack object, append an event, append evidence, enqueue a trigger, mutate semantic witnesses, or write a gameplay log.

### commit

`commit` is the only operation allowed to mutate authoritative state. It applies all mutations through the transaction journal in a deterministic order:

1. commit the validated payment with an undo token or ledger snapshot;
2. tap/payment-source mutations;
3. move the spell from its authoritative zone to stack;
4. allocate and register the stack object;
5. create the authenticated `SPELL_CAST` rules event;
6. deliver artifact-cast and other applicable triggers;
7. append spell-payment/cast evidence and gameplay log entries;
8. run invariants and compute the post-commit fingerprint;
9. mark the transaction committed and return evidence.

If any step raises, `commit` must call `abort` before re-raising. There is no partially successful return.

### abort

`abort` is idempotent and may run exactly once for a committing transaction. It restores the transaction's exact pre-state, not merely selected fields:

- authoritative card zones and original list positions;
- source/permanent identity and land tap state;
- `_objects` additions and `_next_object_number`;
- stack contents and stack ordering;
- floating-mana lots, remaining amounts, consumption allocations, committed payment IDs, revision, and plan authority;
- `_rules_events` and event cursor/ID allocation;
- semantic occurrences and opportunity witnesses;
- `_triggers`, pending trigger queue, and trigger ordering;
- spell-payment/cast evidence;
- gameplay `events` log and any related evidence arrays.

Pre-existing objects and evidence must be restored byte-for-byte. Only transaction-owned additions or edits may be removed. A failed transaction must not append a compensating gameplay event that could be mistaken for an authentic cast.

## 4. Existing-structure ownership

| Existing structure | prepare | commit | abort |
|---|---|---|---|
| Player zones / card order | read + snapshot | move source once | restore exact prior lists/index |
| `_objects`, object counter | read + reserve local IDs | publish new stack object | remove transaction-owned objects; restore counter |
| `FloatingManaLedger` | read/validate | consume via reversible operation | restore exact lots, allocations, IDs, revision |
| Stack | read + snapshot | append one stack object | restore exact stack/order |
| `_rules_events` / event cursor | read + reserve local IDs | publish cast event | remove transaction-owned events; restore cursor |
| Semantic occurrences/witnesses | read | append only authenticated transaction records | remove transaction-owned records |
| Trigger map/queue | read | enqueue/deliver transaction triggers | remove transaction-owned triggers; restore order |
| Spell/payment evidence | read | append after all fallible delivery succeeds, or journal append | remove transaction-owned evidence |
| Gameplay `events` log | read | append success records only after commit succeeds | remove transaction-owned records; no fake success |
| Invariants/fingerprint | read | final gate | verify exact pre-state on failure |

The implementation should prefer immutable snapshots plus transaction-owned journals over ad hoc field-by-field rollback. Ledger rollback must be first-class; restoring zones alone is insufficient.

## 5. Atomicity proof obligation

Let `S0` be the complete authoritative pre-state and `T` the transaction journal. Every commit mutation must be either:

- recorded in `T` before mutation, or
- applied to a transaction-local staging object and published only at the final commit point.

For any exception `e` before the commit gate:

```text
abort(T, e)
authoritative_state(game) == S0
published_success_evidence(game) == prior_success_evidence(S0)
```

Therefore a failed cast cannot leave “mana spent + card still in hand,” “spell on stack + no cast event,” “cast event + no trigger provenance,” or “trigger queued + no authenticated source.” The only durable output may be an external failure/diagnostic record explicitly classified as non-gameplay evidence.

The implementation must test both the authoritative fingerprint and each mutation family because the current RED stops at the first fingerprint assertion.

## 6. Required review fixtures

Before implementation approval, review must agree to these cases:

1. successful artifact spell cast with restricted mana;
2. injected failure during payment;
3. injected failure after payment but before zone move;
4. injected failure after zone move/stack creation;
5. injected failure after `SPELL_CAST` event creation;
6. injected failure during artifact-trigger delivery;
7. injected failure during evidence/log append;
8. pre-existing stack, events, triggers, and evidence remain unchanged on abort;
9. repeated abort is harmless;
10. successful Punks -> Pizza -> Ravenous composition is byte-for-byte equivalent to the pre-transaction path.

## 7. Explicit non-goals

This design does not authorize:

- production code changes;
- gameplay, smoke, or calibration runs;
- deck changes;
- Baseline 005/R9-B changes;
- historical artifact rewriting;
- broad simulator transaction redesign beyond the cast-announcement seam.

## Review request

Approve or reject this interface contract before implementation is authorized. The next implementation should be a bounded seam change with focused synthetic tests only.
