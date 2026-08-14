# Cardcade Post-Foundation Action Coverage Baseline

Baseline date: 2026-08-14 EDT

Engine baseline: `cb7e957e175726ce845ba1279eae4616abf97d44` (merged Engine 0.8)

Scope: evidence-only Action coverage analysis. No Action, engine behavior, deck, prototype,
calibration, or smoke evidence was added or changed.

## Recommendation

The single highest-leverage next Action is **Create Token**.

A bounded, typed Create Token Action reaches **21 unique frozen-roster cards across all ten decks**
and **62 of 332 unique Oracle objects**. It also directly owns one currently unsupported Acceptance
Match pair. More importantly, Food, Mutagen, Robot, Ninja, Mutant, Equipment-copy, and other token
producers all need the same authoritative object-creation transaction. The Action can reuse Engine
0.8 identity, zones, events, triggers, counters, layers, and deterministic ordering without first
requiring complete Priority sequencing.

This recommendation is an architecture/coverage decision, not authorization to implement it. The
minimum future design must extend the YELLOW Zones, State-Based Actions, Events, and Invariants rows
for token objects and token cleanup. It must not implement card-name token handlers.

## Evidence universe

The analysis reconciles three evidence populations:

- Acceptance Match #001 seeds 7001–7005: **81 unsupported events / 23 exact
  card–Oracle-fragment pairs**;
- frozen roster: **102 unique card names / 600 slots / 10 decks**;
- authoritative TMT/PZA/TMC snapshot: **472 prints / 332 unique Oracle objects**.

The committed snapshot checksum and existing 600/600 deck resolution tests pass on the merged
baseline. Oracle-object counts use one representative normalized print per `oracle_id`, including
face text for the one split card. Roster counts use unique card names; deck exposure counts a deck
once when it contains at least one matching card.

Family exposure is deliberately **nonexclusive**. A card can require several reusable Actions: for
example, “discard a card, then draw a card” contributes to both Discard and Draw. Counts therefore
must not be summed across rows. Text signatures were manually spot-checked against all 102 roster
cards; full-pool figures are conservative Oracle-text/keyword exposure counts, not claims that every
matching object becomes fully executable from one Action.

## Exact Acceptance Match reconciliation

Every unsupported acceptance pair has one primary ownership family below. This table is
non-overlapping and sums exactly to 81 events / 23 pairs.

| Primary family | Events | Pairs | Exact acceptance pressure |
| --- | ---: | ---: | --- |
| Sneak casting transaction | 20 | 5 | Five Leonardo/Raphael Sneak fragments: alternative cost, return-an-unblocked-attacker additional cost, Declare Blockers timing, and enters-attacking integration. |
| Card selection / draw-discard | 15 | 4 | April scry, Lita scry mode, Casey top-four artifact selection, and Null Group attack rummage. |
| Combat abilities / permissions | 25 | 8 | First strike, double strike, trample, lifelink, menace, a choice among combat keywords, and attack-scoped ability grants. |
| Damage | 7 | 1 | Raphael, Tough Turtle's Alliance damage to target opponent. |
| Zone access / movement | 13 | 4 | Activated bounce, graveyard casting/finality, exile-top access, and permission to play the exiled card. |
| Create Token | 1 | 1 | Lita's Food-token mode. |
| **Total** | **81** | **23** | Exact reconciliation. |

Secondary tagging is intentionally broader: the Sneak pairs also mention costs, tapping, attacking,
and zone movement; Food also mentions sacrifice and life gain. The primary partition prevents those
compound fragments from inflating the 81/23 reconciliation while the coverage table below preserves
their real dependencies.

## Reusable Action-family coverage

Complexity estimates are relative to the accepted Engine 0.8 foundation:

- **Low** — one bounded transaction over existing represented state;
- **Medium** — typed choices, events, or several atomic mutations;
- **High** — new object categories, replacement rules, compound costs, broad combat, or priority;
- **Very high** — several YELLOW systems must become authoritative together.

“YELLOW extension” names the current Foundation Matrix rows that must grow. It does not change their
classification in this report.

