# Cardcade Post-Deal-Damage Action Coverage

## Status

- Evidence date: 2026-08-14
- Audited branch: `main`
- Audited HEAD: `3b8cc7a5d764408d3977dd1c59955e66414adac6`
- Source integration: PR #31, squash-merged as
  `3b8cc7a5d764408d3977dd1c59955e66414adac6`
- Scope: evidence-only Action coverage re-ranking after accepted Create Token and Deal Damage
- Recommendation: **Scry** is the single highest-leverage Action #3.

This report does not implement or broaden an Action. Frozen decks, prototypes, pilots,
Engine 0.8 behavior, calibration, smoke evidence, explicit limitations, and UNKNOWN
classifications remain unchanged.

## Evidence universe

The ranking reconciles:

- Acceptance Match #001: 78 unsupported events / 23 exact card/Oracle-fragment pairs,
  six block-restriction rejections, and zero invariant violations;
- frozen roster: 102 unique cards across ten decks, with 600/600 slots resolving;
- authoritative TMT/PZA/TMC snapshot: 472 prints / 332 Oracle objects;
- accepted Create Token coverage: 66 objects / 71 fragments recognized, 49 / 50
  bounded-payload executable, and 6 / 6 fully supported;
- accepted Deal Damage coverage: 28 objects / 29 fragments recognized, 12 / 12
  bounded-payload executable, and 2 / 2 fully supported;
- generic `SemanticCoverage` evidence for payload, parent/context, follow-up, full support,
  and limitations.

Deal Damage membership remains locked by:

- recognized: `b8aa5f14cda90075a37af4cac2fab889d6c5f3299973cf4303f603e180e0d39a`
- bounded executable: `5c977d6a1386af69dc65c694dcb146d1e5b52a7278a085df61ae667b852a89f1`
- fully supported: `f0f5e98cedf31748f558a83a20b69834ce31fec43667aa4045de30958769a740`

## Residual acceptance reconciliation

Each exact pair is assigned once to its primary missing semantic capability. Supported
Create Token and Deal Damage payloads are not counted again.

| Primary missing capability | Events | Exact pairs | Current evidence |
| --- | ---: | ---: | --- |
| Combat abilities and permissions | 25 | 8 | first/double strike, lifelink, trample, menace, flying/haste choice |
| Sneak | 20 | 5 | alternate casting, return cost, timing, tapped-and-attacking entry |
| Return, exile, and play-from-zone permissions | 13 | 4 | bounce, graveyard casting/finality, exile and play access |
| Scry and top-card selection | 11 | 3 | scry 1/2 plus Casey's distinct top-four artifact selection/random bottoming |
| Discard/draw and hand-to-library/draw filtering | 8 | 2 | Null Group discard/draw; Manhole Missile optional hand-bottom/draw follow-up |
| Food activation/use | 1 | 1 | activation, cost, sacrifice, and life gain—not Create Token |
| **Total** | **78** | **23** | |

The seven Raphael Deal Damage limitation events are gone for the correct reason. Four
Manhole Missile damage transactions execute, while four newly explicit unsupported
hand-to-library/draw follow-ups remain. The damage payload is not counted as missing.

## Supported-child dependency inventory

Generic `SemanticCoverage` exposes dependency leverage without upgrading the child Action.

### Create Token residual contexts

Forty-four Oracle objects have an executable Create Token payload but incomplete surrounding
semantics. Limitation-fragment counts overlap:

| Missing capability | Fragments |
| --- | ---: |
| Token-type activated ability/use | 28 |
| Trigger context | 19 |
| Condition context | 6 |
| Follow-up | 5 |
| Activation context | 4 |
| Choice context | 3 |
| Preceding effect | 3 |

### Deal Damage residual contexts

Ten Oracle objects have an executable damage payload but incomplete surrounding semantics:

| Missing capability | Fragments |
| --- | ---: |
| Follow-up | 4 |
| Activation context | 3 |
| Trigger context | 3 |
| Choice context | 1 |

These counts measure dependency opportunities. They do not mean a generic activation or
trigger checkpoint could execute every child immediately: many also require costs, target
selection, conditions, modes, sacrifice, timing, or an unsupported follow-up effect.

## Re-ranked missing Action families

Roster and pool counts reuse the same unchanged authoritative snapshot and frozen decks;
incremental acceptance leverage is recomputed after both accepted Actions.

