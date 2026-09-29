# Objective Balance Lab — Round 1 Delta Results

The baseline completed 4,500 games and the isolated candidate runs completed 9,000 games. There were
no runtime errors, replacement seeds, adaptive seeds, or candidate-vs-candidate games. Results below
are computed from `ROUND_1_EVIDENCE.json`.

| Deck | Parent WR | Candidate WR | Balance Δ | Worst matchup Δ | 60/40 parent→candidate | >70/30 parent→candidate | Identity | Verdict |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| Leonardo | 35.44% | 35.78% | -0.56 pp | Raphael -1 pp | 0→0 | 0→0 | IDENTITY_STRENGTHENED | ACCEPT_FOR_COMBINED_MATRIX |
| Raphael | 76.78% | 78.22% | +1.44 pp | Splinter -3 pp | 8→9 | 5→6 | IDENTITY_STRENGTHENED | REJECT_BALANCE_REGRESSION |
| Donatello | 41.00% | 42.33% | +1.33 pp | Raphael -2 pp | 2→2 | 1→0 | IDENTITY_STRENGTHENED | REJECT_BALANCE_REGRESSION |
| Michelangelo | 54.11% | 54.11% | 0.00 pp | Shredder 0 pp | 5→5 | 2→2 | IDENTITY_PRESERVED | INCONCLUSIVE |
| Splinter | 62.78% | 62.78% | 0.00 pp | Shredder 0 pp | 6→6 | 4→4 | IDENTITY_PRESERVED | INCONCLUSIVE |
| Shredder | 73.00% | 73.00% | 0.00 pp | Raphael 0 pp | 7→7 | 6→6 | IDENTITY_PRESERVED | INCONCLUSIVE |
| Krang | 35.11% | 39.89% | +1.22 pp | Raphael +1 pp | 1→3 | 0→1 | IDENTITY_STRENGTHENED | REJECT_BALANCE_REGRESSION |
| Bebop & Rocksteady | 32.67% | 37.33% | -2.89 pp | Casey Jones -4 pp | 1→1 | 0→0 | IDENTITY_STRENGTHENED | ACCEPT_FOR_COMBINED_MATRIX |
| April O’Neil | 25.67% | 28.11% | -2.44 pp | Raphael +7 pp | 0→0 | 0→0 | IDENTITY_STRENGTHENED | ACCEPT_FOR_COMBINED_MATRIX |
| Casey Jones | 63.44% | 59.78% | -1.00 pp | Raphael -9 pp | 6→4 | 3→3 | IDENTITY_STRENGTHENED | ACCEPT_FOR_COMBINED_MATRIX |

## Per-matchup deltas

Each entry is candidate win-rate minus parent win-rate, in percentage points, for the named deck’s
matchup. This is the complete nine-opponent delta set for every candidate.

| Deck | Per-matchup Δ (opponent: pp) |
| --- | --- |
| Leonardo | Raphael -1; Donatello +2; Michelangelo +2; Splinter +5; Shredder 0; Krang -2; Bebop & Rocksteady -2; April +1; Casey -2 |
| Raphael | Leonardo +2; Donatello +2; Michelangelo +4; Splinter -3; Shredder +4; Krang -1; Bebop & Rocksteady +2; April -1; Casey +4 |
| Donatello | Leonardo -1; Raphael -2; Michelangelo 0; Splinter +1; Shredder +5; Krang +5; Bebop & Rocksteady +4; April 0; Casey 0 |
| Michelangelo | all nine matchups 0 |
| Splinter | all nine matchups 0 |
| Shredder | all nine matchups 0 |
| Krang | Leonardo +5; Raphael +1; Donatello +6; Michelangelo -1; Splinter +8; Shredder +2; Bebop & Rocksteady +9; April +12; Casey +1 |
| Bebop & Rocksteady | Leonardo +6; Raphael +5; Donatello +6; Michelangelo +8; Splinter +1; Shredder +7; Krang +9; April +4; Casey -4 |
| April O’Neil | Leonardo -7; Raphael +7; Donatello +1; Michelangelo +1; Splinter +10; Shredder +5; Krang -3; Bebop & Rocksteady +8; Casey 0 |
| Casey Jones | Leonardo -3; Raphael -9; Donatello -7; Michelangelo +1; Splinter -4; Shredder -3; Krang +2; Bebop & Rocksteady -5; April -5 |

Balance Δ is candidate Mean Matchup Balance Error minus parent error; negative is better. Parent and
candidate errors were calculated across the nine matchups involving that deck. Parent errors were:
Leonardo 16.78%, Raphael 26.78%, Donatello 18.11%, Michelangelo 18.33%, Splinter 21.67%, Shredder
24.56%, Krang 20.89%, Bebop & Rocksteady 19.78%, April 24.33%, and Casey 18.33%.

## Matchup deltas

The largest observed shifts were: Leonardo vs Splinter +5 pp; Raphael vs Michelangelo, Shredder, and
Casey +4 pp each; Donatello vs Shredder and Krang +5 pp each; Krang vs April +12 pp and vs Bebop &
Rocksteady +9 pp; Bebop & Rocksteady vs Michelangelo +8 pp; April vs Splinter +10 pp; and Casey vs
Raphael -9 pp. These are directional 100-game estimates, not authorization-grade significance claims.

## Telemetry and interpretation

The evidence records W/L/D, win rate, first-seat result rate, ending-turn mean/median, first creature,
first meaningful creature/blocker proxy, first interaction proxy, battlefield presence at turns 3/5/7,
signature casts, interaction casts, runtime fingerprints, and the full seed schedule. The current
AcceptancePilot snapshot does not expose authoritative per-turn hand size, unused mana, flood/screw,
stranded-card, engine-activation, stabilization, lethal-pressure, or loss-cause labels for every game;
those fields are therefore not inferred or fabricated. They remain a semantic-confidence limitation,
especially for the zero-delta Michelangelo, Splinter, and Shredder probes.

Identity was assessed against the declared hypothesis and exact card diff, not raw win rate alone.
The four ACCEPT candidates improve balance error while retaining or strengthening their stated role.
Raphael, Donatello, and Krang improve raw win rate but worsen balance error; they are rejected. The
three zero-observable-delta candidates are preserved as inconclusive evidence rather than promoted.

All machine-readable game summaries, exact hashes, card diffs, and schedule rows are in
`ROUND_1_EVIDENCE.json`; the reproduction command is:

```text
.venv\Scripts\python.exe tools/run_objective_balance_lab_round1.py --workers 12 --output docs/objective-balance-lab/ROUND_1_EVIDENCE.json
```
