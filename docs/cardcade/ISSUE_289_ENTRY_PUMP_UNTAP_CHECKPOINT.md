# Issue #289 — targeted entry pump and untap

Draft checkpoint stacked on #342. Frozen Baseline 005, all ten deck contents, the original 172-row ledger, earlier overlays, historical simulation evidence and runtime identities are unchanged. No 4,500-game control or balance experiment was run.

## Selection and Oracle authority

The frozen three-copy **Guac & Marshmallow Pizza** is `{G}` Artifact — Food with Flash; its outstanding clause is: “When this artifact enters, target creature gets +2/+2 until end of turn. Untap it.” Its separate sacrifice-for-life activation and Flash already execute. The two-copy **Donatello, Gadget Master** combat-damage artifact-copy effect has two open rows. Arbitrary artifact copying also informs three-copy **Improvised Arsenal**, but requires copiable characteristics, independent token identity, noncopiable counters/modifiers/attachments, and separate target/activation paths. The three-copy **Pain 101** needs a temporary granted death trigger and graveyard return identity. Guac is the smallest complete high-impact intervention with observed pilot casting opportunities. The remaining effects are ranked in the readiness JSON.

## Complete executed rule

A general parser recognizes a permanent entering and the entire targeted `+N/+N until end of turn. Untap it.` clause, validating its source type and rejecting incomplete companion text. The entry event creates a trigger. A mandatory legal creature target is chosen when it goes on the stack, excluding protected targets; if none exists, the trigger has no legal target. Priority is offered before resolution. The original event, source, controller, printed clause and selected target are authenticated. If the target is still legal, layer-7c P/T applies until cleanup and it untaps. If the source departed, the trigger remains independent; if the target departed, changed type or gained protection, neither modifier nor untap occurs. Existing state-based actions and cleanup remove the modifier. No card-name or deck-name dispatch executes the mechanic.

## Verification and exposure

Focused tests use both the exact catalog card and a renamed generic creature. They verify `{G}` payment, entry target options, protection, priority, modifier and untap, source and target departure, illegal target and forged selection, type/protection changes, no-target behavior, cleanup, invariants and exact replay. Full regression, Ruff and structural checks are recorded with the final PR head.

Six authenticated frozen Baseline 005 games each ran twice with exact full-result and pilot-observation digests. The diagnostic records 117 legal cast offerings over pilot stages, 11 selections and casts, 11 authenticated entry events and triggers, ten legal target choices and complete resolutions, and one no-legal-target case. Ten `+2/+2` modifier events occurred; the resolution events separately record whether each target was tapped and untapped. Repeated offerings across stages are **not** 117 distinct cards or casts. This small sample proves pilot exposure and engine execution, not game balance.

The reproducible overlay `ISSUE_289_ENTRY_PUMP_UNTAP_CHECKPOINT.json` preserves all 172 row identities and closes exactly the complete Guac entry clause. The independent `ISSUE_289_ENTRY_PUMP_UNTAP_CALIBRATION_READINESS.json` ranks nine remaining important rows, including four unbounded impacts. `ISSUE_289_ENTRY_PUMP_UNTAP_SMOKE.json` preserves the diagnostics and replay digests. Reproducers are `tools/report_issue289_entry_pump_untap.py` and `tools/run_issue289_entry_pump_untap_smoke.py`.

## Gates

**Checkpoint acceptance: READY subject to successful final-head CI.** **Baseline 005 calibration readiness: BLOCKED.** Zero critical gaps, nine important gaps, five identified blockers and four unbounded important effects remain. Artifact-copy, temporary death recursion and other combat and token effects remain open. No deck revision, control, merge or promotion is authorized.
