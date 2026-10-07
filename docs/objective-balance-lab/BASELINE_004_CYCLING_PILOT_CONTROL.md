# Baseline 004 cycling-pilot runtime control

Evidence `OBL-BASELINE-004-CYCLING-PILOT-REFRESH-001`. The ten official Baseline 004 lists are unchanged. The new semantic runtime is `24ce312cdac00d914606d1f4c111813826ca615768d631532e995faf1c8d57fa`; prior Combined 006 used `f40c4888ef9128d03819fc1be86dde1316b2115fd0d4fb365cd03b288453afa1`.

**Control validated:** 45 cells × 100 games, 50 starts per side, 4,500 games, six matching full-record deterministic replay samples, zero runtime errors. No new candidate, combined validation, or promotion.

Paired games with changed outcomes: **286/4,500**. Ending turn changed: **755/4,500**. Runtime identities differ; the new control replaces the former balance reference for future interpretation rather than being composed with it.

## Global distribution

| Metric | Prior Combined 006 | New unchanged Baseline 004 control | Delta |
|---|---:|---:|---:|
| Mean matchup balance error | 0.220667 | 0.176667 | -0.044 |
| Median matchup deviation | 0.17 | 0.14 | -0.03 |
| >60/40 cells | 33 | 33 | +0 |
| >70/30 cells | 22 | 18 | -4 |
| Deck win-rate spread | 0.654445 | 0.464445 | -0.19 |
| Deck win-rate standard deviation | 0.187555 | 0.14584 | -0.041715 |
| Mean first-player result rate | 0.573111 | 0.575778 | +0.002667 |
| Mean ending turn | 20.088 | 19.8602 | -0.2278 |
| Median ending turn | 18.0 | 18.0 | +0 |

## Deck summaries

| Deck | Prior WR | New WR | Delta | Prior balance error | New balance error |
|---|---:|---:|---:|---:|---:|
| Leonardo | 43.89% | 39.11% | -4.78% | 17.67% | 15.78% |
| Raphael | 71.89% | 69.78% | -2.11% | 22.56% | 20.44% |
| Donatello | 46.00% | 42.11% | -3.89% | 21.11% | 17.22% |
| Michelangelo | 53.33% | 51.44% | -1.89% | 12.44% | 10.56% |
| Splinter | 63.56% | 61.11% | -2.44% | 20.00% | 17.56% |
| Shredder | 71.67% | 69.44% | -2.22% | 21.67% | 19.44% |
| Krang | 38.78% | 47.44% | +8.67% | 22.33% | 15.44% |
| Bebop & Rocksteady | 6.44% | 23.33% | +16.89% | 43.56% | 26.67% |
| April O'Neil | 40.22% | 35.33% | -4.89% | 20.22% | 17.78% |
| Casey Jones | 64.22% | 60.89% | -3.33% | 19.11% | 15.78% |

## All 45 paired matchup cells

First listed deck's result rate; both deck rates and all 4,500 game records are preserved in the machine evidence.

