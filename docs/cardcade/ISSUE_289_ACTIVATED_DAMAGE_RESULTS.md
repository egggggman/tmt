# Issue 289 — activated targeted damage checkpoint

Stacked on draft PR #302. This is an engine coverage checkpoint for the unchanged ten
Baseline 005 decks, never a balance result. No calibration control was run.

## #302 regression reconciliation

The published **1,759 passed, 10 skipped** local run preceded the final hand-zone
landcycling test. The authoritative #302 final-head `53faae4bec99a41ea2c50beb3b42b466f830a01a`
GitHub Actions [Test run #1455](https://github.com/egggggman/tmt/actions/runs/38423754674)
job log records **1,760 passed, 10 skipped in 114.00 seconds**. The final-head CI count
supersedes the earlier local collection; it does not represent a test failure.

## Critical ranking and selected boundary

The exact #302 172-row overlay has 23 P0 rows. Row copy totals can double-count one
card's multiple clauses, so this ranking uses unique frozen card/deck copies within
each shared intervention. Severity and implementation scope break ties.

| Intervention | Frozen copies / decks | Gameplay consequence | Scope decision |
| --- | ---: | --- | --- |
| Equipment combat modifiers and equip costs | 9 / 3 | Repeated combat math and identity | Several different static, trigger, and sacrifice-cost families; retain P0 |
| Targeted creature damage (Foundry, Tenderize) | 7 / 2 | Removal and combat survival | Shared damage transaction; implement four-copy fixed artifact activation first |
| Modal Mouser Attack! | 3 / 1 | Token and first-strike combat | Choices and two distinct payloads; retain P0 |
| Oroku Saki combat damage draw/life loss | 3 / 1 | Repeatable resource swing | Trigger family; retain P0 |
| Linked Raphael exile/play | 2 / 1 | Signature access and casting | Multiple legal casting families remain; retain P0 |
| Other P0 resource, casting, combat, and removal clauses | 1–3 per card | Material but distinct | Reassess next checkpoint |

The chosen rule recognizes a **noncreature artifact** activation with a fixed mana cost,
“Sacrifice this artifact” cost, and “It/This artifact deals N damage to target
creature.” It derives amount and target from the Oracle fragment. The engine generates
legal options during main and priority windows, pays mana and sacrifice transactionally,
keeps the ability on the stack after source departure, uses the authenticated departure
event as last-known damage-source authority, rechecks the target on resolution, applies
damage, and runs state-based actions. The pilot chooses an opposing creature by public
board value and declines to sacrifice solely to damage its own creature. No card or deck
name controls execution.

This bounded grammar does not claim artifact-creature last-known Deathtouch/Lifelink
support. It fails that shape closed. Tenderize's power-dependent creature-to-creature
damage and Foundry's separate Robot-token entry/leave clause remain open in the ledger.

## Validation and preservation

- New deterministic fixtures exercise frozen Oracle recognition, renamed generic
  execution, insufficient mana, target protection, legal priority activation, source
  sacrifice, lethal damage/state-based death, target departure, event relinking rejection,
  pilot choice, and exact replay. Frozen Casey/Krang and Casey/Raphael diagnostics cover
  four balanced seat orientations, four matching replays, zero runtime errors, and one
  actual activated damage resolution. See `ISSUE_289_ACTIVATED_DAMAGE_SMOKE.json`.
- Final local full regression: **1,769 passed, 10 skipped in 86.05 seconds**.
  Focused activation/damage/stage projection tests, Ruff check and format, diff
  check, Baseline 005 structural validation, and exact predecessor hashes passed.
- The original 172-row CSV SHA-256 remains
  `56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100`.
  The #302 overlay SHA-256 is
  `2a4efb70a6e8ae06d4de7dd8f3992f9abca7f30e8ce123ba3bd9023531539745`.
  `ISSUE_289_ACTIVATED_DAMAGE_CHECKPOINT.json` preserves every row and changes only
  the Casey Mouser Foundry damage activation from P0 gap to supported.
- Before runtime: `0d953551f6faee293e74afb9642c75c8cc7a9c93142f64a4c0d7b45537d3832a`.
  New runtime: `7ca337922f33feeaf8371f15eb5813ade5bcbaa21a0f0fbbae6166c8a49daa9d`.
  Historical simulation evidence is untouched and not runtime compatible with this
  semantic change.

**Checkpoint acceptance:** pending final-head CI and independent review.
**Baseline 005 calibration:** BLOCKED (22 critical, 64 important, 3 partial).

No deck revision, automatic merge, 4,500-game control, or promotion occurred.
