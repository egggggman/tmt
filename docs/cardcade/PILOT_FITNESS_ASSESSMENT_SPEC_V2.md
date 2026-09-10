# Pilot Fitness Assessment Specification V2

**Status: PROPOSED FOR HQ REVIEW. Specification only.** This document encodes
HQ's accepted Oracle V2 methodology and common own-deck knowledge entitlement.
Its quotas, thresholds and operational definitions require independent HQ
acceptance. It authorizes no fixture construction, evaluator implementation,
Pilot invocation, gameplay simulation or scoring.

## 1. Version, authority and permitted claim

Upon HQ acceptance, this specification replaces V1's experimental methodology,
uniform 4/4/4 quotas, invocation formula and fitness acceptance rules. V1 remains
historical evidence; neither its text nor either failed preparation is edited.
No old result, fixture or denominator transfers automatically into this version.

| Preserved anchor | Exact commit |
| --- | --- |
| Accepted pilot-input-v2; specification candidate base on main | `fa3f4944a7209f22e70d783d9a7f9abca3b37534` |
| Frozen gameplay reference | `de52f57a24a5c29a258573ad673051a0aa5c7e5c` |
| Fitness Specification V1 | `ca9757b956eafc4b8d03c495dabb03eaab6fe931` |
| V1 failed preparation | `84beb1b28bd80fd53ab75da8bb566f4f4d2718a1` |
| V2 failed preparation | `a19c1a06596862ea3cf947700c57149978e7f77e` |
| Accepted Oracle V2 assessment | `02b5ecdb44cb655cb22580837b1e47da288cc219` |

The assessment target remains the frozen AcceptancePilot; the frozen PassingPilot
is a diagnostic control. Two distinct quality claims are assessed:

- **Deterministic competence:** select an acceptable action when the supported
  tactical or resource consequence follows from permitted information.
- **Uncertainty-sensitive resource judgment:** select an action with an optimal
  ex-ante resource value under the disclosed own-deck reference model and sealed
  objective, irrespective of the realized hidden Draw.

A pass supports only these bounded claims on the complete sealed suite. It
does not establish optimal play under a true current-library posterior,
general memory competence, unrestricted Magic competence, ten-deck balance or
calibration readiness. No pooled score is a substitute for either claim.

## 2. Frozen execution and decision ownership

The accepted flow remains authoritative state → recipient-specific immutable
V2 observation → unchanged Pilot → unchanged option → existing engine execution.
The engine owns legality, payment, identities, timing, triggers, Stack behavior,
random outcomes and mutation. The evaluator may not manufacture legal options,
alter their meaning, add a timing window or change Pilot policy.

| Hook | Binding and represented scope |
| --- | --- |
| `choose_main_action` | Active player; existing land, activate, damage, destroy and creature stages |
| `choose_attack` | Attacking player; existing supported attack options |
| `choose_blocks` | Defending player; existing supported block representation |
| `choose_sneak` | Active attacking player in an existing legal Sneak decision window |
| `choose_scry` | Supplied decision owner; exactly the currently inspected slice |
| `choose_hand_bottom_draw` | Supplied decision owner at the optional instruction point |
| `choose_discard_draw` | Supplied decision owner for optional discard/Draw; not mandatory draw-first discard |
| `choose_priority` | Exact Priority owner and epoch, including nonactive Priority |

Courier, Jury-Rig, mandatory discard, legend and other engine-default choices
remain outside these Pilot strata. Automatic transactions cannot be credited as
Pilot decisions. No chooser is reassigned. The legacy omniscient `public_view()`
is forbidden for Pilot assessment dispatch. The assessment never invokes a
Pilot as an opponent or continuation policy to construct its oracle.

## 3. Legitimate knowledge and the initial reference prior

HQ permits the deciding Pilot to be treated as knowing its **own frozen deck
list and card multiplicities as common domain knowledge**. For each fixture,
the manifest shall bind each seat to one exact frozen deck path, content hash,
card-definition identity map and multiplicity vector `D`. Swapping seats moves
that common knowledge with the player/deck, not with a fixed seat number.

