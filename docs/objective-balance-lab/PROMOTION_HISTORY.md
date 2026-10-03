# Objective Balance Lab — Promotion History

## Initial state

No Objective Balance Lab candidate has yet been promoted into a new official combined baseline.

The current frozen environment is `OBL-BASELINE-000` at repository commit `4f2d69d87bf5a3cbb4d8d9a2508be3851eb2e836`. Its official deck lineage predates OBL and remains the preserved Prototype set recorded in [ENVIRONMENT_REGISTRY.md](ENVIRONMENT_REGISTRY.md).

Round 1 and Round 2 candidates remain experimental evidence. Accepted candidates are eligible for the next combined-matrix selection gate, not automatically promoted.

## Future append-only promotion records

Every future promotion must append a record containing:

- promotion ID;
- prior and new environment IDs;
- changed deck builds and exact hashes;
- candidate experiment IDs;
- combined-matrix evidence and SHA-256;
- environment metric delta;
- date and repository commit;
- explicit authorization.

No future record may rewrite or delete this initial state.

## Promotion OBL-PROMOTION-001

- Prior environment: `OBL-BASELINE-000` (`SUPERSEDED`)
- New environment: `OBL-BASELINE-001`
- Source combined environment: `OBL-COMBINED-001`
- Repository commit: `7d74d24226f904dfb85b3c4a9e57ab8f9de5500a`
- Authorization: explicit Objective Balance Lab promotion request
- Basis: combined-environment evidence, not isolated win rate alone
- Promoted experiments: `OBL-R1-LEONARDO-A`, `OBL-R2-DONATELLO-A`, `OBL-R2-BEBOP_ROCKSTEADY-B`, `OBL-R2-CASEY_JONES-B`
- Retained baseline decks: Raphael, Michelangelo, Splinter, Shredder, Krang, April O'Neil
- Combined evidence: `docs/objective-balance-lab/COMBINED_001_EVIDENCE.json`
- Combined evidence SHA-256: `f2ca3c09e6f07bcba5f754f546bbd5d9a233bf12cf6fd8d08e02fe4539d81bc5`
- Mean Matchup Balance Error: `20.96% → 19.33%` (`-1.62 pp`)
- 70/30 matchups: `21 → 19`
- Aggregate WR spread: `51.11% → 48.56%`
- First-player rate: essentially neutral (`50.38% → 50.40%`)

Krang R2B was not eligible because its isolated improvement reversed/mixed in the combined meta. April R1A weakened in the combined meta and was not eligible. No simulation was rerun and no legacy prototype file was overwritten.

## Promotion OBL-PROMOTION-002

- Date: `2026-10-01`
- Prior environment: `OBL-BASELINE-001` (`SUPERSEDED`)
- New environment: `OBL-BASELINE-002` (`OFFICIAL_BASELINE`)
- Source combined environment: `OBL-COMBINED-003`
- Deck: Raphael
- Candidate: `OBL-R4-RAPHAEL-C`
- Parent deck SHA-256: `220ea90ccc579e09bef38ce972ba84f661c2382b92c7a4559667d24a5eec6f51`
- Promoted deck SHA-256: `e8d29b97e4fa52bd1a8ae0d8056b5217660b1367e0a386e811908e256dea711f`
- Exact diff: `-2 Casey Jones, Jury-Rig Justiciar; -1 Mutant Town Musicians; +2 Skateboard; +1 Spicy Oatmeal Pizza`
- Combined evidence: `docs/objective-balance-lab/COMBINED_003_RUNTIME_COMPATIBLE_EVIDENCE.json` (`2a68b4e2b3e09ef9291b2fde6e64025d9c0b5e499fb85bc4fd562c59958e82e9`)
- Semantic runtime: `78bcce5b5f635f11c67247df91f90fef2bf0dbf948973c5c1ac38419f28b0e25`
- Combined verdict: `COMBINED_VALIDATED`; promotion eligibility: `PROMOTION_ELIGIBLE`
- Reason: lower mean matchup balance error, fewer 60/40 matchups, improved worst matchup, persistent Raphael balance reduction, and strengthened identity. The aggregate WR-spread increase is recorded as an accepted tradeoff.
- Simulations run: `0`
- Authorization: explicit Objective Balance Lab promotion request

