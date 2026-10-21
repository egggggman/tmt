# Bad Guys 0.2 — structural and mana curve validation (2026-10-21)

Status: STATIC VALIDATION COMPLETE; independent Cardcade semantic validation PENDING. Not simulation-ready and no tests launched.

## Exact list and counts
Source candidate: BAD_GUYS_CRONIES_SANDBOX_0_2_CANDIDATE.md on this branch. Baseline 005 unchanged.

**Correction to the candidate's earlier prose:** 28 creatures, 10 noncreature nonland spells, and 22 lands = 60. Its prior 26/12 role breakdown was an arithmetic error; the decklist itself remains unchanged.

## Verified mana-value curve (published TMT card data)

| Mana value | Copies |
|---|---:|
| 1 | 3 |
| 2 | 12 |
| 3 | 12 |
| 4 | 5 |
| 5 | 2 |
| 6 | 4 |
| Total nonlands | 38 |

Weighted MV total = 117; mean MV of nonlands = 117/38 = **3.079**. Variable-X Mutagen Man has printed MV 2 outside the stack. Land mana value zero; 10 Swamp + 10 Forest + 2 Illegitimate Business = 22 lands.

## Card-level mana value and copies

| Card | Copies | MV |
|---|---:|---:|
| Mutagen Man, Living Ooze | 2 | 2 |
| Frog Butler | 2 | 2 |
| Bebop & Rocksteady | 4 | 3 |
| Foot Elite | 4 | 3 |
| Ice Cream Kitty | 3 | 2 |
| Foot Mystic | 3 | 4 |
| Paramecia Coloniex | 2 | 2 |
| Bebop, Warthog Warrior | 2 | 5 |
| Rocksteady, Crash Courser | 4 | 6 |
| Cowabunga! | 3 | 1 |
| Stomped by the Foot | 3 | 2 |
| Tainted Treats | 1 | 3 |
| Mutant Chain Reaction | 3 | 3 |
| Primordial Pachyderm | 2 | 4 |
| Illegitimate Business | 2 | land |
| Swamp | 10 | land |
| Forest | 10 | land |

## Legality and mana assessment
All named nonbasic cards appear in the main TMT set listing, not TMC-only Commander product. Foot Elite (TMT 146) and Foot Mystic (TMT 63) explicitly list Standard as legal; other listed TMT names require machine-readable current Scryfall bulk confirmation before **independent** legality certification. Four-copy maximum holds for every nonbasic name. Foot Elite costs {2}{W/B} and is castable with black; Foot Mystic costs {3}{B}. Illegitimate Business taps for black or green and enters tapped. Basic land sources: 10 B, 10 G; plus two tapped B/G sources = 12 each, before Frog Butler mana production. 22 lands is a hypothesis to test, not proven sufficient.

## Engine semantic gate — NOT PASSED
Foot Elite: attack trigger, selecting **another** creature, +1/+0, indestructible, duration end of turn. Foot Mystic: conditional ETB (intervening-if) only if a permanent left under your control **before the trigger event**; token generation. Confirm both via deterministic tests and engine coverage report. Also verify existing Bebop & Rocksteady attack/block sacrifice-or-discard, cycling, Mutagen token, Stomped kicker, targeting and pilot selection. A GitHub text search is not evidence of absence or implementation.

## Source and preservation
Published set data: https://www.mtgdatabase.com/en/archive/1030-Teenage-Mutant-Ninja-Turtles
Foot Elite: https://mtg.wtf/card/tmt/146/Foot-Elite
Foot Mystic: https://mtg.wtf/card/tmt/63/Foot-Mystic
Frozen Baseline 005: docs/objective-balance-lab/baselines/BEBOP_ROCKSTEADY_OBL_BASELINE_005.txt

No simulator run, baseline revision, or HQ test authorization. **Gate remains BLOCKED** pending independent current Scryfall legality and Cardcade semantic preflight. Design Studio recommends a small bounded smoke test only after those checks pass.
