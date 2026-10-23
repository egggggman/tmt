# Bad Guys — Shredder's Cronies Sandbox 0.2

## C9 semantic checkpoint

This checkpoint implements the generic menace and Rhino-wide keyword-grant
family authorized by HQ. Gameplay simulations remain blocked.

### Provenance

- Parent C8 head: 'c96b13fcc4e32179e3283dbf92d378885064d5fd'
- Parent C8 runtime: '832c37effb02af7351f7d29836c9eb793a008de29c8d77b2ae79431eb9445ad7'
- C9 semantic runtime: 'c483d71cbc63b47d94736f018dd052c57f6a11a2443a74e98bc930aee5754bff'
- Candidate SHA-256: 'cacc77648a4d1659b8ae640d95ac2672694e6951553980246e6d001e5152bfb4'
- Baseline 005 SHA-256: 'aaa61d3a3d65f7c8ab74062cc8f41d220a46066b44c28e3c71921c570a6b66ed'
- Pinned Scryfall snapshot: '56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402'

The candidate, Baseline 005, R9-B, and historical evidence were not modified.

## Oracle behavior implemented

The pinned Oracle clause is:

> Menace (This creature can't be blocked except by two or more creatures.)  
> Rhinos you control have menace.

The interpreter now recognizes the generic controller-scoped grammar
'<quality>s you control have <keyword>', with Menace as the executable
keyword in this bounded packet. The combat engine evaluates the grant live
from authoritative battlefield state: controller, subtype, source presence,
and overlapping grants are recalculated at attack/block legality time. Existing
generic maximum-one-blocker restrictions remain active, so contradictory
constraints reject illegal declarations rather than being bypassed.

No card-name, deck-name, or opponent-specific branch was added.

## Validation

- Dedicated C9 tests: 7
- Focused C9 + existing menace tests: 16 passed
- Full regression: **1,683 passed, 10 skipped**
- Ruff check and formatting: passed
- Gameplay simulations: not run

Fixtures cover exact generic grammar, friendly/opposing controller scope,
dynamic entry and source departure, overlapping grants, menace's two-blocker
requirement, conflict with an at-most-one-blocker restriction, and
deterministic replay.

## Coverage disposition

The C9 coverage audit corrects the historical C8 JSON omission by listing
Paramecia Coloniex death/exile recursion in 'supported'. It also closes the
Menace/Rhino-wide grant family. The only remaining unsupported family in this
audit is Mutagen's artifact-token activation-cost discount, reserved for C10
and not implemented here.

Historical C8 audit files and evidence remain recoverable in their predecessor
commit; this C9 audit records the new authority and runtime.

## Recommendation

**READY for independent C9 checkpoint acceptance.** The next gameplay gate
remains **BLOCKED** pending HQ review; no simulations or C10 work were begun.
