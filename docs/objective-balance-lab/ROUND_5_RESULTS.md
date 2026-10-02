# Objective Balance Lab Round 5 — isolated candidate results

The execution request's `OBL-R5-APRIL-A` denotes the approved plan's stable `OBL-R5-APRIL_ONEIL-A`; this is an alias, not a second candidate.

Five preserved candidates played the nine exact OBL-BASELINE-002 opponents each: 4,500/4,500 games, 100 per pairing, 50 starts per seat, no adaptive/replacement seeds, no candidate-vs-candidate games, and zero runtime errors. No baseline was regenerated. The semantic runtime matches the audited Baseline 002 authority. [Raw evidence](ROUND_5_EVIDENCE.json); [checkpoint](ROUND_5_CHECKPOINT.json).
The immutable card diffs and SHA-256 values remain in the [approved design plan](ROUND_5_CANDIDATE_PLAN.md).
Per-card signature casts are recorded, but these Round 5 game rows do not carry draw, activation, attack-gate, or effect-use counters for artifacts. Their absence means unavailable, not zero. The same limitation applies to a direct Reporter combat-draw or Turtle Techie ETB-draw counter.

Mean Matchup Balance Error is the mean of |(wins + draws/2)/100 − 50%| across the deck's nine opponents. Negative Balance Δ is improvement. Counts above 60/40 and 70/30 use strict thresholds.

The audited Baseline 002 environment remains the comparison authority: global balance error 18.96%, median deviation 17.00%, >60/40 34, >70/30 18, WR spread 49.22%, first-player result 50.56%, mean/median ending turn 19.6916/18.0. This isolated round does not claim a new combined-environment metric.

| Candidate | Parent WR → candidate WR | Balance error parent → candidate (Δ) | >60/40 | >70/30 | Most extreme matchup | Hypothesis | Identity | Verdict |
|---|---:|---:|---:|---:|---|---|---|---|
| `OBL-R5-SHREDDER-A` | 75.00% → 74.56% | 25.00% → 24.56% (-0.44 pp) | 7 → 9 | 6 → 5 | krang 88.00% | PARTIALLY_SUPPORTED | IDENTITY_PRESERVED | PROMISING_NEEDS_VARIANT |
| `OBL-R5-SHREDDER-B` | 75.00% → 72.44% | 25.00% → 22.44% (-2.56 pp) | 7 → 7 | 6 → 5 | april_oneil 89.00% | PARTIALLY_SUPPORTED | IDENTITY_PRESERVED | ACCEPT_FOR_COMBINED_MATRIX |
| `OBL-R5-APRIL_ONEIL-A` | 25.78% → 29.78% | 24.22% → 20.22% (-4.00 pp) | 7 → 5 | 5 → 5 | casey_jones 14.00% | PARTIALLY_SUPPORTED | IDENTITY_STRENGTHENED | ACCEPT_FOR_COMBINED_MATRIX |
| `OBL-R5-KRANG-A` | 35.11% → 40.00% | 19.56% → 21.33% (+1.78 pp) | 6 → 8 | 4 → 5 | shredder 15.00% | PARTIALLY_SUPPORTED | IDENTITY_STRENGTHENED | REJECT_BALANCE_REGRESSION |
| `OBL-R5-KRANG-B` | 35.11% → 43.00% | 19.56% → 17.89% (-1.67 pp) | 6 → 8 | 4 → 4 | shredder 14.00% | PARTIALLY_SUPPORTED | IDENTITY_PRESERVED | ACCEPT_FOR_COMBINED_MATRIX |

## Matchup and functional telemetry

### OBL-R5-SHREDDER-A

The first-creature proxy is 0.27 turns later and turn-3/5 board proxies fall, so the early-pressure lever is observable. Power falls only 0.44 pp, however, and >60/40 matchups rise 7 to 9 despite one fewer >70/30 matchup. The Foot/minion pressure identity remains; this is informative but not the preferred combined-matrix build.

