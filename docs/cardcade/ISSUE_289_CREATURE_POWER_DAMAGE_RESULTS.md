# Issue 289: Creature-power damage checkpoint

Stacked on draft PR #303 (`60b21f2327648d8be046ee72fd9c4aa215484d42`). No frozen deck or historical evidence was edited. This is an engine checkpoint, not balance calibration.

## Selection

| Family | Frozen copies / decks | Gameplay consequence | Reuse and scope | Risk |
| --- | --- | --- | --- | --- |
| Creature-power damage (Tenderize) | 3 / Michelangelo | Instant removal and combat response; source power can change before resolution | One general two-target, creature-sourced damage rule also applies to the damage clause of Super Combo, whose separate Replicate remains unsupported | Lower: existing mana, stack, damage, and state-based-action paths |
| Remaining Equipment (Quintessential Katana, Shredder's Armor, Improvised Arsenal) | 9 / Leonardo, Shredder, Casey Jones | Combat stat, untap/life, attack/block decisions, attachment, and equip costs | Several different rules: combat-damage trigger; enter/attach; sacrifice equip once per turn; artifact-count power; copy token and equip activation | Higher: distinct timing, attachment, payment, and continuous-effect families |

Tenderize is the smallest complete, consequential intervention. The nine Equipment copies merit the next review, especially the three P0 clauses, but implementing one of them would not close the others. Super Combo's Replicate clause is not credited as supported merely because its identical damage sentence is recognized.

## Implemented semantics

The interpreter requires an entire Instant or Sorcery text consisting of the two-target Oracle sentence. Both targets must be legal on announcement: a creature controlled by the caster and a creature controlled by the opponent. Mana is paid normally; the instant is available at priority, while a sorcery can be cast at normal main-phase timing. The source creature remains the damage source. At resolution the engine rechecks both targets, reads the source's *current* power, applies noncombat damage through the existing typed transaction, evaluates relevant damage-source keywords, and performs state-based actions. If either target becomes illegal, no damage occurs; if both become illegal, the spell has no effect. Zero power also deals no damage. Target identities, damage amount, event ID, and source are logged.

The public-state pilot can choose a lethal opposing target using the existing action choice tuple; the sealed `ActionOption` schema remains unchanged. Execution is based on Oracle grammar and legal state, without Tenderize, deck, or opponent dispatch.

## Validation and provenance

- Ten focused fixtures cover frozen Oracle identity, renamed synthetic cards, insufficient mana with no mutation, target pairs and protection, priority versus sorcery timing, paid announcement, dynamic power at resolution, zero power, source or target departure, controller change, lifelink and deathtouch damage, state-based death, and exact deterministic replay. The damage catalog's locked payload and full-support digests were refreshed; Super Combo retains a parent limitation for its unimplemented Replicate clause.
- Full local regression on final semantic code: **1,779 passed, 10 skipped in 96.64 seconds**. Ruff check and format, `git diff --check`, and Baseline 005 structural validation passed. The structural validator's old printed land-count summary is historical prose; no list was changed here.
- Four mirrored frozen Michelangelo/Raphael and Michelangelo/Leonardo diagnostics at seed `3035`: four deterministic replays matched, zero runtime errors, and four actual creature-power damage resolutions. Per-game stable digests and target/source/damage provenance are in `ISSUE_289_CREATURE_POWER_DAMAGE_SMOKE.json`. These are diagnostics, not win-rate or balance data.
- Seed `3032` in Michelangelo-first versus Raphael exposed an Alliance temporary-keyword provenance invariant failure. Repeating exactly that seed on untouched #303 reproduced the same failure, before this change. The diagnostic evidence uses seed `3035`, which exercises this new rule. The pre-existing failure remains an engine-readiness concern; it has not been silently attributed to the damage implementation.
- The original 172-row ledger remains SHA-256 `56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100`; #303's checkpoint remains `27c66e3db22fb8b4968165e59626b088fdab036980c1511e1401737be4d4e13b`. The new machine overlay changes only the Tenderize P0 gap to supported. Counts move **22 critical / 64 important / 3 partial → 21 critical / 64 important / 3 partial**.
- Semantic runtime changes from `7ca337922f33feeaf8371f15eb5813ade5bcbaa21a0f0fbbae6166c8a49daa9d` to `61fcd7d0c5aeb1972fc5e531bc6b7d8168ec7b616feb1d39322d9e56819db4ed`. Historical simulation results are preserved and are not equivalent to this runtime.

**Checkpoint acceptance:** pending final-head GitHub CI and independent review. **Baseline 005 calibration:** BLOCKED: 21 critical entries, plus the reproducible pre-existing Alliance diagnostic failure. The next intervention should examine the shared Equipment P0 clauses and the Alliance provenance invariant without broadening this checkpoint.

No deck revision, 4,500-game control, combined balance experiment, automatic merge, or baseline promotion occurred.
