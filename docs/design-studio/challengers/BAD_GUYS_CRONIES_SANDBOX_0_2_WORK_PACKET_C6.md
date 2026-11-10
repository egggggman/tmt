# Work Packet C6 — Generic conditional Food creation

## Scope

C6 implements the complete Oracle shape used by *Tainted Treats* without
dispatching on its name or on a deck identity:

> Destroy target artifact or creature. If its mana value was 4 or less, create
> a Food token.

The pinned Scryfall snapshot is the authority for this text. The interpreter
requires the complete target, threshold, and Food-token grammar and rejects
appended or incomplete clauses.

## Rules behavior

- Casting exposes every currently legal artifact or creature target.
- The target is revalidated at resolution; a departed or no-longer-legal target
  causes the spell to resolve with no effect and no Food.
- For a legal target, the target's last-known card mana value is captured before
  destruction. A value of four or less creates exactly one Food after removal;
  a value above four creates no Food.
- Food creation uses the existing generic token definition, entry events, source
  provenance, and spell-controller identity.
- No card-name or deck-name execution branches were added.

## Deterministic evidence

`tests/test_conditional_food_c6.py` contains seven focused tests covering:

1. Complete parser acceptance and incomplete-clause rejection.
2. Artifact and creature targets at the threshold.
3. Above-threshold removal without Food.
4. Target departure before resolution.
5. Invalid enchantment target rejection.
6. Exact token characteristics and event ordering.
7. Deterministic replay.

No gameplay simulations were run.

## Coverage disposition

Tainted Treats is now **SUPPORTED** for its complete represented effect. The
remaining unsupported families are Mutagen artifact-token activation discount,
Cowabunga! hidden-zone selection, Paramecia Coloniex recursion, and
Menace/Rhino grants.

## Runtime and validation

- Parent C5 runtime: `5860e357c084973aac2eae3f4b5f27b9948caa866bad3bf3d5c48cc8d5db4cf8`
- C6 runtime: `7bfaa315f3c54a184be1b49dddaad7b598211f91c0f66d47fd0aaafe8af2d3b8`
- Focused C6 tests: **7 passed**.
- Full pytest: **1,662 passed, 10 skipped**.
- Ruff, formatting, structural validation, and terminology checks: **passed**.
- GitHub CI is required before independent HQ acceptance.

No deck, Baseline 005 artifact, R9-B evidence, or historical evidence changed.

**Checkpoint recommendation:** READY for independent C6 acceptance.
**Gameplay testing:** BLOCKED.
