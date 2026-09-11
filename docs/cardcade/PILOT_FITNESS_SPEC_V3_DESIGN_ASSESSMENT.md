# Pilot Fitness Specification V3 design assessment

**EVIDENCE-ONLY METHODOLOGY REVIEW / NO FIXTURES / NO SCORING.**

This assessment is authorized by HQ after the Hand-bottom/Draw feasibility stop.
Specification V2 remains preserved historical methodology. Gameplay, Pilot
policies, quotas, and evaluator behavior are unchanged by this document. The
assessment recommends evidence requirements and prospective category counts;
it intentionally does not choose a total fixture count.

## Evidence retained from V2

V2's sound foundations carry forward: separate T/R/U/B claims; recipient-
specific information parity; common frozen-deck composition knowledge; the
disclosed 60-copy reference prior; exact rational expectations; zero-regret U
decisions; objective-sensitivity screening; no realized-outcome oracle; legal
engine-generated options; sealed horizons and continuations; independent
privacy/transformation checks; per-hook/category failure visibility; and a
pre-run seal before any Pilot authorization.

The bounded Hand-bottom/Draw audit at `a577c0c` examined both frozen decks with
Manhole Missile, two legal setup schedules, both seats, and the one-Draw horizon.
It audited 1,612 complete-prior rows across 76 probes. It found nine objective
reversals, 18 support failures, two setup multiplicity failures, 47 unresolved
survivors, and only one optimistic two-seat strict-retention design where V2
required two. This is evidence against the V2 quota design, not against the
mathematics or the engine.

## Principle for V3

A hook receives a category only when its represented decision surface naturally
contains that competency and a complete, reachable, information-consistent
witness can be sealed. Counts are the number of independently distinct
witnesses needed to cover the supported competency dimensions and controls.
There is no symmetric quota, minimum denominator, or requirement to invent a
role that the hook cannot represent. A category with no natural witness is
`NOT REQUIRED FOR THIS HOOK`, never an automatic pass. A missing required
witness leaves readiness `INCONCLUSIVE` and cannot shrink a passing denominator.

Every proposed R or U fixture must first enumerate materially plausible resource
objectives at its horizon. Any strict reversal, unsupported exchange rate,
retrospective objective, or objective without a concrete endpoint consequence
rejects the proposal. T/R/U/B remains disjoint per canonical fixture.

## Per-hook evidence design

| Hook | Actual decision surface and information | Minimum evidence for bounded competence | Prospective categories/count recommendation |
| --- | --- | --- | --- |
| Main action | Active player chooses among engine-issued land, cast, supported damage/destroy, activation, or pass options. V2 exposes own hand, public boards, life, mana-relevant land state and exact options. | Reachable setup; complete options and ownership; T continuation for guaranteed win/avoidable loss; R objective with equal safety; objective inventory; at least one conservative and one beneficial comparison for each represented stage that is claimed. | T, R, and B only where each naturally occurs. Count one per distinct stage/comparison, with repeated cases only when the public decision surface or consequence is materially different. U is not required unless a real one-Draw dependency is represented. |
| Attack | Active attacker selects a supported attack subset with visible battlefield, keywords, targets and timing. | Concrete legal attackers; every offered subset; combat continuation through supported blockers/triggers; guaranteed tactical or material consequence; conservative subsets cannot be confused with declining a necessary attack. | T for guaranteed tactical obligations, R for explicit public material/resource comparisons, B for empty/equivalent attack surfaces. U is NOT REQUIRED unless a supported hidden replacement actually affects the sealed attack consequence. |
| Blocks | Defender selects among engine-issued block representations using public attackers, blockers, keywords, damage and timing. | Exact block options; all assignments; combat resolution and safety for every option; proof that a “conservative” block is legal and meaningful; no opponent-private inference. | T where a block prevents an avoidable loss, R only for a concrete equal-safety material comparison, B for no attackers/no blockers/equivalent options. U is generally NOT REQUIRED for the represented surface unless one replacement Draw is explicitly in the sealed decision horizon. |
| Sneak | Active attacking player chooses a supported Sneak option in an existing timing window. | Reachable timing window; exact legal Sneak options; ETB/return/target continuation; public information parity; guaranteed tactical or concrete resource consequence. | T, R, and B as represented. U is NOT REQUIRED unless the frozen Sneak semantics include a genuine one-Draw dependency. |
| Scry | Supplied decision owner orders or bottoms engine-inspected cards. The inspected identities are authorized; an uninspected future Draw is not. | Exact inspected slice and legal placements; all permutations; public objective such as immediate land/creature/answer availability; tied acceptable orders retained; no later hidden Draw oracle. | R for distinct inspected-card ordering/retention consequences and B for empty/one-card/equivalent inspections. T/U are NOT REQUIRED for the current supported scry surface unless a new bounded semantic is separately authorized. |
| Hand-bottom/Draw | Supplied owner optionally moves one own-hand card to library bottom and receives the fixed Draw. Own hand and public context are visible; the replacement is unknown under the disclosed prior. | Complete positive-weight replacement enumeration; same predecision payload/options; one-Draw horizon; equal safety; objective inventory at endpoint; exact Q/regret; both directions of strict preference only when both are genuinely constructible; tied/equivalent choices only when stable across plausible objectives; empty hand/library as B; two-seat transformation/privacy proof. | U strict filter-preferred and strict retention-preferred are separate optional categories, each counted only when witnesses exist. Competing identity and exact-EV tie are NOT REQUIRED FOR THIS HOOK unless naturally stable. B covers empty/boundary/integrity behavior. A single-direction U suite is sufficient when the opposite direction has no natural witness; no universal quota axiom requires both directions. |
| Discard/Draw | Supplied owner optionally discards under the frozen optional semantics, with a conditional Draw. The discarded card is not added to the prior pool. | Exact discard options and one replacement enumeration; support consistency; equal safety; explicit failed-draw/tactical consequence where claimed; objective inventory; no mandatory draw-first behavior misclassified. | U discard-preferred or retention-preferred only as naturally supported, plus B for empty/equivalent behavior. T may be used for a deterministic avoidable failed-draw loss if represented. Competing identity is NOT REQUIRED unless a stable comparison exists. |
| Priority | Exact Priority owner chooses pass or supported response at a specific epoch and Stack state, including nonactive Priority. | Reachable Stack/epoch; complete legal priority options; all passes/resolutions; ownership and timing; tactical guarantee or explicit consequence; privacy and RNG purity. | T for action-required/pass-correct obligations, R only for concrete equal-safety response resources, B for empty/pass-only/equivalent windows. U is NOT REQUIRED unless a supported one-Draw event is part of the same sealed decision. |