| Opponent | Parent | Candidate | Δ |
|---|---:|---:|---:|
| leonardo | 78.00% | 70.00% | -8.00 pp |
| raphael | 58.00% | 63.00% | +5.00 pp |
| donatello | 84.00% | 83.00% | -1.00 pp |
| michelangelo | 71.00% | 76.00% | +5.00 pp |
| splinter | 67.00% | 65.00% | -2.00 pp |
| krang | 89.00% | 88.00% | -1.00 pp |
| bebop_rocksteady | 77.00% | 77.00% | +0.00 pp |
| april_oneil | 91.00% | 87.00% | -4.00 pp |
| casey_jones | 60.00% | 62.00% | +2.00 pp |

First-player result: 73.56% → 72.44%; mean/median ending turn: 18.5278/17.0 → 19.0322/18.0. First-creature proxy (observed games, conditional mean turn): 897, 3.0446 → 897, 3.3188.

Battlefield-presence proxy through turn 3/5/7 (observed games; conditional mean): t3 735;1.302 → 678;1.2566; t5 796;2.0817 → 794;2.0353; t7 836;2.6782 → 831;2.6907. Missing snapshots are not zeroes.

Oracle-text-matched interaction casts per game: 0.0 → 0.0. Full per-card cast counts are in machine evidence; artifact activation counters are only present if emitted by the source runtime.

Changed-card signature casts: Dream Beavers 1061 → 770; Squirrelanoids 981 → 725; Tunnel Rats 0 → 503.

Added-card draw/activation telemetry is unavailable; do not infer zero use.

### OBL-R5-SHREDDER-B

Splitting the cut between a one-drop and Shark Shredder lowers WR by 2.56 pp and mean balance error by 2.56 pp; >70/30 falls 6 to 5 without adding >60/40 pairings. Turn-3/5 board proxies do not fall, so this supports a conversion/opportunity-cost effect, not the predicted early-board dilution. The remaining villain shell preserves identity.

| Opponent | Parent | Candidate | Δ |
|---|---:|---:|---:|
| leonardo | 78.00% | 64.00% | -14.00 pp |
| raphael | 58.00% | 53.00% | -5.00 pp |
| donatello | 84.00% | 83.00% | -1.00 pp |
| michelangelo | 71.00% | 72.00% | +1.00 pp |
| splinter | 67.00% | 67.00% | +0.00 pp |
| krang | 89.00% | 88.00% | -1.00 pp |
| bebop_rocksteady | 77.00% | 77.00% | +0.00 pp |
| april_oneil | 91.00% | 89.00% | -2.00 pp |
| casey_jones | 60.00% | 59.00% | -1.00 pp |

First-player result: 73.56% → 72.89%; mean/median ending turn: 18.5278/17.0 → 19.38/18.0. First-creature proxy (observed games, conditional mean turn): 897, 3.0446 → 897, 3.0847.

Battlefield-presence proxy through turn 3/5/7 (observed games; conditional mean): t3 735;1.302 → 707;1.3296; t5 796;2.0817 → 807;2.1202; t7 836;2.6782 → 845;2.7503. Missing snapshots are not zeroes.

Oracle-text-matched interaction casts per game: 0.0 → 0.0. Full per-card cast counts are in machine evidence; artifact activation counters are only present if emitted by the source runtime.

Changed-card signature casts: Dream Beavers 1061 → 801; Shark Shredder, Killer Clone 594 → 405; Tunnel Rats 0 → 519.

Added-card draw/activation telemetry is unavailable; do not infer zero use.

### OBL-R5-APRIL_ONEIL-A

Moving two Negates into Reporter/Utrom bodies raises WR 4.00 pp and lowers balance error 4.00 pp; >60/40 falls 7 to 5. First-creature proxy is 0.26 turns earlier and turn-5/7 presence rises slightly, but turn-3 presence and >70/30 count do not improve. Reporter and adaptive Utrom tempo strengthen identity. Baseline Negate had zero casts, so this converts dormant slots rather than measuring the cost of lost permission. Reporter combat-draw is not credited as simulated value.

