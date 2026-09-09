# Krang hand-refill bounded authorization audit

**BOUNDED FEASIBLE.** The exact ETB hand-refill can reuse ordinary Trigger/Stack/Priority, the accepted intervening-if pattern, authoritative hand/library identities and single-card Draw. Local additions are exact recognition, an immutable entry-hand condition anchor, a resolution-time hand/count capture, a bounded Draw transaction and its reconstruction gate. No generic variable-draw interpreter or conditional-trigger framework is indicated. Action #32 implementation remains NOT AUTHORIZED pending HQ.

Exact source/evidence head: `cd1362e62c2aabbc7d11edd3e7d90af9ea5cd0be`; clean main confirmed. Audit only: no production/test/deck/Pilot/runner changes, no tests and no Stage/Smoke or other simulations. This is a source-inspection feasibility finding, not passed implementation proof.

## Recognition boundary

Frozen catalog `cardcade/scryfall-tmt-pza-tmc-2026-08-13.json` records Krang, Master Mind as Legendary Artifact Creature ? Utrom Warrior, Oracle ID `52562194-4a97-40d2-aa73-7827f7834f2f`; print IDs `3942f813-6241-49f5-8df3-e60e2e332410` and `d27fa497-e842-4812-80fe-28517544e1c5` share the text.

> When Krang enters, if you have fewer than four cards in hand, draw cards equal to the difference.

Recognize this complete self-ETB form with fixed threshold four, strict fewer-than comparison and exact draw-difference payload on a creature source. Follow existing self-reference recognition: the printed source token must match the card's name or short name. An otherwise equivalent renamed source with the correspondingly renamed self-reference can retain semantics; unrelated names must fail closed. Do not dispatch by deck, pairing, Oracle ID or hard-coded card identity. No arbitrary threshold, generic numerical expression, alternate trigger/condition/player, optional draw, additional effects or new reminder-text grammar. Affinity and Krang's other-artifact power bonus remain untouched.

Rules cross-check: an intervening-if condition must hold when the event occurs and again on resolution; false at creation means no trigger, while false on resolution means no effect. Multiple draws occur individually. Existing source-departure and deferred SBA behavior must remain intact. See Wizards' [Comprehensive Rules, June 19, 2026](https://media.wizards.com/2026/downloads/MagicCompRules%2020260619.pdf), 603.4, 608.2a, 121 and 704. This version was inspected as a stable rule reference, not a catalog update or claim of the latest rules edition.

## Two condition checks and the measured player

At the actual creature-entry event, freeze controller C from the entering permanent and its original event authority. Measure C's authoritative hand after the creature has entered; a normally cast Krang has already left hand. Do not use owner, active player, opponent, later controller or a pre-cast hand count. Record hand IDs, ownership/card associations, count, event/source/controller and condition result in an independent immutable anchor at this boundary, before any ETB payload changes the hand.

If entry hand size is four or more, record condition-false inspection evidence but enqueue no trigger. A later discard does not retroactively create one. If below four, enqueue exactly one ordinary trigger for that source incarnation/event/fragment. Do not re-test the live hand when merely putting the already-created trigger onto Stack; response effects can change it again before resolution. Protect the creation-time condition even if the source later leaves or the hand changes.

At actual authorized all-pass resolution, recheck the same frozen controller's current authoritative hand. Capture h once and set n = max(0, 4 - h). If h >= 4, finish an authenticated condition-false/no-Draw outcome. If h < 4, fix n (1 through 4) for this resolution and perform those sequential Draw attempts. Do not reuse the creation-time deficit, recalculate n after each card, or run a draw-until-hand-size loop. Other responses may change h between entry and resolution; that is legitimate and must affect n.

Examples: entry h=3 followed by resolution h=1 requests three draws; entry h=0 followed by resolution h=4 performs none; entry h=4 followed by a discard has no trigger at all. These are required future test cases, not simulations run by this audit.

## Existing code seams and bounded additions

