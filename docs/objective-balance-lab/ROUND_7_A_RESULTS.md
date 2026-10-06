# Round 7 A — frozen Krang conversion hypothesis

Handoff: **RETURN_TO_DESIGN_STUDIO_FOR_INTERPRETATION**. Cardcade reports execution and distribution evidence; Design Studio owns the design verdict.

Frozen candidate: **−1 Does Machines, −1 Negate, +1 Ray Fillet, Man Ray, +1 Stockman, Mad Fly-entist**. No deck redesign, combined validation, promotion, or merge occurred.

Candidate SHA-256 `2d598af2d05212ffb0f19fe5f315b7bf8f85501975155f394448b0a48fa81ab1`. Semantic runtime `f40c4888ef9128d03819fc1be86dde1316b2115fd0d4fb365cd03b288453afa1` from `e445b3adb292d394ef3ca457a4b2a33503a8c112`. All 4,500 unchanged Baseline 003 control games and six sampled replays validated before 900 isolated candidate games and all 900 deterministic replays. Zero runtime errors. The nine cells have 50 starts each way.

Aggregate Krang win rate 34.56% → 38.78%; mean matchup balance error 26.33% → 22.33%. Strict >60/40 cells 8 → 7; >70/30 cells 6 → 5.

| Opponent | Control | R7-A | Delta | Role |
|---|---:|---:|---:|---|
| Raphael | 15.00% | 19.00% | +4.00 pp | primary |
| Shredder | 12.00% | 16.00% | +4.00 pp | primary |
| April O'Neil | 41.00% | 43.00% | +2.00 pp | sentinel |
| Leonardo | 63.00% | 61.00% | -2.00 pp | sentinel |
| Splinter | 18.00% | 22.00% | +4.00 pp |  |
| Casey Jones | 16.00% | 22.00% | +6.00 pp |  |
| Michelangelo | 31.00% | 40.00% | +9.00 pp |  |
| Donatello | 29.00% | 37.00% | +8.00 pp |  |
| Bebop & Rocksteady | 86.00% | 89.00% | +3.00 pp |  |

| Distribution metric | Control | R7-A |
|---|---:|---:|
| wins | 311 | 349 |
| losses | 589 | 551 |
| draws | 0 | 0 |
| win_rate | 34.56% | 38.78% |
| mean_matchup_balance_error | 26.33% | 22.33% |
| median_matchup_deviation | 32.00% | 28.00% |
| over_60_40 | 8 | 7 |
| over_70_30 | 6 | 5 |
| first_player_result_rate | 44.44% | 51.78% |
| mean_ending_turn | 21.3856 | 21.2167 |
| median_ending_turn | 20.0 | 20.0 |

| Mechanism observation | Control | R7-A |
|---|---:|---:|
| ray_casts | 625 | 880 |
| stockman_casts | 9 | 12 |
| mutagen_tokens_created | 1717 | 1981 |
| mutagen_announcements | 1286 | 1428 |
| mutagen_paid_costs | 1286 | 1428 |
| mutagen_resolutions | 1286 | 1428 |
| mutagen_delivered | 1286 | 1428 |
| mutagen_counters_placed | 1286 | 1428 |
| mutagen_illegal_targets_at_resolution | 0 | 0 |
| islandcycling_announcements | 574 | 843 |
| islandcycling_paid_costs | 574 | 843 |
| islandcycling_resolutions | 574 | 843 |
| islandcycling_reveals | 574 | 843 |
| islandcycling_found | 574 | 843 |
| islandcycling_shuffles | 574 | 843 |

The raw activation events retain paid mana source IDs, discarded and sacrificed object IDs, target IDs, reveal and shuffle events, resolution status, and turns. The machine analysis contains cell-specific distributions, first-play timing, battlefield presence, paired outcome changes, target IDs, cast signatures, and complete control refresh comparisons. These observations do not by themselves authorize a design decision.

The new semantic runtime changed 31/45 Baseline cells versus the preserved Aura runtime; 729/4,500 outcomes changed. No runtime equivalence is claimed. A prior 500-game failed control checkpoint was preserved in [audit](audit/R7_A_SUPERSEDED_RUNTIME_001/AUDIT.json); none of its games were reused.

[Machine analysis](ROUND_7_A_ANALYSIS.json) · [raw candidate](ROUND_7_A_EVIDENCE.json.gz) · [control report](BASELINE_003_R7A_SEMANTIC_CONTROL.md) · [raw control](BASELINE_003_R7A_SEMANTIC_CONTROL.json.gz) · [semantic readiness](ROUND_7_A_SEMANTIC_READINESS.json).
