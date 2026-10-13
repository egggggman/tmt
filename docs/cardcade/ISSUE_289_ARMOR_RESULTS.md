# Issue 289: generic Equipment entry and sacrifice equip

This checkpoint is stacked on draft PR #305. It changes engine semantics only. Baseline 005 deck lists, the original 172-row coverage ledger, prior checkpoints, and historical games remain unchanged. Diagnostic games here are not balance evidence.

## Selection

| Frozen Equipment | Copies / deck | Combat impact | Reusable work and complexity | Decision |
| --- | --- | --- | --- | --- |
| Shredder's Armor | 4 / Shredder | Immediate +2/+1 attachment; alternative equip cost changes board and combat | Generic targeted Equipment entry trigger; sacrifice another controlled nonland permanent; per-incarnation once-per-turn history. Existing +2/+1 layer and attachment rules apply. | **Implemented both remaining clauses** |
| Quintessential Katana | 2 / Leonardo | +1/+1 plus granted combat-damage untap and life; optional Ninja-entry attachment | Requires a granted combat-damage trigger with combat-step timing and a separate optional subtype-triggered attachment. | Remains open as two distinct clauses |

The interpreter recognizes the printed shapes without checking names. Entry chooses a legal controlled creature when the trigger goes on the stack and verifies that target on resolution. Source departure, target departure, or a control change prevents attachment. The existing attachment and continuous P/T layer remove the bonus when the attachment ceases. The alternative equip cost is chosen from legal controlled nonland permanents in the action, paid by authoritative zone movement, and logged with source, sacrificed object, destination, and stack IDs. Its once-per-turn marker belongs to the permanent incarnation and Oracle fragment. Equip remains sorcery speed and resolves through the ordinary targeted activated-ability stack.

## Evidence and gates

- Focused tests use renamed Equipment, legal and illegal cost choices, land/opposing/source rejection, legal targeting, once-per-turn timing, target and source departure, payment, trigger stack resolution, attachment cleanup, and snapshot-equal replays. Existing Equipment combat/P/T and attachment tests pass.
- Four mirrored frozen Shredder/Raphael and Shredder/Leonardo diagnostic games at seed `3061` each matched a deterministic replay with zero runtime errors. They recorded three successful entry attachments and eleven nonland sacrifice equip payments. Per-game digests and event IDs are preserved in [machine diagnostic](ISSUE_289_ARMOR_SMOKE.json).
- The original ledger SHA-256 is `56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100`; the #305 overlay SHA-256 is `f7ab8aba792dcf82ec787706bc13696fe504bb6c18c8bdba79200f6e051de490`. The [complete new overlay](ISSUE_289_ARMOR_CHECKPOINT.json) changes exactly the two Armor rows: **20 critical / 63 important / 3 partial → 19 critical / 62 important / 3 partial**. Katana's two rows remain gaps.
- Runtime changes from `d27c9c8f7aeb82a3311b6cc72586b6a5103c0f8ce333588fe13c41812e6c7e2d` to `ceb2b145af1728abad173ab378627b23e58f28f76659e70bdeae27e6a0fdb0a6`. Historical Baseline 005 controls are not runtime compatible.
- Full regression: **1,792 passed, 10 skipped**. Baseline 005 structural validation, Ruff check and format of changed Python files, and diff check passed. The activation-catalog membership lock now includes the new executable Armor fragment and preserves its former digest in source. The structural validator prints historical land-count prose; its authenticated manifest and deck checks passed.

**Checkpoint acceptance:** READY for independent HQ review once final-head GitHub CI is green. **Baseline 005 calibration readiness:** BLOCKED with 19 critical, 62 important, and 3 partial rows still open. No calibration control, deck revision, merge, or baseline promotion occurred.
