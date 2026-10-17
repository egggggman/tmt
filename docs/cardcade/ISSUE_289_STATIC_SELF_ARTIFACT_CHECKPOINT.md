# Issue #289: self scaling from controlled artifacts

## Authority and selection

This draft stacks on validated PR #336. Baseline 005, all ten frozen deck lists, the original 172-row ledger, previous overlays, runtime identities, and historical games remain intact. The executable code and focused tests were published recoverably at `222d7e5b8848268824399192634522fd054f4301` before full regression. No calibration control was run.

| Remaining family | Frozen copies | Current machinery and scope |
| --- | ---: | --- |
| Mutagen Man, Living Ooze | 2 in B&R | `{X}{G}{G}` and `create X Mutagen tokens` need variable casting payment and token quantity; the separate artifact-token activation discount requires a generic activation-cost modifier and a usable token source. The X spell cannot currently be cast by the fixed-cost planner. |
| Donatello, Mutant Mechanic | 2 in Donatello | Targeted `{T}` ability needs three counters, noncreature artifact animation and base 0/0 in continuous layers. Its separate death-trigger counter transfer needs last-known counters and target legality. |
| Krang, Master Mind | 2 in Krang | Affinity and entry hand refill already execute. `Krang gets +1/+0 for each other artifact you control.` is a complete dynamic layer-7c self modifier with no new payment or stack path. |
| Raphael, Ninja Destroyer | 2 in Raphael | Damage-dependent restricted mana and duration need a separate resource intervention. |

All four have consequential potential and two frozen copies. Krang's complete static rule has the smallest implementation surface and can operate immediately if the pilot casts it. Mutagen Man's discount alone would not establish token creation or X payment. This checkpoint implements only the generic self-scaling rule.

## Generic execution and evidence

The interpreter accepts a complete self-reference and signed P/T modifier for each other controlled artifact or enchantment; the source must be a creature. It rejects a wrong recipient or appended unsupported text. The engine recomputes the count as controlled permanents enter, leave, change controller, or change type. It excludes the source, counts tokens, applies the modifier in layer 7c, and removes it when the source loses abilities or leaves. A new incarnation receives its own count. Telemetry records source object ID, exact fragment, counted quality, count, current modifier, and delta. The Stage 002 machine classifier identifies this family explicitly. No card or deck name selects the execution path.

Focused fixtures use the frozen Krang catalog and renamed creatures. They verify tokens, nonartifact creatures, opposing artifacts, control changes, source departure/reentry, Retro-Mutation ability loss and restoration, counters, combat damage, no-op refreshes, invariants, and deterministic traces. The existing Chrome Dome, Aura, affinity, Ice Cream Kitty, and conformance suites remain part of regression. One old conformance fixture expected this exact creature text to be unsupported; its noncreature variant retains that unsupported-observation test, while the creature effect has direct execution tests.

Six authenticated, unchanged Baseline 005 Krang games against B&R, Raphael, and Donatello ran with both seats and six matching deterministic replays. There were zero runtime errors. The normal pilot was offered a legal Krang cast **11** times, selected it **zero** times, and therefore the six games recorded **zero** Krang casts, battlefield-presence turns, and modifier changes. This is a concrete pilot-exposure limitation, not evidence that the mechanical effect is weak or that matchups improved. The focused rules tests prove execution; the six games do not measure balance.

## Coverage and gates

The machine overlay authenticates every frozen deck hash, the original ledger SHA-256 `56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100`, all 172 row identities, and the previous overlay SHA. The new semantic runtime is `86dcde6d0ce1a0c81dd934f2861f8e389885f5d92da0eb793170d10d417ba991`; the predecessor is `cffb5eb46b8ae221eb1cf89f10316f382398fac11fccd11f6d447f9e4cbb10f1`. Exactly one Krang row changes from gap/P1 to supported/none. No other row is reclassified from old evidence. The independent readiness record ranks all 17 remaining important rows and their shared families, retaining the four unbounded entries.

Reproduce the overlay with `tools/report_issue289_static_self_artifact.py` and the paired diagnostic with `tools/run_issue289_static_self_artifact_smoke.py`. Their machine records are `ISSUE_289_STATIC_SELF_ARTIFACT_CHECKPOINT.json`, `ISSUE_289_STATIC_SELF_ARTIFACT_CALIBRATION_READINESS.json`, and `ISSUE_289_STATIC_SELF_ARTIFACT_SMOKE.json`. Full regression, Ruff, structural validation, and final-head CI are required publication gates.

| Gate | Decision | Basis |
| --- | --- | --- |
| Checkpoint acceptance | READY after successful final-head CI | Complete generic Oracle clause, focused mechanics, provenance, and deterministic replay |
| Baseline 005 calibration | **BLOCKED** | 0 critical; 17 important; 13 identified gameplay blockers; 4 unbounded important effects; pilot selected no Krang casts in sampled games |

Mutagen Man's X payment/token creation and artifact-token ability discount, Donatello's artifact mechanics, Raphael's damage-trigger mana, and remaining combat/recursion/copy effects remain open. The four unbounded entries remain Bebop's Rhino menace, Hamato Guardian Stance, Michelangelo Improviser's hand entry, and Michelangelo Mutant BFF's block constraint. No deck revision, full control, merge, promotion, or balance conclusion follows.
