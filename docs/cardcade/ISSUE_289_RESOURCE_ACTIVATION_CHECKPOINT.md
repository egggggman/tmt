# Issue #289: resource activation checkpoint

## Authority and selection

This draft stacks on validated PR #335. Baseline 005, its ten deck lists, the original 172-row ledger, all previous overlays, historical games, and runtime identities remain unchanged. The generic code and focused tests were published to the remote branch as a recoverable commit `e15b6cdd1f23de5f48b59d12bcc4d94ae1f61c03` before lengthy regression. No calibration control was run.

The authenticated B&R list contains three **Ice Cream Kitty** and two **Mutagen Man, Living Ooze**. Ice Cream Kitty's two complete frozen clauses are:

- `{2}, Sacrifice another creature or token: Draw a card. Activate only as a sorcery.`
- `{2}, {T}, Sacrifice this creature: You gain 3 life.`

They account for five repeated ledger entries. The first converts another creature or token to a card at sorcery speed; the second converts itself to 3 life at normal activated ability timing. Existing fixed mana, stack, draw, life, and Food sacrifice machinery could support a bounded common activation checkpoint. Mutagen Man's X-dependent token quantity and artifact-token activation reduction need variable payment and quantity machinery, so both rows remain open. Neither is inferred from the new Kitty execution.

## Generic execution and pilot

The interpreter recognizes the complete cost/effect clauses without card or deck names; altered or incomplete clauses remain unsupported. Legal-action generation offers each eligible creature or token separately, excludes the source and opponent-controlled permanents, and requires complete payment. The draw activation checks sorcery timing, consumes fixed mana and the chosen cost permanent, records its original object and destination identity, and draws on stack resolution even if the source subsequently leaves or changes controller. Repeated activations require fresh legal costs and mana; no once-per-turn limit was added. The tap and self-sacrifice life activation uses the existing provenance and stack evidence, can be offered at ordinary priority, and resolves after its source leaves as a cost. State-based actions and deterministic traces are checked.

The generic pilot considers sacrificing a token for the card draw and declines to sacrifice an ordinary creature by default. It considers self-sacrifice for 3 life when its controller is at 5 life or less. These decisions use legal options and public game state, not the Kitty or B&R name. Focused fixtures verify selecting and declining actions. The six unchanged frozen-deck samples offered **zero** Kitty activation opportunities and cast Kitty **zero** times, so they demonstrate runtime stability and deterministic replay but cannot estimate actual use frequency or balance impact. This limitation remains material to the calibration gate.

## Evidence and readiness

The machine overlay authenticates all ten Baseline 005 deck hashes, the original ledger SHA-256 `56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100`, all 172 row identities, the previous overlay SHA, and the new semantic runtime `cffb5eb46b8ae221eb1cf89f10316f382398fac11fccd11f6d447f9e4cbb10f1` (previous `24441ed6387b01e0e1b26d6181b5d5879a2b20243eacb99078b94a4ae50af7f2`). Exactly three draw and two life rows change from gap/P1 to supported/none. This is new executable Oracle coverage; no earlier row was reclassified from stale evidence.

Focused tests include legal and illegal sacrifice choices, full and insufficient mana, sorcery timing, tap/summoning sickness, source departure and control change, another player's ownership, priority, repeated costs, draw/life result, event linkage, invariants, and deterministic replay. The existing Food, Equipment, and activation tests pass. The full local regression passed **2,013 tests, 10 skipped** before two further focused tests were added; the expanded focused run passed **62 tests**. Final-head CI must cover the full expanded suite. Ruff and the Baseline 005 provenance validator passed. Six paired authenticated B&R games against Raphael, Shredder, and Donatello completed with balanced seats, matching deterministic replays, and zero errors. Their outcomes are diagnostic only.

Reproduce the reports with `tools/report_issue289_resource_activation.py` and `tools/run_issue289_resource_activation_smoke.py`. The machine records are `ISSUE_289_RESOURCE_ACTIVATION_CHECKPOINT.json`, `ISSUE_289_RESOURCE_ACTIVATION_CALIBRATION_READINESS.json`, and `ISSUE_289_RESOURCE_ACTIVATION_SMOKE.json`.

| Gate | Decision | Evidence |
| --- | --- | --- |
| Checkpoint acceptance | READY after successful final-head CI | Complete generic clauses, focused invariants, frozen provenance, and deterministic replays |
| Baseline 005 calibration | **BLOCKED** | 0 critical; 18 important; 14 identified calibration blockers; 4 important effects with unbounded impact |

The next ranked families include Mutagen Man's two X and token-cost clauses, Donatello's artifact counters/animation, Krang's artifact scaling, Raphael's restricted-mana damage trigger, and the remaining combat, recursion, Equipment-copy and token effects. The four unbounded entries remain Bebop's Rhino menace, Hamato Guardian Stance, Michelangelo Improviser's combat-damage hand entry, and Michelangelo Mutant BFF's block constraint. Short diagnostic games do not establish deck balance. No deck revision, control, merge, or promotion follows from this checkpoint.
