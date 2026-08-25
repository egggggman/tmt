# Post-Action #15 Coverage Delta Interpretation #1

## Scope and evidence boundary

This report interprets the independently accepted post-Action #14 and post-Action #15 Coverage-Aware
Engine Smoke Stage 0.1 artifacts. It does not rerun games, assess balance, modify Cardcade, or
authorize another Action. Static counterfactuals predict only coverage classification; they do not
predict changed gameplay trajectories.

Authoritative post-Action #15 input:

- merged baseline: `d1b6c7ac77d0dff26389faf51dccad295145d608`;
- raw artifact SHA-256: `c89affcc6ec5d21123757640d24902d7e1e17927fac57235131fdbf62001e4ab`;
- accepted result: 45 pairings, 180 games, 360 executions, 180 byte-identical duplicate pairs, zero
  runner stops, and zero invariant violations.

## Observations

### Coverage movement

| Measure | Post-#14 | Post-#15 | Delta |
| --- | ---: | ---: | ---: |
| Coverage-complete games | 10 | 17 | +7 |
| Coverage-limited games | 170 | 163 | -7 |
| REACHED / UNSUPPORTED occurrences | 599 | 562 | -37 |
| Exact Action #15 unsupported reaches | 34 | 0 | -34 |

The ten pre-Action coverage-complete games were:

1. `april_oneil--leonardo:reversed:8010`
2. `bebop_rocksteady--leonardo:canonical:8025`
3. `bebop_rocksteady--michelangelo:canonical:8027`
4. `bebop_rocksteady--shredder:reversed:8032`
5. `bebop_rocksteady--splinter:canonical:8033`
6. `bebop_rocksteady--splinter:reversed:8033`
7. `donatello--splinter:reversed:8059`
8. `donatello--splinter:reversed:8060`
9. `leonardo--raphael:canonical:8073`
10. `raphael--splinter:canonical:8088`

All ten remain complete. The seven newly complete games are:

| Game | Action #15 executions | Pre-#15 reached set | Post result versus pre result | Interpretation |
| --- | ---: | --- | --- | --- |
| `bebop_rocksteady--shredder:canonical:8031` | 2 | Action #15 only | Shredder T12 → Shredder T12 | direct static clearance |
| `donatello--shredder:reversed:8057` | 1 | Action #15 only | Shredder T25 → Shredder T25 | direct static clearance |
| `donatello--shredder:reversed:8058` | 3 | Action #15 only | Shredder T21 → Shredder T19 | direct clearance; trajectory also changed |
| `michelangelo--shredder:canonical:8082` | 3 | Action #15 only | Michelangelo T15 → Michelangelo T19 | direct clearance; trajectory also changed |
| `raphael--shredder:canonical:8085` | 0 | Action #15 only | Raphael T23 → Raphael T23 | direct support clearance; no post-Action execution |
| `april_oneil--shredder:reversed:8015` | 8 | Action #15, Shredder deathtouch, Ray Fillet, Fugitive Droid | Shredder T23 → Shredder T15 | trajectory-induced additional clearance |
| `donatello--shredder:canonical:8057` | 6 | Action #15 and Shredder deathtouch | Shredder T20 → Shredder T16 | trajectory-induced additional clearance |

There are no regressions from complete to limited. The static prediction of `10 → 15` correctly
identified the five games whose only pre-Action limitation was Action #15. The observed `10 → 17`
exceeds it because the two last rows no longer reach their other former limitations in the new
deterministic trajectories. Both contain authenticated Action #15 executions and finish earlier, but
the artifacts do not provide a separately randomized counterfactual isolating which individual
counter caused each downstream decision. The report therefore attributes the changed reach sets to
the post-Action trajectory, not to a specific combat counter without direct proof.

### Action #15 execution map

The 55 authenticated executions occur in 16 games and eight matchups:

