# Baseline 001 Semantic Runtime Refresh

Evidence identity: `OBL-BASELINE-001-RUNTIME-REFRESH-001`. The official environment and deck bytes are unchanged; only the simulation runtime evidence was refreshed.

## Runtime identity

- Original baseline runtime: `d64a0755647ba2d57b2f97f5c9d32396e28eef4d2f8cbde35f387f30b77ea084` (commit `0017d9d3b65d57474789ef24471deb615a9b1e54`).
- R4-C runtime: `78bcce5b5f635f11c67247df91f90fef2bf0dbf948973c5c1ac38419f28b0e25` (commit `8b8a3b353d4aac9f00704adf57383101d9c1e048`).
- Current refresh runtime: `78bcce5b5f635f11c67247df91f90fef2bf0dbf948973c5c1ac38419f28b0e25` (commit `4da1fb9a0d746d3078ce498a777a719fbc3d964b`).
- R4-C compatibility: **REUSE_ELIGIBLE_FOR_COMBINED_003**. Its nine cells are semantically compatible with the refreshed runtime and may be reused by a future composition.

## Completion and integrity

The refresh contains 4,500/4,500 games, 45 matchup cells, 50 canonical and 50 reversed games per matchup, zero runtime errors, and schedule identity ``b5fd8ab57016b15662fca420d508c9aab3633ad14b7f7515d667492b0f8abf27``. The original evidence remains at `ROUND_1_EVIDENCE.json` and its recorded SHA-256 is preserved in the machine-readable report.

## Global comparison

| Metric | Original | Refreshed | Delta |
|---|---:|---:|---:|
| Mean matchup balance error | 0.209556 | 0.192444 | -0.017112 |
| Median deviation | 0.19 | 0.17 | -0.02 |
| 60/40 count | 36 | 35 | -1 |
| 70/30 count | 21 | 18 | -3 |
| WR spread | 0.511111 | 0.484445 | -0.026666 |
| WR stddev | 0.173611 | 0.161618 | -0.011993 |
| Mean first-player result rate | 0.503778 | 0.504 | 0.000222 |
| Mean ending turn | 19.4442 | 19.5829 | 0.1387 |
| Median ending turn | 18.0 | 18.0 | 0.0 |

## Per-deck change

| Deck | Original WR | Refreshed WR | WR delta | Original turn | Refreshed turn |
|---|---:|---:|---:|---:|---:|
| Leonardo | 35.44% | 36.22% | +0.78% | 22.61 | 22.8233 |
| Raphael | 76.78% | 73.44% | -3.33% | 17.2544 | 17.5856 |
| Donatello | 41.00% | 40.89% | -0.11% | 19.7967 | 19.6111 |
| Michelangelo | 54.11% | 52.00% | -2.11% | 19.3633 | 19.4178 |
| Splinter | 62.78% | 62.33% | -0.44% | 19.1278 | 19.2011 |
| Shredder | 73.00% | 73.89% | +0.89% | 18.4611 | 18.43 |
| Krang | 35.11% | 34.56% | -0.56% | 19.7422 | 19.9967 |
| Bebop & Rocksteady | 32.67% | 40.11% | +7.44% | 18.4311 | 18.3567 |
| April O'Neil | 25.67% | 25.44% | -0.22% | 20.5344 | 20.5989 |
| Casey Jones | 63.44% | 61.11% | -2.33% | 19.1211 | 19.8078 |

## Utility impact

The refreshed evidence records draw, legal-opportunity, selection, cast, resolution, activation, equip, and effect-use counters for artifact cards. The original evidence predates this telemetry, so zero/absent old counters are not treated as proof of zero use. Matchup-level attribution is observational: a changed cell is utility-associated only when the refreshed cell contains utility events for one of its decks.

Changed matchup cells: **32**; changed cells with observed utility activity: **32**.

