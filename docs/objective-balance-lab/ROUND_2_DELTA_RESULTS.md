# Objective Balance Lab — Round 2 Delta Results

Round 2 reuses the immutable Round 1 baseline (4,500 games) and runs 20 isolated candidates for 900 games each (18,000 games). Negative Balance Δ is improvement.

## Family summary

| Deck | Candidate | Parent WR | R1 WR | R2 WR | Balance Δ | Worst matchup | Worst Δ | >60/40 parent→R2 | >70/30 parent→R2 | Identity | Verdict |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- | --- |
| Leonardo | A | 35.44% | 35.78% | 32.56% | +1.78 pp | Raphael 15.00% | -3.00 pp | 7→7 | 3→4 | IDENTITY_STRENGTHENED | REJECT_BALANCE_REGRESSION |
| Leonardo | B | 35.44% | 35.78% | 35.22% | +0.00 pp | Raphael 18.00% | +0.00 pp | 7→7 | 3→2 | IDENTITY_STRENGTHENED | PROMISING_NEEDS_VARIANT |
| Raphael | A | 76.78% | 78.22% | 78.89% | +2.11 pp | April O'Neil 96.00% | -1.00 pp | 8→8 | 5→5 | IDENTITY_STRENGTHENED | REJECT_BALANCE_REGRESSION |
| Raphael | B | 76.78% | 78.22% | 78.22% | +1.44 pp | April O'Neil 96.00% | -1.00 pp | 8→9 | 5→6 | IDENTITY_STRENGTHENED | REJECT_BALANCE_REGRESSION |
| Donatello | A | 41.00% | 42.33% | 40.44% | -0.78 pp | Shredder 16.00% | -7.00 pp | 7→7 | 5→4 | IDENTITY_STRENGTHENED | ACCEPT_FOR_COMBINED_MATRIX |
| Donatello | B | 41.00% | 42.33% | 40.22% | -0.11 pp | Shredder 16.00% | -7.00 pp | 7→7 | 5→4 | IDENTITY_STRENGTHENED | PROMISING_NEEDS_VARIANT |
| Michelangelo | A | 54.11% | 54.11% | 54.11% | -0.00 pp | April O'Neil 79.00% | +0.00 pp | 9→9 | 3→3 | IDENTITY_PRESERVED | INCONCLUSIVE |
| Michelangelo | B | 54.11% | 54.11% | 54.11% | -0.00 pp | April O'Neil 79.00% | +0.00 pp | 9→9 | 3→3 | IDENTITY_PRESERVED | INCONCLUSIVE |
| Splinter | A | 62.78% | 62.78% | 62.78% | +0.00 pp | April O'Neil 89.00% | +0.00 pp | 8→8 | 4→4 | IDENTITY_STRENGTHENED | INCONCLUSIVE |
| Splinter | B | 62.78% | 62.78% | 62.78% | +0.00 pp | April O'Neil 89.00% | +0.00 pp | 8→8 | 4→4 | IDENTITY_STRENGTHENED | INCONCLUSIVE |
| Shredder | A | 73.00% | 73.00% | 73.00% | +0.00 pp | April O'Neil 91.00% | +0.00 pp | 7→7 | 6→6 | IDENTITY_STRENGTHENED | REJECT_BALANCE_REGRESSION |
| Shredder | B | 73.00% | 73.00% | 73.00% | +0.00 pp | April O'Neil 91.00% | +0.00 pp | 7→7 | 6→6 | IDENTITY_PRESERVED | REJECT_BALANCE_REGRESSION |
| Krang | A | 35.11% | 39.89% | 31.33% | +2.67 pp | Raphael 5.00% | -2.00 pp | 6→6 | 4→5 | IDENTITY_STRENGTHENED | REJECT_BALANCE_REGRESSION |
| Krang | B | 35.11% | 39.89% | 39.00% | -0.11 pp | Raphael 8.00% | +1.00 pp | 6→8 | 4→4 | IDENTITY_STRENGTHENED | ACCEPT_FOR_COMBINED_MATRIX |
| Bebop & Rocksteady | A | 32.67% | 37.33% | 37.33% | -2.89 pp | Casey Jones 14.00% | -4.00 pp | 6→6 | 4→4 | IDENTITY_STRENGTHENED | ACCEPT_FOR_COMBINED_MATRIX |
| Bebop & Rocksteady | B | 32.67% | 37.33% | 38.33% | -3.44 pp | Raphael 21.00% | +9.00 pp | 6→6 | 4→4 | IDENTITY_STRENGTHENED | ACCEPT_FOR_COMBINED_MATRIX |
| April O'Neil | A | 25.67% | 28.11% | 26.11% | -0.44 pp | Raphael 8.00% | +5.00 pp | 7→6 | 5→5 | IDENTITY_STRENGTHENED | ACCEPT_FOR_COMBINED_MATRIX |
| April O'Neil | B | 25.67% | 28.11% | 25.67% | -0.00 pp | Raphael 3.00% | +0.00 pp | 7→7 | 5→5 | IDENTITY_STRENGTHENED | INCONCLUSIVE |
| Casey Jones | A | 63.44% | 59.78% | 61.11% | +0.11 pp | Bebop & Rocksteady 83.00% | +1.00 pp | 7→8 | 3→3 | IDENTITY_STRENGTHENED | ACCEPT_FOR_COMBINED_MATRIX |
| Casey Jones | B | 63.44% | 59.78% | 60.67% | -1.22 pp | April O'Neil 82.00% | -5.00 pp | 7→6 | 3→3 | IDENTITY_STRENGTHENED | ACCEPT_FOR_COMBINED_MATRIX |

