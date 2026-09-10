# Pilot Fitness Assessment Specification

Status: PROPOSED FOR HQ REVIEW. Specification only; no fitness result or experiment authorization.

Frozen engine reference: `de52f57a24a5c29a258573ad673051a0aa5c7e5c`.
Gate-audit and document base: `e28cd6dcd5532b84d38c45d3a710077e5cb589b4`.
Assessment target: the frozen `AcceptancePilot`, with frozen `PassingPilot` as a diagnostic control. Neither is presumed fit. This specification creates no Action #33.

## 1. Question and permitted claim

Pilot fitness means selecting legal, reproducible, information-appropriate actions that meet predeclared tactical and resource-management standards across the decisions the assessed Pilot actually owns. It is a property of a named Pilot version, input interface, runner, rule domain and assessment suite. It is not equivalent to engine correctness, finishing games, winning against a weak opponent, or balancing the ten decks.

The first proposed experiment asks: within the frozen engine's represented decision surface, does AcceptancePilot meet the bounded decision-quality criteria below, and which failures belong to the Pilot, its inputs, the runner or missing rules? A pass supports only represented-domain diagnostic fitness on the sealed suite. It does not establish unrestricted gameplay competence, long-horizon strategic optimality, or calibration readiness.

The accepted Smoke remains 180 games / 360 duplicate executions: 114 coverage-complete, 66 coverage-limited, zero invalid; 495 EXECUTED / 111 REACHED-UNSUPPORTED / 1,530 PRESENT-UNREACHED; zero stops, invariant violations and duplicate mismatches. Every balance record remains invalid for calibration. These are inherited observations from the gate audit, not a new measurement or fitness score. The 114 games are not a prospective calibration population; selecting them after seeing coverage would change the question.

## 2. Responsibility and legal-decision inventory

Legality, payment, timing, authoritative identities, random outcomes and state mutation remain engine-owned. The Pilot selects a supplied option; the runner determines when it is asked. Quality assessment must never manufacture a supposedly legal option to make a desirable move available.

| Pilot hook / assessment stratum | Competence to assess within represented rules | Explicit limit |
| --- | --- | --- |
| `choose_main_action` | Land choice; payable cast/activation selection; target and cost-object choice when present in options; preserve resources or pass when appropriate. Cover each existing stage: land, activate, damage, destroy, creature. | Runner offers one action in each ordered stage, not arbitrary sequencing or a full postcombat main loop. Main/activation legality is bounded. Report stage restrictions separately from policy mistakes. |
| `choose_attack` | Recognize immediate lethal and avoid demonstrably losing attacks; choose useful subsets rather than maximize attacker count automatically. | Only supported combat scenarios; no Menace/multiple-blocker approximation. Opponent responses used by the oracle must be represented and visible-information justified. |
| `choose_blocks` | Prevent avoidable lethal, allocate represented blocks and preserve useful material when survival is equivalent. | Current block representation does not certify multiple-blocker competence. |
| `choose_sneak` | Compare legal Sneak cast, return/cost choices and pass, including immediate combat consequences. | Only engine-generated timing and options; no inferred missing response windows. |
| `choose_scry` | Use privately inspected cards to select top/bottom and order for a predeclared near-term need. | No knowledge of uninspected library order; usefulness must be defined from authorized information. |
| `choose_hand_bottom_draw` | Compare optional filtering with retention; select an appropriate hand identity when filtering is justified. | Do not assume filtering is always good or use the unseen next Draw as an oracle advantage. |
| `choose_discard_draw` | Compare optional discard/Draw with retention and distinguish card value from tuple order. | Draw-first mandatory discard uses a separate engine chooser and is not automatically covered by this hook. |
| `choose_priority` | Pass or take a represented response when its observable tactical consequence warrants it; respect Priority owner and epoch. | Existing nonempty-Stack Priority is bounded. No full unrestricted instant/graveyard-activation timing claim. |