This entitlement supplements the interpretation of the existing V2 payload;
it does not assert that V2 already contains a deck field. The manifest must
state the entitlement and unambiguous seat/deck binding before any later
scoring authorization. No per-decision hidden facts, posterior service, policy
wrapper, memory callback or interface mutation may be smuggled in as common
knowledge. The frozen policies remain unchanged even if they do not exploit
all of their authorized domain knowledge.

### 3.1 Exact meaning of “composition prior” in this initial experiment

The initial uncertainty track uses the **disclosed composition reference
prior**, with one potential replacement-card outcome per card definition:

```text
N = sum_c D[c] = 60
P_ref(c | own_deck) = D[c] / N
```

Each physical copy contributes weight. Names are not weighted equally. This is
a prospective benchmark model of replacement-card quality, **not** a claim
that the actual remaining library has these frequencies. It is deliberately
not “deck minus everything seen so far.” The oracle shall label its values
`reference_prior_expected_value`, not `actual_draw_probability` or
`current_library_posterior`.

No subtraction from `D`, hidden-library recount, return-history reconstruction,
opponent inference, mulligan inference or conditioning on a setup seed is
permitted in this initial model. Current V2 information still controls legality,
the resource predicate, safety and applicability; it is not ignored to rescue
a convenient prior. A later posterior-based claim needs a new specification
and separate authorization for any required knowledge machinery.

**Consistency gate:** the prior must not contradict a deterministic fact
available at the decision. Every positive-weight replacement definition must
have a legal hypothetical completion consistent with that observation, the
declared deck, the complete predecision options and the supported setup. The
future packet must certify this without designating the actual hidden world.
If a card is demonstrably exhausted, a top card is currently known, the library
is empty, or another visible fact forces a different next-card law, the fixture
does not enter the reference-prior uncertainty track. Do not drop impossible
outcomes and renormalize the prior. Use a valid deterministic category where
appropriate, or return an applicability limitation.

Support consistency alone does not make the reference prior a true posterior.
That limitation is part of the bounded claim, even when a fixture is eligible.
Approval of this specification must include this explicit interpretation;
there is no silent substitution between a reference prior and a history-based
belief model during preparation.

### 3.2 Information parity and forbidden evidence

The quality oracle is a function only of the permitted V2 observation `I`,
engine-supplied options `A(I)`, the bound common deck prior and the sealed model.
The evaluator may compute more extensively than the Pilot, but may not rank
actions using a stronger information set.

Actual hidden library order/composition, RNG seeds/state, registry lookups,
omniscient event streams, unprovided past inspections and realized outcomes
are forbidden inputs to action ranking, tie-breaking and prior selection.
Opponent hand identities remain forbidden. Catalog access describes a named
hypothetical card; it is not evidence that the actual library contains it.

A separate integrity auditor may authenticate the actual setup and execution.
It must not export hidden facts to the quality oracle or let actual success
change a decision-quality verdict. Public availability to a human reviewer
alone does not authorize an undisclosed extra Pilot input.

## 4. Tracks, categories and proposed quotas

**72 canonical fixtures** are proposed, with the following disjoint primary
categories. Each fixture occupies exactly one cell; additional coverage labels
do not increase its count. Each canonical fixture has both seat versions.

- **T — deterministic tactical/safety:** guaranteed wins or provably avoidable
  losses within the sealed horizon. All needed facts and responses are
  information-grounded and represented.
- **R — deterministic resource:** a concrete public/authorized resource
  comparison, including inspected-card ordering, with equivalent safety.
- **U — uncertain resource:** one unknown replacement Draw at most, exact
  expectations under section 3, with equivalent safety for all candidate actions.
- **B — boundary/integrity:** empty/pass-only, endpoint or equivalent-option
  cases. These cannot be counted as tactical or useful-action competence.

