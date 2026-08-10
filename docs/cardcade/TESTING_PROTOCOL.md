# Cardcade Testing Protocol

Cardcade provides reproducible automated playtesting and telemetry. It is a heuristic rehearsal
system, not a Magic rules engine, human fun test, or authority to redesign decks.

## Progressive run sizes

| Stage | Games per matchup | Purpose |
| --- | ---: | --- |
| Smoke | 20 | Detect broken behavior, missing telemetry, gross instability, and reproducibility failures. |
| Calibration | 100 | Examine direction, sensitivity, and broad matchup behavior after smoke checks pass. |
| Development | 500 | Evaluate a bounded engine or deck hypothesis after the model is credible enough to justify the cost. |
| Validation | 1,000 or more | Confirm a candidate conclusion before it informs a durable Design Studio decision. |

Every stage uses balanced starting-player splits. Odd game counts are not used for a matchup when
they would prevent an exact split.

## Required controls

Each recorded run identifies the engine version, model and roster inputs, immutable deck versions,
seed, games per matchup, starting-player protocol, configuration, and output schema. Repeating the
same inputs must reproduce the same result.

Comparisons change one named responsibility at a time where practical. Reports distinguish sampling
variation from model changes, publish failed gates and negative results, and retain prior runs rather
than replacing inconvenient evidence.

## Interpretation gate

No larger run repairs a weak model. A stage advances only when the earlier stage's telemetry shows
that relevant mechanics are represented, outcomes are attributable, and stability is adequate for
the question being asked. Simulator findings are hypotheses; [Design Studio](../design-studio/STATUS.md)
owns any deck revision decision.
