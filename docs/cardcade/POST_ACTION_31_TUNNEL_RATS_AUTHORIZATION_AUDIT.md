# Tunnel Rats bounded authorization audit

**Finding: NOT READY for unconditional exact-semantic implementation authorization. Return to HQ for the timing boundary and opportunity-evidence correction.** The self-return transaction appears local and needs no generic graveyard grammar or hidden-zone architecture. However, current activation paths cannot accept graveyard CardObjects, current Priority exposure is incomplete for this unrestricted activation, and the preserved reached-unsupported witnesses do not establish graveyard legality. This is not a finding that a broad zone redesign is necessary.

Exact evidence/source base: `ef1689cd7efb023810f421ea971c128443e82fb3`. Clean main verified before audit. Audit only: no production, test, deck, Pilot, runner, or historical artifact changes; no tests or simulations. Source inspection and existing-artifact analysis are not implementation validation.

## Exact recognition

Frozen catalog `cardcade/scryfall-tmt-pza-tmc-2026-08-13.json`: Tunnel Rats, Creature ? Rat; Oracle ID `0a8e5c48-885d-4ea8-9c68-a3e9213d4289`, print ID `70faf7d8-008a-454a-a21b-702aa661b8f9`.

> {4}{B}: Return this card from your graveyard to the battlefield tapped.

Recognize only this exact complete fragment on a creature card, independent of card name/Oracle ID. No parameterized return grammar, different cost, target, another card, alternate destination, omitted tapped condition, additional effect, or timing instruction. The interpreter currently recognizes fixed-cost activated syntax but leaves this child payload unsupported.

Rules cross-check: an activated ability can be used when its owner/controller has Priority; this fragment functions from the graveyard, has no sorcery restriction or target, and pays before resolution. Activation does not move its source. The activator receives Priority afterward. Zone changes create new objects; an older ability cannot follow a source that leaves and returns. Summoning sickness concerns battlefield attack/tap permissions, not this mana-only activation. See Wizards' [Comprehensive Rules](https://media.wizards.com/2026/downloads/MagicCompRules%2020260819.txt), effective August 7, 2026, sections 113.6, 117, 302.6, 400.7 and 602. The frozen catalog remains the recognition authority; this audit does not update it.

## Material measurement caveat

The committed residual inventory reports 19 occurrences across 16 games. Its sidecar and the compressed/decompressed full Smoke sidecars authenticate. Inspection below joins each occurrence to its original witnesses. All witness source zones are listed; these are recorded exposure classifications, not proof of legal graveyard activations.

`engine07.py::_witness_unsupported_activation_contexts` (6117) only scans authoritative battlefield Permanents and counts available lands against the total mana requirement. It does not establish a black-producing payment. Its `activation_available` contexts therefore cannot certify this fragment's graveyard source or colored-cost legality. Example: `april_oneil--splinter:canonical:8017`, `object-000156`, `semantic-000005`, `context-000001`/`opportunity-000004`, turn 10 precombat main: source and every subject are explicitly on the battlefield. That lineage only later moves to graveyard as `object-000179` on turn 12 combat damage.

Do not overwrite or retroactively relabel the banked aggregate in this audit. Do not infer zero real graveyard opportunities either: these witnesses cannot answer that question. A future exact witness must freeze authoritative graveyard identity, owner, represented Priority permission, and a legal {4}{B} payment. Historical battlefield witnesses must not be converted into successful return evidence or promised continuity counts.

## Existing activation and timing seams

- `activation_payment_plan` (7266) requires `Permanent`, battlefield authority and controller; its land selection and `ManaRequirement(4, ('B',))` construction are reusable. A graveyard CardObject must not be disguised as a Permanent.
- `announce_activated_ability` (7382) hard-codes battlefield authority, `.tapped`, and battlefield indexing even without tap/sacrifice costs. A type annotation change alone is unsafe. Use a dedicated exact-fragment branch or helper sharing fixed payment and ActivatedAbilityObject, while leaving all other source-zone rules intact.
- `legal_activated_ability_actions` (7338) offers only active-player main-phase empty-Stack battlefield actions. `execute_main_action` (6469) rejects non-Permanents. The existing Pilot selects engine-supplied ACTIVATE_ABILITY options, so bounded main-option integration needs no new Pilot strategy.
- `legal_priority_actions` (6260) requires a nonempty Stack and only adds counter activations to passes. `execute_priority_action` (6279) assumes Permanent sources. Adding this exact graveyard response in already represented windows is local, but is not proof of all legal timing coverage.
- `_begin_priority_window` (6400) rejects an empty Stack and always grants the active player Priority. A nonactive player activating in response must retain Priority afterward; blindly using that reset would be wrong. Existing main-only generation must not become an invented sorcery restriction.
- `resolve_top_of_stack` (8255) has an activated all-pass guard. `_resolve_activated_ability` (7700) itself lacks that guard before popping; a protected exact branch must authenticate the matching Stack/epoch at every entry point, including direct calls.

