# Round 8 gate — Bebop & Rocksteady environment-collapse diagnostic

**Disposition: RETURN_TO_DESIGN_STUDIO_DIAGNOSTIC_ONLY.** No games were run, no deck was redesigned, and Baseline 004 was not changed. The 6.44% result is a valid measurement of the current simulator and fixed pilot, but it is **not credible evidence by itself that the unchanged physical deck became intrinsically weak**.

## Source identity and comparison

The merged `OBL-BASELINE-004` manifest (Git blob `cc17b1760410d7a8547626bb9dbd4a0cd534207f`) names Combined 006 (Git blob `67adbd9fcd0e39d3a77847570df80ae7c317c330`) as its source, retains B&R from `BEBOP_ROCKSTEADY_OBL_R2_B.txt`, and records its SHA-256 as `6d9fb051c62f16b49a6ffc9045efb40d26007e2ffbcdac1e0524e1722cd4f509`. That hash matches both the old Round 2 candidate and the unchanged Baseline 003 controls. All four observations below use the same sealed 45-cell schedule; each B&R row has 900 games, 100 per opponent and balanced starts.

| Evidence | B&R wins / 900 | WR | B&R deck | Runtime / opponent qualification |
|---|---:|---:|---|---|
| Round 2 isolated R2-B | 345 | 38.33% | Exact R2-B | Historical runtime and Round 2 opponents |
| Baseline 003 Aura control | 339 | 37.67% | Exact R2-B | Unchanged Baseline 003; Aura runtime `ccfa75ed…b0ec` |
| Baseline 003 semantic control | 61 | 6.78% | Exact R2-B | **Same ten Baseline 003 lists and paired schedule**; Mutagen/landcycling runtime `f40c4888…3afa1` |
| Combined 006 → Baseline 004 | 58 | **6.44%** | Exact R2-B | Same runtime; only the Krang R7-A cell differs from preceding control |

The strongest comparison is **Aura control → semantic control**: no deck list or schedule changed. The B&R result fell **339 → 61 wins (−30.89 percentage points)**. Across its nine paired cells, 310/900 individual outcomes changed; 294 previous B&R wins became losses and 16 previous losses became wins. The subsequent Krang substitution changed 13 outcomes in that one cell and B&R fell just **61 → 58 wins**. R7-A is not the source of the collapse.

## Matchup loss signatures

| Opponent | R2-B | Aura control | New semantic control | Combined 006 |
|---|---:|---:|---:|---:|
| Leonardo | 42% | 46% | 1% | 1% |
| Raphael | 21% | 24% | 2% | 2% |
| Donatello | 52% | 53% | 14% | 14% |
| Michelangelo | 39% | 39% | 13% | 13% |
| Splinter | 25% | 25% | 3% | 3% |
| Shredder | 23% | 23% | 2% | 2% |
| Krang | 49% | 46% | 14% | 11% |
| April O'Neil | 69% | 51% | 10% | 10% |
| Casey Jones | 25% | 32% | 2% | 2% |

The collapse occurs against **all nine unchanged Baseline 003 opponents** in the semantic control, including Michelangelo and Splinter, rather than tracking only the later Krang substitution. The Round 2 comparison also reflects earlier opposing lists; its close agreement with the Aura control supports the breakpoint but is not itself a runtime-only experiment.

## Board development, casting, and game length

| Recorded measure | Aura control | New semantic control | Combined 006 |
|---|---:|---:|---:|
| First creature by turn 4 | 470/900 | 204/900 | 204/900 |
| No creature resolved in game | 70/900 | 119/900 | 122/900 |
| Mean first creature turn, if one resolved | 5.81 | 6.60 | 6.57 |
| Mean B&R creature presence by turns 3 / 5 / 7 | 0.340 / 1.098 / 1.523 | 0.156 / 0.707 / 1.376 | 0.156 / 0.704 / 1.377 |
| B&R spells cast | 2,735 | 1,882 | 1,862 |
| B&R games with zero spells cast | 70 | 119 | 122 |
| Games ending by turn 15 | 246 | 328 | 328 |
| B&R wins among games ending by turn 15 | 26 | 3 | 3 |
| Mean / median ending turn | 18.52 / 18 | 19.42 / 17 | 19.41 / 17 |

The new runtime produces far less early board presence and fewer casts. It also has more early endings, while a long tail raises the mean ending turn. First-player B&R wins fall **181/450 → 46/450** in the runtime-only control transition; second-player wins fall **158/450 → 15/450**. This is not explained by a starting-seat imbalance.

## The newly executable action and the fixed pilot

