# Targeted Return to Hand Acceptance Audit #2

## Audit identity

- Branch: `agent/cardcade-targeted-return`
- Evidence checkpoint: `46e3c684e10a91a4e697629f069b0b24786aa0f0`
- Rejected candidate fingerprint: `4b21f293bee98943bf53c1b736a4819bcc0129fd`
- Corrected candidate fingerprint: `3cdc173503279401aa644db0d89c0ef9dca7d726`
- Historical Audit #1 SHA-256 before Audit #2:
  `7deae80ca008f5e4c94dcbffe817090b595fb3a7bd470bfc58be06e853d9ed3c`
- Audit mode: evidence-only; implementation, tests, and Audit #1 were not modified

## Executive finding

The correction removes the duplicated executable Return grammar from activated-ability
interpretation. The authoritative executable path is now:

`Oracle text → return_to_hand_semantics → ReturnToHandProgram + SemanticCoverage → activated ability composition → engine execution`

The two synthetic compound cases from Audit #1 now retain their exact preceding or follow-up
limitations through activation composition, and Prehistoric Pet's transaction and deterministic
Acceptance behavior remain intact.

The central Audit #2 gate nevertheless fails on real authoritative corpus compounds. Generic
recognition is broader than the bounded executable payload parser, but surrounding-text analysis is
performed only when the narrow executable payload regex matches. When a recognized Return has an
unsupported target shape, source zone, quantity, or other payload form, the parser does not locate
that Return clause's span. It consequently initializes both surrounding spans as empty and reports
`followup_executable=True`, even when authoritative text contains unsupported preceding or following
instructions.

## Original blocker and structural correction

Structural inspection confirms:

- `activated_ability_semantics` calls `return_to_hand_semantics` once;
- activated interpretation contains no second `owner's hand` pattern or equivalent Return grammar;
- the generic Return limitation tuple survives activation composition unchanged for the corrected
  bounded fixtures;
- `SemanticCoverage` remains Action-independent and has no Return, token, card, interpreter, engine,
  or runtime dependency;
- no Prehistoric Pet, deck, roster, Acceptance, or seed dispatch exists in the interpreter or engine
  path.

Thus the duplicated-parser half of Audit #1's blocker is resolved. The narrow-span classification
half is resolved only for the bounded executable syntax, not for all 38 recognized fragments.

## Real-corpus compound probes

Independent probes against the authoritative snapshot produced the following representative
results. Every entry is recognized and incomplete, but each incorrectly reports
`followup_executable=True` and lacks an explicit preceding/follow-up limitation:

| Card | Unsupported surrounding semantics omitted by generic Return coverage |
| --- | --- |
| Ashcoat of the Shadow Swarm | end-step trigger, optional mill, `if you do` condition, quantity and graveyard selection |
| Karai, Future of the Foot | combat-damage trigger plus conditional `instead` return to battlefield |
| Nobody | ETB trigger and following Scry 1 instruction |
| Northampton Farm | sacrifice cost, preceding return from exile to battlefield, then another return instruction |
| Together Forever | target choice followed by a delayed dies-this-turn condition |
| Turtles in Time | following hand/graveyard shuffle, conditional draw-seven, and exile instructions |

For example, Nobody is classified as:

`SemanticCoverage(payload_executable=False, parent_executable=False, followup_executable=True,
limitations=('return_target_shape_not_implemented', 'return_parent_context_not_implemented'))`

The explicit target-shape and parent limitations truthfully prevent full support, so current engine
execution is not incorrectly enabled. However, `followup_executable=True` is false evidence and the
Scry follow-up is absent from the Return coverage record. Turtles in Time, Karai, and Northampton
Farm demonstrate that this is not a single-card anomaly. Therefore the corrected classifier still
does not satisfy the required distinction among recognition, payload execution, surrounding
semantics, and full-fragment support for the complete recognized universe.

## Prehistoric Pet represented support

Prehistoric Pet independently remains the only bounded executable candidate. Its authoritative
fragment contains:

- an activated-ability parent represented by Action #5;
- fixed `{1}{W}` mana plus `{T}`, supported transactionally;
- one target restricted to another creature controlled by the activating player;
- `Activate only during your turn`, satisfied by the represented active-player main-phase action
  windows;
- the bounded battlefield-to-owner's-hand payload;
- no unsupported preceding or follow-up instruction after activation cost/timing separation.

The corrected generic result and composed activation coverage are both fully supported with an
empty limitation tuple. Engine inspection and probes trace the complete path through an immutable
legal `ActionOption`, announcement-time target ID, transactional costs, authoritative ability Stack
object, two-player Priority/pass, resolution-time target revalidation, and the existing zone
transaction. There is no card-name shortcut.

## Authoritative coverage reconciliation

Independent enumeration over 472 print records / 332 unique Oracle objects reproduced:

- recognized: **37 objects / 38 fragments**;
- bounded executable payload: **1 / 1**;
- currently fully supported: **1 / 1**;
- frozen recognized: **18 cards / 8 decks**;
- frozen executable/full: **Prehistoric Pet**, in Leonardo.

Digests reproduced:

- recognized:
  `59bb7f7c2a44fea44e7b94b5f47e6030beb2b25205b009f350a67b35a9b9cd59`;
- executable/full:
  `8de28e00a41e8fedc23667860d223f241c22f6dbac89b12cd218cb5bb3aeca95`.

Across the current 38 recognized fragments, Prehistoric Pet has no limitation. The other 37 each
carry `return_target_shape_not_implemented` and `return_parent_context_not_implemented`. Those two
limitations prevent false full support, but real compound fragments do not carry their additional
preceding/follow-up limitations and incorrectly expose `followup_executable=True`.

The seven context-sensitive UNKNOWN objects remain Arcane Signet, Chromatic Lantern, Command
Tower, Double Jump // Flying Kick, Exotic Orchard, Fast Forward, and Plague of Vermin.

## Transaction regression

The interpretation correction did not damage the previously sound transaction. Executable probes
and focused regressions confirm:

- immutable engine-generated targets and deterministic ordering;
- target selection at announcement;
- fabricated, stale, wrong-zone, self, opponent-controlled, and noncreature target rejection;
- resolution-time zone, identity, type, controller, and `another` revalidation;
- no partial cost or Stack mutation after failed announcement;
- paid costs remain paid if a target becomes illegal during the pass window;
- destination is the owner's hand even after a control-changing effect;
- movement creates a new runtime object and stale battlefield references remain invalid;
- counters, damage, tapped state, controller state, and temporary battlefield effects do not follow;
- returned tokens cease at the post-resolution SBA boundary;
- Stack and Priority remain separate from delivery;
- former ability objects cannot resolve twice.

## Acceptance replay

Seeds 7001–7005 were run twice. Duplicate snapshots were byte-equivalent.

| Seed | Winner / ending turn | Unsupported events / seed pairs | Returns |
| ---: | --- | ---: | ---: |
| 7001 | Raphael / 16 | 10 / 10 | 0 |
| 7002 | Raphael / 16 | 6 / 5 | 3 |
| 7003 | Leonardo / 19 | 12 / 10 | 0 |
| 7004 | Leonardo / 21 | 13 / 11 | 0 |
| 7005 | Raphael / 16 | 6 / 5 | 5 |

Aggregate evidence remains:

- **47 unsupported events / 16 exact pairs**;
- eight successful Return transactions;
- 16 activation announcements, payments, Stack placements, and resolutions;
- 32 Priority grants and 32 passes;
- 13 Scry transactions;
- 17 Deal Damage transactions;
- one block-restriction rejection;
- zero invariant violations.

The classifier correction did not change runtime telemetry because none of the misclassified
real-corpus compounds executes in Acceptance Match #001. This unchanged `47/16` result is therefore
not evidence that their coverage records are correct.

Seed 7002 retains its previously verified causal chain. Prehistoric Pet legally returns Leonardo,
Big Brother on turn 9 and two later Prehistoric Pet objects on turns 13 and 15. Leonardo's reduced
battlefield allows Raphael's attackers to produce lethal combat damage on turn 16. No classifier,
pilot, or balance change altered that result.

## Validation

- Full suite: **364 passed / 1 skipped**.
- Targeted Return: **20 passed**.
- Activated Ability/Priority: **30 passed**.
- Generic SemanticCoverage: **5 passed**.
- Stack/cost/boundary: **23 passed**.
- Token/SBA: **49 passed**.
- Scry: **19 passed**.
- Deal Damage: **29 passed**.
- Strike/combat/state: **77 passed**.
- Card-data integrity: **5 passed**.
- Ruff format check: clean, 40 files.
- Ruff check: clean.
- `git diff --check`: clean.
- Corrected implementation/test fingerprint remained
  `3cdc173503279401aa644db0d89c0ef9dca7d726`.
- Audit #1 remained byte-identical at SHA-256
  `7deae80ca008f5e4c94dcbffe817090b595fb3a7bd470bfc58be06e853d9ed3c`.

Passing tests do not clear the real-corpus compound defect because the new regressions exercise
only the narrow executable Return shape with synthetic preceding/follow-up text.

## Smallest evidence-backed correction

Do not change the engine transaction, targets, costs, Stack, Priority, movement, token handling,
pilot, coverage memberships, or Acceptance behavior. Correct only generic interpretation:

1. after broad Return recognition, locate the recognized Return clause span even when its target
   shape or source zone is not bounded executable;
2. classify text before and after that broad clause independently from payload executability;
3. set `followup_executable=False` and attach explicit preceding/follow-up limitations for every
   real compound whose surrounding semantics are unsupported;
4. add membership-locked corpus regressions for representative trigger/condition, Scry follow-up,
   preceding zone movement, delayed return, shuffle/draw, and exile compounds;
5. retain the single authoritative generic Return result consumed by activated abilities.

## Recommendation

**REJECT — duplicated executable Return parsing is fixed and the transaction remains sound, but
generic coverage still marks follow-up semantics executable and omits explicit surrounding
limitations for real recognized corpus compounds. Apply the smallest broad-clause span correction
above and resubmit for Acceptance Audit #3.**
