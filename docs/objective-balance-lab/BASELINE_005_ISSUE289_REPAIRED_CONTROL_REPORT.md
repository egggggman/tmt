# Baseline 005 Repaired Control — Blocked

Control ID: `OBL-BASELINE-005-REPAIRED-CONTROL-001`  
Environment: `OBL-BASELINE-005`  
Semantic runtime: `a86708257c54495cb3d3a71c578b86f41931184542542bbe676dacb924b1d401`  
Schedule: `b5fd8ab57016b15662fca420d508c9aab3633ad14b7f7515d667492b0f8abf27`

## Decision

**BLOCKED by a simulator defect.** Preflight passed and the single authorized control began, but it stopped fail-closed after 900 completed games when two Raphael/Donatello games raised a `NoneType - int` error. No retry, schedule change, deck change, balance interpretation, merge, or promotion was performed.

## Preflight

- All ten unchanged Baseline 005 deck hashes authenticated against the preserved manifest; line-ending normalization was applied only for historical hash comparison.
- The original 172-row ledger contains 172 rows, with zero recorded critical, important, blocker, or unbounded gaps in the preserved readiness evidence.
- The complete repaired runtime matched `a86708257c54495cb3d3a71c578b86f41931184542542bbe676dacb924b1d401`.
- The unchanged schedule contains 45 cells × 100 games with 50/50 starting-player assignments.
- The prior fail-closed control and 100-game repair diagnostic were verified immutable and excluded from this matrix.

## Control result

Nine cells completed (900 games). The first nine completed cells were the Leonardo pairings; one replay hash was persisted for the completed replay-enabled cell. The next cell failed closed:

| Pair | Orientation | Blocks | Seeds | Error |
|---|---|---:|---|---|
| Raphael / Donatello | reversed | 17, 24 | `110127092095985089794094274391071537768831682836357719713359846607269436624903`; `14531251592110549889095900528423591910809154711277454234709141390939740757152` | `TypeError: unsupported operand type(s) for -: 'NoneType' and 'int'` |

The persisted machine artifact is [BASELINE_005_ISSUE289_REPAIRED_CONTROL.json.gz](BASELINE_005_ISSUE289_REPAIRED_CONTROL.json.gz), status `FAIL_CLOSED`, SHA-256 `45c4cdcd95708bb5974620b543fb50ee4dfb43b2a0d09c288e01ceb9dfeb15d7`. It contains the 900 completed games and both exact failing schedule records.

The completed partial matrix is diagnostic only. For example, Leonardo/Raphael was 30–70 and Leonardo/Donatello 39–61; these values must not be interpreted as ten-deck balance evidence because 36 cells did not run and the runtime failure is material.

## Evidence separation

- **Simulator correctness:** blocked by the unhandled `NoneType - int` failure in the Raphael/Donatello cell. The repaired provenance defect did not produce this error, but the new failure invalidates the control as a whole.
- **Pilot behavior:** only partial telemetry exists for nine cells; it cannot support a calibration-wide pilot assessment.
- **Deck balance:** no conclusion is authorized.
- **Historical repair evidence:** the prior failed control (`OBL-BASELINE-005-FINAL-CONTROL-001`, SHA-256 `1f2442ad5c3f716913c4ee9c5dad84137b75232b15664745e2b722d8bef7a352`) and its 100-game diagnostic are excluded from this control's results.

## Recommendation

**BLOCKED by simulator defect.** Preserve this incomplete artifact, diagnose the generic `NoneType - int` path, and request a separate authorization before any replacement calibration run. Do not revise decks, merge, promote, or infer balance from the partial matrix.
