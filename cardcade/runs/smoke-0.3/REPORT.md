# Cardcade Engine 0.3 Smoke Sensitivity Report

## Protocol

- Frozen Prototype 0.1 roster: 10 decks; no decklist changes
- Seed: `20260809`
- Games: 20 per pairing, 45 unique pairings, 900 total
- Starting players: exactly 10/10 in every pairing
- Engine: `cardcade-0.3.0`; run schema `1.2.0`

## Sensitivity

| Signal | Engine 0.1 | Engine 0.2 | Engine 0.3 |
|---|---:|---:|---:|
| First-player win rate | 52.2% | 52.6% | 52.2% |
| Donatello win rate | 50.0% | 48.9% | 64.4% |
| Krang win rate | 38.9% | 71.1% | 61.7% |
| Krang affinity mana saved/game | n/a | 2.92 | 2.34 |
| Shredder win rate | 61.1% | 52.8% | 47.2% |

Krang's Engine 0.2 affinity distortion contracted by 9.4 win-rate points and 0.58 modeled mana
per game. Engine 0.3 cast 0.59 true affinity spells per Krang game and produced a discount event in
48.3% of games. Only `Krang, Master Mind` receives affinity, and its two blue mana cannot be
discounted. The remaining 61.7% result is no longer explained by the broad Engine 0.2 discount
rule alone. It is a plausible balance hypothesis, but not actionable deck evidence yet.

Donatello established two setup artifacts in 98.3% of games, cast a card-derived payoff in 96.1%,
and completed the modeled plan in 92.8%. Its 64.4% win rate and sharp rise from both earlier engines
show that exact card roles materially change evaluation. This could reflect genuine density, but it
could also reflect limitations in payoff timing, legendary-card redundancy, activated costs, and
rules-text resolution.

Shredder's 47.2% continues the contraction from 61.1% in Engine 0.1 and is not an isolated 0.3
artifact-model beneficiary. The stable 52.2% first-player rate is healthy.

## Major Engine 0.2 to 0.3 shifts

| Matchup (first deck's win rate) | 0.2 | 0.3 | Shift |
|---|---:|---:|---:|
| Donatello vs Shredder | 35% | 75% | +40 points |
| Splinter vs Krang | 10% | 45% | +35 points |
| Donatello vs April O'Neil | 50% | 85% | +35 points |
| Donatello vs Michelangelo | 50% | 75% | +25 points |
| Donatello vs Krang | 30% | 50% | +20 points |

At 20 games per pairing these estimates have wide sampling uncertainty, but the shifts are large
enough to keep the trust gate closed.

## Decision

**Calibration remains blocked.** Engine 0.3 substantially fixes the specific broad-affinity defect,
but the asymmetric jump in card-derived artifact execution and multiple 25–40 point matchup shifts
mean the engine is not yet trustworthy enough for 100 games per matchup / 4,500 games.

The next engine question is card-derived payoff realization: model timing and activation constraints,
legendary redundancy, and the difference between casting a payoff and realizing its value. Treat
Krang and Donatello as engine-validation cases and credible balance hypotheses only. Cardcade does
not authorize or perform deck changes.
