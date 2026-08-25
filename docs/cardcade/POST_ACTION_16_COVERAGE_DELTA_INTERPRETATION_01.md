# Post-Action #16 Coverage Delta Interpretation #1

## Scope and evidence boundary

This report interprets the independently accepted post-Action #15 and post-Action #16
Coverage-Aware Engine Smoke Stage 0.1 artifacts. It does not rerun games, assess balance, modify
Cardcade, authorize Action #17, or authorize calibration or Prototype 0.3.

Authoritative post-Action #16 input:

- merged execution baseline: `e600e680f3b974490dcb5cb1beab24d0c998a630`;
- raw artifact SHA-256: `e02b34b885d2e139f4eee21cc0ee760ac998d33163fd5c6a872e3b0fedd12965`;
- Results Audit #1 SHA-256: `2538d77a2e5211d08e2f3fac1d406a574e956dde493c7d10516d3a461f5d7bda`;
- accepted result: 45 pairings, 180 distinct games, 360 executions, 180 byte-identical duplicate
  pairs, zero invalid games, zero runner stops, and zero invariant violations.

Static counterfactuals in this report predict only semantic coverage classification. They do not
predict game outcomes or balance.

## Observations

### Coverage movement

| Measure | Post-#15 | Post-#16 | Delta |
| --- | ---: | ---: | ---: |
| Coverage-complete games | 17 | 18 | +1 |
| Coverage-limited games | 163 | 162 | -1 |
| REACHED / UNSUPPORTED occurrences | 562 | 548 | -14 |
| Exact Action #16 unsupported reaches | 14 | 0 | -14 |

All 17 post-Action #15 coverage-complete games remain complete. The sole newly complete game is:

`donatello--leonardo:canonical:8052`

Its pre-Action reached set contained only the Donatello conditional ETB Draw fragment. Its winner and
ending turn remain Leonardo on turn 16. The post-Action game contains no Action #16 execution because
the intervening condition did not produce a qualifying trigger, but the engine now authoritatively
understands that nonexecution. This is a direct semantic-support clearance, not a trajectory-induced
clearance. It exactly realizes the static `17 → 18` prediction.

There are no complete-to-limited regressions.

### Direct Action #16 clearance versus trajectory movement

Before implementation, the exact fragment was REACHED / UNSUPPORTED in 13 games and 14 occurrences.
After implementation it has zero unsupported reaches. Eight authenticated executions occurred in
seven games and six matchups; the remaining six formerly reached games legitimately produced no
Action #16 execution under the represented intervening-if lifecycle.

| Game | Executions | Pre result | Post result | Coverage effect |
| --- | ---: | --- | --- | --- |
| `april_oneil--donatello:canonical:8006` | 1 | April T23 | April T23 | target removed; other limits remain |
| `bebop_rocksteady--donatello:canonical:8021` | 1 | Donatello T20 | Donatello T18 | target removed; trajectory shortened; other limits remain |
| `casey_jones--donatello:canonical:8036` | 1 | Casey T13 | Casey T13 | target removed; other limits remain |
| `donatello--krang:canonical:8050` | 1 | Donatello T19 | Donatello T19 | target removed; other limits remain |
| `donatello--leonardo:canonical:8051` | 1 | Donatello T33 | Donatello T33 | target removed; other limits remain |
| `donatello--leonardo:reversed:8052` | 1 | Leonardo T15 | Leonardo T15 | target removed; other limits remain |
| `donatello--raphael:reversed:8055` | 2 | Donatello T18 | Donatello T18 | target removed; other limits remain |

The only changed winner/turn among these games is the two-turn shortening of
`bebop_rocksteady--donatello:canonical:8021`. The authenticated Draw is a measured new transaction,
but the artifact does not isolate which later Pilot choice or game-state consequence caused the
earlier finish. The report therefore records association, not strategic causality.

Across the complete 180-game comparison there are zero newly reached unsupported fragment/game
pairs. Every one of the 13 removed fragment/game pairs is the exact Action #16 fragment. All 25
remaining fragments retain exactly their post-Action #15 occurrence and game counts. Action #16
therefore caused no new unsupported trajectory in this matrix.

## Residual coverage graph

