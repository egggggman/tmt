# Calibration V1 Statistical Analysis

Run: `CALIBRATION_V1_20260923T141649Z_3f838930291e`  
Production evidence: `G:\cardcade\calibration-runs\CALIBRATION_V1_20260923T141649Z_3f838930291e`  
Audited evidence identity: `D202D3B35814E2B67CF2959E73282264CD8AC2B93EA877FB8C8970D1D48616BE`  
Source evidence remains external on G:; this report is analysis only.
Method: one audited evidence record per distinct game; Wilson 95% intervals; duplicate executions are authentication only.

## Overall deck performance

| Deck | Games | Wins | Losses | Draws | Win rate | 95% Wilson CI |
|---|---:|---:|---:|---:|---:|---|
| Shredder | 36864 | 27845 | 9019 | 0 | 75.53% | 75.09%–75.97% |
| Raphael | 36864 | 27470 | 9394 | 0 | 74.52% | 74.07%–74.96% |
| Casey Jones | 36864 | 25137 | 11727 | 0 | 68.19% | 67.71%–68.66% |
| Splinter | 36864 | 21559 | 15305 | 0 | 58.48% | 57.98%–58.98% |
| Michelangelo | 36864 | 19974 | 16890 | 0 | 54.18% | 53.67%–54.69% |
| Leonardo | 36864 | 16383 | 20481 | 0 | 44.44% | 43.94%–44.95% |
| Donatello | 36864 | 13482 | 23382 | 0 | 36.57% | 36.08%–37.07% |
| Bebop & Rocksteady | 36864 | 12650 | 24214 | 0 | 34.32% | 33.83%–34.80% |
| Krang | 36864 | 11002 | 25862 | 0 | 29.84% | 29.38%–30.31% |
| April O’Neil | 36864 | 8818 | 28046 | 0 | 23.92% | 23.49%–24.36% |

## First-player and orientation effects

Overall first-player win rate: **50.64%**.

| Orientation | Games | First-player wins | First-player losses | First-player win rate |
|---|---:|---:|---:|---:|
| canonical | 92160 | 33853 | 58307 | 36.73% |
| reversed | 92160 | 59484 | 32676 | 64.54% |

| Deck | First-player games | First-player wins | First-player losses | First-player win rate |
|---|---:|---:|---:|---:|
| Leonardo | 18432 | 8237 | 10195 | 44.69% |
| Raphael | 18432 | 13976 | 4456 | 75.82% |
| Donatello | 18432 | 6957 | 11475 | 37.74% |
| Michelangelo | 18432 | 10183 | 8249 | 55.25% |
| Splinter | 18432 | 10952 | 7480 | 59.42% |
| Shredder | 18432 | 14096 | 4336 | 76.48% |
| Krang | 18432 | 5527 | 12905 | 29.99% |
| Bebop & Rocksteady | 18432 | 6356 | 12076 | 34.48% |
| April O’Neil | 18432 | 4428 | 14004 | 24.02% |
| Casey Jones | 18432 | 12625 | 5807 | 68.50% |

Canonical/reversed aggregate rates: **DECK-IDENTITY CONFOUNDED — NOT A SEAT-EFFECT ESTIMATE**. Canonical always puts the sorted-earlier deck first and reversed always puts the sorted-later deck first.

| Deck | First games | First win rate | Second games | Second win rate | First minus second |
|---|---:|---:|---:|---:|---:|
| Leonardo | 18432 | 44.69% | 18432 | 44.19% | 0.49% |
| Raphael | 18432 | 75.82% | 18432 | 73.21% | 2.62% |
| Donatello | 18432 | 37.74% | 18432 | 35.40% | 2.34% |
| Michelangelo | 18432 | 55.25% | 18432 | 53.12% | 2.13% |
| Splinter | 18432 | 59.42% | 18432 | 57.55% | 1.87% |
| Shredder | 18432 | 76.48% | 18432 | 74.59% | 1.88% |
| Krang | 18432 | 29.99% | 18432 | 29.70% | 0.28% |
| Bebop & Rocksteady | 18432 | 34.48% | 18432 | 34.15% | 0.34% |
| April O’Neil | 18432 | 24.02% | 18432 | 23.82% | 0.21% |
| Casey Jones | 18432 | 68.50% | 18432 | 67.88% | 0.61% |

### Paired same-seed seat effect

