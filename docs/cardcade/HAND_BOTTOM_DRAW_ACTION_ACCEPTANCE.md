# Optional Hand-Bottom Filtering / Conditional Draw Acceptance Audit #1

Status: **REJECT**  
Audit date: 2026-08-20  
Branch: `agent/cardcade-hand-bottom-draw`  
Parent baseline: `4c15424494cb0de6869537d31fc2f14881711295`  
Evidence checkpoint: `03b8269c722d3acd6dadefb1996890db6e63479c`  
Audited candidate fingerprint: `07e4fabfe49f1c0b852419151b5f7e099b3648a7`

## Audit integrity

This was an evidence-only audit. No implementation or test file was modified. The candidate
fingerprint was independently reproduced as SHA-1 of the newline-joined, path-sorted manifest of
complete-file SHA-256 values for the six candidate files. It remained
`07e4fabfe49f1c0b852419151b5f7e099b3648a7` after all probes and validation. This report is the
only tracked audit artifact created.

## Rules basis

The candidate was compared with Wizards of the Coast's current Comprehensive Rules, effective
August 7, 2026:

- CR 121.1 defines drawing as moving the top card of a library to its owner's hand;
- CR 400.7 makes a zone-changing card a new object unless an exception applies;
- CR 401.2 and 401.4 govern library order and placement at a specified position;
- CR 608.2c requires a resolving spell's instructions to be followed in written order;
- CR 608.2d places non-target choices required by an effect at the point the effect calls for
  them and prohibits impossible choices.

The authoritative source used was
`https://media.wizards.com/2026/downloads/MagicCompRules%2020260819.txt`.

## Independent corpus reconciliation

An independent traversal of the authoritative 472-print / 332-Oracle-object snapshot reproduced
exactly one recognized fragment:

| Oracle object | Fragment | Recognized | Payload executable | Fully supported |
|---|---|---:|---:|---:|
| Manhole Missile | `Manhole Missile deals 3 damage to target creature. You may put a card from your hand on the bottom of your library. If you do, draw a card.` | yes | yes | yes |

The resulting totals are:

- recognized: **1 Oracle object / 1 fragment**;
- bounded executable: **1 / 1**;
- fully supported: **1 / 1**;
- frozen exposure: **Manhole Missile in `casey_jones` and `raphael`**, two decks;
- membership digest:
  `cb1c664c8b157f87bace7c9a2012bb69ab598e1d142cc6a2024e532575b443e8`.

The grammar is Oracle-derived and contains no source-card-name dispatch. Generic Draw, Discard,
loot/rummage, other hand-to-library filtering, top-card selection, Scry, mill, search, shuffle,
and quantity or source-zone variants did not inherit recognition or executable coverage.

Manhole Missile's existing Deal Damage interpretation now reports full-fragment support because
the fixed targeted-damage parent and the exact represented follow-up both report executable. The
dependent Deal Damage full-membership lock truthfully moves from 2/2 to 3/3; its recognized and
payload-executable sets do not change.

## Choice and zone transaction findings

Focused probes confirmed the sound parts of the bounded transaction:

- the pilot-facing `HandBottomDrawView` and `HandBottomDrawOption` values are frozen and contain
  only private card IDs/names and legal ID selections, not authoritative objects or zones;
- decline, empty-hand, one-card-hand, and multi-card-hand paths are deterministic;
- decline performs neither a library move nor a Draw;
- a selected authoritative hand object becomes former, its library incarnation has a fresh ID,
  and insertion at index zero is the authoritative library bottom while the top remains the final
  element;
- the subsequent Draw consumes the pre-Draw top and creates another new hand incarnation;
- with an initially empty library, the selected card first becomes the sole library card and is
  then legally drawn. It changes identity twice and no empty-library loss occurs. Declining does
  not instruct a Draw. The bounded sequence therefore does not invent an empty-library outcome;
- fabricated options and stale plans are rejected; a stale child plan does not partially bottom a
  card or perform a Draw;
- equal-valued definitions remain separated by runtime IDs;
- Scry ordering regressions remain green.

## Material blocker 1: resolving choice occurs before Deal Damage

The authoritative mutations are logged in Oracle order, but the choice itself is not obtained in
Oracle order. In `resolve_top_of_stack`, the engine calls `choose_hand_bottom_draw` before calling
`deal_damage`; it merely delays `commit_hand_bottom_draw` until afterward. Thus the actual engine
interaction is:

`optional choice/preflight -> Deal Damage -> bottom -> Draw -> spell leaves Stack -> SBA`

rather than the required:

`Deal Damage -> optional choice -> bottom -> conditional Draw -> spell leaves Stack -> SBA`.

The current private view happens to contain only the hand, so Acceptance Match outcomes are not
shown to be incorrect by this ordering. Nevertheless, it is a concrete CR 608.2c/608.2d lifecycle
defect and contradicts the acceptance contract. A future supported interaction that changes the
choice state during the preceding instruction would make the preselected plan stale or
observationally wrong.

