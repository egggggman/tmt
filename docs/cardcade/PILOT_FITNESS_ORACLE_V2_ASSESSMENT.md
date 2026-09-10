# Pilot Fitness Oracle V2 Assessment

**Recommendation for HQ review: separate deterministic tactical competence from
uncertainty-sensitive resource judgment.** Retain strict deterministic safety
and integrity requirements. For the uncertainty track, prefer a small, explicitly
disclosed belief model with exact finite expectations and a predeclared resource
objective. Never grade a choice by the realized hidden replacement card.

**Status: assessment only; methodology not accepted or implemented.** This is
neither a rewritten fitness specification nor a sealed experiment. No Pilot
invocation, Game construction, gameplay simulation, scoring, policy change,
interface change or gameplay change was performed for this assessment.

There is an important prerequisite: accepted pilot-input-v2 does not contain a
deck-composition or observation-history contract. A posterior computed from
evaluator-only history is not a fair oracle for that input. If HQ retains the
current inputs without approving any additional knowledge contract, use only
input-grounded deterministic/dominance judgments and explicitly leave broader
uncertainty competence unassessed. Do not silently repair this gap in a harness.

## 1. Provenance and the decision now before HQ

| Anchor | Exact identity / status |
| --- | --- |
| Accepted interface baseline; current main after fast-forward | `fa3f4944a7209f22e70d783d9a7f9abca3b37534`, pilot-input-v2 |
| Frozen gameplay reference | `de52f57a24a5c29a258573ad673051a0aa5c7e5c` |
| Historical Fitness Specification V1 | `ca9757b956eafc4b8d03c495dabb03eaab6fe931` |
| Accepted input-contract assessment | `f3814ae2fc1c9b344960167fcaff5c9630a0a075` |
| Preserved V2 preparation stop | `a19c1a06596862ea3cf947700c57149978e7f77e`, branch `candidate/pilot-fitness-v2-preparation` |

The stop is methodological: the two optional filtering hooks expose the
relevant observable context while correctly concealing the next Draw. V1's
action-required quotas cannot be justified merely by arranging a favorable
hidden replacement. This assessment asks how to judge the **decision before the
Draw**, conditional on legitimate information, while retaining those privacy
and gameplay boundaries.

Source-backed facts and inherited execution evidence are distinguished here
from proposals and mathematical examples. No new empirical fitness evidence is
claimed. The recommendation does not promise that revised quotas will yield 96
honest fixtures; HQ must choose the methodology before quota design resumes.

## 2. Alternatives and their claims

| Method | What establishes an acceptable choice | Strength | Limitation / recommendation |
| --- | --- | --- | --- |
| V1 deterministic forced outcomes for every category | A visible-information proof of a guaranteed result | Strong claims where applicable | Cannot require an uncertain replacement to guarantee improvement. Preserve as historical methodology. |
| Dominance-only | An alternative is at least as good in every admissible hidden completion and better in some; preferences/objectives must also be fixed | Does not need probability weights | Often leaves filtering alternatives incomparable. Report UNASSESSED/INCONCLUSIVE rather than declaring every nondominated action competent. Useful fallback. |
| Worst-case or minimax-regret | Optimize a sealed adverse-completion criterion | Makes conservative choices reproducible without a single prior | Encodes a risk attitude; is not uniquely rational and may systematically reject useful filtering. Assess only if HQ explicitly wants that claim. |
| Known-composition conditional expectation | Maximize the expected predeclared objective under a justified player-information distribution | Can judge useful filtering without seeing the actual Draw | Requires an auditable knowledge model and information parity. Preferred bounded uncertainty method once those prerequisites are authorized. |
| Fixed disclosed reference prior | Use a common, prospectively declared distribution independent of the live hidden deck | Reproducible synthetic benchmark; potentially less history machinery | Measures behavior under that announced model, not natural ten-deck competence. It must actually be available to the assessed decision maker. |
| Separate deterministic and uncertainty tracks | Apply the appropriate rule to each eligible fixture, with separate denominators and claims | Preserves tactical rigor without mistaking uncertainty for clairvoyance | **Recommended structure.** Does not itself supply the missing belief inputs or rewrite quotas. |

Do not call a nondominated action optimal without a probability or risk model.
Likewise, an expected-value optimum is conditional on its prior, horizon and
objective; it is not an unconditional statement about good Magic play.

## 3. Information contract: evaluator and Pilot

