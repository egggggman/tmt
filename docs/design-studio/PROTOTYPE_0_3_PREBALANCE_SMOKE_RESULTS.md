# Prototype 0.3 Pre-Balance Smoke Results

## Execution identity

- Authority: `PROTOTYPE_0_3_PREBALANCE_AUTHORIZATION.md`, `PROTOTYPE_0_3_PREBALANCE_SMOKE_PLAN.md`, and `PROTOTYPE_0_3_PREBALANCE_SMOKE_HARNESS.md`
- Repository SHA: `d3812b924607b114744d40181e41e6e9a33c4c97`
- Harness: `tools/run_prototype_0_3_prebalance_smoke.py`
- Harness SHA-256: `b10234588e7e5d39e20c46337ceeae7248da0fe10b750f2ea03068647753cc4d`
- Runtime identity emitted by the harness: `8d322e2808a6f39549469923ceaa77a8afc478b1ca3eb5c2559cdcadcc544301`
- Schedule identity: the harness does not emit a separate schedule digest; the frozen schedule is identified by the repository SHA, harness contract, six matchups, seeds `3000..3039`, and 20/20 orientation split.

Authenticated deck inputs:

| Deck | Path | SHA-256 |
| --- | --- | --- |
| Shredder | `decks/shredder/PROTOTYPE_0.3.txt` | `818e9a847fcdf8521f53ab9b49c0f054ddd6f9bce95e9fd57c89cb6c94da2ed2` |
| Raphael | `decks/raphael/PROTOTYPE_0.3.txt` | `220ea90ccc579e09bef38ce972ba84f661c2382b92c7a4559667d24a5eec6f51` |
| Donatello | `decks/donatello/PROTOTYPE_0.3.txt` | `77eaf396e6e995a0cbce39b5ad1bf5202f774e8650796480a416122d4a526f08` |
| Casey Jones | `decks/casey_jones/PROTOTYPE_0.3.txt` | `f18d2dd6591520e495a0c723e1d15f5d3f4f6ce8a2693e4f93be0cd6660e838f` |

Banked machine-readable evidence: `PROTOTYPE_0_3_PREBALANCE_SMOKE_EVIDENCE.json`.
Evidence JSON SHA-256: `4bf8ec492ab7de42ad033a1e7740ba44bc413b98d7297e43ab01a6415ee98d56`.

The harness completed on 2026-09-26. It does not record game start/end timestamps; the evidence
file was created at approximately `2026-09-26T05:14:56Z` and the result report at approximately
`2026-09-26T05:14:58Z`.

## Completion

| Measure | Result |
| --- | ---: |
| Scheduled | 240 |
| Attempted | 240 |
| Completed | 238 |
| Malformed | 0 |
| Runtime errors | 2 |
| Draws | 0 |
| Turn-cap outcomes | 0 |

The two runtime failures were preserved without retry:

- `shredder-vs-raphael-3007`: `SmokeGameFailure: max() iterable argument is empty`
- `raphael-vs-casey_jones-3001`: `SmokeGameFailure: max() iterable argument is empty`

## Matchup results

Percentages use completed games only and are descriptive smoke observations, not calibrated
estimates. Runtime-failed games are excluded from W/L percentages and shown separately.

| Matchup | Completed | W/L/D | Descriptive result | Starting-player games | Runtime errors |
| --- | ---: | --- | --- | --- | ---: |
| Shredder / Raphael | 39 | Shredder 22–17–0 | 56.41% / 43.59% | Raphael 20, Shredder 20 | 1 |
| Shredder / Casey Jones | 40 | Shredder 22–18–0 | 55.00% / 45.00% | Casey Jones 20, Shredder 20 | 0 |
| Shredder / Donatello | 40 | Shredder 35–5–0 | 87.50% / 12.50% | Donatello 20, Shredder 20 | 0 |
| Raphael / Casey Jones | 39 | Raphael 24–15–0 | 61.54% / 38.46% | Casey Jones 20, Raphael 20 | 1 |
| Raphael / Donatello | 40 | Raphael 35–5–0 | 87.50% / 12.50% | Donatello 20, Raphael 20 | 0 |
| Casey Jones / Donatello | 40 | Casey Jones 32–8–0 | 80.00% / 20.00% | Casey Jones 20, Donatello 20 | 0 |

## Four-deck aggregates

These aggregates include all 120 scheduled matchup slots per deck; runtime failures are shown
explicitly and are not treated as losses or draws.

| Deck | Scheduled | Completed | W/L/D | Runtime errors | Descriptive completed-game win rate |
| --- | ---: | ---: | --- | ---: | ---: |
| Shredder | 120 | 119 | 79–40–0 | 1 | 66.39% |
| Raphael | 120 | 118 | 76–42–0 | 2 | 64.41% |
| Donatello | 120 | 120 | 18–102–0 | 0 | 15.00% |
| Casey Jones | 120 | 119 | 65–54–0 | 1 | 54.62% |

## Diagnostic interpretation

- **Shredder:** the Super Shredder reduction did not cause collapse, but Shredder remained sharply
  dominant against Donatello. Its results were less extreme against Raphael and Casey in this
  small sample. The runtime failure prevents treating the pairing as fully complete.
- **Raphael:** the Wingnut reduction did not make the deck nonfunctional. Raphael remained strong
  against Donatello and closer against Casey; one Raphael/Casey runtime failure remains unresolved.
- **Donatello:** the restored Does Machines slot did not produce a broad visible recovery in this
  smoke. Donatello completed all games, but lost heavily in all three pairings; this remains a
  diagnostic signal, not a calibrated conclusion.
- **Casey Jones:** the Equipment reduction left Casey functional and closer to the other revised
  decks than its prior broad calibration result. One runtime failure occurred in its Raphael
  pairing.

The Shredder/Donatello, Raphael/Donatello, and Casey/Donatello results are large directional
signals in this sample. The two runtime failures are a runtime-integrity concern, not evidence for
deck tuning. No deck is declared balanced or unbalanced from these 40-game samples.

## Readiness and limits

`PREBALANCE_REVIEW_REQUIRED`

The four decks did execute, but the exact 240-game smoke did not complete cleanly: two games hit
the same runtime failure and were not retried. Design Studio should review that runtime issue and
the Donatello pressure results before human-play readiness is recorded. This report authorizes no
deck edits, Prototype 0.4, engine/Pilot changes, new Calibration V1 run, or expanded revision
scope.
