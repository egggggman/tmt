# Objective Balance Lab — Environment Registry

Experiments are cheap. Promotion is expensive.

## Current environment

- Environment ID: `OBL-BASELINE-004`
- State: `OFFICIAL_BASELINE`; the ten deck lists and their hashes are unchanged.
- Lineage: `OBL-BASELINE-003` → `OBL-COMBINED-006` → `OBL-BASELINE-004`
- Current simulation runtime: `24ce312cdac00d914606d1f4c111813826ca615768d631532e995faf1c8d57fa`
- Current control: `OBL-BASELINE-004-CYCLING-PILOT-REFRESH-001` — [4,500-game evidence](BASELINE_004_CYCLING_PILOT_CONTROL.json.gz), [45-cell results](BASELINE_004_CYCLING_PILOT_CONTROL.md).
- Founding promotion: `OBL-PROMOTION-004`; Combined 006 and the [original Baseline 004 manifest](baselines/OBL_BASELINE_004_MANIFEST.json) remain historical and unchanged under runtime `f40c4888ef9128d03819fc1be86dde1316b2115fd0d4fb365cd03b288453afa1`.
- Deck changed in founding promotion: Krang only. Decks changed by this control refresh: **zero**.
- Next gate: `ROUND_8_BEBOP_CORRECTED_CONTROL_DIAGNOSIS_INTERPRETATION`. [B&R corrected-control diagnosis](ROUND_8_BEBOP_CORRECTED_CONTROL_DIAGNOSTIC.md) is read-only; no Round 8 candidate is authorized.

Current control metrics: mean matchup balance error **17.67%**, median deviation **14%**, >60/40 **33**, >70/30 **18**, WR spread **46.44%**, WR standard deviation **14.58%**.

| Deck | Version | Source | SHA-256 | Current WR | Current balance error | Promotion |
|---|---|---|---|---:|---:|---|
| Leonardo | `OBL-BASELINE-004` | `docs/objective-balance-lab/candidates/LEONARDO_OBL_R1.txt` | `4d5db15f72595d5377c3cd2c6ee57374176fc211a1669ea99c74a8e75744a960` | 39.11% | 15.78% | BASELINE_RETAINED |
| Raphael | `OBL-BASELINE-004` | `docs/objective-balance-lab/baselines/RAPHAEL_OBL_BASELINE_002.txt` | `e8d29b97e4fa52bd1a8ae0d8056b5217660b1367e0a386e811908e256dea711f` | 69.78% | 20.44% | BASELINE_RETAINED |
| Donatello | `OBL-BASELINE-004` | `docs/objective-balance-lab/candidates/DONATELLO_OBL_R2_A.txt` | `d9baf095831d82d7fae01af75b61ecf0debefe04a14ad945e67e0db696aa09c6` | 42.11% | 17.22% | BASELINE_RETAINED |
| Michelangelo | `OBL-BASELINE-004` | `decks/michelangelo/PROTOTYPE_0.1.txt` | `f5dd228b6e3636bd0de367b9d1a2bd836c0388bf37b00f0c0c047a932973ebf9` | 51.44% | 10.56% | BASELINE_RETAINED |
| Splinter | `OBL-BASELINE-004` | `decks/splinter/PROTOTYPE_0.1.txt` | `74b6d7f4cab4bcda9eeb80ffc7a779529115c98c161345f13ac1251d85163b0a` | 61.11% | 17.56% | BASELINE_RETAINED |
| Shredder | `OBL-BASELINE-004` | `docs/objective-balance-lab/baselines/SHREDDER_OBL_BASELINE_003.txt` | `1ce0828b6ac107bc8cdf2e0b965d919e83941316803880a71d11bbbb48902fc1` | 69.44% | 19.44% | BASELINE_RETAINED |
| Krang | `OBL-BASELINE-004` | `docs/objective-balance-lab/baselines/KRANG_OBL_BASELINE_004.txt` | `2d598af2d05212ffb0f19fe5f315b7bf8f85501975155f394448b0a48fa81ab1` | 47.44% | 15.44% | PROMOTED: OBL-R7-KRANG-A |
| Bebop & Rocksteady | `OBL-BASELINE-004` | `docs/objective-balance-lab/candidates/BEBOP_ROCKSTEADY_OBL_R2_B.txt` | `6d9fb051c62f16b49a6ffc9045efb40d26007e2ffbcdac1e0524e1722cd4f509` | 23.33% | 26.67% | BASELINE_RETAINED |
| April O'Neil | `OBL-BASELINE-004` | `docs/objective-balance-lab/baselines/APRIL_ONEIL_OBL_BASELINE_003.txt` | `ebaff265d90b5cfbec4f7e9662a9d105f9ef8f58a17b06949626ed2ff898b8b7` | 35.33% | 17.78% | BASELINE_RETAINED |
| Casey Jones | `OBL-BASELINE-004` | `docs/objective-balance-lab/candidates/CASEY_JONES_OBL_R2_B.txt` | `9cf8a038530dad01f4bc64bc9293889abe389cd043845cf6d538dd29865ad170` | 60.89% | 15.78% | BASELINE_RETAINED |

The original Combined 006 metrics remain in the immutable Baseline 004 promotion manifest and in `original_promotion_reference` in the machine registry. All older baselines, prototypes, candidates, controls, and raw evidence remain preserved.
