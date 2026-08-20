# Cardcade Post-Activated-Ability Action Coverage

## Status

- Evidence date: 2026-08-20
- Audited branch: `main`
- Audited HEAD: `0c9018b7a4f3472bfe2af05b486c5d2ec3d2d489`
- Source integration: PR #35, squash-merged as
  `0c9018b7a4f3472bfe2af05b486c5d2ec3d2d489`
- Scope: evidence-only merged-baseline verification and Action #6 re-ranking after
  Engine 0.8, Create Token, Deal Damage, Scry, First/Double Strike, and bounded
  Activated-Ability Announcement / Delivery

This report changes no engine behavior, tests, decks, prototypes, pilots, calibration, or
smoke evidence.

## PR #35 integration

`main` advanced after the Action #5 branch point only through PR #34. That intervening diff
changed repository orientation/continuity documents (`NOTICE`, `README.md`,
`PROJECT_STATE.md`, `docs/HQ.md`, and new continuity/status documents); it did not touch
Cardcade, Engine 0.8, or Actions #1–#4. GitHub reported PR #35 `MERGEABLE / CLEAN`, its two
pre-merge test checks passed, and a merge-tree inspection found no conflict.

The PR diff contained exactly the post-Strike evidence checkpoint, the bounded activated
ability implementation and tests, and Acceptance Audit #1/#2 history. The established squash
convention produced:

- PR #35 merge commit: `0c9018b7a4f3472bfe2af05b486c5d2ec3d2d489`
- resulting local `main`: `0c9018b7a4f3472bfe2af05b486c5d2ec3d2d489`
- resulting `origin/main`: `0c9018b7a4f3472bfe2af05b486c5d2ec3d2d489`
- merged-main GitHub Actions: Test run `32390628774`, **success**

## Merged baseline verification

| Check | Result |
| --- | --- |
| Full suite | `344 passed / 1 skipped` |
| Activated Ability / Priority | `30 passed` |
| Stack / cost / boundary | `23 passed` |
| Strike / combat / state | `77 passed` |
| Generic SemanticCoverage | `5 passed` |
| Card-data integrity | `5 passed` |
| Ruff format check | clean; 39 files |
| Ruff check | clean |
| `git diff --check` | clean before this report |
| Duplicate Acceptance seeds | byte-equivalent |
| Final Priority/stack leak probe | 0 / 5 games |

The committed Git blob and LF-normalized checkout content for historical REJECT #1 retain
SHA-256 `7021a0f74a2b79d75ecffaf7d744d5c8f80cc816a43b4b09b139babf3721ff83`.
Windows `core.autocrlf` materializes CRLF in the working checkout; the platform-specific raw
working-tree hash is not the preservation contract.

Activated-Ability membership remains locked:

- recognized: 131 Oracle objects / 156 fragments;
- frozen recognized: 45 cards across all 10 decks;
- bounded executable and fully supported: 1 object / 1 fragment;
- recognized digest:
  `35ccf2712e06f6cd0b93d03dbb867e909a6c8350e3e84616d0cee9b14f067190`;
- executable/full digest:
  `9c019f17c42f36208edf15d43eb29b10f2470a3fbcc5019c7c022a74945235f3`;
- seven context-sensitive UNKNOWN objects unchanged.

## Merged Acceptance evidence

Seeds 7001–7005 were each executed twice:

| Seed | Winner | Ending turn | Unsupported events |
| ---: | --- | ---: | ---: |
| 7001 | Raphael | 16 | 10 |
| 7002 | Leonardo | 19 | 17 |
| 7003 | Leonardo | 19 | 12 |
| 7004 | Leonardo | 21 | 16 |
| 7005 | Raphael | 16 | 14 |

Aggregate evidence:

- 69 unsupported events / 17 exact card–Oracle-fragment pairs;
- 8 activation announcements, cost payments, ability stack placements, resolutions, and
  temporary First Strike grants;
- 16 Priority grants and 16 PASS actions;
- 8 Scry transactions;
- 16 Deal Damage transactions;
- 6 block-restriction rejections;
- 0 invariant violations;
- byte-equivalent duplicates;
- empty final stack and no Priority state in every game;
- focused regressions confirm no Priority/pass state survives into combat, later phases,
  cleanup, or another turn.

