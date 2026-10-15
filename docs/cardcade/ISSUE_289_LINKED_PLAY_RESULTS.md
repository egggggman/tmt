# Issue #289 — linked-play closure and calibration risk

Stack: draft PR #318 (`2fe1c2be626199ebcba6f21554699c59d240afdb`) → this checkpoint. The original 172-row ledger, every earlier overlay, Baseline 005 deck files, and historical simulation results are unchanged.

## Oracle audit and correction

Wizards' [TMNT release notes](https://magic.wizards.com/en/news/feature/teenage-mutant-ninja-turtles-release-notes) specify that Raphael's play permission follows ordinary card timing, including the available land play, and that a new Raphael object cannot use cards exiled with the former object. The printed attack trigger says “you may play a card exiled with Raphael” until end of turn. The previous runtime selected one specific exiled object as the attack trigger resolved. That made newly linked cards inaccessible and could deny a later legal choice.

The generic linked-play grant now records its creating trigger, source object identity, controller, expiration turn, and one remaining play. A legal card is selected when played. The grant survives source departure, works for a card linked after the attack trigger resolves, consumes exactly once after an authoritative land or spell commitment, and cannot follow the same card through a zone change. Control of the grant, rather than ownership of the exiled card, determines who can spend it.

The legal-action and payment audit found two additional execution gaps: a linked modal instant's chosen mode was lost on the priority path, and fixed Sneak alternative costs from linked exile were not offered during declare blockers. Both now use the existing complete spell semantics, targets, normal mana/restricted-mana planner, stack priority (including an existing spell on the stack), returned-attacker cost, and source provenance. Direct land play is rejected while the stack or priority window is open. There are no new card-name or deck-name execution branches.

The authenticated frozen Raphael deck SHA-256 is `e8d29b97e4fa52bd1a8ae0d8056b5217660b1367e0a386e811908e256dea711f`. Its 22 Mountains use the land path; every one of its 14 distinct nonland cards has a supported cast family. Parametrized focused fixtures exercised linked legal actions and payment for all 14. Additional fixtures cover selection at play time, grants before later exile, two independent grants, source departure, another player's exiled card, modal instant modes, Sneak from exile at empty and nonempty priority windows, land timing, restricted mana, target loss, grant expiry, new zone identities, and exact replays. Unsupported spell effects elsewhere remain unsupported at those cards' own rows; the permission does not fabricate an effect.

## Preserved diagnostic evidence

Six small authenticated Baseline 005 games (Raphael versus Donatello, Casey Jones, and Bebop & Rocksteady, both starting positions, seed 319) completed with six exact deterministic replays and no runtime errors. Two attack-play grants occurred; this limited sample had no natural linked exile or grant use. Focused tests provide execution proof for the branches. See the [machine diagnostic](ISSUE_289_LINKED_PLAY_SMOKE.json). These games are not balance evidence.

The [172-row checkpoint overlay](ISSUE_289_LINKED_PLAY_CHECKPOINT.json) verifies predecessor SHA-256 `358e2a47084f09121a62a63f44ce6256def99b52133645242d2c9d050a8e57c6`, ledger SHA-256 `56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100`, Baseline 005 manifest SHA-256 `c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac`, and the Raphael list SHA before closing the two partial critical rows. Critical: **2 partial → 0**. Important: **56 remain**. The former runtime `7451f647b6d89b6fa6ee83c673aa29f6056cbadfe72f3e90ac9ab93c95299571` changes to `dad44a47bc6db5c5070142d54017c5021f8481106f521e621163ddcddb0e64d8`.

## Important-gap risk and readiness

The separate [machine-readable readiness assessment](ISSUE_289_LINKED_PLAY_CALIBRATION_READINESS.json) ranks **all 56 important rows** by total frozen copies, affected decks, gameplay impact, shared reuse, and implementation complexity. A row remains a blocker if its unexecuted clause drives core identity/resource/combat outcomes or occurs on at least three frozen copies. That identifies **52 blockers**. Four consequential two-copy rows (Bebop, Warthog Warrior; Hamato Guardian Stance; Michelangelo, Improviser; Michelangelo, Mutant BFF) have unbounded exposure and cannot yet be accepted as harmless residuals.

| Shared intervention | Frozen copies / affected decks | Missing outcome | Highest row score |
| --- | ---: | --- | ---: |
| Disappear ETB token and other leave-history triggers, starting with Foot Mystic | 6 / 2 for Foot Mystic | Token board and related leave-history effects | 48 |
| Ninja Teen Class levels and graveyard Sneak | 5 / 2 | Damage, evasion, combat, recursion | 45 |
| Does Machines Class level 3 and artifact animation | 4 / 2 | Counters and artifact combat | 42 |
| Shark Shredder combat-damage recursion | 4 / 2 | Repeated graveyard board development | 42 |
| Leader's Talent Class triggers/levels | 4 / 1 | Counters, life, attack quality | 39 |
| Rocksteady block restriction | 4 / 1 | Bebop & Rocksteady attack outcomes | 36 |
| Ravenous Robots and Mouser Foundry artifact-token triggers | 4 each / 1 each | Casey token board and artifact payoff | 36 each |

The next small shared implementation candidate is generic Disappear leave-history and conditional ETB token creation, with Foot Mystic as a frozen fixture and Putrid Pals, Insectoid Exterminator, and Michelangelo, Game Master as related audit targets. Ninja Teen and other Class levels remain major cross-deck work. Zero critical rows does **not** make the ten-deck simulator ready: too many high-copy cards currently have missing board, combat, and resource behavior.

Local full regression passed: **1,907 passed, 10 skipped** before the final additional generic coverage fixture; that fixture passed in the focused 25-test suite. Baseline 005 structural validation, Ruff check and format, and diff checks passed. Final-head CI supplies the full suite on the published tree. **Checkpoint acceptance: pending final-head CI. Baseline 005 calibration: BLOCKED.** No 4,500-game control, balance experiment, deck revision, merge, or promotion occurred.
