# Calibration Readiness Gate — after PR #109

**Calibration remains BLOCKED. Pilot Fitness V3 has an HQ-accepted bounded demonstrated-surface PASS.** The remaining critical path is gameplay-semantic coverage and prospective experiment readiness. This is a consolidation packet for HQ review, not an accepted Calibration Protocol, architecture commission, or execution authorization.

Prepared 2026-09-12 against mainline merge `803570a6ebf8e43b143abf43ac2a046455cf7a96`. PR [#109](https://github.com/egggggman/tmt/pull/109) merged normally at 21:00:48 UTC, preserving predecessor evidence and remediation history. Its parents are `77b1228dab31640ca08f56a00007e163e827ca77` and accepted head `a6c96370dfa812faf5606d8a1a101d544718c17d`. Local main and origin/main matched the merge SHA with a clean working tree before packet preparation. This packet is isolated on a documentation branch.

## 1. Authority and current gate

| Item | Disposition |
|---|---|
| Pilot Fitness remediation | ACCEPTED by HQ through `8d6519de`; integrated through PR #109 |
| Pilot Fitness V3 | PASS on the demonstrated surface only; not general strategic competence |
| Privacy | INCONCLUSIVE / unexecuted; no privacy clearance inferred |
| Filtering hooks | INCONCLUSIVE; hand-bottom/Draw and discard/Draw competence not established |
| Calibration | BLOCKED; separate protocol and execution acceptance still required |
| Decks / Prototype 0.2 | FROZEN; existing roster versions and ordered deck contents preserved |
| Action #33 / Prototype 0.3 | NOT AUTHORIZED |

The current HQ decisions in this thread govern the status above. Historical documents saying Pilot acceptance is missing or that remediation awaits HQ remain unchanged as source-time records. V3 supersedes earlier fixed-quota preparation methodology; this packet does not revive those quotas or initiate further Pilot work.

## 2. Evidence baseline and its limits

The [post-Action #32 gate audit](POST_ACTION_32_ENGINE_VALIDATION_GATE_AUDIT.md) is the semantic disposition source. Its accepted candidate-time Smoke measured 45 pairings, 180 distinct games / 360 duplicate executions: 114 coverage-complete, 66 coverage-limited, zero invalid; 495 EXECUTED, 111 REACHED-UNSUPPORTED, and 1,530 PRESENT-UNREACHED occurrences. Stops, invariant violations, and duplicate mismatches were zero. Every game remained `balance_valid: false`.

These are banked engine-validation findings, not newly measured results on the merged Pilot. Exact duplicate executions do not increase statistical sample size. Exposure counts below are raw distinct games / occurrences, overlap across rows, and establish neither payable/beneficial decisions nor causal changes in winners. A different policy can expose additional semantics even with frozen decks. Coverage percentages and clean CI do not quantify calibration error.

## 3. Five must-resolve gameplay-semantic families

These remain blockers for unrestricted printed-gameplay ten-deck calibration. Closure requires separately scoped and accepted semantics with evidence for the complete relevant lifecycle; no implementation is commissioned here. A different reduced-model question would require an explicit prospective HQ authorization and a different claim, not a silent waiver.

| Family | Banked exposure | Required closure and qualification |
|---|---:|---|
| Menace: Splinter, Bebop, Raphael | 24 games / 24 occurrences | Legal multiple-blocker choices, allocation, and strike/Trample/evidence interactions. Existing one-to-one blocking cannot represent this restriction. Neither single-blocker permission nor treating Menace as unblockable is acceptable. The 72 legal-block-context witnesses are not measured outcome deltas. |
| Leonardo graveyard casting and finality | 13 / 15 | Qualifying graveyard casting permission, cost/payment and timing, incarnation identity, finality entry, and death-to-exile replacement as a linked lifecycle. The 29 candidate contexts do not prove 15 payable casts; payment applicability needs confirmation during scoping. |
| Paramecia death/exile/reflexive creature return | 12 / 13 | Optional exile of the death incarnation, reflexive trigger ownership, target availability/legality, and graveyard-to-library return with correct ordering and terminal handling. Accepted ETB mill does not close this sibling. Death witnesses do not each prove a useful return target. |
| Raphael linked exile and attack-time play | Each linked row 6 / 6 | Optional Alliance top-card exile plus authoritative source-linked card access; later land/spell legality, payment, timing, permission lifetime and expiry. Treat both rows as one resource-access program. Nine entry and eight attack witnesses do not prove six playable exiled cards. Exile alone is not closure. |
| Ooze Spill counterspell / Mutagen outcome | 2 / 3 | Instant response casting, target/counter resolution, token outcome, and relevant token activation/payment dependencies. Five Stack-response contexts are exposure, not simulated alternative decisions. Accepted activated counters do not certify the instant transaction; low exposure is not a waiver. |

The six residual rows represent five families because Raphael's two fragments are coupled. The audit groups them as 67 occurrences across 51 games; that game count overlaps the deferred and terminal groups and must not be added to them.

## 4. Deferred risks and terminal-only evidence

“Deferred” means implementation selection awaits applicability and protocol disposition, not harmlessness or permanent exclusion.

| Risk | Banked exposure | Required disposition before a dependent calibration claim |
|---|---:|---|
| Tunnel Rats graveyard self-return tapped | 16 / 19 | All 47 witnesses use battlefield sources, not authenticated graveyard activation/payment. Preserve deferral to future Priority/timing scope; establish actual zone, cost and timing applicability. No main-phase-only substitute. Reconsider if the chosen question needs faithful recursion. |
| Frog Butler mana of any color | 8 / 8 | Fifteen witnesses borrow the `{2}` Reach context with no tap-source requirement. They do not establish the mana ability's untapped/sickness/color/payment conditions. Resolve payment/color-access applicability and potential acceleration impact before claiming fidelity. |
| Frog Butler temporary Reach | 8 / 8 | Fixed-cost main-phase contexts do not prove a flying attacker or usable defensive window. Settle defensive timing/choice requirements; no unrestricted Reach claim from main-only activation. |
| Michelangelo extra +1/+1 counter replacement | 1 / 1 | The sole witness concerns stun, not +1/+1. Reassess the actual replacement predicate and composition dependency; neither a mandatory implementation decision nor irrelevance follows from that row. |

These four rows account for 36 occurrences across 24 overlapping games. Applicability defects in historical witnesses must not be repaired by relabeling original evidence in this packet.

Zoo Escapees (5 / 5) and Casey Jones, Vigilante (3 / 3) are the eight terminal-only occurrences: accepted obligations remained pending at actual game end. They do not establish missing token delivery or missed due-upkeep discard. Preserve conservative incomplete-chain credit; do not extend completed games to manufacture execution. A new, authenticated missed obligation would require separate diagnosis.

## 5. Pilot acceptance and explicit exclusions

HQ accepted the demonstrated surface after the [four-fixture remediation](PILOT_FITNESS_V3_REMEDIATION_96_REPORT.md): 96 actual scoring hook invocations, 96 legal returns, zero exceptions. AcceptancePilot matched 12/12 for each of Priority/T, Scry/R, Sneak/B and Main/B. PassingPilot matched 0/12 on Priority/T and Scry/R, and 12/12 on both boundaries. Normalized outcomes were stable across the declared seats, option permutations, runtime-ID renaming and replays.

Original genuine 288-call evidence at `d880c36` and diagnosis `decb9eb2` remain intact. The correction is separate evidence, not a rewritten original score or a new pooled calibration sample. The original Sneak/T winner-null limitation also remains: matching its sealed cast is not independent lethal-play proof. See the [original report](PILOT_FITNESS_V3_PATH_A_288_REPORT.md) and [diagnosis](PILOT_FITNESS_V3_FAILURE_DIAGNOSIS.md).

The accepted Priority observation is PriorityViewV2; the historical runner and test now conform. Final integrated-head validation recorded 51 focused tests and 1,353 full tests passed / 1 skipped, with Ruff and exact-head PR CI green. These are prior validation results, not tests rerun during packet preparation.

The PASS does not establish general strategy, long-horizon optimization, all decision ownership, hidden-information noninterference, filtering competence, or fitness on newly implemented semantics. Privacy remains INCONCLUSIVE/unexecuted; filtering remains INCONCLUSIVE. The prospective protocol must state the information entitlement and engine-default/runner-owned decisions for its actual domain, and explicitly disposition these exclusions. It cannot silently widen the accepted PASS. No further Pilot investigation or implementation is authorized by this packet.

## 6. Prospective Calibration Protocol requirements

The [checkpoint audit](POST_ACTION_30_ENGINE_VALIDATION_CHECKPOINT_AUDIT.md), [Smoke balance boundary](COVERAGE_AWARE_ENGINE_SMOKE_STAGE_0.1_SPEC.md), and [Stage 0.2 balance firewall](COVERAGE_AWARE_ENGINE_VALIDATION_STAGE_0.2_SPEC.md) require a separate predeclared experiment. The following is a readiness checklist, not a selected design. Numeric sample sizes, thresholds and analysis choices remain UNSET pending that protocol and HQ review.

| Required protocol element | Concrete deliverable needed before execution |
|---|---|
| Question and claim | Named calibration target, estimands, intended roster/domain, permitted conclusions and decision uses. Explicit full-gameplay versus separately authorized reduced-model scope. |
| Semantic eligibility | Closure evidence for the five families, dispositions for deferred risks and unknown applicability, and prospective inclusion/exclusion rules. No selecting the 114 coverage-complete historical games after seeing labels. |
| Frozen inputs and decision ownership | Exact commits/hashes for catalog, ordered decks, engine/interpreter, Pilot, observation schema, runner, evaluator and dependencies; all chooser/default/response scheduling responsibilities and permitted information. Preserve deck freeze. |
| Sampling and independence | Predeclared matchup membership, mirror-match disposition, seeds, orientations, repetitions, randomization and sample-size rationale. Define the analysis unit and handle paired seeds/seats and dependent comparisons; determinism duplicates are not independent observations. |
| Endpoints and analysis | Primary/secondary metrics, aggregation/weighting, uncertainty method, multiplicity treatment where relevant, practical decision thresholds and sensitivity analyses before outcomes are inspected. No retrospective thresholds or resource exchange rates. |
| Stops and deviations | Predeclared turn-cap/incomplete-game treatment, drift checks, mechanical/integrity stops, unsupported/unknown applicability handling, retry/restart policy and failure preservation. No silent seed substitution, selective retry or outcome-based exclusion. |
| Reproducibility and audit | Frozen plan before gameplay; complete per-game inputs, choices, authoritative events/identities, RNG and terminal evidence, duplicate comparison, raw results and sidecars. Independent reconstruction before interpretation; preserve failed attempts. |
| Release gate | HQ acceptance of the prospective protocol and its frozen readiness packet, followed by explicit execution authorization. Calibration findings do not themselves authorize deck changes or Prototype 0.3. |

Older Stage/Smoke matrix sizes, seed schedules, turn caps and historical blocked Action numbers belong to their own experiments. They are not automatically the future calibration design. Historical balance-invalid artifacts remain validation evidence; this packet changes no balance flag and performs no new experiment.

## 7. Explicit remaining blockers and next review

1. **Gameplay fidelity:** the five material semantic families have no closure supplied by this merge or packet. Unrestricted ten-deck calibration remains blocked on their accepted disposition.
2. **Applicability and claim boundaries:** deferred semantic risks, unknown/unreached exposure, decision ownership, privacy and filtering exclusions need explicit treatment for the eventual question. Bounded Pilot PASS is accepted and is not reopened; broader suitability is not implied.
3. **Prospective experiment design:** no accepted calibration-specific question, frozen eligible population, sampling/independence design, analysis/uncertainty method or decision thresholds are supplied here. Existing validation runs cannot supply them retroactively.
4. **Execution readiness and authority:** a future frozen baseline and protocol still require independent readiness review and HQ execution authorization. This packet grants neither.

HQ's next review can accept or revise this register and commission prospective protocol specification and any separately bounded semantic architecture scoping it requires. This is a proposed decision sequence, not a work authorization or automatic Action #33 selection.

## 8. Packet verification

Preparation used committed records and repository metadata only: zero games, Pilot calls, scoring runs, or new test executions. The accompanying source manifest binds exact committed Git blobs with SHA-256 over `git show <merge>:<path>` bytes, avoiding checkout line-ending ambiguity. The original evidence, source code and decks are unchanged. Packet Markdown, source manifest and their SHA-256 sidecars are the only deliverables. Link targets, recorded ancestry, artifact hashes, changed-path scope and whitespace are checked before handoff.
