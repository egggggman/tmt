# Issue 289: bounded graveyard recursion

This checkpoint stacks on validated draft PR #315. It preserves all ten Baseline 005 deck lists, the original 172-row ledger, every previous overlay, and historical game evidence. The small diagnostics below test execution and deterministic replay only, not balance.

## Critical-family ranking

Frozen copies count cards; rows count preserved Oracle fragments. The Last Ronin's Technique is one copy repeated in two original rows.

| Family | Copies / critical rows | Deck identity and cross-deck effect | Implementation scope |
| --- | ---: | --- | --- |
| Raphael linked exile/play | 2 / 2 partial | Very high: stored access and attack permissions | Broad linked identity, duration, timing, and castable card families. |
| Leonardo graveyard recursion | 2 / 1 | High: board recovery and entry triggers | **Selected:** bounded one-or-two targets, existing graveyard zones, stack, Sneak and creature-entry paths. |
| Michelangelo top-eight selection | 2 / 1 | High: two free creatures | Coupled hidden choices and aggregate mana-value cap. |
| Last Ronin attacking tokens | 1 / 2 | High: combat pressure | Conditional tapped-and-attacking token entry and defender provenance. |

The complete printed sorcery says “Return one or two target creature cards each with mana value 3 or less from your graveyard to the battlefield.” It has a fixed Sneak alternative cost. The interpreter recognizes the complete sentence and exact Sneak preface, deriving the mana-value limit from the Oracle text. It rejects changed restrictions or extra instructions. A renamed fixture executes identically; execution contains no card-name or deck-name branch.

## Execution and validation

Legal actions enumerate distinct one- or two-card selections from the caster's graveyard. Both targets are announced and locked to their object identities before normal `{3}{W}` payment or fixed Sneak `{1}{W}` payment plus a legal unblocked-attacker return. Sneak is available only in its declare-blockers window and follows priority; a countered spell returns nothing. At resolution, every target is checked again. If both are illegal, the entire spell has no effect; if one remains legal, that card returns. All legal targets enter under the caster's control with new object identities before their creature-entry events are processed. State-based actions and triggered abilities follow the represented engine order. Events tie old graveyard identities, new battlefield identities, invalid targets, and the stack source together.

- Six focused tests cover complete and altered Oracle forms, renamed sources, legal single/pair selections, wrong zone/owner/type/value, duplicate and missing targets, payment, normal timing, Sneak priority and source departure, target movement before resolution, partial and full invalidation, new zone identities, state-based actions, countering, invariants, and exact seeded replay. Adjacent Sneak and prior mechanics remain in the full regression.
- [Four authenticated Leonardo/Raphael and Leonardo/April diagnostics](ISSUE_289_GRAVEYARD_RECURSION_SMOKE.json) with balanced first seats at seed 317 matched four exact replays without runtime errors. One normal cast and one Sneak cast resolved, each returning one creature card. The focused fixtures establish the two-target and partial-invalid branches; this tiny natural sample is not a matchup estimate.
- [The complete regenerated overlay](ISSUE_289_GRAVEYARD_RECURSION_CHECKPOINT.json) closes exactly one P0 gap: **6 critical (2 partial) / 61 important → 5 critical (2 partial) / 61 important**. The two Raphael linked permissions remain partial critical blockers.

Original 172-row ledger SHA-256: `56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100`. Previous overlay SHA-256: `70bc2c96ba1f731ef321c173d1a41cd596ee5c330c5afd7e23b17cc9e2dad5ed`. Unchanged Baseline 005 manifest SHA-256: `c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac`. The exact frozen source hashes were checked, allowing only the known Git LF to historical CRLF conversion where needed. Runtime changes from `39f7b510513784981863367bb5a0be0aacb62849b1fd483357e92e08e82b7c8a` to **`2e4135b43d16e587175a96608bf54c723c2d772cf67fe8bd4f4c695393388598`**. Historical controls are incompatible.

Reproduce with `PYTHONPATH=src:tools uv run python tools/report_issue289_graveyard_recursion.py` and `PYTHONPATH=src:tools uv run python tools/run_issue289_graveyard_recursion_smoke.py`. Full local regression: **1,868 passed, 10 skipped in 110.92 seconds**. Baseline 005 structural validation passed; its historical printed land-count prose remains stale while the unchanged manifest and selected deck hashes were independently checked. Repository-wide Ruff check/format, overlay row identities, Markdown evidence links, and diff checks passed. Final-head GitHub CI status is recorded on the draft PR.

**Checkpoint acceptance:** pending final-head CI and independent review. **Baseline 005 calibration readiness:** BLOCKED by five critical entries including two Raphael partial permissions. No control, deck revision, merge, or promotion occurred.
