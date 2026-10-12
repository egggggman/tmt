# Issue 289: linked play, Class, and conditional removal checkpoint

Stacked on draft PR #298 at `eb9fd8f8cdcd84bd38da488369eca34f5642b2ab`.
The ten Baseline 005 deck files, the original 172-row ledger, and all earlier overlays and simulation evidence are unchanged.

## Executed rules

| Family | Evidence | Rows closed |
| --- | --- | ---: |
| Linked exile/play permission | A source-bound, chosen exiled card can use represented main-phase or instant-priority casts with ordinary mana, targeting, and stack rules. Kicked instant, counter, targeted damage/removal, draw, Aura, Flash, land, creature, and other represented permanent paths are offered at legal timing. Distinct attack grants accumulate through the end of the turn; source departure does not revoke an existing grant. A card with an uninterpreted spell effect remains unplayable, so the Oracle ability is still partial. | 2 partial P0 retained |
| Class levels and discard | Class level costs advance exactly one level at sorcery timing. Attacking with a creature delivers the Class level-one optional discard then draw. At level two, each actual hand discard triggers damage on the stack, including an unrelated discard, and survives source departure. Level three searches for a card, puts it in hand, shuffles, then discards at random; the level-two trigger sees that discard. | 2 P0 and 3 P1 |
| Conditional destroy and Food | An Instant legally targets an artifact or creature, attempts destruction, uses the target's last-known mana value, and creates a Food token only if that value was at most four. An illegal target on resolution prevents the whole spell's effects. The condition can be true even when an indestructible target remains. | 1 P0 |

The implementation dispatches from interpreted Oracle text and permanent types. The frozen cards are acceptance fixtures; none of the new engine or pilot branches dispatch by a card or deck name. [Wizards' TMNT release notes](https://magic.wizards.com/en/news/feature/teenage-mutant-ninja-turtles-release-notes) confirm the last-known mana-cost interpretation for Tainted Treats.

## Provenance and coverage

- Original ledger: `ISSUE_289_COVERAGE_LEDGER.csv`, SHA-256 `56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100`, 172 rows.
- Previous overlay: `ISSUE_289_IDENTITY_CHECKPOINT.json`, SHA-256 `d1fe2dca95f2e3a3426f1234de3df664f499ca314e59994ce361846c5aa40282`.
- Previous semantic runtime: `4d1dd3aa00758c8bf150878bcc0379e0a92f9c604ca2339c478d3a1b533e24bb`.
- New semantic runtime: `75a725ffdc6460a8d1190c5738837dddf0ed1a85d628eefaca4ed35adf8f1ccd`.
- Reproduce the row overlay: `PYTHONPATH=src:tools python tools/report_issue289_critical_identity.py`.
- Remaining: **27 critical P0** (25 gaps and 2 partial), **65 important P1**, **2 partial**. Six rows changed to supported; 90 gaps remain (25 critical and 65 important). Seven annotations and 33 previously covered rows retain their classifications.

The remaining critical entries include Raphael's uninterpreted exiled spell families and high-copy Mouser Attack! modes, Shredder's Armor equip sacrifice, Casey's Purple Dragon Punks mana and Mouser Foundry damage, Michelangelo's Saved by the Shell cost/defense, Splinter's Death in the Family exile, and other casting/combat/resource effects across the frozen roster. These remain gameplay blockers. The next shared intervention should be selected by copy count, deck impact, and overlap, rather than by aggregate balance outcomes.

## Validation

- Focused tests cover legal and illegal target states, payment, priority timing, source departure, exact event provenance, indestructible and high-value targets, Class level progression, Class search/shuffle/random discard, and deterministic replay.
- Four mirrored frozen B&R/Raphael and April/Raphael diagnostics matched four exact replays, with no runtime errors. Class discard damage resolved nine times and level-three search three times across these small diagnostics. No linked exile or conditional removal resolved in those four seeds; their actual execution is established by focused tests. These are diagnostics, not balance evidence.
- Full regression: **1,738 passed, 10 skipped** after the repeated-grant fixture and updated coverage expectations. Ruff check/format, diff checks, Baseline 005 structural validator, and prior evidence hash checks passed. The validator's console text about a historical land-count change is stale prose; authenticated lists are unchanged.

**Checkpoint acceptance:** pending remote CI.

**Baseline 005 calibration readiness:** **BLOCKED**. No control, deck edit, new balance experiment, merge, or promotion was performed.
