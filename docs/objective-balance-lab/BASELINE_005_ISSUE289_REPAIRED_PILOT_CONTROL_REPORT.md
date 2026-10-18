# Baseline 005 Attempt 3 — Blocked

Control ID: `OBL-BASELINE-005-REPAIRED-PILOT-CONTROL-001`  
Environment: `OBL-BASELINE-005`  
Semantic runtime: `dc80bc679e2c0d118f543d12ae4a95661033039058b1525f32e8d076dae8d308`  
Schedule: `b5fd8ab57016b15662fca420d508c9aab3633ad14b7f7515d667492b0f8abf27`

## Decision

**BLOCKED by a simulator/evidence invariant failure.** Preflight passed and the one authorized attempt completed 1,000 games across 10 cells. It then stopped fail-closed after two Raphael/Michelangelo games raised `ValueError: ETB Food search evidence does not reconstruct`. No retry, schedule change, deck change, balance interpretation, merge, or promotion was performed.

## Preflight

- All ten unchanged Baseline 005 deck hashes authenticated against the preserved manifest.
- The original 172-row ledger contains 172 rows; preserved readiness evidence records zero critical, important, blocker, and unbounded gaps.
- Runtime identity matched `dc80bc679e2c0d118f543d12ae4a95661033039058b1525f32e8d076dae8d308`.
- The unchanged schedule contains 45 cells × 100 games with 50/50 starting-player assignments.
- The two earlier fail-closed controls and the 100-game repair diagnostic were verified immutable and excluded.
- Provenance and animated-permanent P/T focused tests passed 40/40.

## Control result

The previously failing Raphael/Donatello cell completed 100/100. The next Raphael/Michelangelo cell exposed a repeated ETB Food-search reconstruction failure in both orientations:

| Pair | Orientation | Block | Seed | Error |
|---|---|---:|---|---|
| Raphael / Michelangelo | reversed | 3 | `70854356032484108629752045553328311296264080222857296236996711926358961833742` | `ValueError: ETB Food search evidence does not reconstruct` |
| Raphael / Michelangelo | canonical | 41 | `61283485696731598188099450771387457581219000296206197647983307541613500950207` | `ValueError: ETB Food search evidence does not reconstruct` |

The error originates in the generic Food-search evidence reconstruction validator (`food_search07.py`), not a Raphael/Michelangelo branch. Because it occurred in both orientations, it is a material simulator/evidence defect and invalidates the control.

The machine artifact is [BASELINE_005_ISSUE289_REPAIRED_PILOT_CONTROL.json.gz](BASELINE_005_ISSUE289_REPAIRED_PILOT_CONTROL.json.gz), status `FAIL_CLOSED`, SHA-256 `f42348030c56fa12bf5c8c380dd32cd5d8ba6baaefeaf61635a3befea8396eb8`. It contains all 1,000 completed games and both exact failing schedule records.

## Evidence separation

- **Simulator correctness:** blocked by ETB Food-search evidence reconstruction failure.
- **Pilot behavior:** only partial telemetry exists for 10 cells; no calibration-wide conclusion is valid.
- **Deck balance:** no conclusion is authorized.
- **Historical evidence:** both earlier controls and the 100-game repair diagnostic remain excluded and unmodified.

The partial matrix is diagnostic only. For example, Raphael/Donatello completed at 60–40, but the 35 unrun cells prevent any balance interpretation.

## Recommendation

**BLOCKED.** Diagnose the generic ETB Food-search evidence path and request a separate repair authorization before any replacement calibration attempt. Do not revise decks, merge, promote, or launch another control.
