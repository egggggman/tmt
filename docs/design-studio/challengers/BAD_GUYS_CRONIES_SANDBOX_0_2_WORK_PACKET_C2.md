# Bad Guys — Shredder's Cronies Sandbox 0.2
## Work Packet C2: mandatory combat sacrifice-or-discard

**Checkpoint recommendation: READY for independent C2 acceptance.**  
**Gameplay testing: BLOCKED. C3 and later packets: NOT STARTED.**

### Scope and provenance

C2 is stacked on the accepted C1 checkpoint (`bb89a02e02bb6a0eefe6310ef4be2c73b536738f`) and uses the accepted C1 semantic runtime as its predecessor:

| Item | Value |
|---|---|
| Candidate SHA-256 | `cacc77648a4d1659b8ae640d95ac2672694e6951553980246e6d001e5152bfb4` |
| Baseline 005 SHA-256 | `aaa61d3a3d65f7c8ab74062cc8f41d220a46066b44c28e3c71921c570a6b66ed` |
| Pinned card snapshot | `56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402` |
| C1 semantic runtime | `960df6898bcfa765a572f6128391dba735d322f9ce579e2866dcc3d1874bca4b` |
| C2 semantic runtime | `c95426fe7baba7794884782e781df1deda0c8d162cf70df03f0a8da1528a6691` |

No deck list, Baseline 005 artifact, R9-B evidence, or historical simulation was modified. No gameplay simulation was run.

### Oracle behavior implemented

The interpreter recognizes the generic Oracle grammar:

> Whenever [this permanent] attack or block, sacrifice a permanent unless you discard a card.

At declaration, each qualifying attacking or blocking permanent creates an independent triggered ability. The trigger is placed on the normal stack and is resolved only after priority passes. At resolution, its controller is offered the currently legal hand cards and permanents. The controller may discard one card or sacrifice one permanent; if neither zone has a legal object, the trigger resolves with no action. A source may leave the battlefield after triggering without invalidating the independent ability. The trigger stores and revalidates its source incarnation, controller, Oracle fragment, event kind, and declaration subject identity. Sacrifice and discard use ordinary zone movement, object reincarnation, and state-based validation.

The implementation is generic and uses no card-name, deck-name, matchup, or candidate dispatch. The frozen Bebop & Rocksteady text is an acceptance fixture only.

### Deterministic tests

`tests/test_combat_obligation_c2.py` covers:

- Oracle recognition and unsupported-fragment closure;
- attack trigger with legal discard;
- attack trigger with legal sacrifice;
- block trigger and no-resource resolution after source departure;
- source departure before resolution and forged event rejection;
- illegal chooser object rejection;
- deterministic stack/priority resolution and zone accounting.

Focused command:

```text
uv run pytest -q tests/test_combat_obligation_c2.py tests/test_block_restriction_c1.py
```

Result: **10 passed**.

The full regression completed with **1,639 passed, 10 skipped**.

### Coverage disposition

The C2 row is now **SUPPORTED** in the coverage overlay. Remaining work is unchanged in scope and remains blocked pending HQ authorization, beginning with C3 variable-X Mutagen token creation. Menace/Rhino grants, kicker/removal, Mutant Chain Reaction, conditional Food, hidden-zone selection, and recursion remain unsupported. No claim is made that passing C2 tests authorizes gameplay testing.

### Reproducible validation

```text
uv run pytest -q tests/test_combat_obligation_c2.py tests/test_block_restriction_c1.py
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
git diff --check
```

**Recommendation:** READY for independent review of C2; BLOCKED for gameplay testing and C3 until HQ accepts this checkpoint.
