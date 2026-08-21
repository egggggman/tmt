# Discard / Conditional Draw Attack-Trigger Acceptance Audit #2

Status: **ACCEPT**  
Audit date: 2026-08-20  
Branch: `agent/cardcade-discard-draw-trigger`  
Evidence checkpoint: `04aa22d182911ebf89c0c28c4a0aadfe9bc21c28`  
Corrected candidate fingerprint: `5291d7d51ab89b5d11f4470ca8c7b3a1d5d1d049`

## Audit integrity

This was an evidence-only audit. No implementation or test file was modified. This report is the
only tracked artifact created by Audit #2.

Historical Audit #1 remained byte-identical at SHA-256
`8b12b872172d221e3f67af1a095aec8766bd2d66f61db511e311eff575feca48`.
The corrected candidate fingerprint was independently reproduced before the audit as SHA-1 of the
newline-joined, path-sorted complete-file SHA-256 values for the six corrected candidate files. It
remained `5291d7d51ab89b5d11f4470ca8c7b3a1d5d1d049` after all probes, validation, and replay.

## Blocker #1 re-audit: immutable attack provenance

The corrected serialized Action #10 record permanently contains:

- the authoritative attack-event ID and `attackers_declared` kind;
- the event player, active player, turn, and `declare_attackers` step;
- the complete immutable subject-ID tuple;
- the qualifying attacker/source runtime ID and controller;
- the authoritative triggered-ability Stack object ID;
- the Action #10 event/transaction ID;
- the Oracle fragment and full immutable before/after transaction evidence.

### Serialized-only reconstruction

A real transaction was independently reconstructed without consulting current battlefield or combat
state. Its Action record established this complete chain:

1. attack event `event-000001` was an `attackers_declared` event on turn 1 in the
   `declare_attackers` step;
2. event player and active player were player 0;
3. its immutable subjects contained attacker `object-000058` exactly once;
4. the Action source and provenance attacker were both `object-000058`, controlled by player 0;
5. that event created the authoritative triggered ability represented on the Stack as
   `object-000059`;
6. after Priority/pass and resolution, the resulting Action #10 transaction was recorded as
   `event-000002` with its offered choices, selection, zone movement, conditional result, and
   complete post-state.

For this bounded architecture, the authoritative `TriggeredAbilityObject` is the trigger object on
the Stack; no separate mutable battlefield lookup is needed to establish the trigger-to-Stack link.
The source and stack IDs remain historical facts after their objects become former objects.

### Adversarial provenance probes

Independent probes confirmed all rejection paths occur before Hand, Library, Graveyard, or evidence
mutation:

- a fabricated equal-valued trigger with an unregistered Stack ID is rejected;
- a stale trigger not in its resolving/former state is rejected;
- a trigger whose attack-event subjects do not contain its source exactly once is rejected;
- a trigger whose controller, active player, event player, step, or event kind is mismatched is
  rejected by the same generic validation boundary;
- an already-consumed trigger Stack identity cannot validate a second transaction.

Two otherwise equivalent attacks by the same source generated distinct attack-event IDs, distinct
Stack-object IDs, and distinct transaction IDs while retaining the same legitimate attacker source.
Their provenance cannot be exchanged because validation is derived from the event carried by the
registered resolving trigger and the Stack ID can be consumed only once.

Blocker #1 is resolved.

## Blocker #2 re-audit: failed Draw and SBA timing

The bounded empty-library case was independently constructed with a valid selected Hand card and an
empty authoritative Library. Runtime evidence established the exact lifecycle:

1. the selected Hand object moved successfully to Graveyard as a new object;
2. the required Draw was attempted;
3. `draw_failed` recorded the empty-library failure and set generic engine state
   `failed_draw_pending=True`;
4. the player remained in the game, `lost=False`, and no winner existed;
5. Action #10 evidence and the remaining trigger-resolution logging completed;
6. the last event before the SBA boundary was `trigger_resolved`;
7. no Priority action existed inside resolution;
8. the next authoritative state-based check applied the generic `failed_draw` SBA;
9. only then did `player_lost` occur with `draw_from_empty_library`;
10. the pending flag cleared and the opponent became the winner.

The pending failed-Draw state passed the engine invariants between resolution and the SBA check.
Thus no remaining instruction in the resolving object is skipped merely because the Draw failed.

The mechanism is engine-generic: `PlayerState.failed_draw_pending`, `Game.draw`, and
`FailedDrawStateBasedAction` contain no Action #10 type, Oracle grammar, or card-name dependency. A
separate direct generic Draw probe reproduced the same pending-then-SBA lifecycle without creating
Null Group or an Action #10 program.

