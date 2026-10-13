# Issue 289: direct targeted removal checkpoint

Stacked on draft PR #299 at `a2b02a05abb3d99f964e04b055870a74dbd7b70b`.
This is an engine checkpoint, not a Baseline 005 balance assessment. The ten frozen deck
files, original ledger, all earlier checkpoints, and historical game evidence are unchanged.

## Critical-gap ranking before implementation

Copies are distinct frozen-deck card copies, not fragment-row counts. The severity assessment
uses the preserved 172-row overlay. Closely related clauses with different delivery or payment
remain separate implementation work; counting them together does not claim closure.

| Rank | General family and frozen copies | Decks | Gameplay consequence | Scope of this checkpoint |
| --- | --- | --- | --- | --- |
| 1 | Targeted battlefield removal: Death in the Family 3, Shredder's Technique 3, Anchovy & Banana Pizza 2 (8) | Splinter, Shredder | No legal answer to early creatures or enchantments; major board and interaction distortion | The six direct-spell copies share normal target locking, current-characteristic checks and zone movement. Pizza's two ETB copies require a separate trigger-delivery step. |
| 2 | Mana and casting: Purple Dragon Punks 4, Saved by the Shell 3, Krang, Master Mind 2 (9) | Casey, Michelangelo, Krang | Restricted mana, conditional discount and affinity materially alter casting pace | Three distinct cost/payment clauses; next assessment should prioritize shared payment rules. |
| 3 | Targeted damage: Mouser Foundry 4 and Tenderize 3 (7) | Casey, Michelangelo | Activation and own-creature damage can remove blockers or threats | Shared damage transaction, distinct activation and spell targeting. |
| 4 | Equipment/stat effects: Shredder's Armor 4, Improvised Arsenal 3, Quintessential Katana 2 (9) | Shredder, Casey, Leonardo | Costed attachment and dynamic combat characteristics | Multiple distinct attachment costs and continuous effects. |
| 5 | Modal token/combat effect: Mouser Attack! 3 | Raphael | Choice between Robot development and first-strike power swing | One card with two modal payloads. |

The selected family closes two critical rows in two decks, plus the Shredder Sneak timing row.
Its shared target/zone pipeline uses existing engine primitives and is smaller than the three
different payment mechanics in rank 2. The rankings do not imply any balance outcome.

## Oracle execution and validation

- A direct instant or sorcery with a complete recognized removal payload derives legal target
  types and optional mana-value bound from its Oracle text. The object identity locks on
  announcement; current battlefield characteristics, protection and restrictions are rechecked
  on resolution. An illegal target causes no effect. Normal land payment is unchanged.
- Destruction respects indestructible. Exile uses the owner's exile zone. Conditional life loss
  occurs only when an enchantment was actually destroyed. Shredder's Sneak alternative pays its
  mana and attacker-return costs and selects a legal target before the stack object is created.
  Instant removal can also be used with priority. The pilot chooses an opposing legal target
  from public state and declines a targeted Sneak removal when only its own permanents qualify.
- No execution branch tests a card or deck name. The card names in the tests and diagnostic
  reporting are fixtures and labels, not dispatch conditions. The parser rejects extra
  unimplemented spell instructions rather than granting partial spell resolution.
- Focused tests prove both zone destinations, current type and mana-value legality, target
  invalidation, indestructibility, life-loss condition, instant priority, Sneak payment and
  target locking, deterministic state equality, and generic pilot choices.
- Four mirrored frozen Splinter/Shredder and April/Shredder diagnostics matched four exact
  deterministic replays, with no runtime errors. Five direct-removal casts and two targeted
  exiles appeared. These games are execution diagnostics and carry no win-rate inference.
- Full regression: **1,745 passed, 10 skipped**. Ruff check and format, diff checks, and
  Baseline 005 structural validation passed. The structural validator still prints its
  historical stale land-count prose; the authenticated Baseline 005 manifest SHA below is
  unchanged.

## Provenance and coverage

- Original ledger: `ISSUE_289_COVERAGE_LEDGER.csv`, SHA-256
  `56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100`, 172 rows.
- #299 overlay: `ISSUE_289_CRITICAL_IDENTITY_CHECKPOINT.json`, SHA-256
  `540dc5b282750e5d6510b000f6b4ccfc4f6314380d8fa6d7a56c2b1c51e9f29e`.
- Unchanged Baseline 005 manifest SHA-256:
  `c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac`.
- Before runtime: `75a725ffdc6460a8d1190c5738837dddf0ed1a85d628eefaca4ed35adf8f1ccd`.
- This runtime: `92528faf3854869ea0905e36102c2aa22b8b36d8a880ccaeebf7ab8668b33cb5`.
- Reproduce with `PYTHONPATH=src:tools python tools/report_issue289_targeted_removal.py`
  and `PYTHONPATH=src:tools python tools/run_issue289_targeted_removal_smoke.py`.
- Complete overlay: 172 rows, **25 critical P0** (23 gaps and two Raphael partial),
  **64 important P1**, **two partial**. Three rows changed to supported; 87 gaps remain,
  seven annotations and 33 covered rows retain their classifications.
- Next intervention: evaluate shared restricted/discounted mana and payment mechanics, then
  the distinct activated and spell damage clauses. The unexecuted Pizza ETB destroy trigger,
  Raphael linked-play partials, and other critical rows remain explicit blockers.

**Checkpoint acceptance:** pending remote CI and independent review.

**Baseline 005 calibration readiness:** **BLOCKED**. No control or balance simulation was run.