Across 92160 same-seed canonical/reversed pairs, first-player wins in both orientations: 21094; second-player wins in both: 19917; deck winner changes when seats swap: 41011. The paired contrast is 0.012771, yielding a first-player-minus-50% estimate of 0.64% with normal 95% CI 0.42%–0.85%.
This paired contrast uses the same seed with seats swapped and is the seat-effect analysis; raw canonical/reversed rates are not.

### Per-matchup seat effects

For each unordered matchup, A-start means A is seat 0 in canonical order; A-second means A is seat 1 in reversed order.

| Matchup | A start | A second | A start minus second | B start | B second | B start minus second | Aggregate first-player |
|---|---:|---:|---:|---:|---:|---:|---:|
| April O’Neil / Bebop & Rocksteady | 41.94% | 44.43% | -2.49% | 55.57% | 58.06% | -2.49% | 48.75% |
| April O’Neil / Casey Jones | 7.76% | 7.67% | 0.10% | 92.33% | 92.24% | 0.10% | 50.05% |
| April O’Neil / Donatello | 36.33% | 35.84% | 0.49% | 64.16% | 63.67% | 0.49% | 50.24% |
| April O’Neil / Krang | 41.16% | 39.84% | 1.32% | 60.16% | 58.84% | 1.32% | 50.66% |
| April O’Neil / Leonardo | 31.25% | 30.76% | 0.49% | 69.24% | 68.75% | 0.49% | 50.24% |
| April O’Neil / Michelangelo | 21.53% | 20.41% | 1.12% | 79.59% | 78.47% | 1.12% | 50.56% |
| April O’Neil / Raphael | 9.23% | 8.54% | 0.68% | 91.46% | 90.77% | 0.68% | 50.34% |
| April O’Neil / Shredder | 8.06% | 9.72% | -1.66% | 90.28% | 91.94% | -1.66% | 49.17% |
| April O’Neil / Splinter | 18.95% | 17.14% | 1.81% | 82.86% | 81.05% | 1.81% | 50.90% |
| Bebop & Rocksteady / Casey Jones | 16.80% | 18.12% | -1.32% | 81.88% | 83.20% | -1.32% | 49.34% |
| Bebop & Rocksteady / Donatello | 52.05% | 49.46% | 2.59% | 50.54% | 47.95% | 2.59% | 51.29% |
| Bebop & Rocksteady / Krang | 51.37% | 53.27% | -1.90% | 46.73% | 48.63% | -1.90% | 49.05% |
| Bebop & Rocksteady / Leonardo | 41.21% | 40.82% | 0.39% | 59.18% | 58.79% | 0.39% | 50.20% |
| Bebop & Rocksteady / Michelangelo | 35.55% | 31.93% | 3.61% | 68.07% | 64.45% | 3.61% | 51.81% |
| Bebop & Rocksteady / Raphael | 12.50% | 11.77% | 0.73% | 88.23% | 87.50% | 0.73% | 50.37% |
| Bebop & Rocksteady / Shredder | 18.99% | 16.80% | 2.20% | 83.20% | 81.01% | 2.20% | 51.10% |
| Bebop & Rocksteady / Splinter | 26.32% | 27.10% | -0.78% | 72.90% | 73.68% | -0.78% | 49.61% |
| Casey Jones / Donatello | 75.93% | 75.73% | 0.20% | 24.27% | 24.07% | 0.20% | 50.10% |
| Casey Jones / Krang | 87.30% | 87.55% | -0.24% | 12.45% | 12.70% | -0.24% | 49.88% |
| Casey Jones / Leonardo | 67.72% | 68.70% | -0.98% | 31.30% | 32.28% | -0.98% | 49.51% |
| Casey Jones / Michelangelo | 64.99% | 66.89% | -1.90% | 33.11% | 35.01% | -1.90% | 49.05% |
| Casey Jones / Raphael | 43.46% | 38.92% | 4.54% | 61.08% | 56.54% | 4.54% | 52.27% |
| Casey Jones / Shredder | 38.96% | 35.60% | 3.37% | 64.40% | 61.04% | 3.37% | 51.68% |
| Casey Jones / Splinter | 63.87% | 62.11% | 1.76% | 37.89% | 36.13% | 1.76% | 50.88% |
| Donatello / Krang | 59.57% | 59.08% | 0.49% | 40.92% | 40.43% | 0.49% | 50.24% |
| Donatello / Leonardo | 49.27% | 45.56% | 3.71% | 54.44% | 50.73% | 3.71% | 51.86% |
| Donatello / Michelangelo | 33.74% | 30.71% | 3.03% | 69.29% | 66.26% | 3.03% | 51.51% |
| Donatello / Raphael | 20.90% | 15.14% | 5.76% | 84.86% | 79.10% | 5.76% | 52.88% |
| Donatello / Shredder | 13.72% | 11.96% | 1.76% | 88.04% | 86.28% | 1.76% | 50.88% |
| Donatello / Splinter | 23.54% | 20.46% | 3.08% | 79.54% | 76.46% | 3.08% | 51.54% |
| Krang / Leonardo | 42.48% | 42.92% | -0.44% | 57.08% | 57.52% | -0.44% | 49.78% |
| Krang / Michelangelo | 25.73% | 22.07% | 3.66% | 77.93% | 74.27% | 3.66% | 51.83% |
| Krang / Raphael | 11.72% | 10.89% | 0.83% | 89.11% | 88.28% | 0.83% | 50.42% |
| Krang / Shredder | 9.38% | 10.79% | -1.42% | 89.21% | 90.62% | -1.42% | 49.29% |
| Krang / Splinter | 20.31% | 20.07% | 0.24% | 79.93% | 79.69% | 0.24% | 50.12% |
| Leonardo / Michelangelo | 38.72% | 39.75% | -1.03% | 60.25% | 61.28% | -1.03% | 49.49% |
| Leonardo / Raphael | 21.00% | 19.87% | 1.12% | 80.13% | 79.00% | 1.12% | 50.56% |
| Leonardo / Shredder | 30.42% | 28.56% | 1.86% | 71.44% | 69.58% | 1.86% | 50.93% |
| Leonardo / Splinter | 40.82% | 41.50% | -0.68% | 58.50% | 59.18% | -0.68% | 49.66% |
| Michelangelo / Raphael | 31.45% | 30.71% | 0.73% | 69.29% | 68.55% | 0.73% | 50.37% |
| Michelangelo / Shredder | 29.15% | 24.56% | 4.59% | 75.44% | 70.85% | 4.59% | 52.29% |
| Michelangelo / Splinter | 48.39% | 43.07% | 5.32% | 56.93% | 51.61% | 5.32% | 52.66% |
| Raphael / Shredder | 49.56% | 44.92% | 4.64% | 55.08% | 50.44% | 4.64% | 52.32% |
| Raphael / Splinter | 68.70% | 64.21% | 4.49% | 35.79% | 31.30% | 4.49% | 52.25% |
| Shredder / Splinter | 71.19% | 69.58% | 1.61% | 30.42% | 28.81% | 1.61% | 50.81% |

