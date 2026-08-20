# Targeted Return to Hand Acceptance Audit #3

## Audit identity

- Evidence checkpoint: `46e3c684e10a91a4e697629f069b0b24786aa0f0`
- Corrected candidate fingerprint: `23ccaf27bf20cf1230e47f6ecdcbd43265f0fc12`
- Historical Audit #1 SHA-256:
  `7deae80ca008f5e4c94dcbffe817090b595fb3a7bd470bfc58be06e853d9ed3c`
- Historical Audit #2 SHA-256:
  `5e07fd3ad3487726cbef6eb5ff93dc0ccb562e919d230320b754827c69adbec0`
- Audit mode: evidence-only; implementation, tests, and prior reports were not modified

## Executive finding

Both earlier semantic-support defects are substantially corrected:

- activated-ability interpretation consumes the generic Return interpretation and contains no
  duplicate Return grammar;
- broad/non-executable Return forms now retain a recognized clause boundary and independently
  classify meaningful semantic text before and after that clause.

The six Audit #2 corpus examples now preserve truthful payload, parent, preceding, follow-up, and
full-support flags. The complete corpus membership, transaction, deterministic Acceptance replay,
and validation claims also reproduce.

Audit #3 nevertheless finds a narrower but material metadata-integrity defect. `ReturnClause.start`
and `.end` are absolute offsets into the complete Oracle fragment, while `preceding_text` and
`following_text` are copied from a normalized activation effect with activation costs and timing
instructions removed. Consequently those text fields do not always equal the original text before
and after the advertised absolute span. This violates the explicit Audit #3 requirement that the
stored surrounding text correspond exactly to the authoritative fragment.

Independent checking of all 38 recognized fragments found three mismatches:

| Card | Authoritative text before/after absolute span | Stored `ReturnClause` text |
| --- | --- | --- |
| Northampton Farm | before includes `{2}, {T}, Sacrifice this land:` | stored before omits the complete cost prefix |
| Together Forever | before includes `{1}:` | stored before omits the activation cost prefix |
| Prehistoric Pet | before includes `{1}{W}, {T}:`; after includes `Activate only during your turn.` | stored before is empty and stored after is punctuation only |

The classifier separately interprets those omitted regions as activation parent/cost/timing, so the
current `SemanticCoverage` results remain correct and no unsupported gameplay is enabled. But a
consumer cannot reconstruct or verify `preceding_text | Return clause | following_text` against the
original Oracle fragment despite the absolute offsets. The metadata therefore is not yet an
authoritative clause representation.

## Reject #1 verification: one Return grammar

Structural inspection confirms:

- `activated_ability_semantics` invokes `return_to_hand_semantics`;
- no second `owner's hand` pattern or equivalent executable Return grammar exists in activated
  interpretation or the engine;
- the generic child limitation tuple survives activation composition unchanged;
- `SemanticCoverage` remains Action-independent and has no token, Return, card, interpreter,
  engine, or runtime fields;
- no card-name, deck, roster, Acceptance, or seed dispatch exists.

The duplicate-parser defect from Audit #1 is resolved.

## Reject #2 verification: compound support boundaries

All 38 recognized fragments now contain a nonempty Return clause with a valid absolute span whose
slice exactly equals `clause.text`. Meaningful semantic text in the parser's classified before/after
regions produces explicit limitations, and `fully_supported` derives from payload, parent,
follow-up, and limitation state.

The six required authoritative cases independently classify as follows. Flags are payload / parent /
preceding / follow-up / full:

- **Nobody** — clause `return up to one other target artifact you control to its owner's hand`;
  ETB trigger before and Scry/reminder text after; no / no / no / no / no; target-shape, parent,
  preceding, and follow-up limitations.
- **Karai, Future of the Foot** — clause `return target creature card from your graveyard to your
  hand`; combat-damage trigger before and conditional `instead` return after; no / no / no / no /
  no; target-shape, parent, preceding, and follow-up limitations.
- **Northampton Farm** — clause `Return each other card exiled with this land to its owner's hand`;
  preceding return-to-battlefield instruction and no semantic follow-up; no / no / no / yes / no;
  target-shape, parent, and preceding limitations.
- **Together Forever** — clause `return that card to its owner's hand`; preceding choice and delayed
  dies condition and no semantic follow-up; no / no / no / yes / no; target-shape, parent, and
  preceding limitations.
- **Ashcoat of the Shadow Swarm** — clause `return up to two Rat creature cards from your graveyard
  to your hand`; end-step/optional-mill/condition before and mill reminder after; no / no / no / no /
  no; target-shape, parent, preceding, and follow-up limitations.
- **Turtles in Time** — clause `Return all creatures to their owners' hands`; no semantic text before
  and shuffle/draw text after; no / no / yes / no / no; target-shape, parent, and follow-up
  limitations.

The broad classification defect from Audit #2 is resolved. The remaining issue concerns exact
correspondence between stored surrounding text and the absolute original-fragment span, not the
coverage flags shown above.