The old `61 / 18` and current `69 / 17` are not competing coverage scores. Five broad
Leonardo activation events and their pair disappeared. Six Prehistoric Pet exposures now emit
three precise limitations each instead of one broad report, adding twelve events without adding
a pair. A legitimate longer trajectory adds one occurrence of the existing Lita Food pair.
Coverage improved even though the raw event count rose.

## Exact residual attribution

Each exact pair is assigned once to the capability that actually remains missing. Supported
Create Token, Deal Damage, Scry, Strike, and activation-parent semantics are not counted again.

| Primary missing capability | Underlying exposures | Telemetry events | Pairs | Exact residual |
| --- | ---: | ---: | ---: | --- |
| Sneak casting transaction | 20 | 20 | 5 | Leonardo Big Brother 9; Leader in Blue 5; Sewer Samurai 3; Cutting Edge 2; Nightwatcher 1 |
| Targeted Return to Hand after supported activation | 6 | 18 | 1 | Prehistoric Pet; each exposure reports missing child, target/choice, and timing boundaries |
| Other combat keyword slices | 12 | 12 | 4 | Trample 5; Wingnut modal flying/menace/haste 3; Lifelink 2; Menace 2 |
| Discard or Hand→Library-bottom followed by Draw | 8 | 8 | 2 | Null Group Discard→Draw 4; Manhole optional bottom→Draw 4 |
| Exile / play-from-zone / graveyard permission | 7 | 7 | 3 | Sewer Samurai graveyard/finality 3; Raphael exile-top 2; play-exiled permission 2 |
| Triggered top-card selection | 2 | 2 | 1 | Casey look-four/reveal/artifact selection/Hand/random-bottom sequence |
| Food activation/use | 2 | 2 | 1 | Lita's created Food; activation shell exists, but sacrifice/tap/life-gain use does not |
| **Total** | **57 underlying fragment exposures** | **69** | **17** | Precise multi-reason telemetry explains the event/exposure difference |

The 17 exact pairs are therefore fully reconciled. Activated-ability delivery is not a
residual family: Leonardo executes, while Prehistoric and Food are attributed to the missing
target/effect/timing and token-use/cost/effect semantics that now block their supported parent.

## Current evidence universe

The authoritative universe remains:

- 472 print records / 332 unique Oracle objects;
- 102 unique frozen-roster cards / all 10 decks;
- accepted Engine 0.8 foundations and five accepted post-foundation capabilities;
- generic SemanticCoverage separation of parent, cost, target/choice, payload, follow-up,
  full support, and limitations;
- seven UNKNOWN objects: Arcane Signet, Chromatic Lantern, Command Tower,
  Double Jump // Flying Kick, Exotic Orchard, Fast Forward, and Plague of Vermin.

A fresh current-snapshot lexical/semantic census found:

| Family | Full-pool objects / fragments | Frozen cards / decks | Qualification |
| --- | ---: | ---: | --- |
| Draw | 54 / 54 | 17 / 7 | Fixed, variable, conditional, replacement, and compound draws overlap |
| Discard | 16 / 19 | 10 / 6 | Costs, effects, random discard, and conditions overlap |
| Hand→Library-bottom filtering | 1 / 1 | 1 / 2 | Manhole Missile's distinct optional movement |
| Return-to-Hand language | 36 / 37 | 18 / 8 | Targets, costs, self-return, mass return, and conditions overlap |
| Direct leading trigger forms | 166 / 190 | 51 / 10 | Existing supported trigger shapes are included and must not be recounted |
| Sneak | 27 / 32 | 18 / 6 | Compound alternate casting mechanic |
| Equip/attach language | 15 / 21 | 6 / 7 | Equipment, attachment, targets, and continuous effects overlap |
| Target/choice language | 148 / 183 | 49 / 10 | Broad exposure, not one executable Action family |
| Food creation/use language | 8 / 8 | 3 / 3 | Creating Food remains distinct from using it |
| Mutagen creation/use language | 19 / 20 | 10 / 5 | Creating Mutagen remains distinct from using it |
| Activated target/choice limitation | 26 / 26 | — | Interpreter-classified activation fragments |
| Activated nonmana-cost limitation | 34 / 38 | — | Includes sacrifice and other distinct costs |
| Activated timing limitation | 6 / 6 | — | Includes restrictions not implemented generically |

These are exposure counts, not executable coverage claims. Rows overlap and cannot be summed.

## Re-ranked missing capabilities