**Concrete authorization blocker:** this engine does not expose general empty-Stack Priority outside the bounded main-action pathway. Supporting every legal timing for Tunnel Rats therefore is not established by existing windows alone. HQ must explicitly choose a bounded represented-window contract with honest timing limitations, or separately authorize/prove the missing Priority exposure. This audit does not authorize broader turn/priority restructuring. Even under a bounded contract, wrong-player/out-of-window/one-pass calls and stale action options must fail before payment.

## Proposed local payment and source contract

At announcement, require the exact registered non-token graveyard CardObject, its immutable card/owner association, and unique membership in that owner's graveyard. Use ownership as authority; nonbattlefield `.controller` is not an independent permission grant. Reject another owner's card, equal-valued replacement, fabricated registry entry, altered fragment, former incarnation, wrong zone and duplicate membership.

Recompute and authenticate five distinct authoritative untapped controlled land sources, including one producing B and four paying generic, under existing represented mana rules. Revalidate all land identities, controller, untapped status and color immediately before payment. No tap/sacrifice of Tunnel Rats, targets, chooser, library access, RNG or Draw behavior. Insufficient black mana is illegal even with five lands. Do not broaden mana-pool, cost-reduction or generic mana architecture.

Payment taps the chosen lands once and creates one distinct ActivatedAbilityObject plus immutable announcement/payment/source anchors. Preserve the graveyard and battlefield creature membership during payment and before all-pass. On malformed payment/dependencies, restore touched taps, allocation, Stack, registry and records; do not leave a paid-but-unstacked activation. If later legal source departure prevents the effect, costs stay paid.

## Resolution, tapped entry and incarnations

Anchor the original graveyard source ID/object/card/owner when activating; never look up a replacement by name. At matching all-pass resolution, freeze authoritative graveyard and battlefield order and allocation dependencies. If the anchored source still occupies its original graveyard, use `move_object(source, 'battlefield', controller=owner, summoning_sick=True, reason=<exact return reason>)` once. Existing movement (1563) validates registry identity, unique zone membership and former-state rejection, preserves card/owner, creates a new Permanent and marks the source former.

For graveyard G and source at index i, preserve `G[:i] + G[i+1:]`; preserve old battlefield order and append only the new permanent. Retain every untouched reference. The new permanent has a fresh ID, fresh damage/counters/temporary state and current entered_battlefield_turn. Do not reuse the graveyard object or restore old battlefield counters.

`move_object` currently constructs an untapped Permanent and does not itself deliver creature-entry triggers. A bounded handler must establish tapped=True before any observer/entry-event/SBA/priority boundary, then refresh existing static effects and invoke the established creature-entry pipeline exactly once. Source inspection suggests a local uninterrupted move/set-tapped/deferred-entry sequence is sufficient because movement does not emit a battlefield-entry rules event itself; require proof that no observer sees the intermediate untapped state. If necessary, a narrow construction-time tapped argument is an explicit local addition, not a generic replacement-effect framework.

Use `_process_creatures_entered_triggers` (5512), defer delivery until the activation finishes, and normal post-resolution SBA/Trigger/Stack/Priority. Record the new incarnation as the event subject; no cast, spell-resolved, or death event belongs to this return. Existing Alliance/entry watchers must see the actual new tapped creature, without adding unrelated watcher semantics. Existing sickness/untap/combat guards must consume the new state normally. Do not make it attacking.

If the original source legitimately left its graveyard before resolution, consume the ability with an authenticated no-movement outcome. If it left and returned, the new graveyard incarnation is not the old source. Distinguish legitimate departure (with movement chain) from forged/relinked source data, which must fail provenance validation. Reentry after another death can support a newly paid activation of the new graveyard ID.

## Replay and transaction evidence

Do not impose a once-per-card activation rule. With sufficient fresh payment and Priority, two distinct activations of the same still-present graveyard incarnation are valid. The first to resolve may move it; the remaining activation then has no movement. Replaying an already consumed Stack object, reusing a payment record, duplicating a transaction, or using stale option/epoch authority is invalid.

Preserve a dedicated immutable transaction ledger and independent original anchors, modeled on Food activation linkage and mill/Jury-Rig evidence. Reconstruct all of:

1. Original graveyard incarnation birth/movement chain, exact fragment and owner; unique authority and pre-announcement zone membership.
2. Legal announcement timing/player/epoch and fresh Stack identity; exact five-land payment with pre/post taps, colors, ownership and no duplicate payer; untouched source-zone state through payment.
3. Authentic Stack history, responses, Priority grants and two matching passes authorizing this exact resolution. Never borrow permission from another Stack object or epoch.
4. Resolution-time pre-graveyard and battlefield identities/order, anchored source status, exact source-to-new-Permanent movement or authenticated departure/no-movement reason.
5. Original card/owner preserved, distinct new ID, former old ID, tapped entry and fresh sickness/state; unchanged remaining zones and no RNG/Draw consumption.
6. Exactly one linked creature-entry event and correct deferred trigger/SBA boundary for a successful return; none for a no-movement outcome. Later legitimate movements must not invalidate the saved historical transaction.
7. Completed/consumed activation and whole-transaction commit; no orphan, duplicate, missing, relinked, stale or extra payment/movement/entry/commit records.