These recommendations are lower-bound evidence requirements, not a quota table.
The packet may contain more witnesses when they add a new represented
competency, but changing card IDs, seat numbers, option order, or object IDs is
not a new competency.

## Hand-bottom/Draw decision

The hook should remain in fitness because it exposes an actual private-hand
choice with a bounded uncertainty model. Its claim is narrower: the Pilot can
choose an acceptable filter, retention, or equivalent action when the endpoint
consequence is independently justified.

The minimum honest U evidence is therefore:

1. At least one strict preference witness in every direction that the frozen
   decision surface genuinely supports. If both filter-preferred and
   retention-preferred witnesses can be constructed with stable objectives,
   include both directions. If one direction cannot naturally occur, mark that
   direction `NOT REQUIRED FOR THIS HOOK`; do not manufacture it and do not
   treat its absence as a pass.
2. Any number of additional strict witnesses only when they add a distinct
   endpoint competency, such as a different legal option family or materially
   different resource consequence. Repeated near-copies do not establish a new
   claim.
3. Equivalent or tied choices only when the complete acceptable set is stable
   under every materially plausible objective and exact arithmetic. A one-model
   tie that changes under a defensible objective is inconclusive.
4. B cases for empty hand, empty library, decline-without-draw, and other
   represented integrity boundaries when those states are reachable. B does
   not substitute for a missing U witness.
5. Both seat versions and transformations/privacy pairs for every canonical
   witness, with isomorphism justified by state and option relations rather than
   a seat-number swap.

U should require both directions conditionally, not axiomatically. The reason
is evidentiary: two-direction coverage is valuable when both directions are
real competencies, but V2's fixed two-and-two requirement demonstrated that a
quota can exceed the represented surface. A strict one-direction suite with a
clear `NOT REQUIRED FOR THIS HOOK` disposition is stronger than an artificial
opposite-direction case. Zero-regret scoring, exact Q values, all positive
weights, objective screening, equal safety, and realized-outcome independence
remain mandatory in either direction.

## Common seal and reporting requirements

Before scoring authorization, a V3 packet must preserve source identities and
hashes, card/deck bindings, reachable reconstruction, full engine options,
recipient-specific observations, objective and horizon contracts, all branch
weights/Q values/acceptable sets, transformations, privacy eligibility and K,
per-call schemas, and independent arithmetic/privacy/support checks. It must
report each hook/category as `PASS`, `FAIL`, `INCONCLUSIVE`, or `NOT-APPLICABLE`.
No pooled score may hide a tactical failure, missing witness, or inapplicable
category. Pilot outputs remain absent until separately authorized.

## Disposition

This assessment recommends replacing predetermined quotas with competency-
derived prospective counts. It does not authorize Specification V3 adoption,
fixture construction, evaluator changes, Pilot invocation, scoring, calibration,
Action #33, or Prototype 0.3. HQ review is required before any V3 specification
is written or any fixture work resumes.
