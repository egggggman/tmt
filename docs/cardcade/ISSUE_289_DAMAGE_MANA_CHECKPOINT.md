# Issue #289 — damage-triggered retained mana

Draft checkpoint stacked on #341. Baseline 005, its ten frozen deck lists, the original 172 ledger identities, prior overlays, and historical simulation artifacts remain unchanged. No calibration control or balance experiment was run.

## Selection and frozen authority

The frozen two-copy **Raphael, Ninja Destroyer** clause reads: “Enrage — Whenever Raphael is dealt damage, add that much {R}. Until end of turn, you don't lose this mana as steps and phases end.” The separately printed blocking obligation already executes. The clause is an unrestricted red mana grant; its special property is duration. The two-copy **Donatello, Gadget Master** artifact-copy trigger has two open rows and requires general target-copy characteristics and token identity machinery. Raphael's complete trigger fits existing damage events and the per-unit mana ledger with a bounded duration extension. Other high-copy gaps remain ranked in the readiness JSON.

## Complete executed rule

A generic self-damage parser requires the complete trigger and duration sentence. Creature damage events record their original recipient, amount and controller. Combat and noncombat damage enqueue the printed trigger before state-based removal. Stack resolution generates exactly the damage amount of its printed mana color for that original controller, even if the recipient later leaves. The unit carries source, event, permitted spending context and turn-end retention. Ordinary units expire at every step or phase boundary, including the transition from first-strike to regular combat damage; retained units survive those boundaries and expire after cleanup. Normal spell and activated-ability payment draws from eligible units transactionally. Invalid, suppressed, or incomplete effects cannot generate mana. No card- or deck-name execution branch implements this rule.

## Verification

Focused fixtures cover the exact frozen clause and a renamed generic creature; positive damage and no player-damage trigger; combat and noncombat provenance; priority, source departure and ability suppression; mixed restricted, ordinary and retained units; legal spell and activated-ability payments and invalid payment; first-strike to regular-step expiration; cleanup expiration and invariants. Full regression, Ruff and structural validation results are recorded with the final head.

Six authenticated frozen Baseline 005 diagnostics each ran twice with matching full-result and pilot-observation digests. They recorded **11 legal Raphael cast offerings, 2 selections and casts, 1 qualifying combat-damage event, 1 trigger and 1 resolution granting 2 red mana**. Four later boundaries recorded retained mana. The diagnostic found 20 legal cast/activation options and five main-action selections after that trigger, including one authenticated cost payment consuming the retained trigger's mana event ID. The pool fell from 2 to 1 before cleanup. This is direct mechanic and pilot-exposure evidence from a small diagnostic, not a balance estimate. The diagnostic preserves legal opportunities, selections, casts, damage, triggers, resolutions, retention and cost payments separately.

`ISSUE_289_DAMAGE_MANA_CHECKPOINT.json` retains all 172 row identities and closes exactly Raphael's complete Enrage row. `ISSUE_289_DAMAGE_MANA_CALIBRATION_READINESS.json` ranks all ten remaining important rows independently; `ISSUE_289_DAMAGE_MANA_SMOKE.json` preserves game and replay digests. Reproducers: `tools/report_issue289_damage_mana.py` and `tools/run_issue289_damage_mana_smoke.py`.

## Gates

**Checkpoint acceptance: READY subject to final-head CI.** **Baseline 005 calibration: BLOCKED.** Zero critical entries, ten important gaps, six identified blockers, and four unbounded important effects remain. The highest ranked open family is Gadget Master's artifact copy; targeted entry combat modifiers and temporary death recursion follow. The four unbounded cases remain open pending support or a credible impact bound. No deck revision, full control, merge or promotion is authorized.
