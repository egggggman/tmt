# Issue 289: generic targeted creature destruction on entry

This checkpoint stacks on draft PR #308. Baseline 005's ten deck lists, the original 172-row coverage ledger, all prior checkpoint overlays, and historical games remain unchanged. The small frozen-deck games below are diagnostics only.

## Selection

| Remaining family | Frozen copies / critical rows | Impact and complete intervention | Decision |
| --- | ---: | --- | --- |
| Targeted entry removal: Anchovy & Banana Pizza | 2 / 1 | Its creature destruction applies across the ten-deck environment. Entry events, permanent stack resolution, target choice, destruction, and state-based actions already exist. A general mandatory target clause is bounded and complete. | **Selected.** |
| Modal token/combat trick: Mouser Attack! | 3 / 2 | High exposure, but both modes need casting-time choice, optional target by mode, token creation, temporary +3/+0 and first strike. | Retained as two critical rows until the complete modal spell executes. |
| Conditional cost/protection: Saved by the Shell | 3 / 3 | Casting discount partly executes, but a +1/+1 counter and three temporary keywords must work together. | Retained. |
| Type and P/T transformation: Mind Transfer Protocol | 3 / 2 | Artifact-creature type layer, base 4/5, duration and draw are coupled. | Retained. |
| Linked exile/play, recursion, tutor, hand reset, attacking tokens | 1–2 / remaining rows | Each requires linked permissions, multiple target or choice constraints, or conditional combat entry. | Retained separately. |

The previous [full 18-entry assessment](ISSUE_289_COMBAT_DRAW_LIFE_CHECKPOINT.json) remains the selection basis. [This complete overlay](ISSUE_289_ETB_CREATURE_DESTROY_CHECKPOINT.json) preserves its row identities and current classifications.

## Rules and evidence

The interpreter recognizes mandatory “When this artifact/creature/permanent enters, destroy target creature” clauses only for the matching permanent source type. No card/deck-name execution branch exists. The actual frozen Pizza also retains its separate already supported Food activation. An authenticated self-entry event creates the triggered ability. When that ability goes on the ordinary priority stack, the controller chooses among currently legal creatures of either player; if there is no legal target, it cannot be stacked. On resolution the engine rechecks the same permanent incarnation, creature type, and target protections. Source departure does not cancel the trigger. Legal destruction uses the existing indestructible, zone-transition, and state-based-action path. Telemetry records the entry event, trigger, stack object, offered/selected target, legality, and actual destruction.

- Focused tests use a renamed Food and a creature-source variant, plus the frozen Oracle fixture. They prove normal `{2}{B}{B}` casting/payment, both controllers' legal targets, hexproof exclusion, mandatory target/no-target behavior, invalid chooser rejection, priority, source departure, target departure and non-retargeting, target type change, indestructible prevention, zone movement, event provenance, state-based actions, and identical replay snapshots. Existing Rock Soldiers and shared-removal tests pass.
- Four mirrored Baseline 005 Shredder/Casey and Shredder/Leonardo diagnostic games each matched a deterministic replay with zero runtime errors. The selected three exact deck files are verified against the unchanged Baseline 005 manifest. They recorded **four frozen-source casts, four target selections, and four resolutions**. Per-game digests and event/stack/target IDs are in [machine diagnostics](ISSUE_289_ETB_CREATURE_DESTROY_SMOKE.json). No win-rate inference is made.
- The original ledger SHA-256 remains `56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100`; the #308 overlay SHA-256 remains `1ecb1a04a411d2f7e857278ac3b3161efb380c9f0171858b79f5364234574306`. Exactly one Anchovy row changes: **17 critical / 61 important / 3 partial → 16 critical / 61 important / 3 partial**.
- Semantic runtime changes from `d22d08a2d0181af12413cc816c64edbd096d112d55903711d50c13c1fef2f3e3` to `fb7dab9e04fe1b138c5bb1560cc7d0026d289d8cbe5ca7a7890e12ad69346476`. Historical Baseline 005 controls are not runtime compatible. The frozen Baseline 005 manifest remains `c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac`.
- Full regression: **1,809 passed, 10 skipped**. Baseline 005 structural validation, repository-wide Ruff check/format, relative Markdown links, exact row-change audit, and diff check passed. The structural validator prints historical land-count prose; its authenticated manifest/deck checks pass.

**Checkpoint acceptance:** READY for independent review once final-head GitHub CI is green. **Baseline 005 calibration readiness:** BLOCKED. No 4,500-game control, deck revision, merge, or promotion occurred.
