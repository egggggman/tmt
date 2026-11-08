# PR #399 Independent Acceptance Audit

## Audit identity and scope

- Candidate: PR #399, open, draft, and unmerged.
- Published candidate HEAD: `beb5e24e38384b1b0ca0d055240c70e1833e1858`.
- Tested code commit: `278c88245376a4f50017696ca6af73fd5efe85cd`.
- PR #397 comparison HEAD: `29aa3998e06ed1e6b1d399d4a65e18188d9481be`.
- PR #398 original reproduction branch HEAD: `ac857912d7d31f5d0003cde71e6288f162029bf9`.
- Reviewer worktree: `C:\projects\tmt\.audit-pr399-independent`.
- Audit branch: `review/cardcade-pr399-independent-audit`, based on published PR #399 HEAD.
- Red-reproduction comparison worktree: `C:\projects\tmt\.audit-pr399-pr397-red`, detached at PR #397 HEAD.
- Environment: Python 3.12.10, pytest 8.4.2, Ruff 0.16.1, existing environment at
  `C:\projects\tmt\.cardcade-fidelity-correction\.venv`.

PR #397, PR #398, and PR #399 source branches were not changed. Accepted `main` remains
`10d2ac80ef5b81b3a209a3133eb0a84633a1f944`. No complete games, Smoke 001 restart, calibration,
deck or baseline changes, or historical evidence edits were made.

## Original defect reproduction

The original test was retrieved from PR #398's committed branch. Its blob SHA-1 is
`55f30c79866315945bf76ee84b3662290549c9ab`, matching the copied reviewer test file.

At PR #397 HEAD, this exact node failed:

```powershell
$env:PYTHONPATH='C:\projects\tmt\.audit-pr399-pr397-red\src'
& 'C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\python.exe' -B -m pytest -q tests/test_pr397_independent_audit_repro.py::test_pilot_executes_the_artifact_followup_that_justified_punks_mana
```

Result: **1 failed**. The unrelated `{1}` ability consumed Punks' production lot as
`activated_ability`; the advertised artifact remained in hand.

At PR #399, the corrected regression node passed:

```powershell
$env:PYTHONPATH='C:\projects\tmt\.audit-pr399-independent\src'
& 'C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\python.exe' -B -m pytest -q tests/test_pr397_independent_audit_repro.py::test_pilot_executes_the_artifact_followup_that_justified_punks_mana
```

Result: **1 passed**. The test verifies the artifact leaves the hand, the unrelated activation
is not announced, and the consumed allocation references the exact Punks production event
under `artifact_spell`.

## Independent named regression selection

The same 54 explicitly named regression nodes in
`PILOT_FIDELITY_CORRECTION_ACCEPTANCE.md` were independently run, expanding to 56 cases. The
selection also included:

- The 3 Pizza outcome cases and the corrected Punks reproduction in
  `tests/test_pr397_independent_audit_repro.py`.
- The 9 named payment-planning purity, reconciliation, Frog Butler, and invalid Pizza target
  nodes listed in PR #398's audit report.
- The 3 new follow-up activation, stale descriptor, and continuation-bound nodes in
  `tests/test_pilot_fidelity_correction.py`.

This is 68 named nodes total. With parameter expansion, the independent result at published
PR #399 HEAD was **72 passed, 0 failed, 0 skipped**:

```powershell
$env:PYTHONPATH='C:\projects\tmt\.audit-pr399-independent\src'
# $nodes contains the 54 nodes listed in PILOT_FIDELITY_CORRECTION_ACCEPTANCE.md,
# plus the 14 supplemental nodes listed above.
& 'C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\python.exe' -B -m pytest -q @nodes
```

The selected coverage includes Pizza outcomes, April cast history and end-step draw, Ravenous
Robots artifact-cast triggers, restricted spell and activated-ability payments, Frog Butler
compatibility, planning purity, priority/Stack behavior, payment provenance, snapshot
reconciliation, the original Punks follow-up, and the three new follow-up checks. No unrestricted
pytest selection or complete-game entry point was run.

## Additional target-choice challenge

The 68 named nodes do not test target choice when an advertised artifact cast expands into
multiple legal `CAST` options. A reviewer-only reproduction is preserved in
`tests/test_pr399_independent_audit_repro.py::test_punks_followup_preserves_existing_target_policy_for_targeted_casts`.

The fixture uses a synthetic `{R}` Artifact Instant with the engine-supported
`DAMAGE_3_OPPOSING_CREATURE` cast program, Purple Dragon Punks, and two opposing creatures. The
5/5 is created before the 1/1. After mana production, the engine offers both target options for
the advertised spell object. A control using the existing `AcceptancePilot` damage-stage policy
selects the 1/1 and would kill it with three damage. The same fixture through
`_run_main_action_stages` on PR #399 selects the first matching `CAST` option instead, dealing
three damage to the 5/5 and leaving the 1/1 untouched.

The reproduction passes on PR #397 and fails on PR #399 at the assertion that the 1/1 should
leave the battlefield. Therefore this is a behavior introduced by the correction, rather than
the original failure. Engine legality is preserved: the chosen target is one of the currently
offered targets. The pilot's existing choice policy is bypassed because the follow-up descriptor
identifies the spell object but not a target, and `_matching_main_followup` returns the first
matching option without asking the pilot to choose among matching options.

The frozen card-data snapshot identifies the real Manhole Missile as an Instant, not an Artifact;
the reproduction uses a synthetic Artifact type line and does not claim that this exact card
exists in the frozen decks. The concern is still within the generic path PR #399 advertises:
`_mana_followups_for` supports artifact cards with the engine's targeted damage cast kinds, and
the matching stage can receive multiple legal target variants for the same object ID.

The bounded correction would preserve the matching spell object while delegating among its
freshly legal target variants to the existing pilot choice policy. No engine legality or payment
change appears necessary.

## Verdict

**REWORK.** The main Punks defect is fixed and its authenticated restricted-mana payment is
independently verified. All 68 named regression nodes pass, including the April, Robots, Pizza,
payment, priority, and evidence checks. However, the additional targeted-artifact reproduction
shows that follow-up matching bypasses an existing pilot target-selection policy for a supported
generic action path. Preserve the correction, but address this target-choice handoff before
acceptance. No candidate source was modified during this audit.
