# Cardcade Safe CI Workflow Candidate — Safety Report

**Status:** Prepared on unpublished branch `safety/cardcade-safe-ci-deployment`; awaiting independent review. No Actions run or dispatch has occurred.
**Reviewed source commit:** `21dd5152b235c2355f1b3f182d223660f1fcdde4` (PR #377).
**Scope:** Deterministic non-game checks only.

## Workflow candidate

The workflow is installed at `.github/workflows/cardcade-safe-validation.yml` on this unpublished branch based on `origin/main` at `1454e657310c4e5ffc8e3468a8da6ff1ccc3a6de`. Its only trigger is `workflow_dispatch`; it will not start on branch pushes or PR events. It is not yet present on `main`, so it is not normally dispatchable. The exact node list and validator are under `.github/workflow-candidates/`. PR #377 and its branch/history were not changed.

The candidate uses only `workflow_dispatch`, requires the reviewed full source commit SHA `21dd5152b235c2355f1b3f182d223660f1fcdde4`, rejects dispatch from a non-default branch, uses `contents: read`, disables checkout credential persistence and uv caching, and runs on `ubuntu-24.04`. It checks out the default-branch workflow guard separately from the requested source commit. It invokes `uv sync --locked --dev`, Ruff formatting and lint, then pytest collection and execution with only the 28 literal node IDs below. It contains no push, pull-request, schedule, `workflow_call`, or unrestricted pytest trigger/command.

`actions/setup-python` is pinned to full SHA `5fda3b95a4ea91299a34e894583c3862153e4b97` (`v7.0.0`). The SHA is the verified release commit shown by the [official setup-python v7.0.0 release](https://github.com/actions/setup-python/releases/tag/v7.0.0) and its [commit page](https://github.com/actions/setup-python/commit/5fda3b95a4ea91299a34e894583c3862153e4b97). The other external actions remain pinned to full commit SHAs.

## Exact test selection

The candidate manifest lists 28 fully qualified node IDs: 17 Does Machines Level 3 tests, 6 selected Level 2 tests, and 5 Stage 002 authentication test cases (including both parameter cases). Full IDs are in `.github/workflow-candidates/cardcade-safe-nodeids.txt`.

The exact selection is:

```text
tests/test_does_machines_level_three.py::test_level_three_activation_is_interpreted_from_the_card_fragment
tests/test_does_machines_level_three.py::test_level_two_exposes_level_three_action_and_pays_five_mana
tests/test_does_machines_level_three.py::test_insufficient_mana_rejects_level_three_without_payment
tests/test_does_machines_level_three.py::test_level_three_trigger_resolves_for_noncreature_and_creature_artifacts[Sewer-veillance Cam]
tests/test_does_machines_level_three.py::test_level_three_trigger_resolves_for_noncreature_and_creature_artifacts[Fugitive Droid]
tests/test_does_machines_level_three.py::test_level_three_effect_state_is_deterministic_and_persists_after_cleanup
tests/test_does_machines_level_three.py::test_level_three_trigger_does_not_stack_without_a_legal_artifact_target
tests/test_does_machines_level_three.py::test_level_three_targeted_equipment_becomes_robot_and_detaches
tests/test_does_machines_level_three.py::test_level_three_vehicle_animation_sets_zero_base_stats_before_counters
tests/test_does_machines_level_three.py::test_level_three_counter_placement_uses_michelangelo_replacement
tests/test_does_machines_level_three.py::test_level_three_trigger_skips_resolution_when_its_target_becomes_illegal[leaves]
tests/test_does_machines_level_three.py::test_level_three_trigger_skips_resolution_when_its_target_becomes_illegal[controller]
tests/test_does_machines_level_three.py::test_level_three_trigger_skips_resolution_when_its_target_becomes_illegal[not_artifact]
tests/test_does_machines_level_three.py::test_level_three_trigger_resolves_after_source_leaves_play
tests/test_does_machines_level_three.py::test_newly_animated_artifact_remains_summoning_sick_and_cannot_attack
tests/test_does_machines_level_three.py::test_animated_artifact_can_block_as_a_creature
tests/test_does_machines_level_three.py::test_animation_preserves_types_counters_and_temporary_base_stat_modifier
tests/test_does_machines_level_two.py::test_does_machines_level_two_and_recovery_text_are_interpreted
tests/test_does_machines_level_two.py::test_class_starts_at_level_one_and_pilot_gets_one_legal_level_action
tests/test_does_machines_level_two.py::test_insufficient_mana_prevents_level_advancement
tests/test_does_machines_level_two.py::test_level_two_recovery_returns_only_up_to_two_artifacts_in_order
tests/test_does_machines_level_two.py::test_recovery_is_unavailable_before_level_two_and_zero_targets_are_safe
tests/test_does_machines_level_two.py::test_level_state_and_recovery_event_replay_deterministically
tests/test_stage002_runner.py::test_genuine_transaction_authenticates_executed_class
tests/test_stage002_runner.py::test_fabricated_execution_identity_fails_closed_without_promotion[evidence_id-fabricated]
tests/test_stage002_runner.py::test_fabricated_execution_identity_fails_closed_without_promotion[evidence_kind-wrong-kind]
tests/test_stage002_runner.py::test_semantic_key_and_source_lineage_without_transaction_are_insufficient
tests/test_stage002_runner.py::test_real_transaction_cannot_be_borrowed_by_another_source
```

The 17 Level 3 tests cover action availability and payment, insufficient mana, both artifact kinds, effect cleanup/replay, absent legal target, Equipment detachment, vehicle base statistics, replacement effects, target leaving/changing controller/losing artifact type, source leaving after trigger, summoning sickness, blocking, and preserved characteristics/stat modifiers. Stage 002 IDs cover genuine transaction authentication and three fail-closed/lineage cases (one is parameterized twice).

The exact node manifest SHA-256 is `5b635cb8d9d00a6635158291aef635b71aa5edaeb7b2bea825699e368286a11b`; the validator rejects a changed manifest as well as changed test modules.

## Fail-closed safety gates

- The validator requires exactly 28 unique, explicit function node IDs and rejects wildcard/file-level selectors.
- It checks all three selected test modules against reviewed SHA-256 fingerprints and verifies each selected function exists in AST. Any test-source change requires re-review and updated fingerprints.
- The pytest `--collect-only` pass uses the same explicit node list and fails before test execution if a node ID no longer resolves. Execution uses that same list, never a directory, file-only selector, or bare `uv run pytest`.
- A small AST denylist rejects direct calls from selected test functions to known full-game/batch/calibration APIs. The source fingerprints are the primary guard against changed indirect behavior; this is a reviewed fixed selection, not a general-purpose sandbox.
- The unrestricted existing `.github/workflows/test.yml` remains unchanged.

## Reproducibility and records

Python is constrained to the 3.12 minor line (`python-version: '3.12'`); the actual patch version is recorded at runtime. Dependencies are installed only with `uv sync --locked --dev`; uv is explicitly set to 0.13.5. The workflow records the source SHA, Python/pytest/Ruff/uv versions, locked dependency tree, format/lint outcomes, and pytest output in the run log/summary. The JUnit XML is generated in the runner workspace but is not uploaded as an artifact. The lockfile makes package resolution repeatable for a given platform; Python patch and hosted-runner image versions can change, so the actual versions are recorded.

These validation sets are distinct and neither is GitHub-hosted CI:

| Evidence set | Runtime and command scope | Result |
|---|---|---|
| Targeted workstation suite | Local Python 3.13; broader targeted non-game suite | **53 passed, 1 complete-game test deselected**, zero failures/skips; Ruff format/lint passed. |
| Explicit safe-CI selection | Local Python 3.12.10, pytest 8.4.2; exactly the 28 node IDs in the manifest | **28 passed**, zero failures/skips; Ruff format/lint passed locally. |
| GitHub Actions for the candidate | Not run; candidate remains outside `.github/workflows` | **No GitHub CI pass exists.** |

Older `Test` workflow failures on an earlier PR head are not results for either current validation set.

The recorded SHA-256 values are:

| Test module | SHA-256 |
|---|---|
| `tests/test_does_machines_level_three.py` | `0dbcfd5b c22b3664 eba883d7 c04707ab 0bf9d526 c3f0c231 bb78d1fc aec86262` (remove spaces) |
| `tests/test_does_machines_level_two.py` | `010436e3eb70750ceb5c70d8c3d77d8b2cf4ef72ca88f6f443d2d7672b160f62` |
| `tests/test_stage002_runner.py` | `27483a3a139dbce2743d98da265560d0ed61a262755f10776c59cc8894c6507f` |

> Spaces above are only visual grouping; remove them to obtain the exact 64-character SHA-256 value.

## Safe publication and merge procedure

The existing `.github/workflows/test.yml` runs on both `push` and `pull_request` and invokes unrestricted `uv run pytest`. The following sequence suppresses those events without changing that workflow. HQ confirmed that `main` requires PRs and has no required status checks; skipped checks therefore do not block the required PR flow. The read-only repository settings response reports `allow_squash_merge=true`, `squash_merge_commit_title=COMMIT_OR_PR_TITLE`, and `squash_merge_commit_message=COMMIT_MESSAGES`. The workflow itself has no push or pull-request trigger.

Proposed commit/PR title: `ci(cardcade): add manual safe validation workflow [skip ci]`.

1. After independent review and separate HQ publication authorization, push the local commit with `[skip ci]` in its subject. Ensure any later commit pushed to this branch also has `[skip ci]`. GitHub applies the marker to `push`; the PR head marker suppresses the existing `pull_request` workflow when the PR is opened and updated. Do not treat this marker as proof a required check passed. See [GitHub’s skip-workflow guidance](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/skip-workflow-runs).
2. Open the workflow-only PR with the same `[skip ci]` title and verify the existing `Test` workflow did not start. HQ has confirmed there are no required status checks, so the skipped workflow's pending status is not a configured merge requirement. If that setting changes or GitHub starts the existing workflow, stop and cancel/report; do not remove the marker to make checks run.
3. Use **Squash and merge**. Before executing the separately authorized merge, set the squash commit title to `ci(cardcade): add manual safe validation workflow [skip ci]` and its commit message to include `[skip ci]`. Repository settings allow squash. GitHub's merge API accepts explicit `commit_title` and `commit_message`, so the resulting default-branch commit can be made to retain the marker; do not rely on the default generated message. This suppresses the existing workflow's `push` event on the resulting commit. No merge is performed in this preparation step. References: [squash merge message settings](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/configuring-commit-squashing-for-pull-requests) and [merge API parameters](https://docs.github.com/en/rest/pulls/pulls#merge-a-pull-request).
4. After merge, verify the resulting `main` commit message contains `[skip ci]` and that no unrestricted `Test` run was queued by PR creation, later pushes, or merge. The safe workflow has only `workflow_dispatch`, and it becomes normally dispatchable only after the workflow exists on the default branch. Dispatch it only after a separate HQ authorization, from `main`, with source SHA `21dd5152b235c2355f1b3f182d223660f1fcdde4`; verify that exact SHA and the 28 selected IDs in the run. See [GitHub’s manual-run requirements](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow).

**No bypass is required under the confirmed settings.** The branch requires a PR but not checks, and the explicitly titled squash commit preserves `[skip ci]`. If either condition changes, or the exact merge title/message cannot be set, stop before publication: the push or pull-request event could otherwise launch unrestricted pytest. No branch protection is to be bypassed.

## Remaining limitations

- Candidate has not been pushed, opened as a PR, merged, activated, or executed in GitHub Actions; no claim is made that CI passed.
- `python-version: '3.12'` selects the available patch release in that minor line. Exact patch pinning would require an explicit policy update and version maintenance.
- Test-module hash changes intentionally stop the workflow until an independent review refreshes the fingerprints and node list.
- The denylist catches direct named API calls; the reviewed hashes and literal IDs provide the stronger guard. This does not replace a security review of a future test change.
- The setup-python action is now immutably pinned, but Python 3.12 selects the current patch release and the hosted runner image can change.
- The no-required-check setting is HQ-confirmed; a future merge must explicitly preserve `[skip ci]` on the squash commit. This candidate does not modify `main`, merge PR #377, or alter the existing unrestricted workflow.

## Verdict

**Prepared for independent review; publication and dispatch remain unauthorized.**
