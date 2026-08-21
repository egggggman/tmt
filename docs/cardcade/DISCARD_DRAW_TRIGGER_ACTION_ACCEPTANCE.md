# Optional Discard / Conditional Draw Attack-Trigger Acceptance Audit #1

Status: **REJECT**  
Audit date: 2026-08-20  
Branch: `agent/cardcade-discard-draw-trigger`  
Evidence checkpoint: `04aa22d182911ebf89c0c28c4a0aadfe9bc21c28`  
Audited candidate fingerprint: `000bb1f11a086c5a8a3132aa6114bd2cafcd0949`

## Audit integrity

This was an evidence-only audit. No implementation or test file was modified. This report is the
only tracked artifact created by the audit. The candidate fingerprint was independently reproduced
before the probes as SHA-1 of the newline-joined, path-sorted complete-file SHA-256 values for the
five candidate files. It remained
`000bb1f11a086c5a8a3132aa6114bd2cafcd0949` after all probes and validation.

Local and remote checkpoint HEAD both remained
`04aa22d182911ebf89c0c28c4a0aadfe9bc21c28`. The pre-audit candidate changes remained
uncommitted.

## Rules basis

The audit used Wizards of the Coast's current Comprehensive Rules text, effective August 7, 2026,
from `https://media.wizards.com/2026/downloads/MagicCompRules%2020260819.txt`:

- CR 117 governs Priority and the all-pass condition for resolving the top stack object;
- CR 400.7 makes a zone-changing card a new object unless an exception applies;
- CR 508.3 governs abilities that trigger when a creature attacks;
- CR 603.1–603.3 governs trigger conditions, automatic triggering, and placement on the Stack;
- CR 608.2c–d requires instructions to execute in written order and non-target choices to be made
  when the effect calls for them;
- CR 701.8a defines discard as moving a card from its owner's hand to that player's graveyard;
- CR 121.1 defines Draw as moving the top card of a library into its owner's hand;
- CR 704.5b makes failure to draw from an empty library a state-based loss.

## Lifecycle and trigger-condition audit

The positive-path engine lifecycle is real and correctly ordered:

1. the legal declare-attackers option identifies Null Group Biological Assets by authoritative
   runtime identity;
2. declaration creates one typed `attackers_declared` rules event whose subject is that attacker;
3. one pending trigger and one independent authoritative triggered-ability stack object are created;
4. the active player and nonactive player receive engine-generated PASS options;
5. resolution is permitted only after both PASS actions;
6. the immutable hand choice is constructed during resolution, not during attack declaration or
   trigger creation;
7. a selected authoritative Hand object moves to Graveyard as a new object;
8. the successful movement gates the conditional Draw;
9. the typed Action event and immutable transaction evidence are recorded;
10. the trigger finishes resolving and the engine reaches its SBA boundary.

At the choice callback, the trigger was already stacked and both players had passed. Priority state
was `resolution_pending`; no legal Priority action existed. Thus the candidate neither asks the
Pilot early nor opens an improper Priority window inside resolution.

The recognized executable trigger condition is generically derived from either `this creature` or
the authoritative source name followed by `attacks`. Runtime delivery iterates the authoritative
declared attackers, not every battlefield object. Independent probes established:

- declaring Null Group itself as an attacker creates exactly one pending trigger, one stack object,
  and one transaction;
- declaring another creature while Null Group remains on the battlefield creates none;
- merely existing in combat or blocking does not invoke the attack-trigger delivery path;
- stale and fabricated attacker objects are rejected;
- the engine has no represented enters-attacking path for this Action, and existing Sneak
  tapped-and-attacking semantics remain explicitly unsupported;
- one legal authoritative declaration cannot contain the same runtime attacker twice, so one
  attack event cannot duplicate this trigger.

The transaction is therefore attached to the correct represented trigger condition. This portion
of the gate passes.

## Choice, movement, and conditional-Draw audit