| Hook | T | R | U | B | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Main action | 4 | 6 | 0 | 2 | 12 |
| Attack | 4 | 4 | 0 | 2 | 10 |
| Blocks | 4 | 4 | 0 | 2 | 10 |
| Sneak | 2 | 4 | 0 | 2 | 8 |
| Scry | 0 | 6 | 0 | 2 | 8 |
| Hand-bottom/Draw | 0 | 0 | 6 | 2 | 8 |
| Discard/Draw | 1 | 0 | 5 | 2 | 8 |
| Priority | 4 | 2 | 0 | 2 | 8 |
| **Total** | **19** | **26** | **11** | **16** | **72** |

The asymmetry is intentional. Filtering receives no forced-gain obligation.
Discard/Draw has one deterministic failed-draw safety obligation; hand-bottom
into an empty library is a boundary case because the selected card returns to
hand. Scry's first suite assesses reasoning over its authorized inspected cards,
not a forced-win quota or a later remembered inspection. The four decision hooks
with combat/timing responsibilities retain deterministic tactical obligations.
Priority's bounded responses retain their own tactical quota.

### 4.1 Required coverage within these counts

- Main action: each of the five existing stages at least twice. Cover at least
  two justified conservative choices, competing targets/cost objects where
  represented, and beneficial action. No arbitrary action-sequencing search.
- Attack, blocks and Sneak: cover beneficial action and conservative subsets,
  target/return or material tradeoffs as applicable, and actual supported timing.
  Do not equate “conservative blocks” with declining a necessary block.
- Scry R: at least two cases with an acceptable inspected-card placement/order
  change and at least two with justified retention; cover competing inspected
  identities and tied acceptable orders. A future uninspected Draw cannot
  determine a deterministic R label. B covers actual inspection boundaries.
- Hand-bottom/Draw U: two strict filter-preferred cases, two strict
  retention-preferred cases, one competing-hand-identity comparison and one
  exact expected-value tie case. The six roles are disjoint. B covers empty-hand
  and empty-library behavior, not required gain.
- Discard/Draw U: two strict discard-preferred cases, two strict
  retention-preferred cases and one competing-hand-identity comparison. T covers
  a valid avoidable failed-draw loss; B covers distinct legal boundary/equivalence
  behavior and cannot duplicate T under another label.
- Priority: include action-required and pass-correct positions, both Stack
  controllers, nonactive Priority, and competing/equivalent response options
  when represented. Unavailable target provenance cannot support an oracle.

These are prospective design obligations, not claims that fixtures have been
built or shown reachable. A different ID, seat, name, life total or option
permutation does not create another canonical tactical situation. Each fixture
must identify its distinct decision comparison. If any required cell or role
cannot be constructed honestly, stop preparation and return to HQ; do not fill
it with a boundary case, weaken its criterion or shrink the denominator.

## 5. Oracle construction rules

### 5.1 Deterministic T and R

T uses a set-valued rubric: prevent a provably avoidable loss or take a
guaranteed win within a concretely named supported horizon. Save every
alternative continuation needed for that claim. R first requires equivalent
safety, then compares an explicit resource predicate or quantity. T cannot
depend on favorable hidden cards, unoffered decisions or unsupported semantics.
Unresolved choices between conflicting guarantees are not silently ranked.

Objectives must state quantities, constraints and tradeoffs before outputs.
There is no universal life/card/mana conversion. A label such as “discard this
card” is not by itself a gameplay resource objective. R may have tied acceptable
outcomes; equivalent options are all included, not selected by tuple order.

### 5.2 Uncertainty U

The initial U horizon includes **at most one unknown replacement Draw**, not
one per action branch followed by additional unmodeled Draws. No Monte Carlo,
random search, learned opponent model or generic strategic search is permitted.
Use exact rational multiplicity weights and enumerate all positive-weight
replacement definitions. At most 60 distinct definitions and 1,000
action/outcome rows are allowed per U fixture; count before sealing. Do not
truncate or sample when the cap is exceeded.

For action `a` and replacement definition `c`, let `u(a,c)` be a sealed binary
resource predicate at the endpoint. For the first U suite `u` is either 0 or 1,
with explicit resource-preservation constraints; arbitrary cardinal utilities
are excluded. The predicate must be justified by visible game context.

