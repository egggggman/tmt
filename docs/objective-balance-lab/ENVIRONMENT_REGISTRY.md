# Objective Balance Lab — Environment Registry

Experiments are cheap. Promotion is expensive.

## Current environment

- Environment ID: `OBL-BASELINE-003`
- Repository SHA: `ed8848c51750d7b2343a35877857304d88371a5e`
- State: `OFFICIAL_BASELINE`
- Lineage: `OBL-BASELINE-002` → `OBL-COMBINED-005` → `OBL-BASELINE-003`
- Semantic runtime: `78bcce5b5f635f11c67247df91f90fef2bf0dbf948973c5c1ac38419f28b0e25`
- Next gate: **ROUND_6_EXPERIMENT_DESIGN**

Baseline 002 is now `SUPERSEDED`, not deleted. Combined 005 is `COMBINED_VALIDATED` as promotion authority; its historical evidence remains unchanged.

Exact reference metrics are copied from [Combined 005](COMBINED_005_EVIDENCE.json): mean balance error 17.6667%, median deviation 15%, >60/40 32, >70/30 17, WR spread 41.7778%, WR standard deviation 14.5737%, first-player rate 50.9556%, mean turn 19.9027, median turn 19.

**Carried-forward risk:** Krang loses 12/88 to Shredder, the environment's worst matchup. This is a priority diagnostic, not a deck change in this promotion.

| Deck | Version | Source | SHA-256 | WR | Balance error | Promotion |
|---|---|---|---|---:|---:|---|
| Leonardo | `OBL-BASELINE-003` | `docs/objective-balance-lab/candidates/LEONARDO_OBL_R1.txt` | `4d5db15f72595d5377c3cd2c6ee57374176fc211a1669ea99c74a8e75744a960` | 38.67% | 14.22% | BASELINE_RETAINED |
| Raphael | `OBL-BASELINE-003` | `docs/objective-balance-lab/baselines/RAPHAEL_OBL_BASELINE_002.txt` | `e8d29b97e4fa52bd1a8ae0d8056b5217660b1367e0a386e811908e256dea711f` | 69.78% | 20.44% | BASELINE_RETAINED |
| Donatello | `OBL-BASELINE-003` | `docs/objective-balance-lab/candidates/DONATELLO_OBL_R2_A.txt` | `d9baf095831d82d7fae01af75b61ecf0debefe04a14ad945e67e0db696aa09c6` | 40.56% | 15.67% | BASELINE_RETAINED |
| Michelangelo | `OBL-BASELINE-003` | `decks/michelangelo/PROTOTYPE_0.1.txt` | `f5dd228b6e3636bd0de367b9d1a2bd836c0388bf37b00f0c0c047a932973ebf9` | 51.33% | 16.00% | BASELINE_RETAINED |
| Splinter | `OBL-BASELINE-003` | `decks/splinter/PROTOTYPE_0.1.txt` | `74b6d7f4cab4bcda9eeb80ffc7a779529115c98c161345f13ac1251d85163b0a` | 62.11% | 18.56% | BASELINE_RETAINED |
| Shredder | `OBL-BASELINE-003` | `docs/objective-balance-lab/baselines/SHREDDER_OBL_BASELINE_003.txt` | `1ce0828b6ac107bc8cdf2e0b965d919e83941316803880a71d11bbbb48902fc1` | 71.67% | 21.67% | PROMOTED |
| Krang | `OBL-BASELINE-003` | `decks/krang/PROTOTYPE_0.2.txt` | `5a52bc59b5de1034721ba17d1c1d4f12c493ec70681c1a910c8230808e4e4f96` | 35.33% | 19.56% | BASELINE_RETAINED |
| Bebop & Rocksteady | `OBL-BASELINE-003` | `docs/objective-balance-lab/candidates/BEBOP_ROCKSTEADY_OBL_R2_B.txt` | `6d9fb051c62f16b49a6ffc9045efb40d26007e2ffbcdac1e0524e1722cd4f509` | 38.56% | 13.44% | BASELINE_RETAINED |
| April O'Neil | `OBL-BASELINE-003` | `docs/objective-balance-lab/baselines/APRIL_ONEIL_OBL_BASELINE_003.txt` | `ebaff265d90b5cfbec4f7e9662a9d105f9ef8f58a17b06949626ed2ff898b8b7` | 29.89% | 20.11% | PROMOTED |
| Casey Jones | `OBL-BASELINE-003` | `docs/objective-balance-lab/candidates/CASEY_JONES_OBL_R2_B.txt` | `9cf8a038530dad01f4bc64bc9293889abe389cd043845cf6d538dd29865ad170` | 62.11% | 17.00% | BASELINE_RETAINED |

All older baselines, candidate files, raw evidence, and rejected/inconclusive verdicts are preserved.
