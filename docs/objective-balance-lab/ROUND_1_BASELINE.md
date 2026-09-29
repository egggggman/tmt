# Objective Balance Lab — Round 1 Baseline

This is an evidence-only experiment based on main `dd439b892e7d97ff65744419855fc581eff218a6`.
No existing prototype is replaced or promoted. The latest usable parent is the exact file listed below;
where no newer authorized revision exists, the preserved Prototype 0.1 remains the baseline.

Authoritative card snapshot: `cardcade/scryfall-tmt-pza-tmc-2026-08-13.json`, SHA-256
`56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402`.

| Deck | Usable parent | Path | Parent SHA-256 | Lands | Creatures | Noncreatures | Color identity |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| Leonardo | Prototype 0.1 (latest preserved baseline) | `decks/leonardo/PROTOTYPE_0.1.txt` | `d49d155858938d6fc64127c1678e591ee77abad3b7da8302880f16379476fb08` | 22 | 24 | 14 | W |
| Raphael | Prototype 0.3 (latest preserved build) | `decks/raphael/PROTOTYPE_0.3.txt` | `220ea90ccc579e09bef38ce972ba84f661c2382b92c7a4559667d24a5eec6f51` | 22 | 23 | 15 | R |
| Donatello | Prototype 0.3c (latest preserved build) | `decks/donatello/PROTOTYPE_0.3c.txt` | `b0d8a0dc42b267ac1a162096fe6e0336176f92db9a79a95f1c7dbd0d5c2d2cc6` | 23 | 26 | 11 | RU |
| Michelangelo | Prototype 0.1 (latest preserved baseline) | `decks/michelangelo/PROTOTYPE_0.1.txt` | `f5dd228b6e3636bd0de367b9d1a2bd836c0388bf37b00f0c0c047a932973ebf9` | 22 | 22 | 16 | GU |
| Splinter | Prototype 0.1 (latest preserved baseline) | `decks/splinter/PROTOTYPE_0.1.txt` | `74b6d7f4cab4bcda9eeb80ffc7a779529115c98c161345f13ac1251d85163b0a` | 22 | 24 | 14 | B |
| Shredder | Prototype 0.3 (latest preserved build) | `decks/shredder/PROTOTYPE_0.3.txt` | `818e9a847fcdf8521f53ab9b49c0f054ddd6f9bce95e9fd57c89cb6c94da2ed2` | 22 | 23 | 15 | B |
| Krang | Prototype 0.2 (latest preserved build) | `decks/krang/PROTOTYPE_0.2.txt` | `5a52bc59b5de1034721ba17d1c1d4f12c493ec70681c1a910c8230808e4e4f96` | 22 | 23 | 15 | U |
| Bebop & Rocksteady | Prototype 0.1 (latest preserved baseline) | `decks/bebop_rocksteady/PROTOTYPE_0.1.txt` | `3875706a76ffab14d2a82ba836da9e59bce49de2f990a348941490e78a61ef9d` | 24 | 24 | 12 | BG |
| April O’Neil | Prototype 0.1 (latest preserved baseline) | `decks/april_oneil/PROTOTYPE_0.1.txt` | `684c898760a39c5dfc584206ef4675c49d96cfe6bd419f03f86bd0b8358d09f4` | 22 | 22 | 16 | U |
| Casey Jones | Prototype 0.3 (latest preserved build) | `decks/casey_jones/PROTOTYPE_0.3.txt` | `f18d2dd6591520e495a0c723e1d15f5d3f4f6ce8a2693e4f93be0cd6660e838f` | 22 | 23 | 15 | R |

The historical release manifest still names earlier parents for four of these decks. It is not used to
silently downgrade the current main checkout. Every parent was independently revalidated against the
snapshot, copy limits, and exact 60-card requirement.

## Semantic readiness audit

| Deck | Classification | Evidence boundary |
| --- | --- | --- |
| Leonardo | SEMANTICALLY_READY | Leadership counters, combat, Sneak, and protection are represented. |
| Raphael | PARTIALLY_REPRESENTED | Combat pressure and Manhole Missile are represented; combat decisions remain Pilot-shaped. |
| Donatello | PARTIALLY_REPRESENTED | Artifact entry, Mouser, Ooze, and Does Machines are represented; conversion breadth is bounded. |
| Michelangelo | PARTIALLY_REPRESENTED | Food, Mutagen, counters, and combat tricks are represented with bounded choice fidelity. |
| Splinter | PARTIALLY_REPRESENTED | Removal, recursion/rebuild, and evasive threats are represented; timing choices are simplified. |
| Shredder | PARTIALLY_REPRESENTED | Sacrifice, deathtouch, removal, and pressure are represented; not every delayed effect is executable. |
| Krang | PARTIALLY_REPRESENTED | Artifact entry, Affinity, refill, and artifact pressure are represented; long-game sequencing is Pilot-shaped. |
| Bebop & Rocksteady | PARTIALLY_REPRESENTED | Food, Mutagen, sacrifice, and brute-force combat are represented; multi-choice sacrifice behavior is bounded. |
| April O’Neil | PARTIALLY_REPRESENTED | Information/card-advantage bodies and counterplay are represented; answer coverage remains a confidence caveat. |
| Casey Jones | PARTIALLY_REPRESENTED | Jury-Rig and Equipment are represented sufficiently for a bounded probe; future gear quality is not optimized. |

No new semantics are implemented by Round 1. Unsupported or simplified behavior is retained as a
confidence limitation in the result, not compensated for by deck changes.

## Simulation contract

The baseline uses 45 unordered pairings, 100 games per pairing, 50 canonical and 50 reversed seats,
for 4,500 games. The first 50 sealed blocks of Calibration Seed Table V2 supply the deterministic seed
schedule. Each candidate replaces only its own parent while the other nine decks remain baseline lists;
candidate runs therefore contain 9 × 100 = 900 games each, 9,000 total. Candidate-vs-candidate games
are not run. See `ROUND_1_EVIDENCE.json` and `tools/run_objective_balance_lab_round1.py`.