Let `I` denote all information permitted to the deciding player at the instruction
point, and `A(I)` the complete engine-supplied option sequence. Let `M` be the
prospectively declared model/rubric. The quality oracle must be a function of
`(I, A(I), M)`, not of the actual hidden state or its seed.

| Information | Pilot entitlement | Evaluator use for quality |
| --- | --- | --- |
| Current accepted V2 observation and engine options | Exact recipient-bound payload | Same payload and complete options; no omniscient substitute |
| Own initial deck composition | Only if the assessment explicitly makes it legitimate knowledge and makes it accessible | May initialize the prior only after that contract is approved |
| Own observed draws / public movements / authorized private inspections | Only facts actually observed and retained under an approved knowledge policy | May condition on exactly those facts, with observer-specific provenance |
| Public card definitions and represented rules | Audited descriptions/declared common rule knowledge | May calculate consequences of hypothetical visible/revealed cards, but cannot infer actual hidden membership from catalog access |
| Opponent private hand identities | Forbidden | Forbidden as oracle conditions or response-policy inputs |
| Actual hidden library order, hidden registry, engine RNG state or seed | Forbidden as decision information | Forbidden in prior construction, action ranking and tie-breaking |
| Fixture setup and authoritative evidence | Only its explicitly disclosed subset | A separate integrity auditor may authenticate setup; hidden facts do not enter the quality oracle |
| Realized outcome after the decision | Observed only when rules reveal it | May document execution integrity later; cannot retroactively change decision quality |

Evaluator computation may be stronger than Pilot computation; evaluator
**information** may not be stronger for the criterion being assessed. A packet
being public to human reviewers does not make its extra fields available to a
Python Pilot method. Entitlement, delivery and actual payload must be recorded
separately. A frozen policy need not use every supplied fact, but it must not be
penalized for lacking an input it was never given.

### Present V2 capability

`DecisionContextV2` has own hand, both boards, life, hand/library sizes, turn/step
and own lands played. Scry adds the current inspected slice. It has no initial
deck manifest, prior, past observation ledger, known-library segments, graveyard
or exile inventory. `GameViewV2` is narrower still. The existing policies have
no newly authorized memory or belief service.

Consequently, “deck list minus legitimately observed cards” is a **conditional
future design**, not something the present V2 payload already supports. Three
possible dispositions require explicit HQ selection:

1. Keep current inputs and limit the claim to deterministic/robust judgments.
2. Approve an accessible common synthetic prior as assessment-domain knowledge,
   with a concrete delivery audit before any frozen-Pilot scoring. Merely putting
   a distribution in evaluator metadata is insufficient.
3. Commission a separate bounded knowledge-input assessment for a sufficient
   statistic or observation ledger. Do not modify pilot-input-v2 as part of this
   assessment, and do not infer authorization for a generic visibility system.

If the information-delivery requirement cannot be met without a separately
authorized change, the uncertainty track remains blocked. Choosing a method
does not automatically authorize that change.

## 4. Bounded known-composition model

**Proposed initial scope:** the deciding player's own next replacement Draw,
with a known finite card multiset and a justified exchangeable unknown segment.
Exclude opponent-hand inference, opponent policy learning, unknown deck lists,
mulligan-selection inference, unidentified foreign cards, untracked returns,
and undocumented searches or top/bottom manipulations. These are applicability
limits, not assumptions that the missing effects never happened.

For a clean state, let `D[c]` be the declared initial number of physical copies
of card definition `c`. Let `O[c]` count those original copies currently known to
be outside the library; `T[c]` and `B[c]` count copies in legitimately known top
and bottom segments. Then the unknown pool is:

```text
U[c] = D[c] - O[c] - T[c] - B[c]
N_unknown = sum_c U[c]
N_library = N_unknown + length(T) + length(B)
```

This is inventory accounting, not “subtract every card ever seen.” A card drawn,
returned and seen again must not be subtracted twice. Runtime incarnation IDs
are not physical-copy identities; any lineage used by the knowledge builder
must itself be justified by permissible observations. Tokens and copies do not
silently consume original deck multiplicities. Negative counts, unexplained
library-size disagreement or ambiguous lineage make the fixture inapplicable.
The builder must not resolve ambiguity by reading the hidden registry.

If a known top segment exists, it controls the next Draw until exhausted. If
the unknown segment is exchangeable, the next unknown card has weight
`P(c | I,M) = U[c] / N_unknown`. Duplicate copies contribute multiplicity; card
names/types are not each assigned equal probability. An outcome-equivalence
class can be compressed only after proving that every member has the same
consequence for every candidate action and the sealed horizon.

