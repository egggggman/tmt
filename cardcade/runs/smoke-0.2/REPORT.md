# Cardcade Engine 0.2 Smoke Sensitivity Report

Status: **completed — calibration blocked; no deck revisions authorized**

- Engine: `cardcade-0.2.0` (heuristic rehearsal, not a Magic rules engine)
- Baseline: `cardcade-0.1.0`
- Seed: `20260809`
- Roster: the same ten frozen Prototype 0.1 decklists
- Pairings: 45
- Games: 20 per pairing, 900 total
- Starts: exactly 10/10 per pairing
- First-player win rate: 52.6% (Engine 0.1: 52.2%, shift +0.3 percentage points)

## Aggregate sensitivity

| Deck | Engine 0.1 | Engine 0.2 | Shift | Engine 0.2 strategy execution |
| --- | ---: | ---: | ---: | ---: |
| Leonardo | 44.4% | 40.6% | -3.9 pp | 92.2% |
| Raphael | 52.8% | 50.6% | -2.2 pp | 88.9% |
| Donatello | 50.0% | 48.9% | -1.1 pp | 41.7% |
| Michelangelo | 53.3% | 44.4% | -8.9 pp | 87.8% |
| Splinter | 45.0% | 43.9% | -1.1 pp | 94.4% |
| April O'Neil | 55.0% | 48.9% | -6.1 pp | 91.7% |
| Casey Jones | 52.2% | 51.1% | -1.1 pp | 93.9% |
| Shredder | 61.1% | 52.8% | -8.3 pp | 86.1% |
| Krang | 38.9% | 71.1% | +32.2 pp | 71.1% |
| Bebop & Rocksteady | 47.2% | 47.8% | +0.6 pp | 90.6% |

At 20 games per matchup, individual matchup estimates remain noisy. The largest shifts are
Splinter–Shredder (+45 points toward Splinter), Leonardo–Krang (-40), Raphael–Krang (-40), and
Michelangelo–Krang (-40). The full ordered list and exact values are in
`sensitivity-comparison.json`.

## Artifact behavior

Donatello established at least two artifact setup pieces in 77.2% of games, cast a modeled payoff in
46.1%, held a spell for sequencing 0.73 times per game, and executed the full artifact plan in
41.7%. That is only a small change from Engine 0.1's generic 39.4% execution result, but Engine 0.2
now explains the misses: setup occurs substantially more often than payoff conversion.

Krang established setup in 93.3% of games, cast a payoff in 72.2%, saved a modeled 2.92 mana per
game through affinity, and executed the plan in 71.1%. Its win rate rose to 71.1%. Because that jump
is tightly coupled to newly introduced affinity valuation, this is evidence that the current
affinity abstraction is too influential or insufficiently grounded—not evidence that the frozen
Krang deck is overpowered.

## Interaction behavior

Interaction now scores only when the opposing board offers a target. Shredder saw 1.60 modeled
interaction cards per game, used 1.56, left 0.04 dead, and moved from 61.1% to 52.8%. This supports
the Engine 0.1 interaction-bias hypothesis. It does not prove Shredder is balanced: target quality,
timing, sacrifice costs, and removal exchanges are still abstracted.

## Gate decision and hypotheses

The stable first-player rate and normalized Shredder result increase trust in those parts of the
model. The Krang swing above 70%, several 40-point matchup shifts, and profile-level artifact-density
assumptions prevent trusting Engine 0.2 for 100-game-per-matchup calibration.

Next engine work should derive artifact roles and costs from actual card data, distinguish setup
artifacts from artifact creatures and payoffs, and test affinity discount/value caps with fixed
per-game streams. Then rerun this exact smoke protocol. No Prototype 0.1 decklist should change from
this evidence.
