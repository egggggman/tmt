# Calibration Protocol Specification V1 — review candidate

**REVIEW CANDIDATE; execution BLOCKED; authorized: false.** This document proposes a prospective experiment for HQ approval. It does not implement gameplay, a runner, an evaluator, or Action #33. Decks remain frozen and Prototype 0.3 is not authorized.

The governing [Calibration Readiness Register](CALIBRATION_READINESS_GATE_POST_PR_109.md) was accepted by HQ and merged through PR #110 at `3025000fd9e9a3ff39d46f937f9634facc7d8ab1`. Its source-time review wording is preserved; HQ's subsequent acceptance governs. PR #109's merge `803570a6ebf8e43b143abf43ac2a046455cf7a96` remains an ancestor. Local main and origin/main matched the PR #110 merge with a clean tree before this documentation branch was created.

All numeric design choices below are **proposed normative choices**, selected before any calibration outcomes. HQ may revise them before acceptance. They are not inferred from historical win rates or an empirical power study.

## 1. Question, target population and permitted claims

**Question:** Once the frozen ten-deck gameplay surface is eligible, do the ten deck-policy combinations produce practically acceptable equal-opponent, seat-balanced outcome scores under the specified frozen decision system and randomized engine starts? Which predeclared deck or matchup scores warrant a separately authorized design investigation?

The population is the distribution of starts induced by the release engine's authenticated RNG/initialization process, for exactly the ten ordered deck lists below, the frozen Pilot and complete decision-ownership schedule, and each cross-deck opponent with equal weight. Seat 0 starts; the release review must verify the starting-player and first-turn Draw contract. All games begin fresh with no cross-game Pilot memory. No human-play population, metagame weighting, other deck versions, or arbitrary Magic-card universe is included.

Permitted conclusions are conditional outcome estimates and the review flags defined in section 7. These measure the combined deck, rules implementation and frozen policy system. They do not identify intrinsic deck strength, optimal or human strategy, causal value of an individual card, mana fixes, or which deck edit would help. No automatic total ranking or revision follows. Historical Stage/Smoke and Pilot Fitness records are validation evidence only and contribute zero observations to this experiment.

## 2. Gameplay scope and eligibility

The proposed scope is **full intended printed gameplay of this frozen ten-deck roster**, not a reduced-rules experiment. No alternative reduced scope is authorized or embedded as a fallback. If full eligibility cannot be established, return BLOCKED. A reduced-model proposal would need a separately named protocol, explicit omissions and permitted claims, fresh HQ acceptance, and a new prospective run identity before data collection.

Before release, the register's five families need accepted closure/disposition consistent with this full-gameplay claim: Menace/multiple blockers; Leonardo graveyard casting/finality; Paramecia death/exile/reflexive return; Raphael linked exile/play; Ooze Spill counterspell/Mutagen. A disposition that simply removes a material legal choice is not full-gameplay closure.

The four deferred risks—Tunnel Rats recurrence, Frog Butler mana, Frog Butler defensive Reach, and Michelangelo +1/+1 replacement—need individual, evidence-backed applicability and scope decisions. Deferral is not harmlessness. A required applicable omission blocks release. Zoo Escapees/Vigilante terminal-only records remain terminal-only and do not justify forced post-game resolution.

Pilot Fitness remains an accepted **bounded demonstrated-surface PASS**. Privacy and filtering remain INCONCLUSIVE. Release must explicitly establish the permitted observation boundary, every optional/mandatory chooser, engine-default choice and Priority/combat scheduling responsibility, and HQ's suitability decision for this protocol's resulting domain. Missing filtering or privacy evidence cannot be declared satisfied by the bounded PASS. This is an unresolved release prerequisite, not authorization for new Pilot work or a reopening of the accepted result. Newly eligible semantics must not acquire unreviewed decisions through implicit defaults.

## 3. Exact inputs: reference freeze versus future execution freeze

The accompanying JSON binds **exact reference inputs at `3025000fd9e9a3ff39d46f937f9634facc7d8ab1`** by committed Git blob ID and SHA-256. Its hashing method is `git show <commit>:<path>` bytes, not platform-dependent checkout text. It includes the catalog/manifest, roster, ten deck files, all runtime Python source, dependency/configuration files, historical runner reference and governing evidence.

