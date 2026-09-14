# Calibration Release Baseline Refresh V4

Status: **review candidate; execution_authorized: false**. Calibration remains stopped pending independent HQ verification and separate execution authorization.

## Merged baseline

- Stop-evidence PR #136: `7cdd9f7bb1beec690dd3f89e46c8b94fe1e47fbc`.
- Terminal-contract PR #137 and new runtime main: `ab2f8fb8a71d812e188f7955df9447e9a8fc5c6d`.
- Main was synchronized with origin/main and the working tree was clean before creating this refresh branch.
- Prior accepted V3 release: `bf3ace0ebe984dbd24cf825dcc2bd32fb2da39af`; prior runtime: `425fd1dff2925454d10c113a32a662e58fda1544`.

## Runtime identities

These hashes bind exact Windows checkout bytes, continuing V3's convention. The JSON also records committed Git blob IDs and SHA-256 hashes; those hashes differ where checkout line endings differ.

| Source | Windows checkout SHA-256 | Disposition |
|---|---|---|
| `engine07.py` | `E575DD69C56248779562AEE4BD11E8901B73938B0CB0707927480BDBE3A82638` | updated |
| `stage002.py` | `84A4E14D86101BD102A4B0ACA2418A6CA886A96720C06E1F91A8EB8EB0BEFDB0` | updated |
| `calibration_executor.py` | `D00E5B44B532377BD69E454AD1AB20C1710A435420D51C00DDD7E462A80BDBC2` | updated |
| `calibration_runner.py` | `74310BE41E2086AB979C2F18E0A4001D9552AEE5D5B3EED9D1EF5545B571939D` | unchanged |
| `card_interpreter07.py` | `428A1088E26B7FB6A209E7A360B0FAD50E1FC675AF815E7D86DEFAB94D7DB426` | unchanged |
| `pilot07.py` | `CF24950340F6BD54D77302D89A2FBDB99DAE64BDEA3948117108B32F18392563` | unchanged |
| `pilot_input_v2.py` | `C0B608B77473313CC4D1A8DBE19B091742EAD2111CDFD702B937C509316D6BE5` | unchanged |

The accepted fix exposes terminal status from Game.winner and turns_started from Game.turn, requires the exact executor contract, and stops Stage 002 before beginning turn 120. The strict runner, Pilot and interpreter are unchanged. No additional runtime changes are introduced here.

## Preserved freeze and dispositions

Protocol identity remains `96fc43ec3203938eb385618f6187f8496b93ecd3`. Exact deck, corpus, catalog and seed identities remain unchanged and are enumerated in the JSON. Capacity evidence and semantic/Pilot dispositions are carried forward without reinterpretation. The 184,320-game / 368,640-execution design, exact duplicates, no truncation or replacement seeds, and first-material-failure stop remain unchanged.

The JSON binds all tracked prior Calibration V1 run artifacts and the first stop record. The latest attempt is byte-identical to accepted PR #136, including its raw failure evidence and sidecars. No historical failure is replaced or promoted into calibration observations.

## Verification and authorization

Static checks verified the exact three changed runtime sources, unchanged Git bytes and accepted checkout hashes for frozen inputs, preservation of prior stops, and sidecars for the latest failed attempt. The accepted fix's exact-head CI run is `34910135535`; accepted stop CI is `34906314314`. This refresh performs no new game execution or capacity benchmark. CI on the refresh PR independently runs the repository checks.

The JSON and this note have SHA-256 sidecars, and Git attributes preserve their exact bytes. This is a documentation-only release refresh, not authorization to execute Calibration V1. No balance analysis or Prototype 0.3 work is authorized.