Adversarial probes also confirm explicit limitations for unsupported text before, after, and on
both sides; non-executable Returns embedded in triggers; conjunctions; multiple sentences; reminder
text; multiple Return-looking clauses; case/punctuation variants; and non-Return strings containing
`return`. No probe transformed unclassified meaningful semantic text into supported text.

## Authoritative coverage regeneration

Independent enumeration of 472 print records / 332 unique Oracle objects reproduced:

- recognized: **37 objects / 38 fragments**;
- bounded executable: **1 / 1**;
- fully supported: **1 / 1**;
- executable/full member: **Prehistoric Pet**.

Digests reproduced:

- recognized:
  `59bb7f7c2a44fea44e7b94b5f47e6030beb2b25205b009f350a67b35a9b9cd59`;
- executable/full:
  `8de28e00a41e8fedc23667860d223f241c22f6dbac89b12cd218cb5bb3aeca95`.

Prehistoric Pet's support classification is independently justified: Action #5 represents its
activation parent; fixed `{1}{W}` and `{T}` costs are transactional; the source must be legally able
to tap; one other creature controlled by the activating player is selected at announcement;
`Activate only during your turn` is satisfied by the represented active-player action window; the
bounded Return payload is executable; and no unclassified semantic instruction surrounds the
payload after parent/timing decomposition. Its `SemanticCoverage` is fully supported with an empty
limitation tuple. The metadata mismatch described above does not currently change that correct
classification, but it prevents the new absolute clause representation from being accepted as
authoritative.

## Transaction regression

Focused and adversarial probes reconfirm:

- immutable engine-generated target options and deterministic ordering;
- announcement-time target selection and resolution-time revalidation;
- fabricated, stale, wrong-zone, self, opponent-controlled, and noncreature target rejection;
- owner rather than temporary controller determines the destination hand;
- zone movement creates a new runtime identity;
- counters, damage, tapped state, controller state, and temporary battlefield effects do not follow;
- returned tokens cease at the post-resolution SBA boundary;
- failed announcement does not partially pay costs or mutate the Stack;
- costs remain paid when a target later becomes illegal;
- authoritative Stack and two-player Priority/pass precede resolution;
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

Aggregate evidence:

- **47 unsupported events / 16 exact pairs**;
- eight successful Returns;
- 16 announcements, payments, Stack placements, and resolutions;
- 32 Priority grants and 32 passes;
- 13 Scry transactions;
- 17 Deal Damage transactions;
- one block-restriction rejection;
- zero invariant violations.

The six corrected compound classifications do not alter Acceptance telemetry because those
authoritative fragments are not executed in Acceptance Match #001. Seed 7002 retains three legal
Prehistoric Pet Returns—Leonardo, Big Brother on turn 9 and two later Prehistoric Pet objects on
turns 13 and 15—followed by Raphael's turn-16 lethal combat damage. The causal chain is unchanged.

## Validation

- Full suite: **374 passed / 1 skipped**.
- Targeted Return: **30 passed**.
- Return classifier/span subset: **16 passed**.
- Activated Ability/Priority: **30 passed**.
- SemanticCoverage: **5 passed**.
- Stack/cost/boundary: **23 passed**.
- Token/SBA: **49 passed**.
- Scry: **19 passed**.
- Deal Damage: **29 passed**.
- Strike/combat/state: **77 passed**.
- Card-data integrity: **5 passed**.
- Ruff format check: clean, 40 files.
- Ruff check: clean.
- `git diff --check`: clean.
- Candidate fingerprint remained `23ccaf27bf20cf1230e47f6ecdcbd43265f0fc12`.
- Both historical rejection reports remained byte-identical at their recorded SHA-256 values.

The passing tests do not catch the remaining defect because the corpus invariant checks
`fragment[start:end] == clause.text` but does not assert
`fragment[:start] == clause.preceding_text` and
`fragment[end:] == clause.following_text`.

## Smallest evidence-backed correction

Do not change recognition, payload classification, SemanticCoverage, activated composition,
engine execution, targets, costs, Stack, Priority, movement, tokens, pilot, corpus membership, or
Acceptance behavior.

Store `ReturnClause.preceding_text` and `following_text` from the complete original fragment using
the absolute span (`fragment[:start]` and `fragment[end:]`). Preserve separately the normalized
effect-only semantic regions used to classify preceding/follow-up executability, so supported
activation costs and timing text are not mislabeled as unsupported Return surroundings. Add a
corpus-wide invariant asserting all three exact slice equalities for every recognized fragment.

## Recommendation

**REJECT — both prior semantic-support blockers are corrected and gameplay remains sound, but the
new ReturnClause surrounding-text fields are inconsistent with their absolute original-fragment
span for Northampton Farm, Together Forever, and Prehistoric Pet. Apply the smallest metadata-only
correction above and resubmit for Acceptance Audit #4.**
