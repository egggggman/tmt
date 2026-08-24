# Post-Action #14 Coverage Delta Interpretation #1

## Scope and evidence boundary

This is an evidence interpretation of the independently accepted pre-Action #14 Coverage-Aware Engine Smoke Stage 0.1 baseline and the independently accepted post-Action #14 remeasurement. It does not rerun games, assess balance, modify Cardcade, or authorize another Action.

Authoritative post-Action #14 input:

- merged-main baseline: `f40a74eacb4599b0962c1198cba70f4b654c2f99`;
- raw artifact: `POST_ACTION_14_COVERAGE_AWARE_ENGINE_SMOKE_STAGE_0.1_RESULTS.json`;
- raw artifact SHA-256: `351b70cf2845322d49773262353576c46d351d1c1f825505a34a890f1ff4942d`;
- accepted mechanical result: 45 pairings, 180 distinct games, 360 executions, 180 byte-identical duplicate pairs, zero runner stops, and zero invariant violations.

All counterfactuals below are static set calculations over authenticated per-game unsupported memberships. They predict coverage classification only. They do not predict changed trajectories, execution frequency, game outcomes, or balance.

## Observations

### Measured Action #14 delta

| Measure | Pre-#14 | Post-#14 | Delta |
|---|---:|---:|---:|
| Coverage-complete games | 5 | 10 | +5 |
| Coverage-limited games | 175 | 170 | -5 |
| REACHED / UNSUPPORTED occurrences | 692 | 599 | -93 |
| Exact Dream Beavers unsupported occurrences | 91 | 0 | -91 |

The exact Dream Beavers fragment now has 90 authenticated executions in 49 games, with 90 unique transaction/source identities and authenticated `etb_drain_gain_scry`, `scry_committed`, and `trigger_resolved` evidence. It has no remaining REACHED / UNSUPPORTED occurrence, and Dream Beavers has no other unsupported reach. The difference between 91 former reaches and 90 later executions is not treated as a missing transaction: gameplay changed after support became executable, and the accepted results audit authenticated the post-Action evidence independently.

Action #14 therefore realized the static headline prediction exactly: coverage-complete games rose from 5 to 10. The additional net reduction of two unsupported occurrences beyond the removed 91 Dream Beavers reaches is a measured downstream trajectory effect, not an assertion that Action #14 implemented other semantics.

### Residual exact-fragment clusters

The post-Action artifact contains exactly 27 residual exact Oracle-fragment clusters totaling 599 REACHED / UNSUPPORTED occurrences. `Solo` is the number of presently limited games that become complete if only that cluster is removed. `CF` is the resulting total coverage-complete count (`10 + Solo`).

