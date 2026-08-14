# Engine 0.7g Authoritative Card Data Foundation

## Boundary

This checkpoint changes Cardcade's Engine 0.7 card-fact source, not gameplay. It implements no
Draw, Discard, Selection, or other card Action. Decks, pilot behavior, engine semantics, historical
engines, models, prototypes, runs, and evidence remain unchanged.

The historical `cardcade/card-model-0.6.json` remains the immutable 103-record Engine 0.6 export.
Engine 0.7 now loads Acceptance Match facts through `CardDataCatalog` from a durable normalized
TMT/PZA/TMC Scryfall snapshot.

## Authoritative snapshot

- Retrieval: `2026-08-13T23:22:26.674927Z`
- Prints: **472**
- Unique Oracle objects: **332**
- TMT: 320 prints / 195 Oracle objects
- PZA: 20 prints / 20 Oracle objects
- TMC: 132 prints / 117 Oracle objects
- Snapshot SHA-256:
  `56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402`

The manifest records official Scryfall set UUIDs, every set/search source identifier, retrieval
timestamp, user agent, counts, canonicalization, and checksum. The builder retrieves the same
official endpoints used by the audit, restricts records to the audited normalized fact surface,
sorts keyword arrays because keyword membership is set-like, and writes deterministic UTF-8 JSON.
Two consecutive retrievals produced byte-identical snapshot hashes.

The foundation checksum differs from the earlier evidence-audit checksum `042c...`. The audit
serialized Scryfall's keyword-array order as returned; the durable builder sorts those set-like
arrays and was retrieved later. Counts and semantic facts remain equivalent. The evidence-only
audit script and its historical manifest are preserved unchanged at commit `70a4d09`.

Reproduce with:

`python scripts/build_cardcade_card_data.py --snapshot-output cardcade/scryfall-tmt-pza-tmc-2026-08-13.json --manifest-output cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json`

## Normalized interface

Each `CardData` record exposes Scryfall printing ID, Oracle ID, name, normalized card faces, Oracle
text, keywords, type line, mana cost/value, P/T, set and collector identity, and per-format
legalities.

Loading verifies the snapshot's raw SHA-256 and print count against the manifest. Name resolution
fails on a missing name or multiple Oracle identities rather than guessing a printing.

## Migration equivalence

The separate 16-card `ACCEPTANCE_CREATURE_STATS` table was removed. Engine 0.7 now derives those
P/T values from the authoritative interface. Regression tests preserve the removed values as
expectations and verify exact equality for all 16 cards.

Additional deterministic tests establish:

- all 103 historical Engine 0.6 records match authoritative Oracle ID, mana facts, type line,
  Oracle text, and keyword membership;
- the normalized snapshot has 472 prints and 332 Oracle objects and matches its checksum;
- card faces, printing identity, Oracle identity, characteristics, and legalities are exposed;
- all ten frozen decks resolve through the catalog, totaling **600/600 slots**.

Scryfall encodes mana values as JSON numbers. The normalized interface preserves that source value;
the Engine 0.7 adapter accepts only mathematically integral values and converts them losslessly to
the integer representation required by its mana-payment code. It rejects nonintegral values rather
than truncating them.

## Behavioral regression

Acceptance Match #001 seeds 7001–7005 were replayed after migration and compared with preserved
0.7f JSON outputs. Every output is byte-identical:

| Seed | Byte-identical | SHA-256 |
| ---: | :---: | --- |
| 7001 | yes | `ae54bd3066cc46fc57bf6a4f93f50a6bbf3e2eb823ac1d6f5a67f578241e9e1b` |
| 7002 | yes | `6382bfc8b5cc5273b0a648a74378e491bf61a20171239296d682ad869dc7d02f` |
| 7003 | yes | `c50b0f309a621c9f35f8e3b2c03c992b02fa1aec8259a5a253d95dbd50cada86` |
| 7004 | yes | `d09caef2768491bf55840da9bc740022ff55c8b4e2a9d69c812ea9cacd539fe8` |
| 7005 | yes | `0abe51491f10637b81b43cf5f45859c4ade55507fa899c2807fad080bf9a5b17` |

No gameplay difference was accepted or rationalized.
