# Cardcade Post-Strike-Damage-Steps Action Coverage

## Status

- Evidence date: 2026-08-14
- Audited branch: `main`
- Audited HEAD: `a21167a7680d8025fd0a0a79ed775f3d373d410c`
- Source integration: PR #33, squash-merged as `a21167a7680d8025fd0a0a79ed775f3d373d410c`
- Scope: evidence-only capability reconciliation and Action #5 ranking after accepted Create Token, Deal Damage, Scry, and First Strike / Double Strike combat-damage steps
- Recommendation: **Activated-ability announcement/delivery** is the single highest-leverage Action #5.

This report does not implement an Action or change engine behavior, decks, prototypes, pilots, calibration, or smoke evidence.

## PR #33 integration and merged-main verification

PR #33 was based on `6492ab472e3bc87ee0bb3b05fd9d6a9ef7fa8998`, which was still current `main` at final integration. GitHub reported `MERGEABLE / CLEAN`, both Actions checks passed, and no intervening commit or semantic conflict existed. The PR diff contained exactly:

- the committed post-Scry coverage checkpoint;
- the bounded strike interpreter, combat state machine, acceptance-runner integration, and tests;
- historical Strike Acceptance Audit #1 and final Acceptance Audit #2.

It contained no deck, prototype, unrelated Action, pilot strategy, calibration, or smoke changes. The repository's established squash convention produced:

- PR #33 merge commit: `a21167a7680d8025fd0a0a79ed775f3d373d410c`
- resulting local `main`: `a21167a7680d8025fd0a0a79ed775f3d373d410c`
- resulting `origin/main`: `a21167a7680d8025fd0a0a79ed775f3d373d410c`

Merged validation:

| Check | Result |
|---|---|
| Full suite | `314 passed / 1 skipped` |
| Focused strike suite | `33 passed` |
| Combat/state regressions | `44 passed` |
| Generic SemanticCoverage | `5 passed` |
| Card-data integrity | `5 passed` |
| Ruff format check | clean; 38 files |
| Ruff check | clean |
| `git diff --check` | clean |
| Duplicate Acceptance seeds | byte-equivalent |
| Postcombat state probe | 174 / 174 transitions clean |

Both strike acceptance reports are present. The committed repository blob for historical Audit #1 has SHA-256 `824177f2483558b21a678709e05736b4469cdfe6efff469a5b1c57bd3a9a179e`, identical to the accepted evidence. On Windows, `core.autocrlf=true` materializes CRLF bytes in the working checkout; preservation is verified against the committed blob, not the platform-specific checkout transformation.

## Evidence universe

The ranking reconciles:

- 61 remaining unsupported events / 18 exact card–Oracle-fragment pairs;
- 102 unique frozen-roster cards across all ten decks;
- 472 authoritative print records / 332 unique Oracle objects;
- seven preserved context-sensitive UNKNOWN objects;
- accepted Create Token, Deal Damage, Scry, and strike payloads;
- generic `SemanticCoverage` fields for payload, parent/context, follow-up, full-fragment support, and limitations.

Already-supported child payloads are not counted as missing Actions. When an unsupported parent contains accepted Create Token, Deal Damage, Scry, or strike semantics, the remaining pressure is attributed to the missing parent, target/choice, cost, or follow-up that actually blocks delivery.

## Merged Acceptance Match evidence

Seeds 7001–7005 were each replayed twice from merged `main`:

| Seed | Winner | Ending turn |
|---:|---|---:|
| 7001 | Raphael | 16 |
| 7002 | Leonardo | 17 |
| 7003 | Leonardo | 17 |
| 7004 | Leonardo | 21 |
| 7005 | Raphael | 16 |

Aggregate evidence:

- 61 unsupported events / 18 exact pairs;
- 10 first-strike damage steps / 8 following regular steps;
- 2 terminal first-step combats;
- 2 First Strike assignments;
- 10 Double Strike first-step assignments;
- 2 Double Strike second-step assignments;
- 5 creatures removed between steps;
- 8 Scry transactions;
- 16 Deal Damage transactions;
- 6 block-restriction rejections;
- 0 invariant violations;
- unchanged winners and ending turns;
- byte-equivalent duplicate runs;
- no residual mutable combat state in any audited postcombat transition.

