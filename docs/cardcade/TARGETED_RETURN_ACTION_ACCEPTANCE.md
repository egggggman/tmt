# Targeted Return to Hand Action Acceptance Audit #1

## Audit identity and scope

- Branch: `agent/cardcade-targeted-return`
- Evidence checkpoint and candidate parent: `46e3c684e10a91a4e697629f069b0b24786aa0f0`
- Audited implementation/test fingerprint: `4b21f293bee98943bf53c1b736a4819bcc0129fd`
- Audit mode: evidence-only; implementation and tests were not modified

This audit independently inspected the uncommitted Action #6 candidate from Oracle
interpretation through target generation, announcement, transactional costs, authoritative
Stack membership, Priority/pass, resolution-time target revalidation, zone movement, new-object
identity, and token cessation.

## Executive finding

The bounded Prehistoric Pet transaction is operationally sound. The audit reproduced legal target
generation and selection, cost payment, Stack placement, two-player pass sequencing, resolution
revalidation, battlefield-to-owner's-hand movement, new runtime identity, state reset, and token
cessation. The claimed acceptance replay movement is also genuine execution evidence.

The candidate nevertheless fails the semantic-classification gate. The generic
`return_to_hand_semantics` classifier searches for the bounded payload anywhere in a fragment and
then derives `parent_executable=True`, `followup_executable=True`, and full support without
separating preceding and following instructions. Two renamed, card-independent adversarial probes
demonstrated the defect:

1. `{1}, {T}: Draw a card. Return another target creature you control to its owner's hand. Activate
   only during your turn.` was classified by the generic Return contract as fully supported even
   though Draw is unsupported and precedes the payload.
2. `{1}, {T}: Return another target creature you control to its owner's hand. You gain 1 life.
   Activate only during your turn.` was classified by the generic Return contract as fully
   supported even though life gain is an unsupported follow-up.

The activation-specific parser happens to reject or retain a limitation for these fixtures, but it
does so through a second, duplicated Return regex rather than by consuming the generic Return
program and coverage result. Therefore the claimed generic coverage value and the executable
activation classification can disagree. That is a material telemetry-integrity defect: equivalent
future callers of the generic classifier could silently upgrade an unsupported compound fragment.

## Authoritative corpus reconciliation

The authoritative snapshot passed its five integrity tests and retained 472 print records / 332
unique Oracle objects. An independent enumeration over unique Oracle identities reproduced:

- recognized: **37 Oracle objects / 38 fragments**;
- bounded payload executable: **1 object / 1 fragment**;
- currently classified fully supported: **1 object / 1 fragment**;
- bounded executable/full member: **Prehistoric Pet** only.

Stable memberships reproduced:

- recognized digest:
  `59bb7f7c2a44fea44e7b94b5f47e6030beb2b25205b009f350a67b35a9b9cd59`;
- bounded executable digest:
  `8de28e00a41e8fedc23667860d223f241c22f6dbac89b12cd218cb5bb3aeca95`.

The 37 recognized Oracle objects are Ashcoat of the Shadow Swarm; Bespoke Bō; Does Machines;
Donatello's Technique; Donatello, Gadget Master; Foot Ninjas; Jennika's Technique; Karai's
Technique; Karai, Future of the Foot; Kitsune's Technique; Leonardo's Technique; Leonardo, Big
Brother; Leonardo, Cutting Edge; Leonardo, Leader in Blue; Metalhead; Michelangelo's Technique;
Michelangelo, Improviser; Michelangelo, On the Scene; New Generation's Technique; Nobody;
Northampton Farm; Oroku Saki, Shredder Rising; Prehistoric Pet; Ragamuffin Raptor; Raphael's
Technique; Raphael, the Nightwatcher; Renet, Temporal Apprentice; Shredder's Technique; Shredder,
Unrelenting; Splinter's Technique; Splinter, Hamato Yoshi; The Last Ronin; The Last Ronin's
Technique; Together Forever; Turncoat Kunoichi; Turtles in Time; and Wave Goodbye. Karai, Future of
the Foot contributes two recognized fragments, producing 38 fragments from 37 objects.

Frozen-roster reconciliation reproduced 18 recognized cards across eight decks. The exact frozen
members are Bespoke Bō; Does Machines; Donatello, Gadget Master; Leonardo's Technique; Leonardo,
Big Brother; Leonardo, Cutting Edge; Leonardo, Leader in Blue; Michelangelo's Technique;
Michelangelo, Improviser; Oroku Saki, Shredder Rising; Prehistoric Pet; Raphael's Technique;
Raphael, the Nightwatcher; Shredder's Technique; Shredder, Unrelenting; Splinter's Technique;
Splinter, Hamato Yoshi; and The Last Ronin's Technique. Only Prehistoric Pet is bounded executable
and fully supported, in the Leonardo deck.

Recognition remains broader than execution for mass/non-targeted returns, multiple or variable
targets, Sneak returns as costs, graveyard and exile returns, trigger/condition contexts, delayed
returns, and compound follow-ups. The seven pre-existing context-sensitive UNKNOWN objects remain
Arcane Signet, Chromatic Lantern, Command Tower, Double Jump // Flying Kick, Exotic Orchard, Fast
Forward, and Plague of Vermin.

## Transaction and target-integrity evidence

Executable probes confirmed:

- legal options contain authoritative source and target IDs and are emitted in deterministic
  battlefield order;
- exactly one other creature controlled by the activating player is eligible;
- source, opponent-controlled creature, noncreature, fabricated ID, stale ID, and wrong-zone
  targets are rejected before payment;
