# Post-Action #13 Acceptance Stage #002 Evidence Interpretation

## Purpose and decision boundary

This report interprets the accepted post-Action #13 Stage #002 result to decide whether one missing
semantic capability now clearly warrants Action #14 or whether Cardcade has reached a milestone
where broader deterministic validation is more informative.

It does not implement or authorize Action #14, alter Engine/Pilot/deck behavior, make balance
claims, run smoke testing or calibration, or authorize Prototype 0.3.

## Accepted empirical baseline

- Execution baseline: `768585e13dd10bac1e749a161bbadb4da7de2c97`
- Raw results: `docs/cardcade/ACCEPTANCE_STAGE_002_RESULTS_03.json`
- Raw SHA-256: `ab9471d0320cb1a61b9048b6dc83788f3bfd5d12cb0d58800bc7a0dcd78da50a`
- Results audit commit: `6843fc29f8fd2d02a30254d17461a1c9f46954e3`
- Results Audit #1: **ACCEPT**
- Matrix: 16 games / 32 deterministic executions
- Runner stops / invariant violations / duplicate mismatches: `0 / 0 / 0`
- EXECUTED: 11 semantic keys / 17 occurrences / 70 authenticated references
- REACHED / UNSUPPORTED: 15 semantic keys / 53 occurrences
- PRESENT / UNREACHED: 211 semantic keys / 144 occurrences

Action #13's motivating semantic is no longer part of the residual queue: Buzz Bots dies→Draw
executed 13 times across the same eight games that previously reached it unsupported.

## Ranking method

Each residual exact semantic is weighed using:

1. classified occurrence and distinct-game frequency;
2. frozen-deck exposure;
3. ability for one bounded capability to clear the complete reached fragment;
4. reuse of accepted trigger, Stack/Priority, Draw, Scry, counters, zones, costs, and identity;
5. likely gameplay significance when the opportunity occurs;
6. dependency depth and independent-audit surface;
7. whether another deterministic environment is likely to change the ranking materially.

Witness counts measure authoritative opportunities, not executions. They provide repeated-relevance
evidence but cannot be substituted for classified occurrence or transaction counts.

## Exact residual inventory

Frequency is games / classified occurrences / witnesses.

| Semantic | Frozen exposure | Frequency | Principal missing boundary | One bounded Action clears? |
|---|---|---:|---|:---:|
| Utrom Scientists — ETB tap up to one target creature and add a stun counter | April, Krang | 6 / 9 / 9 | optional constrained target; tap; stun counter; untap replacement | No |
| Dream Beavers — ETB opponent loses 1, controller gains 1, then Scry 1 | Splinter, Shredder | 4 / 8 / 8 | fixed life loss/gain; sequential trigger delivery; supported Scry child | **Yes, compound** |
| Fugitive Droid — sacrifice activation countering a targeting spell | April, Donatello, Krang | 4 / 6 / 8 | response window; Stack target; sacrifice cost; target predicate; counterspell | No |
| Super Shredder — another permanent leaves, add a +1/+1 counter to source | Shredder | 3 / 5 / 13 | generic departure trigger; source-survival predicate; counter child | **Yes** |
| Donatello, Turtle Techie — ETB, if artifact controlled, Draw | Donatello | 2 / 4 / 4 | ETB trigger; authoritative artifact predicate; fixed Draw child | **Yes** |
| Donatello, Way with Machines — controlled artifact enters, add a +1/+1 counter | Donatello | 2 / 3 / 4 | artifact-entry trigger; source counter child | **Yes** |
| Ravenous Robots — mana/tap activation gives creature tokens haste until EOT | Casey | 3 / 3 / 6 | scoped token set; temporary keyword/layer duration | Yes, medium |
| Ray Fillet — mana plus counter-removal cost to Draw | April, Krang | 3 / 3 / 14 | nonmana counter-removal cost; source choice; fixed Draw | No small slice |
| Casey Jones, Jury-Rig Justiciar — top-four artifact selection | Casey | 3 / 3 / 3 | hidden selection; reveal; multi-card movement; randomized bottom order | Yes, high |
| Rock Soldiers — optional constrained ETB artifact destruction | Casey | 2 / 2 / 2 | optional target; noncreature-artifact predicate; destroy movement | Yes, medium |
| Stockman — ETB Draw then Discard | Krang | 2 / 2 / 2 | fixed Draw; hand choice; Discard; sequential trigger delivery | Yes, medium |
| Casey Jones, Vigilante — Draw three plus delayed random Discard three | Casey | 2 / 2 / 2 | delayed trigger; multi-Draw; deterministic random Discard | No small slice |
| Shredder, Unrelenting — ETB/attack grants temporary deathtouch | Shredder | 1 / 1 / 1 | dual event parent; target; temporary keyword; deathtouch rules | No small slice |
| Courier of Comestibles — Food search or conditional Food creation | Michelangelo | 1 / 1 / 1 | search/reveal/shuffle; selection; branch; supported token child | No |
| Zoo Escapees — departure Mutagen creation plus reminder activation | Bebop & Rocksteady, Michelangelo | 1 / 1 / 1 | departure trigger; supported token child; unsupported Mutagen activation | No exact clearance |