- `april_oneil` vs `bebop_rocksteady`: april_oneil: Fugitive Droid, Buzz Bots, Bespoke Bō, Utrom Scientists, Sewer-veillance Cam, bebop_rocksteady: Ice Cream Kitty.
- `april_oneil` vs `casey_jones`: april_oneil: Fugitive Droid, Utrom Scientists, Buzz Bots, Bespoke Bō, Sewer-veillance Cam, casey_jones: Ravenous Robots, Spicy Oatmeal Pizza, Mouser Foundry, Rock Soldiers, Hard-Won Jitte, Improvised Arsenal.
- `april_oneil` vs `donatello`: april_oneil: Buzz Bots, Bespoke Bō, Fugitive Droid, Sewer-veillance Cam, Utrom Scientists, donatello: Buzz Bots, Fugitive Droid, Utrom Scientists, Mouser Mark III.
- `april_oneil` vs `leonardo`: april_oneil: Utrom Scientists, Sewer-veillance Cam, Buzz Bots, Fugitive Droid, Bespoke Bō, leonardo: Quintessential Katana.
- `april_oneil` vs `raphael`: april_oneil: Bespoke Bō, Sewer-veillance Cam, Buzz Bots, Fugitive Droid, Utrom Scientists, raphael: Skateboard.
- `bebop_rocksteady` vs `casey_jones`: casey_jones: Spicy Oatmeal Pizza, Improvised Arsenal, Ravenous Robots, Mouser Foundry, Rock Soldiers, Hard-Won Jitte, bebop_rocksteady: Ice Cream Kitty.
- `bebop_rocksteady` vs `donatello`: donatello: Utrom Scientists, Mouser Mark III, Fugitive Droid, Buzz Bots, bebop_rocksteady: Ice Cream Kitty.
- `bebop_rocksteady` vs `krang`: bebop_rocksteady: Ice Cream Kitty, krang: Krang, Master Mind, Sewer-veillance Cam, Buzz Bots, Bespoke Bō, Utrom Scientists, Fugitive Droid.
- `bebop_rocksteady` vs `leonardo`: bebop_rocksteady: Ice Cream Kitty, leonardo: Quintessential Katana.
- `bebop_rocksteady` vs `michelangelo`: bebop_rocksteady: Ice Cream Kitty, michelangelo: Guac & Marshmallow Pizza.
- `bebop_rocksteady` vs `raphael`: bebop_rocksteady: Ice Cream Kitty, raphael: Skateboard.
- `bebop_rocksteady` vs `shredder`: bebop_rocksteady: Ice Cream Kitty, shredder: Shredder's Armor, Anchovy & Banana Pizza.
- `bebop_rocksteady` vs `splinter`: bebop_rocksteady: Ice Cream Kitty.
- `casey_jones` vs `donatello`: casey_jones: Ravenous Robots, Spicy Oatmeal Pizza, Mouser Foundry, Hard-Won Jitte, Improvised Arsenal, Rock Soldiers, donatello: Mouser Mark III, Fugitive Droid, Buzz Bots, Utrom Scientists.
- `casey_jones` vs `krang`: casey_jones: Ravenous Robots, Mouser Foundry, Hard-Won Jitte, Spicy Oatmeal Pizza, Rock Soldiers, Improvised Arsenal, krang: Krang, Master Mind, Fugitive Droid, Bespoke Bō, Utrom Scientists, Buzz Bots, Sewer-veillance Cam.
- `casey_jones` vs `leonardo`: casey_jones: Mouser Foundry, Rock Soldiers, Hard-Won Jitte, Ravenous Robots, Improvised Arsenal, Spicy Oatmeal Pizza, leonardo: Quintessential Katana.
- `casey_jones` vs `michelangelo`: casey_jones: Hard-Won Jitte, Mouser Foundry, Spicy Oatmeal Pizza, Improvised Arsenal, Rock Soldiers, Ravenous Robots, michelangelo: Guac & Marshmallow Pizza.
- `casey_jones` vs `raphael`: casey_jones: Rock Soldiers, Improvised Arsenal, Hard-Won Jitte, Mouser Foundry, Spicy Oatmeal Pizza, Ravenous Robots, raphael: Skateboard.
- `casey_jones` vs `splinter`: casey_jones: Ravenous Robots, Rock Soldiers, Improvised Arsenal, Mouser Foundry, Hard-Won Jitte, Spicy Oatmeal Pizza.
- `donatello` vs `krang`: donatello: Mouser Mark III, Fugitive Droid, Buzz Bots, Utrom Scientists, krang: Sewer-veillance Cam, Fugitive Droid, Bespoke Bō, Utrom Scientists, Krang, Master Mind, Buzz Bots.
- `donatello` vs `leonardo`: donatello: Mouser Mark III, Buzz Bots, Fugitive Droid, Utrom Scientists, leonardo: Quintessential Katana.
- `donatello` vs `michelangelo`: donatello: Fugitive Droid, Mouser Mark III, Buzz Bots, Utrom Scientists, michelangelo: Guac & Marshmallow Pizza.
- `donatello` vs `raphael`: donatello: Mouser Mark III, Utrom Scientists, Buzz Bots, Fugitive Droid, raphael: Skateboard.
- `donatello` vs `shredder`: donatello: Mouser Mark III, Fugitive Droid, Utrom Scientists, Buzz Bots, shredder: Shredder's Armor, Anchovy & Banana Pizza.
- `krang` vs `leonardo`: krang: Utrom Scientists, Sewer-veillance Cam, Buzz Bots, Fugitive Droid, Bespoke Bō, Krang, Master Mind, leonardo: Quintessential Katana.
- `krang` vs `raphael`: krang: Fugitive Droid, Utrom Scientists, Krang, Master Mind, Sewer-veillance Cam, Buzz Bots, Bespoke Bō, raphael: Skateboard.
- `leonardo` vs `michelangelo`: michelangelo: Guac & Marshmallow Pizza, leonardo: Quintessential Katana.
- `leonardo` vs `raphael`: leonardo: Quintessential Katana, raphael: Skateboard.
- `leonardo` vs `splinter`: leonardo: Quintessential Katana.
- `michelangelo` vs `raphael`: michelangelo: Guac & Marshmallow Pizza, raphael: Skateboard.
- `raphael` vs `shredder`: raphael: Skateboard, shredder: Shredder's Armor, Anchovy & Banana Pizza.
- `raphael` vs `splinter`: raphael: Skateboard.
