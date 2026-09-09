# Paramecia ETB mill-three bounded authorization audit

**Finding: READY FOR BOUNDED AUTHORIZATION REVIEW.** Existing primitives are sufficient for the exact ETB mill-three transaction. No broader zone architecture, generic mill scripting, hidden-zone language or unrelated rule expansion is indicated by this source/evidence audit. Implementation remains NOT AUTHORIZED pending HQ's decision.

Exact evidence/source base: `f51c3e123179aa8262e78f0526055e8622afa79d`. Started from clean main at that SHA. This audit changed no production, test, deck, Pilot or runner files and ran no tests, games, Stage or Smoke simulations. Conclusions are source-inspection findings and a proposed implementation contract, not claims that unimplemented mill tests have passed.

## Frozen recognition boundary

The frozen catalog `cardcade/scryfall-tmt-pza-tmc-2026-08-13.json` records Paramecia Coloniex, Oracle ID `9076a886-efe0-4c99-8661-f0fd7a7b3129`, print ID `654e2646-78ac-4b08-bed1-3c71355d55fc`, as a creature with two distinct Oracle lines. The only proposed supported fragment is exactly:

> When this creature enters, mill three cards. (Put the top three cards of your library into your graveyard.)

Use exact equality against the fragment returned by existing newline splitting, including the reminder text, and require the represented source to qualify as a creature. This is Oracle-derived behavior, not card-name, Oracle-ID, deck or pairing dispatch. Renaming an otherwise equivalent source must not change recognition. Altered quantities, attack/death triggers, opponent/target-player mill, optional mill, extra effects, missing/changed reminder text and noncreature sources must fail closed under this deliberately frozen contract. Do not add parameterized mill-N parsing.

The separate dies/exile/reflexive-return fragment remains untouched and unsupported. Library-to-graveyard movement is not a battlefield death and must not enqueue that sibling. No exile zone or reflexive-trigger machinery belongs in this Action.

The preserved prioritization inventory and its sidecar were verified against committed bytes: 22 reached-unsupported occurrences across 17 distinct Smoke games. Example: `april_oneil--bebop_rocksteady:canonical:8001`, source `object-000186`, occurrence `semantic-000018`, original entry `event-000026`. This establishes exposure, not a promised post-implementation count or calibration outcome.

## Resolution-time identity and movement contract

Let `L` be the controller's authoritative library tuple at actual all-pass resolution, stored bottom-to-top, and `G` its existing graveyard tuple. Freeze object references, IDs, owners and card identities, not names alone. Validate unique registry/zone membership, correct owner/controller-side zone, valid non-token CardObjects, and destination integrity before the first movement.

Define:

- `n = min(3, len(L))`.
- `M = tuple(reversed(L[-n:]))` when `n > 0`; otherwise `M = ()` explicitly. The `n == 0` branch must not accidentally inspect `L[-0:]`.
- `U = L[:-n]` when `n > 0`; otherwise `U = L`.

`M` is frozen top-first. The fourth card is not milled. Library changes between ETB creation and resolution must affect this capture; there is no trigger-time top-card snapshot to reuse. This capture is internal evidence input, not a chooser/public GameView expansion.

For each original in `M`, in top-first order, use existing authoritative `move_object(original, "graveyard", reason=<exact mill transaction reason>)`. Each move appends a new CardObject to the owner's graveyard, preserves owner and original card identity, marks the source library object `former`, and logs source/destination incarnation IDs. It must never remove-and-append the original object directly or fabricate replacement IDs outside the registry.

If the returned new graveyard objects are `N0 ... N(n-1)`, the exact final zones must be:

- library: `U`, with every untouched object/reference and order preserved;
- graveyard: `G + (N0, ..., N(n-1))`, retaining the old prefix exactly;
- one distinct new graveyard incarnation per milled original, with no repeated destination ID or stale source reuse.

For example, library `[u0,u1,c,b,a]` and graveyard `[g0]` become library `[u0,u1]` and graveyard `[g0,a_new,b_new,c_new]`, with movement evidence ordered `a,b,c`. This is the proposed deterministic storage/serialization convention for this bounded transaction; it does not introduce a general graveyard-order chooser or claim that arbitrary mill effects require that order. All movements belong to one resolving effect, with no intervening Priority or SBA pass. No generalized simultaneous-zone event system is required by the represented scope; if implementation exposes an observable missing interaction requiring such a system, stop for HQ rather than approximate it.