- payment failure and target-validation failure do not partially tap sources or place an ability
  on the Stack;
- the announced target ID is retained by the authoritative ability object;
- costs are paid before Stack placement and are not refunded when the target becomes illegal;
- two engine-owned passes are required before resolution;
- a target that changes zone or controller while the ability waits resolves with no Return effect;
- successful movement uses the authoritative zone transaction and creates a new hand object ID;
- ownership, rather than temporary control, determines the destination hand;
- old battlefield references become stale and cannot bind to the replacement;
- counters, marked damage, tapped state, controller state, and temporary battlefield effects do not
  follow the new hand object;
- returned tokens briefly move under the zone transaction and then cease at the post-resolution
  state-based-action boundary rather than persisting as cards in hand;
- repeated resolution of the former ability object is rejected;
- no source-card-name or Acceptance-seed dispatch exists in the audited interpreter/engine path.

The extra post-Priority resolution SBA check did not leak Priority state or break existing Stack,
cost, turn, layer, combat, or identity regressions.

## Acceptance replay and telemetry integrity

The committed checkpoint was independently archived and executed separately from the live
candidate. It reproduced the pre-Action baseline exactly:

| Seed | Baseline winner / turn | Baseline unsupported events / seed pairs |
| ---: | --- | ---: |
| 7001 | Raphael / 16 | 10 / 10 |
| 7002 | Leonardo / 19 | 17 / 6 |
| 7003 | Leonardo / 19 | 12 / 10 |
| 7004 | Leonardo / 21 | 16 / 12 |
| 7005 | Raphael / 16 | 14 / 7 |

Baseline aggregate: **69 unsupported events / 17 exact card-fragment pairs**, eight activation
resolutions, eight Scry transactions, 16 Deal Damage transactions, and six block-restriction
rejections.

The candidate was then executed twice per seed. Duplicate snapshots were byte-equivalent:

| Seed | Candidate winner / turn | Unsupported events / seed pairs | Return transactions |
| ---: | --- | ---: | ---: |
| 7001 | Raphael / 16 | 10 / 10 | 0 |
| 7002 | Raphael / 16 | 6 / 5 | 3 |
| 7003 | Leonardo / 19 | 12 / 10 | 0 |
| 7004 | Leonardo / 21 | 13 / 11 | 0 |
| 7005 | Raphael / 16 | 6 / 5 | 5 |

Candidate aggregate:

- **47 unsupported events / 16 exact card-fragment pairs**;
- eight successful Prehistoric Pet Return transactions;
- 16 activation announcements, payments, Stack placements, and resolutions total;
- 32 Priority grants and 32 PASS actions;
- zero targets becoming illegal during the five acceptance games;
- 13 Scry transactions;
- 17 Deal Damage transactions;
- one block-restriction rejection;
- zero invariant violations.

The `69/17 → 47/16` result is not caused by merely suppressing Prehistoric Pet telemetry. The one
Prehistoric Pet pair and its 18 former per-exposure limitation events disappear because eight real
transactions now execute through cost, Stack, pass, resolution, and zone movement. Changed legal
game trajectories account for the remaining net four-event reduction and alter later Scry, damage,
and block exposure. The pair count falls by exactly the Prehistoric Pet pair.

### Seed 7002 causal trace

The baseline independently reproduced Leonardo winning on turn 19. In the candidate, Prehistoric
Pet executes three complete activations on turns 9, 13, and 15. It returns Leonardo, Big Brother and
two later Prehistoric Pet objects from Leonardo's battlefield to Leonardo's hand, each with a new
runtime identity. This reduces Leonardo's battlefield presence while Raphael's Null Group
Biological Assets and Mutant Town Musicians connect on turns 12, 14, and 16. Leonardo reaches zero
life during turn-16 combat. The new Raphael turn-16 result is therefore a deterministic consequence
of legal represented Return gameplay and the existing deterministic pilot choice, not a hidden
balance adjustment or telemetry-only change.

## Validation

- Full suite: **359 passed / 1 skipped**.
- Targeted Return suite: **15 passed**.
- Stack/cost/boundary/layer/turn/engine focused regressions: **103 passed**.
- Generic SemanticCoverage: **5 passed**.
- Authoritative card-data integrity: **5 passed**.
- Ruff format check: clean, 40 files.
- Ruff check: clean.
- `git diff --check`: clean.
- Candidate implementation/test fingerprint remained
  `4b21f293bee98943bf53c1b736a4819bcc0129fd`.

Passing repository tests do not clear the independently demonstrated compound-fragment
classification defect because the candidate suite contains no adversarial preceding/follow-up
fixture for the generic Return coverage entry point.

## Smallest evidence-backed correction

Keep the transaction, target, cost, Stack, Priority, zone, identity, token, replay, corpus
recognition, and gameplay behavior unchanged. Correct only semantic interpretation:

1. make the Action-specific Return parser identify the exact payload span and explicitly retain
   unsupported preceding and following text as limitations;
2. derive full-fragment support only when payload, parent/context, targets, costs, preceding text,
   and follow-up are all executable;
3. have activated-ability interpretation consume/pair that Return program and its generic coverage
   result instead of independently duplicating the Return regex;
4. add renamed, card-independent regressions for unsupported preceding and follow-up instructions,
   and lock the current authoritative corpus memberships/digests unless truthful recomputation finds
   a real membership change.

## Recommendation

**REJECT — the bounded transaction is sound, but generic Return semantic coverage can silently mark
unsupported compound fragments fully supported. Apply the smallest interpretation-only correction
above and submit the unchanged transaction for Acceptance Audit #2.**
