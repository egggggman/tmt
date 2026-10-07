# Combined 007: Frozen R8-A in Baseline 004

Experimental Combined Environment validation. No promotion or baseline change is made here.

- Candidate: `OBL-R8-BEBOP-A`, SHA-256 `aaa61d3a3d65f7c8ab74062cc8f41d220a46066b44c28e3c71921c570a6b66ed`.
- Semantic runtime: `d4466241f0ffeaca809cd6a05210ad53b9af1011a1d7f833de88657c1cf00924`.
- Sources: refreshed Baseline 004 `e5733717bc103ffaffc2582990bf72a8eeb03cded226c57468e4c356654d1d25` and accepted R8-A `31835c9fcdc9b588f333685a6d601ab5bef05aca1657d58e31662d2e9c23ba9a`.
- Accepted isolated record: [PR #275](https://github.com/egggggman/tmt/pull/275), merged as `75133aecde12f0dc979424e324debc465021c788`.
- Exact schedule: 45 matchups × 100 games, 50 starts per side; 36 unchanged control cells and nine frozen R8-A cells.
- Logical games: **4,500**; source games reused: **4,500**; new executions: **0**; runtime errors: **0**.
- Source deterministic checks: 900/900 R8-A replays and six control cell replay samples matched in isolated evidence.

## Global distribution

| Metric | Runtime-compatible Baseline 004 | Combined 007 | Delta |
|---|---:|---:|---:|
| Mean matchup balance error | 0.176667 | 0.156444 | -0.020223 |
| Median matchup deviation | 0.14 | 0.14 | +0 |
| >60/40 cells | 33 | 30 | -3 |
| >70/30 cells | 18 | 16 | -2 |
| Deck WR spread | 0.464445 | 0.355556 | -0.108889 |
| Deck WR standard deviation | 0.14584 | 0.126206 | -0.019634 |
| Mean first-player result rate | 0.575778 | 0.578667 | +0.002889 |
| Mean ending turn | 19.8602 | 19.8304 | -0.0298 |
| Median ending turn | 18.0 | 18.0 | +0 |

## R8-A diagnostics and polarization sentinels

The B&R result rate is shown in each cell. The frozen swap reduces its land count from 24 to 22; these are outcomes for the whole substitution.

| Opponent | Role | Baseline B&R WR | Combined B&R WR | Delta |
|---|---|---:|---:|---:|
| Raphael | primary | 11% | 23% | +12% |
| Shredder | primary | 13% | 19% | +6% |
| Splinter | primary | 12% | 29% | +17% |
| Casey Jones | primary | 16% | 26% | +10% |
| Donatello | sentinel | 39% | 54% | +15% |
| Leonardo | sentinel | 31% | 35% | +4% |
| Krang | sentinel | 27% | 54% | +27% |
| April O'Neil | sentinel | 36% | 55% | +19% |

All four primary cells improve, although B&R remains below 30% in each. Krang, Donatello, and April finish at 54%, 54%, and 55% for B&R, respectively; none crosses 60/40 in the candidate's favor. Krang's 27-point swing is the largest sentinel movement and remains a design review point.

The aggregate standings table below shows the effect on Raphael, Shredder, Splinter, and Casey across all nine opponents. Only their B&R cell changes in this composed environment.

## Ten deck summaries

| Deck | Baseline WR | Combined WR | Delta | Baseline balance error | Combined balance error |
|---|---:|---:|---:|---:|---:|
| Leonardo | 39.11% | 38.67% | -0.44% | 15.78% | 15.33% |
| Raphael | 69.78% | 68.44% | -1.33% | 20.44% | 19.11% |
| Donatello | 42.11% | 40.44% | -1.67% | 17.22% | 16.44% |
| Michelangelo | 51.44% | 50.67% | -0.78% | 10.56% | 9.78% |
| Splinter | 61.11% | 59.22% | -1.89% | 17.56% | 15.67% |
| Shredder | 69.44% | 68.78% | -0.67% | 19.44% | 18.78% |
| Krang | 47.44% | 44.44% | -3.00% | 15.44% | 13.33% |
| Bebop & Rocksteady | 23.33% | 36.33% | +13.00% | 26.67% | 16.56% |
| April O'Neil | 35.33% | 33.22% | -2.11% | 17.78% | 16.78% |
| Casey Jones | 60.89% | 59.78% | -1.11% | 15.78% | 14.67% |

## All 45 matchup cells

The first listed deck's result rate is shown; the other deck has the complementary rate. Full game records and both rates are in the machine evidence.

| Matchup | Baseline | Combined | Delta | Source |
|---|---:|---:|---:|---|
| April O'Neil vs Bebop & Rocksteady | 64% | 45% | -19% | R8-A |
| April O'Neil vs Casey Jones | 19% | 19% | +0% | Baseline 004 |
| April O'Neil vs Donatello | 43% | 43% | +0% | Baseline 004 |
| April O'Neil vs Krang | 39% | 39% | +0% | Baseline 004 |
| April O'Neil vs Leonardo | 47% | 47% | +0% | Baseline 004 |
| April O'Neil vs Michelangelo | 40% | 40% | +0% | Baseline 004 |
| April O'Neil vs Raphael | 19% | 19% | +0% | Baseline 004 |
| April O'Neil vs Shredder | 24% | 24% | +0% | Baseline 004 |
| April O'Neil vs Splinter | 23% | 23% | +0% | Baseline 004 |
| Bebop & Rocksteady vs Casey Jones | 16% | 26% | +10% | R8-A |
| Bebop & Rocksteady vs Donatello | 39% | 54% | +15% | R8-A |
| Bebop & Rocksteady vs Krang | 27% | 54% | +27% | R8-A |
| Bebop & Rocksteady vs Leonardo | 31% | 35% | +4% | R8-A |
| Bebop & Rocksteady vs Michelangelo | 25% | 32% | +7% | R8-A |
| Bebop & Rocksteady vs Raphael | 11% | 23% | +12% | R8-A |
| Bebop & Rocksteady vs Shredder | 13% | 19% | +6% | R8-A |
| Bebop & Rocksteady vs Splinter | 12% | 29% | +17% | R8-A |
| Casey Jones vs Donatello | 64% | 64% | +0% | Baseline 004 |
| Casey Jones vs Krang | 62% | 62% | +0% | Baseline 004 |
| Casey Jones vs Leonardo | 64% | 64% | +0% | Baseline 004 |
| Casey Jones vs Michelangelo | 57% | 57% | +0% | Baseline 004 |
| Casey Jones vs Raphael | 37% | 37% | +0% | Baseline 004 |
| Casey Jones vs Shredder | 41% | 41% | +0% | Baseline 004 |
| Casey Jones vs Splinter | 58% | 58% | +0% | Baseline 004 |
| Donatello vs Krang | 53% | 53% | +0% | Baseline 004 |
| Donatello vs Leonardo | 71% | 71% | +0% | Baseline 004 |
| Donatello vs Michelangelo | 39% | 39% | +0% | Baseline 004 |
| Donatello vs Raphael | 24% | 24% | +0% | Baseline 004 |
| Donatello vs Shredder | 19% | 19% | +0% | Baseline 004 |
| Donatello vs Splinter | 19% | 19% | +0% | Baseline 004 |
| Krang vs Leonardo | 74% | 74% | +0% | Baseline 004 |
| Krang vs Michelangelo | 45% | 45% | +0% | Baseline 004 |
| Krang vs Raphael | 29% | 29% | +0% | Baseline 004 |
| Krang vs Shredder | 25% | 25% | +0% | Baseline 004 |
| Krang vs Splinter | 35% | 35% | +0% | Baseline 004 |
| Leonardo vs Michelangelo | 47% | 47% | +0% | Baseline 004 |
| Leonardo vs Raphael | 20% | 20% | +0% | Baseline 004 |
| Leonardo vs Shredder | 36% | 36% | +0% | Baseline 004 |
| Leonardo vs Splinter | 36% | 36% | +0% | Baseline 004 |
| Michelangelo vs Raphael | 33% | 33% | +0% | Baseline 004 |
| Michelangelo vs Shredder | 37% | 37% | +0% | Baseline 004 |
| Michelangelo vs Splinter | 46% | 46% | +0% | Baseline 004 |
| Raphael vs Shredder | 47% | 47% | +0% | Baseline 004 |
| Raphael vs Splinter | 54% | 54% | +0% | Baseline 004 |
| Shredder vs Splinter | 67% | 67% | +0% | Baseline 004 |

## Handoff

This is a measured experimental environment. 🧪 Design Studio/HQ makes the promotion decision; Cardcade has not promoted the candidate or changed Baseline 004.