## Matchup matrix

Each cell is the row deck's result against the column deck: games, wins-losses-draws, win rate.

| Deck | Leonardo | Raphael | Donatello | Michelangelo | Splinter | Shredder | Krang | Bebop & Rocksteady | April O’Neil | Casey Jones |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Leonardo | — | 4096: 837-3259-0 (20.43%) | 4096: 2154-1942-0 (52.59%) | 4096: 1607-2489-0 (39.23%) | 4096: 1686-2410-0 (41.16%) | 4096: 1208-2888-0 (29.49%) | 4096: 2347-1749-0 (57.30%) | 4096: 2416-1680-0 (58.98%) | 4096: 2826-1270-0 (68.99%) | 4096: 1302-2794-0 (31.79%) |
| Raphael | 4096: 3259-837-0 (79.57%) | — | 4096: 3358-738-0 (81.98%) | 4096: 2823-1273-0 (68.92%) | 4096: 2722-1374-0 (66.46%) | 4096: 1935-2161-0 (47.24%) | 4096: 3633-463-0 (88.70%) | 4096: 3599-497-0 (87.87%) | 4096: 3732-364-0 (91.11%) | 4096: 2409-1687-0 (58.81%) |
| Donatello | 4096: 1942-2154-0 (47.41%) | 4096: 738-3358-0 (18.02%) | — | 4096: 1320-2776-0 (32.23%) | 4096: 901-3195-0 (22.00%) | 4096: 526-3570-0 (12.84%) | 4096: 2430-1666-0 (59.33%) | 4096: 2017-2079-0 (49.24%) | 4096: 2618-1478-0 (63.92%) | 4096: 990-3106-0 (24.17%) |
| Michelangelo | 4096: 2489-1607-0 (60.77%) | 4096: 1273-2823-0 (31.08%) | 4096: 2776-1320-0 (67.77%) | — | 4096: 1873-2223-0 (45.73%) | 4096: 1100-2996-0 (26.86%) | 4096: 3117-979-0 (76.10%) | 4096: 2714-1382-0 (66.26%) | 4096: 3237-859-0 (79.03%) | 4096: 1395-2701-0 (34.06%) |
| Splinter | 4096: 2410-1686-0 (58.84%) | 4096: 1374-2722-0 (33.54%) | 4096: 3195-901-0 (78.00%) | 4096: 2223-1873-0 (54.27%) | — | 4096: 1213-2883-0 (29.61%) | 4096: 3269-827-0 (79.81%) | 4096: 3002-1094-0 (73.29%) | 4096: 3357-739-0 (81.96%) | 4096: 1516-2580-0 (37.01%) |
| Shredder | 4096: 2888-1208-0 (70.51%) | 4096: 2161-1935-0 (52.76%) | 4096: 3570-526-0 (87.16%) | 4096: 2996-1100-0 (73.14%) | 4096: 2883-1213-0 (70.39%) | — | 4096: 3683-413-0 (89.92%) | 4096: 3363-733-0 (82.10%) | 4096: 3732-364-0 (91.11%) | 4096: 2569-1527-0 (62.72%) |
| Krang | 4096: 1749-2347-0 (42.70%) | 4096: 463-3633-0 (11.30%) | 4096: 1666-2430-0 (40.67%) | 4096: 979-3117-0 (23.90%) | 4096: 827-3269-0 (20.19%) | 4096: 413-3683-0 (10.08%) | — | 4096: 1953-2143-0 (47.68%) | 4096: 2437-1659-0 (59.50%) | 4096: 515-3581-0 (12.57%) |
| Bebop & Rocksteady | 4096: 1680-2416-0 (41.02%) | 4096: 497-3599-0 (12.13%) | 4096: 2079-2017-0 (50.76%) | 4096: 1382-2714-0 (33.74%) | 4096: 1094-3002-0 (26.71%) | 4096: 733-3363-0 (17.90%) | 4096: 2143-1953-0 (52.32%) | — | 4096: 2327-1769-0 (56.81%) | 4096: 715-3381-0 (17.46%) |
| April O’Neil | 4096: 1270-2826-0 (31.01%) | 4096: 364-3732-0 (8.89%) | 4096: 1478-2618-0 (36.08%) | 4096: 859-3237-0 (20.97%) | 4096: 739-3357-0 (18.04%) | 4096: 364-3732-0 (8.89%) | 4096: 1659-2437-0 (40.50%) | 4096: 1769-2327-0 (43.19%) | — | 4096: 316-3780-0 (7.71%) |
| Casey Jones | 4096: 2794-1302-0 (68.21%) | 4096: 1687-2409-0 (41.19%) | 4096: 3106-990-0 (75.83%) | 4096: 2701-1395-0 (65.94%) | 4096: 2580-1516-0 (62.99%) | 4096: 1527-2569-0 (37.28%) | 4096: 3581-515-0 (87.43%) | 4096: 3381-715-0 (82.54%) | 4096: 3780-316-0 (92.29%) | — |

## Environment metrics

Highest win rate: 75.53%; lowest: 23.92%; range: 51.61%; population standard deviation: 17.94%.
Median deck win rate: 49.31%.
Decks inside 45–55%: 1; outside: 9.

## Historical hypotheses

Donatello previously overperforming: **weakened**. Krang previously overperforming: **weakened**. Leonardo previously underperforming: **supported**.
Splinter previously near/sub-50%: **materially_changed**. First-player advantage previously around 52–53%: **weakened**.
Prior engine versions and smaller samples were not pooled with V1.

## Interpretation and limitations

These are descriptive statistics from the completed audited run. Historical hypotheses must be compared only with comparable samples and engine versions. Winner distributions may reflect frozen engine/model behavior; this report does not infer unsupported card/action semantics, recommend deck changes, or authorize Design Studio work.

Prototype 0.3 remains unauthorized pending interpretation/authorization review.
