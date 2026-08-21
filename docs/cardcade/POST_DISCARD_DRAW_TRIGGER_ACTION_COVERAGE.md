# Post-Action-#10 Cardcade Action Coverage

Status: **EVIDENCE ONLY**
Date: 2026-08-20
Audited merged main: `aa2ab361de832103e4accccff489bccd0a1918ce`
Merged PR: `#40`
Accepted Action: bounded optional Discard followed by conditional Draw under an authoritative attack trigger

## Purpose and boundaries

This report recomputes Cardcade's next missing reusable Action from the integrated post-Action-#10
baseline. It does not implement Action #11, change decks, create Prototype 0.3, tune a Pilot,
calibrate gameplay, or run smoke testing.

Accepted Create Token, Deal Damage, Scry, First/Double Strike damage steps, Activated-Ability
delivery, Targeted Return, Trample, Lifelink, hand-bottom/conditional Draw, and
Discard/conditional Draw payloads are not counted again when an unsupported parent, cost,
permission, target structure, choice, or follow-up is the actual remaining limitation.

## Merge and baseline integrity

PR #40 had no intervening-main divergence: its merge base and then-current `origin/main` were both
`8cb8c3a12e4d411eaa4e65101268be406679b785`. Its nine changed files were limited to the
post-Action-#9 evidence checkpoint, Action #10 implementation/tests, and the two preserved Action
#10 acceptance reports. GitHub reported `MERGEABLE / CLEAN` with both PR checks passing before
the authorized squash merge.

PR #40 was squash-merged as `aa2ab361de832103e4accccff489bccd0a1918ce` and local `main`
was fast-forwarded to the same remote HEAD. Merged-main GitHub Actions run `32441796448` passed.

The canonical committed report blobs preserve:

- Audit #1 REJECT SHA-256:
  `8b12b872172d221e3f67af1a095aec8766bd2d66f61db511e311eff575feca48`;
- Audit #2 ACCEPT SHA-256:
  `c851f826fd30b7af953c2a6001a74b217f6dd0c6e16c09768a78ca7382c8c6de`.

## Integrated validation

- full suite: **462 passed / 1 skipped**;
- Action #10: **25 passed**;
- Action #9 + Draw/SBA: **60 passed**;
- SemanticCoverage + card data: **10 passed**;
- prior Action regressions: **201 passed**;
- Ruff format check: clean;
- Ruff check: clean;
- `git diff --check`: clean before this evidence-only report;
- Action #10 recognized/payload digest:
  `0adbade241a770917df78da65282c73d2296a5fe8511f24bff46a47005549065`;
- Action #10 fully-supported digest:
  `71732520f3cf6094c7ea9d2dee6377d5677cb6448a7876ba803cda9bbc200821`.

The authoritative card-data tests reconfirmed **472 print records / 332 unique Oracle objects**
and the frozen **102-card / 10-deck** roster foundation.

## Merged Acceptance evidence

Each seed was run twice from merged main and produced byte-identical output.

| Seed | Winner | Ending turn | Action #10 transactions |
|---:|---|---:|---:|
| 7001 | Raphael | 14 | 2 |
| 7002 | Raphael | 18 | 5 |
| 7003 | Leonardo | 19 | 0 |
| 7004 | Leonardo | 21 | 0 |
| 7005 | Raphael | 16 | 0 |
| **Aggregate** | | | **7** |

The integrated baseline is **33 unsupported events / 12 exact pairs**, **44 Priority grants / 44
passes**, **1** block-restriction rejection, and **0** invariant violations.

## Exact residual 12-pair evidence map

"Would clear" means the named bounded capability must truthfully implement the whole remaining
semantic boundary, not merely recognize a child phrase.

