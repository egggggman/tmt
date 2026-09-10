# Pilot Fitness V2 preparation — return to HQ

**INCONCLUSIVE SUITE READINESS. No sealed 96-fixture packet exists.**
This is a source-based preparation diagnostic, not a Pilot result or a universal
proof that no valid filtering fixture can exist. No Pilot or Game was invoked
during this preparation. No quota or tactical oracle has been certified.

## Accepted baseline and completed merge

`main` was fast-forwarded and pushed to the accepted implementation at exact SHA
`fa3f4944a7209f22e70d783d9a7f9abca3b37534`. No merge commit changed that identity.
The new assessment-interface baseline is **pilot-input-v2**, accepted by HQ.
The gameplay reference remains `de52f57a24a5c29a258573ad673051a0aa5c7e5c`.
The accepted fixture specification remains
`ca9757b956eafc4b8d03c495dabb03eaab6fe931`.

This diagnostic is a separate candidate on
`candidate/pilot-fitness-v2-preparation`. It does not revise the accepted V2
implementation, the specification, either Pilot, any deck or either matrix.
The earlier V1 readiness failure and the V2 compatibility evidence remain intact.

## Controlling stop and remaining problem

Specification section 4 requires 12 canonical fixtures per hook: four forced,
four resource/optional and four boundary/pass cases, including at least two
action-required and two conservative cases. It expressly prohibits constructing
false obligations to fill a quota. Sections 3–4 require input-grounded oracles;
the initial suite has no belief model and may not use a hidden future Draw to
establish a forced correct choice.

V2 supplies public context and recipient privacy as intended. It does **not**
reveal the next library card to `choose_hand_bottom_draw` or
`choose_discard_draw`. I could not establish the required action-required cases
for these hooks within that information boundary. The controlling stop applies
before the rest of the 96-fixture suite can be sealed.

This is an unresolved **oracle-feasibility** issue under the accepted rules,
not a regression in V2, a finding about Pilot choices, or authorization for more
input fields. Source inspection supports the following rejected design paths:

| Proposed path | Why it does not establish the missing quota |
| --- | --- |
| Filter to obtain a needed creature/removal/land | A favorable hidden top card can make the evaluator's continuation useful, but the input does not establish that card. A different hidden top can remove the claimed guaranteed improvement. |
| Filter a redundant land or currently unpayable card | The public board can establish redundancy or present unpayability. It does not establish that the replacement is better. A hidden duplicate can supply the same printed card facts. |
| Bottom/Draw with an empty library | The selected card is moved to the bottom, then drawn back as a new incarnation. This supplies a useful boundary test, but does not itself establish a required material gain over retaining it. |
| Discard/Draw with an empty library | Taking the option discards a card and fails the Draw. The existing failed-draw state-based action supplies a restraint case, not a useful-action case. |
| Empty hand or only one legal option | These can test legality and boundaries, but cannot replace tactical/resource quotas. |
| Assume a remembered Scry, deck composition, graveyard synergy or future policy | No concrete eligible construction was established. Do not silently provide prior private knowledge, change memory policy, infer an unprovided library model, or implement missing rules. |

The duplicate-top argument is an **information-equivalence counterexample to
the generic “the replacement is better” justification**, not a reconstructed
legal fixture or a proof that all possible combinations of represented effects
are impossible. For example, swapping a redundant Plains for an unseen Plains
does not obtain the missing creature; swapping it for an unseen creature might.
The same filtering input cannot certify the latter outcome. Both-seat copies,
option permutations and renamed IDs cannot resolve this missing premise.

No contingent “take a chance because retaining loses” position is promoted to a
guaranteed-win/avoidable-loss oracle: that would require a permitted uncertainty
criterion, not the evaluator's favorable seed. Likewise, the externally imposed
objective “move this card out of hand” would not by itself establish useful
gameplay competence.

## Source evidence and scope of validation

The accompanying diagnostic JSON records the exact accepted source/deck Git
blobs and LF-normalized SHA-256 identities, V2 dataclass field inventory, and
complete source excerpts/AST identities for the filtering choice/commit methods
and `Game.draw`.

At the accepted baseline, the relevant source anchors are:

- `pilot_input_v2.py`: `DecisionContextV2`, `HandBottomDrawViewV2` and
  `DiscardDrawViewV2` expose own hand and library counts, not library identities.
- `engine07.py`: `commit_hand_bottom_draw` moves the selected hand object to the
  library bottom before drawing the existing top; with an empty library this is
  the card just bottomed.
- `engine07.py`: `commit_discard_draw` discards the selected object before the
  conditional Draw; declining does neither.
- `engine07.py`: `draw` sets `failed_draw_pending` on an empty library;
  `FailedDrawStateBasedAction` handles the resulting loss at its existing check.

`scripts/check_pilot_fitness_v2_readiness.py` authenticates those sources and
preserves the manually reviewed conclusion. It imports neither the engine nor
either Pilot, constructs no game, executes no continuation and contains no
scoring mode. Its deliberate exit code **2** means readiness is inconclusive,
not that a Pilot failed. Two executions produced byte-identical diagnostic
output. Lint/format and staged whitespace checks were used; no gameplay or
policy test suite was run during preparation.

## Packet accounting

| Deliverable | Status |
| --- | --- |
| Required canonical fixtures | 96; quotas unchanged |
| Sealed canonical fixtures | 0; no partial suite presented as compliant |
| Both seats / permutations / identity maps | Required, not sealed |
| Privacy-eligible list and exact K | Undetermined (`null`, not zero) |
| Planned final invocation count | Undetermined; formula remains `2304 + 4K` |
| Seeds / horizons / acceptable sets / continuations / reconstruction | Not sealed |
| Actual Pilot invocations / scored decisions | 0 / 0 |
| Actual Game constructions / executed oracle continuations | 0 / 0 |
| Accepted engine/interface/Pilot/deck/matrix changes | None |

No results for the other six hooks are claimed: they were not certified after
the controlling quota stop. The JSON and this report have SHA-256 sidecars;
the diagnostic script's source identity is included in the JSON. Historical
evidence is not overwritten.

## HQ decision needed

To resume under the unchanged specification, provide or authorize review of a
concrete V2-input-grounded construction that establishes the missing useful
filtering obligations, including the exact observable premise, represented
continuations and horizon. This report does not rule such a construction out.

Alternatively, HQ can explicitly revise the oracle contract (for example a
separately specified uncertainty/belief model) or revise the affected quotas and
claim. Either would need a new identified specification and independent review.
No such revision is made or presumed here, and no extra visibility or gameplay
implementation is recommended as an automatic fix.

Pilot scoring remains **NOT AUTHORIZED**. Calibration is **BLOCKED**. Action #33
and Prototype 0.3 remain **NOT AUTHORIZED**. The accepted V2 baseline on main is
preserved; the 96-fixture sealed-packet gate remains incomplete.
