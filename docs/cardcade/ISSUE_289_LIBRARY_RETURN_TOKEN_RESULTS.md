# Issue 289: targeted library return and token creation

This checkpoint stacks on draft PR #312. It changes no Baseline 005 deck, the original 172-row ledger, any earlier coverage overlay, or historical game evidence. The small games below test execution and replay only; they are not balance estimates.

## Critical-family selection

Frozen copies count cards, while rows count Oracle fragments. The two Last Ronin rows repeat one card's payload in the preserved ledger and remain distinct row identities.

| Family | Frozen copies / critical rows | Consequence and reuse | Implementation assessment |
| --- | ---: | --- | --- |
| Raphael linked exile/play | 2 / 2 partial | Identity-defining card access, duration and casting permissions | High impact, broad linked-zone and timing scope; remains partial. |
| Graveyard return, Leonardo's Technique | 2 / 1 | Board recursion and one-or-two graveyard targets | High impact; Sneak, target selection and multi-entry timing add scope. |
| Library search, Splinter's Technique | 2 / 1 | Any-card tutoring, shuffle and hidden choice | High resource impact; Sneak and private selection require a new family. |
| Top-eight selection, Michelangelo's Technique | 2 / 1 | Up to two free creature entries with combined mana-value limit | High impact and several coupled choices/zone moves. |
| Hand reset, Raphael's Technique | 2 / 1 | Each player separately decides to discard and draw seven | High resource impact; Sneak and simultaneous choice/draw ordering add scope. |
| Targeted return plus artifact token | 2 April / 1 | Full creature removal, owner top/bottom choice, then Mutagen resource | **Selected:** existing target, owner-zone, token, Mutagen, stack and payment primitives permit one complete general family. |
| Attacking token creation, The Last Ronin's Technique | 1 / 2 | Three tokens and conditional tapped-attacking entries | Combat-dependent entries and Sneak context add scope. |

The printed `{3}{U}` instant says: “Target creature's owner puts it on their choice of the top or bottom of their library. You create a Mutagen token.” Its reminder specifies an artifact token with the already executable counter activation. The new parser recognizes that complete form for any matching instant or sorcery, including a renamed fixture. It rejects added unsupported instructions, missing choice, and altered token follow-up rather than executing a partial spell. No source card or deck name determines execution.

## Execution and provenance

The caster selects a legally targetable creature and pays `{3}{U}` under ordinary announcement and priority. Target identity and current creature/protection legality are checked again on resolution; an illegal target causes the entire spell to have no effect, including token creation. On a legal target, its **owner** chooses top or bottom at resolution; the card enters its owner's library with a new object identity, even if someone else controlled it. The caster then creates the complete artifact token, and normal entry triggers and state-based actions follow. The resolution event ties the stack object, old target, new library object, owner's choice, and token object together. Normal transitions are prohibited while the chooser is running. The token's generic `{1}, {T}, Sacrifice` counter ability remains executable.

- Eight focused tests cover a renamed source, incomplete clauses, legal and illegal targets, insufficient mana, instant priority, both owner choices, a stolen creature, target departure and type loss, no-token fizzle, invalid or impure choices, token ability coverage, zone provenance, invariants and exact seeded replay. Adjacent token and animation tests pass.
- [Six frozen April/Raphael and April/Donatello diagnostics](ISSUE_289_LIBRARY_RETURN_TOKEN_SMOKE.json) matched six exact replays without runtime error. They recorded **three casts, three `{3}{U}` payments, three target-to-owner-library movements, and three complete token resolutions**. The sample is deliberately too small for a win-rate inference. Both owner choices are demonstrated in focused fixtures; the default deterministic pilot chose top in these three resolutions.
- [The regenerated overlay](ISSUE_289_LIBRARY_RETURN_TOKEN_CHECKPOINT.json) preserves all 172 row identities and closes exactly one gap/P0 row. Coverage changes **9 critical / 61 important / 2 partial → 8 critical / 61 important / 2 partial**. The two Raphael partial rows remain explicit critical blockers.

Original ledger SHA-256: `56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100`. Previous overlay SHA-256: `d58dffb2f61b1556cd294fcd30316aaaf1d372099ca8134353a32b207ee2e382`. Unchanged Baseline 005 manifest SHA-256: `c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac`. Runtime changes from `60bcdf05b99454f1e69015652c603f744c0df9a91e8dc83f0eb8fbb3128ebf1a` to `3ba2f858ffa06a24322f98dc2e0da218d53967fee6b385ef8cd1a252e6ad5fc0`; historical controls are incompatible.

Reproduce with `PYTHONPATH=src:tools python tools/report_issue289_library_return_token.py` and `PYTHONPATH=src:tools python tools/run_issue289_library_return_token_smoke.py`. Full regression and final-head CI results are recorded in the draft PR after completion. The Baseline 005 structural validator passed; its historical printed land-count prose remains stale, while the manifest and authenticated deck checks passed. Ruff check/format and unchanged-deck/ledger hashes passed.

**Checkpoint acceptance:** pending final-head CI and independent review. **Baseline 005 calibration readiness:** BLOCKED by eight critical entries. No control, deck revision, merge, or promotion occurred.
