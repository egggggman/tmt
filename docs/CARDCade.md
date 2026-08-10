# TMNT the Cardcade Game

Cardcade is the Design Studio's reproducible automated playtesting machine. Its mission is to
produce comparable rehearsal evidence for the ten-deck beta environment before human playtesting.

## Constitutional boundary

Cardcade reports what happened under a named model, seed, roster, and deck version. It may identify
outliers and offer hypotheses. It must not edit a deck, revise Design Intent, or describe heuristic
results as rules-accurate Magic outcomes. Design Studio owns every revision decision.

Cardcade 0.1 is a stochastic resource/tempo model. It models opening hands and mulligans, land
drops, mana use, broad board/support/interaction development, strategy execution, starting-player
advantage, and a noisy closing race. It does **not** execute card text, priority, the stack, combat,
targets, replacement effects, or matchup-specific decisions. Its smoke results are engine and
ecosystem diagnostics, not proof that decks are balanced or fun.

## Reproducibility and records

Every run records the engine and schema versions, random seed, games per pairing, roster checksum,
all 45 pairing summaries, all ten deck summaries, and one immutable record per simulated match.
The versioned match record includes participants, starting player, winner, turns, closing behavior,
and player telemetry. Identical engine, roster, seed, and game count produce identical output.

The roster lives in `cardcade/roster-0.1.json`. Run output contains `run.json` plus a 10×10
`matchup-matrix.json`. Structural validation reads the actual decklist files and rejects a roster
that does not contain ten unique 60-card prototypes.

## Testing ladder and gates

| Stage | Games per unique pairing | Total games | Purpose |
| --- | ---: | ---: | --- |
| Smoke | 20 | 900 | Structure, telemetry, obvious model/deck outliers |
| Calibration | 100 | 4,500 | Locate major imbalances and model sensitivity |
| Development | 500 | 22,500 | Evaluate Design Studio revisions |
| Validation | 1,000+ | 45,000+ | Freeze a baseline candidate |

Each pairing always splits starts evenly. Advance only after reviewing the previous artifact.
Aggregate targets are 45–55%; matchup targets are preferably 40–60%. A 35–65% matchup requires a
strategic justification, greater than 65% is investigated, and greater than 70% is presumed failure.
At smoke size, uncertainty is wide, so thresholds are triage signals rather than revision mandates.

Stabilize 1v1 before designing a 2v2 model. 4v4 is deferred.
