# Post-Sneak Action Coverage

Status: **EVIDENCE-ONLY CHECKPOINT — ACTION #12 RECOMMENDATION**

Evidence date: 2026-08-20

Merged baseline: `6c056a94eedec3eca2c85811f5040b27830f93a7`

Merged PR: `#41` — accepted bounded Sneak casting action

## Purpose and method

This report recomputes the unsupported Action surface after Sneak from merged `main`. It does not
change engine behavior, card data, decks, prototypes, Pilot strategy, or prior evidence.

The evidence pass used:

- the authoritative 472-print / 332-Oracle-object TMT/PZA/TMC snapshot;
- all 102 unique frozen-roster cards across 10 decks;
- current Interpreter coverage and generic `SemanticCoverage` classifications;
- the merged Engine 0.8 and accepted Actions #1-#11;
- two byte-identical Acceptance Match #001 runs for each seed 7001-7005;
- direct inspection of the exact residual Oracle fragments and their prerequisite architecture.

Already executable Create Token, Deal Damage, Scry, strike-step, Activated Ability, Targeted Return,
Trample, Lifelink, hand-bottom/Draw, Discard/Draw trigger, and Sneak payloads receive no duplicate
credit. A supported parent or child does not make an unsupported compound fragment supported.

## Merged-main verification

PR #41 squash-merged as `6c056a94eedec3eca2c85811f5040b27830f93a7`. The PR had no intervening
base conflict and contained only the post-Action-10 coverage checkpoint, accepted Sneak
implementation/tests, and Acceptance evidence. `SNEAK_ACTION_ACCEPTANCE.md` remains SHA-256
`e77c5f931b905a11c34253813e1d0b0529e511aab54e880d918f8a9610298853`.

Merged validation reproduced:

- full suite: **479 passed / 1 skipped**;
- Sneak: **17 passed**;
- SemanticCoverage + card data: **10 passed**;
- casting/Stack/Priority/cost/zone/combat: **185 passed**;
- Ruff format/check and `git diff --check`: clean.

Sneak coverage remains **27 objects / 32 fragments recognized**, **14/14 bounded executable**, and
**14/14 fully supported**. Membership digests remain:

- recognized: `af93d6edb678df9768372cfc215f2e4fabab455d0eeff2422d05f5a87934b320`;
- executable/full: `8f49420ba3fd4e31bc9746f2e3b50f70fa9ec7add295840925a4610606bba924`.

Acceptance reproduced **20 unsupported events / 7 exact pairs**, **3 genuine Sneak transactions**,
**44 Priority grants / 44 passes**, **1 block rejection**, and **0 invariant violations**. Duplicate
files are byte-identical per seed. Trajectories are Raphael T14, Raphael T18, Leonardo T19,
Leonardo T43, and Raphael T16 for seeds 7001-7005 respectively. Seed 7004 retains its accepted
causal explanation: a legal April return pays Sneak for a second Cutting Edge, which enters through
Stack/Priority tapped and attacking before the legend-rule SBA removes the new copy. This is legal
execution evidence, not a Pilot-tuning defect.

## Exact residual evidence map

### 1. Wingnut, Bat on the Belfry — 5 events

Oracle fragment: `Alliance — Whenever another creature you control enters, Wingnut gains your
choice of flying, menace, or haste until end of turn.`

- Observed: **5 events** — seed 7001: 1; 7002: 1; 7003: 1; 7004: 2.
- Parent/context: typed creature-entry events, independent triggers, Alliance delivery patterns,
  Pilot choices, and cleanup durations exist. This exact modal keyword-grant ability is unsupported.
- Missing semantics: trigger-time choice among three legal modes; temporary Flying, Menace, and
  Haste grants; and the actual combat/timing rules for every offered keyword. Menace itself still
  requires multiple-blocker support.
- Dependencies: generic trigger pipeline, immutable choice, duration/layers, ability-changing
  continuous effects, Flying legality, Haste/summoning-sickness interaction, and Menace/multiple
  blockers.
