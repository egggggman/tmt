# Issue 289: generic spell cost reduction checkpoint

Stacked on draft PR #300, remote head `ef555fa9ccd1e6d4d535a697e8b7748786704e45`.
The ten Baseline 005 deck files, original ledger, previous overlays, and historical game evidence
are unchanged. This checkpoint is engine execution evidence, not a balance assessment.

## Resource and casting assessment

| Frozen Oracle clause | Copies / decks | Current planner gap | Decision and evidence |
| --- | --- | --- | --- |
| Affinity for artifacts, Krang, Master Mind | 2 / Krang | Printed generic `{6}` was charged even with controlled artifacts | Supported: each currently controlled artifact discounts one generic mana, never the `{U}{U}`. The cast passes the same legal-action and payment revalidation paths as other permanents. |
| Conditional Turtle discount, Saved by the Shell | 3 / Michelangelo | Printed `{1}` remained charged when a Turtle was controlled | Partial: the conditional discount computes and revalidates; the targeted counter and temporary trample, hexproof, indestructible payload remains unimplemented, so the frozen spell cannot yet be cast. |
| Restricted `{R}` from Purple Dragon Punks | 4 / Casey Jones | Planner only selects lands or unrestricted floating mana; the ledger records color and source lineage but no allowed expenditure context | Blocked: this mana must never be used for ordinary creature spells. Full support requires nonland mana activation, restricted source units, payment context, and transactional consumption across spells and abilities. No claim of closure. |

The first two clauses share one bounded general mechanic: reduce only the generic portion of a
spell's selected cost according to current controlled permanents. Implementing that family
addresses five frozen copies across two decks without weakening the mana ledger's spending
invariant. The four Purple Dragon Punks copies remain the highest-value next resource
intervention, but treating their mana as unrestricted floating `{R}` would be incorrect.

## Executed rules and tests

- The interpreter recognizes generic conditional subtype discounts and affinity for permanent
  types from Oracle text. The payment planner evaluates current battlefield types, controller,
  and qualifying count for each cast. Conditional presence is applied once; affinity counts each
  permanent. Generic cost stops at zero; colored and hybrid requirements remain unchanged.
- Legal actions, affordability, ordinary announcement and Sneak alternative costs share the
  reduced requirement. Commitment revalidates the exact plan before tapping mana sources or
  moving a card. Deterministic `casting_cost_reduced` events carry printed/paid generic values,
  Oracle fragment, and qualifying permanent IDs.
- Focused tests cover opponent-owned artifacts and Turtles, tapped artifacts, type changes,
  discounts beyond the printed generic cost, colored payment, stale plans, ordinary and Sneak
  timing, deterministic state equality, the frozen Krang cast, and the deliberately unavailable
  Saved payload and Purple restricted-mana activation. A historical conformance test now proves
  that supported Affinity never becomes an artifact-entry trigger.
- Four mirrored frozen Krang/Michelangelo and Krang/Casey diagnostics matched four exact
  deterministic replays, with zero runtime errors. Krang received two actual cost reductions:
  `{6}{U}{U}` became `{1}{U}{U}` with five artifacts and `{3}{U}{U}` with three artifacts.
  Diagnostic games are not balance data.
- Final full regression: **1,752 passed, 10 skipped**. Ruff format/check, diff checks, and
  Baseline 005 structural validation passed. The structural validator still prints historical
  stale land-count prose; the authenticated manifest hash below is unchanged.

## Identity, overlay, and gate

- Original 172-row ledger SHA-256:
  `56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100`.
- #300 overlay SHA-256:
  `bd2962a375bdb95144533dac7a92f8ae776eeb87515de71f75bfe7909e70e383`.
- Frozen Baseline 005 manifest SHA-256:
  `c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac`.
- Before runtime: `92528faf3854869ea0905e36102c2aa22b8b36d8a880ccaeebf7ab8668b33cb5`.
- New runtime: `a3044b406738ae66f12ad3173a655849a5b5317ae2c009d80a460edfca94a178`.
- Reproduce the complete overlay with
  `PYTHONPATH=src:tools python tools/report_issue289_casting_resources.py` and diagnostics with
  `PYTHONPATH=src:tools python tools/run_issue289_casting_resources_smoke.py`.
- **24 critical P0**, **64 important P1**, **3 partial** (two Raphael linked-play rows and
  the Saved discount row). One P0 row closed, one P0 row moved from gap to partial;
  85 gaps remain, with seven annotations and 33 covered rows unchanged.

**Checkpoint acceptance:** pending remote CI and independent review.

**Baseline 005 calibration readiness:** **BLOCKED**. No control, deck edit, balance experiment,
merge, or promotion was performed.