The new interpreter accepts generic basic-landcycling from hand. The B&R list has four **Rocksteady, Crash Courser** (`Forestcycling {2}`) and two **Bebop, Warthog Warrior** (`Swampcycling {2}`). The engine adds those legal hand activations before battlefield activations. The fixed `AcceptancePilot` takes the first activation at its `activate` stage, **before** its `creature` stage. Thus a two-mana cycling option is selected whenever offered even when the creature itself would be valuable to retain; the cost discards that creature and taps mana before the pilot can consider a creature cast on the turn. This is a general engine/pilot interaction, not code special-cased for B&R.

| Key-card event across 900 B&R games | Aura control | New semantic control | Combined 006 |
|---|---:|---:|---:|
| Rocksteady casts | 511 | **0** | **0** |
| Bebop, Warthog Warrior casts | 359 | **0** | **0** |
| Rocksteady landcycling activations | Not recorded / not supported | **1,132** | **1,140** |
| Bebop landcycling activations | Not recorded / not supported | **511** | **509** |
| Any B&R cycling in game | Not recorded / not supported | **755/900** | **756/900** |
| Cycling costs paid / shuffles | Not recorded / not supported | 1,643 / 1,643 | 1,649 / 1,649 |
| Basic lands found | Not recorded / not supported | 1,634 | 1,640 |
| B&R Mutagen counters placed | Not recorded | **595** | **589** |

In the new control, 504/1,643 cycling activations occur on turns 3–4. The searches generally deliver the promised basic land (1,634/1,643), but this is a resource exchange: two mana and a large creature are spent for that land. The preserved records do not show later hand composition or unused mana, so they cannot measure whether the land was needed. The pilot's action order and the disappearance of **all 870 former casts** of these two creatures establish the operational mechanism.

Paired outcomes add a strong association, with a selection caveat. In the 755 new-runtime games where B&R cycled, **292 of 330** old-runtime B&R wins became losses; in 145 games without B&R cycling, **2 of 9** old wins became losses and five losses became wins. Cycling availability is tied to hand and mana state, so these are **not randomized causal estimates**. They do show that 292/294 lost prior wins occur in games with the newly enabled cycling action. The record supports a major simulator-policy effect; it does not justify assigning exactly 292 losses to cycling alone.

Mutagen token activations also became supported and are actually delivered: B&R creates 689 Mutagen tokens and places 595 counters in the new control. These effects could help its board when a target exists; the preserved evidence cannot separately estimate their net impact. The old Aura record did not preserve activation-event telemetry, so an empty historical activation list must **not** be interpreted as zero use of every other activated ability. Opposing activation events now visible include multiple abilities, but this is partly new instrumentation; the source semantic change specifically enabled generic Mutagen and landcycling. The B&R collapse is broadly distributed across opponents, and the same-list, same-seed comparison plus B&R's own discarded payoff creatures provide the more direct explanation.

## Removal, attacks, damage, and resource limits

The retained `signature_casts` show opposing **Make Your Move** casts at 60 → 50 and **Fugitive Droid** casts at 432 → 485 across B&R's 900 games (Aura → new control). This does **not** establish how often a B&R creature was targeted or removed. B&R's own removal/noncreature spells, including **Stomped by the Foot** and **Mutant Chain Reaction**, have zero recorded casts in both controls under this fixed pilot. Even before the collapse, **Bebop & Rocksteady** and **Mutagen Man, Living Ooze** themselves have zero recorded casts. That older nonexecution is a real limitation of what this simulator/pilot tests, not new evidence of deck deterioration.

These OBL game records retain wins, ending turns, first-creature proxies, selected battlefield presence, casts, and new-runtime activation transactions. They do **not** retain attack declarations, damage/life progression, resolved removal targets, turn-by-turn hand contents, authoritative land utilization, or unused mana. The historical `interaction_casts` field counts **distinct cast card names**, not actual removal events; it is excluded from this diagnosis. Attack rate and damage trajectory cannot be quantified from these preserved records. New games are unnecessary to answer the identified breakpoint and mechanism, so none were run.

## Interpretation for 🧪 Design Studio

The **30.89-point runtime-only collapse** is primarily a change in what the simulator allows the fixed pilot to do with an unchanged six-card cycling package, compounded by that pilot's rigid activation-before-creature ordering. It is **not a clean estimate of genuine R2-B deck strength**. The old ~38% measurement was also limited: several nominal payoffs and noncreature cards never executed under the same pilot. The 6.44% Combined 006 result accurately describes this runtime/pilot environment, while its diagnostic use for card design is blocked by the newly exposed cycling-choice behavior. No candidate, baseline, or promotion decision is made here.

Read-only reproduction: `python tools/diagnose_bebop_round8.py --output docs/objective-balance-lab/ROUND_8_BEBOP_COLLAPSE_DIAGNOSTIC.json`. The [machine evidence](ROUND_8_BEBOP_COLLAPSE_DIAGNOSTIC.json) retains source hashes, all nine matchup rates, paired outcome counts, timing histograms, casting, cycling and Mutagen event counts, and explicit telemetry limits.
