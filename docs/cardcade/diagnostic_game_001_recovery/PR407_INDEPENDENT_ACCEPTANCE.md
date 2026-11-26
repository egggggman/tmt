# PR #407 Independent Acceptance Audit

## Verdict: ACCEPT

This report independently accepts the bounded terminal-combat correction at tested implementation SHA `a33f0369a4c56be8ce85f3863f3b7e2fbac220ba`. The published PR head is `fcbe5fbf9419f246663a29467797ed79df57433f`; its only changes after the tested commit are documentation, and the engine and selected test files are identical.

## Source and reproduction

- Original source: `67b9bb3083c9f4b2fe02e7fed258c4739581225f` (PR #404).
- Corrected source tested: `a33f0369a4c56be8ce85f3863f3b7e2fbac220ba`.
- Published source checked: `fcbe5fbf9419f246663a29467797ed79df57433f`.
- Reviewer worktree: `C:\projects\tmt\.audit-diag001-terminal-pr407-fcbe`.
- Python 3.12.10; pytest 8.4.2; Ruff 0.16.1.
- Before pytest, `PYTHONPATH` was pinned to the reviewer worktree's `src`; the imported `engine07.py` resolved from that exact worktree.

The historical RED reproduction was rerun against `67b9bb3`: `tests/test_strike_damage_steps.py::test_first_step_game_end_is_coherent_without_postcombat_transition` failed with the reported `ValueError: cannot advance a terminal game`, raised when lethal first-strike damage continued into `transition_to(END_OF_COMBAT)`. This matches the PR #406 post-lethal exception.

The correction returns from combat-damage continuation once terminal state is established and Stack/Priority work is empty. `transition_to()` retains its terminal-state rejection. The return does not fabricate a post-terminal transition.

## Independent validation

Inspected every selected test body before execution. The 28 named nodes are synthetic fixtures; the integrated Punks → Pizza → Ravenous Robots composition uses ordinary engine actions and does not invoke a complete-game runner.

Exact selection is documented in `docs/cardcade/diagnostic_game_001_recovery/TERMINAL_FIX.md` on PR #407. It covers:

- First-strike and regular lethal damage, including damage, loss and resolution ordering, winner/life totals, empty Stack, no priority, invariants, duplicate-resolution rejection and prohibited post-terminal transitions.
- Combat-step sequencing, removal at the first-strike boundary, no-strike compatibility, later turn/combat state, and failed-transition mutation safety.
- All 11 ordinary priority-window nodes and terminal snapshot contract.
- Four integrated spell/trigger/priority compatibility nodes, three Pizza outcome cases, Punks follow-through, April cast-history authentication and Ravenous Robots cast-event compatibility.

Command: `python -B -m pytest -q` with the 28 explicit node IDs from the PR #407 report.

Result: **30 passed, 0 failed, 0 skipped**.

Additional non-game exercise of the Stage 002 combat-resolution wrapper around lethal damage returned terminally with no conformance stops; the invariant check passed and only one `player_lost` event was present.

The two changed Python files passed Ruff 0.16.1 format check and lint. `git diff --check` passed on the candidate.

## Limitations

This verdict accepts the bounded engine correction only. It does not establish full-game readiness or clear the independent evidence-capture blocker in PR #408. No complete game, smoke, calibration, merge, or deck operation was performed for this audit.

The root checkout's accepted `origin/main` remained `10d2ac80ef5b81b3a209a3133eb0a84633a1f944`; PR #407 remains draft and unmerged.