Source anchors: `src/tmnt_design_studio/pilot07.py` (Pilot protocol, AcceptancePilot, PassingPilot); `engine07.py` (ActionOption, GameView, public_view, legal_main_actions, legal_activated_ability_actions, legal_priority_actions); `stage002.py` (run loop and _drain_priority), all at the frozen engine reference. Pilot source blob: `3eb8bfd8654294e1ef7e6137882651801bf1e2d6`.

The runner wires only Scry, hand-bottom/Draw and optional discard/Draw to these choice hooks. Courier selection, Jury-Rig selection, mandatory Draw/discard, legend selection and several target/mode/keyword choices use separate engine defaults. Record the exact owner of every assessed choice. These defaults may constrain eventual system fitness, but their choices cannot be credited to AcceptancePilot. Automatic Krang refill, mill movement, deterministic random-bottom order and delayed discard are engine transactions, not Pilot decisions. Casting the relevant card can be a Pilot decision where legally offered.

AcceptancePilot currently chooses first available actions for several stages, cheapest creatures, maximum attacker/block counts, first Sneak cast, keep-all Scry, first optional filter card and unconditional Priority pass. It has named-card branches for Manhole Missile and Make Your Move. These source observations motivate tests; they are not measured failure rates. PassingPilot is a legality/control baseline, not a competent adversary; passing is sometimes correct.

## 3. Information and applicability gate

At the frozen reference, GameView/public_view exposes identities and names for both players' hands without recipient filtering. Its PublicObjectView supplies identity, name, controller, power/toughness, tapped, damage and token status, but not every relevant public rule/state field. Immutable views alone do not establish a valid hidden-information interface.

Before scoring each future fixture, record what the deciding player may know, what the actual hook receives, and whether omitted public information is necessary to judge the action. No privileged card identity or hidden next Draw may determine an ostensibly forced correct choice. Oracle criteria must be measurable from permissible information, or use an explicitly predeclared belief model; the initial suite will use the former only. If unavailable public facts are needed, mark INTERFACE-LIMITED rather than blaming the Pilot. No silent adapter, redaction, new chooser wiring or runner extension is part of this frozen assessment.

For each applicable GameView fixture, the future packet must include a paired input with only opponent-private hand identities/names changed consistently, preserving public information, hand size and the deciding player's legal options. Compare mapped choices. A difference indicates hidden-information dependence requiring investigation; equality on tested pairs does not prove universal non-use or repair the interface. Specialized private-choice views require a documented visibility check instead of an irrelevant opponent-hand variant. Exposed opponent hands remain an unresolved system-level calibration risk even if this Pilot appears not to use them.

Separate four outcomes: policy error with sufficient inputs; interface limitation; runner opportunity limitation; semantic limitation. Missing opportunities are not Pilot successes. An illegal engine-generated option is an engine defect, not a sound ground for ranking Pilot tactics. Freeze attribution before aggregate reporting; retain disputed cases as inconclusive pending HQ review.

## 4. Proposed experiment design, not executed here

After HQ accepts this specification and separately authorizes an experiment, prepare and commit a scenario manifest and oracle packet before collecting scored Pilot outputs. Use 12 base decision fixtures per hook, 96 total, with two identity-preserving seat versions and two identical replays per version for each of the two frozen Pilots: 384 canonical invocations per Pilot, 768 total. These are decision invocations, not games or independent statistical trials. No new Smoke or Stage batch is proposed here.

Each stratum contains four forced tactical obligations, four resource/optional-choice comparisons and four boundary/pass cases. A forced obligation has a uniquely acceptable action or a set of outcome-equivalent actions established independently of Pilot output. Each stratum must contain at least two cases where pass/decline/retention (or the nearest valid conservative choice) is correct and at least two where taking action is required. Main-action fixtures must cover all five stages at least twice. Do not construct a false obligation merely to fill a quota: inability to supply a valid represented case is a suite-readiness limitation requiring HQ revision before scoring.

