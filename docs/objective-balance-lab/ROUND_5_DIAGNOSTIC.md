# Objective Balance Lab Round 5 — diagnostic

This is a **design-only** review. No matchup was simulated. The exact parent is [OBL-BASELINE-002](baselines/OBL_BASELINE_002_MANIFEST.json), whose reference metrics were independently corrected in the [metric audit](BASELINE_002_METRIC_AUDIT.md). The current comparison evidence is the runtime-compatible [Combined 003 matrix](COMBINED_003_RUNTIME_COMPATIBLE_EVIDENCE.json), because Baseline 002 is byte-identical to that promoted environment. Its semantic runtime is `78bcce5b5f635f11c67247df91f90fef2bf0dbf948973c5c1ac38419f28b0e25`. The old Round 1–3 numbers are historical context, **not** paired Baseline 002 measurements.

Baseline 002 has 45 complete 100-game pairings, 18.9556% mean matchup balance error, 34 matchups over 60/40, 18 over 70/30, and 49.2222% aggregate deck WR spread. The three targets are Shredder 75.00%, April O'Neil 25.7778%, and Krang 35.1111%.

## Matchups driving the outliers

The table gives the target deck's credited win rate against each other Baseline 002 deck. Each cell has 100 games.

| Opponent | Shredder | April | Krang |
|---|---:|---:|---:|
| Leonardo | 78% | 49% | 68% |
| Raphael | 58% | 9% | 13% |
| Donatello | 84% | 36% | 46% |
| Michelangelo | 71% | 21% | 32% |
| Splinter | 67% | 11% | 20% |
| Shredder | — | 9% | 11% |
| Krang | 89% | 48% | — |
| Bebop & Rocksteady | 77% | 31% | 51% |
| April O'Neil | 91% | — | 52% |
| Casey Jones | 60% | 18% | 23% |

Shredder beats every opponent; April is below 50% in every pairing, with 9% against both Raphael and Shredder. Krang is close to even with April, Bebop & Rocksteady, and Donatello but loses sharply to Raphael, Shredder, Splinter, and Casey. The 9/91 April–Raphael pairing is the current environment's worst cell.

## Development and usage

The first-play measures are the **means among games where the event was observed**, not unconditional game averages. A missing event is unavailable, not turn zero. Battlefield means are conditional on an actually recorded turn snapshot; the composed evidence's stored turn-3/5/7 summary used integer lookups for string JSON keys and is not used here. The following counts/means were recomputed from the 900 target-deck game records in the Combined 003 evidence.

| Deck | First creature observed / mean turn | First meaningful blocker observed / mean turn | First interaction observed / mean turn | Battlefield creatures, turns 3 / 5 / 7 (observations; mean) | Interaction casts |
|---|---:|---:|---:|---|---:|
| Shredder | 897 / 3.04 | 897 / 3.04 | 0 / unavailable | 735; 1.30 / 796; 2.08 / 836; 2.68 | 3,533 |
| April | 872 / 7.04 | 899 / 3.21 | 680 / 5.86 | 611; 1.34 / 814; 2.15 / 870; 2.86 | 3,863 |
| Krang | 809 / 9.34 | 897 / 3.76 | 713 / 5.88 | 608; 1.17 / 756; 1.92 / 810; 2.65 | 4,114 |

The first-creature event is the runner's first-play proxy; it must not be interpreted as the first permanent, because artifact creatures and board snapshots can precede it. Shredder's cast evidence is distributed: Dream Beavers 1,061, Squirrelanoids 981, Super Shredder 772, Foot Mystic 628, Shark Shredder 594, Oroku Saki 563, and Shredder Unrelenting 386 signature casts. This supports a distributed-efficiency diagnosis, not a single-bomb diagnosis. April has substantial creature casts (Fugitive Droid 1,048; Buzz Bots 1,031; Crustacean Commando 1,014; Reporter 750; Utrom Scientists 739), but these do not yield a competitive board against the strongest decks. Krang casts Fugitive Droid 1,304, Buzz Bots 1,211, Utrom Scientists 1,039, Crustacean Commando 1,028, and Does Machines 560, while Krang Master Mind records only 118 casts. That supports testing conversion rather than more setup.

The current artifact-use audit shows Shredder's Armor drawn 831 / cast 0 and Anchovy & Banana Pizza drawn 446 / cast 0; April's Sewer-veillance Cam drawn 954 / cast 0 and Bespoke Bō drawn 456 / cast 0; Krang's Cam drawn 1,040 / cast 0 and Bespoke Bō drawn 514 / cast 0. These are current-runtime telemetry totals, not claims that a legal cast opportunity occurred. The Pilot selects creature casts and bounded draw/setup spells, but most other artifacts do not reach its selection path. No design below relies on their text becoming active. Artifact-creature telemetry is materially different: April's Utrom Scientists were drawn 702 / cast 662; Krang's Utrom Scientists drawn 1,023 / cast 926.

## Historical lever review and confidence limits

- Shredder R1/R2 substitutions were zero-observable or ineffective. R3-A removed two Squirrelanoids for Oroku Saki plus Shredder's Technique: 72.44%→72.22% but balance error worsened 0.44 pp. R3-B removed Armor for the same replacements: 72.44%→74.22%, +1.33 pp balance error. Repeating either package is not informative. [R2](ROUND_2_DELTA_RESULTS.md), [R3](ROUND_3_DELTA_RESULTS.md).
- April R1's extra Hacktivists helped isolated balance but weakened in Combined 001. R3-A's Reporter/Hacktivist value package improved isolated balance by 0.67 pp, yet the Combined 002 environment regressed. R3-B's more reactive Negate/Retro-Mutation package cut WR 26.56%→23.78% and worsened balance 2.78 pp. This round tests *board conversion from reactive slots*, not another value-density or counterspell package. [R1](ROUND_1_DELTA_RESULTS.md), [Combined 001](COMBINED_001_RESULTS.md), [R3](ROUND_3_DELTA_RESULTS.md), [Combined 002](COMBINED_002_RESULTS.md).
- Krang R2's extra Does Machines worsened balance; R2's Gadget Master gain reversed/mixed in Combined 001. R3's extra 8-mana Krang cut WR 38.33%→27.00%; the Omni-Cheese consistency variant did not solve Combined 002. Neither more setup nor a high-end card is a fresh test. [R2](ROUND_2_DELTA_RESULTS.md), [R3](ROUND_3_DELTA_RESULTS.md), [Combined 001](COMBINED_001_RESULTS.md), [Combined 002](COMBINED_002_RESULTS.md).
- The persistent [card-role dataset](CARD_ROLE_EVIDENCE.json) records these positive and negative observations. Drawn-game WR is not treated as card causality. The [Baseline 001 runtime refresh](BASELINE_001_RUNTIME_REFRESH.md) changed several matchups, so old-runtime deltas are not extrapolated into Baseline 002.

Current semantic limitations matter. `AcceptancePilot` prefers cheap legal creature casts; it does not reliably use ordinary utility artifacts, and some thematic triggered abilities (notably April Reporter's combat-damage draw) are not executable. The Round 5 proposal can test April's *body/tempo* change, not a Reporter card-advantage claim. Tunnel Rats' graveyard return is not assumed to fire; Shredder's test is about replacing active one-drops and a closer with its two-mana body. Detailed screening and the deliberately omitted April-B are in the [candidate plan](ROUND_5_CANDIDATE_PLAN.md).
