# Objective Balance Lab — Environment Registry

This is the authoritative human-readable record of the frozen ten-deck environment. Experiments are cheap. Promotion is expensive. No Round 1 or Round 2 candidate has been promoted.

## Environment

- Environment ID: `OBL-BASELINE-000`
- Repository SHA: `4f2d69d87bf5a3cbb4d8d9a2508be3851eb2e836`
- State: `BASELINE`
- Next gate: **SELECT COMBINED-MATRIX CANDIDATES**
- Promotion rule: isolated evidence, candidate selection, combined-environment validation, then explicit promotion.

## Official baselines

| Deck | Official version | Source | SHA-256 | Baseline WR | Mean Matchup Balance Error | Strongest experiment | Candidate status | Identity | Semantic confidence | Promotion | Next question |
|---|---|---|---|---:|---:|---|---|---|---|---|---|
| Leonardo | Prototype 0.1 | `decks/leonardo/PROTOTYPE_0.1.txt` | `d49d155858938d6fc64127c1678e591ee77abad3b7da8302880f16379476fb08` | 35.44% | 16.78% | `OBL-R1-LEONARDO-A` | ACCEPTED_FOR_COMBINED_MATRIX | IDENTITY_PROTECTED: coordinated board / disciplined leadership | PARTIALLY_REPRESENTED; no core semantic block in Round 1 audit | BASELINE_UNCHANGED; no candidate promoted | Select between accepted R1 leadership and promising R2B protection before combined validation. |
| Raphael | Prototype 0.3 | `decks/raphael/PROTOTYPE_0.3.txt` | `220ea90ccc579e09bef38ce972ba84f661c2382b92c7a4559667d24a5eec6f51` | 76.78% | 26.78% | `none` | NONE_ACCEPTED | IDENTITY_PROTECTED: confrontation / aggressive pressure | PARTIALLY_REPRESENTED; no core semantic block in Round 1 audit | BASELINE_UNCHANGED; no candidate promoted | Find a lower-efficiency confrontation package that reduces the major overperformance. |
| Donatello | Prototype 0.3c | `decks/donatello/PROTOTYPE_0.3c.txt` | `b0d8a0dc42b267ac1a162096fe6e0336176f92db9a79a95f1c7dbd0d5c2d2cc6` | 41.00% | 18.11% | `OBL-R2-DONATELLO-A` | ACCEPTED_FOR_COMBINED_MATRIX | IDENTITY_PROTECTED: artifacts / inventions / technical synergy | PARTIALLY_REPRESENTED; no core semantic block in Round 1 audit | BASELINE_UNCHANGED; no candidate promoted | Select whether battlefield presence or payoff conversion is the better artifact bottleneck probe. |
| Michelangelo | Prototype 0.1 | `decks/michelangelo/PROTOTYPE_0.1.txt` | `f5dd228b6e3636bd0de367b9d1a2bd836c0388bf37b00f0c0c047a932973ebf9` | 54.11% | 18.33% | `none` | NONE_INCONCLUSIVE | IDENTITY_PROTECTED: energetic / unconventional play | PARTIALLY_REPRESENTED; no core semantic block in Round 1 audit | BASELINE_UNCHANGED; no candidate promoted | Find a mechanically observable unconventional lever; current swaps are zero-delta. |
| Splinter | Prototype 0.1 | `decks/splinter/PROTOTYPE_0.1.txt` | `74b6d7f4cab4bcda9eeb80ffc7a779529115c98c161345f13ac1251d85163b0a` | 62.78% | 21.67% | `none` | NONE_INCONCLUSIVE | IDENTITY_PROTECTED: patient / disciplined value-control | PARTIALLY_REPRESENTED; no core semantic block in Round 1 audit | BASELINE_UNCHANGED; no candidate promoted | Find a mechanically observable patient-control lever; current swaps are zero-delta. |
| Shredder | Prototype 0.3 | `decks/shredder/PROTOTYPE_0.3.txt` | `818e9a847fcdf8521f53ab9b49c0f054ddd6f9bce95e9fd57c89cb6c94da2ed2` | 73.00% | 24.56% | `none` | NONE_PROMOTABLE | IDENTITY_PROTECTED: ruthless interaction / villain pressure | PARTIALLY_REPRESENTED; no core semantic block in Round 1 audit | BASELINE_UNCHANGED; no candidate promoted | Reduce major overperformance with a Cardcade-distinguishable pressure or interaction change. |
| Krang | Prototype 0.2 | `decks/krang/PROTOTYPE_0.2.txt` | `5a52bc59b5de1034721ba17d1c1d4f12c493ec70681c1a910c8230808e4e4f96` | 35.11% | 20.89% | `OBL-R2-KRANG-B` | ACCEPTED_FOR_COMBINED_MATRIX | IDENTITY_PROTECTED: technology / artifact engine | PARTIALLY_REPRESENTED; no core semantic block in Round 1 audit | BASELINE_UNCHANGED; no candidate promoted | Select a route toward center without adding new matchup extremes. |
| Bebop & Rocksteady | Prototype 0.1 | `decks/bebop_rocksteady/PROTOTYPE_0.1.txt` | `3875706a76ffab14d2a82ba836da9e59bce49de2f990a348941490e78a61ef9d` | 32.67% | 19.78% | `OBL-R2-BEBOP_ROCKSTEADY-B` | ACCEPTED_FOR_COMBINED_MATRIX | IDENTITY_PROTECTED: brute-force aggression | PARTIALLY_REPRESENTED; no core semantic block in Round 1 audit | BASELINE_UNCHANGED; no candidate promoted | Select between creature density and brute-force payoff for combined validation. |
| April O'Neil | Prototype 0.1 | `decks/april_oneil/PROTOTYPE_0.1.txt` | `684c898760a39c5dfc584206ef4675c49d96cfe6bd419f03f86bd0b8358d09f4` | 25.67% | 24.33% | `OBL-R1-APRIL_ONEIL-A` | ACCEPTED_FOR_COMBINED_MATRIX | IDENTITY_PROTECTED: resourceful / adaptive play | PARTIALLY_REPRESENTED; no core semantic block in Round 1 audit | BASELINE_UNCHANGED; no candidate promoted | Select between R1 resource advantage and R2A selection before combined validation. |
| Casey Jones | Prototype 0.3 | `decks/casey_jones/PROTOTYPE_0.3.txt` | `f18d2dd6591520e495a0c723e1d15f5d3f4f6ce8a2693e4f93be0cd6660e838f` | 63.44% | 18.33% | `OBL-R2-CASEY_JONES-B` | ACCEPTED_FOR_COMBINED_MATRIX | IDENTITY_PROTECTED: improvised weapons / scrappy aggression | PARTIALLY_REPRESENTED; no core semantic block in Round 1 audit | BASELINE_UNCHANGED; no candidate promoted | Select the stronger artifact/equipment package before combined validation. |

## Lineage and evidence

Each deck's candidate lineage is recorded in `ENVIRONMENT_REGISTRY.json`. Full game-level evidence remains in the immutable Round 1 and Round 2 artifacts; this registry references those files by SHA-256 rather than duplicating them.

The current environment is intentionally named `OBL-BASELINE-000`. Future promoted environments increment the numeric suffix. Experimental combined environments use `OBL-COMBINED-R<round>-<variant>` or another stable documented identifier.
