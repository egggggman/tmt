# Cardcade Engine 0.4 Smoke Sensitivity Report

## Protocol

- Frozen Prototype 0.1 roster: 10 decks; no decklist changes
- Seed: `20260809`
- Games: 20 per pairing, 45 unique pairings, 900 total
- Starting players: exactly 10/10 in every pairing
- Engine: `cardcade-0.4.0`; run schema `1.3.0`

## Sensitivity

| Signal | Engine 0.1 | Engine 0.2 | Engine 0.3 | Engine 0.4 |
|---|---:|---:|---:|---:|
| First-player win rate | 52.2% | 52.6% | 52.2% | 53.1% |
| Donatello win rate | 50.0% | 48.9% | 64.4% | 67.2% |
| Krang win rate | 38.9% | 71.1% | 61.7% | 62.8% |
| Krang affinity mana saved/game | n/a | 2.92 | 2.34 | 2.47 |
| Shredder win rate | 61.1% | 52.8% | 47.2% | 46.7% |

Engine 0.4 does not tune these results toward 50%. Donatello remains a strong balance hypothesis,
not a deck-change recommendation. Its artifact setup rate is 98.3%, payoff-cast rate is 97.8%,
payoff-realization rate is 94.4%, and full execution rate is 92.2%. The pilot rejected 2.48
available payoff lines and 9.71 legal sequencing alternatives per game on average; it preserved
resources in 15.0% of games. Detection therefore no longer guarantees pursuit or realization.

Krang retains card-derived affinity exclusively on `Krang, Master Mind`; its two blue mana remain
undiscountable. It realizes an artifact payoff in 81.1% of games and saves 2.47 affinity mana per
game. The small increase from 2.34 is a sequencing result, not a return to profile-wide affinity.
Shredder remains stable after the Engine 0.2 interaction correction.

## Previously large Engine 0.2 to 0.3 matchups

| Matchup (first deck's win rate) | 0.2 | 0.3 | 0.4 | 0.3 to 0.4 |
|---|---:|---:|---:|---:|
| Donatello vs Shredder | 35% | 75% | 80% | +5 points |
| Splinter vs Krang | 10% | 45% | 50% | +5 points |
| Donatello vs April O'Neil | 50% | 85% | 85% | 0 points |
| Donatello vs Michelangelo | 50% | 75% | 75% | 0 points |
| Donatello vs Krang | 30% | 50% | 45% | -5 points |

The largest new movement is Donatello vs Bebop & Rocksteady, 40% to 55%: exactly 15 points. Casey
Jones vs Krang moves 10 points; every other matchup moves at most 5 points. The machine-readable
comparison contains all 45 shifts.

## Decision

**Engine 0.4 passes the defined smoke trust gate.** All tests and repository checks pass, chosen
and rejected decisions are explainable, and no same-protocol matchup movement exceeds 15 points.
Proceed to 100 games per pairing / 4,500-game calibration while keeping all Prototype 0.1 decks
frozen. Calibration remains evidence gathering: Cardcade reports hypotheses and never authorizes or
performs deck revisions.
