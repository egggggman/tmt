# Bad Guys — Shredder's Cronies Sandbox 0.2 — Work Packet C7

Status: **READY for independent review; BLOCKED for gameplay testing and C8.**

## Scope and provenance

This checkpoint implements only the authorized generic hidden-zone selection family
for *Cowabunga!*. No deck list, Baseline 005 artifact, R9-B evidence, historical
artifact, or gameplay simulation was changed or run.

- Parent PR #363 head: `c0ead0a8c24bcd5b322c8910ac0576e0b9edb33f`
- Pre-C7 semantic runtime: `7bfaa315f3c54a184be1b49dddaad7b598211f91c0f66d47fd0aaafe8af2d3b8`
- C7 semantic runtime: `197c2acd50c95d669d549f1fe99342740a48b7d7a7fe8ff814c21a449927209f`
- Candidate SHA-256: `cacc77648a4d1659b8ae640d95ac2672694e6951553980246e6d001e5152bfb4`
- Baseline 005 SHA-256: `aaa61d3a3d65f7c8ab74062cc8f41d220a46066b44c28e3c71921c570a6b66ed`
- Pinned snapshot SHA-256: `56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402`

## Oracle grammar implemented

The interpreter recognizes the complete generic shape:

> Look at the top N cards of your library. You may reveal a [qualified] card
> from among them and put it into your hand. Put the rest on the bottom of your
> library in a random order.

The supported qualification vocabulary is derived from the parsed Oracle clause
(`Mutant`, `Ninja`, `Turtle`, and `land` for the accepted fixture). The engine
offers only eligible inspected object IDs plus the legal decline choice. The
chooser receives an immutable top-first projection and never sees lower-library
cards.

Resolution preserves ownership and object identity, creates the normal hand-zone
incarnation for the selected card, records reveal and zone events, and randomizes
only the unselected inspected cards using the deterministic RNG domain tied to the
spell object. Libraries shorter than N and empty libraries resolve legally; no
eligible card leaves all cards in the library. Forged choices, non-authoritative
library objects, and mutated authoritative state fail closed.

## Deterministic validation

Dedicated C7 tests: **10 passed** (`tests/test_top_library_selection_c7.py`). They
cover exact grammar, 4+ cards, short and empty libraries, eligible and ineligible
cards, decline, hidden private views, identity preservation, random-bottom
ordering, invalid choices, and exact repeated snapshots.

The complete regression passed: **1,672 passed, 10 skipped**. Ruff formatting and
lint checks, structural validation, terminology checks, and the coverage audit
also passed in CI run **39844249949** (job **120053195281**). No gameplay
simulations were authorized or run.

## Remaining unsupported families

The refreshed audit leaves three unsupported families: Mutagen artifact-token
activation discount, Paramecia Coloniex recursion, and Menace/Rhino grants. C8 is
not authorized by this checkpoint.

**Recommendation:** READY for independent C7 checkpoint acceptance; BLOCKED for
gameplay testing and further semantic packets pending HQ review.
