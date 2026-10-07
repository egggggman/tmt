# Round 8 A land-count provenance

The exact frozen substitution is **−2 Illegitimate Business / +2 Primordial Pachyderm**. The authenticated parent and candidate deck files each contain **10 Forest and 10 Swamp**, so both retain **20 basic lands**. The frozen card catalog identifies **Illegitimate Business as a Land** with a mana ability. Baseline 004 contains four copies and R8-A two copies. Therefore total lands are **24 → 22**, and the substitution changes two land slots.

| Source | Basic lands | Illegitimate Business | Total lands | SHA-256 |
|---|---:|---:|---:|---|
| [Baseline 004 B&R](candidates/BEBOP_ROCKSTEADY_OBL_R2_B.txt) | 20 | 4 | 24 | `6d9fb051c62f16b49a6ffc9045efb40d26007e2ffbcdac1e0524e1722cd4f509` |
| [Frozen R8-A](candidates/BEBOP_ROCKSTEADY_OBL_R8_A.txt) | 20 | 2 | 22 | `aaa61d3a3d65f7c8ab74062cc8f41d220a46066b44c28e3c71921c570a6b66ed` |

The R8-A readiness, 4,500-game unchanged control, 900-game isolated evidence, and Combined 007 all authenticate the candidate and runtime. Their raw game records and hashes are unchanged by this clarification. The machine evidence contains no derived `land_count` or `resource_count` metadata to repair. `land_miss` and `mana_source_ids` are event/metric fields, not assertions that the deck contains 20 total lands. No games were rerun.

This clarification preserves the valid measured result while making the resource tradeoff explicit. It does not claim that the candidate kept the same total land count.
