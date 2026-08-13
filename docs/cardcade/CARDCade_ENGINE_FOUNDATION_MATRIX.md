# Cardcade Engine Foundation Matrix

Audit date: 2026-08-13 EDT  
Code basis: `0f01c08` (0.7f gameplay plus the byte-equivalent 0.7g authoritative data foundation)  
Rules basis: [Magic Comprehensive Rules, effective June 19, 2026](https://media.wizards.com/2026/downloads/MagicCompRules%2020260619.pdf)

Primary references: [Wizards rules index](https://magic.wizards.com/en/rules),
[TMNT rules update bulletin](https://magic.wizards.com/en/news/announcements/teenage-mutant-ninja-turtles-update-bulletin),
[TMNT release notes](https://magic.wizards.com/en/news/feature/teenage-mutant-ninja-turtles-release-notes),
and the committed [authoritative snapshot manifest](../../cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json).

## Method and classification

This audit compares three independent evidence surfaces:

1. current Comprehensive Rules (CR), using the numbered rules below;
2. the checksum-verified TMT/PZA/TMC snapshot: 472 prints, **332 unique Oracle objects**, and the
   **102 unique cards / 600 slots** in the ten frozen decks;
3. actual Engine 0.7 implementation and deterministic tests.

Status means:

- **GREEN** — the current foundation represents this concern soundly for its declared scope and is
  structurally suitable for extension;
- **YELLOW** — incomplete, but the represented architecture is compatible with correct extension;
- **RED** — existing representation or control flow conflicts with behavior required by the rules;
- **UNKNOWN** — evidence is insufficient to classify. Unsupported by itself is not RED.

Pool probes are not hypothetical. Across the 332 Oracle objects / 102 roster cards respectively,
there are 26 / 17 Sneak cards, 10 / 6 Alliance cards, 15 / 6 Equipment cards, 19 / 10 Mutagen
references, 9 / 4 Disappear cards, and one / one Negate.

## Matrix

| Foundation row | Status | CR and real-card pressure | Engine/test evidence | Required rework or extension |
| --- | :---: | --- | --- | --- |
| Card Data / Oracle | **GREEN** | CR 108.1 makes Oracle the authoritative card reference; CR 200–208 defines card characteristics and faces. All 332 Oracle objects and 600/600 roster slots resolve. | `card_data.py` verifies the normalized snapshot checksum/count and exposes printing/Oracle IDs, faces, text, keywords, type, mana, P/T, set/collector identity, and legalities. `test_card_data.py` verifies 472/332, all 103 historical facts, all 16 former P/T overrides, and 600 slots. | Extend `CardFact` or replace it with a view over `CardData` when more face/layout/color characteristics enter gameplay. Do not reintroduce parallel fact tables. |
| Object Identity | **RED** | CR 109 identifies game objects; CR 400.7 normally makes an object that changes zones a new object. Counters, attachments, continuous effects, targets, and Disappear all depend on identity rather than equal values. | `Permanent` is a normal dataclass with generated value equality. Probe: an equal `Permanent` not on the battlefield satisfies `outsider in legal_attackers`; `combat([outsider])` succeeds, damages the defender, and taps the outsider while the actual battlefield permanent remains untapped. Some newer checks use `is`, but attacker validation and many list operations do not. | Give every game object a stable runtime object ID and disable value equality (`eq=False` or identity-only semantics). Replace membership/removal checks with zone-manager identity lookup. Targets, effects, attachments, combat participants, and event payloads must reference object IDs plus last-known information where required. |
| Zones | **RED** | CR 400–408 defines library, hand, battlefield, graveyard, stack, exile, and command. CR 400.7 governs new objects after zone changes. Mutagen tokens and Disappear require zone-change events; Sneak returns an attacker to its **owner's** hand. | Zones are separate Python lists, but only library/hand/battlefield/graveyard exist. `Permanent` stores controller but not owner. `put_into_graveyard()` uses `players[permanent.controller]` as both controller and owner, which becomes wrong after control changes. No central movement transaction or zone-change record exists. | Introduce owner and object ID separately from controller; a zone manager must atomically move cards/objects, create the new object, preserve allowed exceptions, emit one zone-change event, and support stack/exile. Replace direct list mutation throughout `cast`, `destroy`, `put_into_graveyard`, land play, and pilot code. |
| Turn Structure | **RED** | CR 500–514 defines phases and steps, turn-based actions, and cleanup. Sneak (CR 702.190) is usable during the declare-blockers step; Disappear includes beginning-of-end-step triggers. | `phase` is a string. `begin_turn()` jumps from beginning directly to precombat main; `combat()` is monolithic; `end_turn()` jumps to cleanup/ending. There is no untap/upkeep/draw step object, begin/end-step window, or declare-blockers window. | Replace phase strings as control flow with an explicit phase/step state machine and turn-based action scheduler. Keep strings only as telemetry. Existing `begin_turn`, `combat`, and `end_turn` must be decomposed. |
| Combat State | **RED** | CR 506–511 maintains attacking/blocking objects, defender assignments, declaration legality, blocked status, damage assignment, and priority windows. Sneak enters attacking after blockers (CR 702.190; CR 508.4). Menace and Equipment also depend on declaration-wide state. | `combat()` takes a list and one blocker mapping, taps attackers, applies triggers, assigns blocks, deals damage, performs SBAs, and exits. Attacking/blocking/blocked status is not persistent. One blocker per attacker is baked into the mapping. | Add a combat object with declared/put-attacking distinction, defender, blocked status, blocker lists, requirements/restrictions, damage order, and step transitions. `generate_blocks` can remain a pilot choice only after it consumes a rules-generated legal declaration set. |
| Costs | **RED** | CR 601.2f–h and 118 require total-cost determination, choices, mana abilities, and payment; alternative/additional costs are mutually constrained. Sneak substitutes its cost and returns an unblocked attacker; Equip is an activated cost. | `can_afford()` counts untapped lands, assumes one color, and `_pay()` taps the first N lands. `cast()` receives no cost object and immediately pays/resolves. Card-name cases implement two spells. The lossless integral-mana adapter is sound but deliberately narrow. | Add typed costs and a casting/activation proposal: modes, targets, alternative/additional costs, cost modifiers, mana production/payment, nonmana payments, then commit atomically. Replace `_pay`, `can_afford`, and card-name branches. |
| Choices vs Targets | **YELLOW** | CR 115 targets are chosen during casting/activation; CR 601.2b–d covers modes/targets/divisions. Many non-target choices occur during resolution. Alliance includes both targeted effects and non-target modal choices. | The distinction is partially visible: `cast(..., target)` supplies a target before resolution, while legend, counter-target, and Alliance-mode choosers are callbacks. Tests validate chooser output. There is no typed choice record, legal-option generator, target locking, revalidation, optional choice, or division. | Preserve the timing distinction but replace callbacks/ad hoc parameters with typed `ChoiceRequest`, `TargetSelection`, and legal-option sets. Store chosen targets on stack objects and revalidate at resolution; request non-target choices at the rule-specified time. |
| Events | **YELLOW** | CR uses events for triggers, replacement effects, zone changes, damage, life gain, and "left the battlefield this turn". Disappear is an ability word grouping event-history conditions. | `Game.log()` creates useful contextual audit records, but logs are passive telemetry, not authoritative game events. Mutations often happen before logging, and direct list changes can emit no event. There is no event identity, cause/source chain, simultaneous-event grouping, or last-known information. | Retain the audit log as an output projection. Add a typed internal event model emitted by every state transition, including atomic/simultaneous groups and source/cause/object IDs. Disappear should query tracked zone-change history, not scan log prose. |
| Triggers | **RED** | CR 603 makes triggered abilities trigger on events and wait to be put on the stack the next time a player would receive priority; CR 117.5 performs SBAs before pending triggers are stacked. APNAP ordering applies when multiple triggers stack. Alliance and Disappear are central probes. | `resolve_creature_entered_*` and `resolve_attack_pt_effects` scan Oracle regexes and execute effects immediately. Cross-system probe with Mighty Mutanimals plus a duplicate legend logs `counters_placed` before `legend_rule_choice`; correct architecture would record the trigger, perform the legend-rule SBA, then stack/resolve it later. | Replace direct resolver hooks with trigger registration/matching that creates trigger instances. Add pending-trigger queues, intervening-if checks, APNAP/order choices, source/last-known information, stack placement, and resolution. Existing immediate hook functions require decomposition. |
| Stack | **RED** | CR 112.1 and 405 put spells, activated abilities, and triggered abilities on the stack until resolution/countering. Negate literally requires a noncreature spell stack object. Sneak is a static ability functioning while its spell is on the stack. | No stack zone/object exists. `cast()` directly mutates zones and resolves effects. Probe: Negate returns false, remains in hand, spends no mana, and creates no semantic event because it cannot enter the casting path. Honest non-approximation is good, but the execution architecture cannot add Negate locally. | Introduce stack objects for spells/abilities with controller, source, choices, targets, costs paid, modes, and effect program. Split announce/pay from resolve; move cards hand→stack→destination; implement countering against stack objects. |
| Priority | **RED** | CR 117 controls when players may act and when the top stack object resolves. Priority occurs throughout main phases, combat steps, end step, and exceptional cleanup. Sneak specifically uses instant timing in declare blockers. | No priority player, pass sequence, action window, or all-pass resolution exists. The runner alone decides a fixed action sequence. `hasattr(game, 'priority_player')` is false. | Add priority/APNAP state integrated with the step machine and stack. Pilot receives legal actions only for the priority holder; consecutive passes resolve/advance. This cannot be bolted onto monolithic `combat()`. |
| State-Based Actions | **YELLOW** | CR 704 checks SBAs whenever a player would receive priority, performs all applicable actions simultaneously, repeats, then stacks triggers. Legend rule is CR 704.5j. | `StateBasedAction` protocol and repeat-until-stable loop are a good extension seam; deterministic legend chooser and lethal damage tests pass. Coverage is narrow, actions run sequentially rather than as one simultaneous event, and checks occur at manually selected mutation sites because priority does not exist. | Keep the action registry, but change it to collect/apply a simultaneous batch at the CR 117.5 boundary. Add zero toughness, life/draw loss, token cleanup, illegal attachments, counter annihilation, and other applicable SBAs. |
| Counters | **GREEN** | CR 122 defines counters on players/objects; +1/+1 and -1/-1 counters modify P/T and annihilate as an SBA (CR 704.5q). Mutagen tokens place +1/+1 counters; finality has replacement behavior beyond storage. | Typed counter dictionaries are separate from printed P/T and modifiers. Placement validates target/type/quantity, accumulates, persists through cleanup, and does not transfer to a new object. Tests cover accumulation, P/T interaction, generic types, invalid state, Alliance/life-gain placement, and zone changes. | Add counter-type semantics through interpreter/rules modules, not `Permanent.counter_delta` branches. Implement +1/+1/−1/−1 annihilation in SBA; finality still requires exile/replacement infrastructure. Identity correction is prerequisite. |
| Continuous Effects | **YELLOW** | CR 611–613 governs continuous effects from spells, abilities, and static abilities. Equipment continuously modifies the equipped object; static effects can depend on changing state. | `PowerToughnessModifier` explicitly separates printed P/T, counters, and modifiers; persistent derived modifiers recompute after battlefield changes. This is sound for the declared additive P/T subset, but effect existence is stored on the affected permanent and static sources are rediscovered by regex scans. | Introduce independent continuous-effect instances with source, affected-set query, timestamp, duration, dependency metadata, and characteristic operation. Preserve current additive tests as layer-7c regressions. |
| Layers | **RED** | CR 613 applies continuous effects in ordered layers/sub-layers with dependencies and timestamps; P/T setting, modification, counters, and switching are distinct (CR 613.4). | `Permanent.power/toughness` directly computes `printed + counter delta + sum(modifiers)`. This is commutative and cannot represent characteristic-defining/base-setting effects, copy/type/ability changes, dependencies, timestamps, or P/T switching. | Replace derived property arithmetic with a characteristic evaluation pipeline implementing layers and sublayers. Migrate counters and current modifiers into layer operations; do not add more arithmetic special cases. |
| Durations | **YELLOW** | CR 611.2a and 514.2 govern stated durations and cleanup expiration; delayed effects and "for as long as" require different lifetime conditions. Equipment persists while attached. | Modifier duration is explicitly `persistent` or `until_end_of_turn`; cleanup removes EOT modifiers while counters persist. Tests cover Alliance and attack effects expiring. No end-of-combat, next-turn, conditional, source-linked, delayed, or indefinite attachment duration exists. | Generalize effect lifetime predicates and expiration events while retaining cleanup expiry. Durations belong to effect instances, not only P/T modifier records. |
| Attachments | **YELLOW** | CR 301.5, 303.4, 701.3, and 704.5m–n govern Equipment/Auras, attach/equip, continuous effects, and illegal attachments. The pool has 15 Equipment Oracle objects, six in frozen decks. | No attachment relation or Equipment permanent behavior exists. Equipment spells remain unsupported rather than approximated. `Permanent` can be extended, but identity, zones, activated costs, targets, continuous effects, and attachment SBAs are prerequisites. | Add attachment edges keyed by object IDs, legal attach predicates, equip activated abilities/costs/timing, continuous effects that query the edge, detach-on-zone-change, and illegal-attachment SBAs. Avoid storing only a bonus on the creature. |
| Deterministic RNG | **RED** | CR 103.3 and 701.20 require randomization; cards can randomize library order or selections. Casey Jones requires a random order for cards put on the library bottom. | `Game.__init__` creates local `random.Random(seed)` solely for initial shuffles, then discards it. `hasattr(game, 'rng')` is false. Future random actions would need a new stream, risking seed collisions and order-dependent nondeterminism outside auditable state. | Retain a game-owned RNG service/state, define deterministic consumption APIs, log operation/result provenance, serialize RNG position or replay decisions, and route every random operation through it. Preserve initial shuffle byte regressions. |
| Invariants | **YELLOW** | Rules invariants span unique zone membership, ownership/control, legal targets/declarations, object existence, attachments, stack/priority, and card conservation. | Current checks cover controller/zone consistency, printed creature P/T, counter values, modifier duration/timestamp, surviving positive toughness, and legend uniqueness. Combat tests cover duplicate blockers/nonattacker mapping keys, but the identity probe bypasses attacker membership. No global card conservation or unique-zone/object invariant exists. | Add object registry/zone uniqueness, owner/control, card conservation, combat membership, target existence, attachment, stack, priority, and event-causality invariants. Run at every transaction boundary and in snapshots, not only selected SBA calls. |
| Rules Engine ↔ Card Interpreter ↔ Pilot separation | **RED** | CR 601/608 separate legal procedure from card-specific instructions; Oracle supplies semantics, while player choices select among legal actions. Sneak, Negate, Alliance, Equipment, Mutagen, and Disappear each cross several generic subsystems. | `Game` owns rules state **and** Oracle regex interpretation (`supports_*`, `resolve_*`) **and** card-name dispatch for Manhole Missile/Make Your Move. The runner contains pilot heuristics and card-name dispatch for those spells. Automatic block selection is invoked inside `combat()` when requested. | Establish typed effect/ability IR in a Card Interpreter; Rules Engine executes typed actions and returns legal choices; Pilot selects actions/choices only. Move regex/card parsing and named-card mappings out of `Game`, move block choice out of combat resolution, and delete pilot compensation for unsupported semantics. |

No row is UNKNOWN: the current rules, authoritative pool, and executable code/tests provide enough
evidence to classify every requested concern.

## Cross-system interaction probes

These probes were run against the clean `0f01c08` foundation without modifying engine behavior:

| Interaction | Result | Architectural implication |
| --- | --- | --- |
| Object identity × combat legality | An equal non-battlefield `Permanent` was accepted as a legal attacker, dealt 2 damage, and was tapped; the battlefield permanent was not tapped. | Confirms RED, not theoretical risk. Identity must precede more combat/target work. |
| Attack P/T effect × block restriction | Existing deterministic test applies an attack modifier before current-power evasion and permits an equal-power blocker. | Positive integration evidence for current additive P/T and blocker predicates. |
| Counter × continuous P/T × cleanup | Existing tests show counters accumulate separately, combine with persistent/EOT modifiers, counters persist, and EOT modifiers expire. | Supports GREEN counters and YELLOW continuous effects/durations. |
| Zone change × counters | Existing test moves a permanent to graveyard and creates a new battlefield object with no inherited counters. | Correct observed result, but general identity/zone architecture remains RED. |
| Alliance trigger × legend-rule SBA | Mighty Mutanimals placed its counter before the duplicate legend was processed by the legend-rule SBA. | Confirms trigger effects execute too early; CR 117.5/603 requires pending trigger → SBA → stack. |
| Negate × stack/costs | Negate could not be cast; it stayed in hand and spent no mana. | Honest unsupported behavior, but demonstrates stack/casting pipeline prerequisite. |
| Equipment × costs/attachments/effects | Skateboard could not be cast; it stayed in hand, spent no mana, and emitted exact unsupported fragments. | Honest unsupported behavior; attachment work must not be flattened to a P/T modifier. |
| RNG × future random-bottom selection | Game retains no RNG object after initial shuffle. | Confirms future Casey Jones-style random ordering needs a persistent RNG service. |
| Authoritative data × Engine 0.7 migration | All 103 historical facts and 600 slots resolve; Acceptance seeds 7001–7005 remain byte-identical. | Data foundation is GREEN and did not change behavior. |

## Probe mechanics and dependency pressure

- **Sneak (CR 702.190):** requires stack-resident spell state, alternative/nonmana costs, declare
  blockers timing, priority, owner-aware return, and enters-attacking combat state. Implementing it
  before the RED turn/stack/cost/identity corrections would hard-code around all four.
- **Negate:** requires a noncreature spell on the stack, target selection at cast time, priority,
  countering, and correct destination handling. A named `cast` branch would be architecturally wrong.
- **Alliance:** is a trigger family, not an ETB callback. Targets and modes are chosen at different
  rule-defined times, and simultaneous triggers need APNAP ordering.
- **Equipment:** needs permanent casting, activated equip costs, target legality, attachment identity,
  layer-aware continuous effects, zone-change detachment, and attachment SBAs.
- **Mutagen:** requires predefined token characteristics (CR 111.10), token object identity, artifact
  activated costs, tap/sacrifice, sorcery timing, target selection, counter placement, and token SBAs.
- **Disappear:** is an ability word, not one shared action. Its cards query typed zone-change history
  under a player's control and then create distinct conditional triggers/effects.

## Prioritized RED corrections

1. **Runtime object identity, ownership, and zone transactions.** Fix the demonstrated illegal-clone
   combat path; add owner/controller separation and central movement before expanding targets,
   attachments, tokens, Disappear, or Sneak.
2. **Rules Engine / Interpreter / Pilot boundary.** Define typed actions/effects/legal choices and
   remove parsing, named-card resolution, and pilot decisions from `Game`. This prevents every later
   feature from deepening the current coupling.
3. **Explicit turn/combat state plus priority and stack kernel.** Decompose `begin_turn`, `combat`,
   and `end_turn`; implement phases/steps, passes, and stack objects together because Sneak and Negate
   prove they are not independently bolt-on features.
4. **Transactional casting, activation, and cost payment.** Build proposals and atomic payment over
   the new stack/priority kernel; replace `_pay`, `can_afford`, and named `cast` branches.
5. **Typed event and trigger queue with CR 117.5 sequencing.** Record trigger instances, perform
   simultaneous SBAs, then stack triggers in APNAP order. Replace immediate Alliance/attack/ETB
   resolver hooks.
6. **Layered characteristic engine.** Move counters and additive modifiers into CR 613 evaluation
   before adding Equipment, base-setting P/T, type changes, or characteristic dependencies.
7. **Persistent deterministic RNG service.** Retain and audit the seeded stream before implementing
   random-bottom/order, shuffle, or random selection Actions.

The first five corrections form one dependency chain. Implementing card Actions around them would
create behavior that later has to be removed, not merely extended.

## Validation boundary

This audit adds documentation only. It changes no engine behavior, decks, prototypes, card data,
historical evidence, or expected trajectories. No new Action, Prototype 0.3, calibration, or
900-game smoke was performed.
