# Pilot Input-Contract Assessment

**Recommendation: BOUNDED FEASIBLE.** A small, versioned, recipient-specific immutable projection can supply the missing observations without changing gameplay semantics or either Pilot's decision policy. This is source-based feasibility, not an implemented or experimentally proven interface. The 96-fixture packet remains incomplete; no quota is declared satisfied and no scoring is authorized.

Exact assessment base: `84beb1b28bd80fd53ab75da8bb566f4f4d2718a1`.
Frozen gameplay reference: `de52f57a24a5c29a258573ad673051a0aa5c7e5c`.
Accepted specification: `ca9757b956eafc4b8d03c495dabb03eaab6fe931`, `POST_ACTION_32_PILOT_FITNESS_ASSESSMENT_SPEC.md`.
Gate audit: `e28cd6dcd5532b84d38c45d3a710077e5cb589b4`.
Only this assessment and SHA-256 sidecar are added. No code edits, simulations, Pilot calls, scoring, deck changes or Stage/Smoke runs.

## 1. Current input inventory and provenance

| Hook | Actual immutable input fields | Options | Construction / ownership |
| --- | --- | --- | --- |
| choose_scry | ScryView: player_index, requested, cards tuple of (object_id, name), in inspected top-first order | ScryOption: top_ids, bottom_ids | engine07.py Game.scry, around 3483; exactly the resolution-time inspected identities. Pilot wired by Stage and Smoke runners. |
| choose_hand_bottom_draw | HandBottomDrawView: player_index, cards tuple of (object_id, name) | HandBottomDrawOption: card_id or None | Game.choose_hand_bottom_draw, around 2881; current own hand. |
| choose_discard_draw | DiscardDrawView: player_index, cards tuple of (object_id, name) | DiscardDrawOption: card_id or None | Game.choose_discard_draw, around 3030; current own hand at instruction point. Draw-first mandatory discard uses draw_discard_chooser, not the Pilot's optional-filter hook. |
| choose_priority | GameView: turn, active_player, phase, step, life pair, hands for both players, battlefields for both players | ActionOption: kind, player_index, object_id, target_id, cost_object_id, oracle_fragment, attacker_ids, blocks, priority_epoch | stage002.py _drain_priority, around 418, calls game.public_view(); Smoke uses the shared Priority drain. |

GameView hand entries are (object_id, name, mana_value, is_creature). PublicObjectView fields are object_id, name, controller, power, toughness, tapped, damage, is_token. There is no Stack description. The ActionOption oracle_fragment describes the offered activation, not the target spell. Private views carry no life, battlefield, hand context beyond their cards, library count, resource summary or turn context.

Authoritative source structures already contain the relevant facts: PlayerState owns life, hand/library/battlefield and lands_played; Permanent carries printed card, current type, evaluated power/toughness, counters, tap/sickness and temporary keyword state. StackObject contains spell card/controller/target_id; TriggeredAbilityObject contains source identity/card, fragment, effect and target_id; ActivatedAbilityObject contains source identity/card, fragment/program and target_ids. No new rule interpreter is needed to copy these facts.

## 2. Minimum schema decision

Recommend **extending the three existing hook-specific immutable filtering views with a required version-2 context**, and **a new narrowly scoped PriorityViewV2**. Share a small recipient-scoped DecisionContextV2 value type rather than duplicating public projections. Do not append unrestricted Game state or raw event history. Retain existing filtering cards/requested fields and existing option types/order so unchanged policies can continue selecting exactly as before.

Conceptual schema (a contract proposal, not code to execute):

- ScryViewV2: existing player_index, requested, cards; context: DecisionContextV2; inspected_cards: tuple of CardDescription matching cards exactly.
- HandBottomDrawViewV2 / DiscardDrawViewV2: existing player_index, cards; context: DecisionContextV2. Own-hand descriptions live in context and must match cards exactly; no duplicate independently sourced hand representation.
- DecisionContextV2: schema_version=2, observer_index, turn, active_player, phase, step, life[2], hand_sizes[2], library_sizes[2], own_hand, battlefields[2], own_lands_played. All nested collections immutable tuples; no live object references, dictionaries, closures or query callbacks.
- PriorityViewV2: schema_version=2, context: DecisionContextV2, priority_player, priority_epoch, consecutive_passes, stack_bottom_to_top: tuple of PublicStackItemV2.

