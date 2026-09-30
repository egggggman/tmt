# OBL-COMBINED-002 Results

Logical games: **4,500**. Newly executed: **100**. Reused authenticated games: **4,400**. Environment decision: **COMBINED_ENVIRONMENT_REGRESSED**.

## Global metrics

| Metric | OBL-BASELINE-001 | OBL-COMBINED-002 | Δ |
|---|---:|---:|---:|
| mean_matchup_balance_error | 0.193333 | 0.194222 | 0.0008890000000000009 |
| median_matchup_deviation | 0.17 | 0.15 | -0.020000000000000018 |
| over_60_40 | 36 | 35 | -1 |
| over_70_30 | 19 | 18 | -1 |
| aggregate_win_rate_spread | 0.485555 | 0.486666 | 0.0011109999999999731 |
| mean_first_player_result_rate | 0.504 | 0.501778 | -0.0022220000000000573 |
| mean_ending_turn | 19.4982 | 19.4458 | -0.05240000000000222 |
| median_ending_turn | 18.0 | 18.0 | 0.0 |

## Deck metrics

| Deck | Baseline WR | Combined WR | Balance error baseline → combined | 60/40 | 70/30 | Worst matchup |
|---|---:|---:|---:|---:|---:|---|
| leonardo | 36.44% | 37.44% | 15.78% → 15.22% | 6 → 6 | 3 → 2 | raphael 17.00% → raphael 17.00% |
| raphael | 75.11% | 75.22% | 25.11% → 25.22% | 8 → 8 | 5 → 5 | krang 92.00% → krang 92.00% |
| donatello | 40.11% | 41.67% | 15.89% → 17.44% | 7 → 8 | 3 → 3 | shredder 16.00% → shredder 16.00% |
| michelangelo | 51.22% | 51.00% | 16.11% → 15.89% | 8 → 8 | 2 → 2 | april_oneil 78.00% → april_oneil 78.00% |
| splinter | 60.78% | 60.67% | 19.67% → 19.56% | 8 → 8 | 4 → 4 | april_oneil 79.00% → april_oneil 79.00% |
| shredder | 72.44% | 72.33% | 24.00% → 23.89% | 7 → 7 | 6 → 6 | krang 86.00% → april_oneil 86.00% |
| krang | 38.33% | 36.33% | 21.00% → 21.00% | 7 → 7 | 5 → 4 | raphael 8.00% → raphael 8.00% |
| bebop_rocksteady | 38.11% | 37.78% | 15.00% → 15.11% | 6 → 5 | 3 → 3 | raphael 21.00% → raphael 21.00% |
| april_oneil | 26.56% | 26.56% | 23.44% → 23.44% | 8 → 6 | 5 → 5 | raphael 10.00% → raphael 9.00% |
| casey_jones | 60.89% | 61.00% | 17.33% → 17.44% | 7 → 7 | 2 → 2 | april_oneil 86.00% → april_oneil 87.00% |

## Candidate interaction

- April A: isolated 27.22%, combined 26.56%; balance classification `DELTA_WEAKENS`; April-vs-Krang rate `40.00%`.
- Krang A: isolated 36.00%, combined 36.33%; balance classification `DELTA_WEAKENS`; Krang-vs-April rate `60.00%`.

April is `COMBINED_VALIDATION_MIXED` and `NOT_PROMOTION_ELIGIBLE`: its isolated gain disappears in the combined environment, although its extreme-count profile improves. Krang is `COMBINED_VALIDATION_FAILED` and `NOT_PROMOTION_ELIGIBLE` because its balance position does not improve in the combined environment.

Machine evidence: `COMBINED_002_EVIDENCE.json`; manifest: `combined/OBL_COMBINED_002_MANIFEST.json`; new pairing: `COMBINED_002_NEW_PAIRING.json`.