The post-Action #16 artifact contains exactly 25 exact Oracle-fragment clusters totaling 548 reached
occurrences. `Solo` is the number of currently limited games whose entire reached set is that one
fragment. `CF` is the resulting static coverage-complete count if that cluster alone became fully
supported (`18 + Solo`).

| ID | Card / exact Oracle fragment | Occ. | Games | Matchups | Decks | Solo | CF | Dependency readiness and breadth |
| --- | --- | ---: | ---: | ---: | --- | ---: | ---: | --- |
| C01 | Utrom Scientists — ETB tap up to one target creature and put a stun counter on it, with untap replacement reminder | 61 | 44 | 17 | April, Krang | 6 | 24 | Compound/heavy: ETB and counters exist; needs optional constrained targeting, tap state, stun counter, and rules-wide untap replacement. |
| C02 | Courier of Comestibles — optional Food search/reveal/hand/shuffle with conditional Food-token fallback | 35 | 22 | 9 | Michelangelo | 5 | 23 | Compound/heavy: Food/token/zones exist; needs typed optional search, reveal, shuffle, choice, and fallback transaction. |
| C03 | Zoo Escapees — leaves battlefield, create a Mutagen token with reminder activation | 50 | 34 | 16 | Bebop, Michelangelo | 3 | 21 | Compound/prerequisite: departure triggers and token creation exist; full fragment still requires canonical Mutagen activation/targeting. |
| C04 | Shredder, Unrelenting — enters or attacks, another target controlled creature gains deathtouch until EOT | 15 | 13 | 8 | Shredder | 3 | 21 | Compound/moderate-heavy: ETB/attack triggers exist; needs dual trigger grammar, constrained target, temporary deathtouch, and cleanup. |
| C05 | Casey Jones, Jury-Rig Justiciar — top-four artifact selection and random-bottom remainder | 67 | 42 | 17 | Casey, Raphael | 2 | 20 | Compound/heavy: library identity/bottoming exist; needs look-N, typed optional reveal/selection, hand move, and randomized remainder. |
| C06 | Fugitive Droid — sacrifice activation countering a spell that targets a controlled artifact or creature | 47 | 36 | 21 | April, Donatello, Krang | 2 | 20 | Compound/heavy: activation/Stack exist; needs sacrifice cost, response timing, Stack targeting, target-of-target validation, and counterspell. |
| C07 | Ray Fillet — `{2}`, remove a +1/+1 counter from a controlled creature: Draw | 30 | 29 | 14 | April, Krang | 2 | 20 | Small prerequisite: activation, counters, costs, and Draw exist; needs chosen-creature counter removal as an atomic nonmana cost. |
| C08 | Ravenous Robots — `{R}, {T}`: controlled creature tokens gain haste until EOT | 18 | 13 | 7 | Casey | 2 | 20 | Compound/moderate: activation exists; needs set-valued token predicate and temporary continuous haste. |
| C09 | Wingnut Alliance — choice of flying, menace, or haste until EOT | 15 | 14 | 7 | Raphael | 2 | 20 | Compound/heavy: Alliance provenance exists; needs immutable mode choice and three temporary keywords, including Menace. |
| C10 | Rock Soldiers — ETB destroy up to one target noncreature artifact | 21 | 15 | 8 | Casey | 1 | 19 | Small prerequisite/moderate: ETB/destruction exist; needs optional constrained artifact target and live legality. |
| C11 | Make Your Move — destroy target artifact, enchantment, or creature with power 4+ | 17 | 13 | 6 | Leonardo | 1 | 19 | Moderate: spell/Stack/destruction exist; needs disjunctive target predicates and live characteristic validation. |
| C12 | Tunnel Rats — `{4}{B}` return this card from graveyard to battlefield tapped | 17 | 14 | 7 | Splinter | 1 | 19 | Bounded/moderate: activation/cost/zones exist; needs graveyard-source permission, new incarnation, and tapped entry. |
| C13 | Leonardo, Sewer Samurai — graveyard creature casting permission plus finality entry/death replacement | 14 | 10 | 6 | Leonardo | 1 | 19 | Broad/deferred: alternate-zone casting, characteristic qualification, entry counter, and replacement effect. |
| C14 | Casey Jones, Vigilante — ETB draw three, then next-upkeep random discard three | 27 | 23 | 9 | Casey | 0 | 18 | Compound/heavy: Draw/discard exist; needs multi-Draw, delayed trigger across turns, and random discard. |
| C15 | Menace reminder text | 22 | 22 | 14 | Bebop, Raphael, Splinter | 0 | 18 | Broad/deferred combat legality: needs multi-blocker declarations and combat-choice integration. |
| C16 | Paramecia Coloniex — ETB mill three | 21 | 16 | 9 | Bebop | 0 | 18 | Bounded/low-moderate: ETB/zones exist; needs mill-N, incarnation transitions, and short-library ordering. |
| C17 | Stockman — ETB draw one, then discard one | 19 | 18 | 9 | Krang | 0 | 18 | Bounded compound: Draw/discard exist; needs ordered mandatory choice and terminal Draw boundary. |
| C18 | Paramecia — dies, optional exile, reflexive graveyard target to library top | 16 | 12 | 9 | Bebop | 0 | 18 | Compound/heavy: dies/zones exist; needs optional self-exile, reflexive trigger, and graveyard targeting. |
| C19 | Donatello, Way with Machines — artifact-entry self +1/+1 counter | 8 | 8 | 5 | Donatello | 0 | 18 | Bounded/low: artifact ETB history, triggers, and counters already exist; zero solo leverage. |
| C20 | Raphael Alliance — optional exile top card | 7 | 7 | 6 | Raphael | 0 | 18 | Compound/dependent: Alliance/library identity exist; needs optional exile and durable source linkage for C21. |
| C21 | Raphael attacks — may play a card exiled with Raphael until EOT | 6 | 6 | 5 | Raphael | 0 | 18 | Compound/dependent on C20: source-linked exile set, play permission, timing, and costs. |
| C22 | Frog Butler — `{2}` gains reach until EOT | 5 | 5 | 3 | Bebop | 0 | 18 | Bounded/low: activation/mana exist; needs temporary Reach and cleanup; zero solo leverage. |
| C23 | Frog Butler — `{T}` add one mana of any color | 5 | 5 | 3 | Bebop | 0 | 18 | Small prerequisite: tap activation exists; needs color choice and mana-ability treatment. |
| C24 | Krang — intervening-if variable Draw to four cards in hand | 4 | 3 | 2 | Krang | 0 | 18 | Bounded grammar but needs hand-count condition, variable multi-Draw, and repeated failed-Draw handling. |
| C25 | Ooze Spill — counter target spell, then create Mutagen token | 1 | 1 | 1 | Krang | 0 | 18 | Compound/heavy: needs counterspell targeting plus complete Mutagen semantics. |