## Exact residual Acceptance attribution

Each exact pair is assigned once to its primary missing capability. Compound fragments list the dependency that prevents a single child Action from clearing the telemetry.

| Primary missing capability | Events | Pairs | Exact fragments and dependencies |
|---|---:|---:|---|
| Sneak casting transaction | 20 | 5 | Leonardo Big Brother 9, Leader in Blue 5, Sewer Samurai 3, Cutting Edge 2, Nightwatcher 1; requires alternate/additional cost, Declare Blockers timing, return cost, and tapped-and-attacking entry |
| Other combat keywords/keyword choice | 12 | 4 | Trample 5/1, Wingnut flying/menace/haste choice 3/1, Lifelink 2/1, Menace 2/1 |
| Return/exile/play-from-zone | 13 | 4 | Prehistoric activated bounce 6/1, Sewer Samurai graveyard/finality 3/1, Raphael exile-top 2/1, play-exiled permission 2/1 |
| Discard or hand-bottom followed by Draw | 8 | 2 | Null Group optional attack-triggered Discard→Draw 4/1; Manhole optional Hand→Library-bottom→Draw follow-up 4/1 |
| Activated First Strike delivery | 5 | 1 | Leonardo, Leader in Blue fixed-mana self activation; strike combat semantics now exist, but announcement/payment/delivery and temporary grant are absent |
| Casey top-four artifact selection | 2 | 1 | ETB trigger, look/reveal/choose, Hand movement, and deterministic random-bottom ordering |
| Food activation/use | 1 | 1 | activation, mana/tap/sacrifice cost, and life gain; token creation is already supported |
| **Total** | **61** | **18** | |

## Dependency pressure behind accepted children

The accepted Actions expose reusable payloads behind incomplete parents across the full pool:

- Create Token has 35 Oracle objects / 35 fragments with bounded payloads behind unsupported parents; this includes 19 trigger-context and 4 activation-context fragments. Additional conditions, choices, preceding effects, follow-ups, and token-use text remain separately explicit.
- Deal Damage has 7 / 7 bounded payloads behind unsupported parents: 3 trigger contexts, 3 activation contexts, and 1 choice context, with follow-up limitations where present.
- Scry has 5 / 5 bounded payloads behind incomplete context: 3 trigger/preceding contexts, 1 preceding effect, and 1 condition.
- Strike has 5 / 5 partial fragments: one trigger, one attachment, one activation, and two targeted/modal temporary-grant contexts. Leonardo, Leader in Blue is the one activation whose accepted strike rules provide immediate dependency leverage.

These are exposure counts, not a claim that a generic delivery shell can execute every child. A parent is useful only when its event, timing, cost, target/choice, child delivery, and follow-up are all represented.

## Fresh corpus exposure measurements

The authoritative 332-object pool was scanned independently. These lexical exposure counts deliberately include partial and unsupported shapes; they establish reach, not executable coverage:

| Family | Full-pool exposure | Frozen exposure | Qualification |
|---|---:|---:|---|
| Activated-ability syntax | 131 objects / 156 fragments | 45 cards / 10 decks | Includes mana abilities; 94 objects / 104 fragments remain after excluding `: Add` mana forms |
| Trigger language anywhere in fragment | 193 / 234 | 54 / 10 for direct leading trigger forms | Includes nested, delayed, replacement-adjacent, and compound triggers; existing represented triggers are not missing |
| Draw/Draws | 54 / 54 | 18 / 7 | Fixed, variable, conditional, replacement, and compound quantities overlap |
| Discard | 16 / 19 | 10 / 6 | Costs, effects, choices, random discard, and conditions overlap |
| Hand-to-library-bottom filtering | 1 / 1 | 1 card / 2 decks | Manhole Missile's distinct optional movement |
| Return-to-Hand language | 37 / 38 | 19 / 8 | Targets, costs, self-return, and mass return overlap |
| Sneak | 27 / 32 | 19 / 6 | Compound alternate casting mechanic, not a simple zone move |

The seven UNKNOWN objects remain unchanged:

- Arcane Signet
- Chromatic Lantern
- Command Tower
- Double Jump // Flying Kick
- Exotic Orchard
- Fast Forward
- Plague of Vermin