## Per-matchup deltas versus original parent

| Deck | Candidate | Opponent deltas |
| --- | --- | --- |
| Leonardo | A | Raphael -3.00 pp; Donatello -2.00 pp; Michelangelo -5.00 pp; Splinter +2.00 pp; Shredder -2.00 pp; Krang -4.00 pp; Bebop & Rocksteady -5.00 pp; April O'Neil -2.00 pp; Casey Jones -5.00 pp |
| Leonardo | B | Raphael +0.00 pp; Donatello +2.00 pp; Michelangelo +0.00 pp; Splinter +1.00 pp; Shredder -4.00 pp; Krang +1.00 pp; Bebop & Rocksteady -1.00 pp; April O'Neil +0.00 pp; Casey Jones -1.00 pp |
| Raphael | A | Leonardo +4.00 pp; Donatello +4.00 pp; Michelangelo +2.00 pp; Splinter -1.00 pp; Shredder +3.00 pp; Krang -3.00 pp; Bebop & Rocksteady +3.00 pp; April O'Neil -1.00 pp; Casey Jones +8.00 pp |
| Raphael | B | Leonardo +2.00 pp; Donatello +2.00 pp; Michelangelo +4.00 pp; Splinter -3.00 pp; Shredder +4.00 pp; Krang -1.00 pp; Bebop & Rocksteady +2.00 pp; April O'Neil -1.00 pp; Casey Jones +4.00 pp |
| Donatello | A | Leonardo -6.00 pp; Raphael +6.00 pp; Michelangelo +10.00 pp; Splinter +0.00 pp; Shredder -7.00 pp; Krang -1.00 pp; Bebop & Rocksteady +0.00 pp; April O'Neil +1.00 pp; Casey Jones -8.00 pp |
| Donatello | B | Leonardo -5.00 pp; Raphael +4.00 pp; Michelangelo +11.00 pp; Splinter -1.00 pp; Shredder -7.00 pp; Krang -4.00 pp; Bebop & Rocksteady +0.00 pp; April O'Neil +5.00 pp; Casey Jones -10.00 pp |
| Michelangelo | A | Leonardo +0.00 pp; Raphael +0.00 pp; Donatello +0.00 pp; Splinter +0.00 pp; Shredder +0.00 pp; Krang +0.00 pp; Bebop & Rocksteady +0.00 pp; April O'Neil +0.00 pp; Casey Jones +0.00 pp |
| Michelangelo | B | Leonardo +0.00 pp; Raphael +0.00 pp; Donatello +0.00 pp; Splinter +0.00 pp; Shredder +0.00 pp; Krang +0.00 pp; Bebop & Rocksteady +0.00 pp; April O'Neil +0.00 pp; Casey Jones +0.00 pp |
| Splinter | A | Leonardo +0.00 pp; Raphael +0.00 pp; Donatello +0.00 pp; Michelangelo +0.00 pp; Shredder +0.00 pp; Krang +0.00 pp; Bebop & Rocksteady +0.00 pp; April O'Neil +0.00 pp; Casey Jones +0.00 pp |
| Splinter | B | Leonardo +0.00 pp; Raphael +0.00 pp; Donatello +0.00 pp; Michelangelo +0.00 pp; Shredder +0.00 pp; Krang +0.00 pp; Bebop & Rocksteady +0.00 pp; April O'Neil +0.00 pp; Casey Jones +0.00 pp |
| Shredder | A | Leonardo +0.00 pp; Raphael +0.00 pp; Donatello +0.00 pp; Michelangelo +0.00 pp; Splinter +0.00 pp; Krang +0.00 pp; Bebop & Rocksteady +0.00 pp; April O'Neil +0.00 pp; Casey Jones +0.00 pp |
| Shredder | B | Leonardo +0.00 pp; Raphael +0.00 pp; Donatello +0.00 pp; Michelangelo +0.00 pp; Splinter +0.00 pp; Krang +0.00 pp; Bebop & Rocksteady +0.00 pp; April O'Neil +0.00 pp; Casey Jones +0.00 pp |
| Krang | A | Leonardo +1.00 pp; Raphael -2.00 pp; Donatello -5.00 pp; Michelangelo -7.00 pp; Splinter -5.00 pp; Shredder -1.00 pp; Bebop & Rocksteady -4.00 pp; April O'Neil -7.00 pp; Casey Jones -4.00 pp |
| Krang | B | Leonardo +1.00 pp; Raphael +1.00 pp; Donatello +9.00 pp; Michelangelo +2.00 pp; Splinter +2.00 pp; Shredder +3.00 pp; Bebop & Rocksteady +3.00 pp; April O'Neil +9.00 pp; Casey Jones +5.00 pp |
| Bebop & Rocksteady | A | Leonardo +6.00 pp; Raphael +5.00 pp; Donatello +6.00 pp; Michelangelo +8.00 pp; Splinter +1.00 pp; Shredder +7.00 pp; Krang +9.00 pp; April O'Neil +4.00 pp; Casey Jones -4.00 pp |
| Bebop & Rocksteady | B | Leonardo +2.00 pp; Raphael +9.00 pp; Donatello +4.00 pp; Michelangelo +8.00 pp; Splinter +1.00 pp; Shredder +4.00 pp; Krang +8.00 pp; April O'Neil +8.00 pp; Casey Jones +7.00 pp |
| April O'Neil | A | Leonardo -9.00 pp; Raphael +5.00 pp; Donatello -2.00 pp; Michelangelo +0.00 pp; Splinter +8.00 pp; Shredder +4.00 pp; Krang -7.00 pp; Bebop & Rocksteady +7.00 pp; Casey Jones -2.00 pp |
| April O'Neil | B | Leonardo +0.00 pp; Raphael +0.00 pp; Donatello +0.00 pp; Michelangelo +0.00 pp; Splinter +0.00 pp; Shredder +0.00 pp; Krang +0.00 pp; Bebop & Rocksteady +0.00 pp; Casey Jones +0.00 pp |
| Casey Jones | A | Leonardo -2.00 pp; Raphael -6.00 pp; Donatello +1.00 pp; Michelangelo +1.00 pp; Splinter -5.00 pp; Shredder -5.00 pp; Krang -2.00 pp; Bebop & Rocksteady +1.00 pp; April O'Neil -4.00 pp |
| Casey Jones | B | Leonardo -1.00 pp; Raphael -7.00 pp; Donatello -8.00 pp; Michelangelo +3.00 pp; Splinter +0.00 pp; Shredder +0.00 pp; Krang +0.00 pp; Bebop & Rocksteady -7.00 pp; April O'Neil -5.00 pp |

