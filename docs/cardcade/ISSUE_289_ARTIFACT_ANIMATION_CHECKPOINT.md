# Issue #289: targeted artifact counter and animation activation

## Authority and choice

This draft stacks on validated PR #337. The ten Baseline 005 decks, the original 172-row ledger, earlier overlays, historical games, and their runtime identities remain unchanged. A recoverable implementation and focused-test checkpoint was pushed as `6a80210fe6a76b8a49fee7c0a512b24d7f614f4c` before lengthy validation.

| Remaining family | Frozen copies | Current support and risk |
| --- | ---: | --- |
| Mutagen Man, Living Ooze | 2 B&R | `{X}{G}{G}` cannot yet be announced through the fixed-cost planner. X token quantity and the separate artifact-token activation discount require two complete rules paths. Implementing the discount alone would not make this source castable. |
| Donatello, Mutant Mechanic | 2 Donatello | Existing payment, stack, counters, and persistent layer-4/7b animation can support its targeted `{T}` clause. Its independent graveyard counter-transfer trigger remains unsupported. |
| Raphael, Ninja Destroyer | 2 Raphael | Damage-triggered mana generation and retention through steps/phases require a separate duration and event-provenance intervention. |
| Donatello, Gadget Master and other residuals | 2 or fewer per frozen card | Artifact copying and other combat/recursion effects require distinct, wider rules paths. |

Donatello's targeted clause is the smallest complete intervention with observable pilot exposure. The interpreter derives quantity, base P/T, subtype, target restriction, tap cost, and sorcery timing from the complete Oracle sentence, without card or deck name execution branches. Legal options and announcement require an authoritative controlled artifact and valid targeting. The tap cost is committed before the ability goes on the stack. Resolution rechecks the target, places three counters, and animates a noncreature artifact into a persistent 0/0 Robot creature in addition to its types. Existing artifact creatures retain their base P/T. The effect survives its source's departure; target departure or control change prevents all payload. State-based actions and replay evidence verify the result. The unrelated death-trigger transfer remains open.

## Diagnostics and pilot exposure

Focused frozen-card and renamed-card fixtures cover illegal targets, wrong or incomplete Oracle clauses, timing, payment, stack priority, source departure, target departure/control change, persistent layers, existing creatures, and deterministic replay. Six unchanged, authenticated Baseline 005 diagnostic games (Donatello against B&R, Raphael, Krang with both seats) matched six deterministic replays with no runtime errors. The normal pilot saw **49** legal cast opportunities for the source, selected it **4** times, and cast it **4** times. It saw **4** legal activation options, chose **1**, paid **1**, resolved **1**, and delivered **1** counter-and-animation outcome. The pilot selected a cheaper cast while Donatello was castable in **6** observed choice windows. This is exposure evidence, not matchup balance data; the `AcceptancePilot` always chooses the cheapest available hand creature at its creature stage, which can defer mechanically important expensive creatures.

## Coverage and gates

The machine overlay authenticates all ten deck hashes, the predecessor SHA-256, the original ledger SHA-256 `56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100`, and every one of its 172 row identities. Exactly the three formerly unsupported scanner reasons for the same complete targeted activation become supported. Current semantic runtime is `600749ab339b77a2ba5e6bfcfc0e8e43722b454413515b0da111930e33fd95cb`; predecessor runtime is `86dcde6d0ce1a0c81dd934f2861f8e389885f5d92da0eb793170d10d417ba991`.

Reproduce with `tools/report_issue289_artifact_animation.py` and `tools/run_issue289_artifact_animation_smoke.py`. Machine records are `ISSUE_289_ARTIFACT_ANIMATION_CHECKPOINT.json`, `_CALIBRATION_READINESS.json`, and `_SMOKE.json`. Full regression, structural checks, Ruff, and final-head CI are publication gates.

| Gate | Decision | Basis |
| --- | --- | --- |
| Checkpoint acceptance | READY after successful final-head CI | Complete generic activation, focused mechanics, authenticated frozen diagnostics, deterministic replays |
| Baseline 005 calibration | **BLOCKED** | 0 critical; 14 important; 10 identified blockers; 4 unbounded effects; high-cost pilot selection remains a measurable exposure risk |

No deck revision, calibration control, merge, promotion, or balance inference follows. The four unbounded entries remain open pending execution or credible impact bounds.