No accepted strike evidence resolves their context-sensitive casting, mana, split-card, variable-choice, or replacement questions.

## Re-ranked missing reusable capabilities

Ranks reflect reachable Acceptance leverage first, then dependency leverage, roster/pool reach, gameplay impact, complexity, YELLOW-foundation extensions, and dependencies on other missing Actions. Rows overlap and must not be summed.

| Rank | Missing capability | Direct Acceptance leverage | Frozen / full-pool reach | Dependency leverage and gameplay value | Complexity and foundation work |
|---:|---|---|---|---|---|
| **1** | **Activated-ability announcement/delivery** | **12 events / 3 activation-parent pairs are exposed. Leonardo's 5 / 1 is the bounded first slice with an accepted strike child; Prehistoric 6 / 1 still needs Return-to-Hand/targeting, and Food 1 / 1 still needs tap/sacrifice/life gain.** | 45 cards / 10 decks; 131 objects / 156 lexical fragments, or 94 / 104 excluding `: Add` mana forms | Newly highest dependency leverage: establishes the reusable player announcement → cost → target/choice → stack → revalidation → delivery path. It can first prove delivery through Leonardo without reimplementing strike combat rules, then serve token, damage, and future effect Actions. | High. Extend YELLOW **Priority**, **Choices vs Targets**, and represented **Costs**, plus Stack/Events/Invariants integration. Action #5 must be tightly bounded; a generic shell must not claim unsupported targets, costs, durations, or children. |
| 2 | Draw Cards | 8 / 2 compound pairs contain Draw, but Draw alone clears neither pair | 18 / 7; 54 / 54 | Broad, low-risk child effect with existing turn/opening draw and empty-library-loss foundations. Required by both residual filtering pairs and many future triggers/activations. | Low–medium. Add Action transaction, SemanticCoverage, zone/event evidence, fixed quantities, and explicit replacement/variable exclusions. Still depends on Discard or Hand→Library movement and parent choice/trigger delivery for current telemetry. |
| 3 | Trigger-delivery expansion | 13 / 5 residual pairs have trigger parents: Null Group 4, Wingnut 3, Casey 2, Raphael exile 2, Raphael play permission 2; none clears from a trigger shell alone | 54 / 10 direct-leading-trigger cards; up to 193 / 234 pool fragments containing trigger language | Largest parent exposure behind accepted children: 19 token, 3 damage, 3 Scry, and 1 strike payloads in the pool. However, the residual Acceptance triggers still need Discard/Draw, keyword choice, selection, exile, or permission Actions. | High. Extend represented Trigger delivery without duplicating already-GREEN infrastructure; requires typed events, conditions, targets/choices, ordering, stack delivery, and explicit APNAP/Priority limits. |
| 4 | Return to Hand | Prehistoric 6 / 1 becomes reachable only with activated delivery; also a core Sneak return cost | 19 / 8; 37 / 38 | Strong dependency leverage across the highest-pressure Sneak family and the second activation pair. A zone Action would also support future bounce and cost semantics. | Medium–high. Extend Zones, identity/new-object handling, targets, transactional costs, events, and invariants. Effect return and return-as-cost must remain distinct transactions. |
| 5 | Discard / hand-to-library filtering | 8 / 2; neither pair clears without Draw and parent/choice sequencing | Discard 10 / 6 and 16 / 19; hand-bottom 1 card / 2 decks and 1 / 1 | Direct partner for Draw and meaningful graveyard/hand gameplay. Null Group and Manhole use different destinations and cannot be collapsed into one approximate move. | Medium. Extend Choices, Zones, Events, and Invariants. Null Group additionally needs attack-trigger delivery; Manhole needs optional sequencing after accepted damage. |
| 6 | Sneak casting transaction | 20 / 5, the largest residual event family | 19 / 6; 27 / 32 | Major Turtle/Ninja gameplay impact and high direct telemetry pressure. It reuses Return-to-Hand and casting foundations once prerequisites exist. | Very high. Requires Priority, alternate/additional Costs, Declare Blockers timing, combat identity, return-as-cost, Stack, targets/choices, and tapped-and-attacking zone entry. |
| 7 | Remaining combat keyword slices | 12 / 4 | Trample 3 cards / 4 decks and 25 / 26 pool fragments; other slices have separate reach | High gameplay impact, but Trample, Lifelink, Menace, and Wingnut's modal keyword grant are four different rules boundaries. Accepted strike steps must not be used to approximate them. | Medium–very high by slice. Trample also needs broader damage assignment; Lifelink needs damage-result life gain; Menace needs blocker-count expansion; Wingnut needs trigger, choice, and duration support. |
| 8 | Casey-style top-card selection | 2 / 1 | broader search/look/reveal family extends beyond this exact shape | Reuses Scry's hidden ordered-library choice boundary but is not Scry: it adds look-four, typed selection, reveal, Hand movement, and random bottom ordering. | High. Extend Choices, Zones, Deterministic RNG evidence, Events, and Invariants after ETB trigger delivery. |
| 9 | Sacrifice and artifact-token use | Food activation 1 / 1 | broad Food/Mutagen/Treasure/Clue and sacrifice exposure | Unlocks use of already-creatable tokens and many future costs. | High. Requires activated delivery, Costs, Zones, Events, Triggers/SBAs, target/choice handling, and effect Actions such as life gain or mana production. |