### Complete sparse overlap matrix

For `Cyy=s/p`, `s` is shared games and `p` is the number of currently limited games cleared if the
row cluster and Cyy both became supported. Only the upper triangle is shown. Omitted pairs have zero
overlap. This enumerates all 160 nonzero residual relationships.

- C01: C02=3/11, C03=6/10, C04=2/9, C05=5/9, C06=18/12, C07=19/10, C08=2/8, C09=1/9, C10=1/7, C12=1/7, C13=1/7, C14=3/7, C15=4/7, C16=3/6, C17=12/6, C18=2/6, C19=1/6, C22=1/6, C23=1/6.
- C02: C03=11/9, C04=1/8, C05=3/8, C06=5/9, C07=3/7, C08=1/7, C09=1/7, C10=1/6, C11=3/6, C12=1/6, C13=2/6, C15=1/5, C16=1/5, C17=1/5, C18=1/5.
- C03: C04=2/6, C05=4/5, C06=3/5, C07=5/5, C08=2/5, C09=3/5, C10=1/4, C11=4/5, C12=2/5, C13=1/4, C14=2/3, C15=5/3, C16=10/4, C17=3/4, C18=6/3, C19=2/3, C20=1/3, C21=1/3, C22=4/3, C23=4/3.
- C04: C05=1/5, C06=2/6, C07=1/5, C11=2/5, C13=2/5, C14=1/3, C15=1/4, C22=1/3, C23=1/3.
- C05: C06=2/4, C07=2/5, C08=6/4, C09=9/7, C10=11/5, C11=2/4, C12=1/3, C13=1/4, C14=13/3, C15=5/2, C16=2/2, C17=3/2, C18=2/2, C19=3/4, C20=4/2, C21=4/2.
- C06: C07=14/4, C08=1/4, C09=1/4, C10=1/3, C12=2/3, C13=2/4, C14=2/2, C15=1/2, C16=3/2, C17=6/2, C18=3/2, C19=4/3, C20=1/2, C22=1/2, C23=1/2, C24=2/3.
- C07: C12=1/3, C13=3/3, C15=1/2, C16=3/2, C17=13/3, C18=2/2, C22=1/2, C23=1/2, C24=1/2, C25=1/2.
- C08: C10=3/3, C11=1/3, C14=10/3, C15=1/2, C20=1/2, C21=1/2.
- C09: C15=3/2, C19=1/2, C20=3/2, C21=2/2.
- C10: C11=1/2, C12=1/2, C14=9/3, C15=1/1, C19=1/1.
- C11: C12=2/3, C13=3/2, C14=1/1, C15=2/1, C16=1/1, C18=1/1.
- C12: C14=1/1, C15=8/7.
- C13: C17=2/1, C25=1/1.
- C14: C15=2/0, C16=2/0, C18=2/0, C20=1/0, C21=1/0.
- C15: C16=4/0, C17=2/0, C18=3/0, C20=1/0, C21=1/0, C22=2/0, C23=2/0.
- C16: C17=1/0, C18=12/1, C19=2/0, C20=1/0, C21=1/0, C22=3/0, C23=3/0.
- C17: C18=1/0, C24=2/1, C25=1/0.
- C18: C19=1/0, C20=1/0, C21=1/0, C22=2/0, C23=2/0.
- C19: C20=1/0.
- C20: C21=6/1.
- C22: C23=5/0.

