# Fresh 900 limited implementation — draft review candidate

HQ selected a fresh experiment, not recovery of Durable 001. This packet implements
the synthetic execution/persistence/preflight boundary. **No live adapter, gameplay
CLI, automatic recovery, production reservation, merge or deployment is authorized.**

## Lineage and scope

Base: `fd28f68915c4e7cb6af3444bf41b96608dee712c`, the exact producer gameplay tree.
The PR targets `design/bad-guys-cronies-sandbox-research` at that commit, rather
than substituting current main's different gameplay tree. Acceptance/integration
of this unmerged base remains a separate HQ gate. Draft #365's
`calibration_integrity.py` is reused byte-for-byte; #365 is not merged or deployed.
#366 and #368 are not ancestors. Their streaming reader, historical resume leases,
receipt protocol and monitor worker lifecycle are not incorporated.

The candidate keeps all engine/Pilot/game executor, deck/card/manifest and lockfile
Git blobs unchanged. Input files in the new review checkout were materialized from
their unchanged raw Git blobs to avoid automatic CRLF conversion; no historical
checkout or evidence was edited. All 17 frozen input identities are pinned in
`fresh900_identity.FROZEN_INPUTS`. The ten baseline decks remain accepted references;
Cronies 0.2 remains experimental, and Baxter/12-deck roster promotion is excluded.

## Implemented contract

- `run_synthetic` requires an external approval object, independently supplied
  approval digest, exact plan binding, synthetic-review action and explicit executor.
  The action `fresh-start` is refused. There is no default executor or live command.
  A caller able to rewrite both approval and its pin can self-authorize a fixture;
  this is local governance evidence, not a cryptographic live issuer.
- Require the exact frozen nine-opponent, 900-row, balanced schedule and seeds,
  source/input inventories, actual loaded import origins and payload hashes,
  interpreter identity, 64-bit process, no-user-site/no-bytecode and hash seed zero.
  Existing imported bytecode files are included in the seal and checked too;
  disabling bytecode writes alone would not authenticate cached imports.
- Refuse existing output roots/checkpoints. Exclusive mkdir reserves the synthetic
  run, followed by checkpoint writer ownership. No second invocation resumes it.
  Missing checkpoint during a fresh run does not create an implicit recovery path.
- Fixed output roles separate immutable inputs/runtime/control, checkpoints,
  telemetry, results, integrity, logs and failures. Reject symlinks, junctions,
  reparse points, hardlinks and protected-directory overlap before output. Pin
  created directory identities and recheck during execution. This is cooperative
  process isolation, **not an adversarial same-account ACL/TOCTOU sandbox**.
- Keep every detailed synthetic record. Reject wrong IDs, nonterminal/no-winner
  snapshots, invalid turns, invariant/stop records or absent detailed event lists.
  Preserve the original game ID plus run ID, schedule row and approved-plan digest.
  A turn-limit snapshot is not a draw or successful completion. Live snapshot
  reconciliation into this schema still needs a separately approved adapter.
- Persist after each record using #365's single authoritative accumulator,
  streaming JSON dump, same-directory temporary file, flush/fsync and replacement.
  Eight attempts/seven backoffs apply only to specified access/sharing errors.
  Reuse the same flushed file and preserve the first exception. The maximum
  programmed backoff is 3.55 seconds, **not a total OS I/O deadline**.
- Publish a small integrity record and status only after checkpoint replacement.
  Any subsequent publication failure stops before another dispatch; the advanced
  checkpoint remains intact. Failure logs retain stage, observed count, original
  error/type/errno/winerror and STOPPED_REVIEW_REQUIRED. If logging fails too, stderr
  carries both errors. A process kill may leave a stale ownership marker and an
  ambiguous checkpoint/journal boundary; never auto-replay or roll back.
- Final summary requires 900 in-memory IDs and validation of the persisted envelope.
  The authoritative detailed checkpoint is retained; this draft does not duplicate
  its entire bytes under results or perform a production archive/backup operation.
  Final independent inventory/summary acceptance and backup remain future gates.

## Monitoring

