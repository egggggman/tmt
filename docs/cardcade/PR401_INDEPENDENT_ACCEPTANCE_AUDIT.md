# Independent Acceptance Audit — PR #401

## Verdict

**ACCEPT.** The candidate corrects both the PR #398 main-phase follow-up failure and the PR #400 target-policy regression in the reviewed supported action paths. The original 71 named regression nodes passed independently, and two additional reviewer-only probes passed. No candidate source was changed.

## Source identities and isolation

- Repository: `egggggman/tmt`.
- Candidate PR #401 published HEAD: `ad2034026d6d37904f66da7ef71874f2306e1571`.
- Candidate tested implementation commit: `d7a99aced66cd94998298356315d335f307017fe`.
- PR #401 is open, draft, and unmerged; its base is PR #399's branch at `beb5e24e38384b1b0ca0d055240c70e1833e1858`.
- Independent reviewer worktree: `C:\projects\tmt\.audit-pr401-independent`, branch `review/cardcade-pr401-independent-audit`.
- Historical PR #397 reviewer worktree: `C:\projects\tmt\.audit-pr401-pr397`, detached at `29aa3998e06ed1e6b1d399d4a65e18188d9481be`.
- Historical PR #399 reviewer worktree: `C:\projects\tmt\.audit-pr401-pr399`, detached at `beb5e24e38384b1b0ca0d055240c70e1833e1858`.
- Original PR #398 reproduction source: PR #398 audit branch `ac857912d7d31f5d0003cde71e6288f162029bf9`; test blob `55f30c79866315945bf76ee84b3662290549c9ab`.
- Original PR #400 reproduction source: PR #400 audit branch `aa73070b0dd29a64eb4c489c1a629e611de7f7bd`; test blob `8cdaeea2b8c9af7d409abe1a33d5971ce7747b46`.
- Python 3.12.10, pytest 8.4.2, Ruff 0.16.1. The existing environment at `C:\projects\tmt\.cardcade-fidelity-correction\.venv` was reused.

The reproduction files were checked against their recorded Git blob identities before running. PR #401's implementation, accepted main, prior PR branches, decks, Baseline 005, Smoke 001 artifacts, and historical evidence were not modified.

## Historical failures and corrected results

### PR #398 main-phase follow-up

At PR #397 HEAD `29aa3998e06ed1e6b1d399d4a65e18188d9481be`,
`tests/test_pr397_independent_audit_repro.py::test_pilot_executes_the_artifact_followup_that_justified_punks_mana`
fails: after Purple Dragon Punks produces restricted red mana, an unrelated `{1}` activated ability consumes that lot and the advertised artifact stays in hand.

At PR #401 HEAD, the same preserved reproduction passes. The artifact is cast, the restricted allocation refers to Punks' production event and uses `artifact_spell`, and the unrelated ability is not announced.

### PR #400 target-policy regression

At PR #399 HEAD `beb5e24e38384b1b0ca0d055240c70e1833e1858`,
`tests/test_pr399_independent_audit_repro.py::test_punks_followup_preserves_existing_target_policy_for_targeted_casts`
fails. The existing pilot's policy selects a lethal 1/1 among two legal targets, but the follow-up path chooses the first listed target, a 5/5.

At PR #401 HEAD, the same preserved reproduction passes. The runner filters the current engine-issued options to the advertised spell and lets the existing pilot policy select among its legal target variants. The test fixture is a synthetic Artifact Instant using the supported targeted-damage path; it establishes generic runner behavior and does not claim that Smoke 001's frozen Manhole Missile card is an Artifact.

## Independent regression execution

The 71 named nodes were reconstructed from the exact lists in:

- `docs/cardcade/PILOT_FIDELITY_CORRECTION_ACCEPTANCE.md` (54 nodes).
- `docs/cardcade/PR399_TARGET_POLICY_CORRECTION_ACCEPTANCE.md` (14 supplemental nodes plus 3 target-policy nodes).