### Highest static two-cluster clearances

| Pair | Cleared | Static complete | Implementation interpretation |
| --- | ---: | ---: | --- |
| C01 + C06 | 12 | 30 | Highest result, but combines stun/target/replacement infrastructure with constrained reactive counterspell architecture. |
| C01 + C02 | 11 | 29 | Two large unrelated compound transactions. |
| C01 + C03 | 10 | 28 | Stun subsystem plus incomplete Mutagen token semantics. |
| C01 + C07 | 10 | 28 | High overlap, but still requires the stun subsystem and a new nonmana-cost primitive. |
| C01 + C04 | 9 | 27 | Optional stun targeting plus dual-trigger temporary deathtouch. |
| C01 + C05 | 9 | 27 | Stun subsystem plus complex top-library selection/random-bottom transaction. |
| C02 + C03 | 9 | 27 | Shared token/Food exposure but two compound parent semantics. |
| C02 + C06 | 9 | 27 | Broad search/choice transaction plus reactive Stack targeting. |
| C01 + C09 | 9 | 27 | Stun subsystem plus mode choice and three temporary keywords. |
| C12 + C15 | 7 | 25 | Numerically notable overlap, but combines graveyard return with the broad Menace combat subsystem. |

No high-clearance pair is a small bounded Action batch. The arithmetic is dominated by C01 and other
dependency-heavy parents rather than by two ready generic transactions.

## Hypotheses and candidate ranking

### Bounded or near-bounded candidates

1. **C07 Ray Fillet counter-removal cost → Draw** — two solo clearances and static `18 → 20`.
   Existing activation, mana-cost, counter, controller, Stack/Priority, and Draw infrastructure is
   strong. The missing prerequisite is an authoritative selected-creature `+1/+1` counter removal
   encoded as an atomic nonmana activation cost. This is the highest-leverage candidate near the
   bounded line, but it is a prerequisite-plus-Action sequence rather than one already-composed
   transaction.
2. **C10 Rock Soldiers optional artifact destruction** — one solo clearance and static `18 → 19`.
   ETB, destruction, targets, and artifact characteristics exist, but `up to one` choice and the
   noncreature-artifact target predicate need an exact reusable boundary.
3. **C12 Tunnel Rats graveyard self-return tapped** — one solo clearance and static `18 → 19`.
   It is exact and generic, but introduces graveyard-source activation permission, source payment,
   new incarnation, and tapped entry.
4. **C16 mill three**, **C17 Draw then discard**, and **C19 artifact-entry self-counter** are
   comparatively bounded and reusable, but each clears zero current games alone.