## Why Activated-ability delivery is now Action #5

### Newly unlocked dependency leverage

Before Action #4, Leonardo's activation had no executable strike combat semantics to deliver. After accepted First Strike / Double Strike, its payload is recognized and bounded-executable while `SemanticCoverage` correctly leaves the activation parent unsupported. That creates the first residual parent capability with a substantial current Acceptance child already implemented: 5 events / 1 pair.

The recommended Action #5 is not permission to implement all 131 lexical activation objects. It should establish a generic, card-name-independent activated-ability transaction and prove the smallest authoritative delivery slice through fixed-mana, self-affecting Leonardo semantics. The temporary keyword grant and duration must be represented explicitly as the delivered strike effect; announcement alone must not suppress telemetry. Prehistoric Pet and Food remain unsupported until their target/zone and tap/sacrifice/life-gain dependencies exist.

### Versus Draw Cards

Draw has greater bounded effect breadth and lower implementation complexity, but it currently clears zero Acceptance pairs by itself. Null Group still needs an attack trigger, optional Discard, and conditional sequencing. Manhole Missile still needs an optional Hand choice and Hand→Library-bottom movement. Activated delivery can reach an accepted strike child immediately and creates a cross-cutting protocol for future Actions.

### Versus Trigger-delivery expansion

Trigger language has the largest raw pool reach, and accepted child payloads sit under many incomplete trigger contexts. Yet every currently residual Acceptance trigger also depends on a missing effect, choice, permission, or movement capability. Expanding trigger delivery generically would therefore clear no pair without broadening scope. Activated delivery has a narrower, evidence-backed first executable path.

### Versus filtering and Return to Hand

Discard/hand-bottom filtering is two distinct movement families and still requires Draw. Return to Hand has strong leverage for Prehistoric Pet and Sneak, but the directly observed Prehistoric pair first requires activated announcement/delivery. Establishing the parent transaction first gives the later Return Action a concrete delivery consumer without conflating return-as-effect and return-as-cost.

## Action #5 boundary recommendation

**Implement Activated-ability announcement/delivery as Action #5.**

The checkpoint should establish a reusable, engine-owned activation lifecycle: authoritative source and controller, timing, represented cost transaction, targets/choices where supported, stack object identity, revalidation, resolution, typed evidence, and generic `SemanticCoverage`. Its first bounded executable slice should be the fixed-mana self activation whose accepted First Strike payload supplies real gameplay semantics.

It must explicitly retain unsupported classifications for:

- Prehistoric Pet until target selection and Return-to-Hand exist;
- Food/Mutagen/Treasure/Clue activation until their tap/sacrifice and effect semantics exist;
- variable, alternative, loyalty, graveyard, multi-target, modal, timing-restricted, and unsupported cost forms;
- trigger delivery, Draw, Discard, Sneak, Trample, Deathtouch, Lifelink, multiple blockers, and unrelated Actions.

Recognition of an activation or an accepted child payload must never imply that its parent, cost, target/choice, follow-up, or full Oracle fragment is supported.