| ID | Card / exact Oracle fragment | Occ. | Games | Matchups | Decks | Solo | CF | Classification; reusable dependencies; missing prerequisites / breadth |
|---|---|---:|---:|---:|---|---:|---:|---|
| C01 | Casey Jones, Jury-Rig Justiciar — “When Casey Jones enters, look at the top four cards of your library. You may reveal an artifact card from among them and put it into your hand. Put the rest on the bottom of your library in a random order.” | 67 | 42 | 17 | Casey Jones, Raphael | 1 | 11 | Compound/dependency-heavy; ETB trigger, library identity and choices reusable; needs look-N, typed reveal/selection, conditional hand movement, random-bottom ordering, shuffle-independent evidence. |
| C02 | Utrom Scientists — “When this creature enters, tap up to one target creature and put a stun counter on it. (If a permanent with a stun counter would become untapped, remove one from it instead.)” | 61 | 44 | 17 | April O'Neil, Krang | 3 | 13 | Compound/dependency-heavy; ETB, targeting, tap and counters partly reusable; needs optional target transaction plus the stun-counter untap replacement. |
| C03 | Zoo Escapees — “When this creature leaves the battlefield, create a Mutagen token. (It's an artifact with ‘{1}, {T}, Sacrifice this token: Put a +1/+1 counter on target creature. Activate only as a sorcery.’)” | 50 | 34 | 16 | Bebop & Rocksteady, Michelangelo | 2 | 12 | Small prerequisite first; token creation/identity exists, but needs generic permanent-departure trigger delivery and then canonical Mutagen activation for full surrounding support. |
| C04 | Fugitive Droid — “{U}, Sacrifice this creature: Counter target spell that targets an artifact or creature you control.” | 48 | 37 | 22 | April O'Neil, Donatello, Krang | 1 | 11 | Compound/dependency-heavy; activation, sacrifice, Stack and targeting infrastructure reusable; needs response timing, constrained Stack targeting, target-of-target validation and counterspell delivery. |
| C05 | Courier of Comestibles — “When this creature enters, you may search your library for a Food card, reveal it, put it into your hand, then shuffle. If you don't put a card into your hand this way, create a Food token. …” | 35 | 22 | 9 | Michelangelo | 4 | 14 | Compound/dependency-heavy; ETB, Food token and zone identity reusable; needs optional typed library search, reveal, hand movement, shuffle and conditional fallback. |
| C06 | Super Shredder — “Whenever another permanent leaves the battlefield, put a +1/+1 counter on Super Shredder.” | 34 | 25 | 9 | Shredder | 5 | 15 | **Bounded Action candidate**; departure opportunity provenance, triggers, Stack/Priority and counter placement are reusable; needs exact departure-event trigger delivery, `another` exclusion and self-counter transaction. Low-to-moderate breadth. |
| C07 | Ray Fillet, Man Ray — “{2}, Remove a +1/+1 counter from a creature you control: Draw a card.” | 31 | 30 | 15 | April O'Neil, Krang | 2 | 12 | Small prerequisite first; activation, mana and Draw reusable; needs authoritative counter-removal cost from a chosen controlled creature and atomic cost evidence. |
| C08 | Casey Jones, Vigilante — “When Casey Jones enters, draw three cards. At the beginning of your next upkeep, discard three cards at random.” | 27 | 23 | 9 | Casey Jones | 0 | 10 | Compound/dependency-heavy; ETB, Draw and discard zones reusable; needs multi-draw semantics, delayed trigger identity across turns, random discard and compound evidence. |
| C09 | Menace reminder text | 22 | 22 | 14 | Bebop & Rocksteady, Raphael, Splinter | 0 | 10 | Broad/deferred combat semantic; requires multi-blocker declaration legality and combat-choice integration. Explicit unsupported status remains safer than a narrow telemetry-only implementation. |
| C10 | Paramecia Coloniex — “When this creature enters, mill three cards.” | 21 | 16 | 9 | Bebop & Rocksteady | 0 | 10 | Bounded candidate but no solo clearance; ETB, ordered library/graveyard identity and triggers reusable; needs generic mill-N transaction and short-library boundary. |
| C11 | Rock Soldiers — “When this creature enters, destroy up to one target noncreature artifact.” | 20 | 15 | 8 | Casey Jones | 1 | 11 | Small prerequisite first; ETB, target and destruction infrastructure partly reusable; needs optional constrained noncreature-artifact target and exact instruction occurrence. |
| C12 | Stockman, Mad Fly-entist — “When Stockman enters, draw a card, then discard a card.” | 19 | 18 | 9 | Krang | 0 | 10 | Bounded candidate but no solo clearance; Draw, discard, trigger and ordering infrastructure reusable; needs mandatory ordered Draw-then-discard transaction and empty-library terminal handling. |
| C13 | Ravenous Robots — “{R}, {T}: Creature tokens you control gain haste until end of turn.” | 18 | 13 | 7 | Casey Jones | 2 | 12 | Small prerequisite first; activation/mana/tap and token identity reusable; needs set-valued continuous temporary haste effect and duration cleanup. |
| C14 | Shredder, Unrelenting — “Whenever Shredder enters or attacks, another target creature you control gains deathtouch until end of turn.” | 17 | 16 | 9 | Shredder | 3 | 13 | Compound/dependency-heavy; ETB/attack triggers and targeting reusable; needs dual trigger grammar, `another` constrained choice and temporary deathtouch combat semantics. |
| C15 | Tunnel Rats — “{4}{B}: Return this card from your graveyard to the battlefield tapped.” | 17 | 14 | 7 | Splinter | 1 | 11 | Small prerequisite first; activation, costs, zone/new-object identity and tapped entry reusable; needs graveyard-source activation permission and self-return transaction. |
| C16 | Make Your Move — “Destroy target artifact, enchantment, or creature with power 4 or greater.” | 16 | 13 | 6 | Leonardo | 1 | 11 | Small prerequisite first; spell/Stack and destruction reusable; needs disjunctive type/power target grammar and authoritative current characteristics. |
| C17 | Paramecia Coloniex — “When this creature dies, you may exile it. When you do, put target creature card from your graveyard on top of your library.” | 16 | 12 | 9 | Bebop & Rocksteady | 0 | 10 | Compound/dependency-heavy; dies provenance and zones reusable; needs optional self-exile, reflexive trigger, graveyard target and library-top movement. |
| C18 | Wingnut, Bat on the Belfry — “Alliance — Whenever another creature you control enters, Wingnut gains your choice of flying, menace, or haste until end of turn.” | 15 | 14 | 7 | Raphael | 2 | 12 | Compound/dependency-heavy; Alliance event provenance exists; needs immutable mode choice plus temporary keyword effects, including unsupported Menace. |
| C19 | Leonardo, Sewer Samurai — graveyard casting permission plus finality-counter replacement text | 15 | 10 | 6 | Leonardo | 0 | 10 | Broad/deferred alternate-zone casting and replacement semantic; needs graveyard permission, qualifying characteristic evaluation, finality entry state and death-to-exile replacement. |
| C20 | Donatello, Turtle Techie — “When Donatello enters, if you control an artifact, draw a card.” | 14 | 13 | 7 | Donatello | 1 | 11 | Bounded candidate; ETB, authoritative artifact state, trigger and Draw reusable; needs intervening-if evaluation at trigger creation/resolution and exact controller state. |
| C21 | Donatello, Way with Machines — “Whenever an artifact you control enters, put a +1/+1 counter on Donatello.” | 8 | 8 | 5 | Donatello | 0 | 10 | Bounded candidate but no solo clearance; artifact-entry context and counters reusable; needs authoritative artifact-entry trigger delivery and source/controller linkage. |
| C22 | Raphael, Most Attitude — “Alliance — Whenever another creature you control enters, you may exile the top card of your library.” | 7 | 7 | 6 | Raphael | 0 | 10 | Compound/dependency-heavy; Alliance provenance and library identity reusable; needs optional top exile plus durable source-linked permission evidence for C23. |
| C23 | Raphael, Most Attitude — “Whenever Raphael attacks, until end of turn, you may play a card exiled with Raphael.” | 6 | 6 | 5 | Raphael | 0 | 10 | Compound/dependency-heavy and dependent on C22; attack trigger exists, but needs source-linked exile set, temporary play permission, timing and cost enforcement. |
| C24 | Frog Butler — “{2}: This creature gains reach until end of turn.” | 5 | 5 | 3 | Bebop & Rocksteady | 0 | 10 | Bounded candidate but no solo clearance; activation/mana reusable; needs temporary Reach effect and cleanup. |
| C25 | Frog Butler — “{T}: Add one mana of any color.” | 5 | 5 | 3 | Bebop & Rocksteady | 0 | 10 | Small prerequisite first; tap activation/resource systems reusable; needs authoritative color choice and mana ability treatment. |
| C26 | Krang, Master Mind — “When Krang enters, if you have fewer than four cards in hand, draw cards equal to the difference.” | 4 | 3 | 2 | Krang | 0 | 10 | Bounded grammar but variable multi-draw prerequisite; ETB/hand state/Draw reusable; needs conditional dynamic quantity and repeated failed-draw semantics. |
| C27 | Ooze Spill — “Counter target spell. Create a Mutagen token. …” | 1 | 1 | 1 | Krang | 0 | 10 | Compound/dependency-heavy; spell/Stack and token creation reusable; needs generic counterspell target/effect plus Mutagen token semantics. |

### Exact overlap matrix

Each entry `Cxx=n` is the number of distinct post-Action games containing both row clusters. The diagonal is the row cluster's `Games` value from the table. Any off-diagonal pair omitted below has overlap zero. This sparse representation fully specifies all 351 off-diagonal pair relationships and is symmetric; values are repeated in both row directions to make each cluster independently readable.

- C01: C02=5, C03=4, C04=2, C05=3, C06=3, C07=2, C08=13, C09=5, C10=2, C11=11, C12=3, C13=6, C14=1, C15=1, C16=2, C17=2, C18=9, C19=1, C20=2, C21=3, C22=4, C23=4.
- C02: C01=5, C03=6, C04=18, C05=3, C06=4, C07=19, C08=3, C09=4, C10=3, C11=1, C12=12, C13=2, C14=3, C15=1, C17=2, C18=1, C19=1, C20=2, C21=1, C24=1, C25=1.
- C03: C01=4, C02=6, C04=3, C05=11, C06=1, C07=5, C08=2, C09=5, C10=10, C11=1, C12=3, C13=2, C14=2, C15=2, C16=4, C17=6, C18=3, C19=1, C20=2, C21=2, C22=1, C23=1, C24=4, C25=4.
- C04: C01=2, C02=18, C03=3, C05=5, C06=3, C07=15, C08=2, C09=1, C10=3, C11=1, C12=6, C13=1, C14=3, C15=2, C17=3, C18=1, C19=2, C20=6, C21=4, C22=1, C24=1, C25=1, C26=2.
- C05: C01=3, C02=3, C03=11, C04=5, C06=1, C07=3, C09=1, C10=1, C11=1, C12=1, C13=1, C14=1, C15=1, C16=3, C17=1, C18=1, C19=2.
- C06: C01=3, C02=4, C03=1, C04=3, C05=1, C07=2, C08=3, C09=5, C10=1, C11=2, C12=1, C13=1, C14=9, C15=3, C16=2, C17=1, C19=1, C24=1, C25=1.
- C07: C01=2, C02=19, C03=5, C04=15, C05=3, C06=2, C09=1, C10=3, C12=13, C14=2, C15=1, C17=2, C19=3, C20=1, C24=1, C25=1, C26=1, C27=1.
- C08: C01=13, C02=3, C03=2, C04=2, C06=3, C09=2, C10=2, C11=9, C13=10, C14=1, C15=1, C16=1, C17=2, C20=1, C22=1, C23=1.
- C09: C01=5, C02=4, C03=5, C04=1, C05=1, C06=5, C07=1, C08=2, C10=4, C11=1, C12=2, C13=1, C14=1, C15=8, C16=2, C17=3, C18=3, C20=1, C22=1, C23=1, C24=2, C25=2.
- C10: C01=2, C02=3, C03=10, C04=3, C05=1, C06=1, C07=3, C08=2, C09=4, C12=1, C16=1, C17=12, C20=1, C21=2, C22=1, C23=1, C24=3, C25=3.
- C11: C01=11, C02=1, C03=1, C04=1, C05=1, C06=2, C08=9, C09=1, C13=3, C15=1, C16=1, C21=1.
- C12: C01=3, C02=12, C03=3, C04=6, C05=1, C06=1, C07=13, C09=2, C10=1, C17=1, C19=2, C20=1, C26=2, C27=1.
- C13: C01=6, C02=2, C03=2, C04=1, C05=1, C06=1, C08=10, C09=1, C11=3, C16=1, C20=1, C22=1, C23=1.
- C14: C01=1, C02=3, C03=2, C04=3, C05=1, C06=9, C07=2, C08=1, C09=1, C16=2, C19=2, C24=1, C25=1.
- C15: C01=1, C02=1, C03=2, C04=2, C05=1, C06=3, C07=1, C08=1, C09=8, C11=1, C16=2, C20=1.
- C16: C01=2, C03=4, C05=3, C06=2, C08=1, C09=2, C10=1, C11=1, C13=1, C14=2, C15=2, C17=1, C19=3.
- C17: C01=2, C02=2, C03=6, C04=3, C05=1, C06=1, C07=2, C08=2, C09=3, C10=12, C12=1, C16=1, C20=1, C21=1, C22=1, C23=1, C24=2, C25=2.
- C18: C01=9, C02=1, C03=3, C04=1, C05=1, C09=3, C20=1, C21=1, C22=3, C23=2.
- C19: C01=1, C02=1, C03=1, C04=2, C05=2, C06=1, C07=3, C12=2, C14=2, C16=3, C20=1, C27=1.
- C20: C01=2, C02=2, C03=2, C04=6, C07=1, C08=1, C09=1, C10=1, C12=1, C13=1, C15=1, C17=1, C18=1, C19=1, C21=4, C26=1.
- C21: C01=3, C02=1, C03=2, C04=4, C10=2, C11=1, C17=1, C18=1, C20=4, C22=1.
- C22: C01=4, C03=1, C04=1, C08=1, C09=1, C10=1, C13=1, C17=1, C18=3, C21=1, C23=6.
- C23: C01=4, C03=1, C08=1, C09=1, C10=1, C13=1, C17=1, C18=2, C22=6.
- C24: C02=1, C03=4, C04=1, C06=1, C07=1, C09=2, C10=3, C14=1, C17=2, C25=5.
- C25: C02=1, C03=4, C04=1, C06=1, C07=1, C09=2, C10=3, C14=1, C17=2, C24=5.
- C26: C04=2, C07=1, C12=2, C20=1.
- C27: C07=1, C12=1, C19=1.

### Useful two-cluster counterfactuals

`Cleared` counts presently limited games made coverage-complete if both clusters alone became supported. `Synergy` is the clearance beyond the sum of their individual solo clearances.

| Pair | Cleared | Predicted complete | Synergy | Interpretation |
|---|---:|---:|---:|---|
| C02 + C06 | 10 | 20 | 2 | Highest static clearance, but C02 is substantially broader than C06. |
| C05 + C06 | 10 | 20 | 1 | Same clearance; C05 remains a compound search/fallback transaction. |
| C06 + C14 | 9 | 19 | 1 | Strong Shredder-deck concentration; C14 requires temporary deathtouch and target semantics. |
| C02 + C04 | 8 | 18 | 4 | Highest synergy, but combines two dependency-heavy target/response systems. |
| C02 + C07 | 7 | 17 | 2 | Shares target/choice state, though the two transactions are otherwise distinct. |
| C04 + C05 | 7 | 17 | 2 | High dependency breadth; not a sensible first sequence solely for clearance. |
| C01 + C06 | 7 | 17 | 1 | C06 is bounded; C01 is not. |
| C03 + C05 | 7 | 17 | 1 | Both converge on token infrastructure but require different parent transactions. |

Other seven-game pairs have zero synergy: C02+C05, C03+C06, C05+C14, C06+C07, C06+C13, and C06+C18. No two-cluster counterfactual by itself makes more than 20/180 games coverage-complete. This confirms that residual limitations remain strongly overlapping and fragmented.

## Hypotheses and ranking

Ranking prioritizes measured solo clearance, exact bounded grammar, reuse of accepted infrastructure, prerequisite count, and evidence scope. Frequency is a secondary discriminator.

### 1. Bounded Action candidates

1. **C06 Super Shredder departure trigger** — five solo clearances, 34 reaches in 25 games; exact, generic, and composed largely from accepted departure provenance, trigger and counter machinery.
2. **C20 Donatello conditional ETB Draw** — one solo clearance, 14 reaches in 13 games; bounded but requires correct intervening-if semantics at both trigger and resolution.
3. **C10 ETB mill three** — no solo clearance, 21 reaches in 16 games; mechanically narrow and reusable, but it does not presently unlock a complete game alone.
4. **C12 ETB Draw then discard** — no solo clearance, 19 reaches in 18 games; existing Draw/discard machinery reduces breadth, but ordered compound evidence and empty-library behavior remain material.
5. **C21 artifact-entry self-counter** — no solo clearance, 8 reaches in 8 games; close to existing artifact opportunity evidence and counter placement.
6. **C24 activated temporary Reach** and **C26 conditional variable Draw** are bounded shapes, but each has zero solo clearance and limited empirical leverage; C26 also needs variable multi-Draw semantics.

### 2. Candidates requiring a small prerequisite first

- **C03 Zoo Escapees** needs generic permanent-departure trigger delivery before its Mutagen-token payload can be considered; a correct C06 implementation is likely to supply much of that parent architecture, but canonical Mutagen activation remains separate.
- **C07 Ray Fillet** needs generic authoritative counter-removal as a nonmana cost from a selected controlled creature.
- **C11 Rock Soldiers** needs the optional constrained-target transaction.
- **C13 Ravenous Robots** needs temporary set-valued keyword effects.
- **C15 Tunnel Rats** needs graveyard-source activation permission.
- **C16 Make Your Move** needs authoritative disjunctive target predicates.
- **C25 Frog Butler mana ability** needs color choice and mana-ability treatment.

### 3. Compound/dependency-heavy mechanics

C01, C02, C04, C05, C08, C14, C17, C18, C22, C23, and C27 each combine multiple missing child semantics or linked transactions. Their raw exposure is not equivalent to bounded implementability. C02 and C05 have attractive solo clearance, but their target/replacement and search/fallback dependencies respectively make them poor immediate substitutes for a narrower C06 Action.

### 4. Broad mechanics that should remain deferred

- **C09 Menace** changes blocker legality throughout combat and should not be reduced to a presence keyword merely to clear telemetry.
- **C19 graveyard casting plus finality replacement** spans alternate-zone casting permission, characteristic qualification, entry counters and a zone-change replacement effect. Its ten reached games yield zero solo clearance.

### Comparison with the pre-Action #14 interpretation

The previous interpretation's first recommendation, Dream Beavers, is now fully removed from the unsupported set. Its second-ranked follow-up, Super Shredder's departure-trigger counter, becomes the strongest post-Action candidate because its static solo clearance rises from zero in the pre-Action overlap graph to five after Dream Beavers support removes the co-limitation in those games.

The prior follow-up queue remains broadly recognizable—Donatello conditional ETB Draw, Stockman Draw/discard, Donatello artifact-entry counter, mill three, and Ray Fillet's activation all remain residual clusters—but their order changes under actual post-Action memberships. C20 is the best narrowly bounded alternative with positive solo clearance; C10, C12 and C21 clear no game alone; C07 clears two but first requires a new counter-removal cost transaction. The post-Action evidence therefore strengthens rather than overturns the former second-ranked hypothesis.

## Recommendation

### Action #15 hypothesis

Implement exactly the bounded generic trigger grammar:

> **Whenever another permanent leaves the battlefield, put a +1/+1 counter on this source.**

Authoritative corpus membership for this exact represented shape is **Super Shredder only** in the frozen ten-deck environment. This is a semantic grammar recommendation, not card-name dispatch.

Measured exposure:

- 34 REACHED / UNSUPPORTED occurrences;
- 25 distinct games;
- 9 matchups;
- 1 exposing deck, Shredder;
- 5 solo game clearances;
- static predicted coverage-complete result: **10 → 15 of 180**.

Reusable accepted dependencies:

- authoritative permanent-departure objects and opportunity-context provenance;
- source/controller/object identity and zone lineage;
- trigger creation, Stack identity, Priority/pass and resolution;
- +1/+1 counter placement and immutable transaction evidence;
- deterministic conformance evidence and SBA boundaries.

Minimum missing semantics:

- exact recognizer for the generic self-referential shape;
- authoritative departure-event-to-trigger delivery for every other permanent;
- immutable proof that the departing permanent is not the trigger source;
- frozen trigger controller/source/event identity;
- resolution that places a counter only if the source is still an appropriate battlefield object, while allowing the independently existing trigger to resolve if the source has left;
- deterministic evidence sufficient to distinguish simultaneous departures and triggers.

Estimated breadth is low-to-moderate. It introduces no target, choice, cost, replacement effect, alternate zone permission, variable quantity, or combat keyword. This is the clearest bounded Action #15 hypothesis supported by post-Action #14 evidence.

This recommendation does **not** authorize implementation. The predicted 15/180 result is static and must not be treated as a guaranteed dynamic outcome.