| Oracle card and exact fragment | Events | Parent/context status | Actual missing child semantic(s) | Dependencies | Frozen exposure | Would the candidate clear this pair? |
|---|---:|---|---|---|---|---|
| **Leonardo, Big Brother** — `Sneak {W} (You may cast this spell for {W} if you also return an unblocked attacker you control to hand during the declare blockers step. He enters tapped and attacking.)` | 7 | Declare-Blockers casting window unsupported | Sneak alternate cost; authoritative unblocked-attacker return as an additional cost; tapped-and-attacking entry | Stack/Priority and mana costs exist; Targeted Return exists as an effect, but return-as-cost, special timing, and combat insertion must be added transactionally | Leonardo deck | **Yes**, through complete bounded Sneak; no, through Return or cost recognition alone |
| **Leonardo, Leader in Blue** — `Sneak {3}{W}{W} (You may cast this spell for {3}{W}{W} if you also return an unblocked attacker you control to hand during the declare blockers step. He enters tapped and attacking.)` | 5 | Same unsupported Sneak parent | Same Sneak transaction with a different fixed mana component | Same as above | Leonardo deck | **Yes**, through the same generic bounded Sneak transaction |
| **Wingnut, Bat on the Belfry** — `Alliance — Whenever another creature you control enters, Wingnut gains your choice of flying, menace, or haste until end of turn.` | 4 | Typed ETB events exist; this Alliance trigger/delivery and choice are unsupported | Modal choice plus temporary Flying/Menace/Haste grant; Menace itself needs multiple-blocker support | Generic trigger path, immutable choice, duration/layers; Flying/Haste legality and Menace topology | Raphael deck | **No** for trigger expansion alone; only the complete Alliance modal-keyword capability clears it |
| **Casey Jones, Jury-Rig Justiciar** — `When Casey Jones enters, look at the top four cards of your library. You may reveal an artifact card from among them and put it into your hand. Put the rest on the bottom of your library in a random order.` | 2 | ETB parent and compound child unsupported | Private look, optional type-filtered reveal/selection, Library-to-Hand movement, and random-order bottoming | Hidden-information choice, authoritative library ordering, zone identity, deterministic RNG, trigger delivery | Raphael and Casey Jones decks | **No** for trigger or Draw alone; **yes** only for the full bounded look/reveal/remainder sequence |
| **Leonardo, Cutting Edge** — `Sneak {W} (You may cast this spell for {W} if you also return an unblocked attacker you control to hand during the declare blockers step. He enters tapped and attacking.)` | 2 | Unsupported Sneak parent | Same bounded Sneak transaction | Same as Big Brother | Leonardo deck | **Yes**, through complete bounded Sneak |
| **Leonardo, Sewer Samurai** — `During your turn, you may cast creature spells with power or toughness 1 or less from your graveyard. If you cast a spell this way, that creature enters with a finality counter on it. (If a creature with a finality counter on it would die, exile it instead.)` | 2 | Static turn-limited permission unsupported | Graveyard casting permission and filter; finality-counter entry; dies-to-exile replacement | Alternate casting zone, permission duration/filter, counters, replacement effects, object tracking | Leonardo deck | **No** for graveyard casting alone; all linked permission/finality semantics are required |
| **Leonardo, Sewer Samurai** — `Sneak {2}{W}{W}` | 2 | Keyword's reminder text is omitted on this printing, but the same Sneak rules context is required | Complete Sneak transaction, derived from authoritative keyword semantics rather than local reminder text | Same bounded Sneak grammar/rules mapping and transaction | Leonardo deck | **Yes**, if keyword-only Sneak is recognized generically |
| **Lita, Little Orphan Amphibian** — `• Create a Food token. (It's an artifact with "{2}, {T}, Sacrifice this token: You gain 3 life.")` | 2 | Token creation is already supported; Food's reminder activation is explicitly unsupported | Mana + tap + sacrifice activation costs and life gain | Activated delivery exists; needs sacrifice-cost composition, token cessation, life-gain result/evidence | Leonardo deck | **Yes** for complete bounded Food activation; no for Create Token or life gain alone |
| **Raphael, Most Attitude** — `Alliance — Whenever another creature you control enters, you may exile the top card of your library.` | 2 | Typed ETB event exists; Alliance trigger delivery unsupported | Optional exile-top instruction with stable association to Raphael | Trigger delivery, private/top-card identity, Library-to-Exile movement, linked-object tracking | Raphael deck | **No** for generic trigger expansion alone; **yes** only with the exile/link child |
| **Raphael, Most Attitude** — `Menace (This creature can't be blocked except by two or more creatures.)` | 2 | Combat/blocking is authoritative but supports only the bounded single-blocker topology | Two-or-more blocker legality, enumeration, ordering, and downstream damage assignment | Combat option generation, Pilot choice, blocker order, Trample/strike-step integration | Raphael deck | **Yes** for a complete bounded multiple-blocker/Menace expansion |
| **Raphael, Most Attitude** — `Whenever Raphael attacks, until end of turn, you may play a card exiled with Raphael.` | 2 | Authoritative attack events exist; this trigger and permission child are unsupported | Duration-limited permission to play an object linked to Raphael's exile history | Trigger delivery, linked exile identity, play/cast permissions, timing and costs | Raphael deck | **No** for trigger expansion alone; requires the linked exile/play permission system |
| **Raphael, the Nightwatcher** — `Sneak {1}{R}{R} (You may cast this spell for {1}{R}{R} if you also return an unblocked attacker you control to hand during the declare blockers step. He enters tapped and attacking.)` | 1 | Unsupported Sneak parent | Same bounded Sneak transaction with fixed red mana | Same as Big Brother | Raphael deck | **Yes**, through complete bounded Sneak |

