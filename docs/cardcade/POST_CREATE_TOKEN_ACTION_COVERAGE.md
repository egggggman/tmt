# Cardcade Post-Create-Token Action Coverage

## Status

- Evidence date: 2026-08-14
- Audited branch: `main`
- Audited HEAD: `e726d7be32668690b4e9b138fa077b5e440c020d`
- Source integration: PR #30, squash-merged as `e726d7be32668690b4e9b138fa077b5e440c020d`
- Scope: evidence-only Action coverage re-ranking after the accepted Create Token Action
- Recommendation: **Deal Damage** is the single highest-leverage next Action.

This report does not implement or broaden an Action. It preserves the frozen decks,
Prototype history, pilot behavior, Engine 0.8 foundation, and explicit unsupported and
UNKNOWN classifications.

## Evidence universe

The ranking reconciles four evidence populations:

- Acceptance Match #001: 81 unsupported events, 23 exact card/Oracle-fragment pairs,
  six block-restriction rejections, and zero invariant violations.
- Frozen roster: 102 unique cards across all ten frozen decks (600/600 slots resolve).
- Authoritative TMT/PZA/TMC snapshot: 472 print records and 332 unique Oracle objects.
- Accepted Create Token coverage: 21 frozen cards across all ten decks recognized;
  17 frozen cards across all ten decks bounded-payload executable; 66 full-pool Oracle
  objects / 71 fragments recognized; 49 objects / 50 fragments bounded-payload
  executable; six objects / six fragments fully supported.

The accepted Create Token membership digests remain:

- recognized: `c7cc01b61f3498a8cdb2576532d572815e852c7c47efc6af3a45579aabbc92f8`
- bounded executable: `3fdec6260d5627e3e2c0e57b9a8e56b71ea35e59c51efcbb574de10f67254d55`

`SemanticCoverage` is now the common evidence contract for payload, parent/context,
follow-up, full-fragment support, and explicit limitations. It improves compositional
classification, but it is not itself execution support for any missing Action.

## Create Token accounting boundary

Create Token is not counted again when a fragment contains an accepted token payload
inside an unsupported trigger, activation, condition, choice, preceding effect,
replacement effect, or follow-up.

Forty-four Oracle objects have an executable Create Token payload but still carry one
or more incomplete surrounding semantics. Their residual limitations are counted only
against the missing parent or follow-up family:

| Residual limitation | Objects | Coverage meaning |
| --- | ---: | --- |
| Token activated ability not implemented | 28 | Activation/cost/timing remains unsupported; token payload is not counted again. |
| Token trigger context not implemented | 19 | Trigger delivery remains unsupported; token payload is executable only after valid delivery. |
| Token condition context not implemented | 6 | The condition deciding whether/when to create remains unsupported. |
| Token follow-up semantics not implemented | 5 | Attach, destruction, haste, or another post-creation instruction remains unsupported. |
| Token activation context not implemented | 4 | The surrounding activated-ability context remains unsupported. |
| Token choice context not implemented | 3 | The choice selecting token creation remains unsupported. |
| Token preceding effect not implemented | 3 | A required earlier instruction remains unsupported. |

Counts overlap because a fragment may have more than one limitation. Explicit payload
exclusions also remain: ten token-copy fragments, nine variable-quantity fragments,
one replacement-effect fragment, and one tapped-and-attacking fragment. Food, Mutagen,
Treasure, and Clue use/activation is not Create Token support.

Acceptance Match #001 executed zero token transactions. Its one Lita Food pair is now
residual Food activation/use pressure, not Create Token pressure. Unchanged acceptance
telemetry therefore neither adds nor subtracts Create Token execution evidence.

## Acceptance telemetry reconciliation

Each current exact pair is assigned once to its primary missing semantic family. This
prevents compound fragments from inflating multiple Action candidates.

| Primary missing family | Events | Exact pairs | Current examples |
| --- | ---: | ---: | --- |
| Combat abilities and permissions | 25 | 8 | first/double strike, trample, menace, flying/haste choice |
| Sneak | 20 | 5 | Sneak casting/permission fragments |
| Return, exile, and play-from-exile movement | 13 | 4 | bounce, graveyard casting, exile/play access |
| Scry and top-card selection | 11 | 3 | scry 1/2; top-four artifact selection and random bottoming |
| Deal Damage | 7 | 1 | Raphael, Tough Turtle Alliance damage |
| Discard then draw | 4 | 1 | Null Group attack discard/draw |
| Food activation/use | 1 | 1 | Lita Food sacrifice/life-gain activation |
| **Total** | **81** | **23** | |

The table identifies primary pressure, not a claim that every compound fragment becomes
fully supported after implementing only that family. `SemanticCoverage` must retain any
remaining parent, choice, cost, target, or follow-up limitation.

## Re-ranked missing Action families

Frozen-roster and full-pool exposure are stable where the authoritative snapshot and
decks are unchanged. Acceptance leverage is incremental after Create Token and discounts
dependent compound fragments. Complexity is relative to the existing Engine 0.8
foundation.

