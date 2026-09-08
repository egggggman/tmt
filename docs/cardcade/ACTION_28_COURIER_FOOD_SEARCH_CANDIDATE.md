# Action #28: Courier of Comestibles Food search/fallback candidate

Implements Issue #94 from exact base `40135ed92f1f6049e3f14d90c7d64e9077566a40` for independent HQ review. The existing Courier implementation was preserved on `codex/cardcade-action28-courier-food-search`.

Only the frozen self-ETB Oracle fragment is recognized. The authenticated trigger waits for Stack/Priority resolution, offers authoritative Food-subtype library cards, reveals and moves the chosen card to hand, and deterministically shuffles after searching. If no card enters hand, the effect creates exactly one canonical Food token. Declining the search does not shuffle. Source departure preserves a valid pending trigger. Identity, replay, chooser mutation, and serialized branch corruption fail closed.

## Changed paths

- `src/tmnt_design_studio/card_interpreter07.py`: exact semantic recognition.
- `src/tmnt_design_studio/engine07.py`: ETB, Stack/Priority and evidence integration.
- `src/tmnt_design_studio/food_search07.py`: bounded Food search transaction and reconstructive validation.
- `src/tmnt_design_studio/stage002.py`: serialized evidence validation.
- `src/tmnt_design_studio/smoke01.py`: refreshed frozen input identities and added transaction module.
- `tests/test_courier_food_search_action.py`: 53 focused cases.
- `docs/cardcade/.gitattributes` and Action #28 JSON evidence, SHA-256 sidecars, and this handoff.

## Validation

- Prior focused/relevant Stage/Smoke run: 260 passed, as recorded in the preserved witness.
- Resumed Courier suite: 53 passed.
- Resumed full pytest: 1043 passed, 1 skipped. Optional pytest cache writes were denied; tests passed.
- Ruff check, Ruff format check, canonical terminology scan, and git diff --check passed.
- Standalone Smoke completed and its result reconstructed successfully.
- Stage #002: 16 games / 32 executions per matrix, deterministic duplicates, zero invariant violations and runner stops, 16 reconstructed reports.
- Two resumed Stage matrix executions occurred: the first comparison exposed Python tuple versus JSON list representation; the second JSON-normalized comparison matched the preserved result exactly. Including the one preserved matrix, three Stage matrices are accounted for. This does not change the per-matrix 16/32 budget.
- Saved branch snapshots independently reconstruct success, decline, no qualifying card, and search with no selection. SHA-256 sidecars verified.
- Historical `POST_ACTION_28_SMOKE01_FAILURE.json` is retained: it records the earlier frozen-input mismatch, resolved by the preserved hash refresh. The new `POST_ACTION_28_SMOKE01_RESULTS.json.gz` is the successful resumed run.

## Witness and continuity

Courier is EXECUTED in `michelangelo-bebop-rocksteady:canonical:7211`. Inventory: 25 EXECUTED / 5 REACHED-UNSUPPORTED / 134 PRESENT-UNREACHED. No previously executed game/semantic occurrence is lost relative to Issue #93. Zoo Escapees, Stockman, Donatello and Shredder witnesses retain continuity. The remaining unsupported reached occurrences are the two excluded Casey semantics.

Exact object, trigger, event, reveal/movement/shuffle and fallback references are preserved in `POST_ACTION_28_BRANCH_EVIDENCE.json` and `POST_ACTION_28_STAGE_002_WITNESS.json`. Resumed checks are recorded in `POST_ACTION_28_RESUMED_VALIDATION.json`. Candidate SHA and final clean-worktree status are reported in the PR handoff to avoid a self-referential commit hash.

## Review boundary

No Casey implementation, generic tutor grammar, unrelated Food activation, deck/Pilot changes, calibration/balance, Prototype 0.3, broad simulation, GUI, or Action #29. No self-acceptance or merge. Action #29 remains NOT AUTHORIZED.
