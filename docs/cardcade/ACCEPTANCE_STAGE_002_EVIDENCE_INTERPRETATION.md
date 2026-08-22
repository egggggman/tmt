# Acceptance Stage #002 Evidence Interpretation

## Purpose and decision boundary

Acceptance Stage #002 is accepted empirical conformance evidence, not an instruction to drive the
unsupported count to zero. This report interprets its 16 exact REACHED / UNSUPPORTED semantic keys
and 66 classified occurrences to identify the smallest evidence-backed next engine hypothesis.

It does not implement or authorize Action #13, alter decks or Pilot behavior, make balance claims,
or authorize smoke testing, calibration, or Prototype 0.3.

## Accepted evidence baseline

- Raw Stage #002 results: `docs/cardcade/ACCEPTANCE_STAGE_002_RESULTS_02.json`
- Results Audit #2: **ACCEPT**
- Distinct games / duplicate executions: `16 / 32`
- EXECUTED: `10` unique semantic keys / `15` occurrences
- REACHED / UNSUPPORTED: `16` unique semantic keys / `66` occurrences
- PRESENT / UNREACHED: `209` unique semantic keys / `142` semantic occurrences
- Authenticated EXECUTED references: `55`
- Authoritative contexts / context-witness links: `56 / 68`
- Typed-event witnesses: `32`
- Runner stops / invariant violations: `0 / 0`

Only Casey Jones, Jury-Rig Justiciar's top-four selection fragment overlaps Acceptance #001. The
other 15 exact reached semantic keys are new Stage #002 exposure.

## Interpretation method

Ranking weighs:

1. classified occurrence and distinct-game leverage;
2. frozen card/deck exposure;
3. ability to clear the exact reached fragment rather than merely recognize a child payload;
4. reuse of accepted Engine 0.8 and Action infrastructure;
5. gameplay significance in the observed matches;
6. number and depth of still-missing dependencies;
7. implementation and independent-audit complexity.

Witness count is reported but not treated as execution count. Multiple authoritative opportunities
can map to one classified semantic occurrence, and one context can support multiple witnesses.

## Exact reached-semantic inventory

Frequency is games / classified occurrences / witnesses. “Clears?” asks whether one bounded,
truthful implementation of the named candidate could make the observed exact fragment fully
supported without first implementing another major semantic family.

| Card and exact semantic | Frozen deck exposure | Frequency | Missing dependency boundary | One bounded candidate clears? |
|---|---|---:|---|:---:|
| Buzz Bots — `When this creature dies, draw a card.` | April, Donatello, Krang | 8 / 13 / 13 | death-trigger delivery; fixed Draw | **Yes** |
| Utrom Scientists — ETB tap up to one creature and put a stun counter on it, including stun replacement reminder | April, Krang | 6 / 9 / 9 | ETB trigger; optional target; tap; stun counter; untap replacement | No single small candidate |
| Dream Beavers — ETB opponent loses 1, controller gains 1, then Scry 1 | Splinter, Shredder | 4 / 8 / 8 | ETB trigger; life loss/gain; sequential delivery; supported Scry child | Yes, but compound |
| Fugitive Droid — sacrifice activation to counter a spell targeting controlled artifact/creature | April, Donatello, Krang | 4 / 6 / 8 | response Priority; Stack targeting; sacrifice cost; counterspell; target predicate | No |
| Super Shredder — another permanent leaves, put a +1/+1 counter on it | Shredder | 3 / 5 / 13 | generic permanent-departure trigger; counter delivery | **Yes** |
| Donatello, Turtle Techie — ETB, if artifact controlled, Draw | Donatello | 2 / 4 / 4 | ETB trigger; artifact predicate; fixed Draw | **Yes** |
| Donatello, Way with Machines — controlled artifact enters, put a +1/+1 counter on Donatello | Donatello | 2 / 3 / 3 | artifact-entry trigger; counter delivery | **Yes** |
| Ravenous Robots — mana/tap activation gives controlled creature tokens haste until EOT | Casey | 3 / 3 / 6 | activation child; scoped temporary keyword/continuous effect | **Yes**, medium complexity |
| Ray Fillet, Man Ray — pay mana and remove a +1/+1 counter from a controlled creature to Draw | April, Krang | 3 / 3 / 12 | nonmana counter-removal cost; source choice; fixed Draw | No small candidate |
| Casey Jones, Jury-Rig Justiciar — ETB top-four artifact reveal/selection, hand movement, random bottom order | Casey | 3 / 3 / 3 | selection; reveal; multi-card movement; deterministic random ordering | Yes, high complexity |
| Rock Soldiers — ETB destroy up to one target noncreature artifact | Casey | 2 / 2 / 2 | optional constrained target; destroy/zone movement | **Yes**, medium complexity |
| Stockman, Mad Fly-entist — ETB Draw then Discard | Krang | 2 / 2 / 2 | ETB trigger; fixed Draw; hand choice/Discard; sequencing | **Yes**, medium complexity |
| Casey Jones, Vigilante — ETB Draw three plus delayed next-upkeep random Discard three | Casey | 2 / 2 / 2 | ETB trigger; Draw; delayed trigger; deterministic random Discard | No small candidate |
| Shredder, Unrelenting — ETB/attack grants another target controlled creature deathtouch until EOT | Shredder | 1 / 1 / 1 | modal event trigger; constrained target; temporary keyword; deathtouch | Yes, high dependency |
| Courier of Comestibles — ETB Food search/reveal/shuffle or conditional Food creation | Michelangelo | 1 / 1 / 1 | search; reveal; selection; shuffle; conditional branch; supported token child | No small candidate |
| Zoo Escapees — leaves battlefield, create Mutagen; reminder contains unsupported Mutagen activation | Bebop & Rocksteady, Michelangelo | 1 / 1 / 1 | departure trigger; supported token child; separate Mutagen activation remains unsupported | **No** exact-fragment clearance from trigger alone |

