# Objective Balance Lab Combined Environment 004 — selection

`OBL-COMBINED-004` is an experimental combined environment, not a baseline. No deck list, official prototype, Cardcade semantics, or promotion history changed.

The three selected candidates were already `ACCEPT_FOR_COMBINED_MATRIX` in [Round 5](ROUND_5_RESULTS.md). The other seven decks are exact [Baseline 002](baselines/OBL_BASELINE_002_MANIFEST.json) builds.

| Deck | Build | Exact source | Recorded SHA-256 | Baseline parent SHA-256 |
|---|---|---|---|---|
| Leonardo | `OBL-BASELINE-002` | `docs/objective-balance-lab/candidates/LEONARDO_OBL_R1.txt` | `4d5db15f72595d5377c3cd2c6ee57374176fc211a1669ea99c74a8e75744a960` | `4d5db15f72595d5377c3cd2c6ee57374176fc211a1669ea99c74a8e75744a960` |
| Raphael | `OBL-BASELINE-002` | `docs/objective-balance-lab/baselines/RAPHAEL_OBL_BASELINE_002.txt` | `e8d29b97e4fa52bd1a8ae0d8056b5217660b1367e0a386e811908e256dea711f` | `e8d29b97e4fa52bd1a8ae0d8056b5217660b1367e0a386e811908e256dea711f` |
| Donatello | `OBL-BASELINE-002` | `docs/objective-balance-lab/candidates/DONATELLO_OBL_R2_A.txt` | `d9baf095831d82d7fae01af75b61ecf0debefe04a14ad945e67e0db696aa09c6` | `d9baf095831d82d7fae01af75b61ecf0debefe04a14ad945e67e0db696aa09c6` |
| Michelangelo | `OBL-BASELINE-002` | `decks/michelangelo/PROTOTYPE_0.1.txt` | `f5dd228b6e3636bd0de367b9d1a2bd836c0388bf37b00f0c0c047a932973ebf9` | `f5dd228b6e3636bd0de367b9d1a2bd836c0388bf37b00f0c0c047a932973ebf9` |
| Splinter | `OBL-BASELINE-002` | `decks/splinter/PROTOTYPE_0.1.txt` | `74b6d7f4cab4bcda9eeb80ffc7a779529115c98c161345f13ac1251d85163b0a` | `74b6d7f4cab4bcda9eeb80ffc7a779529115c98c161345f13ac1251d85163b0a` |
| Shredder | `OBL-R5-SHREDDER-B` | `docs/objective-balance-lab/candidates/SHREDDER_OBL_R5_B.txt` | `1ce0828b6ac107bc8cdf2e0b965d919e83941316803880a71d11bbbb48902fc1` | `818e9a847fcdf8521f53ab9b49c0f054ddd6f9bce95e9fd57c89cb6c94da2ed2` |
| Krang | `OBL-R5-KRANG-B` | `docs/objective-balance-lab/candidates/KRANG_OBL_R5_B.txt` | `d1691343e948d96f454468fb360c85e2f68dbe04ae7eed545430560153816bcd` | `5a52bc59b5de1034721ba17d1c1d4f12c493ec70681c1a910c8230808e4e4f96` |
| Bebop & Rocksteady | `OBL-BASELINE-002` | `docs/objective-balance-lab/candidates/BEBOP_ROCKSTEADY_OBL_R2_B.txt` | `6d9fb051c62f16b49a6ffc9045efb40d26007e2ffbcdac1e0524e1722cd4f509` | `6d9fb051c62f16b49a6ffc9045efb40d26007e2ffbcdac1e0524e1722cd4f509` |
| April O'Neil | `OBL-R5-APRIL_ONEIL-A` | `docs/objective-balance-lab/candidates/APRIL_ONEIL_OBL_R5_A.txt` | `ebaff265d90b5cfbec4f7e9662a9d105f9ef8f58a17b06949626ed2ff898b8b7` | `684c898760a39c5dfc584206ef4675c49d96cfe6bd419f03f86bd0b8358d09f4` |
| Casey Jones | `OBL-BASELINE-002` | `docs/objective-balance-lab/candidates/CASEY_JONES_OBL_R2_B.txt` | `9cf8a038530dad01f4bc64bc9293889abe389cd043845cf6d538dd29865ad170` | `9cf8a038530dad01f4bc64bc9293889abe389cd043845cf6d538dd29865ad170` |

## Selection rationale

- Shredder B tests a split reduction in early and closing pressure; its isolated balance error improved 2.56 pp without adding >60/40 cells.
- April A tests proactive development from two Negate slots; isolated balance error improved 4.00 pp and >60/40 fell 7→5. Reporter combat-draw is not credited as a simulated effect.
- Krang B tests an artifact-linked midgame body. Its isolated balance error improved 1.67 pp, but >60/40 rose 6→8; this is the specific combined-risk gate.

The Round 5 parent Negates recorded zero casts. Thus April and Krang are testing active bodies replacing dormant simulation slots, not the cost of counterspells actually used.

## Composition contract

Reuse 21 unchanged Baseline 002 cells and 21 Round 5 candidate-vs-baseline cells; execute only the three candidate-vs-candidate cells (300 games). Every cell retains source artifact, source fingerprint, exact frozen schedule, 50/50 orientation, deck hashes, and semantic runtime identity.

Some historical Baseline 002 deck SHA-256 values were recorded from CRLF Windows checkout bytes, while candidate SHA-256 values identify canonical LF Git bytes. The manifest records the authoritative historical SHA and canonical Git SHA; the verifier independently calculates checkout SHA. Composition verifies exact recorded hashes and byte equality after newline normalization; no card content is normalized away.

Semantic runtime: `78bcce5b5f635f11c67247df91f90fef2bf0dbf948973c5c1ac38419f28b0e25`. Frozen schedule: `b5fd8ab57016b15662fca420d508c9aab3633ad14b7f7515d667492b0f8abf27`.

[Combined manifest](combined/OBL_COMBINED_004_MANIFEST.json) · [Machine evidence](COMBINED_004_EVIDENCE.json).
