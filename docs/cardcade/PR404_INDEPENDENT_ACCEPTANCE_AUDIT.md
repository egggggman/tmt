# PR #404 Independent Acceptance Audit

## Verdict

**ACCEPT** the bounded PR #404 correction for independent HQ acceptance. The reproduced main-action failure is fixed at the audited commit, the 112-node selection passes independently, and the targeted dispatch challenges found no new engine, pilot, or evidence defect. This verdict does not authorize a complete game, Smoke restart, calibration, merge, or baseline promotion.

## Source and reviewer worktrees

- Authorized starting source / PR #401: `ad2034026d6d37904f66da7ef71874f2306e1571`.
- Audited PR #404 HEAD: `67b9bb3083c9f4b2fe02e7fed258c4739581225f`.
- Candidate reviewer worktree: `C:\projects\tmt\.audit-pr404-independent`, detached at the exact PR #404 HEAD and clean after testing.
- Baseline reproduction worktree: `C:\projects\tmt\.audit-pr404-pr401-red`, detached at the exact PR #401 SHA.
- Audit report/test worktree: `C:\projects\tmt\.audit-pr404-independent-report`, based on PR #404 HEAD; it contains only this report and the reviewer-only test file.
- Accepted `origin/main`: `10d2ac80ef5b81b3a209a3133eb0a84633a1f944`.
- Environment: Python 3.12.10, pytest 8.4.2, Ruff 0.16.1; reused `C:\projects\tmt\.cardcade-fidelity-correction\.venv`.

GitHub metadata reconfirmed PR #401 remains open/draft/unmerged at `ad2034026d6d37904f66da7ef71874f2306e1571`; PR #403 remains open/draft/unmerged at `e369be95986419faf3c829808232030d8b013501`; PR #404 remains open/draft/unmerged at `67b9bb3083c9f4b2fe02e7fed258c4739581225f`. PR #404's three changed paths are its acceptance report, `engine07.py`, and `test_integrated_readiness_audit.py`. Its final HEAD had no associated GitHub Actions workflow runs.

## Historical failure and corrected result

The original PR #403 characterization was retrieved from its audit worktree. Its source test blob is `25989bcb14836d7b9908144286814c56b2377620`, unchanged. On the exact PR #401 source, `test_main_cast_wrapper_raises_on_pending_artifact_cast_trigger` passes by observing the original `ValueError: artifact-cast token trigger requires Priority resolution` after the legal cast has paid and announced. Independently running PR #404's positive `test_main_cast_action_composes_punks_followup_robot_trigger_and_pizza_etb` against PR #401 fails at the same exception. The same positive test passes on PR #404.

The correction is appropriately limited to `Game.execute_main_action`: it announces through the shared spell path, finds the authentic `SPELL_CAST` event for that spell object, and yields to a normal priority window when a Stack trigger references that event. Trigger-free casts still resolve through the prior main-action compatibility path. The `Game.cast()` implementation itself is unchanged.

## Independent 112-node validation

The 112 named nodes recorded by PR #404 were reconstructed from its committed acceptance report and its referenced PR #401 acceptance selections, then executed from the isolated candidate worktree. This included the integrated Punks/Pizza/Robots composition, restricted-mana provenance, Pizza/April/Robots semantics, pilot follow-through, Frog Butler, combat/priority, and historical regressions.

Command form:

```powershell
$env:PYTHONPATH=(Resolve-Path src).Path
$env:PYTHONDONTWRITEBYTECODE='1'
& 'C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\python.exe' -B -m pytest -q --rootdir=. $nodes
```

Result at PR #404 HEAD `67b9bb3083c9f4b2fe02e7fed258c4739581225f`: **117 passed, 0 failed, 0 skipped**. The exact supplemental selection is in `PR403_MAIN_CAST_PRIORITY_CORRECTION_ACCEPTANCE.md`; its 71 inherited nodes are enumerated in `PILOT_FIDELITY_CORRECTION_ACCEPTANCE.md` and `PR399_TARGET_POLICY_CORRECTION_ACCEPTANCE.md`. The original failing characterization was additionally run on the PR #401 worktree, and PR #404's positive node was run against both source revisions.

## Additional independent challenges

Three reviewer-only synthetic tests were added on the separate audit branch and passed (**3 passed, 0 failed, 0 skipped**):

- `test_execute_main_action_dispatches_all_authenticated_cast_triggers_to_active_player_priority`: a legal artifact cast by active player 1 creates two independent Robots triggers bound by identity to the single authentic cast event, opens priority for player 1, gives each player a pass at each resolution epoch, and resolves exactly two tokens.
- `test_main_action_artifact_cast_can_be_countered_after_its_cast_trigger_resolves`: after a main-action Pizza cast's Robots trigger resolves, the opponent gets priority and counters Pizza. The token remains, cast evidence remains, and Pizza's ETB trigger does not occur.
- `test_stale_engine_cast_option_rejection_does_not_mutate_state_or_emit_cast_event`: a formerly legal cast option made stale by a zone change is rejected, with the post-fixture snapshot and event history unchanged.

Existing coverage also verifies trigger-free `execute_main_action` casts and direct `Game.cast()` callers. A source search found no production call site of `Game.cast()`; the engine action path uses `execute_main_action`. The direct wrapper retains its pre-existing immediate-resolution behavior. A direct `Game.cast()` call for a cast that creates a priority-requiring trigger remains outside the wrapper's supported compatibility path; this limitation is unchanged by PR #404 and is not used by Stage 002.

## Priority, ordering, and evidence findings

In the composed action path, the first priority window is opened on the top Robots trigger and starts with the active player. Both players pass before each Stack object resolves. The cast event is emitted once, both simultaneous triggers reference that same event, and Robot creation precedes Pizza's ETB trigger. Pizza then deals four damage to the selected opponent and three to its controller. The test verifies the exact restricted-red production allocation, the final empty Stack and mana pool, authenticated damage references, reconciliation without stop records, and `Game.check_invariants()`.

The counter challenge confirms that the ordinary follow-on priority window exposes the spell for a supported counter action after the cast trigger resolves. The pilot-fidelity regression selection passes unchanged.

## Quality and preserved project evidence

Ruff format check, Ruff lint, and `git diff --check` passed independently for the candidate's changed Python files and the supplemental audit tests. The candidate worktree remained clean.

- Accepted main remains `10d2ac80ef5b81b3a209a3133eb0a84633a1f944`.
- Frozen card snapshot SHA-256: `56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402`.
- Card-data manifest SHA-256: `6b5271af75150a361f77e7b89306c709959dfdf497c448dfdc978e5dc9a17950`.
- Smoke 001 April and Casey deck hashes match run metadata: `684c898760a39c5dfc584206ef4675c49d96cfe6bd419f03f86bd0b8358d09f4` and `0fc0adbb370ecfddad03692a4229a04b23268739914a8f2a004b8e042ff3cebb`.
- Baseline 005 OBL manifest SHA-256: `532bad7e489eb25f3184b5a90487e1361f7a2b19b8c02cac3c4115a0fc3e14bc`.
- All eight files listed in Smoke 001's `artifact_sha256.json` matched their retained hashes. No historical artifact was written.

The historical run metadata also records the older `stage002.py` hash `6281cd933dac15502d20a1d89cf4ae9b79e1bfaa1287bc6372240dd768c1c6f7`; the audited candidate has a different engine file because it includes subsequent authorized engine corrections. This is an expected source-version difference, not a change to the preserved Smoke 001 artifact.

No complete games, Smoke restart, calibration, merges, deck edits, or baseline promotion were performed. The only new files on this audit branch are this report and the supplemental synthetic test module.
