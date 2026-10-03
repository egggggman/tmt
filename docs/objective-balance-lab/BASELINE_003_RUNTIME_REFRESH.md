# Baseline 003 New-Runtime Control Refresh

Evidence identity: `OBL-BASELINE-003-RUNTIME-REFRESH-001`. This is a runtime evidence revision of the same ten-deck `OBL-BASELINE-003`, not a new baseline or promotion.

The historical [Baseline 003 manifest](baselines/OBL_BASELINE_003_MANIFEST.json) and [Combined 005 evidence](COMBINED_005_EVIDENCE.json) remain unchanged. Old runtime: `78bcce5b5f635f11c67247df91f90fef2bf0dbf948973c5c1ac38419f28b0e25`. Refreshed runtime: `252f00317d8efbf552512768503d5f453ef9594ade48e27a94f95f05c7625982`. Their game evidence is not semantically composable.

[Machine evidence](BASELINE_003_RUNTIME_REFRESH_EVIDENCE.json) and [checkpoint](BASELINE_003_RUNTIME_REFRESH_CHECKPOINT.json) contain 45 complete cells, 4,500 new control games, 50 starts each way per cell, zero runtime errors, six matched deterministic replays, and frozen schedule `b5fd8ab57016b15662fca420d508c9aab3633ad14b7f7515d667492b0f8abf27`. No R6-B candidate was played.

## Global metrics

| Metric | Historical | Refreshed | Delta |
|---|---:|---:|---:|
| Mean matchup balance error | 0.176667 | 0.176667 | +0.0 |
| Median deviation | 0.15 | 0.15 | +0.0 |
| >60/40 cells | 32 | 32 | +0 |
| >70/30 cells | 17 | 17 | +0 |
| WR spread | 0.417778 | 0.417778 | +0.0 |
| WR standard deviation | 0.145737 | 0.145737 | +0.0 |
| First-player result rate | 0.509556 | 0.509556 | +0.0 |
| Mean ending turn | 19.9027 | 19.9027 | +0.0 |
| Median ending turn | 19.0 | 19.0 | +0.0 |
| Worst matchup | Krang 12.00% vs Shredder | Krang 12.00% vs Shredder | same pair |

## Deck outcomes

| Deck | Historical WR | Refreshed WR | WR delta | Historical balance error | Refreshed balance error | Error delta |
|---|---:|---:|---:|---:|---:|---:|
| Leonardo | 38.67% | 38.67% | 0.00% | 14.22% | 14.22% | 0.00% |
| Raphael | 69.78% | 69.78% | 0.00% | 20.44% | 20.44% | 0.00% |
| Donatello | 40.56% | 40.56% | 0.00% | 15.67% | 15.67% | 0.00% |
| Michelangelo | 51.33% | 51.33% | 0.00% | 16.00% | 16.00% | 0.00% |
| Splinter | 62.11% | 62.11% | 0.00% | 18.56% | 18.56% | 0.00% |
| Shredder | 71.67% | 71.67% | 0.00% | 21.67% | 21.67% | 0.00% |
| Krang | 35.33% | 35.33% | 0.00% | 19.56% | 19.56% | 0.00% |
| Bebop & Rocksteady | 38.56% | 38.56% | 0.00% | 13.44% | 13.44% | 0.00% |
| April O'Neil | 29.89% | 29.89% | 0.00% | 20.11% | 20.11% | 0.00% |
| Casey Jones | 62.11% | 62.11% | 0.00% | 17.00% | 17.00% | 0.00% |

## Matchup-result audit

Changed cells: 0; unchanged cells: 45; maximum cell WR movement: 0.00%. Paired game outcomes changed in 0 seeds; ending turns changed in 0. The zero delta is observed game-result equivalence, not permission to compose evidence across different semantic runtimes.

| Matchup | Historical WR (first deck) | Refreshed WR | Delta | Paired outcomes changed |
|---|---:|---:|---:|---:|
| None | — | — | — | 0 |

## Krang control handoff

Krang: aggregate WR 35.33%; mean matchup balance error 19.56%; >60/40 6; >70/30 4; first-player result rate 37.56%; mean/median ending turn 20.1822/19.0.

| Opponent | Refreshed Krang WR |
|---|---:|
| April O'Neil | 53.00% |
| Bebop & Rocksteady | 51.00% |
| Casey Jones | 23.00% |
| Donatello | 46.00% |
| Leonardo | 68.00% |
| Michelangelo | 32.00% |
| Raphael | 13.00% |
| Shredder | 12.00% |
| Splinter | 20.00% |

Supported early-board/interaction telemetry: {'land_miss': None, 'creature': 9.3276, 'blocker': 3.7625, 'interaction': 5.8251}; battlefield presence t3/t5/t7: {'3': 0, '5': 0, '7': 0}; interaction casts: 4.5744. Unavailable metrics are not imputed as zero.

**R6_B_CONTROL_READY.** All nine new-runtime Krang cells are complete. This evidence may serve as the parent/control for a later R6-B isolated experiment; it does not itself authorize R6-B games or promotion.
