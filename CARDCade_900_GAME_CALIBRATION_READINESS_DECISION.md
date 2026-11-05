# Cardcade 900-Game Calibration Readiness Decision

**Date:** 2026-11-03  
**Scope:** Read-only review of the 450-game exploratory record and targeted Casey evidence correction  
**New gameplay:** Not authorized or run

## Decision

**BLOCKED — SPECIFIC MATERIAL FIDELITY DEFECT**

The Casey Jones artifact-selection concern is resolved as an interpretation error in the synthesis, not a demonstrated gameplay defect. One narrower, potentially consequential evidence gap remains in `Does Machines` Level 3. Before using a 900-game run to compare deck functionality, verify that this path executes and is evidenced correctly. This is a readiness blocker due to uncertainty, not a claim that the engine’s observed result is wrong.

## Casey correction

The focused review in [`CARDCade_CASEY_JONES_ARTIFACT_SELECTION_FIDELITY.md`](CARDCade_CASEY_JONES_ARTIFACT_SELECTION_FIDELITY.md) found the tested implementation and evidence correct. Reconciliation of the 300 preserved snapshots against the frozen Stage 002 manifest classified all **126 Casey Jury-Rig occurrences in 84 games as `executed`**. The commit events, evidence ledger, and authenticated execution references matched.

The raw snapshot field still labels those occurrences `reached_unsupported`. Preserve the raw 3,025 occurrence count and its historical raw labels; do not treat this engine-level label as Stage 002’s final classification. The dated addendum in [`CARDCade_450_GAME_EXPLORATORY_SYNTHESIS.md`](CARDCade_450_GAME_EXPLORATORY_SYNTHESIS.md) records both views without rewriting telemetry.

The full frozen-manifest reconciliation of the 300 snapshots yielded:

| Final Stage 002 class | Occurrences |
|---|---:|
| `executed` | 460 |
| `reached_unsupported` | 119 |
| `present_unreached` | 2,446 |
| **Total** | **3,025** |

## Remaining material gap

The most frequent remaining reconciled `reached_unsupported` family is `Does Machines`, `{4}{U}: Level 3`: **62 occurrences across 46 games**. The authoritative card data says the level grants an ability that, at the beginning of combat on its controller’s turn, puts three +1/+1 counters on a target artifact they control and makes it a 0/0 Robot creature if it is not already one. That can change board development and combat, so absent authenticated execution evidence could bias conclusions about Donatello’s deck function.

Existing evidence does not demonstrate that the engine applied the effect incorrectly, nor that any winner changed. It does establish that this ability remains `reached_unsupported` after frozen-manifest reconciliation, leaving behavior or evidence unverified. This is the single most consequential documented gap for the planned calibration. No broad card-by-card review is proposed.

The full-snapshot reconciliation emitted 485 `silent_approximation` stop records across the broader batch. Their non-Casey causes remain outside this focused assessment; this report does not interpret or clear them. Other unsupported mechanics and the previously recorded post-terminal step marker remain fidelity qualifications. Prior reports did not demonstrate those markers changed a game outcome.

## Calibration value and limits

The completed 50-, 100-, and 300-game batches provide useful exploratory evidence: the 300-game schedule covered all 45 pairings, with 60 appearances per deck and 30 games per seat. All ten decks recorded wins and losses. These observations support continued preparation, but not certified balance rankings. The unresolved Level 3 path could affect the Donatello portion of a calibration intended to compare all ten decks, so the present record is not sufficient to treat that calibration as reliable across the full environment.

Once that single path is reconciled, a useful 900-game schedule would cover each of the 45 unordered pairings 20 times, split evenly across seat orientations (10 each), with fresh deterministic seeds. Execute sequentially through the existing validated system, preserving per-game raw telemetry, authorization and artifact verification, and block checkpoints. Classify each result with the frozen Stage 002 reconciler and qualify unresolved mechanics; do not promote win rates to balance proof. This is schedule guidance only, not a manifest or execution authorization.

## Exact next action

Run a **targeted synthetic and preserved-telemetry reconciliation for `Does Machines` Level 3 only**. Establish whether its observed occurrences have correct effect resolution and matching authenticated evidence; if behavior is correct but evidence is missing, identify the smallest evidence correction. Do not run a game. Reassess 900-game readiness after that finding and keep the broader Stage 002 stop-record review separate unless specific evidence connects it to this mechanic.

No decks, simulator code, historical telemetry, authorization records, or execution artifacts were modified. No games were launched.
