# Fresh 900 four-defect correction — independent re-audit required

Audited parent: `45311dadd1c14e0c183c86085b47e8d3dd670b6f`. This is a limited
synthetic-only correction. No live adapter, game, historical checkpoint access,
memory-threshold change, merge, deployment or new persistence architecture is
authorized. Frozen gameplay/input Git blobs remain unchanged.

## Corrections

**A — Actual filesystem relationships.** `plain()` rejects unsupported extended,
device and UNC namespaces, drive-relative paths, trailing-dot/space components,
alternate streams, reserved devices, symlinks, junctions/reparse points and
hardlinked regular files. It checks the original spelling before Windows path
expansion can hide a trailing dot, then resolves existing ancestry through the
filesystem. `disjoint()` checks canonical ancestry and existing endpoint/ancestor
file identities. The reservation parent and all created directories are pinned by
device/inode; guards recheck protected roles before temporary creation and before
replacement/read-back. Tests substitute both a junction and an ordinary new
directory after dispatch, and replace the reservation parent before mkdir.

This is a local-drive, cooperating-process policy. It fails closed for unsupported
namespaces/relationships; it is not a kernel-handle-relative filesystem sandbox
against a malicious same-account actor racing every check. OS privilege/ACL and
deployment isolation remain separate gates. G: supports the required NTFS identity
checks in the disposable tests. No path checks were relaxed for historical data.

**B — Reject contradictory records.** Before append, validate the required
synthetic/terminal/winner/turn/evidence fields and all supplied redundant row
identities, seeds, orientations, opponents, pairing, participants/players, schedule
indices (zero-based index / one-based position), run/plan/runtime/input identities,
counts, winner index, loser, draw and terminal state. Nested identity/metadata must
use known authoritative fields and agree. Known incomplete-event markers and
malformed evidence entries are refused. JSON-invalid/NaN/cyclic data is refused.
Additional ordinary telemetry is retained; this is not a live semantic reconciler.

Only missing derived run/plan/schedule fields are added after validation; conflicting
values are never normalized into acceptance. JSON-serializable rejected input is
saved unchanged in `failures/rejected-record.json`. If that diagnostic cannot be
serialized/written, the initiating refusal remains authoritative and the diagnostic
failure is recorded separately. The pre-correction invalid records/checkpoints and
cleanup log are preserved as immutable `tests/evidence/pr369_before_*.json.txt`.

**C — Expected bytes and expected content.** Fresh checkpoint writes stream a
SHA-256 over the exact expected UTF-8/LF serialization before replacement. The
read-back digest/size must match those expected bytes before progress advances.
The digest is not minted from already-altered disk content. Compact record digests
bind accepted logical content independently. Final validation requires exact full
ordered schedule coverage, every expected record digest, unchanged expected file
bytes and unchanged file identity/size/mtime across validation. Post-write corruption
or even a substituted file accompanied by a recomputed untrusted hash is refused.

The checkpoint envelope/serialization, per-game full-checkpoint cadence and retry
budget remain unchanged. No receipt/HMAC/anti-rollback or incremental-store system
was added. Pre-replacement failure preserves the previous valid file. Detected
post-replacement corruption stops for review; it does not silently repair/roll back
the file or guarantee recovery of an uncommitted record.

**D — Primary failure and cleanup are distinct.** Lock/temporary cleanup preserves
the initiating exception object. Separate cleanup entries retain type, stage,
resource and OS error details. Ownership markers are checked by actual file identity
before release; disappearance/replacement or a release that leaves ownership held
is a failure. Acquire tracks ownership immediately after exclusive creation, including
metadata/fsync failure. No automatic stale-lock stealing/deletion is introduced.

`stop.json` records original type/stage, separate cleanup failures, operation state,
checkpoint-integrity verification and unresolved ownership/resources. Unavailable
failure-file publication falls back to JSON on stderr; the initiating exception
also carries its structured report. If output channels fail, the primary exception
is still preserved with cleanup evidence. No COMPLETE status or successful return
occurs before ownership release; release-only failures remain failures.

## Preserved predicates and fixtures

The original independent sources are byte-identical:

- `pr369_test_independent.py.txt`: SHA-256
  `f8210adda237543adefb9c8e7f1668cae38384fcae51fcd10ed66488a13b088e`.
- `pr369_test_fullplan_boundary.py.txt`: SHA-256
  `ad93699112f6b5e9cfd4d5c2217cb25229b264ac0d971df6be09f9d7e3007bb4`.

`.gitattributes` marks only new `pr369_*.txt` evidence `-text`, preserving raw bytes
on Windows checkout. Existing historical attributes/evidence are not reclassified.
All four failing function/decorator ASTs are checked unchanged. Runnable boundary
copies adapt only non-failing repository/Git fixtures and positive native-test
platform handling; the original Windows namespace skip was already present.

