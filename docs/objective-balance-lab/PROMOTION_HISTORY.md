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

## Promotion OBL-PROMOTION-004

- Date: `2026-10-06`; source repository commit: `9df32b344fb659594984285f95cbb6f3683a6cea`
- Prior environment: `OBL-BASELINE-003` (preserved; becomes `SUPERSEDED` on merge)
- New environment: `OBL-BASELINE-004`
- Lineage: `OBL-BASELINE-003` → `OBL-COMBINED-006` (`COMBINED_VALIDATED`) → `OBL-BASELINE-004`
- Promoted experiment: `OBL-R7-KRANG-A`
- **Krang is the only deck changed from Baseline 003.**
- Exact diff: `-1 Does Machines; -1 Negate; +1 Ray Fillet, Man Ray; +1 Stockman, Mad Fly-entist`
- Parent Krang SHA-256: `5a52bc59b5de1034721ba17d1c1d4f12c493ec70681c1a910c8230808e4e4f96`
- Promoted Krang SHA-256: `2d598af2d05212ffb0f19fe5f315b7bf8f85501975155f394448b0a48fa81ab1`
- Combined authority: `OBL-COMBINED-006`; report `docs/objective-balance-lab/COMBINED_006_R7A_RESULTS.md`; machine evidence `docs/objective-balance-lab/COMBINED_006_R7A_EVIDENCE.json.gz`
- Accepted isolated evidence: PR #269; Combined 006 evidence: PR #270
- Semantic runtime: `f40c4888ef9128d03819fc1be86dde1316b2115fd0d4fb365cd03b288453afa1`
- Mean matchup balance error: **22.87% → 22.07%**
- >60/40 matchups: **34 → 33**; >70/30: **23 → 22**
- Krang aggregate WR: **34.56% → 38.78%**
- New simulations for promotion: `0`; Combined 006 itself composed 4,500 authenticated source games with `0` new executions.
- Authorization: explicit Objective Balance Lab Baseline 004 promotion request.


## Promotion OBL-PROMOTION-005 — Baseline 005

- Date: `2026-10-07`; source repository commit: `df15e8bff151d07ea5018d8766bba3553eb7b200`
- Prior environment: `OBL-BASELINE-004` (preserved unchanged; becomes `SUPERSEDED` on merge)
- New environment: `OBL-BASELINE-005`; lineage: Baseline 004 → Combined 007 (`COMBINED_VALIDATED`) → Baseline 005
- Promoted experiment: `OBL-R8-BEBOP-A`; **Bebop & Rocksteady is the only deck changed from Baseline 004.**
- Exact diff: `−2 Illegitimate Business / +2 Primordial Pachyderm`
- Parent B&R SHA-256: `6d9fb051c62f16b49a6ffc9045efb40d26007e2ffbcdac1e0524e1722cd4f509`
- Promoted B&R SHA-256: `aaa61d3a3d65f7c8ab74062cc8f41d220a46066b44c28e3c71921c570a6b66ed`
- Accepted isolated evidence: PR #275; Combined 007 promotion evidence: PR #276
- Semantic runtime: `d4466241f0ffeaca809cd6a05210ad53b9af1011a1d7f833de88657c1cf00924`
- Mean matchup balance error: **17.67% → 15.64%**; >60/40: **33 → 30**; >70/30: **18 → 16**; WR spread: **46.44% → 35.56%**
- B&R aggregate WR: **23.33% → 36.33%**; primary cells Raphael/Shredder/Splinter/Casey each improved.
- Both lists retain 20 basic lands. Illegitimate Business is a Land; total lands change **24 → 22**. [Provenance audit](ROUND_8_A_LAND_COUNT_PROVENANCE.md).
- New simulations for promotion: `0`; Combined 007 composed 4,500 authenticated source games with `0` new executions.
- Authorization: explicit Design Studio Baseline 005 promotion request. The land-count provenance is corrected above without changing game evidence or the candidate.
