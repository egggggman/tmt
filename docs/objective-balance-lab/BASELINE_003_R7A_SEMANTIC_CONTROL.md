# Baseline 003 — R7-A semantic runtime control

Control `OBL-BASELINE-003-R7A-SEMANTIC-REFRESH-001` under runtime `f40c4888ef9128d03819fc1be86dde1316b2115fd0d4fb365cd03b288453afa1`. Ten unchanged decks, 45 cells, 4,500 games, 50 starts each way, six matching deterministic replay samples, zero runtime errors. Completed before the R7-A candidate. No equivalence claim, combined test, or promotion.

Against the preserved Aura runtime, 31/45 cells changed aggregate result and 729/4,500 individual outcomes changed. The full Baseline 003 distribution and every cell comparison are retained in [analysis](ROUND_7_A_ANALYSIS.json).

| Global metric | Preserved Aura runtime | New runtime |
|---|---:|---:|
| mean_matchup_balance_error | 16.67% | 22.87% |
| median_matchup_deviation | 15.00% | 21.00% |
| over_60_40 | 32 | 34 |
| over_70_30 | 16 | 23 |
| aggregate_win_rate_spread | 38.33% | 65.56% |
| aggregate_win_rate_stddev | 13.64% | 19.16% |
| mean_first_player_result_rate | 51.02% | 56.69% |
| mean_ending_turn | 20.3087 | 20.1218 |
| median_ending_turn | 19.0 | 18.0 |

[Raw control](BASELINE_003_R7A_SEMANTIC_CONTROL.json.gz) · [prior control](BASELINE_003_AURA_RUNTIME_CONTROL.json.gz) · [semantic authority](ROUND_7_A_SEMANTIC_READINESS.json).
