# Issue 289: granted combat trigger and optional Equipment attachment

This checkpoint stacks on draft PR #306. The ten frozen Baseline 005 lists, the original 172-row coverage ledger, all earlier overlays, and historical games remain unchanged. The five games below are diagnostics only.

## Selection

| Remaining family | Frozen copies / deck | Impact and implementation scope | Decision |
| --- | --- | --- | --- |
| Quintessential Katana, granted combat trigger | 2 / Leonardo | Its +1/+1 and combat-damage untap/life gain change combat and racing. Reuses Equipment attachment, static P/T, combat-damage events, and triggered-ability priority. | Implemented complete printed clause, for damage to a player **or creature**. |
| Quintessential Katana, optional Ninja-entry attachment | 2 / Leonardo | Changes attachment and P/T at instant-speed trigger resolution. Generic subtype matching and non-targeted optional choice suffice. | Implemented complete printed clause. |
| Remaining modal, recursion, and resource families | Several decks | Larger parsing, choices, costs, and zone changes; separate semantic interventions are needed. | Retained as distinct gaps. |

The interpreter recognizes arbitrary Equipment with the printed granted +P/+T combat-damage untap/life-gain shape and arbitrary creature subtype entry attachment. Engine execution has no Katana, Leonardo, or opponent name branch. An attached Equipment grants a trigger to its creature for every positive combat-damage assignment to a creature or player. The trigger source is that creature, with separate grant-source provenance for the Equipment. Priority puts the trigger on the stack after damage. At resolution, it untaps the same creature incarnation if still present; the controller at damage time gains life even if the creature or Equipment departed. It neither retargets nor loses its independent stack existence after departure.

The optional entry trigger observes a controlled subtype creature entering while the Equipment is present. The decision is made at resolution, so the pilot can decline. The entrant is an untargeted recipient. Attachment is legal only while the Equipment and entrant retain their battlefield identities; a changed or absent object cannot be attached. The existing static P/T layer recalculates when attachment changes or leaves.

## Evidence and gates

- Focused synthetic fixtures rename the creature subtype and Equipment. They verify frozen Oracle recognition, +1/+1 attachment recalculation, accepting and declining attachment, recipient and Equipment departure, blocking and damage to a creature, player combat damage, double strike's two damage steps, stack timing, untap, life gain, and equal replay snapshots. The new regression would catch the initial player-only implementation.
- The historical acceptance launcher used a combat loop that skipped priority after damage. In the current runtime, an attached Katana granted a blocked April a creature-damage trigger and the launcher tried to resolve the same damage step twice. The launcher now drains ordinary priority after each damage step using its existing pilot chooser; its original seed and pilot stage schedule remain. The earlier acceptance evidence files are untouched.
- Five frozen Leonardo/Raphael and Leonardo/Shredder diagnostic games matched five deterministic replays with zero runtime errors. A bounded targeted seed records **45 optional attachment resolutions and 6 granted combat trigger resolutions**; event/stack IDs, grant source, recipient, life and untap outcomes, and per-game digests are in [machine diagnostics](ISSUE_289_KATANA_SMOKE.json). This small sample supports execution and replay, not win-rate conclusions.
- The original 172-row ledger SHA-256 is `56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100`; the #306 overlay SHA-256 is `5c73b50eeaf81ccdd0d0c95e4818fdca73a08aa6b9f5e9900ecea5916ff2595c`. The [complete new overlay](ISSUE_289_KATANA_CHECKPOINT.json) changes exactly two Katana rows: **19 critical / 62 important / 3 partial → 18 critical / 61 important / 3 partial**. It preserves all 172 row identities.
- Semantic runtime changes from `ceb2b145af1728abad173ab378627b23e58f28f76659e70bdeae27e6a0fdb0a6` to `289ce95d8282e2ee33b1ffb468c117a7620dea7127609dcfe9ebc993cb5ea8a3`. Historical Baseline 005 controls are not runtime compatible. The Baseline 005 manifest remains `c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac`.
- Full regression: **1,798 passed, 10 skipped**. Baseline 005 structural validation, repository-wide Ruff check and format, Markdown relative-link validation, JSON/runtime consistency, and diff check passed. The structural validator still prints historical incorrect land-count prose, while its authenticated manifest and deck checks pass.

**Checkpoint acceptance:** READY for independent review once final-head GitHub CI is green. **Baseline 005 calibration readiness:** BLOCKED with 18 critical, 61 important, and 3 partial rows still open. No calibration control, deck revision, merge, or promotion occurred.
