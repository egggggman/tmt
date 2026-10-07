# Objective Balance Lab — Environment Registry

Experiments are cheap. Promotion is expensive.

## Current environment

- Environment ID: `OBL-BASELINE-005`
- State: `OFFICIAL_BASELINE` upon merge of this promotion; Baseline 004 remains historical and unchanged.
- Lineage: `OBL-BASELINE-004` → `OBL-COMBINED-007` → `OBL-BASELINE-005`
- Promoted deck: Bebop & Rocksteady only, exact `OBL-R8-BEBOP-A` (`−2 Illegitimate Business / +2 Primordial Pachyderm`).
- Current semantic runtime: `d4466241f0ffeaca809cd6a05210ad53b9af1011a1d7f833de88657c1cf00924`.
- Current reference: [Combined 007 evidence](COMBINED_007_R8A_EVIDENCE.json.gz) and [45-cell report](COMBINED_007_R8A_RESULTS.md); 4,500 logical games composed from accepted sources, zero new simulations.
- Accepted isolated evidence: [PR #275](https://github.com/egggggman/tmt/pull/275); combined promotion authority: [PR #276](https://github.com/egggggman/tmt/pull/276).
- Next gate: `BASELINE_005_REVIEW`; no R8-B authorized.
- Land-count provenance: [20 basics in both, 24 → 22 total lands](ROUND_8_A_LAND_COUNT_PROVENANCE.md).

Current Combined 007 metrics: mean matchup balance error **15.64%**, median deviation **14%**, >60/40 **30**, >70/30 **16**, WR spread **35.56%**.

| Deck | Source | SHA-256 | WR | Balance error | Promotion |
|---|---|---|---:|---:|---|
| Leonardo | `docs/objective-balance-lab/candidates/LEONARDO_OBL_R1.txt` | `4d5db15f72595d5377c3cd2c6ee57374176fc211a1669ea99c74a8e75744a960` | 38.67% | 15.33% | BASELINE_RETAINED |
| Raphael | `docs/objective-balance-lab/baselines/RAPHAEL_OBL_BASELINE_002.txt` | `e8d29b97e4fa52bd1a8ae0d8056b5217660b1367e0a386e811908e256dea711f` | 68.44% | 19.11% | BASELINE_RETAINED |
| Donatello | `docs/objective-balance-lab/candidates/DONATELLO_OBL_R2_A.txt` | `d9baf095831d82d7fae01af75b61ecf0debefe04a14ad945e67e0db696aa09c6` | 40.44% | 16.44% | BASELINE_RETAINED |
| Michelangelo | `decks/michelangelo/PROTOTYPE_0.1.txt` | `f5dd228b6e3636bd0de367b9d1a2bd836c0388bf37b00f0c0c047a932973ebf9` | 50.67% | 9.78% | BASELINE_RETAINED |
| Splinter | `decks/splinter/PROTOTYPE_0.1.txt` | `74b6d7f4cab4bcda9eeb80ffc7a779529115c98c161345f13ac1251d85163b0a` | 59.22% | 15.67% | BASELINE_RETAINED |
| Shredder | `docs/objective-balance-lab/baselines/SHREDDER_OBL_BASELINE_003.txt` | `1ce0828b6ac107bc8cdf2e0b965d919e83941316803880a71d11bbbb48902fc1` | 68.78% | 18.78% | BASELINE_RETAINED |
| Krang | `docs/objective-balance-lab/baselines/KRANG_OBL_BASELINE_004.txt` | `2d598af2d05212ffb0f19fe5f315b7bf8f85501975155f394448b0a48fa81ab1` | 44.44% | 13.33% | BASELINE_RETAINED |
| Bebop & Rocksteady | `docs/objective-balance-lab/baselines/BEBOP_ROCKSTEADY_OBL_BASELINE_005.txt` | `aaa61d3a3d65f7c8ab74062cc8f41d220a46066b44c28e3c71921c570a6b66ed` | 36.33% | 16.56% | PROMOTED: OBL-R8-BEBOP-A |
| April O'Neil | `docs/objective-balance-lab/baselines/APRIL_ONEIL_OBL_BASELINE_003.txt` | `ebaff265d90b5cfbec4f7e9662a9d105f9ef8f58a17b06949626ed2ff898b8b7` | 33.22% | 16.78% | BASELINE_RETAINED |
| Casey Jones | `docs/objective-balance-lab/candidates/CASEY_JONES_OBL_R2_B.txt` | `9cf8a038530dad01f4bc64bc9293889abe389cd043845cf6d538dd29865ad170` | 59.78% | 14.67% | BASELINE_RETAINED |

[Baseline 004 manifest](baselines/OBL_BASELINE_004_MANIFEST.json), [cycling-pilot control](BASELINE_004_CYCLING_PILOT_CONTROL.json.gz), and [unchanged ETB-runtime control](BASELINE_004_R8A_ETB_RUNTIME_CONTROL.json.gz) remain historical. No other deck list changed.