| Matchup | Prior | New | Delta |
|---|---:|---:|---:|
| April O'Neil vs Bebop & Rocksteady | 90% | 64% | -26% |
| April O'Neil vs Casey Jones | 19% | 19% | +0% |
| April O'Neil vs Donatello | 43% | 43% | +0% |
| April O'Neil vs Krang | 57% | 39% | -18% |
| April O'Neil vs Leonardo | 47% | 47% | +0% |
| April O'Neil vs Michelangelo | 40% | 40% | +0% |
| April O'Neil vs Raphael | 19% | 19% | +0% |
| April O'Neil vs Shredder | 24% | 24% | +0% |
| April O'Neil vs Splinter | 23% | 23% | +0% |
| Bebop & Rocksteady vs Casey Jones | 2% | 16% | +14% |
| Bebop & Rocksteady vs Donatello | 14% | 39% | +25% |
| Bebop & Rocksteady vs Krang | 11% | 27% | +16% |
| Bebop & Rocksteady vs Leonardo | 1% | 31% | +30% |
| Bebop & Rocksteady vs Michelangelo | 13% | 25% | +12% |
| Bebop & Rocksteady vs Raphael | 2% | 11% | +9% |
| Bebop & Rocksteady vs Shredder | 2% | 13% | +11% |
| Bebop & Rocksteady vs Splinter | 3% | 12% | +9% |
| Casey Jones vs Donatello | 64% | 64% | +0% |
| Casey Jones vs Krang | 78% | 62% | -16% |
| Casey Jones vs Leonardo | 64% | 64% | +0% |
| Casey Jones vs Michelangelo | 57% | 57% | +0% |
| Casey Jones vs Raphael | 37% | 37% | +0% |
| Casey Jones vs Shredder | 41% | 41% | +0% |
| Casey Jones vs Splinter | 58% | 58% | +0% |
| Donatello vs Krang | 63% | 53% | -10% |
| Donatello vs Leonardo | 71% | 71% | +0% |
| Donatello vs Michelangelo | 39% | 39% | +0% |
| Donatello vs Raphael | 24% | 24% | +0% |
| Donatello vs Shredder | 19% | 19% | +0% |
| Donatello vs Splinter | 19% | 19% | +0% |
| Krang vs Leonardo | 61% | 74% | +13% |
| Krang vs Michelangelo | 40% | 45% | +5% |
| Krang vs Raphael | 19% | 29% | +10% |
| Krang vs Shredder | 16% | 25% | +9% |
| Krang vs Splinter | 22% | 35% | +13% |
| Leonardo vs Michelangelo | 47% | 47% | +0% |
| Leonardo vs Raphael | 20% | 20% | +0% |
| Leonardo vs Shredder | 36% | 36% | +0% |
| Leonardo vs Splinter | 36% | 36% | +0% |
| Michelangelo vs Raphael | 33% | 33% | +0% |
| Michelangelo vs Shredder | 37% | 37% | +0% |
| Michelangelo vs Splinter | 46% | 46% | +0% |
| Raphael vs Shredder | 47% | 47% | +0% |
| Raphael vs Splinter | 54% | 54% | +0% |
| Shredder vs Splinter | 67% | 67% | +0% |

## Cycling execution

### Krang

Cycling in 592 → 98 of 900 games; lands found 843 → 107; shuffles 843 → 107. First creature by turn 4: 103 → 150; games with none: 84 → 56. Creature presence at turns 3/5/7: {'3': 0.7078, '5': 1.3944, '7': 2.2289} → {'3': 0.8322, '5': 1.6567, '7': 2.3933}.

| Cycling creature | Prior casts | New casts | Prior cycling | New cycling |
|---|---:|---:|---:|---:|
| Stockman, Mad Fly-entist | 12 | 434 | 843 | 107 |

### Bebop & Rocksteady

Cycling in 756 → 692 of 900 games; lands found 1640 → 1063; shuffles 1649 → 1063. First creature by turn 4: 204 → 470; games with none: 122 → 98. Creature presence at turns 3/5/7: {'3': 0.1556, '5': 0.7044, '7': 1.3767} → {'3': 0.34, '5': 1.1044, '7': 1.57}.

| Cycling creature | Prior casts | New casts | Prior cycling | New cycling |
|---|---:|---:|---:|---:|
| Bebop, Warthog Warrior | 0 | 173 | 509 | 286 |
| Rocksteady, Crash Courser | 0 | 216 | 1140 | 777 |

## Handoff

This is a full unchanged Baseline 004 runtime-control refresh, not a Round 8 deck test. The prior and new runtime are compared descriptively; no deck weakness, redesign, combined result, or promotion is inferred automatically. 🏢 HQ and 🧪 Design Studio own the environment reassessment and any Round 8 deck-work decision.

[Raw control](BASELINE_004_CYCLING_PILOT_CONTROL.json.gz) · [analysis](BASELINE_004_CYCLING_PILOT_ANALYSIS.json) · [readiness authority](BASELINE_004_CYCLING_PILOT_READINESS.json).
