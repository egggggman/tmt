# Action #14 — ETB Drain/Gain/Scry Acceptance Audit #1

Date: 2026-08-23  
Candidate fingerprint: `7bcbf3f2681d2c1ed3d51ceec0089a7f2686c64c`  
Audit mode: evidence-only; implementation and tests were not modified; Smoke Stage 0.1 was not run.

## Verdict

**REJECT.** The bounded recognizer, ETB provenance, ordered drain/gain/Scry payload, terminal branch, and existing deterministic regressions are strong, but two material lifecycle defects remain:

1. a trigger that was created legally is invalidated if its source changes controller before resolution; and
2. life-gain-trigger work created during the compound resolution is put on the Stack before the parent trigger records completion.

Both defects contradict the acceptance contract's controller-attribution and deferred-trigger boundaries. Neither requires broader Oracle support or card-specific dispatch to correct.

## Frozen candidate integrity

The five audited candidate files were unchanged throughout the audit:

| File | SHA-256 |
|---|---|
| `src/tmnt_design_studio/card_interpreter07.py` | `8b8cdf938bd58cb4cc1edf55f7d76e89716836d4f5618084c8c13ce02802455a` |
| `src/tmnt_design_studio/engine07.py` | `27ef8d40d3b988d64418d8c349252f20285012a2c1b74c61ebfc66a43765a6ff` |
| `src/tmnt_design_studio/smoke01.py` | `519533b980daa790c19421cc3962b6b5ad5ada9ac3d3b29fb5f869f9a8bdd00d` |
| `src/tmnt_design_studio/stage002.py` | `40cd54886fbd27059d4a22f9a6a974c6b6307188a1022115fdbde1013651288e` |
| `tests/test_etb_drain_gain_scry_action.py` | `439baa12b6e4676533e0af63e3a90a9d2f881cd6c7ae7b3e82dc2277a36e5e42` |

The candidate fingerprint independently reconstructs as SHA-1 over the newline-separated, path-sorted complete-file SHA-256 values: `7bcbf3f2681d2c1ed3d51ceec0089a7f2686c64c`.

The worktree contained exactly those five candidate paths before this report was added. `git diff --check` was clean.

## Accepted portions of the bounded implementation

### Recognition and corpus membership

The recognizer accepts the exact generic form:

> When this creature enters, each opponent loses 1 life and you gain 1 life. Scry 1.

including its represented Scry reminder text and a valid self-name substitution. It rejects different life amounts, Scry values, optional forms, target-player forms, reordered instructions, non-ETB triggers, mismatched self names, and noncreature execution contexts.

The authoritative TMT/PZA/TMC corpus scan contains one recognized and fully supported member: **Dream Beavers**. The membership digest remains `ebe2a12cf48c49cfe23d50e7cb3d806c75f85ecffc1024aab858f894fd5977e8`.

No Dream Beavers, deck, matchup, Pilot, or Smoke-specific gameplay dispatch was found.

### Entry, Stack, Priority, and payload

For the ordinary supported case, the serialized transaction reconstructs:

`CREATURE_ENTERED` event → exact source incarnation/controller/fragment → distinct trigger/Stack identity → Priority grants and passes → opponent life 20→19 → controller life 20→21 → Scry 1 → transaction evidence.

The event ordering is drain before gain, gain before Scry, and Scry before the parent `trigger_resolved` event. The source may leave the battlefield after legitimate triggering without destroying the frozen ETB provenance. Fabricated/relinked entry subjects fail invariants and resolution before payload mutation. Adjacent/simultaneous ETBs produce distinct event, Stack, and transaction identities with deterministic serialization.

The terminal branch at opponent life 1 produces life 0, establishes the winner, records terminal Action evidence, and performs neither gain nor Scry. Existing Action #13, combat, strike, terminal-game, and ETB tests remained green.

### Smoke bookkeeping

`smoke01.py` changes only frozen identity entries necessitated by changed interpreter, engine, and Stage #002 tracked inputs. No Smoke matrix, execution, classification, or gameplay-driving behavior changed. The matrix contract remains 45 pairings / 180 distinct games / 360 executions.

## Material blocker 1 — resolution incorrectly requires the source's current controller

The ETB event and `TriggeredAbilityObject` correctly freeze controller 0 when the ability triggers. The audit then performed an authoritative control change before resolution: the same runtime permanent was removed from player 0's battlefield, assigned controller 1, and placed on player 1's battlefield. The trigger remained on the Stack with its original controller and authentic ETB event.

Both independent validation paths rejected the still-valid trigger:

```text
check_invariants: AssertionError: ETB drain/gain/Scry trigger has mismatched entry provenance
resolution:       ValueError: ETB drain/gain/Scry trigger has mismatched entry provenance
life before/after rejection: (20, 20) / (20, 20)
```