Totals reconcile to 66 classified occurrences. Deck exposure is static frozen-manifest membership;
it does not claim every listed copy produced a runtime opportunity.

## Ranked candidate capabilities

### 1. Bounded dies-trigger delivery: Draw one card

**Observed target:** Buzz Bots — 13 occurrences in 8 games, exposed by 3 frozen decks.

This has the strongest combination of exact-fragment elimination, repeated real-game relevance, and
dependency readiness. Cardcade already has:

- authoritative battlefield-to-graveyard/new-object identity;
- typed departure/death opportunity evidence;
- generic trigger objects, Stack placement, Priority/pass, and resolution;
- deterministic Draw movement and empty-library failed-Draw/SBA handling;
- immutable Action evidence patterns and generic `SemanticCoverage`.

The missing slice is narrow: convert an authoritative dies event for the represented source into a
generic trigger lifecycle whose fixed child is Draw one. It does not require target selection,
nonmana costs, replacement effects, temporary layers, or response targeting. A truthful bounded
implementation would clear one exact Stage semantic key and all 13 observed occurrences.

### 2. Bounded ETB life-change sequence followed by Scry 1

**Observed target:** Dream Beavers — 8 occurrences in 4 games, 2 decks.

This receives substantial dependency credit because Scry is already implemented and audited. It
would exercise generic ETB delivery and authoritative life changes. It ranks below dies→Draw because
the fragment is compound: opponent life loss, controller life gain, sequencing, trigger delivery,
and the supported Scry child must all remain one truthful transaction. The gameplay impact is high,
but so is the audit surface.

### 3. Bounded permanent-departure trigger: put one +1/+1 counter on source

**Observed target:** Super Shredder — 5 occurrences and 13 witnesses in 3 games, 1 deck.

Zone departure, runtime identity, counters, layers, and trigger infrastructure already exist. This
is arguably the smallest implementation after dies→Draw and could establish reusable departure
delivery. It ranks third because it affects only one frozen deck and fewer classified occurrences.

### 4. Bounded artifact-conditional ETB Draw

**Observed target:** Donatello, Turtle Techie — 4 occurrences in 2 games, 1 deck.

Stage instrumentation already proves the relevant artifact predicate. Fixed Draw exists. The
remaining engine work is a conditional ETB trigger path. This is high readiness but narrower game
and deck leverage than the top three.

### 5. Bounded artifact-entry trigger: put one +1/+1 counter on source

**Observed target:** Donatello, Way with Machines — 3 occurrences in 2 games, 1 deck.

Artifact-entry contexts and counter application are represented. This is a clean reusable trigger
shape, but its empirical reach is lower than the preceding candidates.

### 6. ETB tap plus stun counter

**Observed target:** Utrom Scientists — 9 occurrences in 6 games, 2 decks.

Raw leverage is second only to Buzz Bots, but one implementation must truthfully cover optional
constrained targeting, tapping, stun-counter identity, and the replacement rule when the permanent
would untap. Implementing only the ETB parent or initial counter would leave the exact fragment
partially unsupported. It is therefore a poor next bounded checkpoint despite high frequency.

### 7. Creature-token haste activation

**Observed target:** Ravenous Robots — 3 occurrences in 3 games, 1 deck.

The activation shell and mana/tap costs are ready. The missing child requires scoped token
selection, temporary haste, layer/duration recomputation, and cleanup. It is coherent but offers
less leverage than generic trigger delivery.

### 8. ETB Draw then Discard

**Observed target:** Stockman — 2 occurrences in 2 games, 1 deck.

