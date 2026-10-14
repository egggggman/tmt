# Issue 289: complete two-mode token and creature-pump spell

This checkpoint stacks on draft PR #309. The ten Baseline 005 decks, original 172-row ledger, prior overlays, and historical simulation evidence remain unchanged. The frozen-deck games below are diagnostics, not balance estimates.

## Selection

| Family | Frozen copies / critical rows | Assessment |
| --- | ---: | --- |
| Mouser Attack! | 3 / 2 | Flexible board development and combat pressure. Existing token creation, temporary P/T, and first/double-strike evaluation permit one complete two-mode cast path. **Selected.** |
| Saved by the Shell | 3 / 3 | The conditional generic discount is partly executable; the counter, trample, hexproof, and indestructible must be delivered as one complete targeted spell. Critical rows remain. |
| Mind Transfer Protocol | 3 / 2 | Temporary type change, base P/T setting, and draw need coupled resolution and layer/duration handling. Critical rows remain. |
| Linked play, recursion, library selection, hand reset, and attacking tokens | 1–2 copies each | Distinct general rules families remain critical. |

The full [previous assessment](ISSUE_289_ETB_CREATURE_DESTROY_RESULTS.md) and [machine overlay](ISSUE_289_MODAL_SPELL_CHECKPOINT.json) preserve the selection and all remaining rows.

## Rules and evidence

The interpreter accepts a complete two-mode instant or sorcery only when both a fixed creature-token creation instruction and a targeted temporary P/T plus first/double-strike instruction are parseable. It rejects extra instructions, unknown keywords, and incomplete modes as unsupported. There is no card-name or deck-name execution branch. The engine exposes a token action without a target and a separate pump action for each legally targetable creature. A mode and target are chosen before payment, preserved on the ordinary stack, and rechecked at resolution. An illegal pump target causes the entire spell to resolve without an effect; it never switches to token creation. The token mode uses the existing token-entry event path with its stack source ID. The pump mode uses existing temporary P/T and combat keyword effects, state-based actions, and end-of-turn cleanup.

- Seven focused tests cover the frozen Oracle fixture and renamed source, incomplete modes, target protection and source types, legal-action generation, pre-payment rejection, priority, countered spell/source departure, target zone/type/hexproof changes, stack and token provenance, first-strike combat, cleanup, invariants, and identical replay snapshots. Existing token and strike coverage membership tests now include the newly supported clause.
- Four mirrored Baseline 005 Raphael/Casey and Raphael/Leonardo diagnostic games matched four deterministic replays without errors. Their deck files match the preserved Baseline 005 manifest. They recorded **four frozen-source casts, four mode selections, and four token-mode resolutions**. The [machine diagnostics](ISSUE_289_MODAL_SPELL_SMOKE.json) preserve game digests and exact stack/token IDs. These games do not exercise the pump mode; the focused deterministic tests do. No win-rate inference is made.
- The original ledger SHA-256 remains `56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100`; the #309 overlay SHA-256 remains `b3d8e15c4609f3bb94801f723c1dc6c3cd4b159dc9566fddb9098a6df0fca0fe`. Exactly two Mouser clause rows change: **16 critical / 61 important / 3 partial → 14 critical / 61 important / 3 partial**; all 172 original row identities are preserved. The annotation header remains an annotation.
- Semantic runtime changes from `fb7dab9e04fe1b138c5bb1560cc7d0026d289d8cbe5ca7a7890e12ad69346476` to `82e98882e36523ade85ee4261a8f0f7675bef98fa50ac4d96d43469d6f2fcf77`. Historical Baseline 005 controls are not runtime compatible. The frozen Baseline 005 manifest remains `c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac`.
- Final-source regression: **1,815 passed, 10 skipped**. Baseline 005 structural validation, repository-wide Ruff check/format, exact row-change audit, deterministic diagnostics, and diff check passed. The structural validator prints historical land-count prose; its authenticated manifest/deck checks pass.

**Checkpoint acceptance:** READY for independent review after final-head GitHub CI is green. **Baseline 005 calibration readiness:** BLOCKED. No 4,500-game control, deck revision, automatic merge, or promotion occurred.
