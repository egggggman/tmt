# Pilot Fitness Assessment Specification V3

**STATUS: REVIEW CANDIDATE. Drafted under HQ authorization; not yet accepted.**

This specification retires V2's predetermined quota model for future use. V2,
its accepted baseline, failed preparations, replacement searches, and feasibility
audits remain historical evidence and are not edited. This document authorizes
no fixture construction, evaluator change, Pilot invocation, scoring,
calibration, Action #33, or Prototype 0.3.

## 1. Purpose and bounded claims

The assessment measures only whether the frozen AcceptancePilot selects an
acceptable action in represented, reachable situations at a sealed horizon.
The frozen PassingPilot remains a diagnostic control. A result supports two
bounded claims, reported separately:

1. **Deterministic competence:** the Pilot selects an action that takes a
   guaranteed supported win or avoids a provably avoidable loss when the needed
   facts are authorized and visible.
2. **Uncertainty-sensitive resource judgment:** the Pilot selects an action in
   the sealed zero-regret acceptable set under the disclosed own-deck reference
   prior and one-Draw model.

The result does not establish general strategic play, a true current-library
posterior, long-horizon optimization, memory competence, or calibration
suitability.

## 2. Frozen baseline and retained V2 principles

The future packet must bind the accepted implementation, frozen gameplay
reference, frozen Pilots and card/deck definitions by exact commit and hashes.
The engine owns legality, payment, identities, timing, Stack behavior, random
outcomes and mutation. The evaluator cannot manufacture options, reassign a
chooser, add a timing window, or use hidden state to rank actions.

The following V2 principles remain binding:

- T, R, U and B are separate categories and every canonical fixture has one
  primary category.
- Pilot observations are recipient-specific, immutable and limited to the V3
  interface entitlement. Opponent-private identities and actual hidden library
  order are excluded from the quality oracle.
- The deciding player may know its exact frozen deck list and multiplicities as
  common domain knowledge. The reference prior is `D[c] / 60`; it is not a
  current-library posterior and is never conditioned on a setup seed.
- U uses exact rational arithmetic, at most one unknown replacement Draw, all
  positive-weight definitions, equal safety for every admitted completion and
  zero regret. Realized hidden outcomes never determine a label.
- Every R/U proposal inventories materially plausible objectives at its horizon.
  A strict reversal, unsupported life/card/mana exchange rate, retrospective
  objective, or objective without a concrete gameplay consequence rejects the
  proposal.
- Transformations, privacy pairs, duplicate replays, option permutations,
  object-ID renaming, source hashes, support checks and pre-run sealing are
  independent evidence, never Pilot credit.

## 3. Competency and witness vocabulary

`T` is a deterministic tactical or safety witness: all candidate actions have
the same authorized information, and the acceptable set follows from a
guaranteed supported win or an avoidable loss within the named horizon.

`R` is a deterministic resource witness: safety is equivalent for all candidate
actions and an explicit public or authorized resource predicate has a concrete
endpoint consequence. No universal resource conversion is permitted.

`U` is an uncertain resource witness: one fixed assessed action precedes at most
one unknown replacement Draw; exact branch values produce an acceptable set by
the reference prior. A binary predicate is preferred, and arbitrary cardinal
utilities are forbidden in the initial V3 suite.

`B` is a boundary or integrity witness: empty/pass-only, empty-library,
empty-hand, equivalent-option, endpoint, privacy or transformation behavior.
B demonstrates harness and interface integrity and cannot substitute for a
missing T, R or U competency.

A witness is **complete** only when its legal setup, predecision observation,
full engine-generated option list, horizon, continuation, safety status,
objective contract, oracle table, and outcome membership are reconstructable
without Pilot output. A witness is **genuinely distinct** only when changing its
card names, seat, option order, or object IDs is insufficient to map one full
decision problem to the other: it must add a materially different supported
stage, timing/Stack state, option family, target/assignment relation, resource
predicate, or information pattern. Duplicates and cosmetic variants do not add
competency coverage.

## 4. Applicability and NOT REQUIRED rule

Each hook/category is assigned one of `REQUIRED`, `CONDITIONALLY REQUIRED`,
`NOT APPLICABLE`, or `INCONCLUSIVE` before scoring. A category is
`NOT REQUIRED FOR THIS HOOK` only if the pre-run design preserves either:

1. a bounded feasibility audit that searched the explicitly authorized domain,
   including every relevant frozen deck, materially distinct reachable context,
   supported horizon and genuinely isomorphic seat version; or
2. a structural argument, tied to the frozen semantics and legal option
   generator, showing that the competency cannot be exposed by that hook.

The audit or argument must list its domain, stopping boundary, searched
contexts, positive-weight/support checks and source hashes. “We looked briefly,”
an unresolved construction attempt, or an inconvenient result is insufficient.
Without this evidence, inability to construct a witness is `INCONCLUSIVE` and
blocks readiness. `NOT APPLICABLE` is not a pass and cannot reduce a required
claim silently.

## 5. Per-hook competency obligations

The following are minimum obligations, not a target total. A packet may add a
witness only when it adds a distinct supported competency.

| Hook | Bounded competence claim | Category status and minimum distinct witnesses |
| --- | --- | --- |
| Main action | Choose among the active player's engine-issued land, cast, supported damage/destroy, activation and pass options when represented. | T REQUIRED for each claimed tactical stage: one witness per distinct guaranteed/avoidable consequence. R CONDITIONALLY REQUIRED: at least one per distinct public resource comparison that is actually represented. B REQUIRED wherever an empty/pass-only or equivalent boundary is reachable. U CONDITIONALLY REQUIRED only if a supported one-Draw dependency is present; otherwise NOT APPLICABLE only by structural proof. |
| Attack | Choose a supported attack subset at the correct combat timing. | T REQUIRED for each represented attack obligation, with at least one beneficial and one conservative/materially different witness when both surfaces exist. R CONDITIONALLY REQUIRED for concrete equal-safety material/resource comparisons. B REQUIRED for reachable no-attacker/equivalent surfaces. U is NOT APPLICABLE only if the frozen attack surface has no supported one-Draw dependency, with structural proof. |
| Blocks | Choose among engine-issued block assignments using visible attackers, blockers and combat characteristics. | T REQUIRED for each represented avoidable-loss/guaranteed-consequence family, including a meaningful conservative block where available. R CONDITIONALLY REQUIRED for equal-safety material comparisons. B REQUIRED for reachable no-blocker/equivalent boundaries. U is NOT APPLICABLE absent a supported one-Draw dependency, with structural proof. |
| Sneak | Choose a supported Sneak option in an existing legal timing window. | T REQUIRED for each distinct timing/return/target consequence represented. R CONDITIONALLY REQUIRED where a concrete equal-safety resource consequence exists. B REQUIRED for reachable empty/equivalent windows. U is NOT APPLICABLE absent supported one-Draw semantics, with structural proof. |
| Scry | Order or bottom the exact inspected cards supplied by the engine. | R REQUIRED for each materially distinct inspected-card ordering/retention competency represented; at least one ordering change and one retention witness are required only when both surfaces are reachable. B REQUIRED for empty, one-card or equivalent inspection boundaries. T and U are NOT APPLICABLE for the current surface unless a separately authorized semantic exposes them; future uninspected Draws cannot justify them. |
| Hand-bottom/Draw | Choose whether and which own-hand card to bottom before the fixed Draw under the disclosed prior. | U CONDITIONALLY REQUIRED for every strict direction proven represented: at least one strict filter-preferred and/or one strict retention-preferred witness per distinct supported competency. Both directions are required only when both have bounded witnesses; an unsupported direction may become NOT REQUIRED only under section 4 evidence. Competing identity and exact-EV tie are optional evidence, not mandatory competencies. B REQUIRED wherever empty-hand, empty-library, decline-without-draw or equivalent behavior is reachable. |
| Discard/Draw | Choose among the frozen optional discard/Draw choices, respecting whether the effect is conditional and which card enters the prior. | U CONDITIONALLY REQUIRED for each strict direction proven represented, with one witness per distinct supported consequence. T CONDITIONALLY REQUIRED for a deterministic avoidable failed-draw loss when represented. B REQUIRED for empty/equivalent boundaries. Competing identity is optional and becomes NOT REQUIRED only under section 4 evidence. |
| Priority | Respond at the exact supplied Priority owner, epoch and Stack state. | T REQUIRED for each represented action-required and pass-correct tactical family, including active and nonactive Priority where both exist. R CONDITIONALLY REQUIRED for concrete equal-safety response resources. B REQUIRED for pass-only/empty/equivalent windows. U is NOT APPLICABLE absent a supported one-Draw dependency, with structural proof. |

