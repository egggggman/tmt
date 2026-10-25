# Durable 001 recovery reliability repair — HQ review

Status: **REPAIR CANDIDATE ONLY; LIVE RESUME NOT AUTHORIZED**. This branch starts at PR #363 commit `fd28f68915c4e7cb6af3444bf41b96608dee712c`. The frozen execution worktree and preserved `G:` checkpoint were not modified. No calibration games were run.

## Scope

- `calibration_integrity.py` retries only `PermissionError` compatible with Windows access or sharing denial (WinError 5/32 or EACCES/EPERM): eight attempts, delays 0.05, 0.1, 0.2, 0.4, 0.8, 1, 1 seconds. Each attempt uses the same already flushed and fsynced temporary file under the single-writer lock. Persistent denial raises the first error and leaves the previous checkpoint intact. Other errors propagate immediately.
- Checkpoint validation now checks the schedule digest, 900-row count, completed count, unique authorized IDs, and schedule order before restoration.
- The runner transfers ownership of the validated JSON records, keeps a set of completed IDs, and writes without deep-copying every restored record. Completion returns a small summary instead of serializing the entire result into `launcher.log`. The checkpoint remains sorted, indented JSON with the same keys and raw game records. The simulator, candidate, decks, pilot, seeds, and gameplay semantics are unchanged.
- `scripts/calibration_durable_status_safe.ps1` opens the checkpoint with `FileShare.ReadWrite | FileShare.Delete`, reads only 256 bytes at each end, and closes the handle. Its count is explicitly **reported progress, not authenticated record evidence**. Full stopped-checkpoint auditing is still required.

## Evidence

- The original 732-record checkpoint SHA-256 remained `ab1ecf83c6acbaf084ee142e5d2d84c0407c4ab82f63d2cbded9c5e4858c7c7a` after testing.
- A disposable copy of the actual 709,602,686-byte checkpoint resumed with a mock executor. The first call was exactly the first missing ID `bad_guys_cronies_sandbox_0_2--shredder:candidate_first:1000732`; one mock record was written, giving 733. The second call was the next ID and deliberately stopped. None of the 732 persisted IDs was executed. Peak process working set was **2,297,761,792 bytes (2.14 GiB)**. The source checkpoint stayed unchanged, and the fixture was removed after the test.
- Disposable G: tests reproduced transient and persistent WinError 5. The transient reader released and the same replacement succeeded. Persistent denial failed closed with the old file intact and the original error preserved. Replacement also succeeded while the repaired monitor held its read handle open. A separate exclusive reader caused the monitor to report `UNAVAILABLE` without modifying the file or exiting in error.
- Focused mock-only tests: 29 passed. Repository-wide Ruff check and formatting passed. CI results should be recorded from the review branch's GitHub workflow before HQ accepts the repair.

## Proposed resume gate and command

Before any separately authorized resume, pin the repair commit, verify the repair worktree is clean, authenticate the unchanged candidate, Baseline 005, snapshot, overlay, declared semantic runtime `c087f84bab4916b516ec6745f5a8e9f2a2d33f9117856bf959da4eb9a7be8e54`, changed persistence file hashes, and schedule digest `4da440bc83b9790876d1020ae83cf2147c4e60a67feba8bb7181421e196b303e`. Recheck the original checkpoint SHA-256, 732 ordered IDs, G: free space, no writer or lock, and absence of unexplained temporary files. Seal a new resume preflight without altering `PREFLIGHT.json`, `INTERRUPTION_001.json`, or the original checkpoint.

After HQ authorizes the new commit and the same-checkpoint resume, use this Windows command from the pinned repair worktree:

```powershell
Set-Location C:\projects\tmt-recovery-repair
$env:PYTHONPATH = 'C:\projects\tmt-recovery-repair\src'
C:\projects\tmt\.venv\Scripts\python.exe -B -u tools\run_bad_guys_initial_calibration.py --checkpoint 'G:\cardcade\calibration-runs\BAD_GUYS_CRONIES_0_2_DURABLE_001\checkpoint.json' *>> 'G:\cardcade\calibration-runs\BAD_GUYS_CRONIES_0_2_DURABLE_001\resume_001.log'
```

Use the read-only safe monitor from the repaired worktree. Its header count is operational telemetry; publish outcomes only after a full stream audit of the stopped checkpoint and final SHA-256 evidence. Do not run this command from this review document alone.