| Opponent | Parent | Candidate | Δ |
|---|---:|---:|---:|
| leonardo | 49.00% | 41.00% | -8.00 pp |
| raphael | 9.00% | 18.00% | +9.00 pp |
| donatello | 36.00% | 41.00% | +5.00 pp |
| michelangelo | 21.00% | 24.00% | +3.00 pp |
| splinter | 11.00% | 22.00% | +11.00 pp |
| shredder | 9.00% | 17.00% | +8.00 pp |
| krang | 48.00% | 47.00% | -1.00 pp |
| bebop_rocksteady | 31.00% | 44.00% | +13.00 pp |
| casey_jones | 18.00% | 14.00% | -4.00 pp |

First-player result: 25.78% → 29.56%; mean/median ending turn: 20.6378/19.0 → 20.8133/19.0. First-creature proxy (observed games, conditional mean turn): 872, 7.039 → 877, 6.7765.

Battlefield-presence proxy through turn 3/5/7 (observed games; conditional mean): t3 611;1.3437 → 611;1.3437; t5 814;2.1499 → 814;2.1769; t7 870;2.8644 → 874;2.9142. Missing snapshots are not zeroes.

Oracle-text-matched interaction casts per game: 1.1644 → 1.1789. Full per-card cast counts are in machine evidence; artifact activation counters are only present if emitted by the source runtime.

Changed-card signature casts: April, Reporter of the Weird 750 → 1038; Negate 0 → 0; Utrom Scientists 739 → 932.

Added-card draw/activation telemetry is unavailable; do not infer zero use.

### OBL-R5-KRANG-A

Mouser casts and turn-3/5/7 presence show a real artifact-linked board lever; WR rises 4.89 pp. Yet balance error worsens 1.78 pp, >60/40 rises 6 to 8, and >70/30 rises 4 to 5. The matchup spread, not its aggregate WR, rejects this otherwise thematic candidate. Baseline Negate had zero casts, so the observed change is active artifact bodies replacing dormant slots.

| Opponent | Parent | Candidate | Δ |
|---|---:|---:|---:|
| leonardo | 68.00% | 71.00% | +3.00 pp |
| raphael | 13.00% | 20.00% | +7.00 pp |
| donatello | 46.00% | 42.00% | -4.00 pp |
| michelangelo | 32.00% | 33.00% | +1.00 pp |
| splinter | 20.00% | 27.00% | +7.00 pp |
| shredder | 11.00% | 15.00% | +4.00 pp |
| bebop_rocksteady | 51.00% | 61.00% | +10.00 pp |
| april_oneil | 52.00% | 69.00% | +17.00 pp |
| casey_jones | 23.00% | 22.00% | -1.00 pp |

First-player result: 37.33% → 40.89%; mean/median ending turn: 20.1156/19.0 → 20.2044/19.0. First-creature proxy (observed games, conditional mean turn): 809, 9.3424 → 807, 9.2924.

Battlefield-presence proxy through turn 3/5/7 (observed games; conditional mean): t3 608;1.1678 → 608;1.2336; t5 756;1.9193 → 746;2.0067; t7 810;2.6481 → 825;2.7636. Missing snapshots are not zeroes.

Oracle-text-matched interaction casts per game: 1.4811 → 1.4633. Full per-card cast counts are in machine evidence; artifact activation counters are only present if emitted by the source runtime.

Changed-card signature casts: Mouser Mark III 0 → 548; Negate 0 → 0.

Added-card draw/activation telemetry is unavailable; do not infer zero use.

### OBL-R5-KRANG-B

Artifact-linked Turtle Techie bodies raise WR 7.89 pp, improve balance error 1.67 pp, and modestly increase turn-5/7 presence. However, >60/40 rises 6 to 8 while >70/30 stays at 4; the conditional ETB draw lacks a direct effect-use counter here. Two Donatello cameos remain technology support rather than a new deck identity. Baseline Negate had zero casts; this is an active-body substitution, not an observed interaction tradeoff. Combined validation must test the extra extremes and identity risk before any promotion.