```text
Q(a) = sum_c D[c] * u(a,c) / 60
Q_best = max_{b in A(I)} Q(b)
regret(a) = Q_best - Q(a)
acceptable_U = {a in A(I): regret(a) = 0}
```

The regret tolerance is **zero**. Genuine exact ties are acceptable. A strict
preference must have an exact gap of at least `1/60` in this binary, 60-copy
reference model; this is the smallest positive grid step, not an empirical
significance claim. No rounded floating-point comparison may break a tie.
There is no partial credit for an inferior choice that happens to draw well.

Safety is not blended into `Q`. Every U candidate action must have equal
terminal win/loss status within the horizon for every admitted completion.
If safety differs or a resource ranking requires a probability-of-loss tradeoff,
the case is outside initial U scope. Reclassify only before sealing and only if
it independently satisfies another category; otherwise report inconclusive.

The hand-bottom action with a nonempty library draws from its preexisting top;
the selected card is not added to the reference replacement pool. With an empty
library the return is deterministic and belongs in B. A discarded card is not
added to the library pool. A decline branch does not draw. The model does not
overwrite these engine semantics or force an actually realized replacement.

### 5.3 Information-consistent continuation

Fix the assessed action before the unknown Draw. Use only automatic effects or
a small, sealed continuation table based on observations available at each
later decision. Worlds still indistinguishable to a player must have the same
continuation decision. After a card is legitimately drawn/revealed, a later
decision may depend on that observation.

Do not maximize separately in hidden worlds before the information is revealed
and then average those clairvoyant optima. Every hypothetical completion must
share the predecision observation and complete legal-option set. The initial U
suite excludes opponent-private response dependencies and further hidden random
events. No Pilot calls may construct or validate the continuation table.

Name the exact existing instruction/step endpoint and preserve all branches,
including unfavorable ones, needed to establish consequences. Legal setup and
branch reconstruction must use accepted engine primitives in a later authorized
preparation phase. They must not create parallel rules in the evaluator or add
new response opportunities. No such reconstruction is executed by this document.

## 6. Sensitivity, ties and applicability

The own-deck reference prior is fixed once the common deck binding is sealed.
It is not selected by an actual top card, seed, observed policy choice or
preferred result. Ambiguous deck binding is an information-contract failure;
do not average candidate decks or choose one using hidden state.

For each R/U objective, the pre-run packet must list any materially plausible
alternative interpretation of its resource constraints and show whether the
acceptable set is stable. If conflicting objectives or a different defensible
prior are necessary to establish correctness, label the case MODEL-SENSITIVE
and return it to HQ before sealing. No ad hoc life-to-card ratio, retrospective
prior adjustment or discretionary tie-breaking is allowed.

This does not require a fixed-deck reference benchmark to pass under every
other frozen deck prior. Cross-deck checks are separate, explicitly bound cases;
they cannot be used to tune the primary prior. If a proposed claim purports to
hold across a declared family of legitimate priors/objectives, its acceptable
set must meet that criterion throughout the family. Ranking reversals make that
broader claim inconclusive. Exploratory sensitivity analysis confers no Pilot
execution authorization or extra scored fixtures.

An exact tie under the accepted fixed model is not an applicability failure:
retain all tied optima. An unresolved preference or unjustified model is not a
tie: it is inconclusive and cannot fill a quota. Report model-conditional
fitness separately from any broader robustness claim.

## 7. Controls and acceptance criteria

Both frozen Pilots receive the same permitted information, options, common
deck binding, transformations and duplicate schedule. Assess each separately;
no requirement says AcceptancePilot must outperform PassingPilot in every case.
Neither policy may be adapted to fit the new oracle.

Before any Pilot calls, designate within the quotas:

- At least four T fixtures across at least two hooks where PassingPilot's
  documented passive selection is expected to miss the independently justified
  obligation.
