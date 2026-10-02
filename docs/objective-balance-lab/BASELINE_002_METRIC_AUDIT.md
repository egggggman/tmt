# Baseline 002 metric consistency audit

Conclusion: **BASELINE_002_METADATA_CORRECTED**. `OBL-BASELINE-002` and the runtime-compatible `OBL-COMBINED-003` have the same deck identities and the same reference metrics. No game was simulated for this audit.

The reported **19.33%** is `global_metrics.combined.mean_matchup_balance_error` in the historical [Combined 001 evidence](COMBINED_001_EVIDENCE.json) (`0.193333`). `tools/build_combined_001_results.py::main` computed it by passing that experiment's `combined_summary` to `global_metrics`, which averaged its matchup deviations. It was the original Baseline 001 promotion result, before the utility semantic runtime refresh. The refreshed Baseline 001 measured `0.192444`; the promoted [Combined 003 evidence](COMBINED_003_RUNTIME_COMPATIBLE_EVIDENCE.json) measured `0.189556`. The Baseline 002 manifest already carried `0.189556`; before this audit, no Baseline 002 artifact stored 19.33% as its reference metric. The Baseline 002 handoff statement misattributed the **PRE_REFRESH_METRIC_USED** value. The registry also had `source_combined_environment: OBL-COMBINED-003` while its inherited `source_combined_evidence` pointed to Combined 001, a **WRONG_EVIDENCE_SOURCE** metadata error. The registry pointer and explicit global metric reference were corrected; historical promotion evidence and verdicts were untouched.

## Independent calculation

The audit grouped the 4,500 authenticated `combined_games` by the 45 unordered deck pairs and verified each 100-game cell fingerprint, deck hash, schedule identity, semantic runtime, and 50/50 orientation against its provenance. For each pair, the credited win rate is `(wins + draws / 2) / 100`, deviation is `abs(win rate - 0.5)`, and mean matchup balance error is the arithmetic mean of the 45 deviations. Counts use strict deviations above `0.1` and `0.2`. Deck WR is `(wins + draws / 2) / 900`. The first-player figure follows the repository's builder: average the ten deck-specific first-seat win rates without half-draw credit.

The historical evidence SHA-256 references and legacy prototype deck hashes were recorded from a Windows CRLF checkout. Promoted candidate deck hashes use LF text. Validation reconstructs the recorded byte convention for each source type, so the same authenticated content passes on Linux LF checkouts. Game-cell fingerprints use canonical JSON and do not depend on checkout line endings.

| Metric | Recomputed Baseline 002 = Combined 003 |
|---|---:|
| Mean matchup balance error | 18.9556% (18.96% rounded) |
| Median matchup deviation | 17% |
| Matchups over 60/40 | 34 |
| Matchups over 70/30 | 18 |
| Aggregate WR spread | 49.2222% |
| Aggregate WR standard deviation | 15.8985% |
| First-player result rate | 50.5556% |
| Mean ending turn | 19.6916 |
| Median ending turn | 18 |
| Worst matchup | April O'Neil 9% / Raphael 91% |

| Deck | Aggregate WR |
|---|---:|
| Leonardo | 36.2222% |
| Raphael | 70.2222% |
| Donatello | 41.0000% |
| Michelangelo | 51.7778% |
| Splinter | 63.3333% |
| Shredder | 75.0000% |
| Krang | 35.1111% |
| Bebop & Rocksteady | 40.0000% |
| April O'Neil | 25.7778% |
| Casey Jones | 61.5556% |

These values exactly match the [Baseline 002 manifest](baselines/OBL_BASELINE_002_MANIFEST.json), the Combined 003 global metrics and all ten Combined 003 deck WRs. The [machine-readable audit](BASELINE_002_METRIC_AUDIT.json) records the evidence hashes, formula, fingerprint digest, and precise values.

The reusable direct-promotion validator now fails when a no-simulation baseline differs from its combined authority in environment identity, cell fingerprints, deck hashes, semantic runtime, schedule, global metrics, or any deck WR. `ROUND_5_EXPERIMENT_DESIGN` is unblocked after this audit.
