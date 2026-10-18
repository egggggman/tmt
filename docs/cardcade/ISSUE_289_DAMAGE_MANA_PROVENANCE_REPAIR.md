# Issue #289 — Damage-to-self retained-mana provenance repair

## Decision

**READY for independent repair-checkpoint acceptance; BLOCKED for renewed Baseline 005 calibration authorization.**

The preserved `OBL-BASELINE-005-FINAL-CONTROL-001` artifact remains unchanged and fail-closed. No second 4,500-game control was run.

## Root cause

The original control stopped while resolving combat damage against a recipient whose combat object had already left the authoritative battlefield. Combat assignments are constructed before the damage step resolves, but stale combat state could still reach the assignment loop. The old code applied damage and constructed a `COMBAT_DAMAGE_TO_CREATURE` event for the departed object; retained-mana trigger provenance then correctly rejected the event.

The preserved block-2 schedule record used seed `27530971794998924477319664755747869070209299252577545546361737057440661833`. Running the complete Leonardo/Raphael 100-game cell before the repair reproduced the same exception class in reversed block 48. The event trace was:

- event `event-000093`, `COMBAT_DAMAGE_TO_CREATURE`, subjects attacker `object-000199` and recipient `object-000175`;
- recipient/source incarnation passed to the retained-mana validator: `object-000175`;
- recipient zone: `former`; battlefield authority: absent;
- amount: 4; event source: `object-000199`.

This was a stale combat-assignment defect, not a reason to weaken provenance validation.

## Repair

The generic combat damage loop now checks that the target remains authoritative on the battlefield immediately before applying damage and constructing the event. Departed targets are skipped, so no forged/invalid damage event or mana trigger is created. Existing source independence, trigger timing, retained-mana duration, controller identity, and mana expiry remain unchanged.

Malformed provenance continues to fail safely through the existing validator tests.

## Validation

- Focused combat/mana/provenance fixtures: **77 passed**.
- Full regression: **2,103 passed, 10 skipped**.
- Ruff format/check: **pass**.
- Exact recorded block-2 seed: **4/4 deterministic replays completed**, all won by Leonardo, zero runtime errors.
- Leonardo/Raphael 100-game diagnostic cell after repair: **100 completed, 0 errors**.
- Final semantic runtime: `a86708257c54495cb3d3a71c578b86f41931184542542bbe676dacb924b1d401`.
- Previous final runtime: `69d09aa4e63bdbc05dc0d7c4ecc212b4739c088034d273548880838bcd5ab130`.
- Promoted historical runtime: `d4466241f0ffeaca809cd6a05210ad53b9af1011a1d7f833de88657c1cf00924`.
- Ten Baseline 005 deck identities and the 172-row coverage ledger remain unchanged.
- Preserved control artifact SHA-256 remains `1f2442ad5c3f716913c4ee9c5dad84137b75232b15664745e2b722d8bef7a352`.

The 100-game cell is diagnostic evidence for the repair only, not balance evidence.

## HQ recommendation

**Repair checkpoint: READY.** The generic defect is repaired and independently validated.  
**Baseline 005 calibration: BLOCKED pending separate HQ authorization.** A fresh control must not begin until HQ reviews this runtime change and authorizes it explicitly.
