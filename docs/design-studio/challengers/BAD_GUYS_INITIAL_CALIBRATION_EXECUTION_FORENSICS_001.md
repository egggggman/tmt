# Bad Guys 0.2 Initial Calibration — Execution-Integrity Forensics

**Finding: ROOT CAUSE VERIFIED — REQUEST CORRECTION AUTHORIZATION**

The contaminated checkpoint `c74ad8c537b73480bc25e2495371bc18df8b3567a230a734cde6f1bb831c30f4` contains 1,211 persisted game rows but only 606 schedule entries and 606 unique game IDs. It is inadmissible and no outcomes are salvaged.

## Reconstructed divergence

The first game row is unique. Starting at row/index 2, each subsequent row is duplicated byte-for-byte. For example, game ID `bad_guys_cronies_sandbox_0_2--leonardo:candidate_first:1000001` appears at rows 1 and 2 with identical result and event digests.

The observed count follows exactly:

`1 + 2 × (606 − 1) = 1,211`

This proves persistence accumulator aliasing rather than duplicated gameplay execution. The runner appended the row to both `games` and `base["games"]`, then assigned `base["games"] = games`; after that assignment both names referenced the same list, so every later row was appended twice.

The schedule list was also only partially persisted when the run stopped, reaching six complete cells plus six Krang entries. Its 606 rows are not an authorized schedule and are not evidence of a valid partial calibration.

## Smallest safe correction for separate authorization

Use one authoritative row accumulator and append each completed row exactly once. Checkpoint from an immutable snapshot or a separate copy. Before aggregate reporting, fail closed unless all of these hold:

- exactly 900 scheduled identities;
- exactly 900 unique game IDs;
- 9 matchup cells × 100 games;
- 50 candidate-first and 50 opponent-first games per cell;
- no duplicate IDs or unauthorized appended records;
- idempotent checkpoint persistence and explicit interruption/resume boundaries;
- one authoritative writer per checkpoint.

This investigation made no gameplay simulation, deck, runtime, historical-evidence, or runner-code changes.
