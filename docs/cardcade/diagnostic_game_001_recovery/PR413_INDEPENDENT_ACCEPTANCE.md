# PR #413 Independent Capture-Lifecycle Audit

## Verdict: ACCEPT

The independent evidence supports accepting PR #413's bounded capture-lifecycle correction. The two PR #412 failures reproduce against the original PR #411 source and are corrected at the PR #413 tested implementation. No new lifecycle, exception-propagation, terminal-combat, or reconciliation defect was found in the requested synthetic scope.

## Audited identities and environment

- PR #413 published HEAD: `6612ba7ee36d7eeeb2b090a3a7664662d6fcdeac`.
- Tested implementation: `b1c089476b47f032b63d169b7dedcb69d85afaee`.
- Original PR #411 source for RED: `b0c5097d56574321200e210a139a58d0ba320648`.
- Original PR #404 source for historical evidence replay: `67b9bb3083c9f4b2fe02e7fed258c4739581225f`.
- Independent candidate worktree: `C:\projects\tmt\.audit-pr413-independent-6612ba7`.
- RED worktree: `C:\projects\tmt\.audit-pr413-pr411-red`.
- Candidate import verified as `C:\projects\tmt\.audit-pr413-independent-6612ba7\src\tmnt_design_studio\stage002.py` with `PYTHONPATH` pinned to that worktree.
- Python 3.12.10; pytest 8.4.2; Ruff 0.16.1.
- Accepted `main`: `10d2ac80ef5b81b3a209a3133eb0a84633a1f944`.

## Historical RED and correction

Using the original PR #411 module, an independent deterministic probe confirmed both failures:

- After a first failed run bound to game A, a later failing call before binding captured game A's prior fingerprint with `capture_error=None` (`stale_snapshot_attached=True`).
- When `Game.snapshot()` raised an exception whose `__str__` also raised, the capture path raised the formatting `RuntimeError`; the original execution exception was not re-raised and `capture.failure` remained unset.

Against PR #413, the same two named regressions pass. The new call lifecycle clears previous bindings and failure data before running. A failed unbound call has no snapshot and reports the missing binding. The snapshot-capture formatting case records the capture failure and re-raises the identical original exception.

The original PR #406 traceback and wrapper were read without alteration. The historical frame walker chooses the last traceback frame with a local named `game`; in the preserved traceback that is `_checked_action`, which lacks the matching `presence` ledger. The candidate no longer infers ownership from traceback locals.

## Independent regression execution

I inspected the selected node bodies and independently ran the full existing 38-node selection: the 10 capture nodes, six strike/terminal nodes, 11 ordinary priority nodes, and 11 Stage 002 runner/presence/reconciliation nodes. The last node has five parameter cases, yielding **42 test cases**.

Command form, with the exact node list recorded in `CAPTURE_LIFECYCLE_CORRECTION.md` on PR #413:

```powershell
$env:PYTHONPATH = 'C:\projects\tmt\.audit-pr413-independent-6612ba7\src'
$env:PYTHONDONTWRITEBYTECODE = '1'
python -B -m pytest -q $nodes
```

Result: **42 passed, 0 failed, 0 skipped**. Ruff format check and lint passed on the runner, capture tests, and selected runner tests. `git diff --check` passed. `engine07.py` is unchanged from PR #411's accepted terminal-combat engine.

Additional independent probes established:

- Reuse after a successful non-game call followed by an unbound failure produces no snapshot and holds no stale game/presence references.
- Reuse after a failed bound call followed by an unbound failure is covered by the named regression; the previous snapshot does not cross the boundary.
- Duplicate binding is rejected during the active call and yields no snapshot; missing binding also fails closed.
- Same-object overlapping capture is rejected without corrupting the outer lifecycle. A separate nested capture object can fail and snapshot independently while the outer call succeeds.
- Ordinary snapshot failure, unprintable snapshot/finalization errors, an unprintable original exception, traceback formatter failure, and an injected failure in capture bookkeeping all preserve the original execution exception. Captured tracebacks/errors use safe fallback text when formatting fails.
- Runner setup without `diagnostic_capture` propagates its injected exception unchanged; the test stops before the gameplay loop. No complete game or runner gameplay loop was executed.

The actual capture integration test authenticates a created token from the captured snapshot and reconciles it without stops, while checking the exact bound game fingerprint and that capture finalization does not mutate the live presence ledger.

## Historical evidence preservation

Read-only replay used the original PR #404 module at `C:\projects\tmt\.diag001-pr404-67b9bb3\src\tmnt_design_studio\stage002.py`, with the preserved snapshot, manifest, and reconciliation in `C:\projects\tmt\.cardcade-diagnostic001-report\docs\cardcade\diagnostic_game_001\evidence`.

The recomputed manifest and reconciliation exactly equal the saved objects. All nine artifact hashes listed in `artifact_sha256.json` verified. The same three stop records remain: `illegal_mutation` for terminal combat, `silent_approximation` for missing presence evidence, and `silent_approximation` for the disputed execution references. No historical presence was reconstructed and no record was deleted or reclassified.

## Limitations and next gate

This accepts the reusable capture lifecycle at its tested synthetic boundary. It does not test a future one-shot launcher or authorize a diagnostic game. The launcher must create a fresh capture object, wrap exactly one `run_game` call, persist any failure evidence before reuse, and retain its single-run/no-retry safeguards. HQ may next review a non-game launcher dry run; another complete game requires separate authorization.
