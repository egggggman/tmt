# Objective Balance Lab — Environment Registry

Experiments are cheap. Promotion is expensive.

## Current environment

- Environment ID: `OBL-BASELINE-004`
- Source repository SHA: `9df32b344fb659594984285f95cbb6f3683a6cea`
- State: `OFFICIAL_BASELINE` (pending human merge approval while this PR is open)
- Lineage: `OBL-BASELINE-003` → `OBL-COMBINED-006` → `OBL-BASELINE-004`
- Semantic runtime: `f40c4888ef9128d03819fc1be86dde1316b2115fd0d4fb365cd03b288453afa1`
- Promotion: `OBL-PROMOTION-004`
- Changed deck: **Krang only**
- Next gate: **BASELINE_004_REVIEW**

Baseline 003 is preserved unchanged and becomes `SUPERSEDED` only when this promotion PR is merged. Combined 006 remains the immutable promotion authority; promotion runs no new simulations.

Combined 006 reference metrics: mean matchup balance error **22.07%**, median deviation **17%**, >60/40 **33**, >70/30 **22**, WR spread **65.44%**, WR standard deviation **18.76%**.

| Deck | Version | Source | SHA-256 | WR | Balance error | Promotion |
|---|---|---|---|---:|---:|---|
| Leonardo | `OBL-BASELINE-004` | `docs/objective-balance-lab/candidates/LEONARDO_OBL_R1.txt` | `4d5db15f72595d5377c3cd2c6ee57374176fc211a1669ea99c74a8e75744a960` | 43.89% | 17.67% | BASELINE_RETAINED |
| Raphael | `OBL-BASELINE-004` | `docs/objective-balance-lab/baselines/RAPHAEL_OBL_BASELINE_002.txt` | `e8d29b97e4fa52bd1a8ae0d8056b5217660b1367e0a386e811908e256dea711f` | 71.89% | 22.56% | BASELINE_RETAINED |
| Donatello | `OBL-BASELINE-004` | `docs/objective-balance-lab/candidates/DONATELLO_OBL_R2_A.txt` | `d9baf095831d82d7fae01af75b61ecf0debefe04a14ad945e67e0db696aa09c6` | 46.00% | 21.11% | BASELINE_RETAINED |
| Michelangelo | `OBL-BASELINE-004` | `decks/michelangelo/PROTOTYPE_0.1.txt` | `f5dd228b6e3636bd0de367b9d1a2bd836c0388bf37b00f0c0c047a932973ebf9` | 53.33% | 12.44% | BASELINE_RETAINED |
| Splinter | `OBL-BASELINE-004` | `decks/splinter/PROTOTYPE_0.1.txt` | `74b6d7f4cab4bcda9eeb80ffc7a779529115c98c161345f13ac1251d85163b0a` | 63.56% | 20.00% | BASELINE_RETAINED |
| Shredder | `OBL-BASELINE-004` | `docs/objective-balance-lab/baselines/SHREDDER_OBL_BASELINE_003.txt` | `1ce0828b6ac107bc8cdf2e0b965d919e83941316803880a71d11bbbb48902fc1` | 71.67% | 21.67% | BASELINE_RETAINED |
| Krang | `OBL-BASELINE-004` | `docs/objective-balance-lab/baselines/KRANG_OBL_BASELINE_004.txt` | `2d598af2d05212ffb0f19fe5f315b7bf8f85501975155f394448b0a48fa81ab1` | 38.78% | 22.33% | PROMOTED |
| Bebop & Rocksteady | `OBL-BASELINE-004` | `docs/objective-balance-lab/candidates/BEBOP_ROCKSTEADY_OBL_R2_B.txt` | `6d9fb051c62f16b49a6ffc9045efb40d26007e2ffbcdac1e0524e1722cd4f509` | 6.44% | 43.56% | BASELINE_RETAINED |
| April O'Neil | `OBL-BASELINE-004` | `docs/objective-balance-lab/baselines/APRIL_ONEIL_OBL_BASELINE_003.txt` | `ebaff265d90b5cfbec4f7e9662a9d105f9ef8f58a17b06949626ed2ff898b8b7` | 40.22% | 20.22% | BASELINE_RETAINED |
| Casey Jones | `OBL-BASELINE-004` | `docs/objective-balance-lab/candidates/CASEY_JONES_OBL_R2_B.txt` | `9cf8a038530dad01f4bc64bc9293889abe389cd043845cf6d538dd29865ad170` | 64.22% | 19.11% | BASELINE_RETAINED |

All older baselines, prototypes, candidate files, rejected experiments, controls, and raw evidence remain preserved.