`MonitorLocation` pins an explicit telemetry-directory identity/run ID and the
separate protected checkpoint directory. The interface accepts no checkpoint leaf
path. Validate containment, directory role, link count and opened file identity;
read at most 4097 bytes, close in finally/context manager, and check protocol,
run ID, count and freshness. Invalid/stale/mismatched telemetry is UNKNOWN;
valid telemetry is REPORTED_ONLY, never authenticated checkpoint truth.

Monitoring runs independently, opens only status, never owns the checkpoint lock,
and does not spawn a worker or require a writer RPC. An OS-blocked synchronous read
has **no hard deadline guarantee**. It does not block the checkpoint writer; an
operator may need to stop a stuck observer. Heartbeat is published at dispatch and
status at commit; a long game can produce stale telemetry, not proof of process
death. A held status reader can prevent status replacement. That publication uses
the same bounded retry helper, then fails closed if denial persists. No retry
extension hides indefinite contention.

Native Windows tests hold a status handle **without FILE_SHARE_DELETE** throughout
five separate checkpoint replacements. Disguised checkpoint filenames, hardlinks,
foreign root/protocol/IDs and stale status are rejected. Broader hostile-process
ACL/version-handshake deployment is not claimed complete.

## No-game tools and reproduction

Use the reconstructed CPython 3.13.15 interpreter by absolute path. These commands
do not activate PowerShell scripts or change execution policy:

```powershell
$env:PYTHONHASHSEED='0'
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONPATH='<review-checkout>\src;<review-checkout>'
& <python.exe> -s -B -m pytest -q tests/test_fresh900.py tests/test_calibration_integrity.py tests/test_bad_guys_calibration_entrypoint.py -p no:cacheprovider --basetemp=<unused-disposable-directory>
& <python.exe> -P -s -B tools/preflight_fresh900.py --git <git.exe> --wheelhouse <verified-wheelhouse> --disposable-parent <existing-disposable-parent>
& <python.exe> -I -B tools/profile_fresh900_synthetic.py --parent <existing-disposable-parent> --records 900
```

Never supply an existing pytest basetemp: pytest can delete it. The final Windows
test runs used fresh checked-unused paths. The profile exclusively creates a
`FRESH900_SYNTHETIC_<timestamp>_<pid>` directory and retains its synthetic output.
It never opens production evidence. No automatic removal of fixtures is provided.

`preflight_fresh900.py` is read-only and emits a **candidate**, not authorization:
full source/tool/environment/base file inventories, actual loaded module checks,
frozen raw Git input checks, installed dependency versions and wheel-payload
comparison against the immutable lock, and Windows physical/commit/disk counters.
The caller must independently approve the exact final source commit/inventory.
The returned candidate is not automatically a fully assembled/approved run plan.

Use `-P -s -B` with `PYTHONHASHSEED=0` for identity preflight: `-I` ignores
that environment setting and is now explicitly rejected. Both the environment
value and actual interpreter hash-randomization/ignore-environment flags must
agree. The initial `-I` diagnostic's input/package/resource measurements remain
measurements, but its startup attestation is superseded by this corrected check.
The memory-only profile uses no gameplay seeds and makes no startup-equivalence
claim; its measured persistence bytes remain unchanged.

The reconstructed interpreter is qualified prospectively, not proven historically
identical. A fresh deployment still requires its own isolated source binding;
the existing recovered environment's historical `.pth` was not altered. The
diagnostic tool prepends this reviewed source before importing project modules and
verifies their actual paths. No unlocked dependency installation or package build
is performed. Missing wheel or payload evidence fails closed.

CI runs only the explicit synthetic/persistence/entrypoint fixture files on this
review branch. The repository's full suite contains gameplay and was not run.
Linux exercises portable persistence/synthetic behavior; native Windows import
seals, held handles and junction checks are skipped there, not counted as passes.

## Resource policy and limitations

Unchanged memory gate: **2,997,492,240 bytes**, independently applied to physical
availability and system commit headroom before initialization and each dispatch.
Minimum evidence-volume free space is 20 GiB. This is a disk reserve, not a changed
memory threshold. No guarantee of gameplay heap peaks, OS reservation or hard I/O
deadline follows from these samples. The current implementation inventories and
hashes runtime/input payloads at each dispatch for simple fail-closed review;
its real I/O cost must be measured on the approved complete plan before launch.

