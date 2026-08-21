# Post-Action-#9 Cardcade Action Coverage

Status: **EVIDENCE ONLY**  
Date: 2026-08-20  
Audited merged main: `8cb8c3a12e4d411eaa4e65101268be406679b785`  
Merged PR: `#39`  
Accepted Action: bounded optional Hand-bottom filtering followed by conditional Draw

## Purpose and boundaries

This report recomputes the next missing reusable Action from the integrated post-Action-#9
baseline. It does not implement Action #10, change a deck, create Prototype 0.3, tune a Pilot,
calibrate gameplay, or run smoke testing.

Accepted Create Token, Deal Damage, Scry, First/Double Strike damage steps, Activated-Ability
delivery, Targeted Return, Trample, Lifelink, and Action #9 payloads are not counted again when an
unsupported parent, cost, choice, trigger, permission, target structure, or follow-up is the actual
limitation.

## Merge and baseline integrity

PR #39 was squash-merged as `8cb8c3a12e4d411eaa4e65101268be406679b785`.
There were no intervening commits after its exact parent
`4c15424494cb0de6869537d31fc2f14881711295`. The PR diff contained only the post-Lifelink
coverage checkpoint, bounded Action #9 implementation/tests, and its REJECT/ACCEPT evidence.

The committed report blobs preserve:

- Audit #1 REJECT SHA-256:
  `8b40060aed4a6850d9776d0face5c42e95c85a2314b63b443ca83d17fcee1d44`;
- Audit #2 ACCEPT SHA-256:
  `3ad2106e53654116a3e0905d0a6d1528e99d329f8505e069d5cc7141fabe4158`.

Merged-main GitHub Actions run `32438120854` passed.

## Integrated validation

- full suite: **437 passed / 1 skipped**;
- Action #9: **22 passed**;
- Action #9 + SemanticCoverage + card data + Deal Damage: **61 passed**;
- broader library/Stack/cost/Priority/identity/SBA/combat regressions: **192 passed**;
- Ruff format check: clean;
- Ruff check: clean;
- `git diff --check`: clean before this evidence-only report;
- Action #9 membership digest:
  `cb1c664c8b157f87bace7c9a2012bb69ab598e1d142cc6a2024e532575b443e8`.

## Merged Acceptance evidence

Each seed was run twice from merged main and produced byte-identical output.

| Seed | Winner | Ending turn | Action #9 transactions |
|---:|---|---:|---:|
| 7001 | Raphael | 14 | 1 |
| 7002 | Raphael | 20 | 1 |
| 7003 | Leonardo | 19 | 1 |
| 7004 | Leonardo | 21 | 0 |
| 7005 | Raphael | 16 | 1 |
| **Aggregate** | | | **4** |

The integrated residual surface is **37 unsupported events / 13 exact pairs**, with **1** block
restriction rejection and **0** invariant violations.

## Exact residual attribution

| Actual missing capability | Events | Pairs | Exact Acceptance exposure |
|---|---:|---:|---|
| Sneak casting transaction | 17 | 5 | Big Brother 7; Leader in Blue 5; Cutting Edge 2; Sewer Samurai 2; Nightwatcher 1 |
| Optional Discard then conditional Draw under attack trigger | 4 | 1 | Null Group Biological Assets 4 |
| Alliance modal choice and temporary keyword grant | 4 | 1 | Wingnut 4 |
| Exile/graveyard/play permissions | 6 | 3 | Sewer Samurai graveyard/finality 2; Raphael exile-top 2; Raphael play-exiled 2 |
| Menace / multiple-blocker legality | 2 | 1 | Raphael, Most Attitude 2 |
| Look/reveal/type-filtered selection and ordered remainder | 2 | 1 | Casey Jones, Jury-Rig Justiciar 2 |
| Food activation/use | 2 | 1 | Lita Food reminder 2 |
| **Total** | **37** | **13** | |

No Manhole Missile pair remains. Its four accepted Action #9 transactions are execution evidence,
not residual Draw exposure.

Trigger delivery is the parent of 12 residual events across four pairs: Null Group 4, Wingnut 4,
Raphael exile-top 2, and Raphael play-exiled 2. It is not charged as a separate child payload, and
generic trigger delivery alone would complete none of the latter three semantic families.

## Fresh authoritative census

The census was rerun against all **332 unique Oracle objects** in the immutable 472-print
TMT/PZA/TMC snapshot and the canonical **102-card / 10-deck** frozen roster. Counts below are
recognition/reach evidence, not support claims.

| Semantic family | Full-pool exposure | Frozen exposure | Dependency state after Action #9 |
|---|---:|---:|---|
| Draw references | 54 objects / 54 fragments | 18 cards / 7 decks | Draw movement exists, but each surrounding instruction still needs truthful delivery and conditions |
| Exact optional Discard then Draw wording | 2 / 2 | 2 cards / 2 decks | Cool but Rude and Null Group; only Null Group is directly exposed in Acceptance |
| Action-shaped Discard semantics | 16 / 19 | 10 cards / 6 decks | Hand identity/choice exists; Hand→Graveyard and trigger delivery remain missing for the exposed path |
| Sneak | 27 / 32 | 18 mechanic-bearing cards / 6 decks | Requires special timing, return-as-cost, alternate/additional payment, and tapped-attacking entry |
| Direct trigger language | 171 / 200 | 54 cards / 10 decks | Typed events/trigger objects exist, but delivery and child semantics remain deliberately bounded |
| Direct exile/play/graveyard instructions | 25 / 27 | 5 cards / 5 decks | Heterogeneous permission, duration, replacement, and tracked-object requirements |
| Menace | 17 / 18 | 6 cards / 4 decks | Requires authoritative multiple-blocker enumeration and combat assignment expansion |
| Food activation/reminder | 5 / 5 | 3 cards / 3 decks | Requires mana/tap/sacrifice cost composition, token cessation, and life gain |
| Look/reveal-to-hand selection | 3 / 3 | 2 cards / 4 decks | Requires hidden selection, type filter, reveal, movement, and ordered/random remainder handling |
| Equipment/equip or attachment semantics | 15 / 40 | 6 cards / 6 decks | No direct residual pair; attachment state and equip costs remain substantial work |

