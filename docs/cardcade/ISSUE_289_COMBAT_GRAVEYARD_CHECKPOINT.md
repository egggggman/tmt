# Issue #289: combat damage graveyard return checkpoint

Parent: validated draft PR #328 (remote head `3d0eb5a60dc871aa31c86132b73567a463bcd5ae`). Baseline 005 is unchanged. This checkpoint runs no calibration games.

## Selection

| Family | Frozen copies / decks | Remaining Oracle behavior | Decision |
| --- | --- | --- | --- |
| Shark Shredder combat recursion | 4 / Shredder, Splinter | On combat damage to a player, target up to one creature card in that player's graveyard; put it under the trigger controller's control tapped and attacking that player | Selected: common combat event, target and zone machinery; immediate board and damage effects in two decks |
| Leader's Talent | 4 / Leonardo | Five linked Class level, counter, cast, attack, and departure clauses | Retain as one larger Class family; partial levels must not masquerade as complete support |
| Rocksteady blocking restriction | 4 / Bebop & Rocksteady | Boars controlled by the source's controller cannot be blocked by more than one creature | Next bounded combat candidate, one deck |
| Mutagen Man X token engine | 2 / Bebop & Rocksteady | X Mutagen tokens on entry and discount of controlled artifact token abilities | Retain: variable payment and cost modification are separate complete clauses |

The card's exact frozen Oracle fragment is in the two rows of the [172-row overlay](ISSUE_289_COMBAT_GRAVEYARD_CHECKPOINT.json). The [official TMNT release notes](https://magic.wizards.com/en/news/feature/teenage-mutant-ninja-turtles-release-notes) clarify that a creature returned after first strike damage can deal damage in the regular step, even if it has first strike, and that a return after regular damage deals no damage that combat. The generic combat eligibility rule was corrected accordingly.

## Execution and evidence

The interpreter recognizes the complete self combat-damage clause, including its optional target and tapped attacking modifier; incomplete variants remain unsupported. A positive, authenticated player damage event creates a source-independent trigger. Target selection occurs when the trigger is stacked, after damage state based actions. The opponent's graveyard card must still be the same legal incarnation at resolution. A valid target changes zone and controller, enters tapped attacking the damaged player, generates normal creature-entry events, and is checked for state based actions. A moved target fizzles; an empty graveyard permits the zero-target branch. Creature damage creates no such trigger. The deterministic pilot chooses the highest printed power legal target, breaking ties by object ID.

The focused regression covers renamed Oracle fixtures, complete parsing, damage to creatures versus players, first strike and double strike return timing, invalidated targets, source departure, optional zero target, immediate zero-toughness death, regular-step return, trigger provenance and replay. The four authenticated frozen-deck diagnostics under semantic runtime `af65d73156dad43e969c5f00b52a37915f4aaa0f47ff117b76f2a129f0e3d84d` produced three casts, three player damage triggers and three tapped attacking entries. All four replays matched and had zero errors. See [diagnostic evidence](ISSUE_289_COMBAT_GRAVEYARD_SMOKE.json). These games are mechanics diagnostics, not balance estimates.

Full regression: **1,969 passed, 10 skipped**. Ruff check and format, Baseline 005 structural validation, diff check, and the focused tests passed. The structural validator still emits inherited `24 -> 22 total lands` prose; authenticated Baseline 005 deck hashes and lists remain unchanged.

## Coverage and gates

The original 172-row ledger SHA-256 remains `56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100`. The predecessor overlay SHA-256 is `3604f80d3893b199d067a66b866d852adc5eb914c7b5244a0e92f5b7513ea360`. The new overlay closes only the two Shark Shredder rows: **0 critical, 31 important, 27 calibration blockers, 4 unbounded important**. Full rankings and the unchanged four unbounded rows are in the [separate readiness report](ISSUE_289_COMBAT_GRAVEYARD_CALIBRATION_READINESS.json). Class levels, Rocksteady's blocking restriction, and artifact-token cost and X creation remain high-impact priorities; no reclassification of older evidence was used to inflate closure.

- **Checkpoint acceptance: READY** for independent PR review, subject to final-head CI.
- **Baseline 005 calibration readiness: BLOCKED.** The 27 remaining gameplay blockers and four unbounded residuals preclude an unchanged 4,500-game control.

No deck list, historical game artifact, earlier overlay, or previous runtime identity was modified.