| Reusable Action family | Acceptance exposure, events/pairs | Frozen roster exposure, cards/decks | Full pool, Oracle objects | Required Engine 0.8 dependencies | Complexity | Expected gameplay impact | YELLOW foundation extension |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| **Create Token** | 1 / 1 | 21 / 10 | 62 | Identity, Zones, Events, Triggers, Counters, Layers, RNG ordering | Medium–High | Very high: enables Food, Mutagen, Robot and creature-board production in every deck | **Yes:** Zones, Events, SBA token cleanup, Invariants |
| **Draw cards** | 4 / 1 | 17 / 7 | 54 | Zones, Identity, Events, loss-on-empty-library | Low–Medium | High card-flow impact across seven decks | **Yes:** Zones transaction/invariants; Events for card-drawn triggers |
| **Scry / top-card selection and ordering** | 11 / 3 | 8 / 7 | 13 | Zones, Choices, RNG for random ordering, hidden information | Medium–High | High acceptance visibility; medium roster breadth | **Yes:** Choices vs Targets, Zones, Invariants |
| **Discard cards** | 4 / 1 | 10 / 6 | 16 | Zones, Choices, Events, Identity | Medium | High when paired with draw, costs, graveyard, and discard triggers | **Yes:** Choices vs Targets, Zones, Events |
| **Search / reveal / shuffle / cycling** | 0 / 0 | 6 / 5 | 26 | Zones, Choices, RNG shuffle, Costs | High | Medium–high consistency and mana access | **Yes:** Choices vs Targets, Zones, Costs, Invariants |
| **Mill** | 0 / 0 | 2 / 3 | 6 | Ordered Library→Graveyard movement, Events | Low–Medium | Focused enabler for graveyard strategies | **Yes:** Zones batching, Events, Invariants |
| **Put / remove / move counters** | 3 / 1 | 23 / 7 | 88 | Existing Counters, Choices, Events, Layers, SBA | Medium | Very high; Mutagen and many growth/stun/finality lines depend on it | **Yes:** Choices, Events, SBA, Invariants; replacement effects separately |
| **Deal damage** | 7 / 1 | 12 / 8 | 52 | Choices/Targets, Events, SBA, combat/source identity | Medium | Very high interaction and life-total impact | **Yes:** Choices vs Targets, Events, SBA boundaries |
| **Destroy permanent** | 0 / 0 | 6 / 5 | 24 | Choices/Targets, Zones, Events, Triggers, SBA | Medium | High interaction; some represented narrow forms already exist | **Yes:** target typing, simultaneous Events/SBA |
| **Exile object/card** | 5 / 2 | 4 / 4 | 23 | New Exile zone, Identity, Choices, replacement/duration permissions | High | High for removal, finality, and impulse access | **Yes:** Zones, Choices, Durations, Invariants |
| **Return / move between non-stack zones** | 8 / 2 directly tagged; 13 / 4 primary zone family | 13 / 10 | 56 | Identity, Zones, Choices, Events, Triggers, LKI | High | Very high; bounce, recursion, reanimation, library placement, and hand deployment span all decks | **Yes:** Zones, Choices, Events, Invariants |
| **Gain / lose / pay life** | 3 / 2 | 16 / 6 | 40 | Events, Triggers, cost transaction, loss checks | Low–Medium | Medium–high; lifegain, drain, Food, and costs | **Yes:** Events; Costs for payment; Invariants |
| **Tap / untap / stun** | 17 / 4 text-tagged, mainly compound Sneak/activation fragments | 19 / 9 | 75 | Identity, Choices, turn state, counters, replacement behavior | Medium | High tempo and resource impact | **Yes:** Choices, Counters/SBA for stun replacement, Invariants |
| **Sacrifice** | 1 / 1 compound Food pair | 23 / 9 | 61 | Costs, Zones, Events, Triggers, SBA, Choices | High | Very high across Food, Mutagen, artifacts, creatures, and Kicker | **Yes:** Costs, Events, SBA, Choices, Invariants |
| **Equip / attach / Aura** | 0 / 0 | 7 / 7 | 19 | Attachments, Costs, Choices, Layers, Durations, SBA | High | High for Casey and artifact/equipment plans; broad secondary reach | **Yes:** Attachments plus Costs, Choices, Effects, SBA |
| **Counter spell** | 0 / 0 | 3 / 3 | 3 | Stack, Priority, Choices/Targets, zone destination | High | High interaction but narrow card exposure | **Yes:** Priority, Choices, Zones/Invariants |
| **Mana production / cost modification** | 20 / 5 compound Sneak pairs | 34 / 10 | 94 | Costs, activated/mana abilities, continuous cost effects, Priority | High | Very high economic impact across all decks | **Yes:** Costs; Priority for mana abilities; Effects for modifiers |
| **P/T, type, and ability modification** | combat grants appear in 25 / 8 primary pairs | 20 / 10 direct P/T/type text | 44 direct objects | Layers, Continuous Effects, Durations, affected-set queries | Medium–High | Very high combat and board-state impact | **Yes:** Continuous Effects, Durations, affected sets; Layers extends beyond P/T |
| **Combat abilities / permissions** | 42 / 12 nonexclusive tags; 25 / 8 primary | 55 / 10 | 150 | Combat State, Choices, Events, Layers, Durations, Triggers | Very high as one family; should be split by keyword | Very high and immediately trajectory-changing | **Yes:** Combat State, Effects, Durations, sometimes Priority |
| **Copy object/spell** | 0 / 0 | 2 / 2 | 8 | Identity, Zones/Stack, copyable values, Layers, Choices | High | Focused but architecturally deep | **Yes:** Zones, Choices, Effects/Invariants |
| **Control change / exchange** | 0 / 0 | 6 / 7 | 19 | Controller/owner identity, Choices, continuous control effects, durations | High | High board swing; modest exposure | **Yes:** Continuous Effects, Durations, Choices, Invariants |
| **Sneak compound casting** | 20 / 5 | 18 / 6 | 27 | Stack, Costs, Priority, Turn/Combat, Zones, Events | Very high | Very high for Turtle/Ninja identity and acceptance trajectories | **Yes:** Priority, Costs, Combat State, Zones, Choices |
| **Modes and runtime choices** | 3 / 1 directly tagged | 13 / 10 | 64 | Choices, Stack/Triggers choice timing, deterministic option IDs | High | High breadth; unlocks compound spells and modal triggers | **Yes:** Choices vs Targets, Priority, Invariants |

