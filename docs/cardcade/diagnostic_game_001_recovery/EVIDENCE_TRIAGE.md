# Diagnostic Game 001 — Read-only Evidence Triage

## Scope and provenance

This report analyzes the preserved Diagnostic Game 001 artifacts from [PR #406](https://github.com/egggggman/tmt/pull/406). It does not execute or reconstruct a game and does not modify any original artifact.

- Game source: PR #404 / `67b9bb3083c9f4b2fe02e7fed258c4739581225f`.
- Report artifact branch: `reports/cardcade-diagnostic-game-001`, report commit `51789292867bddfc364817d389c12294fb74a79c`.
- Match: `april-casey:canonical:7231`, April seat 0 vs Casey seat 1.
- Original output: `C:\projects\tmt\.cardcade-diagnostic-001-pr404-67b9bb3-20261107`.
- Raw PR references: [`run_metadata.json`](https://github.com/egggggman/tmt/blob/reports/cardcade-diagnostic-game-001/docs/cardcade/diagnostic_game_001/evidence/run_metadata.json), [`snapshot.json`](https://github.com/egggggman/tmt/blob/reports/cardcade-diagnostic-game-001/docs/cardcade/diagnostic_game_001/evidence/snapshot.json), [`events.json`](https://github.com/egggggman/tmt/blob/reports/cardcade-diagnostic-game-001/docs/cardcade/diagnostic_game_001/evidence/events.json), [`reconciliation.json`](https://github.com/egggggman/tmt/blob/reports/cardcade-diagnostic-game-001/docs/cardcade/diagnostic_game_001/evidence/reconciliation.json), [`exception.json`](https://github.com/egggggman/tmt/blob/reports/cardcade-diagnostic-game-001/docs/cardcade/diagnostic_game_001/evidence/exception.json), and [`artifact_sha256.json`](https://github.com/egggggman/tmt/blob/reports/cardcade-diagnostic-game-001/docs/cardcade/diagnostic_game_001/evidence/artifact_sha256.json).

Key preserved SHA-256 values: snapshot `53092f2e688c6b6f158d5012419a95fa31f948bbcb115184a13809e65962142a`; events `e25d42bb57d75bc9ae0d1400d3abc840a67c9908f28c35e0d26a6ff31b245bec`; reconciliation `7e943b7cde607cff0bea4018447a4b33f6a74244d2efb997a6fd7be875a65425`; exception `d9c2de38b2604a149eec2b693e337bc7ed36713f202f8d4050bb16660b2dd3d3`.

## Finding 1 — `illegal_mutation` after lethal combat

**Classification: engine/driver control-flow defect; the stop label overstates what the evidence proves.**

Reconciliation stop `stop-000001` records:

- turn 16, combat / `combat_damage`, detail `combat damage`;
- before fingerprint `4d879f93d071a91dd5fcf2a704555a54ef9132d4ea879296a494ae0a5923e7fe`;
- after fingerprint `56108c933cade87eae357882f5f6a23daa1fa5b318bfabda768d1c92638aeb52`.

The raw event tail orders the events as three player-damage records, `player_lost` for April (`life_zero_or_less`), and `combat_damage_step_resolved`. The terminal snapshot then records April at −5, Casey at 17, Casey as winner, `terminal=true`, empty Stack, and no priority. The saved exception is raised after those events when `_advance_after_combat_damage()` calls `transition_to(END_OF_COMBAT)`, which correctly rejects advancing a terminal game.

Stage 002's `_checked_action()` records `illegal_mutation` whenever an operation raises after the authoritative fingerprint changes. Here the mutation is the requested damage and resulting terminal state; the exception is the subsequent forbidden step transition. Thus the record is reproducible as a real engine/runner control-flow defect, but it is not evidence that combat damage itself was an illegal mutation. The original stop record remains untouched.

A synthetic correction was separately reproduced on PR #404 source and is covered by the correction PR: terminal combat continuation now returns without calling `transition_to`; explicit post-terminal calls to `transition_to` remain rejected.

## Finding 2 — `presence_evidence_missing`

**Classification: diagnostic evidence-capture defect; not a missing gameplay effect.**

The failed `run_game()` call never reaches its normal finalization, where it attaches `stage002_presence`. The one-shot wrapper attempted recovery from the exception traceback. Its frame search overwrote the selected frame with every deeper frame containing a local named `game`; the innermost matching frame is `_checked_action(game, ...)`, which has no `presence` local. The wrapper then sees `presence=None`, skips `_add_created_token_presence()` / `_finish_presence()`, and serializes a snapshot without `stage002_presence`.

The saved `snapshot.json` confirms the field is absent, and `reconcile_snapshot()` adds `silent_approximation: presence_evidence_missing` when the field is not a list. The full `run_once.py` and exception traceback preserve this chain. A corrected exception collector would select the `run_game` frame holding both `game` and `presence`, or otherwise pass the presence ledger explicitly. This report does not patch the historical wrapper or backfill the old snapshot.

## Finding 3 — trample/combat execution references

**Classification: evidence authentication blocked by Finding 2; no trample gameplay defect established by this stop.**

The other `silent_approximation` stop's detail is the list of execution evidence IDs that the reconciler could not fully authenticate because it requires a source-presence lineage. It contains 28 references:

- 17 `trigger_resolved` references: `event-000035` / source `object-000164`; `event-000036` / `object-000156`; `event-000041` / `object-000141`; `event-000049` / `object-000164`; `event-000051` / `object-000175`; `event-000054` / `object-000184`; `event-000058` / `object-000164`; `event-000060` / `object-000175` and `object-000192`; `event-000063` / `object-000145`; `event-000065` / `object-000175` and `object-000192`; `event-000066` / `object-000218`; `event-000072` / `object-000164`; `event-000073` / `object-000204`; `event-000076` / `object-000175` and `object-000192`.
- 6 activated-ability references: `object-000150`, `object-000154`, `object-000173`, `object-000190`, and `object-000202` from source `object-000145`; `object-000231` from source `object-000218`.
- 2 damage references: `event-000067` and `event-000068`, source `object-000218`.
- 1 Food activation: `object-000231`, source `object-000218`.
- 1 token creation: `event-000064`, source `object-000145`.
- 1 trample reference: `combat:1:object-000175:trample`, source `object-000175`.

An offline check of the preserved snapshot (no game execution) compared all 28 references against the frozen Stage 002 manifest and `_authoritative_execution_index()`: **28/28 have a matching semantic key/Oracle fragment and a matching source/evidence identity**. The reconciler still cannot authenticate them because the final `execution_is_authenticated()` condition also requires the source ID to occur in `stage002_presence`, which the exception wrapper omitted.

The trample source `object-000175` is Casey's **Mutant Town Musicians**, whose preserved card characteristics include `Trample` and the Alliance ability. The snapshot's combat-damage evidence contains trample-marked assignments for this source, including assignments to creatures and to a player. The exact evidence reference is therefore present and matches the frozen `Trample` fragment and the source-specific combat evidence index. The stop identifies a lineage/authentication gap, not an unsupported trample keyword implementation. Since this was a single run and the full presence history is missing, this analysis does not independently certify every historical source-zone transition or the strategic correctness of damage assignment.

## Conclusions and limits

| Stop | Conclusion | Remaining uncertainty |
| --- | --- | --- |
| `illegal_mutation` | Same terminal-transition defect fixed by the separate correction candidate; damage/loss events precede the forbidden transition. | Independent review must verify the code correction. Original stop stays in PR #406. |
| `presence_evidence_missing` | Exception-wrapper frame selection omitted the `run_game` presence ledger. | Historical presence cannot be reconstructed completely from the incomplete snapshot without rerunning; no backfill is claimed. |
| trample/combat references | 28 references pass static semantic and authoritative evidence-index identity checks; the reconciler lacks required presence lineage. No gameplay defect proven. | Full evidence lineage and broader trample behavior need a future authorized checkpoint if required. |

No complete game, smoke, retry, calibration, merge, deck change, baseline promotion, or historical artifact modification occurred during this triage. This report is documentation-only and does not change PR #406 or its raw evidence.

**Recommendation: BLOCKED for another diagnostic game until independent acceptance of the terminal correction and HQ review of evidence capture.**