The Pilot receives frozen `DiscardDrawView` and `DiscardDrawOption` values containing IDs and card
names, never mutable authoritative objects. Executable and adversarial probes confirmed:

- decline mutates neither Hand, Library, nor Graveyard and performs no Draw;
- an empty Hand exposes only decline;
- one-card and multi-card Hands expose exactly the authoritative identities plus decline;
- equal-valued cards remain distinct choices;
- fabricated and stale choices are rejected;
- a stale plan is rejected before commitment;
- failed movement cannot call Draw or append evidence;
- successful discard creates a new Graveyard identity and retires the selected Hand identity;
- the pre-Draw top identity becomes a distinct new Hand identity;
- Hand, Library, and Graveyard ordering is deterministic.

The conditional Draw is caused by successful movement, not by proposing or selecting a choice.
This transaction behavior passes.

## Immutable evidence blocker

The serialized Action #10 record preserves the full offered-choice set, ordered pre/post Hand,
Library, and Graveyard identities, selected Hand identity, new Graveyard identity, movement result,
conditional-Draw result, pre-Draw top identity, drawn Hand identity, source ID, stack-object ID, and
Oracle fragment. A real seed-7001 record independently reconstructed all three post-zone sequences
exactly without consulting live zones.

However, the Action record does **not** preserve the triggering `RulesEvent` ID, event kind, or
attacker subject IDs. Its `event_id` is the later `discard_draw` Action event, not the
`attackers_declared` event. A stack-object ID and source ID cannot independently prove which event
caused the ability to trigger. Reconstruction of
`attack declaration -> trigger identity/context -> stack object` therefore requires consulting the
separate mutable event log, contrary to the audit's Action-evidence-only requirement.

This is a material evidence-provenance blocker. The smallest correction is to copy immutable
trigger-event provenance from `TriggeredAbilityObject.event` into `DiscardDrawEvidence` at
resolution: at minimum the triggering event ID, `attackers_declared` kind, controller/player, and
subject attacker IDs. Snapshot serialization and deterministic tests must preserve those fields and
prove the Action record alone links the transaction to the qualifying attack.

## Empty-library SBA blocker

The empty-library probe discarded successfully, then attempted its conditional Draw. The immutable
record correctly states `movement_succeeded=True`, `conditional_draw_performed=False`, no pre-Draw
top, and no drawn object. It does not silently manufacture a card or reuse the discarded card.

The loss timing is nevertheless incorrect. Runtime ordering was:

`zone_changed(discard) -> player_lost -> discard_draw event/evidence -> trigger_resolved -> SBA`

`Game.draw` sets `lost`, winner, and logs `player_lost` immediately while the trigger is still
resolving. CR 104.3c and 704.5b require the failed-draw loss at the next state-based-action check,
after resolution completes. Action #9 never exposed this because its successful bottom movement
guaranteed a nonempty library. Action #10 newly exposes the empty-library boundary and cannot claim
the complete fragment as fully supported while applying its loss before the correct rules boundary.

The smallest correction is to record an authoritative pending failed-draw condition when Draw
cannot be completed, finish the resolving trigger and immutable Action evidence, then apply the loss
in the existing post-resolution SBA processing. This need not broaden supported Draw patterns or
change successful Draw behavior.

## Coverage audit

The authoritative 472-print / 332-Oracle-object corpus was independently enumerated by unique
Oracle ID and exact fragment membership:

| Classification | Exact result | Digest |
|---|---:|---|
| Recognized | 2 objects / 2 fragments | `0adbade241a770917df78da65282c73d2296a5fe8511f24bff46a47005549065` |
| Bounded payload executable | 2 / 2 | `0adbade241a770917df78da65282c73d2296a5fe8511f24bff46a47005549065` |
| Fully supported | 1 / 1 | `71732520f3cf6094c7ea9d2dee6377d5677cb6448a7876ba803cda9bbc200821` |

