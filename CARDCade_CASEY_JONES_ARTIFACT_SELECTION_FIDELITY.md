# Cardcade Casey Jones Artifact-Selection Fidelity

**Review date:** 2026-11-03  
**Scope:** Read-only review plus deterministic synthetic game-state tests  
**Live games:** Not run

## Finding

**VERIFIED — EXECUTION AND EVIDENCE CORRECT**

For the frozen Stage 002 path reviewed here, the Casey Jones top-four artifact-selection effect selects from the correct cards, updates hand and library zones consistently, and records enough authenticated evidence to reconstruct the choice and resulting state. No material defect was demonstrated in the tested paths. This does not certify unrelated game mechanics or overall deck balance.

## Card contract

The authoritative input for the reviewed run is the frozen Cardcade/Scryfall snapshot `cardcade/scryfall-tmt-pza-tmc-2026-08-13.json`, SHA-256 `56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402`. It identifies **Casey Jones, Jury-Rig Justiciar** (Oracle ID `b4c4fdb9-e034-49c0-9f7f-07e8cae19eb2`), `{1}{R}`, Legendary Creature — Human Berserker, 2/1. Its exact relevant Oracle text is:

> When Casey Jones enters, look at the top four cards of your library. You may reveal an artifact card from among them and put it into your hand. Put the rest on the bottom of your library in a random order.

The frozen Baseline 005 Casey deck contains four copies. Its file is `decks/casey_jones/PROTOTYPE_0.1.txt`, SHA-256 `5c6a9068bab15a2c9f0098778290adbca29b96bf699e7e595edb0966e375748`.