The five Sneak pairs total **17 events**. Each other semantic family contributes one pair. Trigger
delivery is a dependency in four non-Sneak pairs, but delivery alone clears none because every one
still has an unsupported compound child. Already-supported Create Token and Action #10 payloads
receive no duplicate credit.

## Fresh authoritative census

The corpus scan deduplicated the 472-print snapshot by Oracle ID and independently inspected the
frozen decklists. Counts are recognition/reach evidence, not implementation claims.

| Candidate family | Full-pool exposure | Frozen exposure | Direct Acceptance leverage | Readiness after Action #10 |
|---|---:|---:|---:|---|
| Sneak | **27 objects / 32 fragments** | **18 cards / 6 decks** | **17 events / 5 complete pairs** | Stack, Priority/pass, fixed mana costs, runtime Return identity, and combat state exist; special timing, return-as-cost, and tapped-attacking entry remain |
| Alliance | 10 / 10 | 6 / 3 | 8 / 2 | Typed events exist; children differ and neither pair is cleared by delivery alone |
| Menace | 17 / 18 | 6 / 4 | 2 / 1 | Combat identity exists; multiple-blocker topology is absent |
| Food activation/reminder | 5 / 5 | 3 / 3 | 2 / 1 | Activated delivery and token identity exist; sacrifice costs and life gain remain |
| Look/reveal-to-hand selection | 3 / 3 | 2 / 4 | 2 / 1 | Library identity/order and deterministic RNG exist; compound private selection is absent |
| Graveyard casting permission | 6 objects | 3 / 3 | Child of 2 / 1 | Requires alternate-zone casting and, for the exposed pair, finality replacement semantics |
| Exile-top / linked play permission | 1 object / 2 fragments | 1 / 1 | 4 / 2 | Requires two linked children plus trigger delivery; neither fragment is independently complete |
| Equipment/equip | 15 objects / 25 scanned fragments | 6 / 7 | 0 / 0 | Activated delivery helps, but attachment state/costs have no direct residual pair |

A broad direct-trigger text scan finds substantial corpus reach, but it is deliberately not scored
as completed Action coverage: the four residual trigger-bearing pairs have four different
unsupported children. The seven context-sensitive UNKNOWN objects remain Arcane Signet,
Chromatic Lantern, Command Tower, Double Jump // Flying Kick, Exotic Orchard, Fast Forward, and
Plague of Vermin. Action #10 supplies no evidence for reclassification.