Live `_executed_conformance_references` and Stage `_authoritative_execution_index` (644) currently allow generic resolved activated evidence. The exact fragment needs a mature dedicated transaction gate in both paths; a generic `resolved=True`, zone_changed log or matching outer hashes is insufficient. Terminal pending and no-movement outcomes must stay distinguishable from completed self-return credit; HQ's candidate contract should conservatively require actual reconstructed return for EXECUTED.

Negative evidence proofs must include matching-duplicate snapshot corruption with recomputed outer hashes, fabricated source/payment/Stack joins, altered tapped or post-zone state, replaced card descriptors and consumed-record replay. SHA-256 anchors establish artifact provenance; reconstruction alone cannot detect wholesale replacement by an entirely invented internally consistent history.

## Required future proofs and stop boundary

No tests were written or run. Any future authorization should require exact/renamed-source and near-neighbor recognition; both owners; valid/insufficient/wrong-color/stale/double-used payment; wrong zone/player/epoch; all-pass and direct-resolver guards; pre-resolution no movement; successful tapped/new-ID entry and unchanged prefixes; relevant entry watcher consequences; no cast/death/Draw/RNG contamination; legal source departure, leave-return and two independently paid activations; replay/fabrication/mutation rejection; full snapshot reconstruction; conservative terminal/no-effect credit; unchanged frozen validation matrices and historical continuity.

The bounded source-zone exception, fixed payment, one-card movement, entry-event integration and transaction evidence can reuse existing primitives. No generic graveyard scripting, hidden-zone grammar, staging zone, exile, target/choice system or new scheduler is indicated. The actual unresolved issues are Priority exposure/retention and the invalid graveyard-opportunity inference. Return those to HQ before implementation; do not force a main-phase-only semantic or repair general timing under this audit.

Action #32 implementation remains NOT AUTHORIZED. Calibration remains BLOCKED; Prototype 0.3 remains NOT AUTHORIZED.

## Preserved witness cross-check

Witness source-zone totals: `{"battlefield": 47}`. These totals count witnesses, not games or occurrences.

| Game | Source | Occurrence | Witness source zones | Witness IDs |
| --- | --- | --- | --- | --- |
| april_oneil--splinter:canonical:8017 | object-000156 | semantic-000005 | battlefield | opportunity-000004,opportunity-000005 |
| april_oneil--splinter:canonical:8017 | object-000171 | semantic-000008 | battlefield | opportunity-000006,opportunity-000007 |
| april_oneil--splinter:canonical:8018 | object-000167 | semantic-000008 | battlefield | opportunity-000002 |
| april_oneil--splinter:canonical:8018 | object-000175 | semantic-000010 | battlefield | opportunity-000003,opportunity-000004 |
| bebop_rocksteady--splinter:canonical:8034 | object-000194 | semantic-000018 | battlefield | opportunity-000011,opportunity-000012 |
| bebop_rocksteady--splinter:reversed:8034 | object-000141 | semantic-000001 | battlefield | opportunity-000001 |
| casey_jones--splinter:reversed:8047 | object-000271 | semantic-000018 | battlefield | opportunity-000009,opportunity-000010 |
| donatello--splinter:canonical:8059 | object-000159 | semantic-000006 | battlefield | opportunity-000003 |
| leonardo--splinter:canonical:8077 | object-000181 | semantic-000007 | battlefield | opportunity-000004,opportunity-000006,opportunity-000008,opportunity-000011,opportunity-000014 |
| leonardo--splinter:canonical:8077 | object-000199 | semantic-000010 | battlefield | opportunity-000009,opportunity-000012,opportunity-000015 |
| leonardo--splinter:reversed:8077 | object-000162 | semantic-000004 | battlefield | opportunity-000001,opportunity-000003,opportunity-000005,opportunity-000007,opportunity-000009,opportunity-000011,opportunity-000013,opportunity-000015,opportunity-000017,opportunity-000019 |
| leonardo--splinter:canonical:8078 | object-000195 | semantic-000007 | battlefield | opportunity-000001 |
| leonardo--splinter:reversed:8078 | object-000156 | semantic-000006 | battlefield | opportunity-000004 |
| michelangelo--splinter:canonical:8083 | object-000223 | semantic-000022 | battlefield | opportunity-000007 |
| michelangelo--splinter:reversed:8083 | object-000151 | semantic-000004 | battlefield | opportunity-000003 |
| michelangelo--splinter:canonical:8084 | object-000173 | semantic-000007 | battlefield | opportunity-000003 |
| shredder--splinter:canonical:8089 | object-000193 | semantic-000013 | battlefield | opportunity-000005,opportunity-000006,opportunity-000007,opportunity-000008,opportunity-000009 |
| shredder--splinter:reversed:8089 | object-000192 | semantic-000012 | battlefield | opportunity-000003 |
| shredder--splinter:canonical:8090 | object-000177 | semantic-000011 | battlefield | opportunity-000004,opportunity-000006,opportunity-000007,opportunity-000008,opportunity-000009 |
