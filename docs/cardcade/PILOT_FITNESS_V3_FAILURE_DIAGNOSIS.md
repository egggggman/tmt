# Pilot Fitness V3 Failure Diagnosis

**HQ decision: Pilot Fitness V3 = FAIL. Calibration remains BLOCKED.** This diagnosis does not replace that decision or revise any score.

Scoring authority: [`d880c36ecdb5a8ac3de3edfc92d5caa525ac05d2`](https://github.com/egggggman/tmt/commit/d880c36ecdb5a8ac3de3edfc92d5caa525ac05d2). Original seal: `9fb8574`; Specification V3: `c18a8fc`; execution runner/plan: `fe5cba6`; preserved proof: `37054b7`.

Scope is exactly V3-P1-004, V3-P2-001, V3-P2-004, and V3-P1-005. This is static source and existing-artifact inspection only: zero new Pilot invocations, no fixture construction, no code changes, no rescoring, no privacy work, no V4 proposal, and no deck/gameplay changes. The Sneak/T limitation is outside this requested diagnosis.

## Layer attribution

| Fixture | Primary diagnosis | Pilot interface/dispatch | Evaluator/comparison |
| --- | --- | --- | --- |
| V3-P1-004 Priority/T | Pilot policy: AcceptancePilot unconditionally passes a supplied counter opportunity | Additional fixture/capture defect: GameViewV2 supplied instead of PriorityViewV2; current policy ignores view, so this does not explain its selected pass | Correct literal comparison against sealed counter action |
| V3-P2-001 Scry/R | Fixture/oracle-seal defect: singleton excludes other actions meeting its written objective; not a demonstrated AcceptancePilot resource failure on this fixture | Correct ScryViewV2 and choose_scry dispatch | Correct literal singleton comparison; semantic inadequacy originates in sealed acceptable-set construction |
| V3-P2-004 Sneak/B | Fixture/seal timing defect: observation captured after the Sneak window, with zero options | Replay invokes the requested hook outside its normal actionable window; both policies assume a supplied pass | Exceptions correctly recorded; cannot be boundary-pass evidence |
| V3-P1-005 Main/B | Fixture/seal label contradiction: seven legal land plays plus pass | Correct main hook; explicit damage stage returns pass with no casts, but does not make the full option domain pass-only | Returned-pass predicate is true; it does not certify the mislabeled input domain |

## V3-P1-004: unconditional Priority pass, plus a separate input-contract defect

The existing run records 0/12 matches for each Pilot. Canonical raw calls 73/74 return `pass_priority` at epoch 1. The other supplied option is `activate_ability` from `object-000137` targeting stack object `object-000138`; that counter is the sealed acceptable action. The candidate branch table records the protected Bear as `gone` after passing and `battlefield` after the counter.

`AcceptancePilot.choose_priority` explicitly discards `view` and returns the first PASS_PRIORITY option. PassingPilot inherits this method without overriding it. Thus the observed miss is directly explained by policy, independent of observation content or option order. Supplying a richer view alone would not alter this current method.

There is also a material contract defect: the Phase 1 `capture` helper serializes `game.pilot_view`, and the replay decodes all non-Scry views as GameViewV2. Priority's annotated contract and normal stage runner instead use `game.priority_view`, exposing Priority context and Stack details. The sealed GameViewV2 lacks that data. The actual priority method was invoked, so this is not misrouting to main; however, it is not a clean PriorityViewV2 interface witness for a future view-sensitive policy. Do not attribute the missing public Stack observation to the engine.

Layer-specific conclusion for HQ: policy owns unconditional passing; the separate Priority fixture/input-contract issue must be accounted for when authorizing a meaningful rerun. Neither requires changing decks or engine mechanics. No fix is implemented or authorized by this packet.

Evidence at d880c36: [policy](https://github.com/egggggman/tmt/blob/d880c36ecdb5a8ac3de3edfc92d5caa525ac05d2/src/tmnt_design_studio/pilot07.py#L156), [capture](https://github.com/egggggman/tmt/blob/d880c36ecdb5a8ac3de3edfc92d5caa525ac05d2/scripts/build_v3_phase1_fitness_packet.py#L61), [fixture](https://github.com/egggggman/tmt/blob/d880c36ecdb5a8ac3de3edfc92d5caa525ac05d2/scripts/build_v3_phase1_fitness_packet.py#L187), [normal dispatch](https://github.com/egggggman/tmt/blob/d880c36ecdb5a8ac3de3edfc92d5caa525ac05d2/src/tmnt_design_studio/stage002.py#L411).

## V3-P2-001: sealed singleton contradicts the written Scry objective

The written objective is `top inspected card is a creature at the endpoint`. In canonical raw calls 193/194, **both inspected cards are Bears**, `object-000013` followed by `object-000012`; both public inspected-card descriptions have creature type. AcceptancePilot returns top `[object-000013, object-000012]`, bottom `[]`. Its first retained card is therefore a creature. PassingPilot returns top `[]`, bottom `[object-000013, object-000012]`; its outcome cannot be granted a resource success from this inspected-card comparison.

The sealed singleton is top `[object-000012]`, bottom `[object-000013]`. The builder computes `best = next(...)` over engine options whose first retained card is a creature, then seals only `[best]`. Four of the six supplied options retain a Bear on top, but the builder records only the first qualifying option and supplies no objective-based preference for that identity/partition. The order of option generation is not a resource justification.

AcceptancePilot's fixed keep-order policy is faithfully executed. On this specific observation it satisfies the written objective while failing exact membership in the frozen singleton. The runner's 0/12 literal scores remain correct and unchanged; the diagnostic distinction is that they do not establish a real AcceptancePilot resource mistake here. General Scry policy competence is not established either. A policy change merely to select that arbitrary singleton would overfit a defective oracle.

Layer-specific conclusion for HQ: investigate/authorize at the fixture-oracle layer before treating this result as justification for a Scry policy fix. This packet neither replaces the acceptable set nor recalculates scores or reclassifies the original run. The overall HQ FAIL remains recorded, including the independent Priority problem.

Evidence at d880c36: [Scry fixture and first-match singleton](https://github.com/egggggman/tmt/blob/d880c36ecdb5a8ac3de3edfc92d5caa525ac05d2/scripts/build_v3_phase2_candidate.py#L42), [keep-order policy](https://github.com/egggggman/tmt/blob/d880c36ecdb5a8ac3de3edfc92d5caa525ac05d2/src/tmnt_design_studio/pilot07.py#L130), [typed reconstruction](https://github.com/egggggman/tmt/blob/d880c36ecdb5a8ac3de3edfc92d5caa525ac05d2/scripts/run_v3_path_a_scoring.py#L134), [literal comparison](https://github.com/egggggman/tmt/blob/d880c36ecdb5a8ac3de3edfc92d5caa525ac05d2/scripts/run_v3_path_a_scoring.py#L322).

## V3-P2-004: captured after the actionable Sneak window

All 24 recorded observations have `step: combat_damage`, `options: []`, and `expected_actions: []`; both Pilots raise StopIteration. Canonical examples are raw calls 265/266.

The fixture declares no attackers, executes the empty block action, then queries Sneak options. `execute_block_action` advances to COMBAT_DAMAGE when no Sneak CAST exists. `legal_sneak_actions` returns an empty tuple outside DECLARE_BLOCKERS; inside an eligible window it appends PASS. The serialized step and zero options are therefore consistent with the engine timing guard, not evidence that the engine omitted a required pass in a valid Sneak window. The fixture nonetheless labels this state `no_unblocked_attacker_pass_only`.

AcceptancePilot eagerly evaluates its nested `next(PASS)` fallback; PassingPilot directly searches for PASS. Both fail because the tuple contains no pass or any other action. No supplied legal action could be returned. The normal stage runner enters choose_sneak only while the step is declare_blockers; the scoring replay intentionally invoked the sealed scheduled hook without that gameplay timing guard.

Layer-specific conclusion for HQ: primary fixture/seal timing defect, with replay/input-contract implications. Empty-input defensive handling could change exception presentation, but cannot turn these inputs into a successful pass-only boundary. Do not add a synthetic pass or blame a tactical choice. Exception capture and comparison are functioning as recorded.

Evidence at d880c36: [fixture](https://github.com/egggggman/tmt/blob/d880c36ecdb5a8ac3de3edfc92d5caa525ac05d2/scripts/build_v3_phase2_candidate.py#L150), [Sneak legality guard](https://github.com/egggggman/tmt/blob/d880c36ecdb5a8ac3de3edfc92d5caa525ac05d2/src/tmnt_design_studio/engine07.py#L6641), [block transition](https://github.com/egggggman/tmt/blob/d880c36ecdb5a8ac3de3edfc92d5caa525ac05d2/src/tmnt_design_studio/engine07.py#L6687), [normal timing guard](https://github.com/egggggman/tmt/blob/d880c36ecdb5a8ac3de3edfc92d5caa525ac05d2/src/tmnt_design_studio/stage002.py#L617), [Pilot fallback](https://github.com/egggggman/tmt/blob/d880c36ecdb5a8ac3de3edfc92d5caa525ac05d2/src/tmnt_design_studio/pilot07.py#L122).

## V3-P1-005: main boundary has eight supplied options

Canonical raw calls 97/98 contain seven PLAY_LAND actions for `object-000121` through `object-000127`, plus PASS. The deciding hand contains seven Mountains and the observation is precombat_main. The fixture builder starts a normal all-land deck game, begins the turn, requests legal main actions, and assigns `empty_or_pass_only` without arranging a pass-only state. The engine correctly offers hand lands while the land-play allowance is available.

Both Pilots return PASS in all 12 calls each. AcceptancePilot receives the explicitly recorded `stage: damage`; with no casts it falls back to PASS. PassingPilot always passes. The evaluator retains supplied options satisfying the sealed boundary predicate, hence records returned-pass matches. It does not remove the seven land actions from the supplied tuple, and it already flags the domain contradiction. A returned action meeting the boundary predicate does not prove the fixture's option domain is an empty/pass-only boundary. Relabeling the domain as damage-stage-only after observing outputs would not repair the frozen evidence.

Layer-specific conclusion for HQ: fixture/seal labeling/setup defect; no demonstrated policy, engine-legality, or action-comparison bug. Any future domain-validity reporting decision must remain separate from the unchanged per-call matches.

Evidence at d880c36: [boundary builder](https://github.com/egggggman/tmt/blob/d880c36ecdb5a8ac3de3edfc92d5caa525ac05d2/scripts/build_v3_phase1_fitness_packet.py#L228), [legal land options](https://github.com/egggggman/tmt/blob/d880c36ecdb5a8ac3de3edfc92d5caa525ac05d2/src/tmnt_design_studio/engine07.py#L6107), [boundary comparison](https://github.com/egggggman/tmt/blob/d880c36ecdb5a8ac3de3edfc92d5caa525ac05d2/scripts/run_v3_path_a_scoring.py#L106).

## Preservation and verification

Raw JSONL SHA-256: `aed644c665a0415b70207649fad227b92b1d203e2ad2eed4944a2f6d75d704b0`. All Path A plan/raw/result/report artifacts and sidecars were compared with d880c36 and their recorded hashes. All 96 existing call records for these four fixtures were inspected offline; each per-call match agrees with literal recorded expectation membership. Specific assertions verified both inspected Bears, AcceptancePilot's retained order, the sealed singleton, all 24 empty Sneak observations at combat_damage, and seven land plays plus pass. No new game, hook invocation, fixture, oracle, or score was generated.

The original 288-call run remains 264 returns plus 24 exceptions. Privacy 96 remains INCONCLUSIVE/unexecuted; filtering remains INCONCLUSIVE. Decks stay frozen, calibration BLOCKED, and Action #33 / Prototype 0.3 NOT AUTHORIZED. HQ will authorize any subsequent layer-specific fix; this artifact changes no implementation or evidence.