## Round 2 synthesis

The ranking below uses balance error first, then matchup extremity and functional telemetry. It is an experimental ranking, not an automatic promotion decision.
- **Leonardo:** best current family member is **round1** (16.22% mean matchup error). Most informative failed candidate: **A**. Strongest card-role signal: the package-level result is directional only; no single-card causal claim is made. Unanswered question: whether a different card role can move the profile without diluting identity.
- **Raphael:** best current family member is **B** (28.22% mean matchup error). Most informative failed candidate: **A, B**. Strongest card-role signal: the package-level result is directional only; no single-card causal claim is made. Unanswered question: whether a different card role can move the profile without diluting identity.
- **Donatello:** best current family member is **A** (17.33% mean matchup error). Most informative failed candidate: **none**. Strongest card-role signal: Turtle Techie gave the clearer balance improvement; Gadget Master was nearly neutral. Unanswered question: whether artifact presence or payoff conversion is the durable Donatello bottleneck.
- **Michelangelo:** best current family member is **A** (18.33% mean matchup error). Most informative failed candidate: **none**. Strongest card-role signal: the package-level result is directional only; no single-card causal claim is made. Unanswered question: whether a different card role can move the profile without diluting identity.
- **Splinter:** best current family member is **round1** (21.67% mean matchup error). Most informative failed candidate: **none**. Strongest card-role signal: the package-level result is directional only; no single-card causal claim is made. Unanswered question: whether a different card role can move the profile without diluting identity.
- **Shredder:** best current family member is **round1** (24.56% mean matchup error). Most informative failed candidate: **A, B**. Strongest card-role signal: the package-level result is directional only; no single-card causal claim is made. Unanswered question: whether a different card role can move the profile without diluting identity.
- **Krang:** best current family member is **B** (20.78% mean matchup error). Most informative failed candidate: **A**. Strongest card-role signal: the Gadget Master payoff was less damaging than additional Does Machines density. Unanswered question: whether Krang can gain engine inevitability without creating a new extreme profile.
- **Bebop & Rocksteady:** best current family member is **B** (16.33% mean matchup error). Most informative failed candidate: **none**. Strongest card-role signal: creature-density and brute-force packages both improved balance; B was the stronger balance result. Unanswered question: whether the larger payoff package remains stable outside this 100-game-per-matchup sample.
- **April O'Neil:** best current family member is **round1** (21.89% mean matchup error). Most informative failed candidate: **none**. Strongest card-role signal: the package-level result is directional only; no single-card causal claim is made. Unanswered question: whether a different card role can move the profile without diluting identity.
- **Casey Jones:** best current family member is **B** (17.11% mean matchup error). Most informative failed candidate: **none**. Strongest card-role signal: the larger Mouser Foundry/Pizza artifact package improved balance more than the mixed equipment swap. Unanswered question: whether equipment density or artifact-token conversion better preserves Casey's scrappy identity.

Telemetry includes W/L/D, first-seat result, ending turn, first-play proxies, battlefield presence, interaction casts, signature casts, runtime fingerprints, and per-matchup rates. Cardcade does not expose authoritative engine-activation, hand-size, unused-mana, stranded-card, stabilization, lethal-pressure, or loss-cause labels for every game; those fields remain explicitly unavailable rather than inferred.

Machine-readable evidence: `ROUND_2_EVIDENCE.json`; checkpoint: `ROUND_2_EVIDENCE.checkpoint.json`; card-role dataset: `CARD_ROLE_EVIDENCE.json`. Round 1 evidence SHA-256: `5a74f7ea75349ba33bd4bf4869c09e79fa5f1b4774cea6f1b6aa674a12bcf8dc`.
