# Issue 289: combat-damage draw and life-loss trigger

This engine checkpoint stacks on draft PR #307. The ten frozen Baseline 005 deck lists, original 172-row ledger, earlier overlays, and historical game evidence are unchanged. Diagnostic games here are not balance evidence.

## Ranking and selection

The [machine coverage overlay](ISSUE_289_COMBAT_DRAW_LIFE_CHECKPOINT.json) retains all 18 prior critical entries with their exact fragments, frozen card copies, rank, gameplay severity, shared-rule reuse, and implementation complexity. Repeated rows on one card are distinct semantic fragments, **not additional physical copies**. The ranking weighs card exposure and effect on combat, casting, resources, and opponents; lower complexity breaks ties for a complete next checkpoint.

| Rank | Family / card | Frozen copies; critical rows | Gameplay and scope assessment |
| ---: | --- | ---: | --- |
| 1 | Self combat hit: Oroku Saki, Shredder Rising | 3; 1 | Material card advantage on Shredder's combat turns, with life as a real cost; reuses authenticated player-damage events and priority. **Selected.** |
| 2 | Targeted ETB removal: Anchovy & Banana Pizza | 2; 1 | Strong creature interaction against all opponents; requires target selection and destruction provenance. |
| 3 | Modal token/combat trick: Mouser Attack! | 3; 2 | High exposure and flexible pressure; requires mode selection at casting, conditional target, token creation, temporary power and first strike. |
| 4 | Conditional cost and protection: Saved by the Shell | 3; 3 | High exposure and combat survival; Turtle discount partly executes, while counter/three temporary abilities and complete casting remain linked. |
| 5 | Type/base P/T transformation plus draw: Mind Transfer Protocol | 3; 2 | Changes combat and card flow; requires legal artifact/creature target, continuous type and P/T layers, duration, and draw. |
| 6 | Linked exile/play: Raphael, Most Attitude | 2; 2 | Deck identity; existing linked identity/duration and interpreted casting are partial, while remaining exiled spell families are not all executable. |
| 7 | Owner library choice plus token: Return to the Sewers | 2; 1 | Broad removal and resource effect; requires owner choice, exact zone movement, then Mutagen entry. |
| 8 | Multi-target recursion: Leonardo's Technique | 2; 1 | Major board recovery; requires one or two graveyard targets, mana-value bounds, and independent legality on resolution. |
| 9 | Each-player optional hand reset: Raphael's Technique | 2; 1 | Broad resource reset; requires simultaneous player choices, ordered discards/draws and empty-library handling. |
| 10 | Unrestricted tutor: Splinter's Technique | 2; 1 | Strong selection across the library; requires an authenticated choice, reveal policy, transfer and shuffle. |
| 11 | Top-eight constrained creature selection: Michelangelo's Technique | 2; 1 | High-value board development; requires total mana-value bound and random bottom ordering. |
| 12 | Sneak-dependent attacking tokens: The Last Ronin's Technique | 1; 2 | Creates three bodies; conditional tapped-and-attacking entry requires combat linkage. |

Important Equipment-copy behavior remains a **separate P1 family**: three Improvised Arsenal copies have two ledger entries for `{4}{R}: Create a token that's a copy of this Equipment.` Its complete implementation needs copyable values, a new object identity, unattached token entry, and independent subsequent equip behavior. This checkpoint does not claim it supported.

## Semantics and evidence

The interpreter recognizes any creature whose self-referential Oracle clause says it deals combat damage **to a player**, then “you draw N card(s) and lose M life.” It does not match ordinary damage or creature damage. The engine authenticates positive player combat damage, battlefield source/controller, exact trigger fragment, and original event. The trigger goes on the normal priority stack. Resolution draws before life loss; it persists after the source leaves the battlefield and logs the event, trigger, stack object, source, controller, draw count, and life transition. Failed draws and lethal life loss reach the normal state-based actions after the whole ability resolves. No card/deck-name branch exists in engine execution.

- Synthetic renamed fixtures plus the frozen Oracle fixture test parsing, unblocked and blocked combat, two double-strike steps, priority, source departure, empty-library loss, event provenance, and exact replay. Existing April combat-damage and Equipment tests pass.
- Five frozen Shredder/April, Shredder/Casey and Shredder/Leonardo diagnostic games matched five deterministic replays with zero runtime errors. They recorded six frozen-source casts and three resolved combat draw/life triggers. Per-game digests and event IDs are in the [machine diagnostic](ISSUE_289_COMBAT_DRAW_LIFE_SMOKE.json). This bounded evidence proves execution, not win-rate impact.
- The original ledger SHA-256 remains `56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100`; the #307 overlay SHA-256 remains `65f43641ad41a3d434203b88b4fc6cbb4d864aeac786a95a7cf5224ee4660ed5`. Exactly one Oroku row changes: **18 critical / 61 important / 3 partial → 17 critical / 61 important / 3 partial**.
- Semantic runtime changes from `289ce95d8282e2ee33b1ffb468c117a7620dea7127609dcfe9ebc993cb5ea8a3` to `d22d08a2d0181af12413cc816c64edbd096d112d55903711d50c13c1fef2f3e3`. Historical Baseline 005 controls are not runtime compatible. The frozen Baseline 005 manifest remains `c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac`.
- Full regression: **1,803 passed, 10 skipped**. Baseline 005 structural validation, repository-wide Ruff check/format, Markdown relative-link validation, overlay row audit, and diff check passed. The structural validator prints historical land-count prose, while its authenticated manifest/deck checks pass.

**Checkpoint acceptance:** READY for independent review once final-head GitHub CI is green. **Baseline 005 calibration readiness:** BLOCKED. No calibration control, deck revision, merge, or promotion occurred.
