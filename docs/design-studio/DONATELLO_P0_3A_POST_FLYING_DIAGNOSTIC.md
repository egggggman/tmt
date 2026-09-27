# Donatello Prototype 0.3a Post-Flying Diagnostic

Decision: `READY_FOR_240_GAME_SMOKE`

This is a compact deterministic semantic diagnostic, not a balance result and
not authorization to change a deck. It was run after generic Flying coverage
landed on `main`.

## Repository and input identity

- Repository: `83b8e1e169493e038cfb74cb8bda5a0801dbc76a`
- Runtime: Cardcade `engine07.py`; current frozen engine identity
  `a7d6c18dd88cb9d76cda79a62aebeab5fe66dc03`
- Game lifecycle: repository-owned `run_smoke_game` from `smoke01.py`
- Pilot: `tmnt_design_studio.pilot07.AcceptancePilot`
- Donatello P0.3a SHA-256:
  `25812e2d7f0ac64ae2476c0d62298db35196d1719c9376b5369d5080faa6aad1`
- Shredder P0.3 SHA-256:
  `818e9a847fcdf8521f53ab9b49c0f054ddd6f9bce95e9fd57c89cb6c94da2ed2`
- Raphael P0.3 SHA-256:
  `220ea90ccc579e09bef38ce972ba84f661c2382b92c7a4559667d24a5eec6f51`
- Casey Jones P0.3 SHA-256:
  `f18d2dd6591520e495a0c723e1d15f5d3f4f6ce8a2693e4f93be0cd6660e838f`

The diagnostic used seeds `3000–3009`, one Donatello-first orientation for
each seed, against Shredder, Raphael, and Casey Jones: 30 games total. No
full 240-game smoke was run.

## Way with Machines telemetry

| Measure | Result |
| --- | ---: |
| Games | 30 |
| Runtime errors | 0 |
| Draws | 28 |
| Casts / resolutions | 19 / 19 |
| Observed turns on battlefield | 65 |
| Qualifying artifact entries | 5 |
| Trigger count / resolutions | 5 / 5 |
| +1/+1 counters placed | 5 |
| Peak counters on one Way | 2 |
| Peak observed P/T | 4/4 |

All five triggers were ordinary artifact casts: three `Buzz Bots` and two
`Fugitive Droid`. No token or recovered-artifact recast generated a Way trigger
while Way was present in this sample.

## Flying legality and combat pressure

The diagnostic-only combat wrapper inspected the same engine legality surface
used by `legal_block_options`; it did not alter choices or rules behavior.

| Measure | Result |
| --- | ---: |
| Way attack assignments | 23 |
| Attacks where Flying filtered at least one ordinary blocker | 9 |
| Attacks with no legal Flying/Reach blocker among available creatures | 9 |
| Successful blocks by Flying/Reach creatures | 0 |
| Way attacks with no Way block | 23 |
| Direct combat-damage events from Way | 23 |
| Direct combat damage from Way | 37 |
| Games where Way died | 10 |

The representative pattern was an attacking Way with ordinary opposing
creatures available: the legal blocker set contained no ordinary blocker, so
the Pilot received only the unblocked choice. The five counter resolutions
raised Way to observed 4/4 in the largest case, and later Way damage included
2- and 3-point direct assignments. There was no observed Flying/Reach blocker,
so this sample does not exercise a successful evasion-eligible block.

These are observed outcomes, not counterfactual proof that Flying alone caused
the extra damage. Relative to the previous pre-Flying diagnostic, the observed
sample moved from 14 Way attack assignments and 28 direct damage to 23 and 37;
the legality log also directly records nine filtered attacks.

## Does Machines and Technique confirmation

| Measure | Result |
| --- | ---: |
| Does Machines casts / resolutions | 25 / 25 |
| Successful level-2 advancements | 21 |
| Recovered artifact zone movements | 36 |
| Casts matching recovered artifact names | 39 |
| Technique draws | 11 |
| Technique casts / resolutions | 11 / 11 |
| Cards drawn through Technique | 22 |
| Sneak executions | 9 |

The recovered-card cast figure is a name-based observation: the current smoke
event stream records the recovery object movement and later spell card names,
but does not link every later cast to the exact recovered object identity. It is
therefore not treated as exact per-copy reuse telemetry.

The setup → level-2 recovery path and Technique path remain active. However,
the recovered artifacts did not contribute a Way trigger in these 30 games.

## Descriptive results

| Matchup | Donatello W-L-D | Opponent W-L-D |
| --- | ---: | ---: |
| Donatello / Shredder | 3-7-0 | 7-3-0 |
| Donatello / Raphael | 0-10-0 | 10-0-0 |
| Donatello / Casey Jones | 2-8-0 | 8-2-0 |
| Aggregate | 5-25-0 | 25-5-0 |

The prior compact diagnostic was 3–27. The movement to 5–25 is descriptive
only and is not statistical balance evidence.

## Remaining semantic gaps

The following remain outside this diagnostic and are not being implemented here:

- Donatello, Gadget Master's artifact-copy trigger;
- Donatello, Mutant Mechanic activation/transfer behavior;
- Sewer-veillance Cam abilities;
- Bespoke Bō remaining support semantics; and
- Does Machines level-3 artifact animation/counters.

No evidence in this compact run identifies one of those mechanics as clearly
preventing the represented setup → recovery → Way/Flying conversion chain from
functioning. Their absence remains a limitation on later interpretation.

## Decision and next gate

`READY_FOR_240_GAME_SMOKE`

Way with Machines now benefits from generic Flying legality: ordinary blockers
are excluded, counter growth is observed, and the enlarged creature produces
direct combat pressure without engine errors. Technique and Does Machines
level-2 behavior also remain exercised. The remaining gaps are better evaluated
through broader matchup evidence before selecting another isolated semantic
slice.

The next gate is one exact frozen 240-game smoke using the already authenticated
P0.3/P0.3a inputs, unchanged schedule, seeds, and orientation rule. This
diagnostic does not authorize deck edits, a new prototype, calibration, or
additional semantic implementation.