For two unknown Draws without replacement, the ordered weight is
`U[c]/N * (U[d] - 1[c=d])/(N-1)`. Count-based objectives can use the corresponding
hypergeometric distribution. Sampling-without-replacement counting is standard;
the applicability restrictions above are this assessment's proposal, not a
claim that every Cardcade library is exchangeable. [MIT probability
recitation](https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/3c60959194374eab8b4f75da74d5cacf_MIT6_041SCF13_Edit2_Take2_No13_Ch1_HypergeometicProbabilities.pdf)

For general permitted observations, the conceptual rule is
`P(w | I,M) proportional to P(I | w,M) * P(w | M)` over hypothetical worlds `w`.
It is not permission to invent likelihoods for opponent choices or to add an
unbounded Bayesian engine. If exact conditioning is unavailable in the bounded
model, stop that fixture. If composition itself is unknown, prefer an explicit
set of allowed priors with robust judgments, or decline to assess; do not infer
a point estimate from the actual hidden library.

### Filtering-specific updates

- Hand-bottom/Draw with a nonempty library draws its preexisting top. The
  selected hand card is appended at the known bottom and is **not** mixed into
  the unknown top pool. With an empty library it is drawn back deterministically.
- Discard/Draw removes the selected hand card from hand into graveyard, then
  draws from the preexisting library. It is **not** added to that library's urn.
  Empty-library failed Draw is a deterministic safety case.
- Scry uses its exact inspected order for retained top cards. Bottomed cards
  form a known bottom segment; the next uninspected Draw remains uncertain.
  Carrying this knowledge to another instruction point requires an approved
  memory/input contract. This assessment does not introduce one.
- A later shuffle changes ordering knowledge under a separately authenticated
  transition. Do not retain a stale known-top assertion or reconstruct the
  shuffle from its secret seed.

## 5. Expectations, horizons and acceptable sets

For each action `a`, define a bounded consequence variable `X(a,w)` under the
frozen rules, a sealed continuation protocol `C`, and an explicit objective
`u(X)`. The proposed oracle is:

```text
Q(a | I,M,C) = sum_w P(w | I,M) * u(X(a,w; C))
best_value = max_{b in A(I)} Q(b | I,M,C)
regret(a) = best_value - Q(a | I,M,C)
acceptable = {a in A(I): regret(a) <= epsilon}
```

Use exact rational counts/probabilities for the first bounded model. Recommend
`epsilon = 0` for an exactly enumerated, fully specified resource objective;
ties remain acceptable. Any nonzero practical indifference margin is a
prospective normative choice for HQ, never an adjustment after observing a
Pilot's decisions. Compare mapped action identities and tied outcomes, not
arbitrary tuple positions.

**Safety and resource separation:** retain deterministic proofs of avoidable
losses and guaranteed wins where available. For the initial resource track,
prefer fixtures whose candidate actions have equal terminal win/loss behavior
within the declared horizon, then compare a concrete resource predicate or
quantity. Do not invent a universal exchange rate between life, cards, mana and
risk. A fixture with unequal loss probabilities or conflicting resource goals
needs a separately approved risk preference or remains inconclusive. This is a
bounded claim, not a complete theory of rational play under risk.

The horizon must be an existing instruction/step endpoint, such as completion
of the current filtering resolution or the next already-offered main stage.
An objective such as access to a payable represented blocker must be grounded
in the public board and that endpoint. “Get rid of this card” is not enough.
Do not lengthen a horizon until one action looks best or add a missing response
window to make the hypothetical continuation work.

**Arithmetic illustration, not a Cardcade fixture or scored result:** suppose
an approved knowledge model has ten possible replacement copies, four meeting
a publicly grounded resource predicate, and six not meeting it. Suppose both
choices satisfy the same sealed safety/resource-preservation constraints and
retention cannot meet that predicate at the endpoint. Then the expected binary
predicate value is `4/10` for filtering and `0` for retention. A realized miss
does not make the ex-ante filtering decision wrong. If retention already meets
the predicate with certainty and filtering risks losing it, the comparison
changes. These assumptions require legal reconstruction before any fixture can
count; the example supplies neither a quota cell nor natural-game evidence.

## 6. Continuations must respect information