The smallest correction is to obtain and validate the optional choice at its written point after
Deal Damage, then atomically validate/commit the child bottom-and-Draw transaction. Failure of the
child transaction must leave no partial bottom/Draw mutation; it need not erase an already
completed preceding damage instruction.

## Material blocker 2: transaction evidence is not reconstructive

`HandBottomDrawEvidence` and its snapshot serialization retain only:

- event/player/source/Oracle IDs;
- selected old hand ID;
- bottomed new library ID;
- pre-Draw top ID;
- drawn new hand ID;
- a decline boolean.

They do **not** preserve the offered option set, complete pre-choice hand and library ordering,
complete resulting hand and library ordering, or an explicit successful-movement/condition
outcome. The separate zone-change event stream supplies some individual transitions, but it also
does not record the offered choices or complete before/after zone facts. Consequently an auditor
cannot reconstruct every required fact from immutable historical evidence without consulting or
inferring from state that is not captured by the transaction record.

This is material under the stated gate. The smallest correction is to extend the immutable typed
evidence with the offered IDs, selected/declined outcome, pre-hand IDs, pre-library IDs, movement
success/condition result, bottomed incarnation ID, pre-Draw top ID, drawn incarnation ID, and
post-hand/post-library IDs. The snapshot must serialize those fields deterministically. This does
not require changing the bounded semantic coverage or broadening Draw support.

## Sequential resolution and SBA boundary

Once the premature choice has been obtained, mutation order is otherwise correct. Damage is
applied with post-damage processing deferred; the selected card is bottomed, the conditional Draw
occurs, the spell moves Stack to graveyard, and only then do SBAs, life checks, and pending-trigger
delivery run. Lethal creature damage therefore does not remove the target between the spell's
damage instruction and its filtering instruction. No partial bottom-then-Draw failure was found.

## Acceptance replay and telemetry

The exact parent commit was independently exported and replayed, rather than relying on the prior
report. Duplicate candidate runs were also generated independently.

| Seed | Parent result | Candidate result | Action #9 transactions | Duplicate |
|---:|---|---|---:|---:|
| 7001 | Raphael, turn 16 | Raphael, turn 14 | 1 | byte-identical |
| 7002 | Raphael, turn 16 | Raphael, turn 20 | 1 | byte-identical |
| 7003 | Leonardo, turn 19 | Leonardo, turn 19 | 1 | byte-identical |
| 7004 | Leonardo, turn 21 | Leonardo, turn 21 | 0 | byte-identical |
| 7005 | Raphael, turn 16 | Raphael, turn 16 | 1 | byte-identical |

Reproduced aggregate evidence:

- parent: **40 unsupported events / 14 exact pairs**;
- candidate: **37 unsupported events / 13 exact pairs**;
- actual accepted filter-and-Draw choices: **4**;
- block-restriction rejections: **1**;
- invariant violations: **0**.

All four prior Manhole Missile limitation events disappear individually, and the Manhole pair is
the only removed pair. No pair is added. The remaining non-Manhole event counts change by a net
+1: Leonardo, Big Brother Sneak rises by two and Wingnut's unsupported Alliance choice rises by
one, while each of Leonardo, Sewer Samurai's two limitations falls by one. This is deterministic
trajectory churn, not telemetry suppression.

Seed 7001 bottoms Cool but Rude and draws Raphael, Tough Turtle on turn 8. The newly drawn Turtle
is cast immediately on turn 8 rather than turn 10; subsequent Raphael threats advance by two
turns, producing the turn-14 win and avoiding the baseline turn-15 Sewer Samurai exposure.

Seed 7002 bottoms Raphael, Tough Turtle and draws Null Group Biological Assets on turn 4. Null
Group is consequently available on turn 8, while the bottomed Turtle is no longer the baseline
turn-6 play. The changed board and draw sequence extends the legitimate game to turn 20, exposing
additional Leonardo, Big Brother Sneak events and the extra Wingnut Alliance-choice event before
Raphael wins. These causal chains are stable across duplicate runs.

Seeds 7003 and 7005 likewise show authoritative bottom/top movement with changed subsequent card
availability but retain their prior winner and ending turn. Seed 7004 contains no Manhole
resolution and therefore no Action #9 transaction.

## Validation

- full suite: **433 passed / 1 skipped**;
- Action #9: **18 passed**;
- Action #9 + SemanticCoverage + card data + Deal Damage: **57 passed**;
- Scry/library ordering: **19 passed**;
- Stack/cost/Priority/activation: **42 passed**;
- engine/identity/zone/SBA/Token regressions: **98 passed**;
- Ruff format check: clean;
- Ruff check: clean;
- `git diff --check`: clean;
- candidate fingerprint: unchanged.

Passing tests do not cure the two concrete acceptance-contract defects above.

## Recommendation

REJECT — obtain the optional choice after Deal Damage at its CR 608 instruction point, and extend immutable Action #9 evidence to preserve reconstructive offered/pre-state/condition/post-state facts; make no semantic or gameplay expansion.