## Re-ranked Action candidates

| Rank | Candidate | Pair/event leverage | Evidence-based assessment |
|---:|---|---|---|
| 1 | **Bounded Sneak casting transaction** | **5 pairs / 17 events** | Dominates both pair and event elimination and has 27-object/32-fragment full-pool reach. Existing Stack, Priority/pass, mana-cost, Return identity, zone transaction, and combat foundations materially reduce dependency risk. High complexity remains, but one coherent mechanic can truthfully clear all five pairs. |
| 2 | Menace / bounded multiple blockers | 1 / 2 | Clears one pair with 17-object reach and high combat significance. It is still a combat-topology expansion affecting blocker enumeration, ordering, Trample, and strike steps. |
| 3 | Bounded Food activation/use | 1 / 2 | Can clear one pair and reuse activated delivery/token identity, but needs sacrifice-cost composition and life gain. Acceptance has no Food creation transaction, reducing immediate execution evidence. |
| 4 | Casey look/reveal/remainder sequence | 1 / 2 | Can clear one pair and reuses library ordering/RNG, but combines hidden selection, filtering, reveal, movement, and randomized remainder ordering. |
| 5 | Alliance modal temporary keyword grant | 1 / 4 | Higher event count than ranks 2–4, but cannot clear its pair until Flying, Haste, and Menace choices are all truthful; Menace is itself rank 2 work. |
| 6 | Raphael linked exile/play sequence | 2 / 4 | Two-pair potential, but only as a compound tracked-exile plus duration-limited play-permission system. Trigger expansion alone clears neither pair. |
| 7 | Sewer Samurai graveyard/finality permission | 1 / 2 | Significant gameplay semantics, but one pair combines alternate-zone casting, filtering, a finality counter, and a dies replacement. |
| 8 | Generic trigger-delivery expansion | 0 independently / parent of 4 pairs | Exceptional long-term corpus leverage, but every current residual trigger has an unsupported child; a delivery-only checkpoint would truthfully clear zero pairs. It should be advanced through a concrete supported child, as Action #10 did. |
| 9 | Equipment/equip | 0 / 0 | Meaningful roster reach, but no direct residual pair and substantial attachment-state work. |
| 10 | Remaining generic Draw/filter expansion | 0 independently | Existing Draw paths are not the limiting boundary in any current pair. Broadening Draw would not clear a residual fragment by itself. |

Pair elimination is weighted above raw corpus recognition. Sneak remains first under either metric:
it can close five of the twelve pairs, remove seventeen of thirty-three observed events, and enable
one coherent mechanic across both Leonardo and Raphael decks. The next-best candidates each clear
at most one pair unless bundled with several distinct child semantics.

## Action #11 recommendation

Implement a reusable, Oracle-derived **bounded Sneak casting transaction**.

The bounded capability should cover the currently exposed fixed-cost Sneak forms and keyword-only
form without card-name dispatch. It must preserve the whole mechanic boundary: the Declare
Blockers casting permission, fixed Sneak mana cost, authoritative selection and return of an
unblocked attacker as a transactional casting cost, represented spell placement on Stack,
Priority/pass and resolution, and battlefield entry tapped and attacking. A supported Return child
or cost parser must not independently upgrade the unsupported Sneak parent.

Keep unsupported semantics explicit: generic flash/timing expansion, arbitrary alternate or
additional costs, multiple-blocker combat, broader put-onto-battlefield-attacking effects,
responses beyond represented Priority, and any Sneak form whose costs or context exceed the
bounded evidence.

This recommendation is not balance evidence. It is the highest-leverage architectural next step
because it can truthfully eliminate **5 exact pairs / 17 events** while reusing the accepted Engine
0.8 and Actions #1–#10 foundations.

No Action #11 implementation is included.