Ranking prioritizes directly reachable Acceptance evidence and now-supported parent/child
dependencies, then roster/pool reach, gameplay impact, complexity, YELLOW-foundation work, and
dependencies on still-missing semantics.

| Rank | Missing reusable capability | Direct Acceptance leverage | Frozen / full-pool reach | Dependency leverage and gameplay impact | Complexity and foundation work |
| ---: | --- | --- | --- | --- | --- |
| **1** | **Targeted Return to Hand** | **6 actual Prehistoric activations / 1 pair; 18 telemetry events are three reasons per exposure, not 18 transactions** | **18 cards / 8 decks; 36 objects / 37 fragments with return-to-Hand language** | The activation parent, fixed mana/tap payment, authoritative source, stack, and Priority are now implemented. A bounded “another target creature you control” selection plus Hand destination and during-your-turn validation creates the first newly executable consumer of Action #5. Also supplies a prerequisite for Sneak while preserving return-as-effect vs return-as-cost. | Medium. Extend **Choices vs Targets**, **Zones**, **Events**, and **Invariants** for authoritative target identity and new-object movement; classify the represented timing restriction. Existing stack/cost/priority machinery is reusable. Mass return, opponent targets, self-return, costs, and compound follow-ups remain separate. |
| 2 | Draw Cards | 8 / 2 compound pairs contain Draw, but Draw alone clears neither | 17 / 7; 54 / 54 | Broad, relatively low-risk child effect; required by Null Group and Manhole once their distinct parents/movements exist. Existing turn/opening draw and empty-library seams reduce risk. | Low–medium. Add a generic fixed-quantity transaction, zone/event evidence, and SemanticCoverage. Still depends on Discard or Hand→Library-bottom plus trigger/choice sequencing for current telemetry. |
| 3 | Trigger-delivery expansion | 13 / 5 residual pairs have trigger parents, but none has a complete child sequence | 51 / 10 direct-leading cards; 166 / 190 pool fragments | Highest cross-cutting parent reach and many accepted Token/Damage/Scry children exist behind incomplete trigger contexts. Current Acceptance triggers still require selection, Discard/Draw, exile/permission, or modal keyword effects. | High. Extend represented event conditions, ordering, stack delivery, targets/choices, and explicit APNAP/Priority limits one trigger shape at a time. A shell alone clears no current pair. |
| 4 | Discard and Hand→Library filtering | 8 / 2; both require Draw and optional sequencing | Discard 10 / 6 and 16 / 19; hand-bottom 1 / 2 and 1 / 1 | Direct partner for Draw and meaningful hand/graveyard play. Null Group and Manhole have different destinations and must not be approximated as one move. | Medium. Extend Choices, Zones, Events, and Invariants. Null Group also needs attack-trigger delivery; Manhole is an optional follow-up to accepted damage. |
| 5 | Target/choice expansion | Prehistoric's 6 exposures are the immediate bounded slice; Wingnut and Casey also depend on choices | 49 / 10; 148 / 183 lexical fragments; 26 / 26 activation-limited fragments | Cross-cutting dependency for already-supported activation, token, damage, and Scry payloads. It is valuable only when paired with an actual bounded child Action. | Medium–very high by target class. Extend immutable options, hidden/public views, identity revalidation, and atomic failure. Avoid claiming “generic targeting” from one creature-control slice. |
| 6 | Food activation/use | 2 / 1 after a supported Create Token result and supported activation shell | Food language 3 / 3 frozen; 8 / 8 pool | Newly promoted by Action #5: the missing work is now tap/sacrifice payment and life gain, not activation delivery or token creation. Meaningful token gameplay but narrow current evidence. | Medium–high. Extend nonmana Costs, Zones/token cessation, Events, Triggers/SBAs, and Life Gain. Food use must not imply Mutagen/Treasure/Clue support. |
| 7 | Nonmana activation costs | Food contributes 2 / 1; Prehistoric's `{T}` cost is already represented | 34 objects / 38 activation fragments | Unlocks Food, Mutagen, Treasure, Clue, sacrifice, discard, counter-removal, and other abilities after their child semantics exist. | High. Each cost component needs transactional rollback and zone/identity evidence. A generic cost shell cannot execute missing children. |
| 8 | Sneak casting transaction | 20 / 5, largest raw residual family | 18 / 6; 27 / 32 | Major Turtle/Ninja gameplay impact; Action #5 supplies only part of its Priority need, and Return to Hand would remove another prerequisite. | Very high. Still requires Declare Blockers casting permission, alternate/additional costs, return-as-cost, attacker identity, tapped-and-attacking entry, Stack, combat state, and cleanup. Raw count does not outweigh dependency depth. |
| 9 | Other combat keyword slices | 12 / 4 | Trample and other keyword reach varies by slice | Trample 5/1 is the largest bounded residual keyword and affects combat materially. Lifelink, Menace, and Wingnut's modal grant are separate rules boundaries. | Medium–high by slice. Trample needs damage assignment; Menace needs broader blockers; Lifelink needs damage-result life gain; Wingnut needs trigger/choice/duration support. |
| 10 | Equipment / equip | No direct residual equip pair; Wingnut's grant is not Equipment | 6 / 7; 15 / 21 | Broad persistent-modifier and attachment gameplay, with possible accepted strike children behind Equipment text. | High. Requires attach targets, activated equip timing/costs, battlefield attachment identity, continuous effects/layers, zone departure, and control semantics. |
| 11 | Mutagen activation/use | No current Acceptance pair | 10 / 5; 19 / 20 language exposure | Create Token recognizes/creates applicable token shapes, and Action #5 supplies a future activation parent. The use effect still needs sacrifice, target choice, and counters. | High. Requires nonmana Costs, token cessation, targets, counters/layers, and timing. It does not outrank exercised Return-to-Hand or Food. |