- Frozen exposure: the exact pair is Wingnut in the Raphael deck. Alliance as a family reaches **6
  frozen cards / 3 decks**.
- Full-pool exposure: the exact modal payload is **1 object / 1 fragment**; Alliance reaches **10/10**.
- Can one bounded Action clear it? **Not responsibly as a small next Action.** A single coherent
  implementation could clear it only by truthfully supporting all three offered keyword choices;
  trigger delivery or a cosmetic keyword grant alone would not.

### 2. Leonardo, Sewer Samurai — 5 events

Oracle fragment: `During your turn, you may cast creature spells with power or toughness 1 or less
from your graveyard. If you cast a spell this way, that creature enters with a finality counter on
it. (If a creature with a finality counter on it would die, exile it instead.)`

- Observed: **5 events** — seed 7003: 1; seed 7004: 4.
- Parent/context: normal Hand casting, Stack/Priority, authoritative P/T evaluation, counters, zones,
  and death SBAs exist. The static graveyard-casting permission is not represented.
- Missing semantics: alternate source-zone casting permission; turn/controller and P/T
  qualification; linked “cast this way” state; enters-with-finality; exile replacement for dying.
- Dependencies: graveyard legal-option generation, casting-source provenance, counter-on-entry,
  Exile zone, replacement effects, and finality/LKI handling.
- Frozen exposure: exact pair is one Leonardo-deck card. The graveyard-creature-casting family reaches
  **2 frozen cards / 3 decks**; finality remains **1 / 1**.
- Full-pool exposure: graveyard creature casting is **2 objects / 2 fragments**; finality is **1/1**.
- Can one bounded Action clear it? **No small bounded Action can truthfully clear the full pair.** It
  is a compound permission, entry modification, and replacement lifecycle.

### 3. Raphael, Most Attitude — Menace — 2 events

Oracle fragment: `Menace (This creature can't be blocked except by two or more creatures.)`

- Observed: **2 events** — seeds 7001 and 7005.
- Parent/context: attacker/blocker runtime identity and block-option generation are authoritative;
  the engine explicitly rejects the unsupported restriction instead of approximating it.
- Missing semantics: multiple blockers per attacker, Menace's minimum-two legality, blocker ordering,
  and combat-damage assignment across multiple blockers, including interaction with Trample.
- Dependencies: expansion of YELLOW Combat State and Choices, ordered multi-block assignment,
  damage allocation, SBAs, and immutable combat evidence.
- Frozen exposure: exact pair is Raphael in the Raphael deck. Menace reaches **6 frozen cards / 4
  decks**.
- Full-pool exposure: **17 Oracle objects / 18 fragments** mention Menace.
- Can one bounded Action clear it? **Yes only as a substantial Menace/multiple-blocker combat slice.**
  The corpus leverage is high, but the architectural change is disproportionate to two current
  events and should not be attacked before a narrower ready capability.

### 4. Raphael, Most Attitude — Alliance exile — 2 events

Oracle fragment: `Alliance — Whenever another creature you control enters, you may exile the top
card of your library.`

- Observed: **2 events** — seeds 7001 and 7005.
- Parent/context: creature-entry events and the generic trigger pipeline exist. This optional
  Alliance shape and its exile payload are unsupported.
- Missing semantics: trigger-time may choice, Exile zone movement from the library, top-card
  identity/provenance, and a source-linked exiled-card collection.
- Dependencies: optional trigger choices, Exile zone, library-to-exile transaction, source-linked
  identity/LKI, and the separate play permission in residual pair 5.
- Frozen exposure: exact pair is one card / Raphael deck. Alliance reaches **6 frozen cards / 3
  decks**.
- Full-pool exposure: exact exile-top payload is **1/1**; Alliance is **10/10**.
- Can one bounded Action clear it? **A bounded exile-top Alliance action could clear this pair, but
  it would leave the linked card unusable and pair 5 unsupported.** Building the complete linked
  lifecycle is much larger.