| Game | Executions | Post coverage | Pre result → post result |
| --- | ---: | --- | --- |
| `april_oneil--shredder:canonical:8015` | 5 | limited | Shredder T16 → T16 |
| `april_oneil--shredder:reversed:8015` | 8 | complete | Shredder T23 → T15 |
| `april_oneil--shredder:reversed:8016` | 5 | limited | Shredder T25 → T13 |
| `bebop_rocksteady--shredder:canonical:8031` | 2 | complete | Shredder T12 → T12 |
| `casey_jones--shredder:reversed:8045` | 4 | limited | Casey Jones T14 → T16 |
| `donatello--shredder:canonical:8057` | 6 | complete | Shredder T20 → T16 |
| `donatello--shredder:canonical:8058` | 1 | limited | Donatello T25 → T25 |
| `donatello--shredder:reversed:8057` | 1 | complete | Shredder T25 → T25 |
| `donatello--shredder:reversed:8058` | 3 | complete | Shredder T21 → T19 |
| `krang--shredder:canonical:8067` | 4 | limited | Shredder T20 → T16 |
| `krang--shredder:canonical:8068` | 1 | limited | Shredder T18 → T16 |
| `krang--shredder:reversed:8067` | 3 | limited | Shredder T17 → T17 |
| `leonardo--shredder:reversed:8076` | 6 | limited | Leonardo T20 → Shredder T41 |
| `michelangelo--shredder:canonical:8082` | 3 | complete | Michelangelo T15 → T19 |
| `shredder--splinter:reversed:8089` | 2 | limited | Splinter T23 → T23 |
| `shredder--splinter:reversed:8090` | 1 | limited | Splinter T19 → T19 |

Twenty-three executions occur in six newly complete games. Nine of those executions occur in four
static solo-clearance games; fourteen occur in the two additional trajectory-induced clearances.
The remaining 32 executions occur in ten still-limited games because other exact fragments remain
reached. Nine of the 16 Action-executing games change winner and/or ending turn; seven retain the
same result. These are measured associations. Only authenticated counter placement and subsequent
state transitions are facts; strategic causality beyond the serialized event chain is not inferred.

## Residual coverage graph

The post-Action artifact contains exactly 26 exact Oracle-fragment clusters totaling 562 reached
occurrences. `Solo` is the limited-game count cleared by supporting only that cluster. `CF` is the
static resulting complete-game count (`17 + Solo`).