Casey-style selection, exile/play permissions, graveyard casting/finality, counterspells,
control changes, copies, search/shuffle, mill, and other lower-immediate-leverage families remain
explicit. None is silently absorbed into the ranked families.

## Why Action #6 changes from the old queue

### Newly executable dependency path

Before Action #5, Prehistoric Pet was blocked at the activation parent and could not usefully
exercise a Return Action. Now its announcement, `{1}{W}` plus `{T}` payment, source/controller
identity, stack object, pass cycle, and resolution boundary exist. Its six Acceptance exposures
are blocked specifically by three remaining semantic layers: target/choice, during-your-turn
classification, and the Return-to-Hand child. A tightly bounded Action can implement those
together without claiming every target or every return form.

### Versus Draw

Draw is broader and cheaper, but clears zero current Acceptance pairs alone. Null Group still
needs an attack-trigger parent, optional Discard, and “if you do” sequencing. Manhole still needs
an optional Hand choice and Hand→Library-bottom movement. Targeted Return to Hand can produce six
real activation transactions immediately through already-accepted parent infrastructure.

### Versus trigger delivery

Trigger language has much larger raw reach, and accepted children remain behind incomplete
trigger contexts. Yet every residual Acceptance trigger also requires a missing child sequence:
selection, Discard/Draw, exile/permission, or modal keyword choice. Expanding the trigger shell
alone clears no pair. Return to Hand has one concrete, fully staged consumer.

### Versus Food, Mutagen, and nonmana costs

Food is now correctly attributed to sacrifice/tap/life-gain use rather than activation delivery,
but it has only two current exposures and requires several foundation extensions. Mutagen has no
Acceptance execution. General nonmana-cost work is cross-cutting but cannot resolve an ability
without its child semantics. Prehistoric's fixed mana/tap costs are already supported.

### Versus Sneak

Sneak retains the largest raw event family, but still spans several inseparable missing systems.
The new bounded Priority seam helps but does not provide Declare Blockers casting, return-as-cost,
alternate cost construction, or tapped-and-attacking entry. Targeted Return to Hand is a smaller,
testable architectural slice that also supplies one of Sneak's future zone primitives without
pretending effect-return and cost-return are identical.

## Action #6 recommendation

**Implement bounded Targeted Return to Hand as Action #6.**

The checkpoint should use Prehistoric Pet as a generic Oracle-derived consumer, not a card-name
case. It should represent only the evidenced “another target creature you control” activation
during its currently legal turn window, with immutable engine-generated target options,
authoritative runtime identity, revalidation, atomic zone movement/new-object semantics, typed
events, stack-delayed delivery, and exact SemanticCoverage.

It must explicitly retain unsupported opponent/self/multiple/mass return forms, return-as-cost,
arbitrary timing windows, triggered returns, bounce follow-ups, Sneak, Draw, Discard, Food,
Mutagen, Equipment, generic targeting, and every unrelated Action.
