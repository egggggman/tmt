# Calibration Release Baseline Refresh V6

Status: **review candidate; execution_authorized: false**.

PR #143 merged as `933f3af3d0148cea4ef2f19aefe38013c8f4eff2`. V6 binds the accepted runtime `ab2f8fb8a71d812e188f7955df9447e9a8fc5c6d`, protocol `96fc43ec3203938eb385618f6187f8496b93ecd3`, accepted V2 schedule and the launcher compile guard.

V2 committed SHA-256: `6BE94F69A2E9432E615AEA7A8592D68B6537998B3F7355A60191A29E71DC6E5C`.
V2 retained entropy SHA-256: `E5E3824A4B0590F275F643E86BE87D0E5230FDBEABEF5C798A92DFAE8CBC64BB`.
Historical V1 remains preserved with SHA-256 `C8D3EFBB99B2891808985D66E7EA59EF879D546B7D378F05FA17E63793F9D968`.

The compile-only launcher guard and corrected construction boundary are bound by exact committed identities. The terminal-contract runtime, strict runner, Pilot, interpreter, decks, corpus, capacity disposition and semantic/Pilot dispositions remain unchanged. Failed run `CALIBRATION_V1_20260915T180636Z_77400eb2480d` is preserved with its launcher, stderr, stop and checksums.

The workload remains 184,320 distinct games / 368,640 executions with exact duplicate replay, no truncation, no adaptive or replacement seeds and fail-closed stopping. V6 preparation performed zero game executions and no balance analysis. Independent HQ verification and separate explicit execution authorization remain required.