| Deck ID, lexicographic order | Ordered list fixed for this candidate |
|---|---|
| april_oneil | `decks/april_oneil/PROTOTYPE_0.1.txt` |
| bebop_rocksteady | `decks/bebop_rocksteady/PROTOTYPE_0.1.txt` |
| casey_jones | `decks/casey_jones/PROTOTYPE_0.1.txt` |
| donatello | `decks/donatello/PROTOTYPE_0.2.txt` |
| krang | `decks/krang/PROTOTYPE_0.2.txt` |
| leonardo | `decks/leonardo/PROTOTYPE_0.1.txt` |
| michelangelo | `decks/michelangelo/PROTOTYPE_0.1.txt` |
| raphael | `decks/raphael/PROTOTYPE_0.1.txt` |
| shredder | `decks/shredder/PROTOTYPE_0.1.txt` |
| splinter | `decks/splinter/PROTOTYPE_0.1.txt` |

Use `cardcade/roster-0.2.json`, the exact `scryfall-tmt-pza-tmc-2026-08-13.json` and its manifest. Independently authenticate catalog membership and ordered deck counts against the frozen files; no fetch of newer Oracle text or normalization of deck order. Proposed Pilot reference is AcceptancePilot in the bound `pilot07.py`; PassingPilot is a fitness control and is not a second calibration treatment.

**The current reference engine is not eligible for execution.** The future `execution_commit`, protocol acceptance identity, complete runner/analyzer/toolchain manifest and seed-manifest digest are deliberately UNSEALED/null in the candidate JSON. They cannot truthfully be fixed to a future implementation now. Their absence blocks release; it is not permission for runtime defaults or “latest main.”

A separately accepted release addendum must bind one clean execution commit, all exact runtime/runner/evaluator inputs, Python patch version, locked dependency hashes, platform, schema, initialization/mulligan/starting rules, complete chooser map and artifact validator. Enumerate every difference from this reference and its HQ acceptance. Deck/catalog inputs must retain the hashes in this candidate unless a separately reviewed protocol revision precedes all outcomes. Engine changes require separately accepted semantic work; a changed decision system requires explicit suitability review for this question. The protocol text and analysis implementation must also be committed and hashed before execution.

## 4. Matchups, randomized seeds, orientation and execution order

Fixed design: all `C(10,2)=45` unordered cross-deck pairs, lexicographically ordered by the table above. Mirror matches are excluded because this question concerns equal weighting of the nine *other* decks, not self-play balance. No matchup is dropped for expected weakness, unsupported exposure, or observed outcome.

Use **2,048 independent whole-roster blocks**, numbered 0–2047. Within each block, include all 45 pairs. For each `(block, pair)` draw one independent uniform 256-bit integer seed using the release environment's recorded operating-system entropy API, before any gameplay. Sampling is with replacement: do not reject a duplicate value or search for interesting seeds. Record exact entropy tooling, draw order, seed bytes and integer conversion (32 bytes, unsigned big-endian). No seed is drawn in this documentation phase.

Freeze the complete 92,160-row seed table and its digest before game #1. HQ readiness review must inspect the seed-generation procedure and immutable manifest; no choice among multiple generated candidate tables is allowed. If generation fails, preserve the partial attempt and stop for disposition. Historical seeds/outcomes are not used to select or tune the table. The seed table is not private information supplied to a Pilot.

For each pair `(A,B)` and seed, execute both orientations from fresh state: canonical A in seat 0/B in seat 1, and reversed B in seat 0/A in seat 1. Reuse the pair seed across orientations to form a paired observation; do not assume this produces the same card order or RNG consumption. Each orientation is executed twice from identical frozen initial conditions. The second execution authenticates exact replay and is not another observation.

Fixed order is block, pair, canonical then reversed, duplicate first then second. IDs are `CP1:bBBBB:pPP:oC|R:r1|2`, using four-digit block and two-digit pair indices; the release manifest expands them literally. Duplicate identity must not affect gameplay or RNG. This yields:

- 2,048 blocks × 45 seed-paired matchups = **92,160 paired observations**;
- × 2 orientations = **184,320 distinct games**;
- × 2 exact replays = **368,640 engine executions**.

This is a proposed workload, not permission to run it. Release requires an approved runtime/storage estimate and capacity for complete evidence. If resources are inadequate, revise and reaccept the protocol before outcomes; do not shorten the run or thin evidence midstream. No pilot-derived adaptive seed allocation or interim sample-size adjustment is permitted.

## 5. Analysis unit, estimands and endpoints

For a valid terminal game, a deck's score is 1 for a win, 0 for a loss, and 1/2 only for an authoritative rules-defined draw supported and accepted in the release engine. Both players' scores sum to 1. A timeout, missing winner, unsupported state or exception is **not a draw**. If the release engine admits no rules-defined draws, the release addendum must certify that scope and score only wins/losses; it may not discard encountered draws to enforce that assertion.

