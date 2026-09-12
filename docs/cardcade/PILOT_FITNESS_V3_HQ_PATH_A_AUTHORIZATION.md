# HQ Decision: Path A Authorized

HQ authorizes execution of the original 288 reconstructable non-privacy Pilot Fitness V3 calls. This decision follows the Privacy Seal Defect Return to HQ at `4bb9ed61c6f1080dfec7b4a38d91261ff204de52`.

- Authorized scope: 12 fixtures x 2 seats x 3 variants (canonical, option permutation, runtime-ID rename) x 2 replays x 2 Pilots = 288 calls.
- Privacy: the extra 96 calls for 24 privacy seat-version pairs remain INCONCLUSIVE / unexecuted.
- Privacy Addendum: NOT AUTHORIZED. No new privacy states or retrospective reconstruction claims are authorized.
- Fixtures, oracles, Pilot policies, gameplay implementation, and original pre-run seal remain frozen. The 288-call execution correction must preserve their authority and report actual returned actions against the sealed expectations.
- Pilot Fitness remains unknown pending genuine execution and HQ review. Filtering remains INCONCLUSIVE / unchanged. Calibration remains blocked.

## Continuity and evidence status

Preserve Specification V3 `c18a8fc`, original pre-run seal `9fb8574`, invalid synthetic scoring attempt `32e692b`, genuine two-call proof `37054b7`, current proof runner `efe0968`, and privacy defect assessment `4bb9ed61`.

The rejected generic-state attempt `b353537` and the subsequent reconstruction-stop record remain historical evidence. Inclusion of rejected attempts or old scoring artifacts in the synchronization PR does not accept their results. The proof demonstrates actual Pilot/control separation on one fixture; it does not score the full suite. This decision supersedes the pending Path A/Path B choice in the defect assessment without rewriting that assessment or the original seal.

## Mainline synchronization scope

The synchronization PR carries existing V3/Pilot Fitness history through `4bb9ed61` and this decision record. It adds no gameplay work, cleanup, new fixture design, or scoring results. No additional scoring or proof calls are performed while preparing the PR. The current runner remains proof-only; Path A execution implementation and the authorized 288-call run are subsequent work.

Open the synchronization PR against `main`. Do not merge automatically. Authorization to execute Path A is recorded here; it is not a claim that execution has occurred or that calibration is approved.