### Delivery/timing pressure

Two cross-cutting shapes are not standalone Actions but determine how Actions are invoked:

- **Triggered timing:** 60 roster cards across all ten decks and 190 Oracle objects contain trigger
  shapes. Engine 0.8's generic event→trigger→stack path is GREEN for represented shapes, but broader
  events, player ordering, target/mode timing, delayed triggers, and Priority remain YELLOW
  extensions.
- **Activated abilities:** 46 roster cards across all ten decks and 127 Oracle objects contain
  activated/level shapes. A future activated-ability announcement transaction must reuse Stack,
  Costs, Choices, and Priority rather than invoking Action effects directly.

These counts explain why Create Token must be an Action callable from spells, triggers, and later
activated abilities—not a “token card” implementation attached to named cards.

## Frozen-roster exposure detail

Create Token's 21 roster cards are:

- Courier of Comestibles;
- Crustacean Commando;
- Donatello, Gadget Master;
- Foot Mystic;
- Improvised Arsenal;
- Lita, Little Orphan Amphibian;
- Michelangelo, Mutant BFF;
- Michelangelo, Weirdness to 11;
- Mighty Mutanimals;
- Mouser Attack!;
- Mouser Foundry;
- Mutagen Man, Living Ooze;
- Mutant Chain Reaction;
- Ooze Spill;
- Ravenous Robots;
- Ray Fillet, Man Ray;
- Return to the Sewers;
- Slithering Cryptid;
- Tainted Treats;
- The Last Ronin's Technique;
- Zoo Escapees.

Together they expose every frozen deck. Token definitions include Food, Mutagen, Robot, Ninja,
Mutant, copied Equipment, and other artifact/creature tokens. Implementing only one named token would
not satisfy the family.

## UNKNOWN and manual-classification boundary

No Foundation Matrix row is reclassified UNKNOWN. This section instead preserves **Action-coverage
UNKNOWN** where automatic Oracle-text clustering is not responsible enough to claim executable
semantics.

Seven full-pool Oracle objects are family-tagged but retain UNKNOWN sub-classification for their
context or compound sequencing:

| Oracle object(s) | Known family | UNKNOWN semantic boundary |
| --- | --- | --- |
| Command Tower; Arcane Signet; Exotic Orchard; Chromatic Lantern | Mana production | Legal output depends on commander color identity or opponent-producible colors, neither represented in the frozen deterministic 1v1 state. |
| Fast Forward | Cost modification / combat control | Goad requires multiplayer-aware attack requirements and “if able” routing; a keyword match is not sufficient. |
| Double Jump // Flying Kick | Counter, P/T set, damage | Split-card faces and Fuse require a multi-half casting transaction and combined resolution contract. Face text was counted, but automated classification cannot claim the casting semantics. |
| Plague of Vermin | Life payment / Create Token / choices | Repeated turn-order life bidding until every player declines requires an explicit iterative choice protocol. |