Let `X[d,j,b]` be deck d's mean score over the two seat orientations against j in block b, after duplicate equality is authenticated. It lies in [0,1], and `X[j,d,b]=1-X[d,j,b]`.

**Primary endpoints (10):** `D[d,b]=(1/9) sum(j != d) X[d,j,b]`; estimate `mu[d]` by the mean of D across the 2,048 blocks. Every opponent receives equal weight, independent of game duration or outcome. The roster mean of these ten estimates must be exactly 1/2, a reconstruction check rather than evidence of balance.

**Secondary endpoints (46):** the 45 matchup means of X for the lexicographically first deck, and one pooled starting-seat mean. For the latter, define `S[b]` as the mean seat-0 score over all 90 games in block b. Its interpretation is the starting-seat effect within the frozen rules and deck/Pilot mix, not a universal first-player advantage. Report per-deck seat splits and game-length/draw counts descriptively only; no extra inferential decisions or card/activation rankings.

**Independent analysis unit: the whole-roster block.** Dependence between orientations, between the two players, among matchups in a block, and among the 56 endpoints is allowed. Never analyze 368,640 executions as independent trials. The proposed inference assumes independent seed vectors across blocks, fresh engine/Pilot state, and a fixed deterministic response to each seed. Audit those conditions. Independence is a design/PRNG-model assumption, not proved by differing seed values or passing determinism tests. If it cannot be supported, withhold inferential claims and return a protocol-readiness failure; do not switch estimators post hoc.

## 6. Uncertainty and sample-size rationale

Use simultaneous, distribution-free bounded-mean intervals across the **56 prespecified endpoints**, family-wise error at most 0.05 under the block-independence assumptions. For every endpoint mean m, publish `[max(0,m-epsilon), min(1,m+epsilon)]`, with

`epsilon = sqrt(log(2*56/0.05)/(2*2048))`.

This applies Hoeffding's two-sided bound to each [0,1] block statistic and a union bound across endpoints; it requires no independence between endpoints. See [Hoeffding (1963), Probability Inequalities for Sums of Bounded Random Variables](https://www.cs.rpi.edu/academics/courses/spring06/random/hoefding.pdf). The theorem does not validate the RNG, semantic coverage, policy suitability or sampling population; those are separate release obligations.

The half-width is approximately **4.34 percentage points**. N=2,048 was selected prospectively to keep this conservative simultaneous bound below 4.5 points. This is a precision rationale, not an empirical power guarantee. Differences close to a threshold may remain inconclusive; absence of a flag is not proof of equivalence. No normal approximation, bootstrap tuning, pooled-game binomial interval, sequential stopping, or extra sample collection is substituted after seeing outcomes. Compute decisions using the unrounded means and bound, not displayed percentages.

## 7. Practical thresholds and decision rules

These candidate thresholds are HQ-reviewable design tolerances, not existing empirical facts or general standards of good game balance.

| Endpoint | Proposed acceptable band | Out-of-band review flag |
|---|---|---|
| Each of 10 primary equal-opponent deck scores | [0.40, 0.60] | Lower interval endpoint >0.60, or upper endpoint <0.40 |
| Each of 45 secondary cross-deck matchup scores | [0.25, 0.75] | Lower endpoint >0.75, or upper endpoint <0.25 |
| Pooled starting-seat score | [0.45, 0.55] | Lower endpoint >0.55, or upper endpoint <0.45 |

For each endpoint: **WITHIN BAND** only if the entire simultaneous interval lies inside the closed acceptable band; **REVIEW FLAG** only under the strict outside conditions above; otherwise **INCONCLUSIVE**. An interval crossing a boundary is never rounded into either acceptance or a flag.

Report primary deck disposition separately from secondary matchup/seat disposition. A claim that all proposed criteria are met requires all 56 intervals WITHIN BAND. A secondary flag does not change a primary estimate; it identifies a separately named interaction or starting-rule investigation. No omnibus roster average can cancel a deck flag. Even if all criteria are met, permitted wording remains conditional on this engine/Pilot domain. Flags authorize no deck edits; HQ must separately approve investigation or revision. No calibration conclusion can itself select Action #33 or launch Prototype 0.3.

## 8. Stops, incomplete games and deviations

The proposed hard cap is **120 turns**. A valid terminal state must occur before entering turn 120; any attempt to begin turn 120 without such a terminal state stops the entire experiment. The release runner must enforce this exact boundary and test the off-by-one behavior. The cap is a prospective operational limit, not an outcome endpoint or a draw rule. It is not inherited as evidence that this larger experiment will finish.

