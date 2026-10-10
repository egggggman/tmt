# Issue 289 — critical semantic closure checkpoint

**Recommendation to HQ: BLOCKED** for an unchanged 45-cell / 4,500-game Baseline 005 control. No deck, catalog, historical evidence, or accepted PR #290–#293 file changed; no calibration or promotion was run.

## Provenance and bounded closure

This checkpoint stacks on validated [PR #293](https://github.com/egggggman/tmt/pull/293), following draft PRs [#290](https://github.com/egggggman/tmt/pull/290), [#291](https://github.com/egggggman/tmt/pull/291), and [#292](https://github.com/egggggman/tmt/pull/292). The preserved [172-row original CSV](ISSUE_289_COVERAGE_LEDGER.csv) has SHA-256 `56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100`; the [#293 checkpoint](ISSUE_289_READINESS_CHECKPOINT.json) has SHA-256 `f4c8c8cf1cf9cb53d814d7c9cf2b9a039538fa2a3386b5f4862451b18c556be3` and runtime `08a7705c385daf2b1c3e8cfd0da6a303eb7a52ac54aec9dff734a78d76798e3b`. Both are byte-for-byte preserved. The [new machine-readable checkpoint](ISSUE_289_CRITICAL_SEMANTICS_CHECKPOINT.json) overlays these sources and records the full per-row before/after disposition and runtime `57b01e4af5cd15a995e527da26cc7f017441a8df030d66a64bb189159198d72f`. The old Combined 007 runtime is `d4466241f0ffeaca809cd6a05210ad53b9af1011a1d7f833de88657c1cf00924`: neither earlier control is runtime-compatible.

| Classification | At #293 | This checkpoint |
|---|---:|---:|
| Critical P0 | 55 | **50** |
| Important P1 | 71 | **71** |
| Supported by current overlays | 6 | **11** |
| Gaps | 123 | **118** |
| Partial | 3 | **3** |
| Existing covered / annotation | 33 / 7 | **33 / 7** |

**Generic hand counterspell:** The interpreter accepts the *complete* instant clause `Counter target spell.` or `Counter target noncreature spell.` without a follow-up effect. Legal hand responses use payment, current priority, stack target identity and creature filtering, permit a spell below the top of the stack, give priority to the caster, and counter through ordinary stack-to-graveyard movement. Target departure causes a no-effect resolution. Both frozen Negate ledger rows close. Compound counter-plus-draw remains unsupported; a conformance fixture was changed to that still-unsupported grammar so it continues checking opportunity witnesses.

**Generic conditional evasion:** The printed clause `This creature can't be blocked if an artifact entered the battlefield under your control this turn.` uses the attacker's live ability text and the entry turn/controller preserved on permanent incarnations. Any artifact card or token that entered under that controller counts even if it subsequently leaves; an artifact entering under an opponent's control does not become qualifying after a control change. All three frozen Fugitive Droid ledger rows close, across April, Donatello, and Krang. No card or deck name drives the rules path.

Focused tests exercise the frozen catalog facts, renamed fixtures, legal/illegal priority choices, noncreature restriction, mana insufficiency, nested counter war, targeting a lower stack spell, departed target, artifact token entry and departure, control change, ability loss, turn boundary, invariants, and exact snapshot/event replays. The two mirrored April/Krang diagnostic games each matched a deterministic replay without errors ([machine smoke evidence](ISSUE_289_CRITICAL_SEMANTICS_SMOKE.json)); neither game resolved a counterspell, so those games establish integration stability, while the focused tests establish actual execution. Full regression: **1,680 passed, 10 skipped**; a subsequent additional token/ability-loss test passed with the focused evasion suite (**5 passed**). Ruff check/format and diff checks pass. The unchanged Baseline 005 structural validator passes; its old console sentence about land totals is stale and is not treated as provenance.

## Remaining intervention order

The P0 rows are per-deck clauses or scanner reasons, not independent bugs. The following order weights live gameplay consequences, copies, shared work, and the danger of silently treating an unavailable action as a weak deck.

1. **Mana and land entry (5 P0 rows).** B&R's two Illegitimate Business copies currently enter untapped, omit their life trigger, and only offer black where the land says black or green. Correct general tapped-entry replacement, land ETB life trigger, and multi-output payment selection as one resource-semantic family. A partial green mode remains a critical row. This checkpoint inspected the paths but did not claim a partial fix: land ETB currently uses creature-entry trigger provenance, while payment treats a land as a single color.
2. **Shared spells and removal (18 interaction P0 rows plus related casting/board rows).** Stomped by the Foot occurs in three decks, with seven total copies; Cowabunga! in two decks, six copies; Mutant Chain Reaction in two decks, five copies; Spicy Oatmeal Pizza across Raphael/Casey with five copies and multiple missing target/self-damage reasons. Implement target, modal, kicker, counter/token, and draw/selection families only where their full Oracle clause and timing can execute.
3. **Deck identity and combat.** Raphael's linked exile/attack-play fails when its source leaves; Cool but Rude's attack filter/discard damage affects four copies. B&R's four commander copies have no attack/block sacrifice-or-discard obligation. April Hacktivist's end-step typed-spell draw remains missing. Shredder attack damage draw/life, Raphael must-block, and Leonardo Katana's granted combat trigger remain significant. Verify stack independence, choices and zones across these shared trigger families.
4. **Casting and resource filters.** Krang's artifact affinity, Michelangelo's reduced-cost protection, and Casey's restricted red mana can change whether spells are cast at all. Address these before trusting absence-of-use observations.

Remaining P0 family counts: combat 11, resource 8, linked exile 2, interaction 18, token 1, board/zone 2, casting 3, mana 5. The 71 P1 rows are still materially important: class identity 24, combat 14, board/zone 14, tokens 12, resources 4, casting 3. The three partial rows include the land green mode and two Raphael linked effects. The complete machine ledger is the authoritative row-level list.

**Next highest-value intervention:** general land entry and mana-source choice, with deterministic land/cost/trigger tests, then refresh the ledger and runtime identity. This checkpoint does not authorize the control. Design Studio should use the mechanical gap inventory as diagnosis, not as balance evidence or a deck-revision request.
