# Combined Environment 003 — Selection and Composition Gate

Status: `BLOCKED_BY_RUNTIME_INCOMPATIBILITY`

The proposed environment would select `OBL-R4-RAPHAEL-C` for Raphael and retain the other nine OBL-BASELINE-001 decks. No games were run and no combined matrix was produced.

## Fail-closed result

The 36 baseline-vs-baseline cells in Combined 001 were authenticated under repository `0017d9d3b65d57474789ef24471deb615a9b1e54`. The nine Raphael R4-C cells were generated under `8b8a3b353d4aac9f00704adf57383101d9c1e048`, after generic Skateboard, Equipment, Food, permanent-casting, and utility telemetry support changed Cardcade/Pilot semantics.

The frozen schedule identity is equal, but runtime identity is not. Therefore the cells cannot be composed into one independently auditable Combined 003 environment under the stated compatibility rules. No replacement seeds or new games were used.

## Exact incompatibility

Changed semantic/runtime sources between the baseline evidence repository and the R4-C evidence repository:

| Path | Baseline source identity | Current post-support identity |
|---|---|---|
| `src/tmnt_design_studio/card_interpreter07.py` | `7e067bd3d5e08e76af8ef3a6ad7345ce894ef960` | `e7f842524478b756eda75ae75dddd2334ce67cf6` |
| `src/tmnt_design_studio/engine07.py` | `117e69bb467fed4c1885e95cbb867aaec10f6f93` | `70b78fdc62d4d40b79ddd1892c8ac8345030c6a0` |
| `src/tmnt_design_studio/pilot07.py` | pre-support runtime | post-support utility-cast priority |
| `src/tmnt_design_studio/smoke01.py` | pre-support frozen-input contract | post-support frozen-input contract |

The baseline artifact repository SHA is `0017d9d3b65d57474789ef24471deb615a9b1e54`; R4-C evidence repository SHA is `8b8a3b353d4aac9f00704adf57383101d9c1e048`. The schedule hash is equal (`b5fd8ab57016b15662fca420d508c9aab3633ad14b7f7515d667492b0f8abf27`), but schedule equality does not establish semantic compatibility.

Next action: establish a post-support baseline matrix before attempting Combined 003 again. This PR does not run that matrix.