Use legal reachable-state setup through accepted engine primitives in the later authorized harness; record setup and its reconstruction. Fixtures may be controlled decision positions, but cannot revise the ten decks or be presented as natural ten-deck exposure. Seal the represented rule dependencies, source identities, input view, generated options, stage, acceptable option set, tactical horizon, outcome comparison, and all random seeds for every fixture. Name each horizon concretely (for example through current combat damage or resolution of the current Stack); do not expand it after seeing a choice. Include cases of beneficial action, beneficial restraint, competing legal targets and equivalent alternatives. Do not run generic strategic search to invent an oracle.

The oracle uses a set-valued tactical rubric: first avoid a provably avoidable loss or take a guaranteed win within the declared horizon; then meet the fixture's explicit resource objective where survival is equal. Resource objectives must state quantities and tradeoffs in advance (for example retain a specified usable blocker while preventing lethal); there is no universal life-to-card conversion. If a hidden future outcome or unresolved tradeoff is necessary, the position cannot be one of the 96 scored fixtures. All alternative continuations required to justify a dominance claim must fit the represented rules and be saved. Expected long-horizon value and win rate are outside this first suite.

Two additional transformations apply to every canonical seat version: one sealed permutation of legal option order, and one consistent object-identity renaming. Replay each transformed input twice for each Pilot. This adds 1,536 invocations, making 2,304 across both Pilots before privacy pairs. A transformed input must remain equivalent and preserve legal relationships; invalid transformations invalidate that check, not the Pilot. Exact choice equality is required for duplicates, while transformations require equivalent acceptable outcomes; choosing a different tied option is allowed. The future manifest lists privacy-eligible seat versions (K), each with two replays per Pilot, adding 4K invocations. K and the resulting exact total must be committed before scoring; no discretionary variants after results.

All 96 canonical fixtures are required. Do not drop failures, replace fixtures after inspection, pool an unassessable hook into another, or turn unsupported cases into passes. If the frozen interface cannot support a required stratum, return INCONCLUSIVE for the overall target and report valid stratum results separately. Any revised suite receives a new version and HQ approval; retain the original evidence. Future implementation of the harness/fixtures is subject to experiment authorization and must not modify the frozen engine or Pilot under this specification.

## 5. Reproducibility and evidence contract

The future packet must preserve:

- Exact engine, Pilot, runner, evaluator and fixture commits/blobs; this spec's SHA-256; gate-audit SHA; Python/dependency versions and clean-worktree status. Separately identify new assessment harness files so they cannot masquerade as the frozen engine.
- Hashes of frozen card definitions, decks and any reused evidence; full scenario manifest, oracle/rubric version, deterministic seed mapping, seat/variant/replay IDs and option-order mapping. No unrecorded clock, global RNG, network or process-order dependency.
- Per invocation: deciding player, authorized information boundary, canonical input and complete supplied option set, selected option including identities/targets/costs/Priority epoch, pre/post state and input hashes, RNG state digest, decision owner and criterion verdict. Pure choice must not mutate engine state, input or consume engine RNG. Any later engine execution is recorded separately.
- Where consequences justify scoring: ordinary authoritative execution and complete relevant Trigger/Stack/Priority, movement, Draw and terminal evidence. A generic action-success event is not enough to prove the claimed consequence. Reconstruct from saved evidence without trusting precomputed verdicts.
- Duplicate equality, transformed-outcome comparisons, per-hook denominators, all failures/limitations, and machine-readable links from scores to their oracle and decision records. Stale/foreign selected identities or relinked evidence must fail authentication; fabricated records cannot count as assessed choices.
- SHA-256 sidecars for every preserved result and specification, including compressed and decompressed hashes where applicable. Preserve failed attempts and reasons; corrections require a new identified packet rather than overwriting historical evidence.

Predeclare execution order; separate fixtures so choices cannot inherit accidental mutable state. Seeds are paired across compared Pilots where engine continuation uses RNG. Random outcomes are not chosen by the Pilot. Replays and seats test robustness; they do not multiply independent sample size. Report exact counts for this designed suite, not population confidence intervals or an inferred ten-deck win-rate advantage. Runtime may be recorded descriptively; no hardware-dependent timeout becomes a tactical error without a predeclared budget.