| Opponent | Parent | Candidate | Δ |
|---|---:|---:|---:|
| leonardo | 68.00% | 74.00% | +6.00 pp |
| raphael | 13.00% | 22.00% | +9.00 pp |
| donatello | 46.00% | 50.00% | +4.00 pp |
| michelangelo | 32.00% | 37.00% | +5.00 pp |
| splinter | 20.00% | 29.00% | +9.00 pp |
| shredder | 11.00% | 14.00% | +3.00 pp |
| bebop_rocksteady | 51.00% | 61.00% | +10.00 pp |
| april_oneil | 52.00% | 64.00% | +12.00 pp |
| casey_jones | 23.00% | 36.00% | +13.00 pp |

First-player result: 37.33% → 46.22%; mean/median ending turn: 20.1156/19.0 → 20.3167/19.0. First-creature proxy (observed games, conditional mean turn): 809, 9.3424 → 826, 8.977.

Battlefield-presence proxy through turn 3/5/7 (observed games; conditional mean): t3 608;1.1678 → 608;1.1809; t5 756;1.9193 → 737;1.9525; t7 810;2.6481 → 818;2.7078. Missing snapshots are not zeroes.

Oracle-text-matched interaction casts per game: 1.4811 → 1.4922. Full per-card cast counts are in machine evidence; artifact activation counters are only present if emitted by the source runtime.

Changed-card signature casts: Donatello, Turtle Techie 0 → 447; Negate 0 → 0.

Added-card draw/activation telemetry is unavailable; do not infer zero use.

## Preserved candidate identities

| Candidate | Exact diff from Baseline 002 | Candidate SHA-256 |
|---|---|---|
| `OBL-R5-SHREDDER-A` | -1 Dream Beavers; -1 Squirrelanoids; +2 Tunnel Rats | `7431daaed35e68d663a88f6e529444e468500b393d4676aaa658bb0c2a564139` |
| `OBL-R5-SHREDDER-B` | -1 Dream Beavers; -1 Shark Shredder, Killer Clone; +2 Tunnel Rats | `1ce0828b6ac107bc8cdf2e0b965d919e83941316803880a71d11bbbb48902fc1` |
| `OBL-R5-APRIL_ONEIL-A` | -2 Negate; +1 April, Reporter of the Weird; +1 Utrom Scientists | `ebaff265d90b5cfbec4f7e9662a9d105f9ef8f58a17b06949626ed2ff898b8b7` |
| `OBL-R5-KRANG-A` | -2 Negate; +2 Mouser Mark III | `565b5e0c0486d04c631ccefa238fc0c16af13d13c4b6d409fd12d4ea82a24ca9` |
| `OBL-R5-KRANG-B` | -2 Negate; +2 Donatello, Turtle Techie | `d1691343e948d96f454468fb360c85e2f68dbe04ae7eed545430560153816bcd` |

## Interpretation and next gate

Compared with [Round 3](ROUND_3_DELTA_RESULTS.md), Shredder's earlier single-card substitutions did not supply a viable balance correction; the R5-B split across opening and closing slots is a distinct, measurable lever. April R3-A's small isolated value-density gain and R3-B's reactive failure motivated this proactive board experiment. Krang R3-A's setup-oriented mixed result and R3-B's high-end regression motivated the two conversion tests here. These are different semantic runtime baselines, so historical percentages are context, not paired deltas.

Negate registers zero signature casts in the exact April and Krang Baseline 002 parent samples, and remains zero in their candidate samples. These experiments therefore test whether making two dormant slots into castable bodies changes outcomes. They do not measure an actual loss of reactive-spell use. This is the strongest shared card-role signal; it is a deck-level association, not proof that a particular drawn Negate caused a loss.

April Reporter's combat-draw trigger and Tunnel Rats' graveyard return are not credited without runtime evidence. Mouser's other-artifact attack condition and Turtle Techie's conditional ETB draw are considered only to the extent the current engine executes them. The historical `interaction_casts` source field counts distinct cast card names, not interaction spells; this report independently filters signature-cast counts by the runner's Oracle-text interaction-name rule. Both values remain in machine evidence. No hand-size, flood/screw, unused-mana, stabilization, or loss-cause values are invented.

Provisional Combined 004 pool: {"april_oneil": "OBL-R5-APRIL_ONEIL-A", "krang": "OBL-R5-KRANG-B", "shredder": "OBL-R5-SHREDDER-B"}. This is a recommendation only; no combined matrix or promotion occurred.
