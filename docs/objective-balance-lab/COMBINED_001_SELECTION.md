# OBL-COMBINED-001 Selection

This is a provisional combined validation environment, not a baseline and not a promotion. Selection follows the governance gate and uses only preserved baseline or accepted candidate files.

- Environment: `OBL-COMBINED-001`
- State: `EXPERIMENTAL_COMBINED_ENVIRONMENT`
- Parent: `OBL-BASELINE-000`
- Repository SHA: `0017d9d3b65d57474789ef24471deb615a9b1e54`

| Deck | Selected experiment | Source | Selected SHA-256 | Parent baseline SHA-256 | Diff | Rationale |
|---|---|---|---|---|---|---|
| Leonardo | `OBL-R1-LEONARDO-A` | `docs/objective-balance-lab/candidates/LEONARDO_OBL_R1.txt` | `4d5db15f72595d5377c3cd2c6ee57374176fc211a1669ea99c74a8e75744a960` | `d49d155858938d6fc64127c1678e591ee77abad3b7da8302880f16379476fb08` | -1 The Last Ronin's Technique; +1 Leader's Talent | Round 1 has the stronger balance-error improvement (-0.56 pp); R2B improves the >70/30 count but is balance-neutral, so R1 is selected. |
| Raphael | `BASELINE` | `decks/raphael/PROTOTYPE_0.3.txt` | `220ea90ccc579e09bef38ce972ba84f661c2382b92c7a4559667d24a5eec6f51` | `220ea90ccc579e09bef38ce972ba84f661c2382b92c7a4559667d24a5eec6f51` | none; none | No candidate is accepted; preserve the baseline while the Casey-density reduction goal remains unresolved. |
| Donatello | `OBL-R2-DONATELLO-A` | `docs/objective-balance-lab/candidates/DONATELLO_OBL_R2_A.txt` | `d9baf095831d82d7fae01af75b61ecf0debefe04a14ad945e67e0db696aa09c6` | `b0d8a0dc42b267ac1a162096fe6e0336176f92db9a79a95f1c7dbd0d5c2d2cc6` | -2 Bespoke Bō; +2 Donatello, Turtle Techie | Accepted R2A improves balance error by -0.78 pp, strengthens identity, and reduces >70/30 matchups 5→4. |
| Michelangelo | `BASELINE` | `decks/michelangelo/PROTOTYPE_0.1.txt` | `f5dd228b6e3636bd0de367b9d1a2bd836c0388bf37b00f0c0c047a932973ebf9` | `f5dd228b6e3636bd0de367b9d1a2bd836c0388bf37b00f0c0c047a932973ebf9` | none; none | R1 and R2 produced zero observable delta; preserve baseline pending a semantically observable experiment. |
| Splinter | `BASELINE` | `decks/splinter/PROTOTYPE_0.1.txt` | `74b6d7f4cab4bcda9eeb80ffc7a779529115c98c161345f13ac1251d85163b0a` | `74b6d7f4cab4bcda9eeb80ffc7a779529115c98c161345f13ac1251d85163b0a` | none; none | R1 and R2 produced zero observable delta; preserve baseline pending a semantically observable experiment. |
| Shredder | `BASELINE` | `decks/shredder/PROTOTYPE_0.3.txt` | `818e9a847fcdf8521f53ab9b49c0f054ddd6f9bce95e9fd57c89cb6c94da2ed2` | `818e9a847fcdf8521f53ab9b49c0f054ddd6f9bce95e9fd57c89cb6c94da2ed2` | none; none | No candidate produced a downward power delta; preserve this major overperformer unchanged for environmental interaction measurement. |
| Krang | `OBL-R2-KRANG-B` | `docs/objective-balance-lab/candidates/KRANG_OBL_R2_B.txt` | `6b502e7e9cafda4b3b14e4659eecabae820961c6f9a1afb99b5ddf21606856eb` | `5a52bc59b5de1034721ba17d1c1d4f12c493ec70681c1a910c8230808e4e4f96` | -2 Bespoke Bō; +2 Donatello, Gadget Master | Accepted R2B is the only tested route with a balance-error improvement, but its >60/40 count rises 6→8; select for combined interaction testing, not promotion. |
| Bebop & Rocksteady | `OBL-R2-BEBOP_ROCKSTEADY-B` | `docs/objective-balance-lab/candidates/BEBOP_ROCKSTEADY_OBL_R2_B.txt` | `6d9fb051c62f16b49a6ffc9045efb40d26007e2ffbcdac1e0524e1722cd4f509` | `3875706a76ffab14d2a82ba836da9e59bce49de2f990a348941490e78a61ef9d` | -2 Tainted Treats; +2 Rocksteady, Crash Courser | Strongest accepted package: balance error improves -3.44 pp while identity strengthens. |
| April O'Neil | `OBL-R1-APRIL_ONEIL-A` | `docs/objective-balance-lab/candidates/APRIL_ONEIL_OBL_R1.txt` | `22b2632d838b869812c6765d08f72c4463895ae0bdce75ee9917acd34e314aaa` | `684c898760a39c5dfc584206ef4675c49d96cfe6bd419f03f86bd0b8358d09f4` | -2 Return to the Sewers; +2 April O'Neil, Hacktivist | R1 improves balance error -2.44 pp versus R2A -0.44 pp; choose the stronger global balance signal. |
| Casey Jones | `OBL-R2-CASEY_JONES-B` | `docs/objective-balance-lab/candidates/CASEY_JONES_OBL_R2_B.txt` | `9cf8a038530dad01f4bc64bc9293889abe389cd043845cf6d538dd29865ad170` | `f18d2dd6591520e495a0c723e1d15f5d3f4f6ce8a2693e4f93be0cd6660e838f` | -2 Mutant Town Musicians; +1 Mouser Foundry, +1 Spicy Oatmeal Pizza | R2B improves balance error -1.22 pp versus R1 -1.00 pp and strengthens Casey's artifact identity. |

No candidate is promoted. Krang R2B is selected for interaction testing despite its isolated 6→8 increase in >60/40 matchups because it is accepted for combined-matrix validation; that concern is a specific combined gate question.
