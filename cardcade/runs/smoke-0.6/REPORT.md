# Cardcade Engine 0.6 — Generic Card-Fact Modeling

## Protocol and governance

Frozen Prototype 0.2 roster; seed `20260809`; all 45 matchups; 20 games each;
900 games total; exact 10/10 starting-player split. Engine 0.5's fully neutralized
condition is the primary baseline. No decklist, Prototype history, or card value was
changed to target a win rate.

## Aggregate results

| Deck | 0.5 neutralized | 0.6 | Shift | Flood | Execution |
|---|---:|---:|---:|---:|---:|
| Leonardo | 44.4% | 34.4% | -10.0% | 25.6% | 1.7% |
| Raphael | 46.1% | 32.8% | -13.3% | 26.1% | 20.0% |
| Donatello | 66.7% | 70.0% | +3.3% | 24.4% | 83.9% |
| Michelangelo | 43.9% | 54.4% | +10.6% | 27.2% | 6.7% |
| Splinter | 50.6% | 19.4% | -31.1% | 26.1% | 0.0% |
| April O'Neil | 51.1% | 63.9% | +12.8% | 22.2% | 81.1% |
| Casey Jones | 46.7% | 57.2% | +10.6% | 21.7% | 86.1% |
| Shredder | 42.8% | 41.7% | -1.1% | 23.3% | 16.1% |
| Krang | 65.0% | 70.6% | +5.6% | 26.7% | 82.2% |
| Bebop & Rocksteady | 42.8% | 55.6% | +12.8% | 33.9% | 11.7% |

First-player win rate: **50.3%** (0.5 neutralized: 52.7%).

## Generic role use and execution telemetry

Values below are average cards with each derived role cast per game. Missing roles are zero.

| Deck | Threat | Removal | Draw | Support | Tempo | Acceleration | Finisher |
|---|---:|---:|---:|---:|---:|---:|---:|
| Leonardo | 5.04 | 0.57 | 0.00 | 1.11 | 0.00 | 0.00 | 0.00 |
| Raphael | 4.88 | 0.00 | 2.11 | 0.50 | 0.00 | 0.00 | 0.00 |
| Donatello | 4.57 | 1.58 | 2.48 | 0.37 | 0.00 | 0.00 | 0.00 |
| Michelangelo | 4.91 | 0.39 | 0.00 | 0.00 | 0.00 | 0.39 | 0.00 |
| Splinter | 5.10 | 0.66 | 0.00 | 0.58 | 0.00 | 0.00 | 0.00 |
| April O'Neil | 5.01 | 1.03 | 3.74 | 0.39 | 0.00 | 0.00 | 0.00 |
| Casey Jones | 4.92 | 0.48 | 1.79 | 1.57 | 0.00 | 0.00 | 0.00 |
| Shredder | 5.14 | 0.96 | 0.71 | 1.28 | 0.00 | 0.00 | 0.00 |
| Krang | 4.72 | 1.27 | 3.23 | 0.33 | 0.00 | 0.00 | 0.00 |
| Bebop & Rocksteady | 4.96 | 1.33 | 0.71 | 0.00 | 0.00 | 0.43 | 0.00 |

## Seven surviving Engine 0.5 polarity matchups

| Matchup | 0.5 neutralized | 0.6 | Shift |
|---|---:|---:|---:|
| Leonardo–Donatello | 30.0% | 15.0% | -15.0% |
| Leonardo–Krang | 25.0% | 25.0% | +0.0% |
| Donatello–April O'Neil | 70.0% | 60.0% | -10.0% |
| Donatello–Shredder | 85.0% | 80.0% | -5.0% |
| Splinter–Shredder | 75.0% | 35.0% | -40.0% |
| Casey Jones–Krang | 20.0% | 30.0% | +10.0% |
| Shredder–Krang | 30.0% | 20.0% | -10.0% |

## Stability interpretation

The >15-point stability gate records **18** unexplained threshold exceedances.
Threshold-exceeding pairings: `splinter_vs_krang` (-45%), `raphael_vs_splinter` (+40%), `raphael_vs_bebop_rocksteady` (-40%), `splinter_vs_shredder` (-40%), `splinter_vs_bebop_rocksteady` (-40%), `leonardo_vs_bebop_rocksteady` (-35%), `raphael_vs_michelangelo` (-35%), `michelangelo_vs_shredder` (+35%), `raphael_vs_april_oneil` (-30%), `splinter_vs_april_oneil` (-30%), `splinter_vs_casey_jones` (-30%), `raphael_vs_casey_jones` (-25%), `donatello_vs_splinter` (+25%), `casey_jones_vs_shredder` (+25%), `leonardo_vs_raphael` (-20%), `leonardo_vs_michelangelo` (-20%), `raphael_vs_shredder` (-20%), `raphael_vs_krang` (-20%).

All large movements are changes in modeled information: anonymous curve slots and
deck-authored multipliers were replaced by real card types/text and universal heuristic
weights. They are therefore explained architecturally, but smoke resolution cannot validate
whether the remaining universal weights represent real games.

Krang affinity savings are **1.18 mana/game**.
Bebop & Rocksteady flood remains a direct consequence of its frozen land count. Historical
0.1–0.5 artifacts remain preserved in adjacent run directories.

## Value provenance and decision

Card-derived: card identity/count, mana value/cost, type, Oracle text, keywords, threat and
spell roles, artifact permanence/token setup/payoff, affinity eligibility/floor, and which
role counters are incremented. Heuristic and universal: role-unit magnitudes, score weights,
one-step line-choice constants, artifact milestone values, starting-player bonus, mulligan
penalty, interaction target cap, and closing variance. Legacy profile priors remain
inspectable but have no classification, line-choice, or outcome effect.

Cardcade is **not trustworthy enough** to resume Design Studio deck revisions. Prototype
0.3 remains unauthorized. The next specific correction is richer rules-text semantic and
magnitude modeling: quantify token/draw/removal effects, conditional/modal/triggered value,
creature combat contribution, and target/relevance constraints. Zero tempo and finisher use
and 18 >15-point shifts show that universal role labels alone are not a stable outcome model.
