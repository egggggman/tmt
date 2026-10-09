# Cardcade Readiness Gate — Combat-Damage Trigger Semantics

Owner: 🕹️ Cardcade. Request from HQ ten-deck expansion; evidence anchor `docs/objective-balance-lab/BASELINE_005_REVIEW.md`.

## Verified current limitation

The accepted Baseline 005 review records April, Reporter of the Weird's combat-damage-to-player draw-and-discard trigger in the frozen card catalog, but the recorded `engine07.py` runtime does not execute that trigger. April's 900 Combined 007 games contain 1,018 Reporter casts, yet those casts do not establish the card's intended effect. Zero selected Sewer-veillance Cam and Bespoke Bō casts are separately observed, but do not prove whether legal casting opportunities existed.

Do not infer a deck-design defect from April's 33.22% aggregate rate before semantic confidence improves.

## Implementation work (Cardcade-owned)

1. Freshness-check current engine code, card data, and relevant existing generic TriggerEffect handlers against the frozen Baseline 005 semantic runtime `d4466241f0ffeaca809cd6a05210ad53b9af1011a1d7f833de88657c1cf00924`.
2. Establish actual Oracle semantics for the named card and current official Magic combat-damage trigger rules; identify exact source data and card IDs. Never implement a rule based only on a paraphrase in this packet.
3. Implement **generic** combat-damage-to-player trigger detection and appropriate event timing, controller/source attribution, effect ordering, legal choice handling, draw/discard and zone transitions. Do not special-case April or named opponents.
4. Add deterministic tests for successful combat damage, blocked/no-player-damage cases, multiple trigger sources, first/double strike damage steps where relevant, source leaving the battlefield, empty-library and discard edge cases, and event-log/replay consistency.
5. Inspect utility-artifact pilot selection of Sewer-veillance Cam and Bespoke Bō as a separate evidence question; do not force casts or alter selection solely to increase April's win rate.
6. Run the repo's targeted regression and structural validations. Stop for any semantic discrepancy; preserve diagnostics.

## Control and calibration gate

- Preserve frozen Baseline 005, Combined 007 and all earlier artifacts.
- A semantic runtime change invalidates direct comparison to the old control for the affected outcomes. After validated implementation, refresh **unchanged Baseline 005** under the new runtime with authenticated deck hashes, seeds, starting-player balance and deterministic replay.
- Reassess all ten decks and 45 cells only when the new runtime passes semantic tests and the unchanged control is reproducible. Keep the historical 4,500-game matrix as its own labeled baseline; never silently overwrite.
- Report card-trigger execution frequency, game-state effects, pilot choices, win rates, pace, first-player rates, errors and matchup distribution with clear runtime IDs.
- Cardcade reports evidence and hypotheses only. Any candidate deck revision or baseline promotion requires Design Studio authority and a separate gate.

## Separate human-play issue

Skateboard/haste/double strike and artifact/sneak questions from Human Playtest 001 require an independent rules and runtime audit. Do not combine an unvalidated Skateboard fix with April's trigger experiment and then attribute changes to one cause.

## Definition of done

Reproducible generic tests pass; correct Oracle semantics demonstrated; runtime identified; unchanged control refreshed if semantics changed; evidence preserved; Design Studio receives a semantic-confidence report. No claim of completed implementation or simulation is made by this specification.