The profile uses new synthetic dictionaries/strings at the prior aggregate event,
presence and rule-event densities. It does not copy protected records. Identical
serialized size does not establish identical heap topology or gameplay memory.
See `FRESH900_VALIDATION.json` for the measured mean-size 900-record profile and
the 90-record large-size stress sample. The latter is not a 900-record worst-case
proof. Per-game whole-checkpoint persistence retains the ~393 GB cumulative-write
projection; full-size single-write time must not be presented as total runtime.
No streaming/incremental redesign or telemetry reduction was introduced.

## Remaining gates

Recorded Windows CPython 3.13.15 validation:

| Run | Passed | Failed | Errors | Skipped |
|---|---:|---:|---:|---:|
| Final combined synthetic/persistence/entrypoint suite | 70 | 0 | 0 | 1 |
| G: disposable target-volume suite, before six added identity/startup cases | 64 | 0 | 0 | 1 |
| Final targeted import/wheel/bytecode/startup identity slice | 11 | 0 | 0 | 0 |

The one skip is native symlink creation privilege. Windows junction, hardlink,
held-status-reader and actual process interruption cases passed. The final
combined run took 78.74 seconds; the G: run took 73.73 seconds. Ruff, formatting
and whitespace checks passed. Linux CI is recorded in the PR/checks at its exact
published head, not inferred from these Windows results.

Full-size mean-density synthetic profiles both serialized **872,442,162 bytes**,
SHA-256 `c6d72919a6a82f4445714bf3a14040717f7f1b2f2c9e6be9863f9ad5945eb805`.
Local write/restore: 22.48/7.76 seconds; G: write/restore: **35.79/7.96 seconds**.
G: retained private commit was 1,113,317,376 bytes; peak through restore was
**2,050,625,536 bytes**. Both restored all 900 synthetic records without changing
checkpoint bytes. The 90-record large-size sample serialized 261,948,940 bytes
and peaked at 566,886,400 bytes private commit. These are synthetic persistence
measurements, not gameplay headroom certification.

Read-only candidate preflight verified **17 frozen input Git hashes**, **13 locked
distributions / 741 installed wheel payloads**, loaded source/import/bytecode seals,
the recorded official base executable hash and both unchanged resource gates.
Before final-head resealing, physical availability was 8,505,323,520 bytes, system
commit headroom 11,001,208,832 bytes and C: free 425,033,379,840 bytes. Resource
snapshots are not reservations. No historical interpreter equivalence is asserted.

Earlier attempts remain accounted for: a missing pytest basetemp parent caused
49 harness setup errors; a transient status replacement denial caused one product
failure, fixed by reusing bounded replacement; CRLF checkout bytes caused a
correct preflight refusal until exact unchanged input Git blobs were materialized
in this new review tree. No historical record was normalized or repaired.

Initial Linux CI at `e123be3` recorded 47 passed/12 failed/11 skipped because
the hosted runner lacked the real 20 GiB disk reserve. The runner correctly
refused before dispatch. Synthetic contract fixtures now supply a deterministic
30 GiB disk reading alongside their existing synthetic physical/commit readings;
dedicated low-disk tests still exercise refusal. Real C:/G: profiling/preflight
counters and the production 20 GiB reserve are unchanged. This test-harness fix
does not qualify the Linux hosted runner for execution.

1. Independent review of this draft's synthetic safety implementation and frozen
   base/integration decision. Neither author tests nor CI are acceptance.
2. A separately authorized no-game execution preflight against the exact reviewed
   final commit, fresh source-bound environment, full prospective plan, real target
   volume/permissions and independently pinned approval artifacts.
3. Explicit review of the live result adapter/reconciliation, actual gameplay
   resource uncertainty, final evidence export/backup and operator stop/recovery
   procedure. This draft cannot dispatch live games.
4. Only after those gates, an explicit HQ fresh-launch authorization. No automatic
   recovery, Durable 001 continuation, historical identity exception or roster
   promotion is implied.

Durable 001 remains PAUSED — HISTORICAL, 732/900. No production checkpoint was
read/written. PRs #365/#366/#368, historical reports, frozen decks/source evidence
and the memory threshold were not modified, merged or deployed.
