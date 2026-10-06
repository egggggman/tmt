# Krang R7-A — semantic readiness

**Status: BLOCKED_SEMANTIC_EXECUTION.** No R7-A games or replays were run.

Merged [Design Studio authority](https://github.com/egggggman/tmt/pull/268) at `9f48bdbd6fc4800429217ca7897257180132302d` freezes `−1 Does Machines / −1 Negate / +1 Ray Fillet, Man Ray / +1 Stockman, Mad Fly-entist`. Candidate SHA-256: `2d598af2d05212ffb0f19fe5f315b7bf8f85501975155f394448b0a48fa81ab1`; Git blob: `3d224fecb398bb01d675837238e1196a07bdcb2d`. The list is 60 cards and is the exact four-card-count diff from Baseline 003.

The existing Aura-runtime Baseline 003 control `OBL-BASELINE-003-AURA-RUNTIME-REFRESH-001` is compatible with runtime `ccfa75ed8e817bc3af0a04f75ef048aaee54e5175c06abfc21feaad6515bb0ec`. All 4,500 preserved control records and six deterministic replay samples authenticated. The 900-game candidate schedule is the established `b5fd8ab57016b15662fca420d508c9aab3633ad14b7f7515d667492b0f8abf27` schedule; it has not been executed for R7-A.

| Added card | Executable | Missing printed mode | Consequence for this test |
|---|---|---|---|
| Ray Fillet, Man Ray | ETB Mutagen token creation | Mutagen token's {1}, {T}, sacrifice: +1/+1 counter activation | The token's counter is a printed route to the counter that Ray Fillet can remove to draw a card. |
| Stockman, Mad Fly-entist | Flying and ETB draw-then-discard | Islandcycling from hand | The extra Stockman copy changes access to its printed land-selection mode, which the pilot cannot execute. |

Stockman's ETB filter and Ray Fillet's flying/body, Mutagen creation, and counter-removal draw are represented. The Mutagen's activated counter ability and Islandcycling are not. Their increased copy counts make the missing modes asymmetric against the existing control. The inherited baseline also has unsupported Negate and Does Machines level-3 behavior; neither is credited as simulated value.

The merged [R7-A plan](ROUND_7_A_CANDIDATE_PLAN.md) directs Cardcade to fail closed when a required rule is unavailable. No deck edits, fresh control games, candidate games, combined validation, or promotion occurred.

**NEXT MOVE → 🕹️ Cardcade engine/readiness:** implement the missing generic token activation and hand-zone Islandcycling semantics, validate them, then refresh all 4,500 unchanged Baseline 003 control games under the new runtime before the frozen 900-game R7-A isolated test. Return completed test evidence to 🧪 Design Studio for interpretation.

[Machine-readable identity, coverage, and control checks](ROUND_7_A_READINESS.json).
