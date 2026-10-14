# Issue 289: optional bilateral hand reset

This checkpoint stacks on draft PR #314. It preserves all ten Baseline 005 lists, the original 172-row ledger, previous overlays, and historical simulation evidence. Four small games below diagnose execution and replay only; they are not balance estimates.

## Critical-family ranking and selection

Frozen copies count cards; rows count preserved Oracle fragments. The Last Ronin's Technique has one frozen copy represented by two original critical rows.

| Family | Copies / critical rows | Deck-identity effect | Reuse and implementation scope |
| --- | ---: | --- | --- |
| Raphael linked exile/play | 2 / 2 partial | High: stored card access and attack-time play | Linked permission across card types and timing remains broad. |
| Leonardo graveyard recursion | 2 / 1 | High: board recovery | Two possible graveyard targets, Sneak, and entry timing add target work. |
| Raphael bilateral hand reset | 2 / 1 | High: full resource reset for both players | **Selected:** existing discard, draw, priority, and fixed Sneak primitives allow one complete shared rule family. |
| Michelangelo top-eight selection | 2 / 1 | High: two creature entries | Coupled hidden selections and combined mana-value cap add complexity. |
| Last Ronin attacking tokens | 1 / 2 | High: conditional combat pressure | Tapped-and-attacking entry and defending-player provenance require distinct combat rules. |

The complete frozen instant says “Each player may discard their hand and draw seven cards.” It has a printed fixed Sneak alternative cost. The interpreter recognizes the complete instant or sorcery sentence and exact fixed Sneak preface, derives the draw quantity from text, and rejects an altered or additional instruction. A renamed fixture executes identically. There is no source-card or deck-name execution branch.

## Resolution and validation

Normal payment is `{4}{R}{R}` at instant priority; Sneak pays `{2}{R}` and returns a legal unblocked attacker in the declare-blockers window. The spell enters the stack and may be responded to or countered. On resolution, each player privately decides in active-player/nonactive-player order **before any hand changes**. All consenting players discard their entire current hands before the active player and then the nonactive player draw the printed number, one card at a time. A declining player's hand and library stay intact. The resolution event ties the stack object to decisions, old and new discard identities, new hand identities, and draw results. An invalid or impure choice fails before a discard or draw. When both libraries are empty and both players choose to draw, the generic failed-draw state action now records a simultaneous terminal draw instead of arbitrarily assigning a winner.

- Nine focused tests cover complete renamed and incomplete Oracle forms, normal/Sneak costs, legal and illegal priority/targets/payment, independent accept/decline, APNAP choice and movement order, source departure, invalid/impure choices, countering, simultaneous failed draws, invariant checks, and exact seeded replay. Adjacent Sneak and shared-removal tests pass.
- [Four frozen Raphael/Splinter and Raphael/April diagnostics](ISSUE_289_HAND_RESET_SMOKE.json) with balanced first seats at seed 314 matched four exact replays and had no runtime error. One normal cast resolved; both players accepted, two cards were discarded, and 14 cards were drawn. The Sneak branch and a decline are demonstrated by deterministic focused fixtures, not by this tiny natural-game sample.
- [The regenerated complete overlay](ISSUE_289_HAND_RESET_CHECKPOINT.json) closes exactly the one Raphael's Technique P0 gap. **7 critical (2 partial) / 61 important → 6 critical (2 partial) / 61 important**. Raphael's two linked-play partial rows remain critical blockers.

Original 172-row ledger SHA-256: `56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100`. Previous overlay SHA-256: `fd9d7d490c019d42438ae57d5e3917b9d2bd582bf540dcd89d926d36ebe3fe11`. Unchanged Baseline 005 manifest SHA-256: `c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac`. The two historical prototype sources whose manifest hashes use CRLF were authenticated through exact LF-to-CRLF conversion; no deck changed. Semantic runtime moves from `d41b7310e12992ad4cf2052e7803968d9bea8a083ae4461ba3dae89d8a735986` to **`39f7b510513784981863367bb5a0be0aacb62849b1fd483357e92e08e82b7c8a`**. Historical controls are incompatible.

Reproduce with `PYTHONPATH=src:tools uv run python tools/report_issue289_hand_reset.py` and `PYTHONPATH=src:tools uv run python tools/run_issue289_hand_reset_smoke.py`. Full local regression: **1,862 passed, 10 skipped in 103.71 seconds**. The Baseline 005 structural validator, repository-wide Ruff check/format, exact overlay identity audit, links, and diff check passed. The structural validator's historical printed land-count prose remains stale; the unchanged manifest and selected deck hashes were checked separately. Final-head GitHub CI status is recorded on the draft PR.

**Checkpoint acceptance:** pending final-head CI and independent review. **Baseline 005 calibration readiness:** BLOCKED by six critical rows including two Raphael partial permissions. No control, deck revision, merge, or promotion occurred.