Exact recognized membership is Cool but Rude and Null Group Biological Assets. Exact full
membership is Null Group Biological Assets.

Cool but Rude remains payload-executable but parent-incomplete with
`discard_draw_attack_trigger_context_not_implemented`; its player-attack/Class parent is not
silently promoted. No source-card-name dispatch exists in the interpreter or transaction.

Discard costs, opponent/random selection, multiple or variable discard, discard payoffs,
replacement effects, Class leveling, broader trigger forms, and unrelated Draw patterns remain
outside bounded support. The coverage membership and digests pass, although Null Group's final
full-support claim must remain gated by the two blockers above.

## Acceptance replay and causal reconciliation

The committed checkpoint was independently extracted to a temporary directory and replayed twice:

- baseline: **37 unsupported events / 13 exact pairs**;
- winners/turns: Raphael T14, Raphael T20, Leonardo T19, Leonardo T21, Raphael T16;
- duplicate outputs: byte-identical;
- block rejection: 1;
- invariant violations: 0.

The candidate was independently replayed twice:

- candidate: **33 unsupported events / 12 exact pairs**;
- 7 Action #10 transactions: seed 7001 = 2; seed 7002 = 5;
- 44 Priority grants / 44 PASS actions;
- block rejection: 1;
- invariant violations: 0;
- duplicate outputs: byte-identical.

The four removed events are the former Null Group fragment reports in seeds 7001, 7002, 7003, and
7004, one per game when that card's unsupported abilities were reported. Transaction counts measure
actual attacks after a supported permanent exists: two in seed 7001 and five in seed 7002. Seeds
7003 and 7004 reported the fragment but never produced a qualifying Null Group attack; seed 7005
did neither. Seven executions eliminating four reports is therefore coherent rather than telemetry
suppression.

Candidate trajectories were independently reproduced:

- 7001 — Raphael, turn 14;
- 7002 — Raphael, turn 18;
- 7003 — Leonardo, turn 19;
- 7004 — Leonardo, turn 21;
- 7005 — Raphael, turn 16.

Seed 7002's five legal transactions discarded, in order: Raphael's Technique, Cool but Rude, Cool
but Rude, Mountain, and Raphael, Most Attitude. The third transaction drew Wingnut, Bat on the
Belfry on turn 14. The baseline did not naturally draw Wingnut until turn 20; the candidate cast it
on turn 16, attacked with it on turns 17 and 18, and its additional combat damage contributed to
Leonardo reaching zero life on turn 18 instead of turn 20. The changed result is a deterministic,
rules-connected consequence of the supported filtering transaction, not a balance claim.

## Validation

| Gate | Result |
|---|---:|
| Full suite | **458 passed / 1 skipped** |
| Action #10 | **21 passed** |
| SemanticCoverage + card data | **10 passed** |
| Trigger / Stack / cost / identity focused gate | **61 passed** |
| Action #9, library, Scry, trigger, Stack, cost, identity, turn/combat/SBA regressions | **131 passed** |
| Ruff format | clean |
| Ruff check | clean |
| `git diff --check` | clean |
| Candidate fingerprint after validation | `000bb1f11a086c5a8a3132aa6114bd2cafcd0949` |

Passing tests do not override the independently observed provenance and SBA-timing defects. The
current empty-library test in fact asserts the premature loss, so it documents current behavior
rather than proving rules-correct timing.

## Decision

The represented attack condition, trigger/Stack/Priority lifecycle, instruction-time Pilot choice,
zone transaction, conditional Draw, corpus classification, telemetry reduction, and deterministic
gameplay evidence are otherwise sound. Banking is blocked only by the missing immutable
trigger-event provenance and premature empty-library loss boundary. Both corrections are narrow
and should preserve successful gameplay, coverage memberships, and Acceptance trajectories.

**REJECT — add immutable triggering-attack provenance to Action #10 evidence and defer failed-empty-library Draw loss to the post-resolution SBA boundary.**
