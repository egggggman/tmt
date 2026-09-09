# Action #31 candidate — Paramecia ETB mill three

Authorized base: `90b3c9535bed7a9d1878eef762d41b42616f8912`, Issue #102. Branch: `codex/cardcade-action31-mill-three`. Candidate SHA is the PR head and final handoff; this report does not self-accept or authorize merge.

The exact frozen creature-entry fragment now mills the controller's resolution-time top `min(3, library size)` cards in top-first order through existing Trigger / Stack / Priority and authoritative `move_object`. Each milled card receives one distinct graveyard incarnation. Untouched library and graveyard prefixes retain identity/order. There is no chooser, RNG use, Draw/failed-draw behavior or empty-library loss caused by milling. Existing post-resolution SBAs may still consume a preexisting failed-draw condition.

The dedicated module records original card/permanent birth identities, authenticates source/event/trigger/Stack provenance, and preflights all touched zone objects, containers and allocation state before any move. A local rollback restores only the touched movement state if a move fails. Source departure/control change does not transfer or cancel the original controller's trigger; reentry is independently authenticated. The exact dies/exile/reflexive-return sibling remains unsupported.

An immutable original pre-state and transaction ledger support independent reconstruction from ETB, Trigger/Stack/all-pass permission, pre-library/graveyard, exact contiguous movement identities/order, final zones, unchanged hand/failed-draw/RNG evidence and completion. Serialized identities and preceding zone/cessation history authenticate the joins. Both live and serialized execution indexes require the completed mill chain, not generic trigger or zone-change events.

## Final validation

- Focused Action #31: **61 passed**.
- Focused plus Jury-Rig, Courier, hand-bottom/draw, Scry, Vigilante and Trigger regressions: **273 passed**.
- Full pytest: **1,216 passed, 1 skipped**.
- Ruff check, Ruff format check, canonical terminology scan, unstaged/staged diff checks and evidence sidecar checks passed before commit.
- Complete raw/derived evidence is preserved below, with exact source/test Git blob identities in the validation record.

## Stage and Smoke

**Stage #002:** one unchanged 16-game / 32-execution invocation. Observed **30 EXECUTED / 1 REACHED-UNSUPPORTED / 133 PRESENT-UNREACHED**. Exact duplicate evidence; zero stops/violations; all 16 reports reconstruct under final code. This frozen matrix reaches no mill transaction, so no natural Stage mill credit is claimed. The sole remaining unsupported occurrence remains terminal-pending Vigilante. Prior Stage EXECUTED occurrence counts are unchanged.

**Smoke:** accepted restart completes the unchanged 180-game / 360-execution matrix. All duplicate snapshots and 180 reports reconstruct; zero stops, violations or invalid games. Mechanical labels: **108 coverage-complete / 72 coverage-limited**. Observed semantic occurrences: **490 EXECUTED / 118 REACHED-UNSUPPORTED / 1,530 PRESENT-UNREACHED**. **21 natural mill transactions across 17 games** reconstruct; zero reached-unsupported mill-three occurrences remain. These are measured counts, not forced targets or calibration evidence.

The first Smoke attempt stopped fail-closed while reconciling game 50, `bebop_rocksteady--leonardo:reversed:8025`, at execution ordinal 100 after 49 completed reports. The new mill validator reconstructed the prior graveyard from movement logs but omitted existing token-cessation records. The correction only joins authenticated `token_ceased` events and original token identities into that reconstruction. A focused cessation/corruption regression and the full suite then passed. The failed attempt and exact failed-validator source are retained. Smoke restarted from game 1; no partial reports were combined with the accepted aggregate. Total Smoke attempts: one rejected partial attempt plus one accepted 180/360 run.

Stage ran before that validator-only correction; all saved Stage reports independently reconstruct under final code. No gameplay change occurred after its run, and no extra Stage run was made.

## Continuity, including actual trajectory changes

All **2,829 banked Action #30 Smoke execution references** still authenticate under final validators. Focused/full regressions pass and existing semantic implementations remain intact. Historical artifacts are unchanged.

Runtime occurrence counts in the new Smoke trajectories are not identical: four prior EXECUTED occurrences disappear in three games. These are explicitly preserved in `POST_ACTION_31_CONTINUITY.json`:

- `bebop_rocksteady--donatello:reversed:8022`: Donatello initial object `object-000048` dies on turn 14 in the changed trajectory; its prior counter executions were turns 19 and 23. The candidate correctly classifies this lineage as present-unreached for that fragment.
- `bebop_rocksteady--leonardo:reversed:8025`: Zoo Escapees initial objects `object-000092` and `object-000091` are milled on turn 34 rather than later entering/leaving the battlefield.
- `bebop_rocksteady--splinter:canonical:8034`: Zoo Escapees initial object `object-000051` is milled on turn 3 rather than later entering/leaving the battlefield.

These observations explain reduced runtime exposure without claiming unchanged per-game counts. Prior chains remain reconstructible; no generic execution credit is fabricated to preserve a counter. HQ should review these concrete continuity deltas with the candidate.

## Changed paths and preserved evidence

Production: `src/tmnt_design_studio/card_interpreter07.py`, `engine07.py`, new `mill_three07.py`, `stage002.py`; `smoke01.py` changes only frozen source identities. Tests: new `tests/test_mill_three_action.py`. Attributes: `docs/cardcade/.gitattributes` adds scoped Action #31 text/binary rules.

Fresh artifacts in `docs/cardcade/`, with SHA-256 sidecars:

- `POST_ACTION_31_STAGE_002_RESULTS.json` and `POST_ACTION_31_STAGE_INVENTORY.json`.
- `POST_ACTION_31_SMOKE01_RESULTS.json.gz` and `POST_ACTION_31_SMOKE_INVENTORY.json`.
- `POST_ACTION_31_MILL_TRANSACTIONS.json.gz`: full authoritative evidence for all 17 natural mill games, including 21 complete transactions.
- `POST_ACTION_31_MILL_CONTROLLED_SNAPSHOTS.json`: complete one-transaction fixtures for library sizes 0, 1, 2, 3 and 5; these are focused witnesses, not additional Stage/Smoke games.
- `POST_ACTION_31_CONTINUITY.json`: exact old/new lineages, references and explanations.
- `POST_ACTION_31_SMOKE01_FAILURE.json` and `POST_ACTION_31_SMOKE01_FAILED_VALIDATOR.py.txt`: rejected attempt and exact failed-validator blob `1e274d6caa81c87717d8ddf49bfabfa87c71771e`.
- `POST_ACTION_31_VALIDATION.json`: final code/test identities, results, attempts and exclusions.
- This handoff and its sidecar.

For gzip artifacts, `.json.gz.sha256` authenticates compressed bytes and `.json.sha256` authenticates exact decompressed JSON bytes. The redundant raw Smoke file is removed only after verified compression round-trip. Staged sidecars and source identities are checked before commit.

## Explicit exclusions and gate

No generic mill-N grammar, arbitrary player/quantity/choice scripting, hidden-zone architecture, new zones/exile, simultaneous-zone framework, general transaction framework, dies/reflexive sibling, turn/scheduler/Pilot/deck change, calibration, balance or Prototype 0.3 work. No simulation matrix was broadened. Action #32 remains NOT AUTHORIZED. Calibration remains BLOCKED. Prototype 0.3 remains NOT AUTHORIZED.

Independent HQ review of the exact candidate is required before merge. No self-acceptance or merge is performed.