### 5. Raphael, Most Attitude — attack-time play permission — 2 events

Oracle fragment: `Whenever Raphael attacks, until end of turn, you may play a card exiled with
Raphael.`

- Observed: **2 events** — seeds 7001 and 7005.
- Parent/context: authoritative attack events and attack-trigger Stack delivery exist. No card can
  yet be exiled with Raphael because pair 4 is unsupported.
- Missing semantics: source-linked exiled-card tracking; temporary play permission; distinction
  between playing lands and casting spells; timing, costs, and zone revalidation; permission expiry.
- Dependencies: pair 4, Exile zone, linked-object/LKI state, land-play and spell-cast option
  generation from exile, timing/cost rules, and end-of-turn duration.
- Frozen exposure: exact pair is one card / Raphael deck.
- Full-pool exposure: the exact fragment is **1/1**; broader `exiled with` play/linked handling
  appears in **4 objects / 4 fragments**.
- Can one bounded Action clear it? **Not independently.** A combined Raphael-style linked
  exile-and-play-permission lifecycle could clear pairs 4 and 5, but it requires a new zone and two
  distinct permission/trigger contexts. Its two-pair leverage does not justify that architecture yet.

### 6. Casey Jones, Jury-Rig Justiciar — ETB artifact filter — 2 events

Oracle fragment: `When Casey Jones enters, look at the top four cards of your library. You may
reveal an artifact card from among them and put it into your hand. Put the rest on the bottom of
your library in a random order.`

- Observed: **2 events** — seeds 7003 and 7004.
- Parent/context: creature-entry events, independent ETB triggers, Pilot choices, authoritative
  Hand/library identity, deterministic RNG, and bottom placement exist in bounded forms. This
  multi-card hidden-information sequence is unsupported.
- Missing semantics: private look at N, filtered optional reveal/selection, multi-card extraction,
  remaining-card random permutation, and atomic ordered library reconstruction.
- Dependencies: hidden choice views, artifact filtering, reveal evidence, multi-object transactional
  movement, deterministic RNG, and ordered library snapshots.
- Frozen exposure: exact pair is Casey in **2 decks** (Casey Jones and Raphael).
- Full-pool exposure: exact semantic family is **1 object / 1 fragment**.
- Can one bounded Action clear it? **Yes as one cohesive Casey-style filter action**, but it is a
  high-complexity hidden-information and multi-object transaction for one pair.

### 7. Lita, Little Orphan Amphibian — Food activation reminder — 2 events

Oracle fragment: `• Create a Food token. (It's an artifact with "{2}, {T}, Sacrifice this token:
You gain 3 life.")`

- Observed: **2 events** — seeds 7003 and 7004.
- Parent/context: the represented modal/Alliance path and Create Token payload are supported. Food
  token identity, artifact/type characteristics, battlefield entry, token cessation, Activated
  Ability announcement/delivery, fixed mana/tap costs, Stack/Priority, life changes, and SBAs exist.
  Telemetry remains solely because using Food is explicitly unsupported.
- Missing semantics: the compound `{2}, {T}, Sacrifice this token` activation cost and the bounded
  `gain 3 life` payload, with sacrifice and mana/tap committed atomically.
- Dependencies: extend the accepted cost transaction with a nonmana sacrifice component; move the
  authoritative Food to graveyard, apply token cessation at the SBA boundary, and deliver typed
  life gain through the existing activation Stack lifecycle.
- Frozen exposure: exact pair is Lita in the Leonardo deck. The Food activation reminder reaches
  **3 frozen cards / 3 decks** (Courier of Comestibles, Lita, and Tainted Treats).
- Full-pool exposure: **5 Oracle objects / 5 fragments** carry the canonical Food activation
  reminder.
- Can one bounded Action clear it? **Yes.** One generic, card-name-independent canonical Food
  activation transaction can truthfully clear the pair without implementing other Food-related
  abilities or arbitrary sacrifice costs.

