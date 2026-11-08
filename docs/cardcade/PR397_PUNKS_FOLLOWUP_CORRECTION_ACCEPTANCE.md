# PR #397 Purple Dragon Punks Follow-Up Correction

## Source identity

- Starting candidate: PR #397 branch `review/cardcade-pilot-fidelity-correction` at `29aa3998e06ed1e6b1d399d4a65e18188d9481be`.
- Implementation branch: `review/cardcade-punks-followup-correction`.
- Worktree: `C:\projects\tmt\.cardcade-punks-followup-correction`.
- Tested code commit: `278c88245376a4f50017696ca6af73fd5efe85cd`.
- Parent/base branch: `review/cardcade-pilot-fidelity-correction`.
- The implementation commit contains `[skip ci]`.
- The PR #398 independent audit branch and PR #397 source branch were not modified.

## Preserved failure and correction

At the starting PR #397 SHA, the preserved independent test
`tests/test_pr397_independent_audit_repro.py::test_pilot_executes_the_artifact_followup_that_justified_punks_mana`
failed. Punks' option advertised a payable artifact creature cast, but after red mana
production the next `activate` decision selected an unrelated `{1}` ability. That ability
consumed the Punks production lot as an `activated_ability` payment, and the artifact stayed
in hand.

The independent test file was copied unchanged before implementation and run at the starting
SHA to establish the red result: **1 failed**, with `artifact.zone == "hand"` instead of
`"former"`. The audit branch retains its original independent report and reproduction.

The Stage 002 main-action driver now carries the selected option's engine-generated
`mana_followups` into the next bounded activation recheck. It re-enumerates legal main actions,
then chooses a current `CAST` or `ACTIVATE_ABILITY` option matching the descriptor's object
identity and, for abilities, its Oracle fragment. The selected option still goes through the
normal engine execution and payment validation. If the advertised follow-up is stale or no
longer legal, the driver drops the hint and uses the existing pilot policy. The existing
three-selection continuation cap remains in place. No card, deck, or opponent-specific rule
was added.

The preserved reproduction now verifies that the exact Punks production event pays for the
artifact spell, the unrelated ability is not announced, and the artifact leaves the hand.
Additional tests cover a matching activated ability and its payment lineage, stale descriptors,
and the continuation limit.

## Validation

Environment: Python 3.12.10, pytest 8.4.2, Ruff 0.16.1, using the existing environment at
`C:\projects\tmt\.cardcade-fidelity-correction\.venv`. `PYTHONPATH` pointed to this worktree's
`src` directory. No environment was rebuilt or modified.

The selection retained the 54 explicit regression node IDs from
`PILOT_FIDELITY_CORRECTION_ACCEPTANCE.md` (56 cases after parameter expansion), plus:

- The three parameter cases and preserved Punks reproduction in
  `tests/test_pr397_independent_audit_repro.py` (4 cases).
- Nine independent planning-purity, payment/reconciliation, Frog Butler, and invalid Pizza
  target nodes listed in `PR397_INDEPENDENT_ACCEPTANCE_AUDIT.md`.
- Three new nodes in `tests/test_pilot_fidelity_correction.py` for matching activation,
  unavailable follow-up, and bounded continuation.

At tested source SHA `278c88245376a4f50017696ca6af73fd5efe85cd`, the selection returned
**72 passed, 0 failed, 0 skipped**.

Commands, run from the implementation worktree:

```powershell
$env:PYTHONPATH='C:\projects\tmt\.cardcade-punks-followup-correction\src'
& 'C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\python.exe' -B -m pytest -q @nodes
& 'C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\ruff.exe' format --check src/tmnt_design_studio/stage002.py tests/test_pilot_fidelity_correction.py tests/test_pr397_independent_audit_repro.py
& 'C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\ruff.exe' check src/tmnt_design_studio/stage002.py tests/test_pilot_fidelity_correction.py tests/test_pr397_independent_audit_repro.py
git diff --check HEAD^ HEAD
```

Results: Ruff format check passed (3 files already formatted), Ruff lint passed, and
`git diff --check` passed. No complete games, Smoke 001 restart, calibration, deck changes,
merge, or historical evidence modifications were performed.

## Changed files

- `src/tmnt_design_studio/stage002.py`
- `tests/test_pilot_fidelity_correction.py`
- `tests/test_pr397_independent_audit_repro.py`
- `docs/cardcade/PR397_PUNKS_FOLLOWUP_CORRECTION_ACCEPTANCE.md`

## Handoff

This report documents the implementation and its focused evidence. It does not claim
independent acceptance. The candidate is returned to HQ for the requested independent re-audit.
