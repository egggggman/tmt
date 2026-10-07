# Baseline 005 — post-promotion evidence review

**Owner:** 🕹️ Cardcade evidence handoff to 🧪 Design Studio / 🏢 HQ.
**Status:** Read-only review of the accepted 45-cell Combined 007 environment. No games were run for this review, and no deck or runtime changed.

The official [Baseline 005 manifest](baselines/OBL_BASELINE_005_MANIFEST.json) promotes only exact `OBL-R8-BEBOP-A` (Bebop & Rocksteady, `−2 Illegitimate Business / +2 Primordial Pachyderm`). Its runtime is `d4466241f0ffeaca809cd6a05210ad53b9af1011a1d7f833de88657c1cf00924`. The evidence anchor is [Combined 007](COMBINED_007_R8A_RESULTS.md), SHA-256 `2e3d15137b77c8e8eea6da5c26d11ff95d8918570554fdbbb9615afda09be984` for the [compressed machine evidence](COMBINED_007_R8A_EVIDENCE.json.gz). The 36 cells without B&R are reused unchanged; nine B&R cells use accepted [R8-A](ROUND_8_A_RESULTS.md) games. All 4,500 logical outcomes come from those preserved sources.

## Pace and distribution

| Metric | Runtime-compatible Baseline 004 | Baseline 005 / Combined 007 | Change |
|---|---:|---:|---:|
| Mean ending turn | 19.8602 | 19.8304 | −0.0298 |
| Median ending turn | 18 | 18 | 0 |
| Games ending by turn 14 | 745 / 4,500 | 715 / 4,500 | −30 |
| Games ending on turn 40 or later | 76 / 4,500 | 69 / 4,500 | −7 |
| First-player result rate | 57.58% | 57.87% | +0.29 pp |
| Mean matchup balance error | 17.67% | 15.64% | −2.02 pp |
| Strict >60/40 cells | 33 | 30 | −3 |
| Strict >70/30 cells | 18 | 16 | −2 |
| Aggregate WR spread | 46.44 pp | 35.56 pp | −10.89 pp |

In B&R's nine cells alone, mean ending turn moves 18.5833 → 18.4344 and median stays 17. Games ending by turn 14 move 222 → 192 out of 900; games ending on turn 40 or later move 16 → 9. The largest single-game ending turn in these cells moves 96 → 58, while the global maximum moves 96 → 82. These are descriptive distributions, not a forecast of human-play pace. There is no observed drastic pace deterioration in this paired simulator evidence.

## Residual balance question

| Deck | Baseline 005 aggregate WR | Relevant cells |
|---|---:|---|
| April O'Neil | 33.22% | 19% vs Raphael, 19% vs Casey, 23% vs Splinter, 24% vs Shredder |
| Bebop & Rocksteady | 36.33% | 19% vs Shredder, 23% vs Raphael, 26% vs Casey, 29% vs Splinter |
| Raphael | 68.44% | 77% vs B&R, 81% vs April |
| Shredder | 68.78% | 81% vs B&R, 76% vs April |

April is now the lowest aggregate deck. Its four cited cells were among the 36 unchanged control cells, so the B&R substitution did not cause those deficits. B&R's four severe cells improved by 6–17 percentage points but remain below 30%. Its Krang, Donatello, and April cells are 54%, 54%, and 55%; none newly exceeds 60% in B&R's favor. The Krang cell moved 27 percentage points, so a future design review should continue to watch polarization even though the endpoint is near balanced.

April's card execution needs a separate readiness check before a new deck hypothesis. The historical [Round 5 diagnostic](ROUND_5_DIAGNOSTIC.md) reported no credited combat-damage draw for April, Reporter of the Weird and no selected casts for Sewer-veillance Cam or Bespoke Bō under its then-current runtime. Combined 007 records 1,018 Reporter casts and 505 Retro-Mutation casts across April's 900 games, but its compact cast telemetry alone cannot prove Reporter's triggered draw is executing under the current runtime. Treat the win rates as simulator outcomes with that semantic-confidence limit until Cardcade checks the present engine and pilot coverage. This review does not infer that the old coverage gap still exists.

The R8-A game telemetry does not show uniformly earlier creature deployment: B&R's first-creature mean among observed games moves turn 5.6496 → 5.7530 (median 4 in both), while creature presence at the turn-7 observation moves 1.9095 → 2.0472. In the promoted games, B&R's mean ending turn against Raphael and Shredder is 16.25 and 16.51; against Donatello, Krang, and April it is 18.44, 20.04, and 20.57. Matchup composition and opponent behavior can explain these differences, so the timing alone cannot establish a card-level cause.

## Handoff

Design Studio should choose whether the next bounded diagnosis concerns April's unchanged severe cells, B&R's residual four-cell deficit, or the Raphael/Shredder environment pressure. If April is chosen, first verify current-runtime execution of its identity cards. This review does not authorize a candidate, Round 8-B, a combined experiment, a promotion, or a revert. Reversion remains possible through the preserved [Baseline 004 manifest](baselines/OBL_BASELINE_004_MANIFEST.json), but the existing pace and distribution evidence gives no simulator-based reason to trigger it now. Human play remains a separate source of evidence.
