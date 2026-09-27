# Donatello Prototype 0.3a Way with Machines Diagnostic

Decision: `FLYING_COVERAGE_REQUIRED`

This is a 30-game semantic diagnostic, not a balance result or a smoke
authorization.

## Evidence and identities

The run used the current `main` repository at `03a0f2d1eb345c5d2f35783667e0989f13152ed6`
and the repository-owned `run_smoke_game` lifecycle used by
`tools/run_prototype_0_3_prebalance_smoke.py`. It used one Donatello-first game
for each seed 3000–3009 against Shredder, Raphael, and Casey Jones.

Deck inputs were authenticated by the existing smoke identities:

- Donatello P0.3a: `25812e2d7f0ac64ae2476c0d62298db35196d1719c9376b5369d5080faa6aad1`
- Shredder P0.3: `818e9a847fcdf8521f53ab9b49c0f054ddd6f9bce95e9fd57c89cb6c94da2ed2`
- Raphael P0.3: `220ea90ccc579e09bef38ce972ba84f661c2382b92c7a4559667d24a5eec6f51`
- Casey Jones P0.3: `f18d2dd6591520e495a0c723e1d15f5d3f4f6ce8a2693e4f93be0cd6660e838f`

No deck, engine, Pilot, schedule, or harness behavior was changed.

## Way with Machines telemetry

| Measure | Result |
| --- | ---: |
| Games | 30 |
| Way draws | 28 |
| Games with Way drawn | 20 |
| Way casts | 19 |
| Way resolutions | 19 |
| Observed turns on battlefield | 73 |
| Qualifying artifact entries | 5 |
| Trigger count | 5 |
| Trigger resolutions | 5 |
| +1/+1 counters placed | 5 |
| Maximum counters on one Way | 2 |
| Peak observed P/T | 4/4 |

All five qualifying entries were normal artifact casts: three `Buzz Bots` and
two `Fugitive Droid`. There were no artifact-token triggers and no recovered-
artifact recast triggers. Thus the complete setup → recovery → recast → Way
loop did not occur in this sample, despite 21 Does Machines level-2
activations and 36 artifacts recovered.

## Combat pressure

The existing combat events show:

- 14 combat-damage assignments with Way as the source;
- 15 direct combat-damage events from Way, totaling 28 damage;
- 18 observed combat assignments targeting Way as the blocker/defender;
- no explicit counterfactual event proving that a counter changed a survival or
  trade outcome; and
- no recorded lethal event attributed specifically to Way.

Representative pressure exists. In Shredder seed 3004, Way dealt 1 damage on
three attacks before the first counter, then 2 and later 3 damage after its
two counters; it eventually blocked `Dream Beavers`. In seed 3007 it reached
2 counters, attacked into creature blocks, and dealt 2–3 damage on subsequent
attacks. These are observed state changes, not counterfactual balance proof.

The card's canonical Flying ability is still not represented in the broader
combat-choice surface. Repeated block engagements and several early deaths
make it impossible to conclude that the intended evasive conversion is being
tested. Flying is therefore materially suppressing the payoff measurement.

## Does Machines interaction

- Does Machines casts/resolutions: 26/26.
- Level-2 activations: 21.
- Artifacts recovered: 36.
- Recovered artifacts subsequently cast: 18.
- Recovered artifacts contributing Way triggers: 0 in this sample.

The setup/recovery loop is active, but its recovered recasts did not overlap
with a surviving Way with Machines permanent in these 30 games.

## Technique confirmation

Technique was drawn 12 times, cast 12 times, resolved 12 times, and drew 24
cards. No Technique Sneak execution appeared in this Donatello-first sample.
This confirms the draw path remains active but does not provide new Sneak
frequency evidence.

## Descriptive results

| Matchup | Donatello W-L | Opponent W-L |
| --- | ---: | ---: |
| Donatello / Shredder | 1-9 | 9-1 |
| Donatello / Raphael | 0-10 | 10-0 |
| Donatello / Casey Jones | 2-8 | 8-2 |
| Aggregate | 3-27 | 27-3 |

There were 30 completed games, zero runtime errors, and no retries. These
small-sample results are directional only.

## Decision and next gate

The artifact-entry trigger is functioning in normal games and produces real
counters, larger P/T, attacks, and damage. However, only five triggers occurred,
none came from the recovered-artifact loop, and the missing Flying ability is
central to whether the enlarged creature can convert into reliable pressure.

Required decision: `FLYING_COVERAGE_REQUIRED`.

Next gate: implement the smallest faithful reusable Flying coverage, then run a
new compact diagnostic before considering another 240-game smoke. Gadget Master,
Mutant Mechanic, Sewer-veillance Cam, Bespoke Bō, and Does Machines level 3
remain unresolved. This artifact does not declare Donatello balanced or ready
for human-play authorization.
