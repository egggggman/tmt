# Objective Balance Lab Combined Environment 005 — selection

`OBL-COMBINED-005` is an experimental combined environment, not a promoted baseline. It selects only the two candidates marked promotion-eligible by [Combined 004](COMBINED_004_RESULTS.md), restoring Krang to exact Baseline 002.

| Deck | Build | Source path | Recorded SHA-256 | Parent baseline SHA-256 |
|---|---|---|---|---|
| Leonardo | `OBL-BASELINE-002` | `docs/objective-balance-lab/candidates/LEONARDO_OBL_R1.txt` | `4d5db15f72595d5377c3cd2c6ee57374176fc211a1669ea99c74a8e75744a960` | `4d5db15f72595d5377c3cd2c6ee57374176fc211a1669ea99c74a8e75744a960` |
| Raphael | `OBL-BASELINE-002` | `docs/objective-balance-lab/baselines/RAPHAEL_OBL_BASELINE_002.txt` | `e8d29b97e4fa52bd1a8ae0d8056b5217660b1367e0a386e811908e256dea711f` | `e8d29b97e4fa52bd1a8ae0d8056b5217660b1367e0a386e811908e256dea711f` |
| Donatello | `OBL-BASELINE-002` | `docs/objective-balance-lab/candidates/DONATELLO_OBL_R2_A.txt` | `d9baf095831d82d7fae01af75b61ecf0debefe04a14ad945e67e0db696aa09c6` | `d9baf095831d82d7fae01af75b61ecf0debefe04a14ad945e67e0db696aa09c6` |
| Michelangelo | `OBL-BASELINE-002` | `decks/michelangelo/PROTOTYPE_0.1.txt` | `f5dd228b6e3636bd0de367b9d1a2bd836c0388bf37b00f0c0c047a932973ebf9` | `f5dd228b6e3636bd0de367b9d1a2bd836c0388bf37b00f0c0c047a932973ebf9` |
| Splinter | `OBL-BASELINE-002` | `decks/splinter/PROTOTYPE_0.1.txt` | `74b6d7f4cab4bcda9eeb80ffc7a779529115c98c161345f13ac1251d85163b0a` | `74b6d7f4cab4bcda9eeb80ffc7a779529115c98c161345f13ac1251d85163b0a` |
| Shredder | `OBL-R5-SHREDDER-B` | `docs/objective-balance-lab/candidates/SHREDDER_OBL_R5_B.txt` | `1ce0828b6ac107bc8cdf2e0b965d919e83941316803880a71d11bbbb48902fc1` | `818e9a847fcdf8521f53ab9b49c0f054ddd6f9bce95e9fd57c89cb6c94da2ed2` |
| Krang | `OBL-BASELINE-002` | `decks/krang/PROTOTYPE_0.2.txt` | `5a52bc59b5de1034721ba17d1c1d4f12c493ec70681c1a910c8230808e4e4f96` | `5a52bc59b5de1034721ba17d1c1d4f12c493ec70681c1a910c8230808e4e4f96` |
| Bebop & Rocksteady | `OBL-BASELINE-002` | `docs/objective-balance-lab/candidates/BEBOP_ROCKSTEADY_OBL_R2_B.txt` | `6d9fb051c62f16b49a6ffc9045efb40d26007e2ffbcdac1e0524e1722cd4f509` | `6d9fb051c62f16b49a6ffc9045efb40d26007e2ffbcdac1e0524e1722cd4f509` |
| April O'Neil | `OBL-R5-APRIL_ONEIL-A` | `docs/objective-balance-lab/candidates/APRIL_ONEIL_OBL_R5_A.txt` | `ebaff265d90b5cfbec4f7e9662a9d105f9ef8f58a17b06949626ed2ff898b8b7` | `684c898760a39c5dfc584206ef4675c49d96cfe6bd419f03f86bd0b8358d09f4` |
| Casey Jones | `OBL-BASELINE-002` | `docs/objective-balance-lab/candidates/CASEY_JONES_OBL_R2_B.txt` | `9cf8a038530dad01f4bc64bc9293889abe389cd043845cf6d538dd29865ad170` | `9cf8a038530dad01f4bc64bc9293889abe389cd043845cf6d538dd29865ad170` |

Shredder B: −1 Dream Beavers; −1 Shark Shredder, Killer Clone; +2 Tunnel Rats. April A (`OBL-R5-APRIL_ONEIL-A`, alias `OBL-R5-APRIL-A`): −2 Negate; +1 April, Reporter of the Weird; +1 Utrom Scientists. The other eight decks have no Round 5 diff in this environment.

## Zero-new-game composition

The matrix reuses 28 unchanged [Baseline 002](baselines/OBL_BASELINE_002_MANIFEST.json) cells, 16 [Round 5](ROUND_5_EVIDENCE.json) candidate-vs-baseline cells, and the exact Shredder B–April A cell from [Combined 004](COMBINED_004_EVIDENCE.json). All 45 cells have the same semantic runtime, frozen schedule, deck identities, 100 games, 50/50 starts, and authenticated fingerprints. No game was rerun.

Historical Baseline 002 SHA values can describe CRLF Windows checkout bytes; candidate SHA values identify canonical Git bytes. The verifier checks the recorded hash and exact card content across newline forms without treating different line endings as different deck lists.

Semantic runtime: `78bcce5b5f635f11c67247df91f90fef2bf0dbf948973c5c1ac38419f28b0e25`. Schedule: `b5fd8ab57016b15662fca420d508c9aab3633ad14b7f7515d667492b0f8abf27`.

[Combined 005 manifest](combined/OBL_COMBINED_005_MANIFEST.json) · [machine evidence](COMBINED_005_EVIDENCE.json).
