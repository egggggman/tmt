# Issue 289 — rebuilt shared removal checkpoint

**Checkpoint acceptance: READY for independent HQ review after CI.** **Baseline 005 calibration: BLOCKED.** This draft stacks directly on [PR #296](https://github.com/egggggman/tmt/pull/296), commit `987bddc770225c0dd001acdea9801f1bcd24eb54`. It is a reconstruction from durable source, not an assertion that its runtime or test count equals the lost local checkpoint. No deck list, frozen catalog, previous checkpoint, historical result, or control was modified.

## Provenance and coverage

- Original [172-row ledger](ISSUE_289_COVERAGE_LEDGER.csv): SHA-256 `56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100`.
- Parent [shared interaction checkpoint](ISSUE_289_SHARED_INTERACTION_CHECKPOINT.json): SHA-256 `5b581fdf101822dd504dd44134fbc8d0c7fccafe89b7b8d2c816bf267b1d0167`; parent runtime `5a7b948a7c6745971bfb9d66471aee4a369363ff944f2926fad0536700f7aed3`.
- Rebuilt runtime: see the exact `semantic_runtime_sha256` in the [complete row overlay](ISSUE_289_SHARED_REMOVAL_CHECKPOINT.json) and [diagnostic replay evidence](ISSUE_289_SHARED_REMOVAL_SMOKE.json). Both are generated from the modified source, with no inherited lost-run hash.

| Row classification | #296 parent | Rebuilt checkpoint |
|---|---:|---:|
| Critical P0 | 41 | **33** |
| Important P1 | 68 | **68** |
| Partial | 2 | **2** |
| Gaps | 107 | **99** |
| Supported by overlays | 23 | **31** |
| Prior covered / annotation | 33 / 7 | **33 / 7** |

An independent row comparison confirmed exactly **eight P0 closures** and **164 unchanged rows**: three Spicy Oatmeal Pizza entries in Raphael, three in Casey Jones, one Mutant Chain Reaction entry in Michelangelo, and one in Bebop & Rocksteady. The previous 172 rows retain their identities and order. The reporter also checks the original ledger hash, parent checkpoint hash and runtime, and each Oracle clause against the interpreter's executable coverage.

## Scope and mechanical evidence

- An artifact entering with the parsed “deals N damage to any target and M damage to you” text places a trigger on the stack. Legal creature or player targets are chosen as the trigger is stacked. Priority passes before resolution. The engine rechecks the target; if all targets are illegal, neither damage instance occurs. If legal, both damage instances are applied before state-based/life checks. The original immutable entry event anchors damage if the source leaves first.
- A sorcery with the parsed optional destroy and token clause uses normal mana payment, optional legal artifact/enchantment/flying-creature targeting, a stack object, legality recheck, destruction with indestructibility respected, and the existing parsed token program. An invalidated chosen target counters the entire effect; declining the target still creates the token. Noncreature artifact tokens now generate permanent-entry events and can trigger an existing artifact-entry ability.
- Simultaneous lethal life loss yields a terminal draw with two loss events and one draw event. Its authoritative fingerprint, serialized snapshot, game loop, and Stage 02 terminal checker agree; historical non-draw fingerprint tuples remain unchanged.
- No card-name or deck-name execution branch was added. The pilot's removal choice is based on the Oracle action fragment and observed opposing battlefield state.

Focused tests cover renamed cards, grammar rejection, legal/illegal targets, optional decline, zone change, indestructibility, source removal, priority timing, both damage instances, simultaneous draw, artifact-entry triggers, invariants, and byte-deterministic replay (**16 passed**). The complete regression passed **1,714 tests, 10 skipped**. The four mirrored frozen-deck diagnostics and four exact replays completed with zero runtime errors. Two Pizza resolutions occurred in Casey's orientation; one Chain resolution occurred in each B&R/Michelangelo orientation. Raphael's orientation exercised neither effect, so the focused tests are the direct proof for those branches. These games are diagnostic only and convey no balance estimate.

The unchanged Baseline 005 structural validator, repository Ruff check and format, and diff checks passed. Its historical console sentence about a 24→22 land count is stale prose and was not used as deck provenance. GitHub CI results are verified on the stacked PR after publication.

## Remaining readiness

The 33 critical entries, 68 important entries and two partial entries still require their own mechanical assessment. Severe identity gaps remain around Raphael's linked exile/play permission, B&R's attack/block obligation and April Hacktivist's end-step draw. The existing Baseline 005 control has an incompatible semantic runtime. HQ has not authorized a fresh 4,500-game control; no control or balance batch was run. Design Studio owns any future deck changes.
