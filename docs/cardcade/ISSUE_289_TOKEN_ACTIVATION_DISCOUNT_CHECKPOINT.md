# Issue #289 — controlled artifact-token activation discount

This checkpoint is stacked on draft PR #339. The ten Baseline 005 decks, original 172-row ledger, earlier overlays, runtime identities, and historical games remain frozen. No balance control was run.

## Selection

The frozen two-copy Bebop & Rocksteady clause is: “Activated abilities of artifact tokens you control cost {1} less to activate.” Mutagen Man's `{X}{G}{G}` casting and X-dependent token entry already execute under #339. Those Mutagen tokens have `{1}, {T}, Sacrifice this token: Put a +1/+1 counter on target creature. Activate only as a sorcery.` This makes the static discount directly observable in legal actions and payments.

| Remaining candidate | Frozen copies | Existing machinery | Scope decision |
| --- | ---: | --- | --- |
| Controlled artifact-token activation discount | 2, B&R | Generic activation planner, token costs, targeting, priority, counters | Selected; bounded static cost calculation |
| Donatello artifact counter transfer | 2, Donatello | Departure events and counters exist; snapshot, optional legal target and stack resolution remain | Open |
| Raphael damage-to-mana trigger | 2, Raphael | Damage events and mana units exist; quantity and retained mana across steps remain | Open |

## Mechanic and validation

A parser recognizes the full static Oracle clause for controlled tokens of an artifact, creature, or enchantment type. The payment planner applies each live matching reducer only to the generic portion of an activated ability's cost, flooring it at zero. It does not change casting costs or colored activation requirements. The live controller, token identity, permanent type, source incarnation, and ability suppression determine the payment plan. The normal activation transaction still validates timing, target, tap and sacrifice costs, stack priority, and resolution. An activation remains independent of a reducer that leaves after payment. The paid amount and reduction source identities are logged.

Focused deterministic fixtures cover zero and stacked discounts, illegal unaffordable actions, colored costs, ordinary artifacts and enemy/nonartifact tokens, spell costs, ability loss and controller change, reducer departure, target choice, cost sacrifice, priority, counters and replay. The earlier X token and artifact animation regression tests remain in the complete suite.

Six authenticated Baseline 005 frozen-deck diagnostics in balanced seats replay identically. The pilot was offered 571 per-target activation options, selected and paid for 21, resolved 21 counter placements, and received eight discounts. Three Mutagen Man token batches were observed. The diagnostic records reducer and token presence, offered and selected actions, payment, discount provenance, resolution, and replay digests. Options can recur within a turn and have multiple targets; these counts are **pilot exposure**, not win-rate evidence.

`ISSUE_289_TOKEN_ACTIVATION_DISCOUNT_CHECKPOINT.json` retains the 172 original row identities and closes exactly one static ability entry. The independent `ISSUE_289_TOKEN_ACTIVATION_DISCOUNT_CALIBRATION_READINESS.json` ranks the residuals. Reproduction scripts are `tools/report_issue289_token_activation_discount.py` and `tools/run_issue289_token_activation_discount_smoke.py`.

## Gates

**Checkpoint acceptance:** the implementation and preserved evidence are reviewable; use the final-head GitHub CI result as the acceptance gate. **Baseline 005 calibration: BLOCKED.** Twelve important entries remain: eight identified blockers and four unbounded effects. Donatello's counter transfer and Raphael's damage-to-mana trigger remain the highest-ranked single-card families. No deck change, new control, merge, or promotion is authorized by this checkpoint.
