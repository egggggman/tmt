# Cardcade — Krang Round 6-A isolated validation

Design Studio's [preserved candidate](candidates/KRANG_OBL_R6_A.txt) was tested byte-for-byte against [OBL-BASELINE-003](baselines/OBL_BASELINE_003_MANIFEST.json). No deck or Cardcade semantics changed. [Game-level evidence](ROUND_6_A_EVIDENCE.json) and [checkpoint](ROUND_6_A_CHECKPOINT.json) preserve the 900 frozen games and 900 matching deterministic replays. The predeclared Stage 1 rule permitted Stage 2 after Shredder improved 12→17% and Raphael 13→14%.

Candidate checked-out SHA-256: `f7d5734781c06349d33dc3396614ec8f7e448ada4ceb8d468db84d1f268a38fa`; Git-blob SHA-256: `15d218c5395eb66e1e36bdd66758051287ed383fb09d803f0eec465284e8d3f6`. Parent SHA-256: `5a52bc59b5de1034721ba17d1c1d4f12c493ec70681c1a910c8230808e4e4f96`. Runtime: `78bcce5b5f635f11c67247df91f90fef2bf0dbf948973c5c1ac38419f28b0e25`. Schedule: `b5fd8ab57016b15662fca420d508c9aab3633ad14b7f7515d667492b0f8abf27`. These two candidate hashes differ only because Windows checkout uses CRLF while the preserved Git blob uses LF; the list and card content were not edited.

Exact diff: -1 Negate, +1 Donatello, Turtle Techie. Candidate is 60 cards, Standard-legal, mono-blue, and preserves Krang's artifact-engine identity.

Mean Matchup Balance Error = mean of `abs((wins + draws/2)/100 - 0.5)` over nine opponents. Counts above 60/40 and 70/30 use strict `>` thresholds; negative balance delta is improvement.

| Metric | Baseline 003 Krang | R6-A | Delta |
|---|---:|---:|---:|
| Aggregate WR | 35.33% | 40.11% | +4.78 pp |
| Mean balance error | 19.56% | 19.89% | +0.33 pp |
| >60/40 | 6 | 7 | +1 |
| >70/30 | 4 | 4 | +0 |
| Worst matchup | shredder 12.00% | raphael 14.00% | — |
| Candidate-first result | 37.56% | 42.00% | — |
| Mean / median ending turn | 20.1822 / 19.0 | 20.3011 / 19.0 | — |

| Opponent | Baseline 003 | R6-A | Delta |
|---|---:|---:|---:|
| leonardo | 68.00% | 72.00% | +4.00 pp |
| raphael | 13.00% | 14.00% | +1.00 pp |
| donatello | 46.00% | 48.00% | +2.00 pp |
| michelangelo | 32.00% | 31.00% | -1.00 pp |
| splinter | 20.00% | 23.00% | +3.00 pp |
| shredder | 12.00% | 17.00% | +5.00 pp |
| bebop_rocksteady | 51.00% | 56.00% | +5.00 pp |
| april_oneil | 53.00% | 67.00% | +14.00 pp |
| casey_jones | 23.00% | 33.00% | +10.00 pp |

Stage 1 used 100 frozen games per cell, 50 starts per side, no adaptive/replacement seeds. Shredder: 12→17%; Raphael: 13→14%. Both severe diagnostics moved toward center, so Stage 2 was authorized. Detailed seat splits, game lengths, and all fingerprints are in machine evidence.

| Stage 1 opponent | Krang first-seat wins / 50 | Opponent first-seat wins / 50 | Mean / median ending turn | First-creature proxy | Turtle Techie casts / resolved draws | Interaction casts |
|---|---:|---:|---:|---:|---:|---:|
| shredder | 7 | 40 | 18.59 / 17.5 | 7.9022 | 19 / 17 | 126 |
| raphael | 8 | 44 | 18.56 / 18.0 | 9.3571 | 16 / 14 | 139 |

Stage 1 battlefield-presence proxies t3/t5/t7 are in machine evidence; missing observations are not zero.

First-creature timing (conditional mean when observed): {'observed_games': 809, 'mean_turn_if_observed': 9.3276, 'median_turn_if_observed': 9} → {'observed_games': 809, 'mean_turn_if_observed': 8.9629, 'median_turn_if_observed': 9}. Battlefield-presence proxies t3/t5/t7 (observed-only conditional means): {'3': {'observed_games': 608, 'mean_creatures_if_observed': 1.1595, 'positive_games': 494}, '5': {'observed_games': 756, 'mean_creatures_if_observed': 1.9259, 'positive_games': 700}, '7': {'observed_games': 810, 'mean_creatures_if_observed': 2.6568, 'positive_games': 796}} → {'3': {'observed_games': 608, 'mean_creatures_if_observed': 1.1793, 'positive_games': 494}, '5': {'observed_games': 750, 'mean_creatures_if_observed': 1.9293, 'positive_games': 698}, '7': {'observed_games': 822, 'mean_creatures_if_observed': 2.6788, 'positive_games': 809}}. Missing observations are not zero.

Interaction casts (Oracle-text matched): 1327 → 1340; Negate signature casts in parent: 0; Turtle Techie signature casts: 218. Supported ETB effect events in replay: resolved 188, artifact condition met 188, cards drawn 188. Drawn-card frequency from hand is unavailable, not zero.

Distribution test: Shredder improved; Raphael improved slightly; overall mean balance error worsened; >60/40 increased 6→7; >70/30 stayed 4; previously near-even April (53%) became 67% Krang-favored. The one-copy package is less polarizing by >60/40 count than historical R5-B's two-copy result (8), but still introduces an additional extreme and does not smooth the Baseline 003 distribution. R5-B used Baseline 002 opponents, so its 43% WR and 17.89% balance error are historical context, not a paired comparison to this Baseline 003 test.

Hypothesis: **PARTIALLY_SUPPORTED**. Cardcade verdict: **RETURN_TO_DESIGN_STUDIO_REJECT_POLARIZATION**. Identity: **IDENTITY_PRESERVED**. The active artifact-linked body raises WR and improves the primary diagnostic, but the core smooth-distribution claim fails. Return this evidence to Design Studio; Cardcade does not originate R6-B or recommend promotion from this isolated result.

Nine 100-game cells, 450 starts per side in aggregate, 900/900 games, zero runtime errors, and 900/900 matching deterministic replay fingerprints. No baseline evidence was regenerated. No candidate-vs-candidate games were run.
