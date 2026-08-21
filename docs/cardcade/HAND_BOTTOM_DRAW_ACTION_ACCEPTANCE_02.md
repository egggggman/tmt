# Hand-Bottom / Conditional Draw Acceptance Audit #2

Status: **ACCEPT**  
Audit date: 2026-08-20  
Branch: `agent/cardcade-hand-bottom-draw`  
Parent baseline: `4c15424494cb0de6869537d31fc2f14881711295`  
Evidence checkpoint: `03b8269c722d3acd6dadefb1996890db6e63479c`  
Corrected candidate fingerprint: `d183e97e460b8e29ebc9c50bc5164af67c531773`

## Audit integrity

This was an evidence-only audit. No implementation or test file was modified. Audit #1 remained
byte-identical at SHA-256
`8b40060aed4a6850d9776d0face5c42e95c85a2314b63b443ca83d17fcee1d44`.
This report is the only tracked artifact created by Audit #2.

The corrected candidate fingerprint was independently reproduced as SHA-1 of the newline-joined,
path-sorted manifest of complete-file SHA-256 values for the six candidate files. It remained
`d183e97e460b8e29ebc9c50bc5164af67c531773` after all probes and validation.

## Rules basis

The audit used Wizards of the Coast's current Comprehensive Rules text, effective August 7,
2026, from `https://media.wizards.com/2026/downloads/MagicCompRules%2020260819.txt`:

- CR 121.1: drawing moves the top library card to its owner's hand;
- CR 400.7: a zone-changing card becomes a new object unless an exception applies;
- CR 401.2/401.4: library order and specified top/bottom placement are authoritative;
- CR 608.2c: resolving instructions are followed in written order;
- CR 608.2d: non-target choices are made when the effect calls for them.

## Blocker 1 re-audit: CR 608 sequencing

The rejected candidate obtained the Pilot choice before applying Deal Damage. The corrected
candidate no longer does so.

An independent runtime probe observed the game inside the Pilot callback. At that exact point:

- the target already had 3 damage marked;
- the typed `damage_dealt` event already existed;
- the authoritative Manhole Missile stack object remained on Stack;
- Stack size was one;
- `priority_state` was `None`;
- the private view's card IDs exactly matched the authoritative current hand;
- the offered options were precisely explicit decline plus each current hand identity.

The resulting historical event order was:

1. Deal Damage;
2. construct current legal hand choices and obtain/validate the Pilot choice;
3. move the selected hand object to library bottom;
4. Draw the pre-Draw top card;
5. commit typed Action #9 evidence;
6. move the resolving spell from Stack to graveyard;
7. run the existing SBA/life/trigger boundary.

The lethal-target regression independently confirms the spell leaves Stack before lethal-damage
SBA movement. No Priority grant or PASS action occurs between any of these instructions. The
correction is an instruction-time choice inside one resolving spell, not a new CR 117 window.

**Finding: blocker resolved.**

## Blocker 2 re-audit: reconstructive immutable evidence

Every executing or declining transaction now serializes:

- the complete ordered offered-choice identities, including explicit decline;
- complete ordered pre-operation hand IDs;
- complete ordered pre-operation library IDs, with bottom first and top last;
- selected old hand identity or explicit decline;
- bottomed new library identity;
- movement-success and conditional-Draw-result booleans;
- authoritative pre-Draw top identity;
- drawn new hand identity, if any;
- complete ordered post-operation hand IDs;
- complete ordered post-operation library IDs.

The evidence consists only of immutable scalar/tuple facts and remains valid after referenced
objects later change zones. Snapshot serialization preserves the same ordering and fields.

### Independent reconstruction

A real seed-7001 Acceptance transaction was reconstructed using only its serialized Action #9
record:

- offered choices were `None` plus the four IDs in `pre_hand_ids`;
- the selected ID was removed from `pre_hand_ids`;
- its new incarnation became the first ID in `post_library_ids`;
- `drawn_library_id` equaled the last ID in `pre_library_ids`, proving the authoritative top was
  drawn rather than the newly bottomed card;
- `post_library_ids` equaled the new bottom ID followed by every pre-library ID except the old
  top, in unchanged order;
- `post_hand_ids` equaled the remaining pre-hand IDs followed by `drawn_hand_id`;
- movement and conditional Draw were both recorded successful.

The independently observed original zone transition matched that reconstruction exactly. No live
hand, library, or object lookup was required.