A context is required in assessment V2. A legacy constructor default of None, if needed for a separately retained V1 API, must never silently qualify as V2. Snapshot at the existing choice instruction point, after earlier completed effects and before the chooser runs. No extra Priority window or reevaluation of legality is introduced by building it.

## 3. Field-by-field privacy and necessity

P = currently public observation; O = deciding player's own private information; I = specifically authorized private inspection; M = interface metadata derived only from public/authorized facts. Prohibited information is enumerated separately. These classifications describe the represented face-up model; unknown visibility must fail closed rather than be inferred from registry access.

| Proposed field / nested fields | Class | Why needed / exact source and limit |
| --- | --- | --- |
| schema_version, observer_index | M | Prevent cross-recipient reuse and identify assessment V2. Observer is the chooser/controller, never assumed equal to active_player. |
| turn, active_player, phase, step | P | Distinguish current resource use from later turns and active/nonactive response contexts; copy existing Game fields. No forecast of future turns. |
| life[2] | P | Ground survival and guaranteed-win priorities in forced tactical fixtures. Copy current PlayerState.life; no predicted damage. |
| hand_sizes[2], library_sizes[2] | P | Resource accounting and empty-library boundaries. Counts only, including opponent counts. Do not include library IDs, composition or order. |
| own_lands_played | P | Interpret represented remaining land opportunity using existing per-turn count. Do not claim another land play is legal merely from this field. |
| own_hand tuple | O | Compare inspected cards with retained resources and identify hand-card opportunity cost. Only observer's actual hand; no opponent identities. |
| CardDescription.object_id | O in own hand; I in inspection; P on public Stack/battlefield | Current incarnation, not a future ID or a lookup handle into hidden registry state. |
| CardDescription.name, mana_cost, mana_value, type_line, oracle_text, printed power/toughness, printed keywords | Same as its containing zone's visibility | Immutable copied card facts; needed to avoid name-only tactical oracles and externally privileged catalog knowledge. None for inapplicable power/toughness. Printed text is not a claim that all its rules are executable. |
| inspected_cards and existing Scry cards order | I | Exactly the existing inspected min(requested, library size) set and top-first order; never additional top cards. No retained private inspection history or future Draw identity. |
| battlefields[2] | P | Both boards are needed for threat, blocker and survival judgments; own board alone is insufficient. Restrict to current public permanents. |
| Battlefield row: object_id, owner, controller, card description, current type_line, power, toughness, tapped, damage, is_token | P | Copy current authoritative characteristics. Owner avoids ambiguity in return/cost contexts. Do not expose CardObject or Permanent instances. |
| Battlefield row: counters tuple of (type, count), summoning_sick | P/M | Public counter state and represented control-duration eligibility; copy existing state. Needed to avoid assuming a newly entered creature can attack or pay a tap cost. No new sickness computation. |
| Battlefield row: represented keyword status tuple | P/M | Snapshot existing read-only keyword queries and current temporary effects, with explicitly enumerated supported tags. Do not build a generic continuous-effect engine. Unsupported/unknown status is not false; exclude dependent oracles until scoped. |
| Battlefield row: represented_land_payment_color, land_payment_untapped | M from P | For lands only, reproduce the existing payment model's _mana_color and untapped predicate; color may be null. These are model observations, not new mana abilities or a guarantee of cast legality. |
| priority_player, priority_epoch, consecutive_passes | P/M | Copy PriorityState at its existing owner decision. No hidden timing window or advanced all-pass outcome. Epoch authenticates supplied choices. |
| Stack fields below | P except metadata | Ground legal-response comparisons; no resolution-time private choices or predicted outcomes. |

There is no floating mana pool in PlayerState. Do not invent an available_mana integer, add nonland mana production, or interpret Frog Butler as implemented. Untapped lands and the existing fixed-color payment projection supply the bounded model's resource observations. Existing engine-generated options remain the only authority on what can be paid and played now. Projection must not call legal_main_actions merely to populate context: that method can emit opportunity witnesses. Use read-only fields/helpers without logging, RNG or payment execution.