- At least one strict action-preferred U fixture in each optional filtering
  hook where its decline behavior is expected to be inferior under the sealed
  reference model.
- At least one retention-preferred case in each filtering hook where declining
  is acceptable, to show that the oracle does not reward activity by default.

These expectations are source-based control declarations, not measured
results. If the future control disagrees unexpectedly, review the oracle,
applicability and harness before any fitness claim. Never alter labels to force
the control to fail. A valid expected control failure is not a packet-integrity
failure; an unexpected control response needs explicit disposition.

| Requirement | Threshold / consequence |
| --- | --- |
| Legal authentic options and ownership | 100%; any foreign/stale/illegal choice is a Pilot integrity failure if the supplied options were valid |
| Observation privacy, immutability and RNG purity | Zero unauthorized exposure, mutation or RNG consumption; attribute engine/harness defects separately from Pilot conduct |
| Duplicate reproducibility and evidence | 100% matching choices and separately recorded continuations where executed; all identities and hashes reconstruct |
| T, separately for each hook with T cells | All T cases acceptable in both seats and every required variant; zero missed guarantees or avoidable forced losses |
| R, separately for each hook with R cells | All R cases meet their sealed acceptable set; no strict dominance violation |
| U, separately for each filtering hook | All U choices have zero exact reference-model regret; exact ties allowed; realized hidden outcomes irrelevant |
| B, separately for every hook | All boundary/integrity cases meet their sealed criteria; cannot offset a quality failure |
| Transformations and privacy pairs | Valid transformations preserve legality and acceptable outcome membership; no unexplained dependence on forbidden information |
| Suite/control completeness | All 72 canonical cases, both seats, category roles, controls and required variants authenticated; no missing or inapplicable cells |

This small designed suite uses 100% acceptable decisions within each category;
V1's pooled 11/12 allowance is superseded. Report exact per-hook/category counts,
individual expected regrets and all failures. Do not average incompatible
resource units or let resource success hide even one tactical failure.

Maintain separate fields: packet integrity VALID/INVALID; suite readiness
READY/INCONCLUSIVE; each hook/category PASS/FAIL/INCONCLUSIVE/NOT-APPLICABLE;
and the two bounded quality claims. Zero-quota categories are NOT-APPLICABLE,
not passes. The overall represented-suite claim is PASS only if readiness is
complete, integrity is valid, controls are resolved and every required category
passes. Known failures remain visible alongside inconclusive categories; no
single label erases another. A missing cell cannot produce a smaller passing
denominator. Calibration suitability remains BLOCKED under every result.

## 8. Variants, privacy accounting and invocation plan

For each of 72 canonical fixtures, require both seat versions and these three
input variants: canonical order, one sealed legal-option permutation, and one
consistent runtime-object-ID renaming. Each variant is replayed twice for each
of the two Pilots, giving a proposed base count:

```text
72 fixtures * 2 seats * 3 variants * 2 replays * 2 Pilots = 1728 invocations
```

Maps must preserve current identity relations, options, targets, costs,
Priority epochs and deck binding. Identical duplicates require identical
choices. Mapped variants may choose different tied optima, but not an inferior
outcome. Variants/replays are not new independent canonical cases.

Enumerate every eligible canonical seat version for an additional opponent-hand
privacy pair. Only opponent-private identities/names may change consistently;
public data, counts, own-deck common knowledge and the deciding player's options
must remain fixed. Require the pair for every eligible version and a concrete
reason for each ineligible one; absence of leaked fields alone is not an
eligibility excuse if an authoritative hidden-state perturbation is available.

Let `K` be the number of eligible canonical seat versions (`0 <= K <= 144`).
One additional paired-input variant, replayed twice per Pilot, adds `4K` calls.
The final plan is **1728 + 4K**, but K and the resulting integer are not set by
this document and must be sealed before scoring. No discretionary variants or
additional calls may be added after results. Mathematical oracle/sensitivity
checks do not invoke Pilots and are not counted as decision trials.