| ID | Card / exact Oracle fragment | Occ. | Games | Matchups | Decks | Solo | CF | Dependencies and breadth |
| --- | --- | ---: | ---: | ---: | --- | ---: | ---: | --- |
| C01 | Utrom Scientists — “When this creature enters, tap up to one target creature and put a stun counter on it. …” | 61 | 44 | 17 | April, Krang | 6 | 23 | Compound/heavy: ETB and counters exist; needs optional constrained targeting, tap, stun counter, and untap replacement. |
| C02 | Courier of Comestibles — Food search/reveal/hand/shuffle with conditional Food-token fallback | 35 | 22 | 9 | Michelangelo | 5 | 22 | Compound/heavy: Food/token/zone identity exists; needs optional typed search, reveal, shuffle, and fallback choice transaction. |
| C03 | Shredder, Unrelenting — “Whenever Shredder enters or attacks, another target creature you control gains deathtouch until end of turn.” | 15 | 13 | 8 | Shredder | 3 | 20 | Compound/moderate-heavy: ETB/attack triggers exist; needs dual grammar, constrained target, temporary deathtouch, cleanup. |
| C04 | Casey Jones, Jury-Rig Justiciar — top-four artifact selection and random-bottom remainder | 67 | 42 | 17 | Casey, Raphael | 2 | 19 | Compound/heavy: library identity/bottoming exist; needs look-N, typed optional selection/reveal, hand move, random remainder order. |
| C05 | Zoo Escapees — leaves battlefield → create Mutagen token with reminder activation | 50 | 34 | 16 | Bebop, Michelangelo | 2 | 19 | Compound/prerequisite: departure triggers and token creation exist; full fragment also needs canonical Mutagen activation/targeting. |
| C06 | Ray Fillet — `{2}`, remove a +1/+1 counter from a controlled creature: Draw | 30 | 29 | 14 | April, Krang | 2 | 19 | Small prerequisite: activation/Draw exist; needs chosen-creature counter-removal as atomic nonmana cost. |
| C07 | Ravenous Robots — `{R}, {T}`: controlled creature tokens gain haste until EOT | 18 | 13 | 7 | Casey | 2 | 19 | Compound/moderate: activation exists; needs set-valued token predicate and temporary continuous haste. |
| C08 | Wingnut Alliance — choice of flying, menace, or haste until EOT | 15 | 14 | 7 | Raphael | 2 | 19 | Compound/heavy: Alliance provenance exists; needs immutable mode choice and three temporary keywords, including Menace. |
| C09 | Fugitive Droid — sacrifice activation countering a spell that targets a controlled artifact/creature | 47 | 36 | 21 | April, Donatello, Krang | 1 | 18 | Compound/heavy: activation/Stack exist; needs sacrifice cost, response timing, Stack targeting, target-of-target validation, counterspell. |
| C10 | Rock Soldiers — ETB destroy up to one target noncreature artifact | 21 | 15 | 8 | Casey | 1 | 18 | Small prerequisite/moderate: ETB/destruction exist; needs optional constrained artifact target. |
| C11 | Make Your Move — destroy target artifact, enchantment, or creature power 4+ | 17 | 13 | 6 | Leonardo | 1 | 18 | Moderate: spell/Stack/destruction exist; needs disjunctive target predicates and live characteristic validation. |
| C12 | Tunnel Rats — `{4}{B}`: return this card from graveyard to battlefield tapped | 17 | 14 | 7 | Splinter | 1 | 18 | Bounded/moderate: activation/cost/zones exist; needs graveyard-source permission, new identity, tapped entry. |
| C13 | Donatello, Turtle Techie — “When Donatello enters, if you control an artifact, draw a card.” | 14 | 13 | 7 | Donatello | 1 | 18 | **Bounded/low-moderate:** ETB, artifact state, trigger, Draw and failed-Draw handling exist; needs intervening-if checks. |
| C14 | Casey Jones, Vigilante — ETB draw three; next-upkeep random discard three | 27 | 23 | 9 | Casey | 0 | 17 | Compound/heavy: Draw/discard exist; needs multi-draw, delayed trigger across turns, random discard. |
| C15 | Menace reminder text | 22 | 22 | 14 | Bebop, Raphael, Splinter | 0 | 17 | Broad/deferred combat legality: needs multi-blocker declarations and combat choice integration. |
| C16 | Paramecia Coloniex — ETB mill three | 21 | 16 | 9 | Bebop | 0 | 17 | Bounded but zero solo leverage: ETB/zones exist; needs mill-N and short-library ordering. |
| C17 | Stockman — ETB draw one, then discard one | 19 | 18 | 9 | Krang | 0 | 17 | Bounded compound but zero solo leverage: Draw/discard exist; needs ordered mandatory choice and terminal Draw boundary. |
| C18 | Paramecia — dies, optional exile, reflexive graveyard target to library top | 16 | 12 | 9 | Bebop | 0 | 17 | Compound/heavy: dies/zones exist; needs optional self-exile, reflexive trigger, graveyard target. |
| C19 | Leonardo, Sewer Samurai — graveyard casting permission plus finality replacement | 14 | 10 | 6 | Leonardo | 0 | 17 | Broad/deferred: alternate-zone casting, characteristic test, entry counter, death replacement. |
| C20 | Donatello, Way with Machines — artifact-entry self +1/+1 counter | 8 | 8 | 5 | Donatello | 0 | 17 | Bounded but zero solo leverage: artifact entry witness, triggers, and counters exist. |
| C21 | Raphael Alliance — optional exile top card | 7 | 7 | 6 | Raphael | 0 | 17 | Compound/dependent: Alliance/library identity exist; needs optional exile and durable linkage for C22. |
| C22 | Raphael attacks — may play a card exiled with Raphael until EOT | 6 | 6 | 5 | Raphael | 0 | 17 | Compound/dependent on C21: source-linked exile set, play permission, timing and costs. |
| C23 | Frog Butler — `{2}`: gains reach until EOT | 5 | 5 | 3 | Bebop | 0 | 17 | Bounded but zero solo leverage: activation/mana exist; needs temporary Reach and cleanup. |
| C24 | Frog Butler — `{T}`: add one mana of any color | 5 | 5 | 3 | Bebop | 0 | 17 | Small prerequisite: tap activation exists; needs color choice and mana-ability treatment. |
| C25 | Krang — conditional variable Draw to four cards in hand | 4 | 3 | 2 | Krang | 0 | 17 | Bounded grammar but variable multi-Draw and repeated failed-Draw handling. |
| C26 | Ooze Spill — counter target spell, then create Mutagen token | 1 | 1 | 1 | Krang | 0 | 17 | Compound/heavy: needs counterspell targeting plus complete Mutagen semantics. |

### Complete sparse overlap matrix

For entry `Cyy=s/p`, `s` is shared games and `p` is the number of currently limited games cleared
if the row cluster and Cyy both became supported. Only the upper triangle is shown; omitted pairs
have zero overlap. This enumerates all 176 nonzero residual relationships.