For the first bounded fixture suite, graveyard/exile contents, a full combat history, arbitrary continuous-effect internals and pending delayed private payloads are not part of this minimum. A fixture requiring them must be reported as an explicit remaining input dependency rather than supplied evaluator-only facts. A new public field may be justified later, but this recommendation is not a blank check to add all zones. Immediate combat outcomes must be grounded in the represented public board and declared oracle horizon; if an actual attack/block assignment is necessary at a filtering instruction point, assess that specific additional public projection before sealing that fixture.

## 4. Exact quota dependencies and limits

The accepted quotas stay 12 per hook (4 forced, 4 resource, 4 boundary), with at least two action-required and two conservative cases, both seats and all transformations. This assessment identifies the facts required to design those cases; it does not supply or certify them.

| Hook | Four forced-case dependency | Four resource-case dependency | Four boundary/pass dependency |
| --- | --- | --- | --- |
| Scry | Inspected descriptions/order plus life, own hand, both boards, resources and step to establish a bounded near-term need using a known inspected card. | Existing hand versus inspected resource utility and represented land/color access; no uninspected-card advantage. | Requested/actual inspected length, hand/library counts and a justified keep/retain case. An empty inspection is a legality boundary, not forced tactical competence. |
| Hand-bottom/Draw | Actual hand, board/life/resources and library count; any guaranteed improvement must follow from visible facts, not an unseen Draw. | Explicit preservation objective among hand identities under represented costs and board needs. | Decline/empty-hand/small-library behavior grounded in actual instruction order. Bottoming into an empty library can Draw the bottomed card; do not import discard/Draw failed-draw assumptions. |
| Discard/Draw | Actual hand, public library count, current threats/resources; determine loss risk and guaranteed consequences independently of hidden top identity. | Identify a retained useful card versus a discard opportunity with a predeclared visible objective. | Decline and empty-library risk; current hand reflects any prior Draw if this view is reused by the non-Pilot mandatory chooser. Do not attribute that chooser to the Pilot. |
| Priority | Public ordered Stack item/effect/targets plus current board/life to establish whether a response averts a loss or preserves a guaranteed win. | Response cost source and threatened resources versus passing, using unchanged options and public spell effects. | Pass-only states, harmless/nonlethal represented effects and equivalent alternatives; epoch and controller for legality. |

A larger view does not make an unknown Draw predictable. There may still be insufficient input-grounded forced useful-filter cases under the no-belief-model requirement. That is an oracle-feasibility question for preparation after interface authorization, not evidence that the projection requires broader architecture. **BOUNDED FEASIBLE applies to the interface change, not a guarantee that all 96 tactical fixtures can be honestly sealed.** If quotas remain unachievable, return to HQ again; never weaken thresholds or declare hidden outcomes known.

## 5. Stack visibility contract

PublicStackItemV2 fields:

| Field | Source / meaning / privacy |
| --- | --- |
| object_id, kind (spell / activated / triggered), controller | Current public Stack incarnation/type/controller; P. Tuple is bottom-to-top so final element is next to resolve. Do not sort by ID. |
| spell_card or source_card: CardDescription | Public announced spell characteristics, or public source characteristics preserved on the ability object; P. Exactly one role identified. No dereference of a departed source into a new hidden incarnation. |
| source_id (abilities; null for spells unless an existing public relation exists) | The publicly known originating incarnation; P. Source departure does not erase the already-public ability or cancel it. Do not expose a private destination ID. |
| oracle_fragment / public_effect_text | Spell's public Oracle text or ability's recorded fragment; P. Copy text rather than synthesize a predicted outcome. Existing effect enum may be included as represented_effect_tag (M), without generic parsing or evaluator advice. |
| targets: ordered tuple of public target references | StackObject.target_id / TriggeredAbilityObject.target_id / ActivatedAbilityObject.target_ids; P. Each reference has identity, public zone-kind at announcement if available, and current publicly resolvable description or explicit unresolved status. Never rebind to a later incarnation. |
| public announced choices, if any | Only explicitly audited announcement-time public values needed by a represented effect; P. No wholesale serialization of ActivatedAbilityObject.choice_ids or RulesEvent. Omit when absent; resolution-time choices remain absent until actually public. |