## 6. Metrics and minimum acceptance criteria

These are proposed normative thresholds for HQ approval, not empirical findings or guarantees of general fitness. Evaluate each Pilot separately. AcceptancePilot must meet every applicable row; high performance in one hook cannot mask failure in another.

| Measure | Required minimum / failure rule |
| --- | --- |
| Legality and ownership | 100% returned options belong to the supplied legal set with authentic current identities, player and epoch; zero unauthorized mutation or engine-RNG consumption. Any violation fails integrity. |
| Determinism / evidence | 100% duplicate choice and consequence equality for identical inputs/seeds; all scored records and hashes reconstruct; zero unexplained mismatches or missing records. An invalid packet is not a fitness pass. |
| Forced tactical competence | 4/4 canonical forced fixtures per hook in both seats; zero avoidable forced losses or missed guaranteed wins under the sealed oracle. Any such error fails that hook. |
| Overall acceptable decisions | At least 11/12 canonical fixtures per hook, with each fixture passing both seats. Report 96-fixture total as secondary; no pooled substitute for per-hook minima. |
| Resource and optional-choice quality | Report resource-objective success, unnecessary expenditure, beneficial restraint, missed useful action and target selection separately, using their predeclared eligible denominators. Any strict dominance violation under the sealed oracle fails the hook, even if 11/12 is reached. |
| Robustness | Every transformed version preserves legality and an outcome equivalent to an acceptable canonical choice on cases scored acceptable; a failed canonical choice cannot be repaired by averaging variants. Report order and identity sensitivity on all cases, including failures. |
| Information appropriateness | Zero unexplained dependence on forbidden private information in eligible pairs; all view limitations disclosed. A privacy violation fails suitability. Passing finite pairs does not clear the exposed-hands architecture for calibration. |
| Suite sensitivity | Predeclare at least four forced fixtures in at least two hooks where PassingPilot's documented passive policy should fail. Confirm those failures and its legality; unexpected outcomes require oracle/harness review. No requirement that AcceptancePilot beat PassingPilot on cases where passing is correct. |
| Completeness | All eight hooks, all fixture quotas, both seats and required variants present. Missing or semantically unassessable cells yield overall INCONCLUSIVE, never a smaller post hoc passing denominator. |

Maintain distinct outcome fields: packet VALID/INVALID; each hook PASS/FAIL/INCONCLUSIVE; represented-domain target PASS only if every hook passes; unrestricted calibration suitability BLOCKED. Classify a verified Pilot error as FAIL, an unavailable semantic/input opportunity as INCONCLUSIVE, and evidence corruption as INVALID. Report multiple problems rather than letting one label erase another. A bounded suite pass still needs broader prospective validation before strategic fitness claims.

## 7. Semantic dependency and risk register

Exposure is inherited raw distinct games / occurrences from the accepted Smoke, not fitness opportunities or measured causal effects. Rows overlap. A changed Pilot may reach previously unobserved semantics; present-unreached is not clearance.

