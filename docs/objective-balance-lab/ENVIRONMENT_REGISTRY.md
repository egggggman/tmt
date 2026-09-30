# Objective Balance Lab — Environment Registry

This is the authoritative human-readable record of the current ten-deck environment. Experiments are cheap. Promotion is expensive.

## Current environment

- Environment ID: `OBL-BASELINE-001`
- Repository SHA: `7d74d24226f904dfb85b3c4a9e57ab8f9de5500a`
- State: `BASELINE`
- Lineage parent: `OBL-BASELINE-000` (`SUPERSEDED`)
- Source combined environment: `OBL-COMBINED-001`
- Next gate: **ROUND_3_EXPERIMENT_DESIGN**
- Promotion basis: combined-environment evidence, not isolated win rate alone.

## Official baselines

| Deck | Official version | Source | SHA-256 | Current WR | Mean Matchup Balance Error | Candidate state | Identity | Semantic confidence | Promotion | Next question |
|---|---|---|---|---:|---:|---|---|---|---|---|
| Leonardo | `OBL-BASELINE-001` | `docs/objective-balance-lab/candidates/LEONARDO_OBL_R1.txt` | `4d5db15f72595d5377c3cd2c6ee57374176fc211a1669ea99c74a8e75744a960` | 36.44% | 15.78% | PROMOTED | IDENTITY_PROTECTED: coordinated board / disciplined leadership | PARTIALLY_REPRESENTED; no core semantic block in Round 1 audit | PROMOTED: OBL-R1-LEONARDO-A | Select between accepted R1 leadership and promising R2B protection before combined validation. |
| Raphael | `OBL-BASELINE-001` | `decks/raphael/PROTOTYPE_0.3.txt` | `220ea90ccc579e09bef38ce972ba84f661c2382b92c7a4559667d24a5eec6f51` | 75.11% | 25.11% | NONE_ACCEPTED | IDENTITY_PROTECTED: confrontation / aggressive pressure | PARTIALLY_REPRESENTED; no core semantic block in Round 1 audit | BASELINE_RETAINED; no eligible candidate promoted | Reduce Casey Jones density without increasing Raphael's already-high power. |
| Donatello | `OBL-BASELINE-001` | `docs/objective-balance-lab/candidates/DONATELLO_OBL_R2_A.txt` | `d9baf095831d82d7fae01af75b61ecf0debefe04a14ad945e67e0db696aa09c6` | 40.11% | 15.89% | PROMOTED | IDENTITY_PROTECTED: artifacts / inventions / technical synergy | PARTIALLY_REPRESENTED; no core semantic block in Round 1 audit | PROMOTED: OBL-R2-DONATELLO-A | Select whether battlefield presence or payoff conversion is the better artifact bottleneck probe. |
| Michelangelo | `OBL-BASELINE-001` | `decks/michelangelo/PROTOTYPE_0.1.txt` | `f5dd228b6e3636bd0de367b9d1a2bd836c0388bf37b00f0c0c047a932973ebf9` | 51.22% | 16.11% | NONE_INCONCLUSIVE | IDENTITY_PROTECTED: energetic / unconventional play | PARTIALLY_REPRESENTED; no core semantic block in Round 1 audit | BASELINE_RETAINED; no eligible candidate promoted | Find a semantically observable unconventional lever. |
| Splinter | `OBL-BASELINE-001` | `decks/splinter/PROTOTYPE_0.1.txt` | `74b6d7f4cab4bcda9eeb80ffc7a779529115c98c161345f13ac1251d85163b0a` | 60.78% | 19.67% | NONE_INCONCLUSIVE | IDENTITY_PROTECTED: patient / disciplined value-control | PARTIALLY_REPRESENTED; no core semantic block in Round 1 audit | BASELINE_RETAINED; no eligible candidate promoted | Find a semantically observable patient-control lever. |
| Shredder | `OBL-BASELINE-001` | `decks/shredder/PROTOTYPE_0.3.txt` | `818e9a847fcdf8521f53ab9b49c0f054ddd6f9bce95e9fd57c89cb6c94da2ed2` | 72.44% | 24.00% | NONE_PROMOTABLE | IDENTITY_PROTECTED: ruthless interaction / villain pressure | PARTIALLY_REPRESENTED; no core semantic block in Round 1 audit | BASELINE_RETAINED; no eligible candidate promoted | Reduce major overperformance with a distinguishable pressure or interaction change. |
| Krang | `OBL-BASELINE-001` | `decks/krang/PROTOTYPE_0.2.txt` | `5a52bc59b5de1034721ba17d1c1d4f12c493ec70681c1a910c8230808e4e4f96` | 38.33% | 21.00% | ACCEPTED_FOR_COMBINED_MATRIX | IDENTITY_PROTECTED: technology / artifact engine | PARTIALLY_REPRESENTED; no core semantic block in Round 1 audit | BASELINE_RETAINED; no eligible candidate promoted | Find an engine route toward center without adding matchup extremes; R2B was mixed. |
| Bebop & Rocksteady | `OBL-BASELINE-001` | `docs/objective-balance-lab/candidates/BEBOP_ROCKSTEADY_OBL_R2_B.txt` | `6d9fb051c62f16b49a6ffc9045efb40d26007e2ffbcdac1e0524e1722cd4f509` | 38.11% | 15.00% | PROMOTED | IDENTITY_PROTECTED: brute-force aggression | PARTIALLY_REPRESENTED; no core semantic block in Round 1 audit | PROMOTED: OBL-R2-BEBOP_ROCKSTEADY-B | Select between creature density and brute-force payoff for combined validation. |
| April O'Neil | `OBL-BASELINE-001` | `decks/april_oneil/PROTOTYPE_0.1.txt` | `684c898760a39c5dfc584206ef4675c49d96cfe6bd419f03f86bd0b8358d09f4` | 26.56% | 23.44% | ACCEPTED_FOR_COMBINED_MATRIX | IDENTITY_PROTECTED: resourceful / adaptive play | PARTIALLY_REPRESENTED; no core semantic block in Round 1 audit | BASELINE_RETAINED; no eligible candidate promoted | Increase resourceful adaptability; R1 weakened in the combined meta. |
| Casey Jones | `OBL-BASELINE-001` | `docs/objective-balance-lab/candidates/CASEY_JONES_OBL_R2_B.txt` | `9cf8a038530dad01f4bc64bc9293889abe389cd043845cf6d538dd29865ad170` | 60.89% | 17.33% | PROMOTED | IDENTITY_PROTECTED: improvised weapons / scrappy aggression | PARTIALLY_REPRESENTED; no core semantic block in Round 1 audit | PROMOTED: OBL-R2-CASEY_JONES-B | Select the stronger artifact/equipment package before combined validation. |

OBL-BASELINE-000 remains preserved as the superseded parent environment. OBL-COMBINED-001 remains preserved as the combined validation evidence. No rejected or inconclusive historical experiment was changed.

The unresolved priorities are Raphael and Shredder overperformance, April and Krang underperformance, Leonardo weakness, Splinter above center, and Michelangelo's semantically difficult movement.