- `card_interpreter07.py::etb_artifact_draw_semantic_coverage` (973) already validates a fixed self-ETB intervening-if form. Add only the hand-refill recognizer, not a condition AST or variable-draw language.
- `engine07.py::_detect_creature_entered_triggers` (5383/5454) conditionally enqueues ETB artifact Draw. `_validate_etb_artifact_draw_provenance` (5266) authenticates original event/source/controller and separately checks current conditions; `_resolve_triggered_ability` (4337) implements resolution-time condition failure. Reuse the lifecycle pattern, not its artifact predicate.
- `_new_rules_event` records battlefield authority/characteristics but not an immutable entry hand. A Krang-specific entry-hand anchor is necessary. Store it at event detection, not at later trigger delivery, and bind it to independent original event evidence. No general RulesEvent hand-snapshot redesign is required.
- `vigilante07.py` and `mill_three07.py` provide original source/trigger/Stack anchors, immutable transaction histories, consumed-state checks, source-departure handling and all-pass guards.
- `Game.draw` (5896), `move_object` (1563) and `FailedDrawStateBasedAction` (1026) provide Draw movement/new incarnations, failure marking and subsequent loss. The refill needs no chooser, shuffle or RNG.
- `process_priority_resolution` (6335), protected `resolve_top_of_stack` (8255), and existing trigger delivery already run ETBs. Add this effect to all applicable protected resolver/drain guards; no new Priority windows, scheduler or runner policy is needed. Frozen runner source-hash bookkeeping may later change with an authorized implementation; its matrix must not.

## Sequential Draw and short libraries

Use the actual Draw primitive, never mill movement or manual hand append. On success, each current library-top CardObject moves to hand under reason draw, receives a distinct hand incarnation and emits card_drawn. Preserve preexisting hand order and the untouched library prefix. Let L be bottom-to-top library storage and H the hand before resolution; successful draws append newly allocated incarnations of reversed(L[-k:]) to H in order, where k is the number actually drawn. Handle k=0 explicitly rather than slicing with -0.

Important implementation seam: `draw(player, count)` returns immediately at its first empty-library failure. It does not log every remaining attempted draw. To evidence the exact fixed number of sequential attempts without changing shared Draw semantics, a local bounded loop can call `draw(player, 1)` n times, record each result, and not short-circuit on False. Maximum n is four. This reuses existing failure behavior and needs no generic Draw architecture. Do not recompute n or insert Priority/SBAs between calls.

An empty-library attempt sets failed_draw_pending and emits draw_failed; successful earlier draws stay committed. Record requested count, attempted count, successful count and failures separately. Empty/short libraries are normal semantic outcomes, not malformed-transaction rollback cases. Existing unrelated failed_draw_pending must not be cleared by this handler. Ordinary post-resolution SBA consumes the flag and determines loss; do not end the game inside the draw loop or fabricate missing hand objects. Do not label partial/failed refill as a successful four-card refill.

Prevalidate identities, zone containers, source/Stack authority and allocation dependencies before any Draw. Runtime tampering or relinking must not leave a partially mutated malformed transaction: reuse local prevalidation and, if needed, rollback of only touched zones/registry/allocator/event records. Do not roll back genuine empty-library outcomes or introduce a global transaction system. Future replacement-draw or additional draw-trigger support is outside this bounded action.

## Source departure and ordinary delivery

After a true creation condition, source departure does not cancel the trigger. Retain original source/card/event/controller authority and allow the registered source to be former. The original controller's hand remains the subject even after source control changes or reentry. A new battlefield incarnation can create a separate trigger; duplicate replay of the old event cannot.

The existing legend-rule/SBA boundary may remove Krang before its trigger resolves; that must not erase the already-created trigger. Recognize the trigger at entry before intervening ETB payloads or SBA delivery can lose the creation state. No Draw, hand/library movement or RNG use before the original trigger reaches Stack and matching all-pass resolution. Entry-time hand capture is evidence, not early Draw execution.

## Complete reconstruction and conservative credit

A dedicated immutable entry/transaction ledger plus validator is a required local addition. Existing generic trigger_resolved evidence cannot certify this fragment. The live execution index and serialized Stage `_authoritative_execution_index` must both require the mature exact chain:

1. Original unique creature-entry event, source incarnation/card, controller, exact fragment and immutable entry-hand IDs/count; join hand state to prior authoritative movement history. Prove the creation condition, including records for suppressed false-condition entries.
2. For a true condition, unique trigger and Stack anchors, chronology and controller; preserve source-departure provenance. Reject fabricated, duplicate, relinked or replayed event/trigger/Stack IDs.
3. Matching Priority epoch, real pass sequence and permission for the specific top Stack object; reject direct/early resolution and borrowed pass evidence.
4. Immutable resolution pre-hand/pre-library identities and condition; derive h and n independently. Authenticate legitimate hand changes since creation without accepting a substituted player or mutable count summary.
5. Exactly n ordered single-card attempts for a true condition, each successful zone_changed/card_drawn pair with original-to-new identity and owner, or a proven empty-library draw_failed with pending flag. No missing/extra/reordered/borrowed draws or destination IDs.
6. Exact post-hand/library order and membership, untouched prefixes, requested/attempted/successful/failed totals, and preserved RNG state. A false resolution condition has n=0 and no Draw events.
7. Consumed transaction/trigger completion, deferred SBA consequences if any, and later legitimate movement continuity. Event ledger and original anchor mutations must fail rather than rebuilding trust from an edited final summary.

