# Krang Round 6-B — isolated Chrome Dome validation

Immutable Design Studio candidate `OBL-R6-KRANG-B`: -1 Negate, +1 Chrome Dome; canonical LF SHA-256 `5460b9d1288d193db3f8db7a78076dfeb38f734c79acdd1ddbe898da030b3bdf`, Git blob `53af73af05c475832bd3e8a08c67264a0ff8fd44`. Its 60-card list was not changed.

The paired control is [Baseline 003 Runtime Refresh 001](BASELINE_003_RUNTIME_REFRESH_EVIDENCE.json) under semantic runtime `252f00317d8efbf552512768503d5f453ef9594ade48e27a94f95f05c7625982` and frozen schedule `b5fd8ab57016b15662fca420d508c9aab3633ad14b7f7515d667492b0f8abf27`. Historical R6-A used another runtime and is context only. [Machine evidence](ROUND_6_B_EVIDENCE.json) and [checkpoint](ROUND_6_B_CHECKPOINT.json) retain nine 100-game cells and all 900 matching deterministic replays. No parent games were rerun.

Mean Matchup Balance Error = mean of absolute matchup WR distance from 50%. The >60/40 and >70/30 counts use strict thresholds. Negative Balance Δ is improvement.

| Metric | Refreshed control | R6-B | Delta |
|---|---:|---:|---:|
| Aggregate WR | 35.33% | 38.67% | +3.33 pp |
| Mean balance error | 19.56% | 19.78% | +0.22 pp |
| >60/40 | 6 | 7 | +1 |
| >70/30 | 4 | 3 | -1 |
| Worst matchup | shredder 12.00% | raphael 13.00% | — |
| Krang-first result | 37.56% | 40.89% | — |
| Mean / median ending turn | 20.1822 / 19.0 | 20.1156 / 19.0 | — |

| Opponent | Control WR | R6-B WR | Delta |
|---|---:|---:|---:|
| Leonardo | 68.00% | 70.00% | +2.00 pp |
| Raphael | 13.00% | 13.00% | +0.00 pp |
| Donatello | 46.00% | 46.00% | +0.00 pp |
| Michelangelo | 32.00% | 32.00% | +0.00 pp |
| Splinter | 20.00% | 23.00% | +3.00 pp |
| Shredder | 12.00% | 15.00% | +3.00 pp |
| Bebop & Rocksteady | 51.00% | 56.00% | +5.00 pp |
| April O'Neil | 53.00% | 62.00% | +9.00 pp |
| Casey Jones | 23.00% | 31.00% | +8.00 pp |

## Development and mechanism

First creature (conditional mean when observed): 9.3276 → 9.3317; first meaningful blocker proxy: 3.7625 → 3.6946; first interaction proxy: 5.8251 → 5.7571. Unobserved is not zero.

| Turn | Control observed games / mean creatures | R6-B observed games / mean creatures | Delta in conditional mean |
|---|---:|---:|---:|
| 3 | 608 / 1.1595 | 608 / 1.1957 | +0.0362 |
| 5 | 756 / 1.9259 | 756 / 1.959 | +0.0331 |
| 7 | 810 / 2.6568 | 825 / 2.7018 | +0.0450 |

Interaction casts: 1327 → 1325; Chrome Dome casts: **271** in 269 games; battlefield entries/exits recorded: 271/114.

The generic `pt_static_team_modifier_changed` stream records 829 changes: 512 applications, 317 removals, 0 updates. It applied +1/+0 to qualifying targets 512 times (maximum simultaneous qualifying targets observed: 5). Affected artifact-creature names and counts: {'Buzz Bots': 162, 'Fugitive Droid': 141, 'Krang, Master Mind': 16, 'Utrom Scientists': 193}. It affected another artifact creature in **196 games**; 73 games had a cast without a recorded modifier application. Casts alone are not counted as modifier impact, and neither observation proves win causality. Chrome Dome's {5} copy activation remains unsupported and is not credited.

## Distribution audit

1. Shredder improved 12% → 15%; Raphael held at 13%.
2. April moved 53% → 62%, creating a new >60/40 extreme from a near-even cell.
3. Casey improved 23% → 31% and is not excessively Krang-favored; Leonardo moved 68% → 70% but did not exceed the strict >70/30 threshold.
4. Mean balance error worsened 19.5556% → 19.7778%; >60/40 increased 6 → 7, while >70/30 decreased 4 → 3.
5. Early battlefield-presence proxies rose modestly, but first-creature timing did not improve. The supported continuous modifier was exercised in actual game states.
6. Replacing Negate with an artifact body and team artifact modifier strengthens Krang's technology-engine identity, without relying on the unsupported copy activation.

R6-A historical context: its one-copy Turtle Techie reached 40.11% WR, Shredder 17%, Raphael 14%, April 67%, mean error 19.89%, >60/40 7 and >70/30 4. R6-B is less severe on April and >70/30, but still worsens its own runtime-compatible control's mean balance and >60/40 distribution. R6-A is not used as statistical control.

Hypothesis: **PARTIALLY_SUPPORTED**. Cardcade handoff: **RETURN_TO_DESIGN_STUDIO_REJECT_POLARIZATION**. Identity: **IDENTITY_STRENGTHENED**. The primary Shredder cell and artifact mechanism show a real signal, but Raphael does not move and April becomes a new extreme. Return evidence to Design Studio; this is not a promotion decision and Cardcade does not design R6-C.

Nine complete cells, 900/900 unique candidate games, 450 Krang-first and 450 opponent-first starts, 900/900 matching replay fingerprints, no adaptive/replacement seeds, zero runtime errors, and no candidate-vs-candidate games.
