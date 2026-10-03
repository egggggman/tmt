# Objective Balance Lab Combined Environment 005 — results

The full 45-cell matrix is **4,500 logical games, 4,500 authenticated reused games, and zero newly executed games**: 28 Baseline 002, 16 Round 5, and one Combined 004 cell. Runtime errors: **0**. No deck or Cardcade semantics changed; no promotion occurred.

[Selection](COMBINED_005_SELECTION.md) · [machine evidence](COMBINED_005_EVIDENCE.json).

## Global comparison

| Metric | Baseline 002 | Combined 004 | Combined 005 | 004→005 |
|---|---:|---:|---:|---:|
| Mean matchup balance error | 18.96% | 17.22% | 17.67% | +0.44 pp |
| Median matchup deviation | 17.00% | 14.00% | 15.00% | +1.00 pp |
| >60/40 cells | 34 | 34 | 32 | -2 |
| >70/30 cells | 18 | 17 | 17 | +0 |
| Deck WR spread | 49.22% | 42.22% | 41.78% | -0.44 pp |
| Deck WR standard deviation | 15.90% | 13.88% | 14.57% | +0.70 pp |
| First-player result rate | 50.56% | 51.04% | 50.96% | -0.09 pp |
| Mean ending turn | 19.6916 | 19.9364 | 19.9027 | -0.0337 |
| Median ending turn | 18.0 | 19.0 | 19.0 | +0.0000 |

Worst matchup: Baseline 002 April O'Neil 9.00% / Raphael 91.00%; Combined 004 April O'Neil 14.00% / Casey Jones 86.00%; Combined 005 Krang 12.00% / Shredder 88.00%.

## All ten decks versus Baseline 002

| Deck | WR Baseline → 005 (Δ) | Mean error Baseline → 005 (Δ) | >60/40 | >70/30 | Most lopsided matchup Baseline → 005 |
|---|---:|---:|---:|---:|---|
| Leonardo | 36.22% → 38.67% (+2.44 pp) | 14.89% → 14.22% (-0.67 pp) | 6→6 | 2→1 | raphael 20.00% → raphael 20.00% |
| Raphael | 70.22% → 69.78% (-0.44 pp) | 22.00% → 20.44% (-1.56 pp) | 7→7 | 5→5 | april_oneil 91.00% → krang 87.00% |
| Donatello | 41.00% → 40.56% (-0.44 pp) | 16.33% → 15.67% (-0.67 pp) | 7→6 | 3→3 | shredder 16.00% → shredder 17.00% |
| Michelangelo | 51.78% → 51.33% (-0.44 pp) | 16.22% → 16.00% (-0.22 pp) | 8→8 | 2→2 | april_oneil 79.00% → april_oneil 76.00% |
| Splinter | 63.33% → 62.11% (-1.22 pp) | 19.78% → 18.56% (-1.22 pp) | 7→7 | 4→4 | april_oneil 89.00% → krang 80.00% |
| Shredder | 75.00% → 71.67% (-3.33 pp) | 25.00% → 21.67% (-3.33 pp) | 7→7 | 6→5 | april_oneil 91.00% → krang 88.00% |
| Krang | 35.11% → 35.33% (+0.22 pp) | 19.56% → 19.56% (+0.00 pp) | 6→6 | 4→4 | shredder 11.00% → shredder 12.00% |
| Bebop & Rocksteady | 40.00% → 38.56% (-1.44 pp) | 14.89% → 13.44% (-1.44 pp) | 6→5 | 3→3 | shredder 23.00% → shredder 23.00% |
| April O'Neil | 25.78% → 29.89% (+4.11 pp) | 24.22% → 20.11% (-4.11 pp) | 7→5 | 5→5 | raphael 9.00% → casey_jones 14.00% |
| Casey Jones | 61.56% → 62.11% (+0.56 pp) | 16.67% → 17.00% (+0.33 pp) | 7→7 | 2→2 | april_oneil 82.00% → april_oneil 86.00% |

## Removing Krang B: the nine changed matchup cells

