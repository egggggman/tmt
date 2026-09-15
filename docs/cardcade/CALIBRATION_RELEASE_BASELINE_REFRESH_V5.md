# Calibration Release Baseline Refresh V5

Status: **review candidate; execution_authorized: false**.

PR #140 merged as `a8a970a89f3fe9740a5237077380f14bafeed4e1`. V5 binds the accepted runtime `ab2f8fb8a71d812e188f7955df9447e9a8fc5c6d`, protocol `96fc43ec3203938eb385618f6187f8496b93ecd3`, and Seed Table V2.

Seed Table V2 committed SHA-256: `6BE94F69A2E9432E615AEA7A8592D68B6537998B3F7355A60191A29E71DC6E5C`.
Retained entropy committed SHA-256: `E5E3824A4B0590F275F643E86BE87D0E5230FDBEABEF5C798A92DFAE8CBC64BB`.
Historical V1 committed SHA-256: `C8D3EFBB99B2891808985D66E7EA59EF879D546B7D378F05FA17E63793F9D968`.

V2 has 184,320 rows and 92,160 orientation pairs validated for equal seeds and opposite seat order. The strict runner and accepted terminal-contract runtime remain bound; the Pilot, interpreter, corpus, catalog, ten decks, capacity disposition and semantic/Pilot dispositions are unchanged. Prior failed runs are preserved and enumerated in the JSON.

The workload remains 184,320 distinct games / 368,640 executions with exact duplicate replay, no truncation, no adaptive or replacement seeds, and fail-closed stopping. V5 preparation performed zero game executions and no balance analysis. Independent HQ verification and separate explicit execution authorization remain required.

The JSON records committed Git bytes and checkout hashes separately because Windows line-ending conversion affects working-tree bytes; the accepted frozen identity is the committed Git SHA-256.
