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