At candidate HEAD `ad2034026d6d37904f66da7ef71874f2306e1571`, the 71 nodes returned **75 passed, 0 failed, 0 skipped**. The two extra reviewer-only nodes below also passed, for a combined **73 named nodes, 77 passed cases, 0 failed, 0 skipped**. No complete-game runner or unselected module was run.

Reviewer-only nodes:

- `tests/test_pr401_independent_audit_repro.py::test_followup_defers_after_pass_and_selects_same_spell_at_later_cast_stage`
- `tests/test_pr401_independent_audit_repro.py::test_pilot_passes_do_not_speculatively_spend_preferred_followup_mana`

The first probe exposes only the currently legal matching spell variants and PASS after mana production, has the pilot PASS at the damage stage, then verifies that the same spell remains preferred at the destroy stage and the existing target policy's selected 1/1 target is used. It also verifies no unrelated activation occurs and the payment consumes the exact Punks lot as an artifact spell.

The second probe has the pilot PASS at every cast stage. The spell remains in hand, the opponent's creatures remain unchanged, restricted mana remains available for `artifact_spell`, and no unrelated ability is announced. Existing planning-purity and payment-authenticity nodes passed in the 71-node selection.

The 71-node regression coverage includes Pizza target and terminal outcomes, April cast history and end-step draw, Ravenous Robots artifact triggers, restricted spell and ability payment, Frog Butler, Punks planning purity, the three-attempt continuation bound, priority/Stack behavior, and snapshot/reconciliation provenance.

## Commands and checks

The tests ran from the independent candidate worktree with its `src` directory on `PYTHONPATH`:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONPATH='C:\projects\tmt\.audit-pr401-independent\src'
# $nodes are the exact 71 node IDs in the two acceptance reports above.
& 'C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\python.exe' -B -m pytest -q @nodes
```

Result for that 71-node command: **75 passed, 0 failed, 0 skipped**. The two named reviewer-only nodes were then run together and returned **2 passed**; the final combined invocation of all 73 named nodes returned **77 passed**.

Reviewer probe checks:

```powershell
& 'C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\ruff.exe' format --check tests/test_pr401_independent_audit_repro.py
& 'C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\ruff.exe' check tests/test_pr401_independent_audit_repro.py
git diff --check
```

Ruff format check passed, Ruff lint passed, and `git diff --check` passed. The reviewer test file is the only added test artifact in this audit branch; candidate implementation files remain untouched.

## Challenge findings and limits

- **Multiple target variants:** passed through the preserved PR #400 reproduction; target choice remains with the existing pilot policy.
- **Single-target and untargeted casts:** covered by the existing selected target-policy nodes and passed.
- **Advertised spell identity and unrelated actions:** matching is based on the advertised descriptor and fresh engine action identity; the selected regression confirms unrelated options do not preempt a still-legal matching spell.
- **Activated-ability follow-up, stale descriptors, and three-attempt bound:** existing named tests passed.
- **Deferral and PASS:** the two added reviewer probes passed. A declined cast-stage choice retains the preferred spell for the next existing cast stage; after all cast stages decline, no speculative payment or unrelated ability execution occurs in that Stage 002 pass.
- **Fresh legality:** the tested runner path re-enumerates actions after mana production and executes the current engine-issued option. Payment validation remains engine-owned.
- **Stale hints:** the selected stale-descriptor regression verifies the matcher yields no stale action and normal current options can resume. The immediate Punks mana ability does not yield priority between preview and the next main-action enumeration, so an asynchronous state change in that narrow interval was not simulated.

The audit is synthetic and bounded to the engine-supported action paths. It does not establish full-game strategic quality or semantics for unsupported card effects. No complete games, smoke runs, calibration, deck revisions, merges, or historical artifact modifications were performed.

## Recommendation

**ACCEPT** PR #401 for the stated target-selection regression and previously corrected Punks follow-up behavior. This independent verdict does not authorize integration, merge, complete-game execution, or calibration; HQ retains those decisions.
