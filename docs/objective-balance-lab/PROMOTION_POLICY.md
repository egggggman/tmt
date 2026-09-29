# Objective Balance Lab — Promotion Policy

## Governing principle

Experiments are cheap. Promotion is expensive.

Experimental candidates may be created frequently. Official baseline deck builds change only after isolated candidate evidence, candidate selection, combined-environment validation, and an explicit promotion decision. A locally improved candidate must never automatically overwrite the current baseline.

## State model

- `BASELINE` — official deck build in the current environment.
- `EXPERIMENTAL` — candidate exists but has not completed isolated evidence.
- `PROMISING` — isolated evidence is useful or directionally favorable; not selected for combined validation.
- `ACCEPTED_FOR_COMBINED_MATRIX` — eligible for selection into a provisional combined environment.
- `REJECTED` — evidence argues against further promotion in its current form; evidence is retained.
- `INCONCLUSIVE` — evidence did not distinguish the hypothesis; candidate is retained.
- `COMBINED_VALIDATED` — selected candidate passed the combined ten-deck matrix gate.
- `PROMOTED` — explicit authorization changed the official environment.
- `SUPERSEDED` — a later authorized state replaces this experimental or promoted state.

## Required flow

`BASELINE → EXPERIMENTAL → isolated evidence → ACCEPTED_FOR_COMBINED_MATRIX → combined 10-deck matrix → COMBINED_VALIDATED → explicit promotion → PROMOTED`

A candidate may move to `REJECTED` or `INCONCLUSIVE` at any gate. `PROMISING` is not an authorization state.

## Promotion thresholds

Win rate is never sufficient by itself. Combined promotion must consider:

- environment Mean Matchup Balance Error;
- worst matchup and matchup extremity;
- counts above 60/40 and 70/30;
- aggregate deck spread;
- first-player effect;
- runtime cleanliness and deterministic reproducibility;
- semantic confidence;
- strategic identity preservation or strengthening.

A new combined environment should normally improve the environment globally or provide a clearly justified tradeoff. A candidate must not be promoted merely because its own win rate moved closer to 50%.

## Identity protection

Promotion must preserve or strengthen the declared identity:

| Deck | Protected identity |
|---|---|
| Leonardo | coordinated board / disciplined leadership |
| Raphael | confrontation / aggressive pressure |
| Donatello | artifacts / inventions / technical synergy |
| Michelangelo | energetic / unconventional play |
| Splinter | patient / disciplined value-control |
| Shredder | ruthless interaction / villain pressure |
| Krang | technology / artifact engine |
| Bebop & Rocksteady | brute-force aggression |
| April O'Neil | resourceful / adaptive play |
| Casey Jones | improvised weapons / scrappy aggression |

A numerically improved candidate with diluted identity must be flagged and must not automatically promote.

## Current gate

The active next gate is **SELECT COMBINED-MATRIX CANDIDATES**. This governance change does not select candidates, create a combined environment, run simulations, or promote any deck.