For a category marked REQUIRED, at least one complete witness is the minimum;
additional witnesses are required for each distinct competency dimension stated
in the claim. No category receives a numeric quota merely for symmetry.

## 6. Hand-bottom/Draw U direction rule

The hook remains in the fitness suite because the represented private-hand
choice is real and its bounded uncertainty can be evaluated exactly. The V3
rule is conditional:

- A strict filter-preferred direction is CONDITIONALLY REQUIRED if a complete,
  objective-stable witness exists in the authorized domain.
- A strict retention-preferred direction is CONDITIONALLY REQUIRED under the
  same standard.
- If both directions are proven represented, both are required for the bounded
  two-direction claim. If only one is proven represented, the other may be
  `NOT REQUIRED FOR THIS HOOK` only with the feasibility or structural evidence
  required by section 4.
- If neither direction has a complete witness, the hook/category is
  `INCONCLUSIVE`, not a pass and not automatically optional.
- Competing-hand-identity and exact-EV tie cases are optional evidence. They may
  strengthen coverage but are not required competencies unless HQ later adopts
  them explicitly and a feasibility audit supports them.
- B/integrity cases remain required wherever reachable and never replace a U
  witness.

For every U fixture, the packet must preserve the complete predecision payload
and options across every positive-weight replacement, exact `Q` and regret,
acceptable indices, equal safety and terminal status, continuation information
parity, and objective-sensitivity disposition. The selected card is not added to
the replacement pool; decline draws nothing; empty-library return is B.

## 7. Controls and transformations

Assess AcceptancePilot and PassingPilot separately. Declare source-based control
expectations before calls, including cases where the passive control should miss
an independently justified obligation. An unexpected control result triggers
review of oracle, applicability and harness; labels are never changed to force
an expected outcome.

Every canonical fixture requires both seat versions when a genuinely isomorphic
transformation exists. The packet must prove legality, option relations,
ownership, public/private fields, objectives and acceptable membership are
preserved. It must include a sealed legal-option permutation and a consistent
runtime object-ID renaming. Duplicate replays must reproduce choices and
continuations. An opponent-private privacy pair is required whenever an
authoritative hidden-state perturbation can preserve public data and options;
every ineligible version needs a concrete reason.

## 8. Acceptance criteria and reporting

Before scoring, the candidate packet must contain the source and dependency
hashes, canonical fixture IDs and categories, complete reachability evidence,
observations/options, common deck bindings, objective/horizon contracts, every
branch/Q table, transformations/privacy schedule, per-call schemas, and
independent support/privacy/arithmetic checks. Pilot output fields remain empty.

Report packet integrity separately from suite readiness. For each hook and
category report `PASS`, `FAIL`, `INCONCLUSIVE` or `NOT APPLICABLE`; show every
failure, missing witness, objective reversal, and unresolved applicability.
There is no pooled pass. A represented-suite claim passes only when all
REQUIRED categories have complete witnesses, all calls are acceptable, controls
are resolved, integrity is valid, and no category is hidden by aggregation.
NOT APPLICABLE categories do not pass and do not reduce the evidence claim.
Calibration remains a separate blocked decision.

## 9. Invocation count and pre-run seal

No invocation count is fixed by this specification. After canonical fixture IDs,
categories, both justified seat versions, variants and replay schedule are
sealed, let `F` be the number of canonical fixtures and `K` the number of
eligible canonical seat versions for an additional opponent-private pair. The
base plan is:

```text
F * 2 seats * 3 variants * 2 replays * 2 Pilots = 24F
```

The privacy addition is `4K`, giving:

```text
final_invocation_count = 24F + 4K
```

`F` and `K` are sealed values, not tuning parameters. No discretionary calls,
fixtures, variants or replays may be added after scoring authorization.

The mandatory pre-run seal must preserve the exact implementation baseline,
all canonical IDs and distinctions, both seats and deck bindings, complete
observations/options, information entitlement, support certificates, objective
and continuation contracts, exact rational tables, transformation/privacy
eligibility, invocation order, per-call integrity records, and all source
sidecars. Scoring requires a separate explicit HQ authorization after this seal.

## 10. Current status

This is a V3 review candidate derived from the accepted design assessment at
`27a5dd8`. It is not yet Specification V3 authority. Fixture construction is
paused; V2 remains preserved historical evidence; Pilots have not been invoked;
scoring, Action #33, calibration and Prototype 0.3 remain unauthorized.
