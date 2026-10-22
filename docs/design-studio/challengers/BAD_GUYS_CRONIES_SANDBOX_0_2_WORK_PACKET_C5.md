# Work Packet C5 — Generic compound removal and token resolution

## Scope

C5 implements the complete Oracle shape used by *Mutant Chain Reaction* without
dispatching on its name or on a deck identity:

> Destroy up to one target artifact, enchantment, or creature with flying.
> Create a Mutagen token.

The pinned Scryfall snapshot is the authority for this text. The parser requires
the complete removal-and-token grammar and rejects appended or missing clauses.

## Rules behavior

- Casting exposes a deterministic no-target choice plus every currently legal
  artifact, enchantment, or flying-creature target.
- A selected target is revalidated at announcement. At resolution, an absent or
  illegal selected target is ignored without retargeting; the independent token
  instruction still resolves.
- When legal, removal occurs before token creation. The token is created through
  the existing generic token definition and entry-event machinery, with the spell
  as its provenance source and the spell controller as its controller.
- State-based actions and existing object-identity checks remain authoritative.
- No card-name or deck-name execution branches were added.

## Deterministic evidence

`tests/test_compound_removal_c5.py` contains five focused tests covering:

1. Complete-parser acceptance and incomplete-clause rejection.
2. Optional target removal, ordering, and token entry.
3. Declined removal with token creation preserved.
4. Invalid target rejection without payment or mutation.
5. Target departure before resolution without retargeting or loss of the token.

Focused C5 tests: **5 passed**. No gameplay simulations were run.

## Coverage disposition

Mutant Chain Reaction is now **SUPPORTED** for its complete represented effect.
The Mutagen artifact-token activation discount remains a separate unsupported
family. Tainted Treats, Cowabunga!, Paramecia Coloniex, and Menace/Rhino grants
remain open for later authorized packets.

## Runtime and validation

- Parent C4 runtime: `6b2f86bf1834aece9dc1b3bc3817451601fb5c88e8581f1c7f6ba2a1d50d63a0`
- C5 runtime: `5860e357c084973aac2eae3f4b5f27b9948caa866bad3bf3d5c48cc8d5db4cf8`.
- Full pytest, Ruff, formatting, structural validation, and CI are required
  before independent HQ acceptance.

No deck, Baseline 005 artifact, R9-B evidence, or historical evidence changed.

**Checkpoint recommendation:** READY for independent C5 acceptance.
**Gameplay testing:** BLOCKED.
