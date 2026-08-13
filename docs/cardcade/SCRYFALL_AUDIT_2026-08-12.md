# Cardcade Scryfall Data Audit — 2026-08-12 EDT

## Result

All ten frozen `roster-0.2` decks resolve completely against current Scryfall TMT/PZA/TMC data:
**600 of 600 slots**, representing 102 distinct deck names. Current Scryfall Oracle IDs, mana
costs, type lines, Oracle text, and keyword sets agree with every corresponding committed Engine
0.6 model record. No deck or engine change is warranted by this comparison.

The previously reported 472-print figure is correct **for the newly retrieved current snapshot**,
but repository evidence does not establish that such a snapshot was previously committed or
retained. The repository's actual Cardcade runtime source is the smaller 103-record
`cardcade/card-model-0.6.json` export.

## Reproducible current snapshot

The audit script queried Scryfall's official set endpoint and paginated print-unique card search for
each set. The generated manifest records every requested URL, set UUID, retrieval timestamp,
canonicalization procedure, and checksum.

| Set | Scryfall set UUID | Prints | Unique Oracle objects |
| --- | --- | ---: | ---: |
| TMT | `03990f52-1d8a-4ce8-828a-c9bf633f0de6` | 320 | 195 |
| PZA | `59aecbd0-4c5b-4dd7-a0f2-ba16b4403c56` | 20 | 20 |
| TMC | `178a07bb-cd54-4443-8b62-675e0c52cfe3` | 132 | 117 |
| **Union** | — | **472** | **332** |

- Retrieved: `2026-08-13T03:54:23.705578Z` (2026-08-12 EDT)
- Canonical snapshot SHA-256:
  `042c556b3e67af83f69d4e1f96bb7bb026aedccb7f0aa792a53ace225d4de8df`
- Canonicalization: normalized audited fields, UTF-8 JSON, sorted keys, compact separators, records
  sorted by set/collector number/Scryfall ID
- Reproduce:
  `python scripts/audit_cardcade_scryfall.py --output docs/cardcade/SCRYFALL_AUDIT_2026-08-12.json`

This checksum covers the normalized audit snapshot, not a claim that the complete raw Scryfall
responses are committed.

## What is actually committed or generated

### Cardcade runtime model

`cardcade/card-model-0.6.json` is committed and contains 103 records. Its SHA-256 is
`8631a98759ffd762931f5305b6c2bca72fdcd26827adbf5cdb5a764edb131b80`. The file declares only:

> tmnt-design-studio.db cards/keywords; frozen for Engine 0.6

It was introduced by commit `ed3ec1e5c01a238c4028c3c61c8a9e1972631ca4`, authored
`2026-08-10T17:03:52-04:00`. The export script selects card facts by names found across committed
Cardcade rosters. Neither the source database nor a raw TMT/PZA/TMC Scryfall snapshot is committed.
The model has no retrieval timestamp, Scryfall import ID, source checksum, download URI, or bulk-data
`updated_at`, so its exact upstream retrieval date and source version are **not recoverable from
repository evidence**. The commit date is not treated as a retrieval date.

The committed model contains Oracle ID, mana cost/value, type line, Oracle text, and keywords. It
does not contain card-face records, legalities, power, or toughness. Engine 0.7 separately supplies
hard-coded Acceptance Match creature P/T for 16 named cards; that is not a complete Scryfall card
snapshot and does not make P/T available for all frozen decks.

### Other Scryfall-shaped data

The only tracked file named as Scryfall data is
`tests/fixtures/scryfall-default-cards.json`: a synthetic four-print/three-Oracle-object test
fixture, SHA-256 `f82fc8e300d5e20232abe6d57040d82a0c154d025eb3f2797ed7fd11e8d018cd`.
It is not TMT/PZA/TMC source data.

The general import pipeline can download Scryfall `default_cards`, validate it, and persist facts,
faces, keywords, printings, and legalities in SQLite with import provenance. No populated SQLite
database is tracked in this checkout, so that capability does not establish the provenance of the
committed Engine 0.6 export.

## Frozen-deck validation

| Deck | Frozen list | Slots | Names | Unresolved |
| --- | --- | ---: | ---: | ---: |
| Leonardo | Prototype 0.1 | 60 | 15 | 0 |
| Raphael | Prototype 0.1 | 60 | 14 | 0 |
| Donatello | Prototype 0.2 | 60 | 14 | 0 |
| Michelangelo | Prototype 0.1 | 60 | 14 | 0 |
| Splinter | Prototype 0.1 | 60 | 13 | 0 |
| April O'Neil | Prototype 0.1 | 60 | 14 | 0 |
| Casey Jones | Prototype 0.1 | 60 | 13 | 0 |
| Shredder | Prototype 0.1 | 60 | 13 | 0 |
| Krang | Prototype 0.2 | 60 | 14 | 0 |
| Bebop & Rocksteady | Prototype 0.1 | 60 | 16 | 0 |
| **Total** | — | **600** | **102 unique** | **0** |

Every representative deck printing resolves to TMT. Comparison against current Scryfall found zero
differences in Oracle ID, mana cost, type line, Oracle text, or keyword membership. Keyword ordering
is treated as nonsemantic.

Current Scryfall supplies Oracle text, keyword arrays, type lines, mana-cost fields, and legality
maps for all 600 slots. All 231 creature slots have power and toughness. No frozen deck contains a
multiface card; across the full 472-print audit snapshot, the one multiface printing has two faces
and both faces contain name, type line, mana cost, and Oracle text.

All 600 slots are currently Standard-, Commander-, Brawl-, Pioneer-, Modern-, Legacy-, Vintage-,
and Timeless-legal. The manifest retains exact slot counts for every legality format returned by
Scryfall, including formats with mixed values.

## Discrepancies and boundary

- **No current fact discrepancy** was found for fields present in the committed model.
- **Provenance discrepancy:** the committed model cannot prove which Scryfall retrieval produced
  it or when that retrieval occurred.
- **Schema gap:** current Scryfall has the requested face, legality, and P/T facts, but the committed
  Cardcade model omits them. Cardcade therefore cannot consume those fields generally from its
  frozen runtime model today.
- **No historical 472-print artifact:** the current audit confirms 472 prints now; it does not
  retroactively validate an earlier claimed snapshot.

No decks, engine behavior, historical models, runs, or evidence were modified. This audit stops at
data/provenance validation.
