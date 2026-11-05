# Cardcade Post-Merge Fidelity Readiness Reconciliation

**Audit reference:** accepted `main` at `e0855fc1f00f465121649cc6ceba24c269355e71` (2026-11-05).  
**Method:** read-only review of committed engine/test/documentation blobs and GitHub records. No tests, games, calibration, or deck changes were run or made.

## Disposition

**BLOCKED for unrestricted printed-gameplay calibration readiness.** The current mainline contains bounded implementations and deterministic regression tests for the five semantic families that the older Post-Action #32 audit had classified as calibration blockers. Does Machines Level 3 is now merged and passed its narrow safe-validation run. That is meaningful closure of synthetic implementation gaps; it does not update historical game classifications, demonstrate natural execution in the 300/450-game samples, or supersede the accepted calibration gate.

The controlling [Post-Action #32 Engine Validation Gate Audit](POST_ACTION_32_ENGINE_VALIDATION_GATE_AUDIT.md) still blocks calibration. Its classifications were made against an earlier engine identity. No accepted follow-up gate currently reconciles those classifications against the later implementation commits and tests.

## Current evidence crosswalk

| Historical concern | Evidence in accepted main | Reconciliation |
|---|---|---|
| Menace / multiple blockers | [`test_menace_action.py`](../../tests/test_menace_action.py) covers two-or-more blocker legality, rejection of a single blocker, ordered damage assignment, trample, deathtouch, strike steps, and deterministic option generation. | **Bounded synthetic behavior implemented and tested.** The historical 300-game report calls Menace a present-but-unreached family, not proof of a live error. Historical telemetry has not been reclassified or replayed. |
| Leonardo graveyard casting / finality | [`test_leonardo_graveyard_finality.py`](../../tests/test_leonardo_graveyard_finality.py) covers own-graveyard and P/T eligibility, timing and mana, stack/zone identity, finality entry, and death-to-exile replacement. | **Bounded lifecycle implemented and tested.** No historical occurrence-by-occurrence execution reconciliation was performed here. |
| Paramecia death / optional exile / reflexive return | [`test_paramecia_death_reflexive_return.py`](../../tests/test_paramecia_death_reflexive_return.py) covers declining, exile and return lineage, target invalidation, and ordinary death evidence. | **Bounded lifecycle implemented and tested.** It does not establish natural use or outcome impact in the preserved samples. |
| Raphael linked exile / attack-time play | [`test_raphael_linked_exile_attack_play.py`](../../tests/test_raphael_linked_exile_attack_play.py) covers source-linked exile, attack permission, land/spell use, turn expiry, and source departure/cross-source isolation. | **Bounded lifecycle implemented and tested.** Historical natural execution remains unreconciled. |
| Ooze Spill counterspell / Mutagen | [`test_ooze_spill_counterspell_mutagen.py`](../../tests/test_ooze_spill_counterspell_mutagen.py) covers opposing-stack legality, countering, token creation, payment/timing/target legality for Mutagen, replacement effects, and deterministic replay. | **Bounded compound path implemented and tested.** This is not a complete general-purpose priority or instant-response system. Historical natural execution remains unreconciled. |
| Does Machines Level 3 | [PR #377](https://github.com/egggggman/tmt/pull/377) merged at the audit reference. [Safe-validation run #42093334217](https://github.com/egggggman/tmt/actions/runs/42093334217) succeeded: Python 3.12.16, three source fingerprints and 28 explicit synthetic/authentication nodes validated; **28 passed**. The accepted regression file is [`test_does_machines_level_three.py`](../../tests/test_does_machines_level_three.py). | **Narrow correction verified and merged.** It restores legal Level 3 activation, trigger/effect handling, target and artifact state, replacement-counter behavior, and authenticated execution evidence. The pre-correction 62/46 Stage 002 classification is historical and remains unchanged; no game replay or retroactive reclassification was done. |

The test files above are committed on the audited mainline. This audit did not rerun them; only the cited safe-validation run is reported as a newly verified GitHub result here.

## Latest ledgers and evidence status

- [Post-Action #32 Engine Validation Gate Audit](POST_ACTION_32_ENGINE_VALIDATION_GATE_AUDIT.md) is the latest accepted semantic disposition ledger found. It records 114/180 coverage-complete and 66/180 coverage-limited candidate-time games, 495 executed, 111 reached-unsupported, 1,530 present-unreached, and says unrestricted ten-deck calibration is not ready. Its five must-resolve families predate the bounded implementations listed above.
- [Semantic Closure Planning — Post Calibration Protocol V1](SEMANTIC_CLOSURE_PLANNING_POST_PROTOCOL_V1.md) is explicitly **review candidate / planning only**, not a closure acceptance. It orders Menace, Leonardo, Paramecia, Raphael, then Ooze and states that calibration remains blocked.
- [Engine Foundation Matrix](CARDCade_ENGINE_FOUNDATION_MATRIX.md) is dated 2026-08-14 and describes a candidate-era foundation snapshot. Its general GREEN/YELLOW labels are not a current card-by-card acceptance ledger.
- [Donatello P0.3a Does Machines coverage](../design-studio/DONATELLO_P0_3A_DOES_MACHINES_COVERAGE.md) still says Level 3 is unsupported. That source-time record is superseded for implementation status by PR #377, but has not been amended.

## 300/450-game evidence and PR #375

The recovered [300/450-game synthesis and related reports](https://github.com/egggggman/tmt/pull/375) remain in **draft PR #375**, not accepted into main. Its synthesis preserves the raw 300-snapshot totals (3,025 semantic occurrences: 2,456 present-unreached and 569 reached-unsupported), then records the frozen Stage 002 reconciliation (460 executed, 119 reached-unsupported, 2,446 present-unreached). It identifies Casey's 126/84 occurrences as executed after authenticated reconciliation, while retaining the raw labels. It also records the pre-correction Does Machines Level 3 gap as 62 occurrences across 46 games.

Those numbers describe the preserved pre-correction sample. They are not corrected by the synthetic tests or PR #377. The report's 485 `silent_approximation` stop records are expressly outside the focused Casey analysis and remain unexplained there. The 450-game synthesis is exploratory evidence, not calibration acceptance. No source-time warning, snapshot, run record, outcome, deck baseline, or Stage 002 classification is changed by this reconciliation.

## Remaining blockers and next action

1. Calibration readiness has no accepted updated decision after the newer synthetic implementations. The older gate cannot be treated as cleared solely because matching tests now exist.
2. The accepted Post-Action #32 audit retains deferred applicability questions for Tunnel Rats graveyard self-return and Frog Butler mana/Reach. It found that recorded witnesses did not establish the exact zone, payment, color, or defensive-timing requirements. Resolve applicability against the intended experiment before claiming full-roster fidelity.
3. The 485 historical `silent_approximation` stops in the draft 300/450 reconciliation have not been causally or mechanically classified. They are unresolved evidence records, not demonstrated gameplay defects.
4. PR #375 requires independent review and HQ acceptance. Its recovery should remain separate from any calibration decision.

**Smallest next action:** independently review and accept (or correct) the evidence-only recovery in PR #375, then issue a new evidence-only readiness disposition that crosswalks the accepted targeted tests against the older gate and explicitly settles the deferred/stop-record items. Keep calibration blocked until HQ accepts that disposition. No gameplay or deck work follows from this report.
