# Objective Balance Lab Combined Environment 004 — results

The 45-cell logical matrix contains **4,500 games**: **4,200 authenticated reused** games and **300 newly executed** games. Provenance is 21 Baseline 002 cells, 21 Round 5 cells, and three new candidate-vs-candidate cells. Runtime errors: **0**. No promotion occurred.

[Selection](COMBINED_004_SELECTION.md) · [Machine evidence](COMBINED_004_EVIDENCE.json) · [New-pair checkpoint](COMBINED_004_NEW_PAIRS.checkpoint.json).

## Environment balance

| Metric | Baseline 002 | Combined 004 | Change |
|---|---:|---:|---:|
| Mean matchup balance error | 18.96% | 17.22% | -1.73 pp |
| Median matchup deviation | 17.00% | 14.00% | -3.00 pp |
| >60/40 cells | 34 | 34 | +0.0000 |
| >70/30 cells | 18 | 17 | -1.0000 |
| Deck WR spread | 49.22% | 42.22% | -7.00 pp |
| Deck WR standard deviation | 15.90% | 13.88% | -2.02 pp |
| First-player result rate | 50.56% | 51.04% | +0.49 pp |
| Mean ending turn | 19.6916 | 19.9364 | +0.2448 |
| Median ending turn | 18.0 | 19.0 | +1.0000 |

Most lopsided matchup: ['april_oneil', 'raphael'] {'april_oneil': 0.09, 'raphael': 0.91} → ['april_oneil', 'casey_jones'] {'april_oneil': 0.14, 'casey_jones': 0.86}.

## All ten decks

| Deck | WR Baseline → combined (Δ) | Mean error Baseline → combined (Δ) | >60/40 | >70/30 | Most lopsided matchup Baseline → combined |
|---|---:|---:|---:|---:|---|
| Leonardo | 36.22% → 38.00% (+1.78 pp) | 14.89% → 14.89% (+0.00 pp) | 6→6 | 2→2 | raphael 20.00% → raphael 20.00% |
| Raphael | 70.22% → 68.78% (-1.44 pp) | 22.00% → 19.44% (-2.56 pp) | 7→7 | 5→5 | april_oneil 91.00% → april_oneil 82.00% |
| Donatello | 41.00% → 40.11% (-0.89 pp) | 16.33% → 15.22% (-1.11 pp) | 7→6 | 3→3 | shredder 16.00% → shredder 17.00% |
| Michelangelo | 51.78% → 50.78% (-1.00 pp) | 16.22% → 15.44% (-0.78 pp) | 8→8 | 2→2 | april_oneil 79.00% → april_oneil 76.00% |
| Splinter | 63.33% → 61.11% (-2.22 pp) | 19.78% → 17.56% (-2.22 pp) | 7→7 | 4→4 | april_oneil 89.00% → april_oneil 78.00% |
| Shredder | 75.00% → 71.00% (-4.00 pp) | 25.00% → 21.00% (-4.00 pp) | 7→7 | 6→5 | april_oneil 91.00% → donatello 83.00% |
| Krang | 35.11% → 43.33% (+8.22 pp) | 19.56% → 17.33% (-2.22 pp) | 6→8 | 4→4 | shredder 11.00% → shredder 18.00% |
| Bebop & Rocksteady | 40.00% → 37.44% (-2.56 pp) | 14.89% → 14.56% (-0.33 pp) | 6→6 | 3→3 | shredder 23.00% → shredder 23.00% |
| April O'Neil | 25.78% → 28.78% (+3.00 pp) | 24.22% → 21.22% (-3.00 pp) | 7→6 | 5→5 | raphael 9.00% → casey_jones 14.00% |
| Casey Jones | 61.56% → 60.67% (-0.89 pp) | 16.67% → 15.56% (-1.11 pp) | 7→7 | 2→1 | april_oneil 82.00% → april_oneil 86.00% |

## Three novel interactions