Draw, hand identity, discard movement, choices, Stack, and triggers all have extension paths. The
compound selection/sequencing surface makes it less attractive than fixed dies→Draw.

### 9. Optional targeted artifact destruction

**Observed target:** Rock Soldiers — 2 occurrences in 2 games, 1 deck.

This would extend generic target/choice and destroy-zone semantics, but its empirical leverage is
small and it introduces more legality surface than the top candidates.

### 10. Top-four artifact selection and random bottom ordering

**Observed target:** Casey Jones, Jury-Rig Justiciar — 3 occurrences in 3 games, 1 deck.

This is the only exact Stage reach that overlaps Acceptance #001. It would provide useful library
selection coverage but requires multi-card hidden-information choice, reveal, hand movement, and
engine-owned deterministic random ordering. It is not a small Action #13.

### 11. Counter-removal-cost Draw activation

**Observed target:** Ray Fillet — 3 occurrences and 12 witnesses in 3 games, 2 deck manifests.

The parent activation architecture is ready, but generic nonmana counter-removal costs and selection
are not. Partial support would not truthfully clear the fragment.

### 12. Shredder ETB/attack deathtouch grant

One occurrence, one deck. It combines trigger modes, constrained targeting, temporary effects, and
unimplemented deathtouch damage semantics. Defer.

### 13. Casey Vigilante Draw/delayed random Discard

Two occurrences, one deck. Delayed trigger identity and deterministic random multi-card Discard are
substantial dependencies. Defer.

### 14. Fugitive Droid sacrifice/counter response

Six occurrences across four games and three decks give this high raw leverage, but it is the most
architecturally expensive observed fragment: response windows, spell targeting, target predicates,
sacrifice cost, and counterspell resolution must all be correct together. It should not be attacked
until those components are independently justified.

### 15. Courier Food search/conditional token branch

One occurrence. Although Create Token and canonical Food activation exist, search/reveal/shuffle,
conditional branching, and selection dominate the fragment. Defer.

### 16. Zoo Escapees departure Mutagen fragment

One occurrence. A generic departure trigger could deliver the already-supported Create Token child,
but the same fragment's Mutagen activation reminder remains explicitly unsupported. Implementing
only the parent would not clear the exact semantic key, so it receives no pair-elimination credit at
this stage.

## Dependency map

| Reusable dependency | Reached semantics benefiting | Current implication |
|---|---|---|
| Generic ETB/death/departure trigger delivery | Buzz Bots, Dream Beavers, Super Shredder, Donatello Turtle Techie, Donatello Way with Machines, Stockman, Rock Soldiers, Utrom, Courier, Zoo Escapees | Largest shared parent opportunity; implement one bounded child at a time |
| Fixed Draw with failed-draw SBA | Buzz Bots, Donatello Turtle Techie, Stockman, Ray Fillet, Casey Vigilante | Engine boundary exists; parent/cost/choice remains the limiter |
| Target/choice expansion | Utrom, Rock Soldiers, Shredder, Fugitive Droid, Casey Jury-Rig | High reuse but broad legality surface; not one small Action |
| Nonmana activation costs | Ray Fillet, Fugitive Droid | Requires transactional cost components and authoritative subject choice |
| Temporary keyword/layer duration | Ravenous Robots, Shredder | Existing layer foundation extends cleanly, but downstream keyword rules differ |
| Supported child Actions | Dream Beavers→Scry; Zoo/Courier→Create Token | Parent support receives leverage only when the whole observed fragment can be truthful |

## Recommended Action #13 hypothesis

**Recommend exactly one next candidate: bounded generic “When this creature dies, draw a card” trigger delivery.**

Evidence-backed scope:

- Oracle-derived and card-name independent;
- authoritative source must die from the battlefield;
- new-object/zone identity remains correct;
- create a distinct trigger object from the typed death event;
- place it on Stack through the existing trigger machinery;
- use engine-owned Priority/pass;
- resolve a fixed Draw-one child through existing Draw and failed-draw/SBA boundaries;
- preserve reconstructive event → source → trigger → Stack → Draw evidence;
- do not generalize to arbitrary death triggers, death replacement, “another creature dies,”
  multi-card Draw, or other trigger children.

Expected empirical leverage if independently validated: one exact Stage semantic key, 13 classified
occurrences, 8 of 16 games, and frozen exposure across April, Donatello, and Krang. Any changed
trajectories would be execution consequences, not balance evidence.

## Decision

Stage #002 demonstrates that Cardcade's next likely engine value lies in bounded generic trigger
delivery, not in chasing every high-count compound interaction. Dies→Draw is the smallest candidate
with the highest independently observed leverage and the fewest unsupported dependencies.

**Recommendation: nominate bounded dies-trigger Draw-one as Action #13 for a future explicitly authorized checkpoint. Do not implement it from this report alone.**
