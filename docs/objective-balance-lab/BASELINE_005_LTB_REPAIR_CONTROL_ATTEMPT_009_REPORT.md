# Baseline 005 — LTB Repair Control Attempt 9

Control `OBL-BASELINE-005-LTB-REPAIR-CONTROL-ATTEMPT-009` completed under semantic runtime `defefdce8a716ceef6dcedad1a6f50e2abc367bd3cb772a369853506d2f5398d`.

## Integrity

- **4,500/4,500 games completed** across all 45 matchup cells.
- Zero runtime errors; one draw preserved in the artifact.
- Six deterministic replay cells matched.
- Schedule SHA-256: `b5fd8ab57016b15662fca420d508c9aab3633ad14b7f7515d667492b0f8abf27`.
- Control artifact SHA-256: `55a1f0074e5c61548744ed78421ade014ea04627ac01a6f772dfce5daad19c09`.
- Ten frozen deck hashes and the 172-row ledger remained unchanged.
- Prior failed controls and diagnostics remain excluded; no games were retried or combined.

## Aggregate results

| Deck | Wins / 900 | Win rate | Wilson 95% interval |
| --- | ---: | ---: | ---: |
| Leonardo | 429 | 47.67% | 44.42–50.93% |
| Raphael | 555 | 61.67% | 58.45–64.79% |
| Donatello | 521 | 57.89% | 54.64–61.07% |
| Michelangelo | 453 | 50.33% | 47.07–53.59% |
| Splinter | 608 | 67.56% | 64.43–70.53% |
| Shredder | 329 | 36.56% | 33.47–39.75% |
| Krang | 433 | 48.11% | 44.86–51.38% |
| Bebop & Rocksteady | 316 | 35.11% | 32.06–38.29% |
| April O'Neil | 325 | 36.11% | 33.04–39.30% |
| Casey Jones | 530 | 58.89% | 55.64–62.06% |

## Pace and first-player effects

First player won 2,594/4,500 games (57.64%); each deck started 450 games. Mean ending turn was 19.82, median 18, range 9–71. Distribution: 7 games through turn 10, 2,887 through turn 20, 1,299 through turn 30, 236 through turn 40, and 71 beyond turn 40.

The complete 45-cell matrix is preserved in the machine report and raw control artifact. Notable cells include Splinter over Bebop & Rocksteady 84–16, Splinter over April 82–18, Raphael over April 80–20, and Donatello over Shredder 77–23. These are polarization observations for Design Studio review, not automatic promotion decisions.

## Execution and limitations

The artifact records 87,966 casts, 205,729 activation events, 4,984 aura events, and 942 ETB life-gain events. The fixed AcceptancePilot made all decisions; mechanic exposure is execution telemetry, not causal evidence. No pilot or simulator defect occurred during this control.

## Recommendation

**READY for Design Studio balance interpretation.** This is a mechanically authenticated control, not an authorization to revise decks, merge PRs, promote a baseline, launch another control, or authorize Prototype 0.3. HQ/Design Studio must interpret the matrix separately from simulator and pilot confidence.
