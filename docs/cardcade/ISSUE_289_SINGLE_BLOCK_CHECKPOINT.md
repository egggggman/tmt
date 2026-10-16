# Issue #289: controlled-subtype one-block limit

Parent: validated draft PR #329, remote head `1e606ff7bce903dfd447c882b4a1e6cef7a1e321`. Baseline 005, the 172-row original ledger, and historical evidence remain unchanged. No calibration games were run.

## Choice and scope

| Family | Frozen copies / affected decks | Exact remaining Oracle clauses | Assessment |
| --- | --- | --- | --- |
| Leader's Talent | 4 / Leonardo | `{2}{W}: Level 2`; `{3}{W}: Level 3`; attack counter, creature-departure life, spell-cast team counters | Five connected Class clauses require a larger complete intervention. |
| Rocksteady, Crash Courser | 4 / Bebop & Rocksteady | `Boars you control can't be blocked by more than one creature.` | Selected: bounded static combat rule, current subtype and control, one previously open row. |
| Mutagen Man, Living Ooze | 2 / Bebop & Rocksteady | `Activated abilities of artifact tokens you control cost {1} less to activate.`; `When Mutagen Man enters, create X Mutagen tokens. ...` | Payment-linked variable X and activated-cost modification remain separate complete effects. |

The frozen Rocksteady also reads `Rocksteady can't be blocked by more than one creature.` Its self restriction was already classified as covered, but the old generic string check actually rejected **one** blocker as well as two. This checkpoint corrects that existing execution defect; it does not count the self row as a new closure. The general combat restriction is evaluated when blockers are declared, as required by the [Magic Comprehensive Rules](https://media.wizards.com/2026/downloads/MagicCompRules%2020260619.pdf).

## Runtime and tests

`CardInterpreter.single_block_limit` recognizes the full self or regular plural controlled-subtype Oracle clause. The combat legality evaluator uses current authoritative battlefield objects, controller, evaluated creature subtype, and source abilities. It accepts zero or one blocker and rejects two or more; Menace combined with the limit makes declaration impossible. `execute_block_action` revalidates the choice and records the source ID, attacker ID, clause, controller, and selected blocker count. The static effect has no activation, payment, trigger or stack object; subsequent removal of the source cannot undo an already declared block.

Focused tests cover renamed fixtures, incomplete-clause rejection, self and team limits, single versus multiple blockers, non-Boars, source departure before and after block declaration, controller and subtype changes, ability loss, Menace, combat damage, state-based actions, and deterministic replay. The prior Shark Shredder first-strike return, granted Sneak and Robot-token regressions remain in the full suite. Full regression: **1,979 passed, 10 skipped**. Ruff check and format, Baseline 005 structural validation, and diff check passed.

Six authenticated frozen-deck diagnostics and six deterministic replays matched with zero errors. Two Rocksteady casts produced ten block-limit evaluations, five affecting other controlled Boars. Three selected single-block assignments occurred. The first four games had no Rocksteady cast; seed 349 in both starting positions supplies the execution witness. See [machine diagnostic evidence](ISSUE_289_SINGLE_BLOCK_SMOKE.json). These games measure engine and pilot use, not balance.

## Coverage and gates

Semantic runtime: `32dbafe9f3ef612ed49b988ca447af9e85264589574ad635b6c96e30f864e346`. Original ledger SHA-256: `56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100`. Predecessor overlay SHA-256: `f8af6fd18d89d712c9ec61f2f2e29c0730a5b5385943424c6c545fe6d92685aa`.

The [new complete overlay](ISSUE_289_SINGLE_BLOCK_CHECKPOINT.json) closes the one Rocksteady team row and separately records the existing self-row correction: **0 critical, 30 important, 26 calibration blockers, 4 unbounded important**. The [independent readiness report](ISSUE_289_SINGLE_BLOCK_CALIBRATION_READINESS.json) ranks all 30 remaining rows and retains the same four unbounded effects. Leader's Talent, Splinter's tribal combat modifier, Ice Cream Kitty's resource abilities, Donatello's artifact counters and Mutagen Man remain prominent.

- **Checkpoint acceptance: READY** for independent review, pending final-head CI.
- **Baseline 005 calibration readiness: BLOCKED.** Twenty-six important gameplay blockers and four unbounded effects still prevent a trustworthy 4,500-game reference.

No deck revision, historical-game overwrite, merge or promotion was performed.