Successful Draw behavior remains unchanged. Action #9's selected-card move still guarantees a
nonempty Library before its conditional Draw; its identity, ordering, evidence, and Draw behavior
remain intact. The combined Action #9 plus engine Draw/SBA suite passed all 60 tests.

Blocker #2 is resolved.

## Coverage and architecture

The authoritative 472-print / 332-Oracle-object corpus was independently enumerated by unique
Oracle ID and exact fragment membership:

| Classification | Result | Membership | Digest |
|---|---:|---|---|
| Recognized | **2 / 2** | Cool but Rude; Null Group Biological Assets | `0adbade241a770917df78da65282c73d2296a5fe8511f24bff46a47005549065` |
| Bounded payload executable | **2 / 2** | Cool but Rude; Null Group Biological Assets | `0adbade241a770917df78da65282c73d2296a5fe8511f24bff46a47005549065` |
| Fully supported | **1 / 1** | Null Group Biological Assets | `71732520f3cf6094c7ea9d2dee6377d5677cb6448a7876ba803cda9bbc200821` |

Cool but Rude remains explicitly parent-incomplete with
`discard_draw_attack_trigger_context_not_implemented`; its player-attack/Class context is not
promoted by its executable child payload.

Discard costs, opponent/random selection, multiple or variable discard, discard payoffs,
replacement effects, Class leveling, broader trigger forms, and unrelated Draw patterns remain
outside bounded support. Neither correction changes `semantic_coverage.py` or introduces
Action-specific fields into `SemanticCoverage`. Attack provenance exists only in Action #10
evidence; failed Draw exists only in generic engine/SBA state.

No source-card-name dispatch exists in the engine or interpreter implementation.

## Acceptance replay

Seeds 7001–7005 were replayed twice. Every duplicate output was byte-identical.

| Seed | Winner | Ending turn | Action #10 transactions |
|---:|---|---:|---:|
| 7001 | Raphael | 14 | 2 |
| 7002 | Raphael | 18 | 5 |
| 7003 | Leonardo | 19 | 0 |
| 7004 | Leonardo | 21 | 0 |
| 7005 | Raphael | 16 | 0 |

Aggregate evidence reproduced exactly:

- **33 unsupported events / 12 exact pairs**;
- **7 Action #10 transactions**;
- **44 Priority grants / 44 PASS actions**;
- **1 block rejection**;
- **0 invariant violations**;
- **0 failed Draws** in Acceptance Match #001.

The seven transactions and four removed unsupported events remain distinct metrics. The committed
baseline reported the Null Group fragment once in each of seeds 7001, 7002, 7003, and 7004 when
unsupported abilities were inventoried. The candidate removes those four reports because the
fragment is now fully supported. Runtime execution instead counts qualifying attacks after the
permanent exists: two in seed 7001 and five in seed 7002. Seeds 7003 and 7004 expose the card text
but never execute a qualifying attack; seed 7005 does neither. The telemetry reduction is therefore
truthful rather than suppressed or equated with transaction count.

Because no Acceptance game reaches the empty-library case, the failed-Draw correction is
behavior-neutral in these seeds. The provenance correction changes serialized evidence only. The
accepted candidate trajectories and action counts remain stable.

## Regression gate

| Gate | Reproduced result |
|---|---:|
| Full suite | **462 passed / 1 skipped** |
| Action #10 | **25 passed** |
| Action #9 + engine Draw/SBA | **60 passed** |
| SemanticCoverage + card data | **10 passed** |
| Prior Action regressions | **201 passed** |
| Trigger / Stack / Priority / identity / turn-state focused suite | **59 passed** |
| Ruff format | clean |
| Ruff check | clean |
| `git diff --check` | clean |

Focused and full validation covered trigger/Stack/Priority sequencing, attack-event identity,
Hand/Graveyard/Library runtime identity, failed-Draw pending state, SBAs and invariants, Scry/library
ordering, Action #9, all previously accepted Actions, and deterministic evidence serialization.

## Decision

Both material blockers from Audit #1 are resolved by narrow, architecture-consistent corrections.
The candidate now supplies self-contained immutable attack provenance and CR-correct failed-Draw
loss timing without changing coverage, successful gameplay, Pilot strategy, decks, or unsupported
semantic boundaries.

**ACCEPT — corrected bounded optional Discard followed by conditional Draw under an authoritative attack trigger is suitable to bank.**
