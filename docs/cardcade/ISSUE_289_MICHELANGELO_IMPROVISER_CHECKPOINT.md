# Issue #289 — Final Michelangelo Improviser checkpoint

This checkpoint continues PR #349 and closes the final important Oracle gap in
the frozen Baseline 005 environment. The exact two-copy Michelangelo clause is:

> Whenever Michelangelo deals combat damage to a player, you may put a creature card and/or a land card from your hand onto the battlefield.

The implementation is generic: qualifying positive combat damage creates an
authenticated independent trigger; resolution gives the controller a private,
deterministic choice of neither card, creature only, land only, or one of each.
Selected cards move directly from hand to the battlefield under their owner’s
control, without being cast or played. Creature entry triggers, state-based
actions, source departure, and replay provenance are preserved.

## Evidence

- Final semantic runtime: `69d09aa4e63bdbc05dc0d7c4ecc212b4739c088034d273548880838bcd5ab130`
- Previous PR #349 runtime: `939c0d0c3fc8a9bbbc80a6b6afa04b1b3b310c904797476d6b4c1d2e2653c5de`
- Historical PR #348 runtime: `deeba684652abf2f0de958c97969bc3f6a5731a055d104f39ae789cf1e063a71`
- Frozen ledger identities: 172 unchanged
- Coverage: 0 critical, 0 important, 0 unbounded effects
- Focused tests: 32 passed across the final hand-entry and prior semantic suites
- Frozen diagnostics: 6 games / 6 exact replays; 3 damage opportunities, 3 triggers, 3 choices
- Natural diagnostic entries: 0 creature, 0 land; fixture evidence covers all four legal choice shapes
- Full calibration control: not run or authorized

## Readiness decision

- Checkpoint acceptance: **READY** pending independent review and CI.
- Baseline 005 calibration readiness: **READY FOR HQ AUTHORIZATION**. The simulator
  has no remaining unsupported or unbounded ledger rows, but HQ must separately
  authorize the unchanged 4,500-game control.

No deck list, historical simulation, baseline promotion, or calibration control
was changed or launched by this checkpoint.