## Promotion OBL-PROMOTION-003

- Date: `2026-10-03`; source repository commit: `ed8848c51750d7b2343a35877857304d88371a5e`
- Prior environment: `OBL-BASELINE-002` (`SUPERSEDED`)
- New environment: `OBL-BASELINE-003` (`OFFICIAL_BASELINE`)
- Lineage: `OBL-BASELINE-002` → `OBL-COMBINED-005` (`COMBINED_VALIDATED`) → `OBL-BASELINE-003`
- Combined evidence: `docs/objective-balance-lab/COMBINED_005_EVIDENCE.json` (`f62f65030a841795696c58a9f08e2cb20932111ba7b9848530ccd97902e3519e`)
- Semantic runtime: `78bcce5b5f635f11c67247df91f90fef2bf0dbf948973c5c1ac38419f28b0e25`
- Mean matchup balance error: 18.9556% → 17.6667%
- >60/40 matchups: 34 → 32; >70/30: 18 → 17
- WR spread: 49.2222% → 41.7778%
- Both isolated candidate effects persisted or strengthened under Combined 005; promotion is based on the combined ten-deck environment, not isolated WR alone.
- Carried-forward risk: **Krang vs Shredder 12/88**, the worst matchup; priority diagnostic for the next round.
- New simulations: `0`; new logical games: `0`
- Authorization: explicit Objective Balance Lab promotion request

### Shredder — OBL-PROMOTION-003-SHREDDER

- Candidate: `OBL-R5-SHREDDER-B`
- Parent baseline: `OBL-BASELINE-002`; new baseline: `OBL-BASELINE-003`
- Parent deck SHA-256: `818e9a847fcdf8521f53ab9b49c0f054ddd6f9bce95e9fd57c89cb6c94da2ed2`
- Promoted deck SHA-256: `1ce0828b6ac107bc8cdf2e0b965d919e83941316803880a71d11bbbb48902fc1`
- Exact diff: `-1 Dream Beavers; -1 Shark Shredder, Killer Clone; +2 Tunnel Rats`
- Combined authority: `OBL-COMBINED-005`; evidence `docs/objective-balance-lab/COMBINED_005_EVIDENCE.json`
- Semantic runtime: `78bcce5b5f635f11c67247df91f90fef2bf0dbf948973c5c1ac38419f28b0e25`
- Identity: `IDENTITY_PRESERVED`
- Combined result: `COMBINED_VALIDATION_PASSED`; eligibility: `PROMOTION_ELIGIBLE`; state: `PROMOTED`

### April O'Neil — OBL-PROMOTION-003-APRIL_ONEIL

- Candidate: `OBL-R5-APRIL_ONEIL-A` (alias `OBL-R5-APRIL-A`)
- Parent baseline: `OBL-BASELINE-002`; new baseline: `OBL-BASELINE-003`
- Parent deck SHA-256: `684c898760a39c5dfc584206ef4675c49d96cfe6bd419f03f86bd0b8358d09f4`
- Promoted deck SHA-256: `ebaff265d90b5cfbec4f7e9662a9d105f9ef8f58a17b06949626ed2ff898b8b7`
- Exact diff: `-2 Negate; +1 April, Reporter of the Weird; +1 Utrom Scientists`
- Combined authority: `OBL-COMBINED-005`; evidence `docs/objective-balance-lab/COMBINED_005_EVIDENCE.json`
- Semantic runtime: `78bcce5b5f635f11c67247df91f90fef2bf0dbf948973c5c1ac38419f28b0e25`
- Identity: `IDENTITY_STRENGTHENED`
- Combined result: `COMBINED_VALIDATION_PASSED`; eligibility: `PROMOTION_ELIGIBLE`; state: `PROMOTED`
