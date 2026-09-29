# OBL-COMBINED-001 Results

This is a combined validation experiment, not a promotion. The provisional environment uses the frozen Round 1 schedule for 4,500 games and compares directly with the banked `OBL-BASELINE-000` 4,500-game baseline.

## Decision

**COMBINED_ENVIRONMENT_IMPROVED**

Global Mean Matchup Balance Error improved from 20.96% to 19.33% (-1.62 pp). This is not an automatic promotion: Krang and April remain mixed at the deck gate, and explicit promotion is separate.

## Global metrics

| Metric | OBL-BASELINE-000 | OBL-COMBINED-001 | Δ |
|---|---:|---:|---:|
| Mean Matchup Balance Error | 20.96% | 19.33% | -1.62 pp |
| Median matchup deviation | 19.00% | 17.00% | -2.00 pp |
| Aggregate deck WR spread | 51.11% | 48.56% | -2.56 pp |
| Aggregate deck WR standard deviation | 17.36% | 15.75% | -1.62 pp |
| Mean first-player result rate | 50.38% | 50.40% | +0.02 pp |
| Mean ending turn | 19.44 | 19.50 | +0.05 |
| Median ending turn | 18.00 | 18.00 | +0.00 |
| >60/40 matchups | 36 | 36 | +0 |
| >70/30 matchups | 21 | 19 | -2 |
| Worst matchup | Raphael over April O'Neil (97.00%) | Raphael over Krang (92.00%) | changed |

## Per-deck comparison

| Deck | Selected build | WR baseline→combined | Balance error baseline→combined | >60/40 baseline→combined | >70/30 baseline→combined | Worst matchup baseline→combined | Verdict | Promotion |
|---|---|---:|---:|---:|---:|---|---|---|
| Leonardo | `OBL-R1-LEONARDO-A` | 35.44%→36.44% | 16.78%→15.78% (-1.00 pp) | 7→6 | 3→3 | Raphael→Raphael | COMBINED_VALIDATION_PASSED | PROMOTION_ELIGIBLE |
| Raphael | `BASELINE` | 76.78%→75.11% | 26.78%→25.11% (-1.67 pp) | 8→8 | 5→5 | April O'Neil→Krang | BASELINE_RETAINED | NOT_PROMOTION_ELIGIBLE |
| Donatello | `OBL-R2-DONATELLO-A` | 41.00%→40.11% | 18.11%→15.89% (-2.22 pp) | 7→7 | 5→3 | Raphael→Shredder | COMBINED_VALIDATION_PASSED | PROMOTION_ELIGIBLE |
| Michelangelo | `BASELINE` | 54.11%→51.22% | 18.33%→16.11% (-2.22 pp) | 9→8 | 3→2 | April O'Neil→April O'Neil | BASELINE_RETAINED | NOT_PROMOTION_ELIGIBLE |
| Splinter | `BASELINE` | 62.78%→60.78% | 21.67%→19.67% (-2.00 pp) | 8→8 | 4→4 | April O'Neil→April O'Neil | BASELINE_RETAINED | NOT_PROMOTION_ELIGIBLE |
| Shredder | `BASELINE` | 73.00%→72.44% | 24.56%→24.00% (-0.56 pp) | 7→7 | 6→6 | April O'Neil→Krang | BASELINE_RETAINED | NOT_PROMOTION_ELIGIBLE |
| Krang | `OBL-R2-KRANG-B` | 35.11%→38.33% | 20.89%→21.00% (+0.11 pp) | 6→7 | 4→5 | Raphael→Raphael | COMBINED_VALIDATION_MIXED | NOT_PROMOTION_ELIGIBLE |
| Bebop & Rocksteady | `OBL-R2-BEBOP_ROCKSTEADY-B` | 32.67%→38.11% | 19.78%→15.00% (-4.78 pp) | 6→6 | 4→3 | Raphael→Raphael | COMBINED_VALIDATION_PASSED | PROMOTION_ELIGIBLE |
| April O'Neil | `OBL-R1-APRIL_ONEIL-A` | 25.67%→26.56% | 24.33%→23.44% (-0.89 pp) | 7→8 | 5→5 | Raphael→Raphael | COMBINED_VALIDATION_MIXED | NOT_PROMOTION_ELIGIBLE |
| Casey Jones | `OBL-R2-CASEY_JONES-B` | 63.44%→60.89% | 18.33%→17.33% (-1.00 pp) | 7→7 | 3→2 | April O'Neil→April O'Neil | COMBINED_VALIDATION_PASSED | PROMOTION_ELIGIBLE |

## Interaction effects

| Selected candidate | Isolated Balance Δ | Combined Balance Δ | Classification |
|---|---:|---:|---|
| `OBL-R1-LEONARDO-A` | -0.56 pp | -1.00 pp | DELTA_STRENGTHENS |
| `OBL-R2-DONATELLO-A` | -0.78 pp | -2.22 pp | DELTA_STRENGTHENS |
| `OBL-R2-KRANG-B` | -0.11 pp | +0.11 pp | DELTA_REVERSES |
| `OBL-R2-BEBOP_ROCKSTEADY-B` | -3.44 pp | -4.78 pp | DELTA_STRENGTHENS |
| `OBL-R1-APRIL_ONEIL-A` | -2.44 pp | -0.89 pp | DELTA_WEAKENS |
| `OBL-R2-CASEY_JONES-B` | -1.22 pp | -1.00 pp | DELTA_WEAKENS |

## Findings

- Raphael and Shredder remained unchanged; the selected weaker-deck improvements reduced Raphael's aggregate WR from 76.78% to 75.11% and Shredder's from 73.00% to 72.44%.
- April and Bebop & Rocksteady both improved materially in the combined environment, though April's isolated balance gain weakened.
- Donatello R2A strengthened in the combined environment: its balance-error delta improved from -0.78 pp isolated to -2.22 pp combined.
- Krang R2B reversed from a slight isolated improvement (-0.11 pp) to a slight combined regression (+0.11 pp), and remains mixed.
- Casey R2B retained a favorable balance direction (-1.00 pp combined) and reduced >70/30 matchups 3→2.
- Authoritative telemetry includes W/L/D, first-player result, ending turn, first-play proxies, battlefield presence, interaction casts, signature casts, runtime fingerprints, and matchup rates. Hand size, unused mana, flood/screw, stranded cards, engine activation, stabilization, lethal pressure, and loss causes remain unavailable and are not fabricated.

No deck file was overwritten. No candidate was promoted. The next governance action remains explicit promotion review after any future authorization, not automatic baseline replacement.
