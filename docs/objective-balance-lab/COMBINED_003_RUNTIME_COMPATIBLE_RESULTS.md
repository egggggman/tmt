# Combined 003 Runtime-Compatible Results

Logical matrix: **4,500 games**; reused: **4,500**; newly executed: **0**.

## Global comparison

| Metric | Refreshed Baseline 001 | Combined 003 | Delta |
|---|---:|---:|---:|
| Mean matchup balance error | 0.192444 | 0.189556 | -0.002888 |
| Median deviation | 0.17 | 0.17 | +0.000000 |
| 60/40 count | 35 | 34 | -1.000000 |
| 70/30 count | 18 | 18 | +0.000000 |
| WR spread | 0.484445 | 0.492222 | +0.007777 |
| WR stddev | 0.161618 | 0.158985 | -0.002633 |
| First-player result rate | 0.504 | 0.505556 | +0.001556 |
| Mean ending turn | 19.5829 | 19.6916 | +0.108700 |
| Median ending turn | 18.0 | 18.0 | +0.000000 |

## Per-deck comparison

| Deck | Baseline WR | Combined WR | WR Δ | Baseline error | Combined error | Error Δ | 60/40 | 70/30 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Leonardo | 36.22% | 36.22% | +0.00% | 14.89% | 14.89% | +0.00% | 6→6 | 2→2 |
| Raphael | 73.44% | 70.22% | -3.22% | 23.44% | 22.00% | -1.44% | 8→7 | 5→5 |
| Donatello | 40.89% | 41.00% | +0.11% | 16.44% | 16.33% | -0.11% | 7→7 | 3→3 |
| Michelangelo | 52.00% | 51.78% | -0.22% | 16.00% | 16.22% | +0.22% | 8→8 | 2→2 |
| Splinter | 62.33% | 63.33% | +1.00% | 20.78% | 19.78% | -1.00% | 8→7 | 4→4 |
| Shredder | 73.89% | 75.00% | +1.11% | 24.33% | 25.00% | +0.67% | 7→7 | 6→6 |
| Krang | 34.56% | 35.11% | +0.56% | 20.11% | 19.56% | -0.56% | 6→6 | 4→4 |
| Bebop & Rocksteady | 40.11% | 40.00% | -0.11% | 14.78% | 14.89% | +0.11% | 6→6 | 3→3 |
| April O'Neil | 25.44% | 25.78% | +0.33% | 24.56% | 24.22% | -0.33% | 7→7 | 5→5 |
| Casey Jones | 61.11% | 61.56% | +0.44% | 17.11% | 16.67% | -0.44% | 7→7 | 2→2 |

## Raphael

R4-C changes Raphael from 73.44% to 70.22% under the same semantic runtime, so the isolated balance improvement **persists** in the composed environment. Identity is **IDENTITY_STRENGTHENED**: Casey density is lower, Skateboard/Pizza utility is usable, and the deck remains aggressive rather than becoming generic Casey equipment control.

Combined validation: **COMBINED_VALIDATION_PASSED**. Promotion eligibility: **PROMOTION_ELIGIBLE** (recommendation only; no promotion occurs here).

## Environment decision

**COMBINED_ENVIRONMENT_IMPROVED**. Mean matchup balance error and 60/40 count improve, 70/30 count is unchanged, while aggregate WR spread increases slightly; this is a modest global improvement with a documented spread tradeoff.