Credit policy proposed for HQ: terminal-pending and creation-condition-false cases never receive EXECUTED merely from ETB. Resolution-condition-false outcomes remain explicitly distinguishable and conservatively do not certify a refill. A fully reconstructed n-attempt transaction can certify execution even when genuine failed-draw behavior occurs, but must expose failed/partial outcome and subsequent SBA rather than imply n successful cards. Never credit generic trigger resolution, equal duplicates, count-only evidence or recomputed outer hashes. If HQ instead requires successful refill for EXECUTED, freeze that policy explicitly; do not silently conflate it with transaction execution.

Negative proofs must mutate both duplicate snapshots and recompute outer hashes: forged hand counts/IDs, wrong player, changed entry or resolution condition, stale/relinked source, altered n, duplicated/borrowed draw or movement records, missing failure, altered prefixes, premature SBA, missing ledger, replayed commit and generic-only reference must fail semantic joins. Sidecars anchor preserved artifact provenance; reconstruction is not cryptographic proof against wholesale invention of an internally consistent history.

## Evidence exposure and required future validation

The preserved Smoke reports seven reached-unsupported Krang occurrences across six games, joined to creature_entered events. Unlike the Tunnel Rats battlefield-activation witnesses, these identify the correct triggering zone and event. Generic entry witnesses alone do not prove the hand-size condition. The table below therefore reconstructs the entry hand from existing chronological zone_changed records, starting with empty hands before setup Draw. This is read-only artifact analysis, not a new run and not a hypothetical post-implementation result. It does not predict resolution-time h after adding new draws.

Full compressed and decompressed result sidecars were verified. Existing official labels/counts and artifacts remain unchanged. Future instrumentation must make hand-condition proof explicit at creation rather than relying on generic ETB opportunity credit.

Required future focused proofs: entry hand sizes 0/1/2/3/4/>4, resolution threshold crossing in both directions, count fixed at resolution, both controllers and changed active player, source departure/control change/reentry/legend-rule departure, ordered sufficient/short/empty libraries, preexisting failed-draw flags, deferred SBA, all-pass/direct/drain guards, equal-valued distinct identities, duplicate/stale/relinked/fabricated records, all three no-trigger/no-effect/executed outcomes, and complete positive/negative reconstruction. Required candidate validation remains an HQ authorization decision; no tests were run here.

## Recommendation and stop boundary

**BOUNDED FEASIBLE** with only exact recognition, fixed hand-threshold capture/check, at-most-four single-card Draw attempts, protected ordinary ETB delivery and full evidence integration. No generic variable-draw scripting, broad conditional-trigger architecture, new zones, scheduler, Priority overhaul, Pilot redesign, deck changes or unrelated rule expansion is necessary from inspected seams. Stop for HQ if implementation exposes any such dependency rather than broaden this packet.

Tunnel Rats remains deferred. Action #32 implementation remains NOT AUTHORIZED. Calibration remains BLOCKED; Prototype 0.3 remains NOT AUTHORIZED.

## Existing entry-hand reconstruction

Four entries across three games satisfy the creation condition (hand sizes 2, 2, 3, 3). Three entries across three other games do not (4, 6, 4). This narrows proven condition-true exposure without changing the official seven-occurrence/six-game inventory. Full chronological hand reconstruction was also cross-checked against final hand identity/order in all six saved game snapshots. These observations do not predict fresh post-implementation counts.

| Game | Entry event | Source | Controller | Hand size | Condition <4 | Hand IDs |
| --- | --- | --- | ---: | ---: | --- | --- |
| donatello--krang:canonical:8049 | event-000053 | object-000246 | 1 | 4 | False | object-000133, object-000192, object-000233, object-000242 |
| donatello--krang:reversed:8049 | event-000050 | object-000240 | 0 | 6 | False | object-000152, object-000164, object-000175, object-000179, object-000201, object-000234 |
| donatello--krang:canonical:8050 | event-000032 | object-000207 | 1 | 4 | False | object-000130, object-000133, object-000168, object-000181 |
| donatello--krang:reversed:8050 | event-000032 | object-000208 | 0 | 2 | True | object-000190, object-000205 |
| donatello--krang:reversed:8050 | event-000035 | object-000215 | 0 | 2 | True | object-000190, object-000213 |
| krang--leonardo:canonical:8061 | event-000058 | object-000269 | 0 | 3 | True | object-000123, object-000215, object-000238 |
| krang--michelangelo:reversed:8063 | event-000029 | object-000200 | 1 | 3 | True | object-000134, object-000168, object-000197 |