The occurrence column reconciles to 53. Static deck exposure does not claim each card copy produced
an opportunity.

## Ranked Action hypotheses

### 1. Dream Beavers — bounded ETB life exchange followed by Scry 1

Empirical leverage: 8 occurrences in 4 games across 2 decks.

This is the strongest remaining direct Action hypothesis. Generic trigger/Stack/Priority delivery,
player life totals, typed evidence, and Scry already exist. A bounded exact sequence could reuse
substantial accepted infrastructure and would have meaningful gameplay impact.

It does not dominate the queue the way dies→Draw did. The complete fragment is compound: opponent
life loss, controller life gain, instruction order, Scry choice, and one trigger transaction must
all remain atomic and auditable. Cardcade has life-change results but no accepted generic fixed
life-loss/gain child equivalent to its mature fixed Draw child.

### 2. Super Shredder — bounded permanent-departure counter trigger

Empirical leverage: 5 occurrences and 13 witnesses in 3 games, but only 1 deck.

This is probably the cleanest reusable implementation candidate. Departure provenance, trigger
delivery, runtime identity, counters, and layers already exist. Correctness still requires another
permanent, source survival through resolution, and authoritative source identity. Its narrow
one-deck exposure prevents it from clearly outranking Dream Beavers.

### 3. Donatello, Turtle Techie — artifact-conditional ETB Draw

Empirical leverage: 4 occurrences in 2 games, 1 deck.

Action #13 supplies a mature fixed Draw trigger child, while accepted witness infrastructure can
prove artifact state. The missing slice is a conditional ETB parent and resolution-time predicate.
This is highly dependency-ready but too narrow to dominate the next project gate.

### 4. Donatello, Way with Machines — artifact-entry counter trigger

Empirical leverage: 3 occurrences / 4 witnesses in 2 games, 1 deck.

Artifact-entry evidence and counter infrastructure exist. This is similarly clean and reusable,
but even narrower than Turtle Techie.

### 5. Utrom Scientists — ETB tap/stun

Empirical leverage: 9 occurrences in 6 games across 2 decks, the largest remaining raw reach.

It ranks below the cleaner candidates because clearing the exact fragment requires optional
constrained targeting, tap state, stun-counter identity, and the untap replacement rule. Shipping
only the visible ETB effect would leave the complete represented semantic partially unsupported.
Its high count does not justify treating several coupled capabilities as one small Action.

### 6. Ravenous Robots — scoped token haste activation

Empirical leverage: 3 occurrences / 6 witnesses in 3 games, 1 deck.