The relevant rules distinction is that “look” shows the cards only to the specified player (Comprehensive Rule 701.20e); “reveal” shows a card to all players and does not itself move it between zones (701.20a–b). The card text authorizes the private look, the optional reveal, the hand move, and random bottom ordering. The default restriction on looking at or changing library order is in CR 401.2; the card effect supplies the permission for this operation. [Wizards’ current rules page](https://magic.wizards.com/en/rules), [Wizards’ 2026 Comprehensive Rules PDF](https://media.wizards.com/2026/downloads/MagicCompRules%2020260619.pdf).

## Reviewed source identities

All source and test identities below are from the detached frozen checkout at `.diag003-frozen-32a8022`, whose Git `HEAD` is `32a80228714674327aca62f8b86b70c4c4afc929` (the PR #372 gameplay candidate used by the 300-game run).

| File | SHA-256 | Relevant behavior |
|---|---|---|
| `src/tmnt_design_studio/card_interpreter07.py` | `a99a8527ed0d80539230327bc9b3c722e898450e382410b73b7ef9791b0d7277` | Exact Jury-Rig rules fragment and semantic coverage, lines 2869–2876. |
| `src/tmnt_design_studio/jury_rig07.py` | `b9253e2dcaf735412918e152e937f6680fd3e77f92e6ddcc15f1b27865f00448` | Eligibility, top-four choice, zone transition, event ledger and snapshot validator, lines 33, 153–168, 253–341, 343 onward. |
| `src/tmnt_design_studio/stage002.py` | `5641af9830f669874c0c99fd320aa137cd0917a25cd22b99ea3c1df6dc7dda26` | Authenticated Jury-Rig reference indexing and snapshot reconciliation, lines 676 onward and 950 onward. |
| `tests/test_jury_rig_action.py` | `64f256c65487049b955fb7675a0c2e0f211f614153c37f2e5177eba60318269b` | Deterministic isolated-action regression cases. |
| `cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json` | `ddbf57645bd016d16659424f2196cd816edfc7a187c4b653a9e6e8839b3e9a6d` | Frozen card-data inventory manifest. |

## Implementation findings

- **Inspection boundary:** `_choose_jury_rig` examines `min(4, library size)` cards. The engine stores the top at the library’s end and reverses that slice to present the inspected cards top-first. Only that tuple of inspected cards is passed to the chooser.
- **Eligibility:** `_jury_rig_artifact` accepts non-token card objects whose card type line includes `Artifact`; artifact creatures qualify. The choice list contains one option for each eligible inspected card plus an explicit “choose none” option. A card below the top four cannot be selected.
- **Resolution:** The chosen eligible card is revealed and moved to hand. Every other inspected card is randomized onto the library bottom. The untouched prefix above the inspected group stays in place. If the player selects none, all inspected cards go to the randomized bottom. The implementation checks that library membership is preserved during reordering.
- **Evidence:** The decision event records source/stack identity, the inspected and eligible IDs, selected ID, pre-choice hand IDs, and library identities. Separate reveal, bottom-order and commit events record the actual reveal, RNG state/domain/permutation, and post-resolution hand/library IDs. An internal evidence ledger preserves the original event sequence. `Game.validate_jury_rig_snapshot_evidence` reconstructs and checks trigger provenance, choices, reveal, zone movement, ordering, RNG evidence, event order, and ledger integrity.
- **Privacy boundary:** The chooser receives only the inspected-card view, not lower library contents. A regression confirms the public view does not expose libraries or the private card identities. Internal evidence is more detailed and records the full library identity list at decision time; that is telemetry, not information passed to the pilot.

## Deterministic synthetic verification

The frozen test file contains **60 parameterized test cases**. All 60 test bodies passed when directly invoked with a small compatibility shim for the file’s two pytest features (`parametrize` and `raises`). The qualified CPython 3.13.15 runtime has no installed `pytest` (`No module named pytest`), so this is **not reported as a pytest run**. No dependencies were installed and no test files were changed.

Coverage includes:

| Scenario | Expected and observed |
|---|---|
| Eligible artifact among the top four | It is an option and, when selected, moves to hand. |
| Multiple eligible artifacts | Each is offered; the chooser may select one or choose none. Existing size/choice cases exercise multiple eligible cards. |
| No eligible artifact in the top four | Only “choose none” is offered; the lower fifth-card artifact case remains ineligible. |
| Fewer than four cards / empty library | The engine inspects only available cards and preserves valid zone membership. Sizes 0–3 are covered. |
| Artifact creature | Correctly treated as an artifact card. |
| Hand/library result and ordering | The selected card is absent from library and present in hand; untouched prefix remains; remaining inspected cards are randomized at bottom. |
| Deterministic replay | Equivalent seeded synthetic states produce identical snapshots. |
| Evidence corruption | Altered inspection/eligibility, ordering, reveal, RNG, hand, or ledger evidence is rejected. |
| Stale/replayed provenance and chooser mutation | Invalid source, trigger, state mutation, RNG mutation, and fabricated selections are rejected without committing the effect. |

An additional deterministic mixed case with one artifact and three non-artifacts confirmed that the chooser received exactly the eligible artifact plus “none”; its selected action and final evidence passed the snapshot validator and Stage 002 authenticated-reference index. No complete-game entrypoint was invoked.

## Preserved 300-game telemetry check

Read-only validation covered the 300 assigned `result.json` files under `G:\cardcade\diagnostics\cardcade-smoke10-20261031-explore300r1-*`. Each recorded run ID matched its expected per-game directory ID. The exact frozen Stage 002 manifest was built from the frozen checkout and used to reconcile the stored snapshots; no game was executed.

- 300/300 snapshots loaded and reconciled without a Casey-path validation exception.
- 126 Casey Jury-Rig occurrences appeared in 84 games.
- All 126 had a `jury_rig_committed` event, an evidence-ledger entry, and a matching authenticated execution reference.
- Stage 002 reconciliation classified all 126 occurrences as **`executed`**.
- Their raw engine `conformance.semantic_occurrences[].classification` field nevertheless says **`reached_unsupported`** in all 126 cases. That raw opportunity-stage label is not the final Stage 002 execution classification.

This resolves the Casey-specific concern raised by the 450-game synthesis: its Casey recommendation treated the raw `reached_unsupported` label as if no authenticated execution evidence existed. Reconciliation against the frozen manifest shows the opposite for all 126 Casey instances. The earlier 450-game counts and other mechanic warnings are not changed by this focused review. Full-snapshot Stage 002 reconciliation also emitted 485 `silent_approximation` stop records across the broader batch; this focused review does not attribute or classify those records, and does not use the Casey result to clear them.

## Limitations

- The normal pytest command could not run because pytest is absent in the qualified runtime; test function assertions were directly executed under the documented minimal shim instead.
- The review establishes the frozen tested action path and stored telemetry. It does not prove every full-game interaction, every possible external effect on a library, or overall Magic rules completeness.
- The 300-game results remain exploratory and fidelity-qualified; this card finding does not convert them into calibration evidence.

## Smallest next action

Correct the Casey-specific interpretation in the 450-game synthesis by appending this reconciliation result, then let HQ decide whether to prepare 900-game calibration. No Casey gameplay correction or additional game is indicated by this evidence.