The seven counts sum exactly to **20 events**: `5 + 5 + 2 + 2 + 2 + 2 + 2`.

## Fresh Action ranking

Ranking weights pair elimination first, then dependency readiness, gameplay significance, event
reduction, frozen reach, corpus reach, and implementation complexity.

| Rank | Candidate | Acceptance leverage | Reach | Readiness / complexity | Decision |
| ---: | --- | --- | --- | --- | --- |
| **1** | **Bounded canonical Food activation** | **1 pair / 2 events** | **3 frozen cards / 3 decks; 5 pool objects / 5 fragments** | Existing activation, mana/tap, Stack/Priority, token, zone, SBA, and life-change foundations leave one focused extension: transactional sacrifice cost plus gain 3 life. | **Action #12** |
| 2 | Raphael linked exile/play-permission lifecycle | Potentially **2 pairs / 4 events** only if both abilities are implemented together | 1 frozen card / 1 deck; linked family 4/4 | New Exile zone, linked provenance/LKI, optional trigger choice, land/spell permissions, timing, costs, and duration make this a large compound checkpoint. | Defer despite two-pair ceiling |
| 3 | Menace and bounded multiple blockers | **1 pair / 2 events** | 6 frozen cards / 4 decks; 17 objects / 18 fragments | High corpus leverage, but requires multi-block legality, order, damage assignment, Trample interaction, and broader combat evidence. | Defer: architecture disproportionate to current leverage |
| 4 | Wingnut Alliance modal keyword grant | **1 pair / 5 events** | exact 1/1; Alliance 6 frozen cards / 3 decks and 10/10 pool | Requires truthful support for all three choices, including Flying, Haste, and Menace/multiple blockers. Trigger expansion alone clears nothing. | Defer |
| 5 | Casey ETB artifact filter | **1 pair / 2 events** | 1 frozen card / 2 decks; exact 1/1 pool | Cohesive but high-risk hidden-information, filtered-choice, multi-object movement, and random-bottom operation. | Defer |
| 6 | Sewer Samurai graveyard/finality lifecycle | **1 pair / 5 events** | 2 frozen graveyard-cast cards / 3 decks; 2/2 pool, finality 1/1 | Requires casting permission, qualifier, linked provenance, counter-on-entry, Exile, and replacement effects. No smaller child clears the compound pair. | Defer |
| 7 | Generic trigger-delivery expansion alone | **0 complete pairs** | Broad | Parent delivery is present for represented patterns; every residual trigger pair still has an unsupported choice, zone, permission, or payload. | Do not pursue as Action #12 |

Raw events do not override semantic completeness. Wingnut and Sewer Samurai each contribute five
events, but neither can be removed by a small truthful Action. Raphael's linked pair offers two-pair
leverage, but its missing Exile/permission architecture is substantially larger than the observed
surface. Menace has valuable corpus reach but is a general combat expansion, not a narrow keyword
toggle.

## Action #12 recommendation

Implement **bounded canonical Food activation**:

`{2}, {T}, Sacrifice this Food: You gain 3 life.`

The Action should be Oracle-derived and token-name-independent at the runtime identity boundary,
while recognizing only the authoritative canonical Food ability shape. It should reuse the accepted
Activated Ability lifecycle, generic `SemanticCoverage`, fixed mana/tap payment, Stack/Priority,
token identity/cessation, typed life change, and SBA processing. Mana, tap, and sacrifice must form
one revalidated atomic cost transaction. Resolution should gain exactly 3 life for the ability's
controller and preserve immutable source/cost/Stack/life evidence.

This recommendation does not authorize arbitrary sacrifice costs, Treasure/Clue/Mutagen
activation, general life-gain Actions, broader Food text, deck changes, Pilot tuning, Prototype 0.3,
calibration, or smoke testing.

**Recommended Action #12: bounded canonical Food activation.**