The full-plan wrapper executes the entire original predicate unchanged. It creates
a new fixture-local source/import seal for the candidate being tested, rather than
rewriting the old historical attestation or falsely accepting its stale code hashes.
Its initial-checkpoint assertion still requires the complete unmodified plan,
runtime, input and resource preflight to succeed before checking seed refusal.
Linux uses the same underlying interpreter via its resolved path plus locked test
site-packages, installed by copy rather than cache hardlink; neither the predicate
nor verifier is patched/skipped there. Native Windows-only positive handle cases
remain explicit Linux skips, never passing Windows evidence.

Before correction: boundary C:/G: suites each reproduced **20 pass / 6 fail**;
the separately run full-plan seed predicate failed at the actual conflicting seed.
A combined before run stopped the full proof at its import-seal guard because another
unsealed audit module was loaded; that harness distinction is retained. First-after
testing exposed a command-specific Git safe-directory fixture issue, corrected
without changing its frozen input assertions. An added trailing-dot case exposed
and corrected pre-expansion path validation. No failed test predicate was weakened.

Final Windows suite: **142 passed / 0 failed / 0 errors / 1 skipped**, 489.96 seconds.
The one skip is native symlink creation privilege. Original/expanded G: correction
suite: **72 passed / 0 failed / 0 errors / 0 skipped**, 38.28 seconds. Actual junction,
ordinary-directory/parent substitutions, hardlinks, held readers, process interruption,
original predicate AST preservation and combined cleanup failures executed. See PR
checks for exact replacement-head Linux results; passing CI is not acceptance.

## Complete checkpoint-path resource evidence

The profiler uses the shared corrected writer and final validator, including expected
byte hashing, fsync/replacement, verified read-back, status reauthentication/publication,
compact expected-record hashes, accumulator release/GC before parse, full ordered
content validation and ownership release. It generates nested synthetic records at
the audit's rounded historical aggregate densities, not protected checkpoint data.
No game is executed. It samples growing checkpoints at 225/450/900 rather than
performing all 900 large rewrites; cumulative costs below are explicit projections.

Both C:/G: mean-density fixtures serialized **872,442,162 bytes** and verified all
900 records. C: peak private commit **2,533,052,416 bytes**, peak working set
**2,536,083,456 bytes**. G: peak private commit **2,532,544,512 bytes**, peak working
set **2,535,682,048 bytes**. Both remain below **2,997,492,240 bytes**, including the
previously omitted finalization path (which measured ~3.26 GiB before correction).
The operational minimum-free physical/commit gate is unchanged; HQ additionally
requires this numeric comparison to measured complete-path peaks. The profiler
records BLOCKED and exits nonzero if either peak exceeds it.

The original accumulator is released before the final decoded graph is created;
full detailed records remain in the checkpoint. These results cover the specified
synthetic shape, not live gameplay transients, every possible record distribution,
future allocator behavior or total system headroom. Some synthetic tests ran
concurrently; timings are observations, not isolated-device guarantees. The final
G: report binds the writer/validator/path-source hashes and profile-source hash.

Per-game full checkpoints still imply approximately **393 GB / 366 GiB logical
writes** over 900 games. Verified read-back plus status reauthentication adds about
**786 GB of checkpoint reads**, plus final content parsing/hashing and runtime/input
attestation I/O. Observed checkpoint persistence extrapolates to approximately
**11.2 hours on C: / 11.8 hours on G:**, excluding gameplay, every-dispatch runtime
verification, device-level amplification, backups and other workloads. These are
linear estimates, not 900 large writes actually executed or promised runtime.

Retaining per-game full checkpoints is the smallest unchanged persistence policy
for this correction and avoids dropping telemetry or a multi-game durability window.
Its production cost is **not approved or demonstrated reasonable** by green tests.
HQ should accept/reject a persistence latency/write/recovery budget before execution.
If this cost is unacceptable, the smallest evidence-preserving alternative to
evaluate separately is one immutable full-record artifact per game plus a small
atomic ordered progress/hash manifest; that needs an interruption/recovery contract.
It is an incremental architecture and was **not implemented** here. Do not reduce
checkpoint frequency or discard detailed records as an implicit optimization.

## Handoff boundary

All measurements/test details and original failed-record hashes are in
`FRESH900_CORRECTION_VALIDATION.json`. The previous validation JSON and audit report
remain historical evidence. Neither historical checkpoint bytes nor production
paths were accessed by this correction; no new historical checksum is claimed.

Request independent re-audit of the published replacement head. Live adapter,
production environment/plan approval, source-base integration, ACL/backup/recovery
policy, a separate no-game execution preflight and explicit launch authority remain
blocked. This correction grants none of them.
