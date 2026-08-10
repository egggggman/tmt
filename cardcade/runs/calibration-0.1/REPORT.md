# Cardcade Beta 0.1 Calibration Report

Status: **completed — specific findings ready for Design Studio consideration; no deck revisions authorized**

## Protocol and provenance

- Engine: `cardcade-0.4.0` at source commit `0dbb04a4bbeaeded9adab40c7f462fda8948ec3b`
- Frozen roster: Prototype 0.1, roster hash `a72848dafdc47a9268b89a6d0c75aa37c82d8922bcb447205c705994c5de60fb`
- Seed: `20260809`; deterministic stream key: seed, ordered pairing IDs, and game index
- Games: 100 per pairing, 45 unique pairings, 4,500 total
- Starts: exactly 50 starts for each deck in every pairing
- Artifacts: `configuration.json`, `run.json`, and `matchup-matrix.json`

`configuration.json` preserves the complete protocol and SHA-256 of every frozen decklist. The
engine describes itself as a heuristic rehearsal, not a Magic rules engine or direct record of
human play. Results support balance hypotheses, not autonomous card or deck changes.

## Aggregate results

Each deck played 900 games. Intervals are normal-approximation 95% sampling intervals; with 900
games, an estimate near 50% has a margin of about ±3.3 points. These intervals describe simulation
sampling uncertainty only and do not account for model error.

| Rank | Deck | Win rate | 95% interval | Classification |
|---:|---|---:|---:|---|
| 1 | Krang | 63.7% | 60.5–66.8% | Credible balance issue |
| 2 | Donatello | 63.2% | 60.1–66.4% | Credible balance issue |
| 3 | Raphael | 52.6% | 49.3–55.8% | Healthy / target edge |
| 4 | Shredder | 50.3% | 47.1–53.6% | Healthy |
| 5 | Bebop & Rocksteady | 47.0% | 43.7–50.3% | Healthy |
| 6 | April O'Neil | 45.6% | 42.3–48.8% | Healthy / target edge |
| 7 | Casey Jones | 45.3% | 42.1–48.6% | Healthy / target edge |
| 8 | Michelangelo | 45.1% | 41.9–48.4% | Healthy / target edge |
| 9 | Splinter | 44.3% | 41.1–47.6% | Watchlist |
| 10 | Leonardo | 42.9% | 39.7–46.1% | Watchlist |

Krang and Donatello both clear the 55% target boundary by more than their sampling intervals. Their
near-identical aggregate strength comes from different profiles: Donatello is 58–70% against eight
opponents but only 53% against Krang; Krang is 62–70% against eight opponents but 47% against
Donatello. Leonardo and Splinter fall below target, but the evidence does not yet separate their own
power from metagame pressure created by the two leaders.

## Complete matchup matrix

Rows are the listed deck's win rate. Each off-diagonal cell contains 100 games and therefore has a
worst-case normal 95% margin of ±9.8 points. Exact 70% results do not cross the established `>70%`
presumed-failure rule, but all results above 65% require investigation.

| Deck | Leo | Raph | Don | Mikey | Splinter | April | Casey | Shredder | Krang | Bebop/Rock |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Leonardo | — | 33% | 33% | 57% | 52% | 44% | 50% | 34% | 34% | 49% |
| Raphael | 67% | — | 30% | 58% | 56% | 56% | 52% | 54% | 34% | 66% |
| Donatello | 67% | 70% | — | 69% | 63% | 66% | 62% | 58% | 53% | 61% |
| Michelangelo | 43% | 42% | 31% | — | 60% | 49% | 58% | 43% | 33% | 47% |
| Splinter | 48% | 44% | 37% | 40% | — | 52% | 42% | 47% | 38% | 51% |
| April O'Neil | 56% | 44% | 34% | 51% | 48% | — | 55% | 43% | 35% | 44% |
| Casey Jones | 50% | 48% | 38% | 42% | 58% | 45% | — | 49% | 36% | 42% |
| Shredder | 66% | 46% | 42% | 57% | 53% | 57% | 51% | — | 30% | 51% |
| Krang | 66% | 66% | 47% | 67% | 62% | 65% | 64% | 70% | — | 66% |
| Bebop & Rocksteady | 51% | 34% | 39% | 53% | 49% | 56% | 58% | 49% | 34% | — |

Twelve pairings finish outside 35–65%: Donatello over Raphael (70%), Michelangelo (69%), Leonardo
(67%), and April (66%); Krang over Shredder (70%), Michelangelo (67%), Leonardo (66%), Raphael
(66%), and Bebop & Rocksteady (66%); Raphael over Leonardo (67%) and Bebop & Rocksteady (66%);
and Shredder over Leonardo (66%). All twelve exclude 50% in their approximate intervals, but none
has an interval wholly beyond 65%. They are matchup watchlist evidence, not standalone presumed
failures. The remaining 33 pairings are healthy or potentially intentional characteristics pending
strategic review; the Krang–April 65–35 boundary is the most important of those.

## Starting player and game length

The first player won 52.2% overall (2,349 of 4,500), close to Engine 0.4 smoke's 53.1%. Pairing-level
first-player rates range from 40% (Donatello–April) to 61% (Splinter–Shredder); none is independently
compelling at 100 games after accounting for 45 comparisons. Deck win rates when that deck started
ranged from 45.3% for Leonardo to 66.0% for Krang and largely track deck strength rather than a new
starting-player anomaly. Balanced starts remove starting order as an explanation for aggregate rank.