Other compound cards may carry several known family tags; those tags are exposure evidence only.
Before implementation, the selected Action's exact Oracle subset must receive card-by-card semantic
fixtures. Anything that fails that bounded review remains explicit unsupported telemetry rather than
falling through to an approximate family handler.

## Evidence-backed leverage ranking

Ranking prioritizes reusable roster/pool reach, deck breadth, direct acceptance evidence, fit with
GREEN foundations, and the number/severity of YELLOW extensions. It does not simply sort by raw text
frequency: Triggered timing and Combat abilities are broader delivery/rules domains, while Sneak is
a compound mechanic requiring several simultaneous foundation extensions.

| Rank | Candidate Action | Evidence-backed leverage | Principal reason it is not ranked higher |
| ---: | --- | --- | --- |
| **1** | **Create Token** | 21 roster cards / all 10 decks / 62 Oracle objects / 1 acceptance pair; shared dependency for Food, Mutagen, Robots, creatures, and copies | Recommended; medium–high work must still define token identity, creation batches, events, and cleanup. |
| 2 | Draw cards | 17 / 7 / 54 and direct acceptance rummage exposure; existing draw/loss primitives reduce risk | Narrow Draw alone does not complete compound selection/discard pairs and reaches fewer decks. |
| 3 | Deal damage | 12 / 8 / 52 and 7 acceptance events; existing narrow spell damage provides a seed | Correct generic targets, prevention/replacement seams, event timing, and SBA boundaries must extend. |
| 4 | Put/remove counters | 23 / 7 / 88; existing +1/+1 infrastructure lowers migration risk | Many matches are already partly represented; new value depends on counter types, choices, replacements, and SBA breadth. |
| 5 | Sacrifice | 23 / 9 / 61; central to Food, Mutagen, artifacts, creatures, and additional costs | Must distinguish cost from effect and coordinate Events/Triggers/SBA atomically. |
| 6 | Scry / top-card selection | 8 / 7 / 13 and 11 acceptance events / 3 pairs | Strong acceptance leverage but smaller pool reach and substantial hidden-information/choice ordering. |
| 7 | Return/move zone | 13 / all 10 / 56 and four primary acceptance pairs | Several destinations and casting permissions make this multiple bounded Actions, not one safe first slice. |
| 8 | P/T and ability modification | 20 / all 10 / 44 plus combat-pair pressure | Requires affected-set and non-P/T Continuous Effect extensions despite GREEN represented Layers. |
| 9 | Equip/attach | 7 / 7 / 19; central to Casey's identity | Attachments is explicitly YELLOW and needs costs, targets, effects, detachment, and SBA together. |
| 10 | Sneak | 18 / 6 / 27 and the largest single acceptance family at 20 / 5 | Very high complexity: Priority, alternative/additional Costs, zone return, Declare Blockers timing, and enters-attacking integration. |
| 11 | Combat keyword/permission slices | 55 / all 10 / 150 and 25 / 8 primary acceptance exposure | “Combat abilities” is not one Action; each keyword needs distinct combat/layer/duration rules. |
| 12 | Counter spell | 3 / 3 / 3 | Requires authoritative Priority/all-pass sequencing for narrow exposure. |

## Required shape of the recommended next Action

A future Create Token checkpoint should remain one architectural correction and prove at least:

1. a typed immutable token definition derived from Oracle constructs, not card names;
2. authoritative owner/controller and fresh deterministic runtime identity for each created token;
3. atomic creation of one, many, or variable-count tokens with deterministic ordering;
4. explicit tapped, attacking, color, type, P/T, ability, and artifact status only when supplied by
   the typed definition;
5. creature summoning-sickness and enters-the-battlefield event/trigger integration;
6. token-copy construction through copyable values rather than aliasing a source object;
7. token cessation as an SBA after leaving the battlefield, without losing required zone-change/LKI
   evidence;
8. invariants preventing token identity reuse, duplicate-zone occupancy, or card-object confusion;
9. unsupported telemetry for token text outside the represented definition/effect scope;
10. adversarial tests plus unchanged existing acceptance trajectories unless the newly authorized
    token pair is intentionally brought into coverage.

Food and Mutagen activated abilities are not part of token creation itself. Creating those tokens
must not silently implement their sacrifice, life-gain, targeting, counter-placement, activation-cost,
or sorcery-timing text. Those remain separate Action families and explicit unsupported semantics.

## Stop condition

This baseline recommends **Create Token** as the single next Action. It does not authorize or begin
implementation. Review should confirm the Action boundary and its required YELLOW extensions before
any new checkpoint starts.