Exact enumeration alone does not prevent clairvoyance. A future evaluator must
not optimize an unseen continuation separately in every hidden world and then
average those perfect-information optima. It must fix the assessed action
before the Draw and require identical continuation decisions in worlds that
remain indistinguishable at each later choice. Once a card is legitimately
drawn/revealed, conditioning a later action on that new observation is valid.

This is the strategy-fusion risk described in imperfect-information search:
world-specific strategies can assume distinctions a player cannot observe.
The cited research identifies the issue; our proposal is to avoid it by using
a bounded, observation-consistent continuation contract, not to implement its
search algorithms. [Long, Sturtevant, Buro and Furtak,
AAAI-10](https://webdocs.cs.ualberta.ca/~nathanst/papers/pimc.pdf)

The first model should use one uncertain replacement followed by automatic
effects or a small sealed observation-based continuation table. No assessed
Pilot is used as a rollout policy. No generic strategic search is authorized.
Avoid horizons requiring opponent private responses; otherwise every opponent
information set and response assumption would also need prospective approval.
All hypothetical completions must support the same predecision legal option
set and observation; otherwise the information-set construction is invalid.
Store all branches needed to justify comparisons, including unfavorable ones.
Unsupported semantics or unresolvable observation distinctions invalidate the
fixture's applicability, not the Pilot.

## 7. Preventing realized-outcome leakage

The future design should separate three capabilities:

| Component | Receives | Must not receive / do |
| --- | --- | --- |
| Knowledge/model builder | Authorized observations and approved common prior; provenance allowlist | Read actual unseen library order or infer it from IDs/seeds |
| Quality oracle | Canonical `I`, engine options, sealed distribution, rubric and hypothetical branch descriptions | Read live GameState, actual hidden completion, seed, evidence stream, or Pilot result when selecting its rubric |
| Integrity auditor | Authoritative setup and later execution evidence | Export hidden facts into the quality inputs or let realized success change the quality verdict |

A hypothetical branch may contain a candidate hidden card for consequence
calculation, but every branch comes from the declared distribution. There is no
special branch tagged “the actual one,” and the actual top card has no extra
weight. Choosing the highest-valued action occurs after taking expectations,
not by selecting the best action in the realized world.

Before eventual scoring, require these independent checks:

- Permute the actual unobserved library order while preserving `I` and options:
  the distribution, `Q` table, acceptable set and oracle digest must be identical.
- Change the actual hidden completion within the same declared information set:
  quality remains unchanged even when realized consequences differ.
- Alter forbidden seed/registry/evidence handles or remove their availability:
  the quality oracle remains unchanged and cannot query them.
- Change a legitimate observation or disclosed prior while holding a live
  hidden realization fixed: recompute only as the approved model prescribes.
- Verify probability mass sums to one, nonnegative integer inventory, known
  segment accounting and correct without-replacement dependence.
- Check option permutation, identity renaming, seat conversion, duplicate
  replay and information-consistent continuation maps without repairing policy.

Seal all oracle values/acceptable sets before future Pilot calls. A selected
action is later looked up in that table. Actual draws can be logged separately
for execution auditing, but cannot earn a bonus or penalty for being lucky.
No selecting/replacing fixtures according to observed Pilot output, helpful
seeds, or successful realized outcomes.

## 8. Reproducibility and weighting

Prefer exact enumeration for the first version: proposed cap of one unknown
replacement Draw, at most 60 distinct card definitions (multiplicities retained),
and at most 1,000 enumerated action/outcome rows per fixture. These are **proposed
scope limits**, not accepted thresholds. Count before sealing; if exceeded,
reject the fixture or seek a revised bound. Do not truncate branches or silently
substitute a sampler. Any later two-Draw/multi-step extension requires its own
bound and review.

Within a fixture, copy multiplicities determine outcome weights. Between
fixtures, report equal canonical-fixture weight within each declared stratum
unless HQ approves another scheme prospectively. Seat copies, permutations,
identity variants and replays are integrity/robustness checks, not independent
sample-size multipliers. Expected regret in incompatible resource units must
not be pooled. Report per-objective/per-stratum results and explicit unavailable
cells; no small easy category can hide a failed safety category.

A later sealed packet must record:

- Exact engine/interface/Pilot/spec/oracle versions and source identities;
  card definitions and deck manifests; normalized encoding and hash scheme.
- Observer and instruction point; full allowed knowledge with provenance;
  inaccessible facts; whether knowledge was delivered in a payload or common
  domain contract; an applicability verdict independent of Pilot output.
- Finite support, multiplicities, known segments, rational branch weights,
  conditioning assumptions, canonical ordering and deterministic arithmetic.
- Complete legal options; exact objective, horizon, continuation table,
  risk/indifference rules, every `Q` value and acceptable set, with derivations.
- Transformation maps, privacy-eligible list, exact K and invocation count;
  reconstruction metadata, all sidecars, and compressed/decompressed hashes
  if applicable. Do not reuse V1's `2304 + 4K` as a commitment before the revised
  design and repetitions have been approved.

Exact expectations need **no RNG seed**. Any future setup/engine-continuation
seed is separate metadata and barred from the oracle. If HQ later permits
Monte Carlo, it needs independent declared sampling seeds, fixed samples shared
across action comparisons, precision/error rules and an inconclusive zone;
the live engine seed is still not a sampler for decision quality. Sampling is
not recommended for this first bounded assessment.

Sensitivity should be designed before scoring: when more than one prior is
legitimately plausible, compare actions over a declared family `P`. Accept a
robustly preferred action only if its ranking meets the approved criterion for
every member. If rankings reverse, label the result model-dependent or
inconclusive; do not pick the prior that agrees with a preferred Pilot.

## 9. Consequences for the future specification

The methodological revision should distinguish:

1. **Integrity:** legal authentic options, observer binding, privacy,
   immutability, determinism and reconstructable evidence remain uncompromised.
2. **Deterministic tactical competence:** visible-information guarantees and
   safety/dominance claims remain strict where genuinely applicable.
3. **Uncertainty-sensitive resource judgment:** a choice is acceptable according
   to its sealed ex-ante criterion, with prior, objective and applicability
   disclosed. Realized outcomes do not decide correctness.
4. **Coverage limits:** absent knowledge, unresolved risk preferences,
   unsupported semantics and missing runner opportunities remain distinct from
   policy errors. No artificial replacement cases or pooled passing denominator.

Do not relabel uncertain resource judgments as “forced wins.” Do not retain a
uniform 4/4/4 quota merely by changing labels. The revised specification should
assign categories to what each hook can honestly assess and then obtain HQ
approval of counts, minimum gaps, controls and acceptance criteria. Whether 96
remains the appropriate total is a subsequent design decision; this assessment
does not change it. PassingPilot remains a later diagnostic control, not a
source of oracle labels or a rollout opponent.

## 10. Recommended HQ disposition and stop boundaries

**Choose the split-track methodology, with exact finite expectation as the
preferred uncertainty oracle conditional on an approved, accessible knowledge
contract.** If that contract is not authorized, the honest near-term fallback
is a separately named deterministic/dominance-only assessment with uncertainty
fitness explicitly unassessed. Neither path establishes broad calibration
fitness.

Before rewriting the specification, HQ should settle: the knowledge source and
delivery route; exact-expectation versus robust-only claims; the initial scope
bound and horizon; and the treatment of probability/risk tradeoffs. Thresholds,
quotas and fixture counts are then prospective specification work, not changes
made by this report.

Stop any future design requiring hidden-state-conditioned priors, undisclosed
history, ad hoc utility conversions, clairvoyant continuations, unsupported
semantics, generic strategic search or a new visibility/memory system outside
separate authorization. A methodology approval alone is not implementation,
Pilot execution, scoring, calibration or permission to change pilot-input-v2.

## 11. Evidence and preservation

Local primary sources: the accepted V2 projection and runner/Pilot contracts at
`fa3f4944a7209f22e70d783d9a7f9abca3b37534`; Fitness Specification V1 sections 3–6;
the preserved preparation stop at `a19c1a06596862ea3cf947700c57149978e7f77e`;
and `Game.commit_hand_bottom_draw`, `Game.commit_discard_draw`, `Game.draw`
for transaction ordering. Their exact identities are recorded in the companion
assessment manifest. External references above support probability counting
and the information-set caution; the Cardcade limits and recommendations are
our proposed design judgments, not empirical claims from those publications.

Only this assessment, its evidence manifest and SHA-256 sidecars are added on
`candidate/pilot-fitness-oracle-v2`, based directly on accepted main. The failed
preparation is preserved separately, not merged into this methodology candidate.
No fitness specification is rewritten and no evaluator is implemented.

**HQ selection pending.** The 96-fixture packet remains unsealed. Pilot scoring,
Action #33 and Prototype 0.3 remain NOT AUTHORIZED; calibration remains BLOCKED.
