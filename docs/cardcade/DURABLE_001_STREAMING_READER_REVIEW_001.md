# Durable 001 streaming checkpoint reader — HQ review

**Status: STREAMING READER READY — HQ REVIEW REQUESTED**  
Prototype only. The authorized runner and threshold remain unchanged. This prototype is not deployed and no calibration evidence was produced.

## Code change

On branch `durable001-streaming-prototype` from repair commit `01ee617683bbc50f38098923c56102738eec9f37`, `run_checkpointed_schedule` now calls `CheckpointAccumulator.restore_stream`. The reader consumes the canonical writer format one record at a time, checks the envelope/counts/schedule digest, and validates each ID for authorization, uniqueness, and increasing schedule order before retaining it. It rejects malformed records, truncation, trailing bytes, and noncanonical envelope/record boundaries. It does not keep a full checkpoint text string or full `records` list beside the accumulator.

The previous API `restore(payload)` and `validate_checkpoint` remain available. Restore ownership, scheduling, record objects, game executor, and checkpoint writer semantics are unchanged. The writer still serializes the existing format and uses the same atomic replacement path.

## Profile and equivalence

Two fresh processes restored separate byte-identical copies of the preserved checkpoint (709,602,686 bytes; SHA-256 `ab1ecf83c6acbaf084ee142e5d2d84c0407c4ab82f63d2cbded9c5e4858c7c7a`). Both restored 732 records under schedule digest `4da440bc83b9790876d1020ae83cf2147c4e60a67feba8bb7181421e196b303e`. Each accumulator wrote a disposable normalized checkpoint. Both output hashes matched the preserved checkpoint hash, and the deterministic small-checkpoint test compares output bytes directly.

| Metric | Whole-file reader | Streaming reader | Change |
|---|---:|---:|---:|
| Peak working set | 2,298,146,816 B | 1,605,959,680 B | **−692,187,136 B (30.1%)** |
| Peak private commit | 2,294,120,448 B | 1,600,499,712 B | **−693,620,736 B (30.2%)** |
| Current private commit after restore | 1,584,996,352 B | 1,597,018,112 B | +12,021,760 B |
| Restore time | 6.414 s | 12.405 s | +5.991 s |

This is a reduction in the *transient load peak*, not in the retained 732-record object graph. The longer cold restore reflects per-record decoding and validation; serialization took 34.791 s for whole-file and 31.669 s for streaming in this profile. Timings are host/load dependent.

The implementation still retains all restored event objects because the resumed runner needs them for final output. The benefit comes from removing the additional 710 MB decoded text representation and full checkpoint payload during loading.

## Integrity tests and checks

The focused deterministic suite passed: **43 passed** across `test_calibration_runner_integrity_integration.py`, `test_calibration_integrity.py`, and `test_bad_guys_calibration_entrypoint.py`. Coverage includes empty and partial checkpoints; equality against whole-file restore; byte-identical serialized output; and rejected count, schedule-digest, schedule-size, duplicate-ID, unauthorized-ID, ordering, missing-ID, noncanonical layout, malformed-record, oversized-line, truncation, and trailing-data cases. Existing resume/no-replay and writer-lock tests also pass.

Ruff check and format check passed for all changed Python files. No remote CI ran: the branch is local, with no PR or push, as directed.

## Engine and hard-paging observations

With the 732 parsed records retained, one non-calibration `run_smoke_game` diagnostic used Shredder/Donatello test decks, seed 3000, and wrote no checkpoint or result artifact. It completed without an error in 0.26 s. Peak working set increased about 405,504 B from the post-restore high-water; peak private commit increased about 618,496 B. Current private commit increased about 4.0 MB during the diagnostic. This is one representative smoke path, not a bound for every card interaction or the frozen calibration decks.

Windows system counters were sampled during restore and serialization. During restore, observed peak `Memory\Pages Input/sec` / `Memory\Page Reads/sec` were about 1,714 / 638 for whole-file (4 samples) and 929 / 70 for streaming (9 samples). During serialization the peaks were about 1,200 / 110 (23 samples) and 1,351 / 439 (20 samples), respectively. These are system-wide, short samples and cannot be assigned to the reader process. Windows documents that hard page faults can fetch executable images, mapped files, or pagefile contents; these counters do not prove pagefile thrashing by this process. The process page-fault count increased more for streaming (about 921,531 versus 728,783 faults during restore), but that counter includes soft faults and is not a hard-paging measure.

The API counters are also distinct: `PeakWorkingSetSize` is peak resident memory, while `PeakPagefileUsage`/`PrivateUsage` are process commit charge; system `CommitTotal` and available physical memory include the rest of the host. See Microsoft's [process-memory counter definitions](https://learn.microsoft.com/en-us/windows/desktop/api/psapi/ns-psapi-process_memory_counters_ex), [system performance information](https://learn.microsoft.com/en-us/windows/win32/api/psapi/ns-psapi-performance_information), and [hard-page-fault counter guidance](https://learn.microsoft.com/en-us/troubleshoot/windows-client/performance/how-to-determine-the-appropriate-page-file-size-for-64-bit-versions-of-windows).

## Remaining risks and next action

- The reader intentionally accepts the canonical LF, sorted-key envelope emitted by `CheckpointAccumulator.write`. A valid but reformatted JSON checkpoint that the old whole-file parser accepted will now fail closed. The preserved checkpoint and writer outputs use the canonical form.
- The stream parser enforces an 8 MiB physical-line limit and a 64 MiB record limit. The largest preserved record was about 2.91 MB; the bounds leave substantial headroom while preventing malformed single records from recreating whole-file memory use.
- The line-boundary parser is tested against the current full checkpoint and corruption fixtures, but it is not a general-purpose JSON stream parser for arbitrary root-field ordering or formatting.
- One smoke diagnostic does not bound every game-engine transient. The helper reports no winner or game statistics and discards the returned event object.
- The profile does not justify changing the existing 2,997,492,240-byte gate. The peak reduction is meaningful for restore, but HQ should review the strict-format compatibility and remaining engine uncertainty before deployment.

Recommended next action: HQ review this local commit. If accepted, run the same reader parity, corruption, memory, and page-counter profile in CI or a clean host, then make a separate deployment/resume authorization decision. Do not lower the gate based on this prototype alone.