The activation lifecycle and mana/tap costs exist. The missing child is a temporary scoped effect
over controlled creature tokens. It is coherent but requires layer/duration and cleanup evidence,
and affects fewer observed interactions than the leading hypotheses.

### 7. Stockman — ETB Draw then Discard

Empirical leverage: 2 occurrences in 2 games, 1 deck.

Draw, discard movement, choice, and triggers all exist in bounded forms. Their composition into a
new ETB sequence is feasible but offers limited Stage leverage.

### 8. Rock Soldiers — constrained optional artifact destruction

Empirical leverage: 2 occurrences in 2 games, 1 deck.

This would use existing zone identity but introduces a new constrained optional target and destroy
transaction. It has less leverage and more legality surface than the leading candidates.

### 9. Casey Jones, Jury-Rig Justiciar — top-four artifact selection

Empirical leverage: 3 occurrences in 3 games, 1 deck.

It offers useful hidden-information and library-ordering validation but requires selection, reveal,
multi-card movement, and deterministic random bottom ordering. It is not a small next Action.

### 10. Ray Fillet — counter-removal-cost Draw activation

Empirical leverage: 3 occurrences / 14 witnesses in 3 games across 2 manifests.

The activation and Draw endpoints are ready; transactional counter-removal cost and authoritative
subject selection are not. Partial support would not clear the fragment.

### 11–15. Defer

Fugitive Droid has substantial frequency but disproportionate response/target/counterspell/cost
dependencies. Casey Vigilante requires delayed triggers and random multi-card discard. Shredder
requires target expansion plus unimplemented deathtouch semantics. Courier requires search,
reveal, shuffle, selection, and branching. Zoo Escapees cannot clear its exact fragment while the
embedded Mutagen activation remains unsupported. None is an appropriate bounded Action #14 now.

## Why no Action clearly dominates

Action #13 had a distinctive evidence profile:

- 13 occurrences in 8 of 16 games;
- 3 frozen decks;
- one exact fragment;
- a fixed Draw child already implemented;
- no targets, choices, compound instructions, temporary effects, or nonmana costs.

The current leaders split those advantages:

- Utrom has frequency but excessive dependency breadth;
- Dream Beavers has frequency and two-deck reach but compound life/Scry semantics;
- Super Shredder is clean but one-deck-specific in this environment;
- the Donatello triggers are highly ready but narrow;
- the remaining interactions are either low-frequency or architecturally expensive.

Dream Beavers accounts for only 8 of 53 residual occurrences and 4 of 16 games. No candidate has
both broad observed reach and the narrow implementation/audit boundary that justified Action #13.

## Decision: milestone review before Action #14

**Do not authorize Action #14 from this evidence alone.**

Cardcade now has:

- deterministic Acceptance #001;
- an accepted 16-game Stage #002 covering all eight additional frozen decks;
- 603/1 regression validation at the integrated runner baseline;
- zero Stage runner stops, invariant violations, duplicate mismatches, or evidence-authentication
  failures;
- an empirically selected Action whose predicted 13 reaches became 13 authenticated executions;
- no known foundational engine or runner blocker.

The evidence therefore supports a **Cardcade Engine Validation Milestone Review** rather than
immediate Action construction. That review should decide whether to design a modest next
deterministic conformance stage exposing more pairing diversity, or whether Dream Beavers' bounded
ETB life-exchange/Scry sequence is strategically important enough to authorize Action #14 despite
its compound scope.

This is not authorization for the 900-game smoke, calibration, Pilot tuning, deck revisions, or
Prototype 0.3. Any broader validation should remain deterministic, conformance-oriented, and
separately designed and gated.

## Final recommendation

**Recommend Cardcade Engine Validation Milestone Review; keep Action #14 stopped.**

If a later explicit decision requires one Action hypothesis from the current evidence, Dream
Beavers' bounded ETB opponent-loses-1 / controller-gains-1 / Scry-1 sequence ranks first. The
current Stage evidence does not make it dominant enough to bypass the milestone decision.