Targets in the represented source structures are object IDs. Do not fabricate player targets for structures that do not store them. A future player target needs its own source-backed public mapping. A stale target remains its original ID with unresolved status, not a hidden-zone registry lookup. If public announcement details cannot be reconstructed from a current object or existing public evidence, mark the field unavailable and the dependent fixture unassessable. Do not introduce a generic target/provenance framework to fill it.

Include all three currently represented Stack object kinds with an explicit field allowlist. Never serialize the raw program, event, source object, cost_target_object, full vars(), immutable transaction anchors or RNG state. These may carry irrelevant or private identities. A spell that will inspect a library reveals its public instruction, not the inspected cards. A trigger that later chooses/discards/reveals has no future choice in this snapshot. Publicly paid costs are already reflected in resource state; projecting full payment history is unnecessary for the minimal response view.

Unknown Stack kinds fail closed for fitness readiness rather than silently disappearing. No new instant support, target legality, counter logic, scheduling or Priority window is implied. The current engine still decides whether the offered counter action is legal and resolves it normally.

## 6. Opponent-hand leakage treatment

New views must never embed the current unfiltered GameView: public_view presently exposes both hands. Use explicit observer_index and copy only that observer's own hand, plus both counts. Sharing a common helper must not turn it into a omniscient view.

The remaining main/attack/block/Sneak hooks also receive the leaking GameView today. Restricting only Priority would leave the same Pilot session exposed. Recommend a small companion **recipient-specific GameView projection for all Pilot-facing runner call sites**, preserving the existing tuple shape and the observer's hand rows, replacing the other hand's rows with an empty tuple; add explicit hand_sizes in its versioned contract so redaction is not mistaken for an actually empty hand. This is an input-only compatibility change, not new tactical policy. The legacy public_view may remain for non-Pilot diagnostics, clearly forbidden in assessment dispatch.

The observer must come from the actual decision owner: active player for main/attack/Sneak, defender for blocks, PriorityState.player_index for Priority, and supplied player_index for private choices. Both seats and nonactive Priority need explicit tests. AcceptancePilot._card reads the acting player's hand; its attack/block methods ignore view, and choose_priority always passes. PassingPilot's overrides likewise do not require opponent hands. Thus source inspection supports unchanged selections after redaction for these exact policies; future paired execution is still required proof. Do not insert a policy wrapper that consults extra state, or assume all future Pilots ignore leaked information.

Privacy validation must also compare legal-option shape and IDs under consistent opponent-hand changes. A leak through options or predictable identity allocation is a separate finding; immutable views do not prove complete noninterference. Existing own/private identities remain necessary for selection, so this assessment proposes no new identity allocator. No library ordering, seed, RNG state, historical all-seeing view or private evidence stream is accessible to the Pilot.

## 7. Why semantics and policies need not change

The proposed dataflow is one-way: existing authoritative state -> copied immutable observations -> existing Pilot -> unchanged ActionOption -> existing engine revalidation/execution. It changes neither engine-owned choice enumeration nor option order, cost payment, movement, Stack contents, triggers, RNG or state-based actions. The new projection runs at the same instruction point and does not execute a rule. Read-only characteristic queries already exist; any query with logging/mutation is prohibited from the projector.

Filtering policies retain their existing cards/requested fields, which are the only view fields used by the frozen methods. AcceptancePilot keeps all Scry cards, takes the first optional filter and always passes Priority; PassingPilot keeps its documented overrides. Added context remains unused until a separately authorized policy program. Priority annotations/protocol typing may change to PriorityViewV2, but method selection logic must not. File hashes can change for imports/types while function-body ASTs remain identical; record both, never claim unchanged whole-file hashes if annotations changed.

This establishes an architectural separation by source inspection. Required implementation proof, after separate authorization: equal complete legal-option sequences before/after projection; no state/evidence/RNG mutation from building/reading a view; identical original-policy choices and consequent engine traces under paired inputs/seeds; unchanged gameplay-source logic, deck and matrix hashes; recursive immutability and recipient isolation. These are future validation obligations, not tests performed in this audit. Policy-compatibility execution would need explicit authorization and must be distinguished from fitness scoring.

## 8. Migration and versioning

