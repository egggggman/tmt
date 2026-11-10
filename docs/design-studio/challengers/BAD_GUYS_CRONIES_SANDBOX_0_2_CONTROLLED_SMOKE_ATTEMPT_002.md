# Bad Guys — Controlled Gameplay Smoke Attempt 002

**Status: SMOKE PASSED — READY FOR HQ CALIBRATION REVIEW**  
**Calibration:** BLOCKED pending HQ review  
**Gameplay scope:** 180 games maximum, 20 per matchup; no calibration inference

## Authenticated inputs

- Runtime: `c087f84bab4916b516ec6745f5a8e9f2a2d33f9117856bf959da4eb9a7be8e54`
- Candidate SHA-256: `cacc77648a4d1659b8ae640d95ac2672694e6951553980246e6d001e5152bfb4`
- Baseline 005 Bebop & Rocksteady SHA-256: `aaa61d3a3d65f7c8ab74062cc8f41d220a46066b44c28e3c71921c570a6b66ed`
- Snapshot SHA-256: `56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402`
- Overlay: `OBL-BASELINE-005-PROVENANCE-OVERLAY-001`
- Provenance preflight deck count: 10
- Primary games completed: 180; failures: 0; draws: 0
- Deterministic replay samples: 18; all matched: True

## Matchup results

| Opponent | Games | Candidate wins | Opponent wins | Candidate-first wins | Opponent-first wins | Mean turns |
|---|---:|---:|---:|---:|---:|---:|
| april_oneil | 20 | 15 | 5 | 6 | 9 | 20.35 |
| casey_jones | 20 | 8 | 12 | 5 | 3 | 18.5 |
| donatello | 20 | 13 | 7 | 6 | 7 | 19.25 |
| krang | 20 | 12 | 8 | 6 | 6 | 19.4 |
| leonardo | 20 | 10 | 10 | 3 | 7 | 23.2 |
| michelangelo | 20 | 9 | 11 | 6 | 3 | 15.85 |
| raphael | 20 | 6 | 14 | 3 | 3 | 18 |
| shredder | 20 | 8 | 12 | 5 | 3 | 17.2 |
| splinter | 20 | 8 | 12 | 4 | 4 | 18.9 |

## Mechanics and integrity

Representative replays observed 100 event families, including combat damage, blockers, spell casting/resolution, activated abilities, tokens, sacrifice/zone changes, Food search, landcycling, recursion, and trigger resolution. See the machine artifact for exact event-type counts and replay digests.

No illegal action, invalid payment, runtime exception, unexplained terminal outcome, identity mismatch, or replay mismatch occurred. No game was retried, and no prior probe or Attempt 001 result was included.

This is mechanical smoke evidence only. It does not authorize deck revision, candidate promotion, calibration, or balance interpretation.
