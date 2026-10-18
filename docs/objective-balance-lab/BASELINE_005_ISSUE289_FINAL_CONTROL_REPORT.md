# Baseline 005 Final Control — Blocked

Control ID: `OBL-BASELINE-005-FINAL-CONTROL-001`  
Environment: `OBL-BASELINE-005`  
Semantic runtime: `69d09aa4e63bdbc05dc0d7c4ecc212b4739c088034d273548880838bcd5ab130`  
Schedule: `b5fd8ab57016b15662fca420d508c9aab3633ad14b7f7515d667492b0f8abf27`

## Decision

**BLOCKED by simulator defect.** The authorized control was stopped fail-closed before any game completed. No balance interpretation, deck revision, second calibration, merge, or promotion is authorized.

## Preflight

- Ten unchanged Baseline 005 deck lists authenticated against the preserved manifest; the manifest's CRLF canonical hashes match the current LF-formatted files after line-ending normalization.
- Original coverage ledger: 172 rows; final overlay: 0 critical, 0 important, 0 unbounded residuals.
- Runtime identity matched the final Issue #289 authority.
- Schedule: 45 cells × 100 games, 50 starts per side per cell; 4,500 expected games.

## Preserved failure

The first cell (`leonardo|raphael`) failed on scheduled reversed game block 2, seed `27530971794998924477319664755747869070209299252577545546345361737057440661833`, seats `raphael,leonardo`, first player Raphael. The runtime raised:

`ValueError: damage-to-self mana trigger has invalid event provenance`

The machine artifact is [BASELINE_005_ISSUE289_FINAL_CONTROL.json.gz](BASELINE_005_ISSUE289_FINAL_CONTROL.json.gz). It is `FAIL_CLOSED`, contains zero completed games, and preserves the exact failing schedule record. SHA-256: `1f2442ad5c3f716913c4ee9c5dad84137b75232b15664745e2b722d8bef7a352`.

This failure occurs in the generic retained-mana damage-trigger provenance validator, not in a deck-specific branch. Because the failure is material and occurs during the authorized control, the control is invalid for balance evidence. No retry was performed.

## Recommendation

**BLOCKED.** Repair and independently validate the generic damage-to-self mana event provenance, then request a new explicit calibration authorization. Preserve this incomplete artifact; do not overwrite or reinterpret it.

