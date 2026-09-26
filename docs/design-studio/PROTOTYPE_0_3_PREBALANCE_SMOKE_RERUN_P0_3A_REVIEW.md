# Prototype 0.3a Pre-Balance Smoke Rerun Review

This is the single corrected-runtime rerun of the frozen Prototype 0.3 pre-balance
smoke. It is descriptive evidence, not a calibrated win-rate estimate.

## Run identity

- Repository SHA: `b6095ac6a2bc19f9c27662bcb67ad080802869fb`
- Harness: `tools/run_prototype_0_3_prebalance_smoke.py`
- Harness SHA-256: `4f07befdadc97da9c614123471f555b70f0e320f24eb7ba38a838c6ae2c2854f`
- Evidence artifact: `PROTOTYPE_0_3_PREBALANCE_SMOKE_RERUN_P0_3A_EVIDENCE.json`
- Runtime identity digest: `47c7507c87c9a0affcbdd72582e43454d96ecf042438071aeae4e4a100c7bae3`
- Schedule identity SHA-256: `f54978e98bc491aa0aa3cd90b67b4d3d1b2612738ee07d95d6d5f5050137fac2`

Runtime component hashes used by the harness:

| Component | SHA-256 |
| --- | --- |
| `src/tmnt_design_studio/engine07.py` | `e575dd69c56248779562aee4bd11e8901b73938b0cb0707927480bdbe3a82638` |
| `src/tmnt_design_studio/stage002.py` | `42b5f4612dda7829efa38f779c238531642b973c717a1ca5598db77629cf965f` |
| `src/tmnt_design_studio/pilot07.py` | `cf24950340f6bd54d77302d89a2fbdb99dae64bdea3948117108b32f18392563` |
| `src/tmnt_design_studio/card_interpreter07.py` | `428a1088e26b7fb6a209e7a360b0fad50e1fc675af815e7d86defab94d7db426` |

## Deck inputs

| Deck | Input | SHA-256 |
| --- | --- | --- |
| Shredder | `decks/shredder/PROTOTYPE_0.3.txt` | `818e9a847fcdf8521f53ab9b49c0f054ddd6f9bce95e9fd57c89cb6c94da2ed2` |
| Raphael | `decks/raphael/PROTOTYPE_0.3.txt` | `220ea90ccc579e09bef38ce972ba84f661c2382b92c7a4559667d24a5eec6f51` |
| Casey Jones | `decks/casey_jones/PROTOTYPE_0.3.txt` | `f18d2dd6591520e495a0c723e1d15f5d3f4f6ce8a2693e4f93be0cd6660e838f` |
| Donatello | `decks/donatello/PROTOTYPE_0.3a.txt` | `25812e2d7f0ac64ae2476c0d62298db35196d1719c9376b5369d5080faa6aad1` |

All four inputs authenticated before game 1 and passed 60-card, recognized-card,
quantity, Standard-legality, and manifest validation.

## Completion summary

- Scheduled: 240
- Attempted: 240
- Completed: 240
- Runtime errors: 0
- Malformed: 0
- Draws: 0
- Turn caps: 0

The schedule remained six matchups, 40 games per matchup, seeds 3000–3039,
and 20 starts per deck. No retries or replacement seeds were used.

## Matchup results

Percentages are descriptive shares of the 40 scheduled games.

| Matchup | Result | Completed | Descriptive percentage | Starting-player split | Errors |
| --- | --- | ---: | --- | --- | ---: |
| Shredder / Raphael | Shredder 22–18 Raphael | 40 | 55.0% / 45.0% | 20 / 20 | 0 |
| Shredder / Casey Jones | Shredder 22–18 Casey Jones | 40 | 55.0% / 45.0% | 20 / 20 | 0 |
| Shredder / Donatello | Shredder 35–5 Donatello | 40 | 87.5% / 12.5% | 20 / 20 | 0 |
| Raphael / Casey Jones | Raphael 25–15 Casey Jones | 40 | 62.5% / 37.5% | 20 / 20 | 0 |
| Raphael / Donatello | Raphael 35–5 Donatello | 40 | 87.5% / 12.5% | 20 / 20 | 0 |
| Casey Jones / Donatello | Casey Jones 32–8 Donatello | 40 | 80.0% / 20.0% | 20 / 20 | 0 |

## Deck aggregates

| Deck | W–L–D | Descriptive percentage |
| --- | --- | ---: |
| Shredder | 79–41–0 | 65.8% |
| Raphael | 78–42–0 | 65.0% |
| Casey Jones | 65–55–0 | 54.2% |
| Donatello | 18–102–0 | 15.0% |

## Comparison to first smoke

The first smoke recorded Donatello at 5–35 versus Shredder, 5–35 versus
Raphael, and 8–32 versus Casey Jones: 18–102 aggregate. The rerun produced the
same three Donatello pairings and the same 18–102 aggregate. This is no
meaningful recovery, even though the corrected runtime completed cleanly.

The non-Donatello results were directionally stable. Shredder/Raphael remained
close at 22–18 versus the first smoke's 22–17 with one runtime failure;
Shredder/Casey remained 22–18; and Raphael/Casey moved from 24–15 with one
runtime failure to 25–15 cleanly. These are 40-game descriptive movements,
not statistical proof.

## Readiness decision

`PREBALANCE_REVIEW_REQUIRED`

All four decks functioned and the runtime was clean, but Donatello remained at
the obviously noncompetitive 15.0% aggregate level with catastrophic results
against each pairing. The four-deck provisional environment is therefore not
reasonable to take to humans on this evidence.

No deck, engine, Pilot, harness, or calibration changes are authorized by this
rerun. Do not create P0.3b/P0.4 or launch full calibration from this sample.
