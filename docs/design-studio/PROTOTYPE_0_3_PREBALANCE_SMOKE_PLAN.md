# Prototype 0.3 Pre-Balance Smoke Plan

Status: **Preparation only; do not run in the decklist PR.**

This plan is authorized by `PROTOTYPE_0_3_PREBALANCE_AUTHORIZATION.md` for one small deterministic
diagnostic after the four Prototype 0.3 candidate decklists merge. It is not Calibration V1 and must
not be used for iterative simulator tuning.

## Matrix

Run each unordered matchup below for **40 games**, with 20 games per starting-player orientation.
Use fixed deterministic seeds `3000` through `3039` for each matchup, with the orientation assigned
by seed parity: even seeds start with the alphabetically earlier listed deck, odd seeds start with
the other deck. Use the exact merged candidate decklists for all four named decks.

| Matchup | Games | Starting-player split | Primary diagnostic |
| --- | ---: | ---: | --- |
| Shredder / Raphael | 40 | 20 / 20 | pressure versus pressure; recoverable counterplay |
| Shredder / Casey Jones | 40 | 20 / 20 | removal versus Equipment payoff density |
| Shredder / Donatello | 40 | 20 / 20 | sacrifice pressure versus restored artifact reliability |
| Raphael / Casey Jones | 40 | 20 / 20 | early pressure versus gear setup |
| Raphael / Donatello | 40 | 20 / 20 | aggression versus proactive restoration |
| Casey Jones / Donatello | 40 | 20 / 20 | Equipment reduction versus artifact recovery |

Total: **240 games**, 120 per starting orientation across the six authorized-deck pairings.

## Optional controls

If the deterministic harness supports the existing frozen decks without broadening the revision
scope, add 20 games per orientation against one control named by each Candidate Packet: Raphael or
Shredder for Donatello, Leonardo or Michelangelo for Casey, and Raphael or Casey for Shredder and
Raphael. These controls are diagnostic only and must not cause a deck change automatically.

## Measurements and stop rules

Record completion, malformed results, legality/runtime failures, terminal outcomes, starting player,
and a descriptive win/loss count. Inspect only for catastrophic movement:

- a revised deck cannot complete games or violates deck/runtime integrity;
- a former 75% deck remains obviously extreme or collapses against its named control;
- Donatello shows no executable artifact-engine path at all;
- a revised deck becomes a new extreme or a matchup becomes nonfunctional.

Do not interpret 40-game percentages as calibrated estimates, pool them with Calibration V1, or tune
again to the observed smoke result. Any unexpected result is recorded for Design Studio review.

## Human-play gate

After smoke validation, begin balanced human play from the four-deck provisional environment. Human
play evaluates fun, identity, recoverability, interesting decisions, repeated frustration, Equipment
friction, and whether any deck remains obviously too strong or weak. Human evidence is the primary
refinement input.
