# Cardcade Smoke Run 0.1

Status: **completed — advance engine review, do not revise decks from this sample alone**

- Engine: `cardcade-0.1.0` (heuristic rehearsal, not a Magic rules engine)
- Seed: `20260809`
- Roster: ten Prototype 0.1 decks
- Pairings: 45
- Games: 20 per pairing, 900 total
- Starts: exactly 10/10 per pairing
- First-player win rate: 52.2%

## Aggregate observations

| Deck | Win | Strategy execution | Mulligan | Screw | Flood | Board T3 | Board T8 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Leonardo | 44.4% | 90.6% | 14.4% | 1.1% | 23.3% | 1.80 | 5.07 |
| Raphael | 52.8% | 87.8% | 20.6% | 1.7% | 22.8% | 1.45 | 5.18 |
| Donatello | 50.0% | 39.4% | 23.9% | 0.0% | 30.0% | 1.51 | 4.39 |
| Michelangelo | 53.3% | 86.7% | 22.8% | 1.7% | 25.6% | 1.64 | 4.47 |
| Splinter | 45.0% | 92.8% | 21.7% | 0.6% | 29.4% | 1.70 | 4.84 |
| April O'Neil | 55.0% | 90.0% | 25.6% | 2.2% | 28.3% | 1.63 | 4.62 |
| Casey Jones | 52.2% | 93.3% | 15.6% | 1.7% | 27.8% | 1.21 | 4.87 |
| Shredder | 61.1% | 91.1% | 22.8% | 0.6% | 20.6% | 1.70 | 4.86 |
| Krang | 38.9% | 29.4% | 27.2% | 0.0% | 17.8% | 1.68 | 4.62 |
| Bebop & Rocksteady | 47.2% | 87.8% | 18.3% | 0.6% | 32.8% | 1.45 | 4.57 |

Shredder and Krang fall outside the aggregate target in this smoke sample. Donatello and Krang's
low strategy-execution rates are the most useful diagnostic: the generic pilot likely does not
represent artifact sequencing well enough. Treat this first as a gameplay-model gap, not a deck
change request. Bebop & Rocksteady's flood rate and April/Krang mulligan rates merit observation in
the calibration tier.

Eight pairings crossed 65% in this 20-game sample. Their 95% sampling intervals are extremely wide
(typically about ±20 percentage points), so none is sufficient to authorize a revision. The largest
signals are Leonardo–Shredder (25–75) and the broader Shredder/Krang aggregate separation.

## Design Studio hypotheses, not decisions

1. Add artifact-specific sequencing and payoff telemetry before trusting Donatello or Krang results.
2. Audit the heuristic's interaction valuation; it may structurally favor Shredder.
3. Re-run the same smoke tier under sensitivity variants before the 100-game calibration run.
4. Preserve all Prototype 0.1 lists unchanged until model review or human observations corroborate
   a concrete failure.

The full immutable match records are in `run.json`; `matchup-matrix.json` is the machine-readable
10×10 matrix.