| Dependency / exposure | Assessment treatment and calibration consequence |
| --- | --- |
| Menace / multiple blockers, 24 / 24 | Exclude dependent tactical oracles from represented-domain scoring and list the unavailable combat competence. Must resolve before unrestricted calibration; no one-blocker substitute. |
| Leonardo graveyard casting/finality, 13 / 15 | Recursion/payment/replacement lifecycle unavailable; do not penalize Pilot for absent options. Must resolve before unrestricted calibration. |
| Paramecia death/exile/reflexive return, 12 / 13 | ETB mill support does not cover the compound death choice. Must resolve before unrestricted calibration. |
| Raphael linked exile and attack-time play, each 6 / 6 | One coupled resource-access program; no independent credit for an entry/attack witness. Must resolve before unrestricted calibration. |
| Ooze Spill counterspell/Mutagen, 2 / 3 | Bounded activated responses do not certify this instant/token sequence. Must resolve before unrestricted calibration. |
| Tunnel Rats, 16 / 19 | All 47 old witnesses were battlefield-source contexts, not legal graveyard activations. Deferred to future timing/Priority work; assess applicability before claiming recursion fitness or protocol clearance. |
| Frog Butler mana, 8 / 8 | Fifteen witnesses borrowed Reach cost contexts. No established mana-choice exposure; retain potentially material payment/color-access risk. Defer implementation pending applicability/protocol decision, not as harmless. |
| Frog Butler Reach, 8 / 8 | Main-phase fixed-cost contexts do not establish needed defensive timing. Defer pending protocol applicability; no unrestricted defensive competence claim. |
| Michelangelo counter replacement, 1 / 1 | Sole witness concerned stun, not +1/+1. Do not convert it into a Pilot test demand. Actual replacement dependency remains subject to protocol applicability. |
| Zoo Escapees, 5 / 5; Vigilante, 3 / 3 | Saved terminal obligations only. Preserve conservative credit and actual terminal endpoints; do not extend games to make a score. A genuinely missed due obligation would be a different defect. |
| Opponent-hand exposure / missing public fields | Separate information-interface risk; finite non-use tests cannot establish general secrecy. HQ must settle the intended information model before calibration. |
| Engine-default choices and stage/response scheduling | Report unowned or unoffered decisions explicitly. Full Pilot-system competence cannot be inferred from eight hooks alone; new wiring or timing work requires separate authorization. |
| Narrow deterministic policy and fixed fixture suite | Potential card-name, option-order and scenario overfitting. Preserve controls/variants; a later held-out prospective assessment needs separate approval before broader claims. |

No residual is waived by high decision accuracy. If a requested fixture requires generic variable scripting, broader Priority, hidden-zone architecture, deck changes or other engine expansion, stop that design path and return the dependency to HQ. Do not implement a workaround in the evaluator and call it frozen-engine competence.

## 8. HQ decision path

1. Review and accept or revise this specification. This document alone authorizes no harness implementation, Pilot change or experiment run.
2. Separately authorize the bounded experiment and its preparation scope. Seal fixtures, oracles, applicability and exact execution manifest before scoring; return unresolved suite feasibility to HQ rather than changing the question.
3. Review results with attribution. Pilot failures can justify a separately authorized policy-improvement packet; interface/runner/semantic failures require their own scope decision. No automatic Action #33 follows any score.
4. A represented-domain pass permits HQ to consider further Pilot validation and use the findings in Calibration Protocol preparation. It does not unlock calibration. Unrestricted ten-deck calibration still requires closure of the five must-resolve semantic families, explicit dispositions of deferred applicability risks, an accepted information/decision-ownership model, demonstrated fitness for that resulting domain and a separately accepted prospective Calibration Protocol. An explicitly reduced-model experiment would require a different named claim and HQ authorization.

The separate Calibration Protocol may be drafted in parallel under the existing preparation gate; it is not delivered or executed here. Actual calibration remains BLOCKED. Prototype 0.3 and Action #33 remain NOT AUTHORIZED.

## 9. Preservation and sources

Only this specification and its SHA-256 sidecar are added. No production, Pilot, test, runner, deck or historical evidence changes; no simulations or fitness experiments. Documentation integrity checks do not constitute a new gameplay run.

Primary local sources, resolved at the references above: [accepted gate audit](POST_ACTION_32_ENGINE_VALIDATION_GATE_AUDIT.md), [final validation](POST_ACTION_32_FINAL_VALIDATION.json), [candidate handoff](POST_ACTION_32_CANDIDATE_HANDOFF.md), [Smoke inventory](POST_ACTION_32_SMOKE_INVENTORY.json), and the source interfaces named in section 2. Exposure and prior validation are inherited from these banked artifacts. All assessment thresholds, fixture counts and decision rules in this document are prospective proposals for HQ review.