- C01: C02=3/11, C03=2/9, C04=5/9, C05=6/9, C06=19/10, C07=2/8, C08=1/9, C09=18/11, C10=1/7, C12=1/7, C13=2/7, C14=3/7, C15=4/7, C16=3/6, C17=12/6, C18=2/6, C19=1/6, C20=1/6, C23=1/6, C24=1/6.
- C02: C03=1/8, C04=3/8, C05=11/8, C06=3/7, C07=1/7, C08=1/7, C09=5/8, C10=1/6, C11=3/6, C12=1/6, C15=1/5, C16=1/5, C17=1/5, C18=1/5, C19=2/5.
- C03: C04=1/5, C05=2/5, C06=1/5, C09=2/5, C11=2/5, C14=1/3, C15=1/4, C19=2/4, C23=1/3, C24=1/3.
- C04: C05=4/4, C06=2/5, C07=6/4, C08=9/6, C09=2/3, C10=11/5, C11=2/4, C12=1/3, C13=2/3, C14=13/3, C15=5/2, C16=2/2, C17=3/2, C18=2/2, C19=1/3, C20=3/3, C21=4/2, C22=4/2.
- C05: C06=5/4, C07=2/4, C08=3/4, C09=3/3, C10=1/3, C11=4/4, C12=2/4, C13=2/4, C14=2/2, C15=5/2, C16=10/3, C17=3/3, C18=6/2, C19=1/2, C20=2/2, C21=1/2, C22=1/2, C23=4/2, C24=4/2.
- C06: C09=14/3, C12=1/3, C13=1/3, C15=1/2, C16=3/2, C17=13/3, C18=2/2, C19=3/2, C23=1/2, C24=1/2, C25=1/2, C26=1/2.
- C07: C09=1/3, C10=3/3, C11=1/3, C13=1/3, C14=10/2, C15=1/2, C21=1/2, C22=1/2.
- C08: C09=1/3, C13=1/3, C15=3/2, C20=1/2, C21=3/2, C22=2/2.
- C09: C10=1/2, C12=2/2, C13=6/3, C14=2/1, C15=1/1, C16=3/1, C17=6/1, C18=3/1, C19=2/2, C20=4/1, C21=1/1, C23=1/1, C24=1/1, C25=2/1.
- C10: C11=1/2, C12=1/2, C14=9/3, C15=1/1, C20=1/1.
- C11: C12=2/3, C14=1/1, C15=2/1, C16=1/1, C18=1/1, C19=3/1.
- C12: C13=1/2, C14=1/1, C15=8/6.
- C13: C14=1/1, C15=1/1, C16=1/1, C17=1/1, C18=1/1, C19=1/2, C20=4/1, C25=1/1.
- C14: C15=2/0, C16=2/0, C18=2/0, C21=1/0, C22=1/0.
- C15: C16=4/0, C17=2/0, C18=3/0, C21=1/0, C22=1/0, C23=2/0, C24=2/0.
- C16: C17=1/0, C18=12/1, C20=2/0, C21=1/0, C22=1/0, C23=3/0, C24=3/0.
- C17: C18=1/0, C19=2/0, C25=2/1, C26=1/0.
- C18: C20=1/0, C21=1/0, C22=1/0, C23=2/0, C24=2/0.
- C19: C26=1/0.
- C20: C21=1/0.
- C21: C22=6/1.
- C23: C24=5/0.

### Useful two-cluster counterfactuals

| Pair | Cleared | Static complete | Why it matters |
| --- | ---: | ---: | --- |
| C01 + C02 | 11 | 28 | Highest clearance, but combines two large missing subsystems. |
| C01 + C09 | 11 | 28 | Same headline; optional stun targeting plus constrained counterspell is broader still. |
| C01 + C06 | 10 | 27 | Two extra co-limited clearances; both require new cost/target semantics. |
| C01 + C03 | 9 | 26 | No synergy beyond singles; C03 remains target/continuous-effect heavy. |
| C01 + C04 | 9 | 26 | One synergistic clearance, but two complex target/library transactions. |
| C01 + C05 | 9 | 26 | One synergistic clearance; Mutagen reminder semantics remain a second Action. |
| C01 + C08 | 9 | 26 | One synergistic clearance; choice plus three keywords is broad. |
| C02 + C05 | 8 | 25 | One synergistic clearance around token/Food infrastructure, but both parents are compound. |
| C02 + C09 | 8 | 25 | Two broad and unrelated target/choice systems. |
| C04 + C08 | 6 | 23 | Two extra co-limited games, but both require substantial choice architecture. |