| Surface | Narrow migration / validation impact |
| --- | --- |
| engine07.py view definitions and three constructor sites | Add immutable values and pure projection helper at existing chooser calls; preserve transaction guards, original fields, legal options and resolution sequencing. Do not alter CardInterpreter or accepted card transaction logic. |
| Pilot Protocol/type imports | Type PriorityViewV2 and extended private views. Preserve both policy method bodies; protect with AST comparison, including defaults and helper logic. |
| Stage/Smoke dispatch | Shared _drain_priority uses priority_view(owner). Other Pilot-facing calls use recipient-filtered view(owner). Private chooser wiring remains the same; no new callbacks assigned to Pilot. Matrix, stage ordering, run limits and seeds remain frozen. |
| Existing tests/custom choosers | Constructor/type compatibility needs inventory during implementation. Update view-construction expectations, add privacy and immutability checks, maintain transaction reconstruction tests. Mandatory draw-first chooser shares DiscardDrawView and must retain original behavior and ownership. |
| Preflight / future assessment harness | Preserve old diagnostic as V1 evidence. Build a new versioned preflight for V2; verify required fields, owner binding, current identities, transformations and source hashes. No automatic editing of the old failed readiness artifact. |
| 96-fixture manifest | Regenerate from the new named assessment baseline after accepted interface implementation; retain accepted quotas. Seal exact seats/options/permutations/identity maps/privacy K/count/oracles/seeds before scoring. No old fixture result promoted across versions. |
| Source/evidence identities | New interface commit plus unchanged gameplay reference and accepted spec hash; hash engine/Pilot/runner files and method-level policy bodies. Existing Smoke remains historical V1 evidence, not falsely rerun under V2. |

Recommended assessment baseline name: `pilot-input-v2`, anchored to the exact future accepted implementation commit and frozen gameplay reference, never a moving branch label alone. Preserve old e28/ca975/84beb provenance and clearly distinguish interface version from gameplay-rule version. No new baseline exists yet.

## 9. Acceptance and stop boundaries for a possible implementation authorization

A narrow implementation packet should prove: observer binding; no opponent-private or future-library data; only authorized inspected identities; correct empty counts; Stack order/controller/type/target/source-departure snapshots; no fabricated target rebinding; deep immutability; projection purity; unchanged legal options and policy bodies; correct runner ownership for both seats; deterministic serialization and transformation maps; reconstructed visibility links to existing public facts. Tests must include changing opponent hand identities and uninspected library order without changing the permitted projection, while preserving the legitimate inspected slice. Snapshot hashes belong in evaluator evidence, not the Pilot view if derived from hidden state.

Stop if implementation needs a generic hidden-zone visibility engine, new public-history framework, broad target schema, new payment solver, new gameplay rule or knowledge/memory policy. Also stop if a proposed source is not demonstrably public/own-private at the choice point. Narrowly mark it unavailable and return the fixture dependency to HQ. The companion opponent-hand redaction is explicitly proposed for review here; it must be included in the implementation authorization rather than silently expanded later.

**BOUNDED FEASIBLE**, with the above finite projection boundary and future validation requirements. This assessment authorizes no implementation and does not certify any Pilot as fit. Scoring, calibration, Action #33 and Prototype 0.3 remain NOT AUTHORIZED/BLOCKED under their existing gates.

## 10. Evidence and preservation

Read-only source anchors at the exact base: engine07.py ActionOption/PriorityState (138+), private views (389/441/489), GameView/PublicObjectView (633+), Stack classes (810/832/866), Permanent/PlayerState (893+/985), private-choice constructors (2881/3030/3483), public_view (6050), counter-option generation (6248), _mana_color/payment_plan (7243/7974); pilot07.py protocol and both policies; stage002.py _drain_priority and runner; smoke01.py runner. Line numbers are base-local aids, not moving references.

Existing Pilot Git blob verified: `3eb8bfd8654294e1ef7e6137882651801bf1e2d6`. The prior preflight JSON preserves engine/Pilot/runner source identities and field inventories. This assessment uses source inspection only and does not invoke that diagnostic or any Game/Pilot. Document SHA-256 and staged scope/diff checks authenticate this two-file evidence packet. No existing artifacts overwritten.