| Matchup | Combined 004 | Combined 005 | Deviation Δ | Balance direction |
|---|---|---|---:|---|
| april_oneil / krang | april_oneil 37.00% / krang 63.00% | april_oneil 47.00% / krang 53.00% | -10.00 pp | IMPROVED |
| bebop_rocksteady / krang | bebop_rocksteady 39.00% / krang 61.00% | bebop_rocksteady 49.00% / krang 51.00% | -10.00 pp | IMPROVED |
| casey_jones / krang | casey_jones 64.00% / krang 36.00% | casey_jones 77.00% / krang 23.00% | +13.00 pp | WORSENED |
| donatello / krang | donatello 50.00% / krang 50.00% | donatello 54.00% / krang 46.00% | +4.00 pp | WORSENED |
| krang / leonardo | krang 74.00% / leonardo 26.00% | krang 68.00% / leonardo 32.00% | -6.00 pp | IMPROVED |
| krang / michelangelo | krang 37.00% / michelangelo 63.00% | krang 32.00% / michelangelo 68.00% | +5.00 pp | WORSENED |
| krang / raphael | krang 22.00% / raphael 78.00% | krang 13.00% / raphael 87.00% | +9.00 pp | WORSENED |
| krang / shredder | krang 18.00% / shredder 82.00% | krang 12.00% / shredder 88.00% | +6.00 pp | WORSENED |
| krang / splinter | krang 29.00% / splinter 71.00% | krang 20.00% / splinter 80.00% | +9.00 pp | WORSENED |

Restoring baseline Krang changes exactly nine cells: 3 less lopsided, 6 more lopsided, and 0 unchanged in absolute 50% deviation. The other 36 cell results remain byte-identical to Combined 004.

## Candidate interactions and decisions

| Candidate | Isolated WR / Δ | Combined 004 WR / Δ | Combined 005 WR / Δ | Classification | Combined 005 verdict | Eligibility |
|---|---:|---:|---:|---|---|---|
| `OBL-R5-SHREDDER-B` | 72.44% (-2.56 pp) | 71.00% (-4.00 pp) | 71.67% (-3.33 pp) | DELTA_STRENGTHENS | COMBINED_VALIDATION_PASSED | PROMOTION_ELIGIBLE |
| `OBL-R5-APRIL_ONEIL-A` | 29.78% (+4.00 pp) | 28.78% (+3.00 pp) | 29.89% (+4.11 pp) | DELTA_STRENGTHENS | COMBINED_VALIDATION_PASSED | PROMOTION_ELIGIBLE |

## Verdict and promotion gate

- `OBL-R5-SHREDDER-B`: Shredder is 71.67% versus 75.00% in Baseline 002; its balance error improves 3.33 pp and >70/30 falls 6→5 without more >60/40 cells. The effect is 0.67 pp weaker than in Combined 004 but still stronger than its 2.56 pp isolated reduction. Villain-minion pressure remains intact. The 88/12 Krang pairing is an important residual extreme, not hidden.
- `OBL-R5-APRIL_ONEIL-A`: April rises 25.78%→29.89% and improves balance error 4.11 pp; >60/40 falls 7→5 while >70/30 stays at 5. Its gain is stronger than both the 4.00 pp isolated result and the 3.00 pp Combined 004 result, so it does not depend on Krang B. Reporter/Utrom preserve adaptive identity; no unsupported combat-draw is credited.

Environment decision: **COMBINED_ENVIRONMENT_IMPROVED**. Recommended subset for a separate, explicit promotion decision: `OBL-R5-SHREDDER-B`, `OBL-R5-APRIL_ONEIL-A`. No promotion or Baseline 003 creation occurs here.

Both candidates pass together in the exact Combined 005 subset and are recommended for a separate explicit promotion to OBL-BASELINE-003. Against Baseline 002, the environment improves mean balance error by 1.29 pp, cuts >60/40 cells 34→32 and >70/30 cells 18→17, and narrows WR spread. Compared with Combined 004, removing Krang B reduces >60/40 cells 34→32 but raises mean balance error 17.22%→17.67% and worsens the worst split 14/86→12/88. Krang remains an unresolved underperformer; this tradeoff and the still-high Shredder strength must be recorded in the promotion decision. No promotion is performed in this experiment.

Mean balance error is the mean over 45 cells of |((wins + draws/2)/100) − 50%|; threshold counts are strict. Reporter combat-draw and other unavailable effect-use telemetry are not credited.
