# Round 9-A — Splinter isolated balance probe

## Decision

Candidate `OBL-R9-SPLINTER-A` is **REJECTED** for further balance work. The primary weak cells improved modestly, but the Raphael sentinel worsened from 48% to 61%, so the intervention does not smooth the distribution.

Candidate: `−1 Splinter, Hamato Yoshi / +1 Stomped by the Foot`  
Control: `OBL-BASELINE-005-LTB-REPAIR-CONTROL-ATTEMPT-009`  
Runtime: `defefdce8a716ceef6dcedad1a6f50e2abc367bd3cb772a369853506d2f5398d`  
Candidate SHA-256: `402a74e37eb38da1c0ea6b1ee9ff3ffc003ca7a38273d65038256f2a4e718768`  
Evidence SHA-256: `a66ac124b332af85aec1193f4fff64f0d74e29a9cb3312c92b6e6ab58be6fef4`

## Integrity

**900/900 games completed; zero runtime errors; nine full-cell deterministic replays matched.** The established 45-cell schedule was filtered to the nine Splinter pairings without changing seeds, orientations, or opponent decks. Each cell contained 50 canonical and 50 reversed games. The artifact was written, gzip-decompressed, schema-checked, and durably read back before publication.

## Matchup comparison

Control values are from authenticated Attempt 9; candidate uncertainty is Wilson 95% for the 100-game isolated cell. The 100-game deltas are directional evidence only, not standalone causal proof.

| Opponent | Control Splinter WR | R9-A wins / games | R9-A WR (Wilson 95%) | Delta |
| --- | ---: | ---: | ---: | ---: |
| Leonardo | 66% | 63 / 100 | 63% (53.2–71.8%) | −3 pp |
| Raphael | 48% | 61 / 100 | 61% (51.2–70.0%) | +13 pp |
| Donatello | 62% | 55 / 100 | 55% (45.2–64.4%) | −7 pp |
| Michelangelo | 63% | 66 / 100 | 66% (56.3–74.5%) | +3 pp |
| Shredder | 75% | 73 / 100 | 73% (63.6–80.7%) | −2 pp |
| Krang | 67% | 59 / 100 | 59% (49.2–68.1%) | −8 pp |
| Bebop & Rocksteady | 84% | 79 / 100 | 79% (70.0–85.8%) | −5 pp |
| April O'Neil | 82% | 80 / 100 | 80% (71.1–86.7%) | −2 pp |
| Casey Jones | 61% | 61 / 100 | 61% (51.2–70.0%) | 0 pp |

Splinter finished 597/900 (66.33%), versus 608/900 (67.56%) in the control: −1.22 percentage points. No draws occurred. Mean ending turn was 19.87 versus 19.82 in the full control; median was 19 versus 18. The candidate's first-player Splinter subset was 322/450 (71.56%); this is reported as an exposure measure because Attempt 9's published report provides global first-player results rather than a directly comparable Splinter-by-cell baseline.

## Mechanic and pilot exposure

The candidate artifact records 18,367 total casts in the nine cells, 6,252 Splinter interaction casts, 29,754 activation events, 572 aura events, and 100 ETB life-gain events. These counts establish that the games executed normally; they do not show that the added Stomped copy caused the observed results. Pilot choice quality remains a limitation of the deterministic AcceptancePilot.

## Interpretation

The primary cells moved in the intended direction only modestly: B&R −5 pp, April −2 pp, and Shredder −2 pp. Donatello and Krang also improved by −7 and −8 pp, while Raphael moved sharply in the unwanted direction (+13 pp). Casey was unchanged and Michelangelo rose +3 pp. The aggregate reduction therefore came mainly from ordinary 100-game variation and broad matchup shifts, not evidence of a smooth, general suppression mechanism.

**Recommendation: REJECT CANDIDATE.** Do not run combined validation or promote this substitution. Baseline 005 and Attempt 9 remain unchanged. Any next design action requires a new Design Studio hypothesis and separate authorization.