Preflight the complete source set, destination prefix, trigger/Stack authority and allocation dependencies before mutation. Each existing move is individually validated; that alone is not proof of whole-transaction failure safety. The future implementation must ensure malformed dependencies cannot leave a partially milled prefix, using prevalidation and, if required, rollback limited to the touched zones/registry/IDs/event records. Do not create a global transaction framework to meet this requirement.

## Milling must not use Draw semantics

`Game.draw` moves a top card to hand and sets `failed_draw_pending` plus `draw_failed` on an empty library. Those are explicitly inappropriate here.

Mill uses only `move_object` to graveyard. Empty and short libraries complete with zero through two movements; no attempted fourth/third missing-card draw occurs. There must be no `card_drawn`, `draw_failed`, hand movement, failed-draw flag creation or clearing, or mill-caused empty-library loss. Existing unrelated failed-draw state must be preserved. Later genuine Draw behavior remains unchanged.

Milling needs neither a chooser nor RNG. RNG object/state/records must remain unchanged throughout the transaction. Do not reuse Jury-Rig's mandatory shuffle record or Courier's search/shuffle policy merely because their identity/evidence machinery is reusable.

## ETB, Priority and source departure

Reuse the existing typed creature-entry event, TriggerInstance, TriggeredAbilityObject and Priority lifecycle. At enqueue, authenticate the original event and source incarnation, exact fragment, subject ID and controller against creation-time battlefield authority. Deduplicate the same entry/fragment/source. A distinct reentry incarnation may create its own legitimate trigger.

Anchor the original source/card, original rules event, trigger and Stack object. After trigger creation, source departure does not cancel the trigger: the registered former source and original event remain valid. Do not require the source still to occupy the battlefield at resolution, and do not transfer the obligation to a new incarnation or a later controller. The trigger's frozen controller identifies the library to mill.

Add the exact effect to the same protected trigger-delivery and all-pass checks used by Jury-Rig/Courier, including direct resolver and compatibility drain paths. Before both players pass, it may create trigger/Stack evidence but must not capture the top milling set, inspect cards for a decision, change library/graveyard, allocate destination incarnations or consume RNG. Revalidate original Stack/trigger authority before popping the Stack object and before commitment; effect-field tampering must not bypass authentication of an already anchored object.

The existing Stage/Smoke drivers already drain these Priority windows. No turn, scheduler, runner timing or Pilot policy change is indicated. A future Smoke frozen-source hash refresh is bookkeeping, not permission to alter its matrix or behavior.

## Required independent transaction reconstruction

A dedicated mill evidence record/ledger and validator are necessary localized additions. Existing generic zone logs alone do not establish that an exact ETB mill transaction executed. Proposed event names are illustrative, not a preexisting API.

The validator must reconstruct:

1. Unique original creature-entered event and its immutable evidence; source subject, controller, creature authority and exact Oracle fragment.
2. Unique pending trigger and Stack object, their source/event/fragment/controller joins, correct chronological ordering and the all-pass permission for that exact Stack object and Priority epoch. Pass records cannot be borrowed from another resolution.
3. An original resolution-time pre-zone record containing `L` and `G` identities/order/card/owner associations, plus `n`, `M` and `U`. Cross-check runtime capture against the authoritative containers and preserve it immutably; serialized checks must join to original records instead of trusting a mutable final summary or counts.
4. Exactly `n` contiguous library-to-graveyard movements in top-first `M` order, each with its authenticated source ID, distinct new destination ID, same owner/card, exact reason and correct zones. No missing, duplicate, extra, reordered, hand-routed or borrowed movement.
5. Final library `U` and graveyard `G + N`, membership cardinality and untouched-prefix preservation. Zero-card milling still needs a completed, authenticated no-movement transaction.
6. Unchanged hand and RNG evidence; no mill-created Draw/failure events or failed-draw mutation. The enclosing normal post-resolution SBA boundary remains unchanged.
7. A unique completed transaction and consumed Stack/trigger marker, followed by the normal trigger-resolution record. Later legitimate zone moves must not invalidate the historical chain or overwrite its recorded post-zones.

Both live `_executed_conformance_references` and serialized Stage `_authoritative_execution_index` need an exact-fragment gate modeled on Jury-Rig: grant the mill reference only after this validator accepts the completed transaction. Generic `trigger_resolved`, arbitrary `zone_changed`, a matching count, two matching duplicate snapshots or matching outer hashes must never suffice. Terminal-pending triggers retain conservative non-EXECUTED classification.

