# Engine Validation Checkpoint Audit — post-Action #30

**Recommendation: NOT READY for calibration.**

Exact evidence base: `dea15960904696901f255e34aac26bebd2e0a735`.
Authoritative Action #30 merge: `1c54dd755d97b9a963589c32e76bc66526a1132a`.
Accepted candidate: `ff1aece11d9811c5e50d67821d2277a1f903ee7f`.

The represented engine passes this checkpoint's mechanical and evidence-integrity review. Calibration is blocked by observed gameplay omissions in the wider frozen roster and two concrete missing validation deliverables: a Pilot fitness assessment for the intended calibration question and a predeclared calibration sampling/analysis protocol. No current foundational state-corruption, nondeterminism, or evidence-authentication defect was found in the reviewed artifacts. This is a recommendation for HQ review, not authorization for any further implementation or experiment.

## Scope and method

Started on clean main at the exact evidence base above. Read committed artifacts and their sidecars, checked current source identities against the preserved validation record, reran saved-artifact validators, reconstructed all 16 merged Stage reports, and examined the current Smoke residual witnesses and balance-exclusion records. No production, test, deck, Pilot, runner or historical artifact was changed. No Stage or Smoke game was run. Existing artifacts answer every audit question; additional executions would not resolve the blockers listed below.

Current evidence reviewed:

- [Merged Stage result](POST_ACTION_30_MERGED_STAGE_002_RESULTS.json), [inventory](POST_ACTION_30_MERGED_INVENTORY.json), [remaining ranking](POST_ACTION_30_MERGED_UNSUPPORTED_RANKING.json), and [transaction chains](POST_ACTION_30_MERGED_TRANSACTION_CHAINS.json).
- [Full Smoke artifact](POST_ACTION_30_SMOKE01_RESULTS.json.gz), including both duplicate snapshots for every game.
- [Preserved validation record](POST_ACTION_30_VALIDATION.json) and [candidate handoff](POST_ACTION_30_CANDIDATE_HANDOFF.md).
- [Smoke specification](COVERAGE_AWARE_ENGINE_SMOKE_STAGE_0.1_SPEC.md), especially the balance/deck-observation boundary and conditions 6–7; [Smoke runner acceptance](SMOKE_EVIDENCE_RUNNER_ACCEPTANCE_02.md); [Milestone Review #2](CARDCade_ENGINE_VALIDATION_MILESTONE_REVIEW_02.md), coverage-complete versus balance-valid; and the corresponding [Stage 0.2 balance firewall](COVERAGE_AWARE_ENGINE_VALIDATION_STAGE_0.2_SPEC.md).
- Frozen `src/tmnt_design_studio/pilot07.py`: AcceptancePilot is a deterministic acceptance strategy; its code includes fixed option priorities and acceptance-specific card choices. Determinism and legal-option selection do not establish fitness for a calibration question.

The historical documents supply definitions and validation criteria only. Their older Action counts and execution gates are not substituted for the current evidence or treated as new authorization.

## Mechanical and evidence findings

| Check | Finding |
|---|---|
| Merged Stage matrix | 16 distinct games / 32 executions; frozen manifest reconstructs |
| Merged Stage classifications | 30 EXECUTED / 1 REACHED-UNSUPPORTED / 133 PRESENT-UNREACHED |
| Stage duplicates and reports | Exact duplicates; all 16 reports independently reconstruct |
| Stage stops / invariant violations | 0 / 0 |
| Stage continuity | Preserved inventory reports no lost prior EXECUTED occurrence; fresh result is identical to accepted candidate evidence |
| Jury-Rig | 3 complete Stage and 68 complete Smoke transactions; mature transaction evidence required for execution credit |
| Wider Smoke | 45 pairings, 180 distinct games / 360 executions; full saved result validator passes |
| Smoke mechanical labels | 105 clean coverage-complete; 75 clean coverage-limited; 0 invalid |
| Smoke stops / invariant violations / duplicate mismatches | 0 / 0 / 0 |
| Smoke residual exposure | 133 reached-unsupported occurrences across 16 card/fragment clusters |
| Balance validity | All 180 per-game future-balance records explicitly have `balance_valid: false` |
| Accepted tests | Preserved final record: 60 focused; 218 focused/regressions; 1,155 full passed, 1 skipped; not rerun during this evidence-only audit |
| Frozen source continuity | All six production/test Git blob identities in the Action #30 validation record match this exact evidence base |

The one Stage residual is the terminal-pending Vigilante obligation in `april-casey:canonical:7231`; it is not evidence of failed due-upkeep delivery. Present-unreached rows are not automatically engine defects. Neither row class alone warrants an implementation program or Action #31.

Smoke is the accepted candidate-time artifact, not a newly run merged-baseline Smoke. Its `execution_commit` records `40149d0ca6d231af7dd46aae30ce67446e8670b4`, the precommit working-tree HEAD when it ran. Its authenticated frozen source identities match the final candidate and this audit base. Comparing its manifest to today's reconstructed manifest yields only the expected `execution_commit` and derived `manifest_digest` differences; all other fields, source inputs and matrix membership match. The original artifact was not rewritten to substitute a later SHA.

## Concrete calibration blockers

### B1 — Material reached gameplay remains omitted in the wider roster

Closing Stage #002's Jury-Rig gaps did not close the broader Smoke gaps. The following are concrete authenticated witnesses from `aggregate.games[*].occurrences`, joined through matching semantic keys and object lineage to `presence`:

| Missing represented behavior | Occurrences / distinct games | Exact example game and object |
|---|---:|---|
| Paramecia Coloniex enters: mill three cards | 22 / 17 | `april_oneil--bebop_rocksteady:canonical:8001`, `object-000186` |
| Tunnel Rats: return itself from graveyard to battlefield tapped | 18 / 15 | `april_oneil--splinter:canonical:8017`, `object-000156` |
| Paramecia Coloniex dies: optional exile followed by targeted graveyard-to-library return | 16 / 12 | `april_oneil--bebop_rocksteady:reversed:8001`, `object-000143` |
| Leonardo, Sewer Samurai: graveyard casting with finality entry/death handling | 15 / 13 | `april_oneil--leonardo:canonical:8009`, `object-000197` |
| Krang, Master Mind: conditional hand refill toward four cards | 7 / 6 | `donatello--krang:canonical:8049`, `object-000246` |

These omissions affect zones, resources or legal plays; they prevent treating the affected games as faithful calibration samples. This finding does not assume every one of the 133 residual occurrences is an unimplemented rule: conservative terminal-pending or compound-semantic classifications require their own interpretation. The five concrete examples already establish the blocker. Game counts overlap and must not be summed as distinct games.

Closure criterion: the intended calibration domain must have accepted coverage of its materially reached rules, or a prospectively specified scope that excludes unsupported semantics without selecting games based on observed results. This audit neither requires complete Magic implementation nor selects the next Action. The present 105 coverage-complete games cannot simply be selected after the fact and treated as a valid calibration population.

### B2 — Pilot fitness for calibration has not been established

The existing evidence validates authoritative legal choices and deterministic replay. It does not validate whether AcceptancePilot's decisions are fit for a stated calibration question. The Smoke records explicitly identify absent Pilot/statistical-design gates, and the Smoke specification requires separate acceptance of the Pilot/version and decision policy. Repository searches of the preserved documentation found no superseding calibration-specific Pilot acceptance.

Closure criterion: a separately reviewed, frozen Pilot fitness assessment for the actual calibration question, including the decision-policy limitations relevant to that question. This does not imply a Pilot redesign is necessary; the missing deliverable is evidence of fitness, not an assumed implementation defect.

### B3 — No predeclared calibration experiment or analysis protocol

The preserved matrices were specified for conformance and engine robustness. Exact duplicate executions are replay proofs, not independent statistical observations. The current artifacts contain no accepted calibration target, predeclared sampling/inclusion plan, analysis method or uncertainty/decision criteria for translating their outputs into calibration changes. The Smoke specification explicitly leaves this separate statistical-design condition unsatisfied, and no superseding protocol was found in the reviewed repository documentation.

Closure criterion: a prospective calibration protocol defining the question, frozen inputs/Pilot, eligible scope, sampling and independence treatment, analysis and decision criteria before observing calibration outcomes. More runs of the existing validation matrix cannot supply that missing design retroactively.

## Integrity and reproducibility

Verified SHA-256 against committed sidecars:

- Merged Stage JSON: `8964047343cc6b49d4346a190ace49a8ca94186d5958797de47ae9debef9eaf5`.
- Compressed Smoke JSON: `7fce9bd9feab5a8e1d2075f9b0cbd8155923d8a433c5a505cf31724bcac22829`.
- Exact decompressed Smoke JSON: `ccbaa5dea3a76368be97782ded82c5610e3411f8e2b4877e3f4eb539e9ee4f38`.

Also verified the committed sidecars for the merged inventory, ranking, transaction chains and final validation record. `validate_stage_result_evidence`, all 16 `reconcile_snapshot` reconstructions, and `validate_smoke_result` passed using saved evidence. The latter independently reconstructs all 180 duplicate pairs, reports, mechanical labels, aggregates and balance exclusions. No artifact could be promoted to calibration evidence merely by rewriting its balance flag.

Only this audit and its SHA-256 sidecar are preserved by this checkpoint commit. Before commit, their staged scope, sidecar bytes and `git diff --check` are verified. No new simulation or production validation claim is inferred from this documentation-only commit.

## HQ handoff

**NOT READY for calibration**, for B1–B3 above. The represented engine is mechanically credible within the measured scope, and no new foundational repair is established by this audit. HQ can use this checkpoint to choose the calibration-domain and validation deliverables rather than infer that Stage #002 closure alone authorizes calibration.

Action #31 remains NOT AUTHORIZED. Calibration remains BLOCKED pending HQ's next decision. Prototype 0.3 remains NOT AUTHORIZED. No implementation, deck revision, Pilot change or experiment is authorized by this audit.
