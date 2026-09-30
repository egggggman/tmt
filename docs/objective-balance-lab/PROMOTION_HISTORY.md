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