No two-cluster result supplies a compelling bounded pair: the highest values all contain C01, C02,
C04, C05, C08, or C09, whose missing prerequisites dominate their apparent clearance leverage.

## Hypotheses and ranking

### Bounded candidates

1. **C13 conditional ETB Draw** — only one solo clearance, but the smallest positive-leverage exact
   grammar. It directly composes accepted ETB trigger, artifact-state, Draw, Stack/Priority, and
   failed-Draw infrastructure.
2. **C12 graveyard self-return tapped** — one clearance and similar exposure, but introduces
   graveyard activation permission and activated-source/new-incarnation rules.
3. **C16 mill three** and **C17 Draw then discard** — mechanically bounded and highly reusable, but
   each clears zero current games alone.
4. **C20 artifact-entry self-counter** — close to Action #15's counter machinery and existing
   artifact opportunity evidence, but clears zero games alone.
5. **C23 temporary Reach** — narrow, but zero solo leverage.

### Small-prerequisite candidates

C06 needs authoritative selected-creature counter removal as an atomic cost; C10 needs optional
constrained targeting; C11 needs disjunctive live target predicates; C24 needs color choice and mana
ability treatment. Each is plausible after its prerequisite but is not smaller than C13 today.

### Compound/dependency-heavy candidates

C01–C05, C07–C09, C14, C18, C21, C22, and C26 combine multiple missing child semantics, linked
transactions, or continuous effects. Their occurrence/clearance counts do not make them bounded.
In particular, C01's six solo clearances require both target/tap/counter delivery and the rules-wide
stun-counter untap replacement; C02's five require search, reveal, selection, shuffle, and fallback.

### Broad/deferred candidates

C15 Menace changes blocker legality throughout combat. C19 combines alternate-zone casting,
characteristic qualification, finality entry state, and a death replacement. Neither should be
reduced to telemetry support to improve the coverage count.

## Comparison with the pre-Action #15 ranking

The prior recommendation predicted five direct Super Shredder clearances; all five occurred, with no
formerly complete game regressing. Dynamic play added two more complete games by avoiding other
unsupported reaches. Removing Super Shredder leaves the former alternatives intact but changes their
relative leverage: Utrom Scientists now has six solo clearances and Courier five, yet both remain
dependency-heavy. The previously identified Donatello conditional ETB Draw remains the strongest
narrowly bounded candidate with positive solo clearance. Mill, ordered Draw/discard, and
artifact-entry counter remain bounded but still clear no game alone.

## Action #16 recommendation

### Hypothesis

Implement only the generic intervening-if ETB trigger grammar represented by:

> **When this source enters, if its controller controls an artifact, draw a card.**

Frozen corpus membership is exactly **Donatello, Turtle Techie**, Oracle ID
`f84850bc-6348-449e-bd82-bb39e2119bec`, TMT collector number `37`.

Measured exposure:

- 14 reached occurrences;
- 13 games;
- 7 matchups;
- one deck, Donatello;
- one solo clearance;
- static coverage prediction: **17 → 18 of 180**.

Reusable dependencies are authoritative ETB incarnation/event provenance, trigger/Stack/Priority,
controller identity, battlefield artifact state, Draw, failed-Draw pending state, and terminal SBA
handling. The principal risks are implementing the condition as a true intervening-if check at both
trigger creation and resolution; evaluating the trigger controller's artifact state rather than a
mutable/current source assumption; preserving source-independent trigger resolution; and not
generalizing to arbitrary conditions, quantities, or card-name dispatch.

### Strongest rejected alternatives

- **C01 Utrom Scientists** clears six games but requires optional targeting, tap state, stun counters,
  and the untap replacement rule—a substantially larger subsystem.
- **C02 Courier of Comestibles** clears five but requires typed search, reveal, shuffle, optional
  choice, and conditional Food-token fallback.
- **C03 Shredder deathtouch** clears three but couples two trigger modes, constrained targeting,
  temporary deathtouch, combat consequences, and cleanup.
- **C06 Ray Fillet** clears two and reuses Draw, but adds selected-creature counter removal as an
  atomic nonmana cost.
- **C12 Tunnel Rats** is comparably bounded with one clearance, but graveyard-source activation and
  new-incarnation/tapped-entry permission are broader than C13's existing ETB/Draw composition.

This is one evidence-backed hypothesis, not authorization to implement Action #16. The `18/180`
result is a static coverage prediction and must be measured dynamically if the Action is later
authorized and accepted.
