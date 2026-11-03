# Bad Guys — Shredder's Cronies Sandbox 0.2

## C10 semantic checkpoint

This checkpoint implements generic artifact-token activated-ability cost
reduction for the Mutagen Oracle family. Gameplay simulations remain blocked.

### Provenance

- Parent C9 head: 'd81256391adeb0b0dcd7add3fc2712f58d40aa55'
- Parent C9 runtime: 'c483d71cbc63b47d94736f018dd052c57f6a11a2443a74e98bc930aee5754bff'
- C10 semantic runtime: 'c087f84bab4916b516ec6745f5a8e9f2a2d33f9117856bf959da4eb9a7be8e54'
- Candidate SHA-256: 'cacc77648a4d1659b8ae640d95ac2672694e6951553980246e6d001e5152bfb4'
- Baseline 005 SHA-256: 'aaa61d3a3d65f7c8ab74062cc8f41d220a46066b44c28e3c71921c570a6b66ed'
- Pinned Scryfall snapshot: '56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402'

The candidate, Baseline 005, R9-B, and historical evidence were not modified.

## Oracle behavior implemented

The pinned Mutagen Man clause is:

> Activated abilities of artifact tokens you control cost {1} less to activate.

The interpreter recognizes the generic grammar for controller-scoped
activated-ability reductions on qualifying tokens. During activation planning,
the engine evaluates current battlefield objects, controller, token status, and
artifact type; reductions stack by independent effects and floor the generic
portion of the cost at zero. Colored requirements remain payable, and the
reduction applies to activated-ability costs rather than spell-casting costs.
Source departure and controller changes are reflected immediately by the live
evaluation.

No card-name, deck-name, or opponent-specific branch was added. C3 variable-X
announcement and token quantity remain separate from C10.

## Validation

- Dedicated C10 tests: 7
- Focused C10 + existing Mutagen-token tests: 10 passed
- Full regression: **1,690 passed, 10 skipped**
- Ruff check and formatting: passed
- Gameplay simulations: not run

Fixtures cover no/one/multiple qualifying artifacts, exact payment boundaries,
insufficient resources, zero-cost floors, nonqualifying tokens, controller
changes, source departure, event cost telemetry, and deterministic replay.

## Coverage disposition

The refreshed coverage audit now lists the artifact-token activated-ability
reduction as supported. The remaining partial entry is the previously bounded
intrinsic keyword/ordinary land-entry family; no unsupported C10 family remains.

## Recommendation

**READY for independent C10 checkpoint acceptance.** This does not authorize
gameplay testing or calibration; those remain blocked pending HQ's complete
engine-readiness decision.
