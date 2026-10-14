# Issue 289: unrestricted library search to hand

This checkpoint stacks on draft PR #313. It preserves the ten frozen Baseline 005 lists, the original 172-row ledger, every earlier checkpoint, and historical game evidence. Four small games below diagnose execution and deterministic replay; they do not estimate balance.

## Critical-family selection

Frozen copies count cards; rows count distinct preserved Oracle fragments. The last row pair repeats one card's payload and retains both ledger identities.

| Family | Frozen copies / critical rows | Gameplay consequence | Scope and decision |
| --- | ---: | --- | --- |
| Raphael linked exile/play | 2 / 2 partial | Deck-defining card access and permission duration | High impact; remaining castable families and linked-zone permissions require broader closure. |
| Graveyard recursion | 2 / 1 | Leonardo board recovery | Sneak and multiple graveyard targets add target and entry timing work. |
| Unrestricted library search | 2 / 1 | Splinter access to any resource or answer | **Selected:** private choice, normal movement, shuffle, stack, and fixed Sneak payment primitives already exist. |
| Top-eight creature selection | 2 / 1 | Michelangelo can put two creatures into play | Multiple hidden-zone selections and a combined mana-value cap add coupled choices. |
| Bilateral hand reset | 2 / 1 | Raphael resource reset for each player | Both players' choices and simultaneous draw ordering add scope. |
| Attacking token creation | 1 / 2 | Last Ronin combat pressure | Requires conditional tapped-and-attacking entries and Sneak context. |

The complete printed search effect is “Search your library for a card, put that card into your hand, then shuffle.” The spell also has a fixed Sneak alternative cost. The interpreter recognizes the entire instant or sorcery payload and complete Sneak preface, including the identical printed alternative cost and unblocked-attacker return condition. A renamed fixture executes the same way. Any added instruction or altered search restriction is rejected as unsupported rather than partially executed. There is no card-name or deck-name execution branch.

## Execution and evidence

The spell can be announced with normal mana in the main phase or with the existing Sneak alternative cost in the declare-blockers priority window. Its controller privately selects one card from their library during resolution (or none if empty), moves it to hand with a new zone identity, then deterministically shuffles the remaining library. The choice is made after the stack resolves, so a countered spell has no search. Search resolution uses its stack object as provenance even if the original source moved; event evidence records both old and new object IDs and the pre/post shuffle IDs. The chooser cannot invoke authoritative zone movement, and invalid choices fail before selection movement. A generic pilot policy values a needed land or a castable nonland using its own board and hand, with no named-card preference.

- Eight focused tests cover complete parsing, renamed and incomplete Oracle fixtures, normal payment, legal timing, missing payment, target rejection, hidden selection, zone identity, shuffle, empty library, invalid and impure choices, Sneak priority and payment, source independence, countered resolution, state invariants, and exact seeded replay. Adjacent Sneak tests pass.
- [Four authenticated Splinter/Raphael and Splinter/April diagnostics](ISSUE_289_LIBRARY_SEARCH_SMOKE.json), with both starting positions at seed 313, matched **four exact replays** without runtime error. They record **three normal payments, five Sneak payments, eight private searches, eight hand movements, and eight deterministic shuffles**. This tiny sample is only an execution check.
- [The regenerated 172-row overlay](ISSUE_289_LIBRARY_SEARCH_CHECKPOINT.json) closes exactly one gap/P0 row. Coverage changes **8 critical (including 2 partial) / 61 important → 7 critical (including 2 partial) / 61 important**. The two Raphael partial rows remain critical blockers. The overlay preserves all original row identities and predecessor classifications.

Splinter's historical manifest hash was recorded from CRLF bytes (`74b6d7f4cab4bcda9eeb80ffc7a779529115c98c161345f13ac1251d85163b0a`); Git checks out that prototype with LF bytes (`a6c61786654f6d37c7b7ee779fdcb4252ee77d9d43a6e0160154831c204d8e42`). Restoring CRLF alone reproduces the exact manifest hash. Michelangelo has the same historical line-ending convention. The diagnostic accepts only the raw manifest hash or that precise newline conversion, and changes no deck source.

Original ledger SHA-256: `56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100`. Predecessor overlay SHA-256: `d555ddf265d17fa9a29799aef71a962a75fe071ceb030e666e1b6806998832a2`. Unchanged Baseline 005 manifest SHA-256: `c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac`. Semantic runtime changes from `3ba2f858ffa06a24322f98dc2e0da218d53967fee6b385ef8cd1a252e6ad5fc0` to **`d41b7310e12992ad4cf2052e7803968d9bea8a083ae4461ba3dae89d8a735986`**. Historical controls are incompatible with this runtime.

Reproduce with `PYTHONPATH=src:tools uv run python tools/report_issue289_library_search.py` and `PYTHONPATH=src:tools uv run python tools/run_issue289_library_search_smoke.py`. Full regression: **1,853 passed, 10 skipped in 102.13 seconds**. Baseline 005 structural validation passed; its historical printed land-count message remains stale, while the manifest and deck hashes were verified separately. Ruff check/format and diff checks passed. Final-head GitHub CI status is recorded on the draft PR.

**Checkpoint acceptance:** pending final-head CI and independent review. **Baseline 005 calibration readiness:** BLOCKED by seven critical entries, including Raphael's two partial permissions. No control, deck revision, merge, or promotion occurred.
