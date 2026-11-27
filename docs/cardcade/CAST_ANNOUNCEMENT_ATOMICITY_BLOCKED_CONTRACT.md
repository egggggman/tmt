# Cardcade cast-announcement atomicity — bounded candidate STOP checkpoint

**Classification:** BLOCKED — no production correction implemented or accepted.
**Authority:** HQ authorization for an isolated, bounded correction candidate, conditioned on safe ledger/Stack/RulesEvent/trigger/witness/log restoration. This report records the implementation stop required by that condition.
**Source base:** `main` at `3ca09fc53728047a64ead77866660f379c6cea13`.
**Existing failing reproducer:** [draft PR #434](https://github.com/egggggman/tmt/pull/434), head `415cd2762b8c6435c314dd1c51619dd46c8b451f`, `tests/test_restricted_spell_payment.py::test_spell_cast_event_failure_preserves_preannouncement_state`. Preserve that branch and its exact-SHA RED evidence; do not edit or overwrite it.
**Governance:** [HQ Issue #387](https://github.com/egggggman/tmt/issues/387). No games, smoke, calibration, CI/workflows, merges, frozen deck changes, archive access or authorization keys.

## Confirmed evidence and its limit

At PR #434 exact SHA, the owner ran only the named injected-failure test: **1 failed**, with the *first* authoritative fingerprint equality assertion failing after a synthetic `_process_artifact_spell_cast_triggers` exception. Lint and formatting passed. Subsequent assertions about each ledger, Stack and evidence collection **were not reached**, so their independent failures are not confirmed by that run. This establishes a bounded exception-atomicity defect under injection, **not** a proven naturally occurring card-resolution error.

Read-only source inspection at the above `main` identifies:

1. `Game._commit_announcement_payment` revalidates a plan, taps source lands, moves the source card into a new Stack incarnation, then calls `floating_mana.commit_payment`. The existing local `except` only handles *payment-commit exceptions*, not the later `_record_spell_cast_event` call.
2. `FloatingManaLedger.commit_payment` mutates `_remaining`, `_consumptions`, `_committed_allocation_keys`, `_committed_payment_ids`, and `_revision`. Its public `snapshot()` and `fingerprint_state()` are observations, not transaction rollback; no validated general restore/undo API was found in this read.
3. `_new_rules_event` updates `_next_event_number`, `_rules_events`, `_rules_event_evidence`, event logs, and possibly adds witnesses for existing semantic occurrences.
4. `_enqueue_trigger` may register semantic occurrences and opportunity witnesses; it increments `_next_trigger_number`, appends to `_triggers` and `pending_triggers`, and logs `trigger_pending`.
5. `_put_pending_triggers_on_stack` drains a selected pending batch; creates and registers triggered ability Stack objects and logs `trigger_stacked`. These mutations must not destroy preceding authentic queue/Stack history when undoing a failed cast.
6. The ordinary authoritative fingerprint includes zone IDs, Stack object IDs and the mana fingerprint, but **does not cover every event registry, log, trigger registry, witness or semantic occurrence**. Fingerprint equality alone is not full proof of rollback.

## Interface-only transaction design proposal — for review, not implementation

**Status:** Proposed interface contract only. It is not evidence that the current engine can satisfy the contract, and it grants no implementation authority. The current direct-mutation engine does not provide this seam. Review this contract and its state ownership before separately authorizing any implementation.

### Proposed interface

```text
prepare_cast(request) -> PreparedCast | Rejected
commit_cast(prepared) -> CommitResult | Rejected
abort_cast(prepared, reason) -> Aborted
cast_outcome(transaction_id) -> Prepared | Committed(result) | Aborted(reason)
```

`PreparedCast` is opaque and single-use. It binds a transaction ID, base state-root identity/generation, original card handle and exact source container/index, touched mana-source handles and tapped values, exact payment plan and ledger authority/revision, and a private candidate state containing the proposed zone, payment, event, trigger, witness, Stack, and evidence deltas. It must not expose provisional IDs or evidence through public Game APIs.

The proposal requires a single authoritative `GameStateRoot` (or an equivalent single atomic publication boundary) that owns all mutable state listed below. Existing objects retain stable identity handles; mutable values such as zone, tap state, and collection membership are represented in the root. Readers, snapshots, reconciliation, and trigger processing must read one root generation consistently. Trigger discovery and event construction used during preparation must operate on the private candidate/pure transition interface, never mutate the live Game.

### Operation ownership and allowed mutations

| Operation | May modify | Must not modify |
|---|---|---|
| `prepare_cast` | Its private `PreparedCast` workspace only; optional non-authoritative in-flight token bookkeeping | The authoritative root or any live object field; ledger lots/consumptions/revision/plan authority; zones, tapped state, `_objects`, Stack, or ID counters; RulesEvent registries/evidence; logs; semantic occurrences/witnesses; trigger registries/queues/anchors; spell-payment evidence |
| `commit_cast` rejected or failing before publication | Private candidate/workspace and terminal transaction outcome bookkeeping only | The authoritative root. Rejection, invariant failure, or injected failure before publication leaves the prior root identical |
| `commit_cast` successful | Exactly one complete next root, published once after validation | Any partial live mutation before publication; deletion, truncation, rewriting, or ID reuse affecting preexisting history |
| `abort_cast` before publication | Private workspace and its transaction outcome only | Any authoritative or historical state; it never “undoes” by popping global lists or resetting counters |
| `abort_cast` after publication | Nothing; reject as already committed | The committed root or its evidence |

The successful next root may contain only the attempted cast's coherent deltas across these current engine structures:

- **Card/object state:** original card handle moved from its exact zone/index into the new Stack incarnation; player zone ordering; touched mana-source tap values; `_objects`; `stack`; `_next_object_number`.
- **Mana ledger:** remaining production lots, consumption records, committed allocation keys, committed payment IDs, revision, and unchanged ledger plan-authority relationship.
- **Cast evidence:** `_rules_events`, `_rules_event_evidence`, `_next_event_number`, `spell_payment_evidence`, and the corresponding `rules_event`/`cost_paid` log records.
- **Derived trigger evidence and state:** semantic occurrence registrations, new witnesses attached to preexisting occurrences, witness/cursor counters, `_triggers`, `pending_triggers`, `_next_trigger_number`, any effect-specific trigger anchor maps, newly registered triggered ability objects, their IDs, Stack order, and `trigger_pending`/`trigger_stacked` logs.
- **Transaction outcome:** the transaction ID and final committed result, so a retry can discover the outcome instead of consuming the payment twice.

All collections in the candidate preserve existing element/object identities and ordering; the candidate adds or updates only records caused by this cast. Preexisting event, witness, trigger, payment, log, card, and Stack identities are retained. No global truncate-to-length rollback is permitted.

### Commit and abort invariants

1. Preparation validates the exact payment and cast preconditions against one root generation, then stages all consequences—including event witnesses for existing semantic occurrences and any trigger-to-Stack materialization—without publishing them.
2. Commit revalidates that the prepared base root and exact object handles are still current. It builds the complete next root privately, checks its invariants and payment/event/trigger linkage, and then publishes it with one root swap under the engine's single-writer/reader synchronization rule. The root swap is the commit point and the final potentially failing operation.
3. If any operation fails before that swap, the old root remains the only visible root. Abort discards the candidate; no payment consumption, cast event, trigger, witness, Stack ability, log, evidence record, or counter advance becomes observable. Since the ledger revision and authority did not change, an unexpired plan can remain valid only if the exact base root is still current; otherwise it is rejected as stale.
4. Once the swap occurs, the cast is committed and must be reported/queryable as committed; it cannot be reported as an aborted cast. A later caller failure must resolve through `cast_outcome(transaction_id)`, not by reversing published historical evidence.
5. Snapshots and reconciliation must serialize one root generation. They can therefore observe either the complete pre-cast state or the complete committed cast, never a payment without its cast evidence or a trigger/event without its payment linkage.

This design depends on moving all listed mutable state behind the publication boundary and keeping staged transition code free of live side effects. If that ownership boundary cannot be implemented without cloning/replacing authoritative object identities, or if any observer can see staged state, this proposal is not safe and requires a different architecture decision before coding.

### Proposed synthetic tests (not executed)

- `test_cast_prepare_is_authoritative_state_pure`: compare root identity, all authoritative counters/collections, ledger plan validity, and existing object identities before and after prepare.
- `test_cast_abort_discards_candidate_without_publishing_evidence`: inject failures during each candidate-build phase; assert identical root and unchanged preexisting event, witness, trigger, Stack, log, and payment evidence identities/order.
- `test_cast_abort_preserves_original_card_index_and_payment_plan`: verify exact object/zone/index/tap state and ledger revision/authority; verify stale-root rejection after an intervening committed action.
- `test_failed_cast_never_exposes_partial_event_trigger_or_payment`: read snapshots/reconciliation at each failure boundary and assert no contradictory cast/payment/trigger linkage is observable.
- `test_cast_commit_publishes_one_coherent_state_generation`: assert a successful cast exposes exact payment, event, trigger, witness, logs, and Stack references together while preserving preexisting identities and APNAP order.
- Rerun the preserved PR #434 named injected-failure node and selected successful Punks/Pizza/Ravenous composition nodes only after a separate implementation authorization; these remain unrun at the design stage.

## Minimum proposed correction contract (NOT implemented)

A valid scoped cast-announcement transaction must restore, after the injected failure:

- The identical original card object, source zone and **exact list index**, `zone` value, touched mana-source tap states, original `_objects` registration map, next object ID, and preexisting Stack identity/order.
- Ledger remaining lots, consumption records, allocation keys, committed payment IDs, exact revision and authorization relationship; existing plans must neither become falsely reusable nor spuriously stale because of the failed cast.
- RulesEvent registry/evidence and event counter, all cast-derived logs, preexisting log contents, trigger registry/ID counter, pending queue identity/order, created triggered ability registrations, and cast-created semantic occurrences/opportunity witnesses plus their counters.
- Any already-existing, authentic event, trigger, witness, Stack object or payment evidence must survive with identical identity and ordering. No deleting pre-existing history, replaying fabricated events, changing card identities, or widening card-name exceptions.
- On success, preserve current Punks → Pizza → Ravenous semantics, exact payments, APNAP trigger order, priority and reconciliation. The correction must preserve the existing accepted payment failure rollback from merged PR #433.

**Critical unresolved design seam:** a ledger consumption commit is independently finalized before cast-event/trigger registration. The current inspected ledger exposes validation and observation, but not a proven reversible commit mechanism that preserves its private revision and plan authority. Separately, `_new_rules_event` may append witnesses to **preexisting** occurrences, while trigger delivery may register new ability objects. Appending a zones-only `except` risks leaving contradictory evidence or silently invalidating prior plans. A whole-Game clone/restore is also not justified because object identity is authoritative.

## Narrow synthetic acceptance plan (NOT executed)

On a separately authorized implementation candidate with an exact new SHA:

1. First rerun only the imported/named PR #434 failure node; require same RED before applying any correction.
2. Exercise injected failure immediately after the mana commit, after RulesEvent registration, after trigger enqueue, after ability Stack registration, and after payment-evidence append. For each: compare original card identity and index, entire Stack identities/order, all tapped source states, full ledger fingerprint **and committed ID/allocation keys**, object/event/trigger/semantic/witness counters, prior and current evidence content, and log record identity.
3. Include nonempty **preexisting** trigger queues, event history, witnesses and Stack entries to ensure undo is scoped to the attempted cast rather than truncating authentic history.
4. Validate exact payment-plan behavior after rejection and before retry; prevent double allocation, ID reuse or falsely accepted forged plans.
5. Run selected existing successful Punks/Pizza/Ravenous composition nodes, and isolated reconciliation/invariant nodes; require identical successful events and no fabricated EXECUTED claims.
6. Run Ruff check/format and `git diff --check` on the isolated branch. Capture exact source and tool versions, logs, RED/GREEN results, skips and traceback. **Do not run full games, broad pytest, smoke, calibration, workflows or CI.**

## Stop decision

**BLOCKED for a safe production correction in this checkpoint.** No trustworthy reversible ledger-commit protocol or verified comprehensive event/trigger/witness undo seam has yet been established, and no executable isolated project checkout is available in this environment for the required named synthetic checks. Rather than introduce an unverified multi-system undo that might compromise historical evidence or source identity, this isolated branch contains **only this review document**. PR #434's RED candidate and the merged engine are untouched.

**Smallest next HQ gate:** independently review/approve a concrete **transaction-undo protocol contract** scoped to ledger + existing occurrence/witness and trigger mutations, including exact ownership and fail-closed invariants; then authorize a separately testable narrow implementation at a pinned SHA. If a safe API cannot be demonstrated, prefer a later architecture decision rather than pretending a zones-only patch is sufficient.

**READY/BLOCKED:** Source inspection **READY**; transaction restoration implementation **BLOCKED**; all gameplay/launcher/calibration gates **BLOCKED**.


## Revision — Modular, scalable architecture comparison (HQ direction; design only)

**Source inspected:** `main` `3ca09fc53728047a64ead77866660f379c6cea13`; engine `src/tmnt_design_studio/engine07.py` blob `98baebde735fd6f124d789cdee3daaa134fe783b`; mana ledger `src/tmnt_design_studio/mana_ledger07.py` blob `2028c453128b6330db3ebd1cfb2d1d2bbd254d9b`. This is a **targeted cast-path map**, not a proved exhaustive whole-engine mutation audit. No executable code, tests, games, or workflows changed or ran.

### Non-negotiable architecture qualities

- **Modularity:** each subsystem owns its staging and validation contract. The coordinator cannot mutate the ledger's private fields or forge RulesEvents and witnesses.
- **Scalability:** the transaction *interface* must compose future operations (activated abilities, tokens, combat) without implementing those families now. Avoid card-name-specific exceptions.
- **Identity:** original authoritative runtime object identity, object ID provenance, payment-plan authority, and preexisting evidence identity/order are preserved; copies of mutable `CardObject`/`Permanent` are never published as a silent substitute for originals.
- **Observability:** readers must never observe a partially published cast. In-process atomicity is not crash durability; power loss and durable transaction journals remain outside this gate.
- **Incrementality:** first prove one exact cast transaction boundary with a named synthetic reproducer; no wholesale refactor unless a narrow boundary is shown infeasible.

### Verified targeted reader/mutator map

| Owner / data | Cast-path writer(s) verified in source | Readers / observation surfaces verified | Necessary boundary or unresolved leak |
| --- | --- | --- | --- |
| Zones, card incarnation, tap state, `_objects`, object allocator | `_commit_announcement_payment` (11094), `move_object` (1778), `_register` (1552), `_allocate_object_id` (1547) | `_authoritative_container`, `is_authoritative`, `authoritative_state_fingerprint` (12854), `snapshot` (13056), general actions | Live mutable card/permanent fields and lists preclude a private candidate that directly reuses mutable objects. Stage identities + deltas, never mutate originals during prepare |
| Restricted mana lots, consumes, committed payment IDs, ledger revision/authority | `FloatingManaLedger.commit_payment` (`mana_ledger07.py` 243); `Game._commit_announcement_payment` (11094) | `validate_payment`, `fingerprint_state` (ledger 622), `snapshot` (ledger 475), `Game.snapshot` | Ledger has no proven undo, staging or root-swap API. Need ledger-owned **pure prepared payment delta** bound to original authority/revision; no cloned ledger authority and no caller private-field edits |
| RulesEvents, event evidence, logs, event counter | `_record_spell_cast_event` (11212), `_new_rules_event` (2847), `log` (2036) | `_authenticate_original_rules_event` (3014), `Game.snapshot`, reconciliation consumers | Event construction currently eagerly publishes and may attach witnesses. Introduce event-subsystem-owned pure draft and authentication against a candidate view |
| Semantic presence + opportunity witnesses/counters | `_register_semantic_occurrence` (2124), `_record_opportunity` (2398), `_witness_from_event` (2771) | `_validate_opportunity_applicability`, `snapshot` and reconciliation | Some *preexisting* occurrences acquire new witnesses: candidate overlay must express append-without-mutating original, preserve old identity and original ordering |
| Trigger registries, pending queue, triggered ability Stack objects and counter | `_enqueue_trigger` (4032), `_put_pending_triggers_on_stack` (4259), `_process_artifact_spell_cast_triggers` (11227) | stack/priority and trigger-validation consumers, `snapshot` | Trigger materialization drains existing pending queue; staging must not move or clear existing objects until publication, preserve APNAP order and anchor relations |
| Payment evidence + cost log | `_commit_announcement_payment` (11094) | `snapshot`, reconciliation | Must be committed with spell event, ledger and trigger linkage, never logged as complete before all other results are valid |

**Scale caution:** source-wide static occurrence scan found `self._objects` on 155 lines, `self.stack` 63, `self._rules_events` 30, `self.events` 25, `self.floating_mana` 22 and `self._triggers` 18 in `engine07.py`. These are **text occurrences, not a complete mutator classification**. A mandatory prerequisite to claiming full reader isolation is an enumerated write/read call-graph audit, including activated abilities, Sneak (`_commit_sneak_announcement` at 11254), `move_object` elsewhere, game snapshots and Stage 002 reconciliation. No claim of exhaustive coverage is made here.

### Alternatives and decision

| Criterion | Whole-`GameStateRoot` publication | Cast-scoped staged coordinator / overlay |
| --- | --- | --- |
| Publication model | One root-generation swap after migrating **all** mutable readers/writers | Transaction-specific private deltas, with one *narrow* publication boundary across touched subsystem owners |
| Identity / existing APIs | Requires indirection for mutable identity-bearing `CardObject` and `Permanent` fields and all observations | Keeps preexisting live object references; staged mutations are declarations, applied only at commit after complete validation |
| Ledger authority | Must move existing ledger semantics into root without replacing its private `_plan_authority` | Ledger owns validated staged payment delta and publication; exactly one ledger revision change per committed payment |
| Migration radius | Broad: snapshots, reconciliation, combat, activation, token and direct collection readers/writers | Potentially smaller for one cast, **but cannot honestly promise one-step atomicity while existing direct readers can interleave with several live writes** |
| Current evidence | Not implemented or proven | Not implemented or proven |
| Recommendation | Contingency if staged coordinator cannot safely publish | **Preferred first research/proof target** for modularity and smallest meaningful change |

**Critical boundary choice:** The previous `prepare_cast` / `commit_cast` root-swap contract remains a *conditional target*, not an accepted API. An overlay cannot safely claim atomic publication merely by applying a sequence of deltas to current publicly mutable Game fields. A bounded coordinator is viable only if (a) one engine-owned single-writer rule forbids reentrant casts/observers at commit and (b) all supported snapshot/reconciliation/public getters and callbacks are prevented from observing midway, or (c) touched state is redirected through a single published cast-state handle. The correct choice requires an audited reader/mutator ownership map and a proof of non-observability before any implementation. In-process single-thread Python execution alone is **not** proof because callbacks may reenter.

### Proposed public interface and ownership refinement (NOT implemented)

```text
Game.prepare_cast(request, expected_generation) -> PreparedCast | Rejected
Game.commit_cast(prepared) -> CommitResult | Rejected
Game.abort_cast(prepared, reason) -> Aborted | AlreadyCommitted
Game.cast_outcome(transaction_id) -> InFlight | Committed | Aborted | Unknown
```

- `PreparedCast` is single-use and opaque; Game owns transaction token creation and an **in-process-only** outcome registry. The token binds original Game identity, base generation, original authoritative object handles, prior indices/taps and the exact ledger plan authority/revision. Never issue public provisional object IDs.
- The coordinator requests **subsystem-owned drafts**: `ledger.prepare_payment_delta(plan)`; object/zone planned move and tap delta; event/semantic draft; trigger/Stack materialization draft; payment evidence/log draft. These are **conceptual contracts**, not code or evidence of existing methods.
- If any prepare or commit validation fails *before publication*, discard only private drafts and record Aborted. The previous source state and all authentic event history remain untouched. If a current engine mutator can run during staging, its effect must invalidate the prepared generation rather than be overwritten.
- A commit needs a verified indivisible visibility boundary for all touched state. The published cast and its in-process transaction outcome must be observed together; `cast_outcome` must report Committed even if the caller experiences a **postpublication** failure. No rollback after publication, no repeated ledger spending from retry.
- No guarantee of persistence across process crash, power loss, filesystem persistence, or multi-process observers. If recovery beyond this process is desired, design a separate durable log/claim protocol and seek new HQ approval.
- Existing PR #433 rejected-payment handling remains the compatibility baseline: a failure **before any successful commit** must leave source identity, mana lots and state unchanged. The Punks → Pizza → Ravenous successful cast must retain authentic RulesEvent/event cursors, APNAP trigger order, payment identity and reconstruction.
- **Legacy terminology correction:** earlier sections say “restore after injected failure” because they describe the *current eager-mutation defect*. Under the proposed staged protocol, prepublication failure means **discard unpublished candidate**, not retroactive restoration of already observable state. Postpublication exceptions mean **Committed**, not Aborted.

### Independent review gates (before implementation)

1. Is there a demonstrably complete cast-scoped reader/mutator boundary, including `snapshot`, fingerprint, Stage 002 reconciler, trigger callbacks, and `_commit_sneak_announcement` compatibility? If not, **BLOCKED**, not an optimistic overlay.
2. Can subsystem-owned staged deltas preserve real `_plan_authority`, payment revision, object identity, witness references to existing occurrences, APNAP trigger ordering and all preexisting queue history?
3. Can publication and `cast_outcome` be linearized at one in-process commit point without reentrancy, ambiguous retries or double spending?
4. Does the design permit the PR #434 injected postpayment failure to become a private prepublication failure without inventing an external card-resolution failure?
5. Are broader future families modular design inputs only, rather than silently authorized implementation work?

**Verdict for this revision:** Documented architecture comparison **READY FOR INDEPENDENT REVIEW**; chosen publication/reader boundary **NOT VALIDATED**; implementation, testing, gameplay, calibration and merge **BLOCKED**. Do not describe this document as accepted architecture or an implementation authorization.