Games lasted a mean 8.84 turns (median 9; population SD 1.97). The distribution was: turn 4, 133;
5, 147; 6, 286; 7, 493; 8, 736; 9, 875; 10, 933; 11, 585; 12, 241; 13, 58; and 14, 13.
Contested closes represented 3,879 games (86.2%); 621 (13.8%) were classified as runaways.

## Mulligan and mana telemetry

| Deck | Mulligan | Screw | Flood | Strategy execution |
|---|---:|---:|---:|---:|
| Leonardo | 19.6% | 1.3% | 23.4% | 91.8% |
| Raphael | 21.4% | 0.1% | 26.3% | 91.0% |
| Donatello | 18.0% | 0.8% | 29.4% | 92.0% |
| Michelangelo | 19.8% | 0.9% | 26.6% | 90.6% |
| Splinter | 19.9% | 0.7% | 25.8% | 92.1% |
| April O'Neil | 20.9% | 0.8% | 26.1% | 89.6% |
| Casey Jones | 21.4% | 0.8% | 26.2% | 91.6% |
| Shredder | 20.1% | 0.7% | 24.4% | 91.0% |
| Krang | 19.8% | 0.8% | 26.2% | 82.1% |
| Bebop & Rocksteady | 15.3% | 0.3% | 37.0% | 88.6% |

Mana screw is rare and does not explain rank. Bebop & Rocksteady's 37.0% flood rate is a distinct
watchlist signal despite its healthy aggregate result. Donatello's 29.4% flood is elevated yet does
not prevent high performance. Mulligan rates are otherwise tightly grouped.

## Artifact, sequencing, and resource preservation

| Signal | Donatello | Krang |
|---|---:|---:|
| Setup rate | 98.8% | 99.7% |
| Payoff cast rate | 97.7% | 86.6% |
| Payoff realization rate | 93.8% | 83.0% |
| Full strategy execution | 92.0% | 82.1% |
| Realized payoffs / game | 2.77 | 1.44 |
| Rejected payoff lines / game | 2.36 | 0.79 |
| Artifacts cast / game | 4.67 | 5.80 |
| Sequencing decisions / game | 8.30 | 8.25 |
| Rejected sequencing lines / game | 8.97 | 7.97 |
| Artifact sequencing holds / game | 0.19 | 0.18 |
| Resource-preservation game rate | 14.1% | 14.6% |

Donatello closely reproduces smoke execution (98.3% setup, 94.4% realization, 92.2% full execution)
while its win rate falls from 67.2% to 63.2%. This convergence makes over-efficient, highly reliable
artifact conversion the highest-priority Design Studio hypothesis. The pilot still rejects many
legal and payoff lines, so the result is not explained by blindly forcing every tagged card.

Krang also converges: 63.7% versus 62.8% in smoke, with 2.42 affinity mana saved per game versus
2.47. Affinity triggers in 49.9% of games and averages 0.59 affinity spells cast per game. Krang's
lower 82.1% full execution combined with the strongest aggregate rate suggests its broader card
quality/infrastructure plus the successful affinity turns may be too resilient, rather than setup
reliability alone. Its 47% result against Donatello is a healthy counterpoint.

Shredder improves from 46.7% smoke to 50.3% calibration, with 91.0% strategy execution and 1.58 of
1.62 seen interaction pieces used per game. The calibration does not support an aggregate Shredder
problem, although 70–30 into Krang and 66–34 over Leonardo are matchup watchlist items.

## Findings and handoff

### Credible balance issues

1. **Donatello aggregate strength and execution reliability.** Its 63.2% interval lies wholly above
   target and it has four >65% matchups. Investigate the modeled conversion of ubiquitous setup into
   repeated realized payoff value and verify the pattern in human play.
2. **Krang aggregate strength and matchup breadth.** Its 63.7% interval lies wholly above target and
   it has five >65% matchups plus a 65% boundary result. Investigate infrastructure resilience and
   the impact of affinity turns, preserving the distinction between discount and general strength.

### Watchlist

- Leonardo (42.9%) and Splinter (44.3%) are below aggregate target. Re-test after accounting for
  Donatello/Krang metagame pressure before attributing weakness to their individual cards.
- The twelve 66–70% matchup outliers listed above warrant strategic review and human-play checks;
  no result is above 70%, so none automatically meets the presumed-failure rule.
- Bebop & Rocksteady's 37.0% mana-flood rate is materially higher than the field and should be
  checked against the coarse mana model and real opening/play patterns.

### Healthy or potentially intentional characteristics

- Raphael, Shredder, Bebop & Rocksteady, April, Casey, and Michelangelo are within the 45–55%
  aggregate target. Shredder's smoke concern is not reproduced.
- Overall first-player behavior, game length, closing mix, and very low screw rates show no global
  calibration-level defect. Thirty-three matchups remain within the accepted 35–65% band.

**Handoff decision:** the evidence is strong enough to return specific balance findings to Design
Studio for Prototype 0.2 consideration. Priority is (1) Donatello's extremely reliable payoff
conversion, (2) Krang's broad strength and affinity-supported resilience, then (3) whether Leonardo
and Splinter remain weak after controlling for those two leaders. Human play and Design Intent must
test these hypotheses before any card swap or deck revision. Cardcade authorizes none.
