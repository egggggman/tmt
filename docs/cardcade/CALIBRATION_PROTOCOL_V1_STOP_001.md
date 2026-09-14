# Calibration Protocol V1 Execution Stop Record

Run identity: `CALIBRATION_V1_dea90ea8903152e4a608d9f3b0fd81b5efddc564`
Frozen execution commit: `dea90ea8903152e4a608d9f3b0fd81b5efddc564`
Protocol: `96fc43ec3203938eb385618f6187f8496b93ecd3`
Manifest: `docs/cardcade/CALIBRATION_RELEASE_MANIFEST_CAPACITY_V1.json`

Status: **FAIL_CLOSED_STOP**

Completed distinct games: 0 / 184,320
Completed executions: 0 / 368,640
Duplicate authentications: 0
Failures: 1 preflight failure

Failed member: `PRECHECK-RUNNER-001`
Failure: the frozen repository contains no protocol-conformant Calibration V1 execution runner. The available Cardcade runner produces aggregate Engine 0.6 round-robin results and does not implement the required 2,048 whole-roster blocks, paired seat orientations, exact duplicate executions, raw authoritative telemetry, or fail-closed protocol ledger. Substituting it would be a protocol deviation, so execution did not start.

No calibration games were run and no observations were produced. No seed was consumed. No later member was attempted. This stop record is preserved for independent HQ review; execution remains blocked pending a separately reviewed conformant runner and release authorization.
