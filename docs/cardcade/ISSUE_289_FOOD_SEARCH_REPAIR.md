# Issue 289 — ETB Food-search reconstruction repair

## Decision

**Repair checkpoint: READY.** The defect was reproduced under runtime `dc80bc679e2c0d118f543d12ae4a95661033039058b1525f32e8d076dae8d308`, corrected generically, and validated under repaired runtime `8d873b6ae9527a9274c0d783c90c71f26f5c1302d161e43998eee8c9cd559972`.

**Renewed Baseline 005 calibration: BLOCKED pending separate HQ authorization.** No replacement 4,500-game control was run.

## Root cause

Both preserved failures were validator/reconstruction defects, not gameplay defects. Nested ETB work can occur before the outer `etb_food_search_committed` event; the validator treated those nested `tokens_created`, reveal, movement, and shuffle records as outer actions. The repair retains nested events in the bounded evidence while authenticating each action by its stack/source (and, for movement, selected-object) identity. The existing canonical JSON comparison is preserved, and forged or inconsistent evidence still fails closed.

The exact pre-repair path for both seeds was:

```text
stage002.py:753 run_game
engine07.py:19019 Game.snapshot
engine07.py:18749 _executed_conformance_references
food_search07.py:531 validate_food_search_snapshot_evidence
food_search07.py:451 assertion
ValueError: ETB Food search evidence does not reconstruct
```

The complete pre-failure event-boundary summaries (including outer transaction cursors, source/stack identities, zone counts, and the nested action that was misclassified) are preserved in [the root-cause forensics artifact](ISSUE_289_FOOD_SEARCH_ROOT_CAUSE_FORENSICS.json), SHA-256 `6a191e2928203311c898c9908a9ff478f8a74281b803f01581f35a12aa777c6a`.

## Reproduction and validation

| Fixture | Result after repair |
| --- | --- |
| Raphael/Michelangelo reversed block 3, seed `70854356032484108629752045553328311296264080222857296236996711926358961833742` | completed; repeated serialized snapshots matched |
| Michelangelo/Raphael canonical block 41, seed `61283485696731598188099450771387457581219000296206197647983307541613500950207` | completed; repeated serialized snapshots matched |
| Raphael/Michelangelo diagnostic | 100/100 completed, 0 errors, 50/50 orientation split |

The complete diagnostic machine evidence is preserved in [the JSON artifact](../objective-balance-lab/BASELINE_005_ISSUE289_FOOD_SEARCH_REPAIR_RAPHAEL_MICHELANGELO_DIAGNOSTIC.json) with SHA-256 `fe843e16159f69ed73bfab0940b00d930af6c2eae78e6299e6d93ea12b26e8bf`. The two exact-seed fixtures are in `tests/test_food_search_failure_repair.py`; the focused Food-search suite passed 55 tests and the complete regression passed **2,107 tests, 10 skipped**.

The frozen 172-row ledger and all ten Baseline 005 deck identities remain unchanged. The three prior fail-closed control artifacts remain immutable and are excluded from any future calibration result.

This diagnostic is repair evidence only: its 49–51 result is not a balance conclusion.