Decline evidence likewise reconstructs explicit decline, no selected/bottom/drawn IDs, false
movement/Draw results, and identical pre/post hand and library sequences.

**Finding: blocker resolved.**

## Adversarial boundaries

Independent focused probes reproduced the following results:

- decline performs neither bottom movement nor Draw;
- an empty hand offers only decline and does not Draw;
- fabricated options are rejected after the preceding damage instruction without mutating hand
  or library;
- a plan made stale before child mutation is rejected with no partial bottom or Draw;
- an injected movement failure occurs before Draw, leaves both zones unchanged, and emits no
  committed Action #9 evidence;
- equal-valued cards retain distinct runtime IDs and remain independently selectable;
- the selected hand incarnation becomes former, and its library-bottom incarnation has a new ID;
- the Draw consumes the actual prior top and creates another new hand identity;
- all other library ordering remains stable;
- executing and declining evidence serializes deterministically.

The empty-library result from Audit #1 is unchanged. If a card is selected from hand while the
library is empty, that successful movement first makes it the sole library card; the conditional
Draw then draws that card under CR 121.1, producing a second new identity and no empty-library
loss. Decline does not cause a Draw. No disconnected or broader Draw behavior was added.

## Coverage freeze

An independent traversal of the authoritative 472-print / 332-Oracle-object snapshot reproduced:

- recognized: **1 Oracle object / 1 fragment**;
- bounded executable: **1 / 1**;
- fully supported: **1 / 1**;
- sole member: **Manhole Missile**;
- frozen exposure: Manhole Missile in **two decks**, `casey_jones` and `raphael`;
- membership digest:
  `cb1c664c8b157f87bace7c9a2012bb69ab598e1d142cc6a2024e532575b443e8`.

Generic Draw, Discard, loot/rummage, unrelated hand/library filtering, top-card selection, Scry,
mill, search, shuffle, quantity variants, and different source-zone variants remain outside this
bounded semantic. No card-name dispatch was found.

Manhole Missile's Deal Damage fragment is fully supported only because its existing fixed damage
parent and the complete represented optional filtering/conditional Draw follow-up are executable.

## Acceptance replay

The exact parent commit was independently exported and replayed. Each corrected candidate seed
was then run twice.

| Seed | Parent | Corrected candidate | Action #9 | Duplicate |
|---:|---|---|---:|---:|
| 7001 | Raphael, turn 16 | Raphael, turn 14 | 1 | byte-identical |
| 7002 | Raphael, turn 16 | Raphael, turn 20 | 1 | byte-identical |
| 7003 | Leonardo, turn 19 | Leonardo, turn 19 | 1 | byte-identical |
| 7004 | Leonardo, turn 21 | Leonardo, turn 21 | 0 | byte-identical |
| 7005 | Raphael, turn 16 | Raphael, turn 16 | 1 | byte-identical |

Aggregate corrected evidence:

- **37 unsupported events / 13 exact pairs**;
- **4 actual Action #9 transactions**;
- **1 block-restriction rejection**;
- **0 invariant violations**.

The parent independently reproduced **40/14**. All four former Manhole Missile limitation events
disappear and the Manhole pair is the only removed pair; no pair is added. Relative to simply
subtracting those four events, downstream deterministic trajectory changes contribute a net +1:

- Leonardo, Big Brother Sneak: 5 -> 7;
- Wingnut unsupported Alliance choice: 3 -> 4;
- Leonardo, Sewer Samurai graveyard/finality limitation: 3 -> 2;
- Leonardo, Sewer Samurai Sneak limitation: 3 -> 2.

The +3 additional and -2 avoided downstream occurrences net to the one extra event. This is
legitimate changed gameplay, not reporting instability or suppressed limitations. The corrected
choice timing does not alter the already-valid Action #9 choices in these five games, so Audit #1's
causal seed-7001 and seed-7002 trajectory explanations remain applicable.

## Regression gate

- full suite: **437 passed / 1 skipped**;
- Action #9: **22 passed**;
- Action #9 + SemanticCoverage + card data + Deal Damage: **61 passed**;
- broader library/Stack/cost/Priority/identity/SBA/combat regressions: **192 passed**;
- Ruff format check: clean;
- Ruff check: clean;
- `git diff --check`: clean;
- Audit #1 hash: unchanged;
- corrected candidate fingerprint: unchanged.

No contradictory evidence or remaining material acceptance blocker was found.

## Verdict

ACCEPT — corrected bounded optional hand-bottom filtering followed by conditional Draw is suitable to bank.
