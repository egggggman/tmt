# Issue 289 — utility and Equipment semantic checkpoint

**Owner:** 🕹️ Cardcade. **State:** Separate semantic enablement stacked on [combat trigger PR #290](https://github.com/egggggman/tmt/pull/290). The unchanged 4,500-game Baseline 005 control remains **blocked**; no balance rates or deck hypotheses are inferred from this checkpoint.

## Authenticated input and runtime

- The exact ten `OBL-BASELINE-005` lists are read from `docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json`; the independent promotion/structure validator passes. No deck, frozen card catalog, schedule, historical runtime, or earlier game evidence was changed.
- Main was refreshed from `f1cf41f07347d7f65ed1db68eec726071d082031`. This branch is based on the combat trigger checkpoint; the new semantic runtime content identity is `98a9bf5847d729175d442dc5fba3c26be55e902cae2dd9ef322d05b671f6e89b`. This identity is **not** runtime-compatible with the historical Baseline 005 control `d4466241f0ffeaca809cd6a05210ad53b9af1011a1d7f833de88657c1cf00924`.
- The implementation reads the frozen Oracle clauses for Sewer-veillance Cam, Bespoke Bō, Skateboard, and other Equipment. The executable grammar uses type lines, costs, fragments, attachments, and legal targets; it never checks those card or deck names to dispatch an effect.

## General execution enabled

| Family | Executed behavior and evidence |
|---|---|
| Equipment continuous effects | An authoritative attachment grants bounded printed `+P/+T` and haste, vigilance, trample, or double strike in the applicable layers. Re-equip, attachment target leaving, source leaving, and Retro-Mutation ability-loss timestamps recalculate immediately. |
| Artifact entry and leave triggers | Generic artifact/Equipment fragments select legal targets and resolve through the existing pending-trigger, APNAP stack, Priority, and zone paths. The covered payloads are tap target permanent, return up to one *other* nonland permanent to its owner's hand, and optional tap/untap target creature on entry or departure. An illegal target at resolution does nothing. |
| Flash | A represented Flash permanent can be announced during its controller's priority, including the opponent's turn. |
| Sacrifice to draw | A generic fixed-mana, sacrifice-this-artifact activation pays from real lands, moves the source as a cost, delivers its departure trigger above the ability, and draws the parsed positive number of cards on resolution. |
| Acceptance pilot | With no affordable creature to cast, the pilot can select an affordable noncreature cast without a utility card-name list; a castable creature still takes priority. Legal casts and pilot selections are distinct telemetry. |

Focused tests in `tests/test_equipment_continuous_semantics.py` and `tests/test_utility_artifact_semantics.py` cover renamed fixtures, attachment movement and loss, ability-loss ordering, all three frozen utility cards, optional targets, source removal, failed target identity, Flash on the opposing turn, sacrifice/leave/draw ordering, generic pilot branches, and snapshot-equal replay. One previous Skateboard test now resolves the entry trigger before the sorcery-speed Equip action. The activation catalog digest was updated for the newly supported Cam ability; the old digest is retained as historical provenance in the test.

Two **diagnostic-only** April–Raphael games (seed `289`, both seat orientations) were each replayed exactly. They ended on turns 16 and 15, with zero runtime errors; one game recorded five utility trigger resolutions. These four executions are a smoke check, **not** a control sample and not balance evidence.

## Remaining material calibration gate

An Oracle coverage inventory of the exact ten manifest lists still reports **172 per-deck unsupported-fragment/reason entries** after excluding basic-land parenthetical mana reminder text. This is a diagnostic count, not 172 unique cards or equally severe defects. Every deck has remaining coverage gaps:

| Deck | Unsupported entries | Cards with entries |
|---|---:|---:|
| Leonardo | 15 | 6 |
| Raphael | 19 | 6 |
| Donatello | 15 | 8 |
| Michelangelo | 14 | 11 |
| Splinter | 21 | 11 |
| Shredder | 22 | 12 |
| Krang | 14 | 8 |
| Bebop & Rocksteady | 32 | 14 |
| April O'Neil | 8 | 7 |
| Casey Jones | 12 | 6 |

Examples that can materially change the requested ten-deck interpretation include April O'Neil, Hacktivist's end-step draw and Fugitive Droid's evasion; Raphael, Most Attitude's linked trigger incorrectly declining after its source leaves before resolution, and the Spicy Oatmeal Pizza damage trigger; and multiple B&R effects. The ordinary Raphael Alliance/exile and attack-play paths are executable despite being reported by the fragment scanner. Equipment beyond the bounded grammar also retains unsupported compound entry/combat abilities. The historical engine accepted some of these as explicit limitations; passing tests does not make them mechanically correct. Pilot selection of a legal card whose remaining effects are unsupported is not proof of faithful gameplay. The [independent review](ISSUE_289_INDEPENDENT_ACCEPTANCE_REVIEW.md) reconciles all scanner entries.

**Gate decision:** Do not run the 45-cell Baseline 005 control under this runtime. First identify and enable the remaining *material* gameplay clauses under general semantic patterns, with deterministic invariants and pilot coverage; independently establish the readiness threshold for full-ten-deck calibration. Then authenticate the unchanged ten decks and schedule, run the new 4,500-game control and replays, and compare against historical Combined 007 without overwriting it. Design Studio owns deck adjustments and any promotion decision.

## Validation

Local validation: **1,657 passed, 10 skipped** in the full pytest suite; the Baseline 005 independent structural validator, Ruff check and format, diff check, and targeted semantic/replay tests passed. The stacked PR records the GitHub CI result separately. No combined validation, candidate change, Baseline 006, or merge was performed.