Protect the original pre-state and transaction ledger against live relinking and mutation. For serialized evidence, changing both duplicate copies and recomputing report/aggregate hashes must still fail when entry/Stack/pass/identity/order joins are inconsistent. Committed artifact SHA-256 remains the provenance anchor against wholesale replacement of the original artifact; semantic validators are not cryptographic proof against an entirely invented, internally consistent history.

## Required future negative and positive proofs

These are acceptance requirements for a future implementation; no new tests were written or run in this audit.

| Case | Required result |
|---|---|
| Exact fragment, renamed source, near neighbors, unsupported sibling | Exact-only recognition, independent of card name; dies/exile sibling remains unsupported |
| Both controllers; library sizes 0/1/2/3/4/>4 | Exact `min(3,size)` capture and movements; fourth/untouched cards preserved |
| Library changed after ETB, before all-pass | Capture actual resolution-time top identities |
| Equal-valued distinct cards | Preserve reference/ID distinction and source-to-new-incarnation links |
| Source departure, control change, reentry | Original trigger still mills original controller's library; reentry is independent |
| Duplicate ETB, consumed trigger, replayed resolver | No duplicate milling/commit; reject stale resolution |
| Stale/former/fabricated/relinked source, library card, registry, card identity or destination | Fail before any committed zone change; no partial transaction |
| Forged source/event/controller/fragment/Stack or borrowed Priority epoch | Reject against original anchors and pass chain |
| Tampered movement count/order/card/owner/IDs, pre-zone prefix or post-zones | Reject independently, including synchronized duplicate-copy corruption |
| Missing ledger or generic-only execution reference | Cannot certify EXECUTED |
| Empty/short library, preexisting failed-draw state | No Draw behavior or failed-draw-state modification caused by mill |
| Later legitimate zone movement | Original completed transaction still reconstructs |
| RNG/public view | No RNG consumption or new hidden-zone chooser/public visibility API |

## Primitive sufficiency and proposed boundary

Concrete inspected seams at this exact base:

- `card_interpreter07.py::fragments` splits the frozen Oracle lines; a dedicated exact recognition method is sufficient.
- `engine07.py::_authenticate_original_rules_event` joins unique derived events to independent creation-time evidence; Jury-Rig provides source/trigger/Stack/consumed-identity anchor patterns and source-departure behavior.
- `engine07.py::move_object` validates authoritative identity and unique zone membership, constructs a new destination object, preserves card/owner and logs the incarnation link. Library and graveyard already exist; no new zone is needed.
- `engine07.py::process_priority_resolution`, `resolve_top_of_stack` and `_resolve_triggered_ability` supply all-pass delivery and post-resolution SBAs. Add only the bounded mill dispatch/guard participation.
- `jury_rig07.py` and `food_search07.py` supply original transaction ledger, mutation/provenance and reconstruction patterns; the mill handler requires no chooser/search/reveal/RNG payload.
- `stage002.py` already validates bounded effect evidence before indexing authoritative execution references; `smoke01.py` reuses that reconciliation.

Proposed scope consists only of exact recognition, one ETB effect with authenticated resolution-time mill transaction, localized reconstruction/mutation guards, exact execution-credit integration and the required focused proofs. No generic mill grammar, arbitrary quantities/players, mill-until/reveal choices, graveyard ordering policy framework, exile, recursion, scheduler, turn-engine replacement or unrelated rule support is justified.

**Stop assessment:** no forbidden architectural requirement was found. If future implementation needs a broader zone/simultaneity/replacement system, generic mill scripting, new hidden-zone visibility, or unrelated rule work, stop and return to HQ. This finding does not waive those boundaries.

## Integrity and HQ handoff

Inspected Git blob identities at the exact base:

| Source | Git blob |
|---|---|
| `engine07.py` | `b3dc92dbefe4aaaabda61398d0839d300c01f64f` |
| `card_interpreter07.py` | `fa122270a886ba94942a370149805a162ee1a2b9` |
| `jury_rig07.py` | `0e200a979b33baa80036509f06ff3df2bc73d54d` |
| `stage002.py` | `236312280adb987a0783049ea964a4945fa8ecc2` |
| `smoke01.py` | `5f0d764d3ad96c28dbfd077496fad124859d2f96` |

The preserved prioritization audit/inventory sidecars match their committed bytes. Only this authorization audit and its SHA-256 sidecar are added; staged scope and sidecar bytes are verified before commit. Historical artifacts remain unchanged.

**HQ recommendation: authorize only the bounded exact ETB mill-three scope above if accepted.** No implementation has started. Action #31 remains NOT AUTHORIZED until HQ explicitly grants it. Calibration remains BLOCKED and Prototype 0.3 remains NOT AUTHORIZED.