| Rank | Reusable Action family | Acceptance leverage | Frozen exposure | Full-pool exposure | Gameplay impact | Complexity | Required YELLOW extensions / unsupported dependencies |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | **Deal Damage** | **7 events / 1 pair directly reachable** | **12 cards / 8 decks** | **52 Oracle objects** | High: changes life totals, removes creatures, and advances games | Medium | Extend targets/choices, typed events, damage/SBAs, and invariants. Generic trigger delivery already exists for the represented Alliance path; broader replacement/prevention semantics remain explicit. |
| 2 | Scry / bounded top-card ordering | 11 / 3 aggregate; the bounded scry slice is 9 / 2, while Casey's top-four selection remains a separate compound | 8 / 7 | 13 | Medium-high: materially improves deterministic decisions and draw quality | Medium-high | Hidden-zone views, choices, ordered zone movement, and deterministic random-bottom handling. Selection and scry must remain distinct constructs. |
| 3 | Draw Cards | 4 / 1, but the current pair also requires Discard | 17 / 7 | 54 | High and broadly reusable | Low-medium | Zones, events, empty-library/SBA handling, and replacement hooks. It does not independently clear the current discard-then-draw pair. |
| 4 | Put / Remove Counters | 0 incremental acceptance pairs after existing represented counter support | 23 / 7 | 88 | High across creature development and engine state | Medium | Choices/targets, events, layers/SBAs, counter-kind interpretation, and replacement hooks. Existing +1/+1 behavior must not be double-counted. |
| 5 | Sacrifice / artifact-token activation cost | 1 / 1 direct residual Food pair | 23 / 9 | 61 | High; unlocks many activated abilities and token uses | High | Costs, choices, zones, events, triggers, and atomic activation. Food also needs life gain; Mutagen/Treasure/Clue require their own effect semantics. |
| 6 | Discard Cards | 4 / 1 compound with Draw | 10 / 6 | 16 | Medium-high; hand disruption and filtering | Medium | Hidden-zone choices, zones, events, and random/opponent-choice variants. Draw remains a dependency for the current acceptance pair. |
| 7 | Return / General Zone Movement | 13 / 4 | 13 / 10 | 56 | High | High | Destination-specific identity rules, choices/targets, costs, permissions, stack interaction, and zone-change events. Exile/play and graveyard-cast permissions must remain separate. |
| 8 | P/T and ability modification | Embedded in combat pressure rather than a safely isolated pair total | 20 / 10 | 44 | High | Medium-high | Layers, durations, targets/choices, cleanup, and keyword grants. Avoid collapsing independent continuous-effect sublayers. |
| 9 | Sneak | 20 / 5 | 18 / 6 | 27 | Very high acceptance leverage | Very high | Priority, costs, casting permissions, zones, stack timing, combat state, and cleanup. It depends on several unsupported Actions and is not a prudent next isolated checkpoint. |
| 10 | Combat keyword / permission slices | 25 / 8 aggregate | 55 / 10 | 150 | Very high | Very high as one family | Combat state, choices, layers, durations, blocking restrictions, damage ordering, and timing. Implement as evidence-defined slices, not one monolithic Action. |
| 11 | Modes and runtime choices | 3 / 1 directly exposed; many compound dependencies | 13 / 10 | 64 | High enabling value | High | Generic choices, targets, validation, and semantic-coverage composition. This is cross-cutting infrastructure, not a substitute for the selected effect Action. |

Other lower-immediate-leverage families remain explicitly missing, including search /
reveal / shuffle / cycling (6 frozen cards / 5 decks; 26 pool objects), destroy
(6 / 5; 24), equip (7 / 7; 19), control change (6 / 7; 19), copy (2 / 2; 8), mill
(2 cards across 3 decks; 6), and counterspell (3 / 3; 3). Their zero current direct
acceptance exposure does not imply unimportance; it reduces their leverage for the next
single checkpoint.

Triggered timing (60 frozen cards across all ten decks; 190 pool objects) and activated
abilities (46 frozen cards across all ten decks; 127 pool objects) remain cross-cutting
delivery contexts. They must compose through `SemanticCoverage`; they must not be credited
as effect Actions or used to silently deliver an otherwise unsupported payload.

## UNKNOWN preservation

The seven context-sensitive Oracle objects remain UNKNOWN where automatic classification
cannot responsibly establish executable meaning:

- Arcane Signet
- Chromatic Lantern
- Command Tower
- Double Jump // Flying Kick
- Exotic Orchard
- Fast Forward
- Plague of Vermin

Plague of Vermin's token grammar remains recognized, but its variable quantity and
iterative-choice context remain non-executable and UNKNOWN. Create Token supplies no
evidence to upgrade any of these objects.

## Recommendation

**Implement Deal Damage as the next single Action checkpoint.**

It provides the best composite leverage after removing already-supported Create Token
payloads from consideration: seven directly reachable acceptance events, exposure in
eight of ten frozen decks, 52 full-pool Oracle objects, immediate gameplay consequences,
and medium implementation complexity. The current Raphael Alliance path also offers a
represented generic trigger-delivery route, allowing the Action transaction itself to be
proved without first implementing Sneak, generic activated abilities, or a broad combat
redesign.

The checkpoint must remain card-name independent and distinguish damage source, target,
amount, prevention/replacement limitations, and player-versus-permanent consequences.
Unsupported target-selection, variable/scaled damage, division, fight, prevention,
replacement, or compound follow-up semantics must remain explicit through
`SemanticCoverage` rather than being inferred from the presence of a damage payload.

