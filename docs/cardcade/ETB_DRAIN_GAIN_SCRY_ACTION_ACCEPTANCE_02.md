# Action #14 — ETB Drain/Gain/Scry Acceptance Audit #2

Date: 2026-08-23  
Corrected candidate fingerprint: `1c608159fc4cde0e2c5dfaa5a8a30eaa7e000e2b`  
Historical rejected candidate: `7bcbf3f2681d2c1ed3d51ceec0089a7f2686c64c`  
Audit mode: evidence-only; implementation and tests were not modified or committed; Smoke Stage 0.1 was not run.

## Historical evidence integrity

Audit #1 remains byte-identical at:

`8f5e122515fb3650f058af333f9d54a762036b63521980a05ad940b4f91a188d`

It remains the authoritative historical REJECT record for candidate `7bcbf3f2681d2c1ed3d51ceec0089a7f2686c64c`.

The corrected candidate independently reconstructs from the path-sorted complete-file SHA-256 values as `1c608159fc4cde0e2c5dfaa5a8a30eaa7e000e2b`:

| Candidate file | SHA-256 |
|---|---|
| `src/tmnt_design_studio/card_interpreter07.py` | `8b8cdf938bd58cb4cc1edf55f7d76e89716836d4f5618084c8c13ce02802455a` |
| `src/tmnt_design_studio/engine07.py` | `eb3b96125041fc633d4f06003c2de2167d835ab3e2c15ba0e25f902edea642fc` |
| `src/tmnt_design_studio/smoke01.py` | `3ab87b6954b12b42ef0470b84c1383fca83148dcc49a57b64d06f8258fa31723` |
| `src/tmnt_design_studio/stage002.py` | `40cd54886fbd27059d4a22f9a6a974c6b6307188a1022115fdbde1013651288e` |
| `tests/test_etb_drain_gain_scry_action.py` | `0fc07f21984c671f69e4b57d460a6ec18966a70861ea287c8b7c68dc633dde68` |

## Verdict

**ACCEPT.** Both Audit #1 blockers are closed. The corrected candidate implements the exact bounded ETB drain/gain/Scry transaction with authenticated entry provenance, frozen trigger-controller ownership, complete parent resolution before generated-trigger delivery, terminal interruption, deterministic evidence, and unchanged surrounding engine behavior.

## Re-audit of blocker 1 — frozen trigger controller

### Legitimate controller change

The audit created the ETB trigger while player 0 controlled the entering permanent, then authoritatively moved that same battlefield incarnation under player 1's control before the trigger resolved.

The frozen trigger and ETB event continued to identify player 0 as controller. Invariants accepted the new current battlefield controller without rewriting the trigger. Normal Priority/pass resolution produced:

```text
trigger controller: 0
source current controller: 1
life totals: (20, 20) → (21, 19)
```

The original controller gained 1 and that controller's opponent lost 1. The current source controller was not substituted into the transaction.

### Departure and adversarial substitution

A source that legitimately left the battlefield after triggering retained valid immutable ETB provenance and resolved for the frozen controller. Its historical source identity remained reconstructive after the runtime object entered the represented former-object state.

The opposite attacks all failed before payload mutation and independently failed engine invariants:

- replacing the frozen ability controller with the source's new current controller;
- relinking the trigger to a second valid permanent with the same card definition;
- replacing the exact ETB event subject with a fabricated identity.

For every malformed case, authoritative state fingerprints were unchanged after rejection, no drain/gain/Scry evidence appeared, and no life or library mutation occurred.

The validator now authenticates the exact registered ETB event, source runtime identity, frozen event/ability controller, battlefield authority at entry, card definition, Oracle fragment, and represented current/former source identity. It no longer mistakes current control for trigger-creation control.

## Re-audit of blocker 2 — post-resolution generated-trigger delivery

The audit placed two independent supported “Whenever you gain life, put a +1/+1 counter on …” permanents under the Action controller, then resolved the bounded compound trigger.

Instrumentation around generic pending-trigger delivery observed two engine inspection points: the post-parent state-based-action pass and the generic post-resolution delivery pass. At both points:

```text
pending generated triggers: 2
parent trigger_resolved already recorded: true
generated child already on Stack: false
Priority exposed: none
```

The authoritative event sequence was:

```text
parent trigger_resolved: event index 50
generated child trigger_stacked: event indices 51 and 52
Priority granted only after child Stack placement
```

Neither child received Priority nor resolved before the parent completion boundary. Both remained unresolved immediately after placement and subsequently resolved through the ordinary Priority/pass lifecycle, placing one counter on each appropriate source.

The correction is generic: Action #14 leaves generated trigger instances pending. `process_priority_resolution()` completes the parent resolving object, performs state-based processing, then delivers pending triggers through the existing generic Stack mechanism before exposing the next Priority window. No Dream Beavers or Action-specific child-delivery path exists.

