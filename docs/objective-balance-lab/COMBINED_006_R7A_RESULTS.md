# Combined 006: Frozen R7-A in Baseline 003

Experimental Combined Environment validation. No promotion or baseline change is made here.

- Candidate: `OBL-R7-KRANG-A`, SHA-256 `2d598af2d05212ffb0f19fe5f315b7bf8f85501975155f394448b0a48fa81ab1`.
- Semantic runtime: `f40c4888ef9128d03819fc1be86dde1316b2115fd0d4fb365cd03b288453afa1`.
- Sources: refreshed Baseline 003 `85a8aee4fb5349b1755a31870aa0e0df4f0039fb1babf81445b24fa4db14cd02` and accepted R7-A `8f998c3258ef5c8ff98a77d4b51f15a345bb49e098f5a5b04a9f26dc0af34b7f`.
- Exact schedule: 45 matchups × 100 games, 50 starts per side; 36 unchanged control cells and nine frozen R7-A cells.
- Logical games: **4,500**; source games reused: **4,500**; new executions: **0**; runtime errors: **0**.
- Source deterministic checks: 900/900 R7-A replays and six control cell replay samples matched in isolated evidence.

## Global distribution

| Metric | Runtime-compatible Baseline 003 | Combined 006 | Delta |
|---|---:|---:|---:|
| Mean matchup balance error | 0.228667 | 0.220667 | -0.008 |
| Median matchup deviation | 0.21 | 0.17 | -0.04 |
| >60/40 cells | 34 | 33 | -1 |
| >70/30 cells | 23 | 22 | -1 |
| Deck WR spread | 0.655555 | 0.654445 | -0.00111 |
| Deck WR standard deviation | 0.191623 | 0.187555 | -0.004068 |
| Mean first-player result rate | 0.566889 | 0.573111 | +0.006222 |
| Mean ending turn | 20.1218 | 20.088 | -0.0338 |
| Median ending turn | 18.0 | 18.0 | +0 |

## Ten deck summaries

| Deck | Baseline WR | Combined WR | Delta | Baseline balance error | Combined balance error |
|---|---:|---:|---:|---:|---:|
| Leonardo | 43.67% | 43.89% | +0.22% | 17.89% | 17.67% |
| Raphael | 72.33% | 71.89% | -0.44% | 23.00% | 22.56% |
| Donatello | 46.89% | 46.00% | -0.89% | 22.00% | 21.11% |
| Michelangelo | 54.33% | 53.33% | -1.00% | 13.44% | 12.44% |
| Splinter | 64.00% | 63.56% | -0.44% | 20.44% | 20.00% |
| Shredder | 72.11% | 71.67% | -0.44% | 22.11% | 21.67% |
| Krang | 34.56% | 38.78% | +4.22% | 26.33% | 22.33% |
| Bebop & Rocksteady | 6.78% | 6.44% | -0.33% | 43.22% | 43.56% |
| April O'Neil | 40.44% | 40.22% | -0.22% | 20.44% | 20.22% |
| Casey Jones | 64.89% | 64.22% | -0.67% | 19.78% | 19.11% |

## All 45 matchup cells

The first listed deck's result rate is shown; the other deck has the complementary rate. Full game records and both rates are in the machine evidence.

| Matchup | Baseline | Combined | Delta | Source |
|---|---:|---:|---:|---|
| April O'Neil vs Bebop & Rocksteady | 90% | 90% | +0% | Baseline 003 |
| April O'Neil vs Casey Jones | 19% | 19% | +0% | Baseline 003 |
| April O'Neil vs Donatello | 43% | 43% | +0% | Baseline 003 |
| April O'Neil vs Krang | 59% | 57% | -2% | R7-A |
| April O'Neil vs Leonardo | 47% | 47% | +0% | Baseline 003 |
| April O'Neil vs Michelangelo | 40% | 40% | +0% | Baseline 003 |
| April O'Neil vs Raphael | 19% | 19% | +0% | Baseline 003 |
| April O'Neil vs Shredder | 24% | 24% | +0% | Baseline 003 |
| April O'Neil vs Splinter | 23% | 23% | +0% | Baseline 003 |
| Bebop & Rocksteady vs Casey Jones | 2% | 2% | +0% | Baseline 003 |
| Bebop & Rocksteady vs Donatello | 14% | 14% | +0% | Baseline 003 |
| Bebop & Rocksteady vs Krang | 14% | 11% | -3% | R7-A |
| Bebop & Rocksteady vs Leonardo | 1% | 1% | +0% | Baseline 003 |
| Bebop & Rocksteady vs Michelangelo | 13% | 13% | +0% | Baseline 003 |
| Bebop & Rocksteady vs Raphael | 2% | 2% | +0% | Baseline 003 |
| Bebop & Rocksteady vs Shredder | 2% | 2% | +0% | Baseline 003 |
| Bebop & Rocksteady vs Splinter | 3% | 3% | +0% | Baseline 003 |
| Casey Jones vs Donatello | 64% | 64% | +0% | Baseline 003 |
| Casey Jones vs Krang | 84% | 78% | -6% | R7-A |
| Casey Jones vs Leonardo | 64% | 64% | +0% | Baseline 003 |
| Casey Jones vs Michelangelo | 57% | 57% | +0% | Baseline 003 |
| Casey Jones vs Raphael | 37% | 37% | +0% | Baseline 003 |
| Casey Jones vs Shredder | 41% | 41% | +0% | Baseline 003 |
| Casey Jones vs Splinter | 58% | 58% | +0% | Baseline 003 |
| Donatello vs Krang | 71% | 63% | -8% | R7-A |
| Donatello vs Leonardo | 71% | 71% | +0% | Baseline 003 |
| Donatello vs Michelangelo | 39% | 39% | +0% | Baseline 003 |
| Donatello vs Raphael | 24% | 24% | +0% | Baseline 003 |
| Donatello vs Shredder | 19% | 19% | +0% | Baseline 003 |
| Donatello vs Splinter | 19% | 19% | +0% | Baseline 003 |
| Krang vs Leonardo | 63% | 61% | -2% | R7-A |
| Krang vs Michelangelo | 31% | 40% | +9% | R7-A |
| Krang vs Raphael | 15% | 19% | +4% | R7-A |
| Krang vs Shredder | 12% | 16% | +4% | R7-A |
| Krang vs Splinter | 18% | 22% | +4% | R7-A |
| Leonardo vs Michelangelo | 47% | 47% | +0% | Baseline 003 |
| Leonardo vs Raphael | 20% | 20% | +0% | Baseline 003 |
| Leonardo vs Shredder | 36% | 36% | +0% | Baseline 003 |
| Leonardo vs Splinter | 36% | 36% | +0% | Baseline 003 |
| Michelangelo vs Raphael | 33% | 33% | +0% | Baseline 003 |
| Michelangelo vs Shredder | 37% | 37% | +0% | Baseline 003 |
| Michelangelo vs Splinter | 46% | 46% | +0% | Baseline 003 |
| Raphael vs Shredder | 47% | 47% | +0% | Baseline 003 |
| Raphael vs Splinter | 54% | 54% | +0% | Baseline 003 |
| Shredder vs Splinter | 67% | 67% | +0% | Baseline 003 |

## Handoff

This is a measured experimental environment. 🧪 Design Studio/HQ makes the promotion decision; Cardcade has not promoted the candidate or changed Baseline 003.