Stop immediately on the first material failure: input/commit/seed drift; unknown or unsupported reached semantics; illegal choice, stale identity or epoch; unauthorized information/mutation; missing decision owner; runner exception; incomplete game; invariant violation; duplicate/RNG/evidence mismatch; unclassified occurrence; incorrect terminal handling; missing or corrupt evidence; storage failure; or an unapproved protocol deviation. Already authenticated terminal-pending obligations remain terminal-only and do not require post-game actions. Historical broad unsupported labels cannot substitute for correct applicability checks in the release baseline.

Persist the exact failed game/member ID, frozen manifest, completed counts, error and available authoritative state/events before halting. Run no later game. Do not skip, replace, selectively rerun, continue with survivors, or publish a partial balance conclusion. Preserve partial records as failure evidence only. An interrupted experiment is not an accepted statistical sample, even if the interruption appears outcome-independent. Restart requires HQ disposition, a new run identity and separately sealed baseline/seed table; no mixing runs or pretending inspected failure outcomes are unseen. Any design amendment after data exposure must disclose that exposure and receive a prospective new-protocol decision.

No interim balance dashboard, significance peeking or “stop when clear” rule. Operational monitoring may check execution count, capacity and failures only. Raw outcomes needed for integrity are retained but aggregate decision analysis waits until complete raw evidence is sealed and independently accepted. If execution fails, no confidence or band conclusion is issued from its partial data.

## 9. Reproducibility, storage and independent audit

Plan mode must instantiate no Game, invoke no Pilot, and consume no gameplay RNG. It authenticates all frozen inputs and serializes the complete matchup/seed/orientation/replay manifest, exact counts, versions, rule and chooser maps, stop rules, IDs, output locations, and canonical digest. Separate seed-manifest preparation is recorded explicitly; it cannot masquerade as gameplay-free deterministic reconstruction of an unrecorded random seed list.

Preserve both executions' full canonical snapshots and independent hashes, initial/terminal RNG evidence, game/turn/seat identity, complete supplied observations/options and decisions, ownership/Priority epoch, authoritative events, zones/incarnations, Stack/trigger/transaction joins, terminal reason and score derivation. Hidden engine evidence is audit-only, never Pilot input. Authenticate privacy entitlements and relevant original-event anchors. Keep every failed attempt and source-time identity. Atomic raw writes, sidecars and capacity checks are prerequisites; large raw artifacts live in a predeclared immutable evidence store with repository manifests, not truncated summaries.

Only after all 368,640 executions finish and every duplicate/evidence check succeeds may the raw experiment be sealed as COMPLETE_PENDING_AUDIT. An independent results audit reconstructs all memberships, scores, 56 block vectors, endpoint means, intervals and dispositions from raw evidence, verifies failures are zero and no observations were omitted, and checks the exact committed analyzer. It must not trust producer labels or precomputed scores. Readiness acceptance of this specification does not substitute for the future results audit.

Historical balance-invalid flags remain untouched. New calibration eligibility belongs to the separately released experiment and independently accepted complete data; no historical artifact is promoted by copying or editing a flag.

## 10. Execution release gate and unresolved freeze fields

Execution stays blocked until HQ accepts all of the following:

1. This protocol, including its question, workload, thresholds, precision assumptions and all claimed boundaries.
2. Closure/disposition of the five semantic families and four deferred risks for the stated full-gameplay roster scope, with validated applicability/terminal classification.
3. The domain-specific decision-ownership/information contract and an explicit disposition of Pilot privacy/filtering exclusions and new semantic choices. The bounded PASS alone does not clear them.
4. A complete immutable release addendum: exact execution commit, source/toolchain/runner/analyzer identities, rule and chooser contracts, seed table and digests, storage/runtime capacity and every reference-freeze delta. No null or mutable identities remain.
5. Independent readiness evidence for legal timing/options, determinism, complete source/event lineage, failure/stop enforcement, hashing/storage, analysis reconstruction and repository tests/checks. Tooling implementation or test execution requires its own authorization; none is commissioned here.
6. Separate written HQ execution authorization naming the frozen release and permitted run. Protocol acceptance or merge does not imply it.

The accepted register remains governing until superseded by accepted evidence. This protocol candidate does not declare any semantic family closed, choose Action #33, revise decks, tune the Pilot, or permit Prototype 0.3.

## 11. Preparation record

This candidate is documentation/design only. No seeds were drawn, no games or scoring calls ran, no engine/Pilot/test files changed, and no gameplay tests were executed. The packet includes a machine-readable design/reference manifest and SHA-256 sidecars. Static validation checks matchup/count arithmetic, endpoint/bound arithmetic, source identities, ancestry, links and changed-path scope. These checks validate the specification's internal arithmetic and provenance, not engine eligibility or an implemented calibration harness.