| Rank | Reusable missing family | Direct acceptance leverage | Frozen exposure | Full-pool exposure | Dependency leverage | Complexity | Engine 0.8 / missing-Action dependencies |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | **Scry** | **9 events / 2 pairs** are bounded scry; the remaining 2 / 1 Casey pair is separate top-card selection | **8 cards / 7 decks** in the broader scry/top-selection family | **13 Oracle objects** | Uses represented ETB and Alliance event/mode paths; establishes ordered hidden-zone choice primitives for later selection | Medium | Choices, hidden-zone views, ordered library movement, deterministic bottom/top ordering. Casey's random-bottom selection remains explicit. |
| 2 | Activated-ability announcement and delivery | 1 / 1 Food pair directly, but it is compound | 46 cards / 10 decks | 127 objects | Could eventually deliver 28 token-use limitations, 4 token activation contexts, and 3 damage activation contexts | High | Costs, tap/sacrifice, choices/targets, timing, Priority, zones, and each ability's effect Action. Most child fragments are not unlocked by announcement alone. |
| 3 | Trigger-delivery expansion | 4 / 1 Null Group pair has a trigger parent; other direct pairs vary | 60 / 10 | 190 | Could eventually deliver 19 token and 3 damage trigger-context fragments | High | Event kinds, intervening-if/conditions, target choice, APNAP/Priority, and missing effect Actions. Existing Alliance/ETB support must not imply generic trigger completeness. |
| 4 | Draw Cards | 8 / 2 compound pairs contain Draw | 17 / 7 | 54 | Supplies the child effect for Null Group and Manhole Missile | Low-medium | Zones, draw events, empty-library loss, replacement seam. It cannot clear either current pair without Discard or hand-to-library choice/movement. |
| 5 | Discard / hand-to-library filtering | 8 / 2 compound pairs | 10 / 6 for Discard; broader movement overlaps zone family | 16 Discard objects | Unlocks two current Draw payload contexts when paired with choice and movement | Medium | Hidden-zone choices, zones, events, optional sequencing; Manhole's bottom-library movement is not Discard. |
| 6 | Sacrifice and artifact-token use costs | 1 / 1 Food pair | 23 / 9 | 61 | Central to Food/Mutagen/Treasure/Clue use and many activation contexts | High | Transactional costs, authoritative permanents, tap state, zones, events, triggers, and the effect Action; Food additionally needs life gain. |
| 7 | Return / general zone movement and permissions | 13 / 4 | 13 / 10 | 56 | Enables graveyard, exile, bounce, and several compound follow-ups | High | Identity replacement, choices/targets, costs, casting permissions, stack, and destination-specific rules. |
| 8 | Put / remove counters | 0 incremental acceptance pairs after represented +1/+1 support | 23 / 7 | 88 | Common child and trigger dependency, including Mutagen use | Medium | Counter kinds, choices/targets, events, layers/SBAs, replacement hooks. Existing counter support is not counted again. |
| 9 | P/T and keyword modification | Embedded in combat pairs | 20 / 10 | 44 | Enables modes and continuous follow-ups | Medium-high | Layers, durations, choices/targets, Cleanup, and keyword-specific rules. |
| 10 | Sneak | 20 / 5 | 18 / 6 | 27 | Large direct acceptance exposure | Very high | Alternate costs, return-to-hand cost, Priority, stack permissions, blockers timing, tapped-and-attacking entry, and cleanup. |
| 11 | Combat keyword/permission slices | 25 / 8 | 55 / 10 | 150 | High gameplay leverage but heterogeneous | High to very high | Combat state, layers, durations, blocking rules, damage steps, lifelink/deathtouch, modes, and timing. Must be split into evidence-defined Actions. |
| 12 | General modes and runtime choices | 3 / 1 directly visible plus many compound contexts | 13 / 10 | 64 | Could deliver 3 token-choice and 1 damage-choice limitations | High | Choice identity, target validation, semantic composition, and the selected effect Action. It is enabling infrastructure, not effect execution. |

Lower immediate-leverage families remain explicit: search/reveal/shuffle/cycling
(6 frozen cards / 5 decks; 26 pool objects), destroy (6 / 5; 24), equip (7 / 7; 19),
control change (6 / 7; 19), copy (2 / 2; 8), mill (2 cards across 3 decks; 6), and
counterspell (3 / 3; 3).

## Why dependency leverage does not outrank Scry

Activated-ability and trigger delivery have the largest child-payload dependency counts,
but they are cross-cutting architecture families whose individual Oracle contexts require
different costs, events, conditions, targets, modes, and effects. Implementing only an
announcement or detection shell would claim little executable coverage; attempting to
unlock all counted children would violate the single-Action checkpoint boundary.

Scry has the strongest bounded, directly reachable effect slice:

- nine acceptance events / two exact pairs are actual scry instructions rather than a
  heterogeneous umbrella;
- represented creature-entry and Alliance machinery provide credible delivery paths;
- seven frozen decks exercise the family;
- its ordered hidden-zone choice/movement primitive is reusable by later selection,
  filtering, and library Actions;
- it does not require implementing activation costs, generic Priority, Sneak, or combat.

The Casey top-four artifact-selection/random-bottom fragment must remain a separate,
explicit limitation. It is not credited as executable Scry merely because it manipulates
the top of a library.

## UNKNOWN preservation

The seven context-sensitive Oracle objects remain UNKNOWN:

- Arcane Signet
- Chromatic Lantern
- Command Tower
- Double Jump // Flying Kick
- Exotic Orchard
- Fast Forward
- Plague of Vermin

Neither accepted Action supplies evidence to upgrade them. Plague of Vermin remains
recognized for token grammar but non-executable and UNKNOWN for variable quantity and
iterative-choice context.

## Recommendation

**Implement Scry as Action #3.**

The checkpoint should cover only fixed-number scry with authoritative ordered library
movement, bounded player choice, deterministic evidence, and truthful parent/follow-up
coverage. It must not absorb Casey-style look/reveal/select/random-bottom semantics, surveil,
draw, mill, tutor, or generic library reordering. Supported Scry payloads under unsupported
parents must remain undelivered through `SemanticCoverage`.
