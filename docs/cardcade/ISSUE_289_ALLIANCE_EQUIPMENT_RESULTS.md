# Issue 289: Alliance provenance and one Equipment intervention

Stacked on draft PR #304, head `f0d26bdad786240d274f3357c1445cb7453bfbaf`. Baseline 005 deck lists, the original 172-row ledger, all prior checkpoints, and historical simulation results remain unchanged. This is an engine readiness checkpoint, not balance calibration.

## Reproduction and correction

Michelangelo first versus Raphael at seed `3032` fails identically on unchanged #303 and #304. At turn 8, postcombat main, Raphael casts Cool but Rude. Its entry event `event-000030` has kind `permanent_entered` and subject `object-000177`, an Enchantment — Class. The event's battlefield authority correctly includes Wingnut (`object-000175`, controller 1). The dispatcher incorrectly enqueues Wingnut's Alliance temporary-keyword trigger (`trigger-000003`) for that noncreature entry, though the trigger validator correctly requires `creature_entered`. The next invariant check raises `temporary-keyword trigger has mismatched Alliance provenance`.

The shared entry dispatcher now uses the entering permanent's evaluated creature type both to label the event and to decide whether creature-entry triggers may run. Noncreature artifact self-entry processing still happens before the creature filter. An enchantment, land, or noncreature artifact cannot create an Alliance trigger. Actual creature entries still do. A red-before/green-after regression covers those three noncreature shapes and a following creature entry; existing fixtures prove source incarnation, zone departure, keyword duration, and cleanup. The same seed `3032` now completes without an invalid trigger and produces a matching replay. The Alliance test that used an Instant as a battlefield creature was corrected to use a legal creature fixture.

## Equipment selection

| Remaining clause | Frozen copies / decks | Combat or payment impact | Shared implementation and complexity | Decision |
| --- | --- | --- | --- | --- |
| Improvised Arsenal: artifact-count +1/+0; bare Equip {R} | 3 / Casey Jones | Attack and block damage change with artifact count; equip must be paid at sorcery speed | Reuses attachment, payment, continuous P/T modifier, and stack paths; small rule addition | **Implemented as two complete clauses** |
| Quintessential Katana: +1/+1 plus combat-damage untap/life; Ninja-entry attach | 2 / Leonardo | Hit-trigger life and untap; attachment timing | Needs granted triggered ability and separate automatic entry attachment | Remains open |
| Shredder's Armor: sacrifice equip once per turn; entry attach | 4 / Shredder | Alternative equip cost, once-per-turn restriction, entry target | Requires transactional nonland sacrifice cost plus activation history; separate ETB trigger | Remains open |
| Improvised Arsenal: Equipment-copy activation | 3 / Casey Jones | Additional Equipment bodies and artifact count | Requires generic token copy of a permanent | Remains open |

The dynamic equipped bonus is evaluated in the P/T modification layer from artifacts currently controlled by the Equipment's controller, including the Equipment itself. It recalculates on attachment changes, artifact entry or departure, and source departure. Generic bare `Equip {cost}` now uses the existing activated-ability payment and attachment path with explicit sorcery-speed enforcement. The same grammar upgrades seven additional Equip clauses elsewhere in the frozen card catalog; only Improvised Arsenal adds a newly executable bare Equip clause to the ten frozen deck lists. No card/deck name controls execution. The Equipment-copy ability remains unsupported, so this does not claim whole-card support.

## Verification and gates

- Focused tests cover legal and illegal Equip targets and controllers, insufficient mana, sorcery timing, source removal on the stack, current artifact count, attachment changes, departure, combat damage at derived power, deterministic replay, and frozen Oracle recognition. Alliance tests verify false noncreature triggers are absent, true creature trigger/event linkage, source identity, zone departure, duration, and cleanup.
- Exact former failure seed `3032`: one game and one matching replay, no runtime error or noncreature Alliance trigger. Four mirrored Casey/Raphael and Casey/Shredder games at seed `3045`: four matching replays, zero runtime errors, **21 Improvised Arsenal attachments and 11 derived-power change events**. Per-game digests and event provenance are in `ISSUE_289_ALLIANCE_EQUIPMENT_SMOKE.json`. These five small games are diagnostic only.
- Final local regression: **1,787 passed, 10 skipped in 97.72 seconds**. Baseline 005 structural validation, Ruff check and format, and diff check passed. Final-head GitHub CI is tracked on the draft PR. The structural validator's historical console land-count prose is unrelated to these changes.
- The original ledger SHA-256 remains `56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100`; #304 overlay remains `439cecc09756c6ccfc1ba9f561b3a2d97b7743de145caa2d49ecd962c0332285`. The new overlay changes exactly two Improvised Arsenal rows (P0 dynamic bonus and P1 bare Equip) to supported: **21 critical / 64 important / 3 partial → 20 critical / 63 important / 3 partial**. The Alliance correction repairs an invariant and does not reclassify an additional ledger row.
- Runtime changes from `61fcd7d0c5aeb1972fc5e531bc6b7d8168ec7b616feb1d39322d9e56819db4ed` to `d27c9c8f7aeb82a3311b6cc72586b6a5103c0f8ce333588fe13c41812e6c7e2d`. Historical controls are not runtime compatible.

**Checkpoint acceptance:** pending final-head CI and independent review. **Baseline 005 calibration:** BLOCKED while 20 critical, 63 important, and 3 partial entries remain. No deck revision, 4,500-game control, automatic merge, or promotion occurred.
