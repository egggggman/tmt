# Round 8 — B&R corrected-control loss signatures

**Diagnostic only.** Exact Baseline 004 B&R list, no new games, no candidate or promotion. This uses the merged 4,500-game cycling-pilot control; B&R appears in 900 games, 100 against each opponent with 50 starts on each side.

Runtime `24ce312cdac00d914606d1f4c111813826ca615768d631532e995faf1c8d57fa`; control `OBL-BASELINE-004-CYCLING-PILOT-REFRESH-001`; schedule `b5fd8ab57016b15662fca420d508c9aab3633ad14b7f7515d667492b0f8abf27`. All ten deck hashes match the immutable Baseline 004 manifest. Raw and derived evidence are hash-linked in the [machine diagnosis](ROUND_8_BEBOP_CORRECTED_CONTROL_DIAGNOSTIC.json).

## Nine matchups

| Opponent | Old → corrected B&R WR | B&R first creature ≤4 | Opponent first creature ≤4 | B&R casts | Cycler casts | Cycling activations | Mean end turn |
|---|---:|---:|---:|---:|---:|---:|---:|
| Raphael | 2% → 11% | 58/100 | 53/100 | 239 | 32 | 110 | 15.7 |
| Shredder | 2% → 13% | 45/100 | 77/100 | 201 | 23 | 121 | 16.3 |
| Splinter | 3% → 12% | 57/100 | 88/100 | 230 | 30 | 119 | 17.1 |
| Casey Jones | 2% → 16% | 47/100 | 64/100 | 221 | 30 | 115 | 16.9 |
| Donatello | 14% → 39% | 52/100 | 12/100 | 272 | 55 | 108 | 19.3 |
| Leonardo | 1% → 31% | 58/100 | 93/100 | 338 | 75 | 136 | 24.5 |
| Krang | 11% → 27% | 46/100 | 15/100 | 249 | 54 | 109 | 19.6 |
| Michelangelo | 13% → 25% | 54/100 | 76/100 | 217 | 34 | 132 | 16.1 |
| April O'Neil | 10% → 36% | 53/100 | 23/100 | 303 | 56 | 113 | 21.7 |

## What separates the groups

The relatively functional Donatello/Leonardo/Krang cells total **97/300 B&R wins (32.33%)**. Raphael/Shredder/Splinter total **36/300 (12.00%)**; Casey is **16/100**. These are descriptive groupings, not deck-change experiments.

B&R has a first creature by turn 4 in **156/300** functional games and **160/300** severe games. The opponent reaches that timing in **120/300** versus **218/300**. B&R's early creature timing alone does not explain the severe split. Leonardo reaches an early creature in 93/100 games yet B&R wins 31/100 there, so opposing first-creature timing is not a complete explanation either.

Severe games end sooner on average (**16.4** vs **21.1** turns). B&R records **85** Bebop/Rocksteady casts in the severe group versus **184** in the functional group, with **350** versus **353** cycling activations. Total B&R casts are **670** versus **859**. Shorter games reduce casting opportunities, so these counts identify a conversion gap without proving its cause.

B&R's turn-5 battlefield-presence proxy is **1.14** in functional cells and **1.17** in severe cells. Its early board is not simply absent in the severe group. The summaries do not say how much damage that board dealt or how it traded.

Across all 900 corrected games, the cast signatures still record zero casts of Bebop & Rocksteady, Mutagen Man, Living Ooze, Cowabunga!, Mutant Chain Reaction, Stomped by the Foot, and Illegitimate Business. This is an execution/measurement limit of the fixed-pilot simulation; the summaries do not establish why each card was absent.

Against Raphael, Shredder, Splinter, and Casey, the mean end turn is 15.7–17.1; B&R's corrected WR is 11–16%. Donatello, Leonardo, and Krang games last 19.3–24.5 turns on average and yield 27–39% B&R WR. The corrected pilot restored the choice to cast cycling creatures, while severe cells still show a poor measured conversion of early board presence into wins.

## Execution and telemetry boundary

The full per-opponent and win/nonwin splits include cast signatures, early creature timing, fixed-turn board presence, cycling activations, and ending-turn histograms. Opponent casts and named-card associations can be inspected there. These summaries do not contain attack declarations, damage/life trajectories, resolved removal targets, per-turn hands, or unused mana. They cannot establish a particular lethal sequence or credit a specific card as the cause of a loss. Recorded casts are also sensitive to ending turn.

## Design Studio handoff

**Diagnosis authorized; candidate design remains unauthorized.** The simulation reference for unchanged Baseline 004 is the corrected control. Design Studio should interpret the early timing and conversion gap, particularly Raphael/Shredder/Splinter and Casey, before choosing any card intervention. The original Combined 006 promotion record remains historical; no Baseline 005 is created.

[Corrected control](BASELINE_004_CYCLING_PILOT_CONTROL.json.gz) · [45-cell analysis](BASELINE_004_CYCLING_PILOT_ANALYSIS.json) · [machine diagnosis](ROUND_8_BEBOP_CORRECTED_CONTROL_DIAGNOSTIC.json).
