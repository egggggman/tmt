# Monitor cleanup candidate — contract decision required

**BLOCKED against the original unconditional-close requirement.** This candidate
fixes delayed termination and asynchronous late exit, but cannot force exit when
the OS denies termination and the child remains alive. The original denial test
is retained, unmodified and failing; it is not skipped or marked xfail. Green
tests for the proposed contract below are not independent acceptance.

Audited base: `d1d109379f8661c5cd9d22f794bdae5a5e5aa329`.
All changes are monitor lifecycle, diagnostics, synthetic tests and documentation.
Checkpoint persistence, authentication A–C, decks and thresholds are unchanged.
No production checkpoint is read or written by this work.

## What is corrected

- Process start, read, join, termination and close run on one owned supervisor,
  never synchronously on the sample caller. Caller waits only within its existing
  budget (maximum 250 ms); no timeout was lengthened to hide cleanup delay.
- After timeout the owner requests termination once, then observes exit using
  finite joins. A late asynchronous exit is rechecked and the handle is closed.
- Exceptions are retained as original objects and exposed with operation, type,
  message, errno and winerror. Termination failure does not skip the exit check.
- Exit confirmation is distinct from resource closure. A failed close reports
  EXIT_CONFIRMED / UNRESOLVED rather than falsely reporting a live process.
- A sample is successful only after confirmed exit and close, without errors,
  inside the caller budget. No late response can change a failure into success.

## Proposed measurable contract (needs HQ acceptance)

1. The sample caller returns by its supervisory budget under normal thread/OS
   scheduling. This is not a hard real-time guarantee during kernel suspension.
   Potentially blocking process-control calls never execute on that caller.
2. Failure returns UNKNOWN. `MonitorFailure.outcome` distinguishes TIMEOUT,
   UNAVAILABLE and OWNERSHIP_UNRESOLVED. `report()` serializes the fixed outcome
   plus current cleanup diagnostics; the supported CLI calls it. Legacy dict
   consumers still see UNKNOWN, which never grants authority. There is no custom
   equality behavior.
3. Cleanup state is PENDING, CLOSED or UNRESOLVED. The process observation is
   UNKNOWN, NO_PROCESS_HANDLE or EXIT_CONFIRMED; it does not claim current liveness
   from a stale snapshot. `cleanup_error` retains the original control exception.
4. There is at most one owned monitor job per interpreter. Until its resources
   are closed, another sample fails with OWNERSHIP_UNRESOLVED and creates no child.
   Ownership is never force-cleared to make room for another worker.
5. Automatic reaping observes for at most 500 ms, in joins of at most 25 ms, after
   the OS control call returns. This is an explicit background observation window,
   **not** an extension of the caller's deadline or a promise of exit in 500 ms.
   If exit remains unconfirmed, the worker and errors remain quarantined/owned.
6. `cleanup_status(refresh=True)` starts a bounded observation of that same worker
   after the prior attempt finishes. It does not start a new child, retry kill
   indefinitely, grant authority or discard errors. A later confirmed exit permits
   closure. If a process-control API itself never returns, its single supervisor
   and ownership remain PENDING; new worker creation remains blocked.

Python cannot safely cancel an arbitrary running thread or close a live process
as if it had exited. Permission failure is not fixed by increasing waits. External
OS/operator recovery can remain necessary. This proposal intentionally reports
that limitation instead of manufacturing successful cleanup.

## Regression evidence

The complete independent re-audit source is preserved byte-for-byte in
`tests/evidence/pr368_monitor_original_adversarial.py.txt` (SHA-256
`f7fb4c50dbc0b1294593feccacc5294099e413407db86dd3a1461feb63f7f215`).
`tests/test_durable_monitor_adversarial.py` preserves the three failure predicates
and backend semantics. Only repository-fixture location, formatting and test-only
teardown are adapted. Teardown simulates external exit of disposable fake backends
**after** assertions, never suppressing the observed denial failure or resetting
ownership of an actual OS process.

`tests/test_durable_monitor_cleanup.py` checks the proposed contract: delayed
termination, late exit, errors followed by natural exit, join/close errors, blocked
startup, no child accumulation, original-error retention, late-response rejection,
success only after closure, and CLI diagnostic serialization.

The complete original adversarial suite remains in CI. Expect the original
termination-error predicate to fail until HQ decides whether the proposed
UNRESOLVED/retained-ownership contract replaces its impossible guarantee that a
permanently live, termination-denied process has already been closed.

## Decision needed

Accept or reject this measurable contract for the synthetic monitor only. If
accepted, authorize updating that one denial predicate to require explicit error,
retained ownership and blocked new workers rather than forced closure. Then obtain
an independent re-audit of the replacement. No live issuer, historical-identity
exception, deployment, merge or calibration execution follows from that decision.
