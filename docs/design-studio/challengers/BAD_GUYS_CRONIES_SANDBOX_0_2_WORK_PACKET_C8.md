# Bad Guys — Shredder's Cronies Sandbox 0.2 — Work Packet C8

Status: **READY for independent review; BLOCKED for gameplay testing and C9.**

This checkpoint adds only the generic Paramecia death/exile reflexive recursion
family. No deck list, Baseline 005 artifact, R9-B evidence, historical artifact,
or gameplay simulation was changed or run.

## Provenance

- Parent C7 head: `027ba065dec7f8d0581783f6e1e04d5af72f52b6`
- Accepted C7 semantic runtime: `197c2acd50c95d669d549f1fe99342740a48b7d7a7fe8ff814c21a449927209f`
- C8 semantic runtime: `832c37effb02af7351f7d29836c9eb793a008de29c8d77b2ae79431eb9445ad7`
- Candidate SHA-256: `cacc77648a4d1659b8ae640d95ac2672694e6951553980246e6d001e5152bfb4`
- Baseline 005 SHA-256: `aaa61d3a3d65f7c8ab74062cc8f41d220a46066b44c28e3c71921c570a6b66ed`
- Pinned snapshot SHA-256: `56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402`

## Oracle behavior implemented

The interpreter now recognizes the exact generic fragment:

> When this creature dies, you may exile it. When you do, put target creature
> card from your graveyard on top of your library.

The rules path uses the authoritative death event and last battlefield
incarnation. The optional exile is resolved from the dead object's graveyard
incarnation; only then is a reflexive trigger created, with a target selected
from the controller's current graveyard excluding the exiled object. The target
is rechecked at resolution and moved to the top of its owner's library as a new
incarnation. Source departure, owner/controller identity, target invalidation,
empty target sets, and forged choices fail closed. No permission or casting
shortcut is substituted for the printed top-of-library effect.

## Validation

- Dedicated Paramecia tests: **8 passed** (`tests/test_paramecia_death_reflexive_return.py`).
- Mill/Paramecia boundary and transaction tests: **69 passed**.
- Full regression: run in CI; no gameplay simulations authorized or run.
- Ruff format/check: passed locally for changed files.

The tests cover optional decline, exact exile and top-library movement,
controller/identity preservation, source departure, target invalidation, no legal
target, forged target rejection before mutation, exact Oracle grammar, and
deterministic existing mill/replay evidence.

## Remaining unsupported families

The remaining unsupported families are Mutagen artifact-token activation-cost
discount and Menace/Rhino-wide grants. C9 is not authorized by this checkpoint.

**Recommendation:** READY for independent C8 checkpoint acceptance; BLOCKED for
gameplay testing and further semantic packets pending HQ review.