## Complete bounded transaction

The accepted nonterminal lifecycle independently reconstructs as:

`CREATURE_ENTERED → exact self-ETB trigger → distinct Stack object → Priority/pass → opponent loses 1 → controller gains 1 → Scry 1 → immutable compound evidence → parent trigger_resolved → generated triggers enter Stack → Priority/pass`

The payload ordering is authoritative:

1. opponent life changes by exactly `−1`;
2. controller life changes by exactly `+1`;
3. Scry inspects exactly one authoritative library-top object and commits before parent completion;
4. parent completion precedes generated-trigger Stack placement.

The immutable evidence links ETB event, Stack identity, source identity, controller/opponent, exact Oracle fragment, turn/step, pre/post life totals, Scry evidence identity, and terminal status. Later source-zone changes do not invalidate the record.

### Terminal boundary

With the opponent at 1 life, the drain establishes life 0 and the winner. Gain, Scry, parent-completion logging, and generated life-gain trigger work do not occur. The Stack and Priority state terminate coherently, and terminal evidence explicitly records the interrupted compound transaction.

### Adjacent and simultaneous entry boundaries

Adjacent/simultaneous qualifying ETBs retain distinct rules-event, trigger, Stack-object, source, and Action-evidence identities. They cannot borrow one another's entry event or source provenance. Duplicate execution remains deterministic.

## Recognition and scope

The recognizer remains constrained to the exact represented Oracle grammar:

> When this creature enters, each opponent loses 1 life and you gain 1 life. Scry 1.

The authoritative TMT/PZA/TMC corpus has exactly one fully supported member: **Dream Beavers**. The membership remains unchanged from Audit #1.

The following remain unsupported and were adversarially checked: different drain/gain amounts, optional wording, target-player forms, Scry values other than 1, reordered Scry/life instructions, non-ETB triggers, mismatched self-name forms, noncreature sources, and compound variants outside the exact grammar.

No card-name, deck, matchup, Pilot, Stage #002, or Smoke-specific gameplay dispatch was found.

## Regression and architecture findings

- Action #13 dies/Draw behavior remains unchanged, including failed Draw and trigger provenance.
- Existing ETB trigger creation/delivery and Create Token entry paths remain green.
- Terminal combat/SBA winner guards remain strict.
- First Strike → trigger/Priority work → regular damage remains coherent and deterministic.
- The duplicate combat-damage readiness guard remains strict.
- Stage #002 driver and reconciliation tests remain green.
- No unsupported near-neighbor semantic is promoted by the correction.

`smoke01.py` changes only frozen tracked-input identity bookkeeping. The canonical Git-clean engine identity independently reconstructs exactly as:

`cfb49402ea32e6460b3d262d6c5c6cd475fe7aec`

No Smoke matrix, driver, classification, or execution behavior changed. Smoke Stage 0.1 was not run.

## Independent validation

| Gate | Result |
|---|---|
| Full suite | `647 passed / 1 skipped` |
| Focused Action #14 / Action #13 / ETB / trigger / Lifelink / token / Scry / strike suite | `167 passed` |
| Focused Action #14 suite | `20 passed` |
| Ruff check | clean |
| Ruff format check | `49 files already formatted` |
| `git diff --check` | clean |

## Acceptance #001

Seeds 7001–7005 were replayed twice. All duplicate artifacts were byte-identical, all accepted trajectories remained unchanged, and every run had zero conformance stops and zero invariant-violation events.

| Seed | Winner | Turn | Duplicate artifact SHA-256 |
|---:|---|---:|---|
| 7001 | Raphael | 14 | `2aecb3e6869f1d87e54d5b993559a5bbf94af4e027024451f694c5263b405522` |
| 7002 | Raphael | 18 | `3d979d0ba371a58668ad79e4c18033b3c7abf0a3e19728200c5b3c48ad54e41d` |
| 7003 | Leonardo | 19 | `8bcb5ea8149eca548843afa593a56394afa7585ab8db5ee4d893f43e082f5a1d` |
| 7004 | Leonardo | 43 | `c0ae70e47df32b7a8092e7840f3fb5695459c5503fa2a08b397dc03f1b9eaa72` |
| 7005 | Raphael | 16 | `4564fe112476a602b30074a32368aae345e12158e062933b9d207d92d9b34f3e` |

## Decision

No material semantic, provenance, ordering, terminal-state, deterministic-execution, or scope defect remains within the bounded Action #14 acceptance contract.

**ACCEPT — corrected bounded ETB opponent-drain/controller-gain/Scry transaction is suitable to bank with frozen controller provenance and generic post-resolution child-trigger delivery.**