Broad text scans were also used as false-negative controls: 148 objects contain target/choice
language and 42 contain some exile/graveyard/play reference. Those broad counts are intentionally
not promoted to Action coverage because many are costs, reminders, permissions, or compound text.

The seven context-sensitive UNKNOWN objects remain Arcane Signet, Chromatic Lantern, Command
Tower, Double Jump // Flying Kick, Exotic Orchard, Fast Forward, and Plague of Vermin. Action #9
provides no basis to reclassify them.

## Re-ranked Action candidates

| Rank | Candidate | Direct Acceptance leverage | Readiness, reach, impact, and complexity |
|---:|---|---|---|
| 1 | **Bounded optional Discard followed by conditional Draw, delivered by an attack trigger** | **4 events / 1 complete pair** | Action #9 already supplies private immutable hand choice, conditional sequencing, Draw identity/evidence, and deterministic choice. The engine already emits authoritative attackers-declared events and has typed trigger/Stack machinery. The new bounded work is Hand→Graveyard movement plus generic delivery of the exact attack-trigger parent. Two exact Oracle objects establish reuse beyond one card. Medium complexity and immediate card-flow/gameplay impact. |
| 2 | Sneak casting transaction | 17 / 5 | Highest raw pressure and 27-object reach, but still combines a Declare Blockers casting window, alternate/additional cost, return of an unblocked attacker as cost, Stack/Priority handling, and tapped-and-attacking entry. Very high complexity and several YELLOW extensions. |
| 3 | Menace / multiple blockers | 2 / 1 | Completes a pair and has 17-object reach, but widens legal block enumeration, blocker ordering, combat assignment, Trample, and strike-step interactions. High architectural complexity. |
| 4 | Trigger-delivery expansion | Parent of 12 / 4 | Exceptional 171-object reach and strong dependency leverage. As a delivery-only checkpoint it completes no pair unless paired with Discard/Draw, modal grants, or exile permissions; the bounded rank-1 slice proves it through one concrete generic child. |
| 5 | Alliance modal keyword grant | 4 / 1 | Good direct leverage, but requires modal choice plus temporary Flying/Menace/Haste semantics; Menace itself still needs multiple-blocker support. |
| 6 | Exile/graveyard/play permissions | 6 / 3 | Valuable exposure, but the three pairs require different permissions, durations, replacement effects, and tracked identities rather than one honest bounded Action. |
| 7 | Food activation/use | 2 / 1 | Activated delivery and token identity exist, but Acceptance has no Food creation transaction. Sacrifice-cost composition, token cessation, and life gain are still required. |
| 8 | Casey look/reveal selection | 2 / 1 | Completes one pair only through hidden-information choice, artifact filtering, reveal, Hand movement, and random/ordered library-bottom handling. |
| 9 | Generic Draw classification | Child of 4 / 1 | Broad 54-object reach, but the engine already performs the represented fixed Draw. Classifying Draw alone would not deliver Null Group's attack trigger or optional Discard condition and therefore would remove no pair truthfully. |
| 10 | Equipment/equip | 0 direct | Meaningful roster reach but no direct `37/13` evidence and major attachment/cost/state dependencies. |

Raw event count is not the score. Sneak remains the largest residual surface, but its five pairs
are one compound mechanic with several missing architectural prerequisites. Conversely, the
rank-1 candidate closes a real pair through an already-observed attack parent while reusing the
choice, sequencing, Draw, zone identity, Stack, event, and immutable-evidence foundations now on
main.

## Action #10 recommendation

Implement a reusable, Oracle-derived **bounded optional Discard followed by conditional Draw under
an authoritative attack trigger**.

The interpreter should recognize the exact compound child independently of its trigger parent and
populate generic `SemanticCoverage`. The engine should detect the supported attack event, create
and stack the represented trigger, then at resolution offer immutable current-hand choices plus
decline. A selected authoritative hand object should move to its owner's graveyard as a new object;
only a successful move should cause the fixed Draw. The engine must preserve trigger/source
identity, ordering, Priority/pass boundaries already represented, transactional child behavior,
and reconstructive before/after evidence analogous to Action #9.

The initial bounded executable member should be Null Group Biological Assets. Cool but Rude's
identical child wording should be recognized, but its Class/level parent must remain explicitly
unsupported unless independently justified. This preserves card-name independence without
claiming Class support.

Keep unsupported semantics explicit: discard as a cost, random or opponent-chosen discard,
multiple-card and variable discard/Draw, discard payoffs, replacement effects, broader attack
triggers, Class leveling, and unrelated Draw instructions.

This recommendation outranks Sneak because it completes one observed pair with a small generic
extension of accepted Action #9 and existing attack-trigger foundations. It outranks generic
trigger expansion and generic Draw because neither alone completes the exposed fragment. It
outranks Menace, Food, and Casey selection because it avoids widening combat topology,
nonmana-sacrifice cost composition, or multi-stage hidden library selection.

No Action #10 implementation is included.