5. **C22 temporary Reach** is narrow, but also clears zero games and adds a temporary keyword whose
   actual gameplay leverage is not exercised by this coverage metric.

### Small-prerequisite candidates

C07 needs selected-permanent counter removal as a cost. C10 needs optional constrained targeting.
C11 needs a reusable disjunctive target predicate. C23 needs color choice and mana-ability treatment.
Each could become a bounded Action after that prerequisite is independently specified and audited.

### Compound/dependency-heavy candidates

C01 through C06 except C07, plus C08, C09, C14, C18, C20, C21, and C25, combine multiple missing
child semantics, linked transactions, temporary continuous effects, response/targeting systems, or
durable source linkage. Their occurrence and clearance counts substantially overstate their
implementation readiness.

### Broad/deferred candidates

C13 combines alternate-zone casting with a finality counter and death replacement. C15 Menace changes
combat legality and blocker choice throughout the engine. Neither should be compressed into a
telemetry-oriented Action merely to raise the coverage-complete count.

## Comparison with the post-Action #15 graph

Action #16 removed exactly its own former cluster: 14 occurrences in 13 games and seven matchups.
Every other cluster retains its prior occurrence count, game count, and corpus exposure. The graph
therefore contracted from 26 to 25 nodes and from 176 to 160 nonzero overlap relationships without
creating a new residual dependency.

The prior second-ranked narrow alternatives remain mechanically plausible, but their leverage has
not improved. The best positive-clearance candidates now either require a new prerequisite (C07,
C10), introduce a new zone permission lifecycle (C12), or are substantially compound. The most
ready zero-clearance semantics would improve represented behavior without making another game
coverage-complete by themselves.

## Decision-path comparison

### Continue targeted Action construction

The strongest evidence-backed construction hypothesis would be a two-checkpoint C07 sequence:

1. specify and audit generic selected controlled-creature `+1/+1` counter removal as an atomic
   activation cost;
2. implement only `{2}, Remove a +1/+1 counter from a creature you control: Draw a card.`

Measured exposure is 30 occurrences across 29 games, 14 matchups, and two decks, with two solo
clearances and a static `18 → 20` prediction. This is testable and reuses mature Draw/counter/cost
infrastructure, but it is not yet a single smallest Action comparable to Actions #13–#16.

### Conduct another Engine Validation Milestone Review

The engine has now completed four independently authenticated full-matrix measurements with stable
mechanics and deterministic duplicates. Unsupported reaches have fallen `692 → 599 → 562 → 548`,
while coverage-complete games have risen only `5 → 10 → 17 → 18`. At the current checkpoint:

- only 18/180 games are coverage-complete;
- 14 of 25 residual clusters clear zero games alone;
- every cluster clearing three or more games is compound or dependency-heavy;
- the best near-bounded positive candidate requires a prerequisite Action;
- no new engine, runner, invariant, or provenance blocker is known.

This is evidence that the remaining bottleneck is increasingly graph structure and semantic breadth,
not a single dominant missing transaction.

## Recommendation

**Recommend a Cardcade Engine Validation Milestone Review before authorizing Action #17.**

The review should decide whether continued single-Action construction remains the best critical path,
or whether the validated engine should enter a deliberately coverage-limited broader measurement
stage while a prerequisite roadmap is designed separately. If the review chooses continued targeted
construction, C07's counter-removal-cost prerequisite and exact Ray Fillet Draw grammar are the
strongest current bounded sequence; this report does not authorize either checkpoint.

This recommendation is based on coverage leverage and implementation breadth only. It is not a
balance conclusion and does not authorize Pilot/deck changes, calibration, Action #17, or Prototype
0.3.

## Observation, hypothesis, and authorization boundary

- **Observed:** Action #16 removed exactly 14 unsupported occurrences, produced eight authenticated
  executions, cleared the one predicted solo game, and created no new unsupported reach.
- **Observed:** the residual graph contains 25 clusters, 548 occurrences, and 160 nonzero overlaps;
  14 clusters have zero solo clearance.
- **Hypothesis:** the C07 prerequisite sequence is the strongest next narrow implementation path if
  targeted construction continues.
- **Recommendation:** perform an Engine Validation Milestone Review first.
- **Not authorized:** Action #17, balance analysis, calibration, Pilot/deck changes, or Prototype 0.3.
