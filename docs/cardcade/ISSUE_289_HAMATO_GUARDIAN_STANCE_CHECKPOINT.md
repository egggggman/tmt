# Issue #289 — Hamato Guardian Stance checkpoint

This draft checkpoint continues PR #348 without changing any Baseline 005 deck
list or historical simulation artifact. The exact frozen clause closed here is
the generic instant effect on two Leonardo copies:

> Target creature gets +1/+3 and gains flying until end of turn. Scry 1.

The interpreter now recognizes the complete Oracle shape generically. The
engine announces and pays the normal mana cost, validates a legal creature
target, applies the temporary +1/+3 and flying effects, resolves an
authoritative Scry 1 choice, and cleans up at end of turn. Target departure
fizzles the spell atomically; source departure does not undo a resolved spell.

## Evidence

- Final semantic runtime: `939c0d0c3fc8a9bbbc80a6b6afa04b1b3b310c904797476d6b4c1d2e2653c5de`
- Previous PR #348 runtime: `deeba684652abf2f0de958c97969bc3f6a5731a055d104f39ae789cf1e063a71`
- Historical PR #347 runtime: `b4690f9f5609d1b9ad2a99a2ad80469d6a9b86a8e7d621bd92e88ea7545087fe`
- Frozen ledger identities: 172 unchanged
- Coverage: 0 critical, 1 important, 0 identified blockers, 1 unbounded residual
- Focused semantic tests: 3 passed
- Frozen deterministic diagnostics: 6 games / 6 exact replays; 28 natural casts and 4 resolutions
- Full calibration control: not run or authorized

The remaining unbounded row is Michelangelo Improviser’s optional combat-damage
hand deployment. It remains a separate readiness risk; no balance conclusion is
drawn from the diagnostic sample.

## Gate decisions

- Checkpoint acceptance: **READY** pending independent review and CI.
- Baseline 005 calibration readiness: **BLOCKED**. The final unbounded effect is
  not yet complete or credibly bounded.

The machine-readable overlay, readiness assessment, and replay evidence are in
the adjacent JSON files. No merge, deck revision, calibration control, or
promotion is authorized by this checkpoint.
