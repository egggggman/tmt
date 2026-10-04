# Baseline 003 Aura-runtime control refresh

Control: `OBL-BASELINE-003-AURA-RUNTIME-REFRESH-001`. Runtime: `ccfa75ed8e817bc3af0a04f75ef048aaee54e5175c06abfc21feaad6515bb0ec`. Source commit: `bd361c5fa5d0671734dacce6fe90a0f6b6a102be`.

The ten unchanged decks were authenticated against the [frozen Baseline 003 manifest](baselines/OBL_BASELINE_003_MANIFEST.json). All 4,500 games completed using the established 45-cell schedule, 100 games per cell, 50 starts each way. Zero runtime errors; all six sampled full-record deterministic replays matched. This is a control refresh, not a combined candidate validation or baseline promotion.

No runtime-equivalence claim is made. Against the previous runtime control, 16/45 cells changed their aggregate result; 129/4,500 individual outcomes and 578/4,500 ending turns changed. The new semantics and generic pilot policy make previously inert Aura slots executable, including the two Retro-Mutations already in unchanged Krang. The candidate was run only after this control completed and passed identity/schedule checks.

[Raw control](BASELINE_003_AURA_RUNTIME_CONTROL.json.gz), [derived metrics](ROUND_6_C_ANALYSIS.json), [prior control](BASELINE_003_RUNTIME_REFRESH_EVIDENCE.json), and [semantic authority](ROUND_6_C_SEMANTIC_READINESS.json). The final runtime also prunes impossible combat block assignments. Its entire 4,500-game control record equals the pre-pruning Aura control record, while all games were freshly rerun under the final identity.

| Global metric | Previous runtime | Aura runtime |
|---|---:|---:|
| mean_matchup_balance_error | 17.67% | 16.67% |
| median_matchup_deviation | 15.00% | 15.00% |
| over_60_40 | 32 | 32 |
| over_70_30 | 17 | 16 |
| aggregate_win_rate_spread | 41.78% | 38.33% |
| aggregate_win_rate_stddev | 14.57% | 13.64% |
| mean_first_player_result_rate | 50.96% | 51.02% |
| mean_ending_turn | 19.9027 | 20.3087 |
| median_ending_turn | 19.0 | 19.0 |

All 45 cells below use the first named deck's win rate. Exact per-deck metrics, wins/losses/draws and outcome-change counts are in the analysis JSON.

| Pair | Previous | Aura runtime | Delta | Changed outcomes |
|---|---:|---:|---:|---:|
| April O'Neil / Bebop & Rocksteady | 44.00% | 49.00% | +5.00 pp | 9 |
| April O'Neil / Casey Jones | 14.00% | 19.00% | +5.00 pp | 7 |
| April O'Neil / Donatello | 41.00% | 43.00% | +2.00 pp | 4 |
| April O'Neil / Krang | 47.00% | 44.00% | -3.00 pp | 13 |
| April O'Neil / Leonardo | 41.00% | 43.00% | +2.00 pp | 10 |
| April O'Neil / Michelangelo | 24.00% | 32.00% | +8.00 pp | 8 |
| April O'Neil / Raphael | 18.00% | 19.00% | +1.00 pp | 5 |
| April O'Neil / Shredder | 18.00% | 18.00% | +0.00 pp | 2 |
| April O'Neil / Splinter | 22.00% | 23.00% | +1.00 pp | 5 |
| Bebop & Rocksteady / Casey Jones | 32.00% | 32.00% | +0.00 pp | 0 |
| Bebop & Rocksteady / Donatello | 53.00% | 53.00% | +0.00 pp | 0 |
| Bebop & Rocksteady / Krang | 49.00% | 46.00% | -3.00 pp | 5 |
| Bebop & Rocksteady / Leonardo | 46.00% | 46.00% | +0.00 pp | 0 |
| Bebop & Rocksteady / Michelangelo | 39.00% | 39.00% | +0.00 pp | 0 |
| Bebop & Rocksteady / Raphael | 24.00% | 24.00% | +0.00 pp | 0 |
| Bebop & Rocksteady / Shredder | 23.00% | 23.00% | +0.00 pp | 0 |
| Bebop & Rocksteady / Splinter | 25.00% | 25.00% | +0.00 pp | 0 |
| Casey Jones / Donatello | 63.00% | 63.00% | +0.00 pp | 0 |
| Casey Jones / Krang | 77.00% | 76.00% | -1.00 pp | 3 |
| Casey Jones / Leonardo | 64.00% | 64.00% | +0.00 pp | 0 |
| Casey Jones / Michelangelo | 65.00% | 65.00% | +0.00 pp | 0 |
| Casey Jones / Raphael | 37.00% | 37.00% | +0.00 pp | 0 |
| Casey Jones / Shredder | 41.00% | 41.00% | +0.00 pp | 0 |
| Casey Jones / Splinter | 58.00% | 58.00% | +0.00 pp | 0 |
| Donatello / Krang | 54.00% | 56.00% | +2.00 pp | 12 |
| Donatello / Leonardo | 65.00% | 65.00% | +0.00 pp | 0 |
| Donatello / Michelangelo | 37.00% | 37.00% | +0.00 pp | 0 |
| Donatello / Raphael | 26.00% | 26.00% | +0.00 pp | 0 |
| Donatello / Shredder | 17.00% | 17.00% | +0.00 pp | 0 |
| Donatello / Splinter | 23.00% | 23.00% | +0.00 pp | 0 |
| Krang / Leonardo | 68.00% | 66.00% | -2.00 pp | 10 |
| Krang / Michelangelo | 32.00% | 36.00% | +4.00 pp | 4 |
| Krang / Raphael | 13.00% | 19.00% | +6.00 pp | 8 |
| Krang / Shredder | 12.00% | 22.00% | +10.00 pp | 12 |
| Krang / Splinter | 20.00% | 26.00% | +6.00 pp | 12 |
| Leonardo / Michelangelo | 40.00% | 40.00% | +0.00 pp | 0 |
| Leonardo / Raphael | 20.00% | 20.00% | +0.00 pp | 0 |
| Leonardo / Shredder | 36.00% | 36.00% | +0.00 pp | 0 |
| Leonardo / Splinter | 36.00% | 36.00% | +0.00 pp | 0 |
| Michelangelo / Raphael | 35.00% | 35.00% | +0.00 pp | 0 |
| Michelangelo / Shredder | 28.00% | 28.00% | +0.00 pp | 0 |
| Michelangelo / Splinter | 36.00% | 36.00% | +0.00 pp | 0 |
| Raphael / Shredder | 47.00% | 47.00% | +0.00 pp | 0 |
| Raphael / Splinter | 54.00% | 54.00% | +0.00 pp | 0 |
| Shredder / Splinter | 67.00% | 67.00% | +0.00 pp | 0 |
