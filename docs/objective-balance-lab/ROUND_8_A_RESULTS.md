# Round 8 A — frozen Bebop & Rocksteady board-development hypothesis

Handoff: **RETURN_TO_DESIGN_STUDIO_FOR_INTERPRETATION**. Cardcade reports execution and distribution evidence. Design Studio owns the hypothesis verdict; aggregate win-rate gain alone is insufficient.

Frozen candidate: **−2 Illegitimate Business / +2 Primordial Pachyderm** against unchanged Baseline 004. No redesign, combined validation, promotion, Baseline 005, or merge occurred.

Candidate SHA-256 `aaa61d3a3d65f7c8ab74062cc8f41d220a46066b44c28e3c71921c570a6b66ed`. Semantic runtime `d4466241f0ffeaca809cd6a05210ad53b9af1011a1d7f833de88657c1cf00924`. The refreshed 4,500-game unchanged control and six deterministic replay samples validated before the 900-game isolated candidate and all 900 deterministic replays. Zero runtime errors; each cell has 50 starts each way.

Aggregate B&R win rate 23.33% → 36.33%; mean matchup balance error 26.67% → 16.56%. Strict >60/40 cells 9 → 6; >70/30 cells 6 → 4.

| Opponent | Control | R8-A | Delta | Role |
|---|---:|---:|---:|---|
| Raphael | 11.00% | 23.00% | +12.00 pp | primary |
| Shredder | 13.00% | 19.00% | +6.00 pp | primary |
| Splinter | 12.00% | 29.00% | +17.00 pp | primary |
| Casey Jones | 16.00% | 26.00% | +10.00 pp | primary |
| Donatello | 39.00% | 54.00% | +15.00 pp | sentinel |
| Leonardo | 31.00% | 35.00% | +4.00 pp | sentinel |
| Krang | 27.00% | 54.00% | +27.00 pp | sentinel |
| April O'Neil | 36.00% | 55.00% | +19.00 pp |  |
| Michelangelo | 25.00% | 32.00% | +7.00 pp |  |

| Distribution metric | Control | R8-A |
|---|---:|---:|
| wins | 210 | 327 |
| losses | 690 | 573 |
| draws | 0 | 0 |
| win_rate | 23.33% | 36.33% |
| mean_matchup_balance_error | 26.67% | 16.56% |
| median_matchup_deviation | 25.00% | 18.00% |
| over_60_40 | 9 | 6 |
| over_70_30 | 6 | 4 |
| first_player_result_rate | 29.56% | 44.00% |
| mean_ending_turn | 18.5833 | 18.4344 |
| median_ending_turn | 17.0 | 17.0 |

| Mechanism observation | Control | R8-A |
|---|---:|---:|
| pachyderm_casts | 0 | 415 |
| pachyderm_etb_life_gain_resolutions | 0 | 415 |
| pachyderm_life_gained | 0 | 830 |
| pachyderm_etb_games | 0 | 363 |
| all_etb_life_gain_events | 0 | 415 |

The raw ETB events preserve source, controller, trigger and stack IDs, amount, and life totals before and after each resolution. Machine analysis includes per-cell paired outcomes, first-creature timing, battlefield presence, ending-turn histograms, cast signatures, and all distribution metrics. The frozen swap also changes B&R from 24 to 22 lands, so this experiment measures the whole substitution rather than isolating life gain from that resource change.

The refreshed unchanged Baseline 004 control has 0/45 changed cell results, 0/4,500 changed outcomes, 4500/4,500 matching state fingerprints, and 0 new ETB life-gain events versus the prior control. The runtime identity changed, so the complete new control is the comparison anchor. No combined candidate validation occurred. A superseded partial 600-game checkpoint is preserved in [audit](audit/R8_A_SUPERSEDED_TELEMETRY_CONTROL_001/README.md) and was excluded from all comparisons.

[Machine analysis](ROUND_8_A_ANALYSIS.json) · [raw candidate](ROUND_8_A_EVIDENCE.json.gz) · [control report](BASELINE_004_R8A_ETB_RUNTIME_CONTROL.md) · [raw control](BASELINE_004_R8A_ETB_RUNTIME_CONTROL.json.gz) · [semantic readiness](ROUND_8_A_SEMANTIC_READINESS.json).