All fixtures also require construction-time checks that changing actual hidden
library order within the same information set leaves the reference distribution,
Q table, acceptable set and oracle digest unchanged. These are oracle-integrity
checks, not rewarded/penalized Pilot outcomes. Exact expectation uses no random
seed. Any future setup/engine-continuation seeds are sealed separately and
inaccessible to the quality oracle.

## 9. Mandatory pre-run seal

After separate preparation authorization, preserve one identified candidate
packet containing all of the following before requesting scoring permission:

1. Exact implementation baseline, gameplay reference, Pilot/runner/evaluator
   and fixture source identities; accepted specification identity; Python and
   dependency versions; clean-worktree record; hashes for card definitions and
   all frozen deck lists used. New evaluator files must be clearly separate
   from frozen engine code.
2. All 72 canonical IDs and primary categories; role/control assignments;
   distinctness rationale; both seats; exact common deck bindings and D vectors;
   complete legal reachable setup/reconstruction; represented dependencies,
   observation payloads and complete engine-generated options.
3. Information entitlement/availability record; reference-prior interpretation;
   support-consistency certificates; private-information exclusions; safety,
   horizon, resource objective and continuation contracts; applicability and
   sensitivity dispositions independent of Pilot output.
4. Every rational branch weight, consequence derivation, Q value, acceptable
   set and strict/tied comparison. Preserve all counterfactual branches needed
   for the claim. The oracle has no actual-world marker or privileged seed.
5. Exact execution order, seats/variants/replay IDs, option-order and identity
   maps, privacy eligibility list and K, final integer invocation count and
   separately recorded setup/continuation seeds. No global clock/RNG dependency.
6. Prospective per-call record schema: recipient, common deck binding, input
   and option hashes, selected option, pre/post mutation/RNG checks, sealed-table
   lookup verdict and separate execution evidence. Selection/consequence fields
   remain unpopulated until scoring is authorized; never create fabricated
   Pilot outputs to make a packet appear complete.
7. Independent oracle privacy, arithmetic, support, transformation and
   reconstruction checks; all unresolved or failed preparation evidence; exact
   source linkage. Any correction creates a new candidate identity; do not
   overwrite failed or scored evidence.
8. SHA-256 sidecars for every artifact, including compressed and decompressed
   hashes when applicable. State whether text hashes use canonical Git/LF bytes.

HQ must independently accept that **sealed pre-run design**, including every
quota and applicability disposition, and then explicitly authorize scoring.
Acceptance of this specification alone does neither. Unexpected opportunity,
semantic or information gaps return to HQ; they are not Pilot successes.

## 10. Retained limits and stop conditions

The gameplay calibration blockers remain unchanged, including the unresolved
Menace/multiple-blocker, graveyard-casting/finality, death/exile/reflexive-return,
linked-exile attack-time play, and instant counter/token families recorded in
V1's dependency register. Deferred mana/timing/replacement risks and terminal
obligation limits remain in force. No inherited Smoke exposure becomes a
fitness denominator or a new calibration population.

Stop any fixture requiring a hidden-state-conditioned oracle, an observation
ledger/general memory system, unavailable history/provenance, opponent inference,
unapproved risk conversion, a second unknown Draw, generic strategic search,
an invalid option map or unsupported gameplay. Do not add a workaround to the
evaluator and call it competence under the frozen model.

## 11. Approval sequence and preservation

The gates remain distinct: HQ accepts this revised specification; HQ separately
authorizes fixture/evaluator preparation; HQ reviews the completed sealed
packet; HQ separately authorizes Pilot scoring. No gate is implied by another.

This review artifact consists only of this specification and its SHA-256
sidecar, on `candidate/pilot-fitness-spec-v2` based directly on accepted main.
V1 specification, V1 failed preparation, V2 failed preparation and Oracle V2
assessment remain intact at the exact references in section 1.

**Current state:** Specification V2 awaiting HQ review. Fixtures and evaluator
not built. No Pilot invoked or scored. Gameplay and policies frozen.
Calibration BLOCKED; Action #33 and Prototype 0.3 NOT AUTHORIZED.