| Matchup | Exact WR split | On-play WR by deck (50 starts each) | Mean / median ending turn | >60/40 | >70/30 |
|---|---|---|---:|---|---|
| april_oneil|krang | april_oneil 37.00% / krang 63.00% | april_oneil 34.00% / krang 60.00% | 21.99 / 21.0 | True | False |
| april_oneil|shredder | april_oneil 18.00% / shredder 82.00% | april_oneil 16.00% / shredder 80.00% | 19.26 / 18.0 | True | True |
| krang|shredder | krang 18.00% / shredder 82.00% | krang 16.00% / shredder 80.00% | 18.52 / 17.0 | True | True |

## Isolated-to-combined effects

| Candidate | Isolated WR and Δ | Combined WR and Δ | Isolated balance Δ | Combined balance Δ | Classification | Combined verdict | Eligibility |
|---|---:|---:|---:|---:|---|---|---|
| `OBL-R5-SHREDDER-B` | 72.44% (-2.56 pp) | 71.00% (-4.00 pp) | -2.56 pp | -4.00 pp | DELTA_STRENGTHENS | COMBINED_VALIDATION_PASSED | PROMOTION_ELIGIBLE |
| `OBL-R5-APRIL_ONEIL-A` | 29.78% (+4.00 pp) | 28.78% (+3.00 pp) | -4.00 pp | -3.00 pp | DELTA_WEAKENS | COMBINED_VALIDATION_PASSED | PROMOTION_ELIGIBLE |
| `OBL-R5-KRANG-B` | 43.00% (+7.89 pp) | 43.33% (+8.22 pp) | -1.67 pp | -2.22 pp | DELTA_STRENGTHENS | COMBINED_VALIDATION_MIXED | NOT_PROMOTION_ELIGIBLE |

## Decision

- `OBL-R5-SHREDDER-B`: Shredder falls 75.00%→71.00%, improves its nine-matchup balance error 4.00 pp, and reduces >70/30 pairings 6→5 without adding >60/40 cells. The isolated downward effect strengthens in combination. It remains a strong villain deck, but its Foot/minion pressure identity is preserved.
- `OBL-R5-APRIL_ONEIL-A`: April rises 25.78%→28.78% and improves balance error 3.00 pp; >60/40 falls 7→6 and the 9% baseline worst split improves to 14% against Casey. Her isolated gain weakens by 1.00 pp, yet remains meaningful against a tougher combined meta. Reporter/Utrom reinforce adaptive development without crediting unsupported combat-draw.
- `OBL-R5-KRANG-B`: Krang rises 35.11%→43.33% and improves balance error 2.22 pp, so the isolated gain strengthens. But his >60/40 count remains 6→8, exactly the distribution risk flagged at selection; >70/30 is unchanged at 4. The 18% result against Shredder B remains severe. Two artifact-linked Donatello cameos preserve technology identity, but this unresolved extremity prevents a promotion recommendation.

Environment: **COMBINED_ENVIRONMENT_IMPROVED**. Global Balance Δ **-1.73 pp**.

Recommended promotion subset (recommendation only; no promotion here): `OBL-R5-SHREDDER-B`, `OBL-R5-APRIL_ONEIL-A`

Recommend only Shredder B and April A for a separate promotion gate, after recomposing and validating the exact two-candidate matrix with baseline Krang. Replace Combined 004's Krang B cells with seven Baseline 002 Krang-vs-unchanged cells, Shredder B vs baseline Krang and April A vs baseline Krang from Round 5; retain the authenticated Shredder B vs April A new cell. All those cells already exist at the same runtime, so no new simulations appear necessary, but the subset must be validated as its own combined environment before any promotion.

Mean balance error is the mean across 45 cells of |((wins + draws/2)/100) − 50%|. Threshold counts use strict >60/40 and >70/30. A baseline opponent replaced by another candidate is an interaction effect, not a fresh isolated test. No unsupported Reporter combat-draw or unavailable artifact activation telemetry is credited.
