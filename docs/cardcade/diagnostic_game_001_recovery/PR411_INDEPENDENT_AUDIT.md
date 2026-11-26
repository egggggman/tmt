# PR #411 Independent Evidence-Capture Audit

## Verdict: REWORK

The explicitly bound capture path fixes the original PR #406 presence omission under its tested one-call usage. Independent validation passed all requested baseline tests, but two adversarial cases show the capture API can still misattribute or lose failure evidence. It is not ready to back a new diagnostic game until those cases fail closed while preserving the original exception.

## Source identity and environment

- Candidate published HEAD: `b0c5097d56574321200e210a139a58d0ba320648`.
- Tested implementation source: `c1f889c4fe9ae0db44940ab36fcdb192626d8ba2`.
- Candidate branch: `fix/cardcade-diagnostic-evidence-capture`.
- Candidate reviewer worktree: `C:\projects\tmt\.audit-pr411-independent-b0c5097`.
- Imported `stage002.py`: `C:\projects\tmt\.audit-pr411-independent-b0c5097\src\tmnt_design_studio\stage002.py`, verified with `PYTHONPATH` pinned to that worktree.
- Historical game engine source: PR #404 at `67b9bb3083c9f4b2fe02e7fed258c4739581225f`.
- Python 3.12.10; pytest 8.4.2.
- Accepted main remained `10d2ac80ef5b81b3a209a3133eb0a84633a1f944`; PR #407 remained `fcbe5fbf9419f246663a29467797ed79df57433f`.

## Historical RED and current behavior

The preserved PR #406 traceback contains the failing path `run_game` → `_resolve_combat_damage_steps` → `_checked_action` → `Game.resolve_combat_damage` → terminal transition rejection. The historical `run_once.py` walks the traceback outer-to-inner and keeps overwriting `frame` for every local named `game`. The last such frame is `_checked_action`, which has a `game` local but no matching `presence` local. Its exception handler therefore snapshots the wrong frame's state and omits `stage002_presence`.

I independently ran a deterministic nested-call reproduction of that exact selector. It selected `_checked_action`; the selected game was not the runner game and `presence` was unavailable. In the candidate, `run_game` explicitly binds its game and presence ledger to `DiagnosticExecutionCapture`, and the nested synthetic failure captured the bound game while re-raising the identical exception object.

## Independent baseline test results

Inspected the selected test bodies and ran the candidate's complete 32-node selection at implementation SHA `c1f889c4fe9ae0db44940ab36fcdb192626d8ba2`:

```powershell
$env:PYTHONPATH = 'C:\projects\tmt\.audit-pr411-independent-b0c5097\src'
$env:PYTHONDONTWRITEBYTECODE = '1'
python -B -m pytest -q <all 32 named nodes in EVIDENCE_CAPTURE_CORRECTION.md>
```

Result: **36 passed, 0 failed, 0 skipped**. This includes all four capture tests, six strike-damage tests, all 11 ordinary-priority nodes, and 11 Stage 002 runner/presence/reconciliation nodes (one has five parameter cases).

Additional positive checks:

- The injected `run_game` exception occurs in setup before the gameplay loop. The saved snapshot fingerprint matches the bound game; its original presence rows are preserved; its created token row matches the token event; `_authoritative_execution_index` and `reconcile_snapshot` authenticate it with zero stop records.
- Missing and duplicate bindings fail closed in the named tests. An ordinary `Game.snapshot()` failure records `snapshot=None` and `capture_error="RuntimeError: snapshot failed"`, then re-raises the original execution exception.
- An unprintable original execution exception remains the exception re-raised; the candidate uses a placeholder for its message/traceback.
- The no-capture `run_game` opt-out path propagated an injected setup exception unchanged. The test stopped before gameplay began.
- The candidate's `engine07.py` is unchanged from PR #407. The selected first-strike, regular lethal, terminal-invariant, and priority tests passed.

## Adversarial defects

### 1. A reused capture can attach stale game state

I bound a capture object to game A, then wrapped a later operation that failed before binding any runner state. `capture_diagnostic_call` re-raised the later exception but left `capture_error=None` and attached game A's snapshot. This can misattribute a failure to a previous execution if a caller reuses the capture object or wraps a path that fails before `run_game` binds. The helper must invalidate prior state at the start of every call and require exactly one binding during that call; an unbound call must fail closed.

### 2. Formatting a snapshot-capture error can mask the original exception

An injected `Game.snapshot()` failure whose exception raises from `__str__` escaped the capture handler while formatting `capture_error` with an f-string. The caller received the formatting `RuntimeError` instead of the original diagnostic exception, and `capture.failure` remained unset. Formatting the original execution exception is guarded, but formatting a snapshot-capture exception is not. All capture-error formatting must be safe, and the wrapper must preserve the original exception even if capture recording itself fails.

These defects do not invalidate the normal tested path, but both violate the requested stale-state and failure-preservation guarantees. The broader report's named tests do not exercise either boundary.

## Historical evidence control

Using the original PR #404 module at `C:\projects\tmt\.diag001-pr404-67b9bb3\src\tmnt_design_studio\stage002.py`, I read and replayed the saved canonical `april-casey:canonical:7231` snapshot and manifest. The recomputed manifest equaled the preserved manifest; `reconcile_snapshot()` returned an object exactly equal to the saved report. All nine files listed in `artifact_sha256.json` matched. The three original stop records remain unchanged:

1. `illegal_mutation` for combat damage after terminal state.
2. `silent_approximation` for `presence_evidence_missing`.
3. `silent_approximation` for the same 28 disputed execution references.

No missing historical presence was reconstructed, and no disputed reference or stop was deleted or reclassified. No game was executed.

## Required rework and next gate

Add a capture-call lifecycle that invalidates stale state before invoking an operation, accepts one runner binding only during that call, and records an unbound failure without a snapshot. Make capture-error formatting non-throwing and ensure a failure inside capture bookkeeping cannot replace the original exception. Add deterministic regressions for capture-object reuse, failure before binding, snapshot failure with an unprintable exception, and original exception identity. Then rerun the 32 named nodes, relevant quality checks, and historical replay.

PR #411 remains unchanged by this audit. This verdict does not authorize a complete game. The future one-shot launcher must adopt the corrected lifecycle and pass independent review before HQ considers another one-game authorization.