The rejection comes from requiring the current runtime source controller to equal the frozen trigger controller. That is not authoritative trigger-controller semantics. A triggered ability is controlled by the source's controller when it triggers, and after triggering it exists on the Stack independently of later changes to its source. Current source control must not rewrite or invalidate the already-frozen ability controller.

This is material even though the present bounded engine does not expose a general control-change Action: the acceptance contract explicitly requires correct last/current controller attribution, and immutable provenance must remain valid after later ordinary state changes.

### Smallest correction

Continue authenticating the exact entry event, source runtime identity, source card, Oracle fragment, and frozen event/ability controller. Do not require a still-present source's **current** controller to equal the trigger controller. If the source remains in a represented zone, its current identity and placement may be validated separately without using current controller as entry-time provenance. Add a regression in which control changes after triggering and the original controller receives the gain/Scry while that controller's opponent loses life.

## Material blocker 2 — child life-gain trigger is stacked before the parent finishes

The compound resolver correctly calls `gain_life(..., defer_trigger_delivery=True)`, but after Scry it calls `_put_pending_triggers_on_stack()` from inside the parent resolution. An independent probe used an existing supported “Whenever you gain life, put a +1/+1 counter on …” permanent. The serialized event indices were:

```text
44 life_gained
48 scry_committed
49 child trigger_stacked
50 parent trigger_resolved (etb_drain_gain_scry)
```

Thus the child is placed on the Stack while the parent resolving object has not yet completed according to the engine's own authoritative lifecycle evidence. This fails the required boundary: life-gain-trigger work must be deferred until the compound ability finishes, then receive normal Stack/Priority treatment.

Magic's triggered-ability lifecycle likewise waits to put abilities that triggered during resolution onto the Stack until after the current resolving object finishes and the next state-based-action/priority boundary is reached. The candidate defers payload execution but not Stack placement far enough.

### Smallest correction

Remove Action-local delivery of pending triggers from inside the compound resolver. At the existing generic post-resolution boundary, after the parent resolution is complete and state-based actions are handled, put pending triggers on the Stack and begin the normal Priority lifecycle. Add regressions proving:

- the parent `trigger_resolved` lifecycle completes before the child `trigger_stacked` event;
- the child remains unresolved until normal Priority/pass;
- simultaneous life-gain triggers are delivered distinctly at that boundary; and
- the terminal branch creates or resolves no later gain/Scry trigger work.

Do not introduce Dream Beavers or Action #14 dispatch into the generic post-resolution mechanism.

## Independent validation

| Gate | Result |
|---|---|
| Full suite | `644 passed / 1 skipped` |
| Focused Action #14 / dies-trigger / trigger / Lifelink / strike suite | `96 passed` |
| Action #14 candidate suite | included; `17 passed` within the focused run |
| Ruff check | clean |
| Ruff format check | `49 files already formatted` |
| `git diff --check` | clean |

The full and focused regressions therefore do not expose broader instability; the rejection rests on two independently reproduced adversarial gaps outside the candidate's current tests.

## Acceptance #001 parity

Seeds 7001–7005 were replayed twice. Every duplicate artifact was byte-identical, with zero conformance stops and zero invariant-violation events:

| Seed | Result | Turn | Duplicate SHA-256 |
|---:|---|---:|---|
| 7001 | Raphael | 14 | `2aecb3e6869f1d87e54d5b993559a5bbf94af4e027024451f694c5263b405522` |
| 7002 | Raphael | 18 | `3d979d0ba371a58668ad79e4c18033b3c7abf0a3e19728200c5b3c48ad54e41d` |
| 7003 | Leonardo | 19 | `8bcb5ea8149eca548843afa593a56394afa7585ab8db5ee4d893f43e082f5a1d` |
| 7004 | Leonardo | 43 | `c0ae70e47df32b7a8092e7840f3fb5695459c5503fa2a08b397dc03f1b9eaa72` |
| 7005 | Raphael | 16 | `4564fe112476a602b30074a32368aae345e12158e062933b9d207d92d9b34f3e` |

No Smoke execution was performed.

## Required disposition

Preserve candidate `7bcbf3f2681d2c1ed3d51ceec0089a7f2686c64c` as rejected historical evidence. Correct only controller-at-trigger-time authentication and generic post-resolution delivery of deferred trigger work, add the bounded adversarial regressions above, rerun validation and deterministic Acceptance #001, and present a new frozen candidate for Audit #2.

**REJECT — the bounded ETB drain/gain/Scry payload is otherwise well constrained, but current-controller coupling invalidates legally triggered abilities after control changes and deferred life-gain triggers are placed on the Stack before the parent compound trigger finishes; correct those two lifecycle boundaries without broadening Action #14.**
