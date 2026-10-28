# PR #368 four-defect correction review

Original audited head: `8b1764ab74dfcab558f8f0e11d6ecc4ddd14b190`.
This is a correction to the existing synthetic adapter, not a persistence redesign,
deployment, authority issuer or historical-identity exception. The #365 checkpoint
schema, START/PREPARE/COMMIT protocol and replacement retry budget are unchanged.

## Evidence preservation

The original independent audit file is preserved verbatim as
`tests/evidence/pr368_original_adversarial.py.txt`, SHA-256
`a9751fa5e1f44f6024d0cf2289cf03eb009f10f7529b0d5016f9e05acc6fd549`.
The four failing predicates are retained in `tests/test_durable_original_four.py`.
Only fixture issuance supplies the now-required telemetry capability and approved
payload manifests; the predicates themselves have the same Python AST.

At the old head all four failures were reproduced before edits. The complete
original evidence and logs remain in the local audit/correction directories.
No historical artifact was normalized or modified to make a test pass.

Final Windows CPython 3.13.15 focused validation: **106 passed, 1 skipped,
0 failed, 0 errors**, 161.93 seconds. The skip is native symbolic-link creation
without the host privilege; Windows junction/hardlink and real-handle tests pass.
All four original predicates pass and their ASTs match the preserved evidence.
Repository Ruff, formatting and whitespace checks pass. Linux CI is recorded in
the PR and final correction handoff, not inferred from Windows results.

## F1 and F2: file-role separation

`ReviewLease` now requires a separately supplied telemetry root and its filesystem
identity. `validate_outputs` rejects overlap among reference, working checkpoint,
receipt store, telemetry and source/input roles before acquiring ownership or
creating output. Validation is repeated before receipt creation, checkpoint-temp
creation/replacement and status publication. Existing aliases, junctions,
symlinks and hardlinks are rejected. The reference's entire directory is protected.

The standalone monitor cannot authorize itself with a filename. Both read and
publish APIs require a trusted `TelemetryGrant` matching the authorization ID,
root identity and protected roles. It is independent of checkpoint/status content.
Untrusted CLI arguments alone supply no grant and yield UNKNOWN. A future live
capability channel is still unapproved and is not introduced in this correction.

The reader validates the actual opened file ID and containment before reading.
Windows handles open reparse points themselves rather than following them, use
read-only/non-inheritable/delete-sharing access, and pin the telemetry directory
against rename. POSIX reads and status replacement use the pinned directory FD
and no-follow/exclusive creation. Status handles never hold the active checkpoint.
Atomic status replacement can change the leaf file ID, so the stable grant pins
the directory object while each individual read validates its opened leaf object.

These controls protect supported cooperative paths, not against arbitrary Python
code inside the trusted issuer or privileged OS interference. Effective live ACL
and monitor-token separation remains a separate deployment prerequisite.

## F3: actual dependency and interpreter payloads

`RuntimeIdentity` now requires independently supplied dependency origin/file-hash
maps and interpreter/base payload hashes; missing manifests refuse authority.
Actual loaded external modules must match their approved origin and payload.
Loader origins are checked too. Namespace-package search paths must match their
approved manifest. A version string does not excuse changed files or origins.

Project imports remain pinned to the reviewed project root, never current main.
The venv executable, base executable and supplied interpreter/stdlib payloads are
verified independently. These are reconstructed current-byte identities, not
proof of unavailable original interpreter/startup/editable-install equivalence.

`tests/resume_test_support.py` is explicitly a disposable fixture issuer: it
snapshots an approved test environment before substitution attacks. Production
code does not generate trusted pins from whichever modules happen to be loaded,
nor load them from checkpoints or telemetry. Production issuance, expiry,
revocation and durable external anti-rollback storage remain disabled/unapproved.

## F4: one supervisory budget, no framed receives

The monitor no longer uses Pipe.poll/recv_bytes. A fixed bounded shared buffer
contains at most 4096 status bytes; the parent reads it only after successful
child exit. Partial/in-progress replies cannot be accepted. There is no blocking
frame body receive or pipe-resource lifecycle to escape a deadline.

One monotonic deadline covers setup/start, worker lifetime and cleanup. Work uses
60% of the budget, reserving the remainder for termination and bounded join.
Launch is supervised so an overdue startup cannot block the caller indefinitely;
cancellation also stops a late-start child. No join is unbounded. Slow, incomplete,
oversized or failed responses return UNKNOWN and never authorize any dispatch.
This is a supervisory bound under OS scheduling, not a hard real-time guarantee.

## Acceptance coverage and compatibility

The focused suite includes the existing resume/persistence tests, the preserved
four predicates, and expanded role/alias/directory-object, same-version dependency
origin/payload/loader, base-interpreter and stalled/partial/late-worker tests.
Real Windows status reads, held status readers, checkpoint replacement and marker
ownership remain covered. Windows hosts without symlink creation privilege report
that case explicitly; junction/hardlink tests still execute. Linux CI exercises
actual symbolic links and POSIX directory-relative operations.

Old in-memory leases without explicit telemetry authority/manifests fail closed.
The policy digest binds the additional pins; old receipt histories are not
silently migrated, adopted or rewritten. The existing real checkpoint is not a
test fixture, and no normalization/recovery is performed on it.

Next gate: independently review the replacement SHA and reproduce the original
failures against the corrections. Keep PR #368 draft. No merge, live issuer,
deployment or any of the remaining 168 games is authorized by these tests.
