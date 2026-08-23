# Stage #002 Runner/Combat Coordination Failure Audit #1

## Verdict

**VALID FAIL-CLOSED STOP — the accepted engine correctly paused combat progression for
damage-created Stack/Priority work, but the Stage #002 runner requested combat-damage resolution
again instead of driving that existing Priority cycle.**

This is a runner coordination defect. It is not evidence against Action #13, the accepted
combat-trigger/Priority engine correction, the decks, or Pilot choices. No Stage #002 gameplay
result is accepted from the incomplete execution.

## Frozen evidence

- Merged execution baseline: `5fb4b28280429f88712b360ddde867ba85fa0ef1`
- Failure-evidence checkpoint: `13879da31acb3063b1565457ea116f81c7424e6d`
- Failure transcript: `ACCEPTANCE_STAGE_002_EXECUTION_FAILURE_03.log`
- Gate report: `ACCEPTANCE_STAGE_002_EXECUTION_GATE_RESULT_03.md`
- Results artifact: **not created**
- Stage #002 reruns during this audit: **none**
- Runner, engine, Actions, Pilot, decks, and tests modified during this audit: **none**

The banked failure artifacts remained unchanged during this audit.

## Reconstructed control flow

The traceback fixes the immediate path:

`execute_stage()` → `run_game()` → combat-damage loop → `_checked_action()` →
`resolve_combat_damage()` → `ValueError("combat damage step is not ready to resolve")`.

The frozen code establishes why:

1. `run_game()` uses `while game.step.value == "combat_damage"` as its entire combat-damage loop
   condition.
2. The first `resolve_combat_damage()` call completes authoritative damage, performs the existing
   SBA/trigger processing, records immutable combat evidence, and sets
   `_combat_damage_resolved = True`.
3. The accepted `_advance_after_combat_damage()` deliberately returns without changing the step
   whenever `stack` is nonempty or `priority_state` is active.
4. Control returns to `run_game()` in the still-authoritative `COMBAT_DAMAGE` step. The runner does
   not call its generic `_drain_priority()` at this boundary.
5. The loop predicate is still true, so the runner calls `resolve_combat_damage()` a second time.
6. The engine's entry guard rejects that call because `_combat_damage_resolved` is already true.

The second call is therefore caused by a runner predicate that confuses "the game remains in the
combat-damage step while Stack/Priority work is pending" with "another combat-damage step is ready
to resolve."

## Pending Stack/Priority finding

The accepted engine correction can leave `COMBAT_DAMAGE` unchanged only at this point when
`_advance_after_combat_damage()` observes Stack or Priority work. The original independently
audited failure path established that a legitimate Buzz Bots `DIES_DRAW` trigger was created by
the combat death and placed on the Stack with Priority active. The new traceback occurs on the
immediate next runner call at the same loop boundary.

The failed run did not serialize the Stack object or active game identity, so this audit does not
claim a newly observed runtime object ID, pairing, seed, orientation, or completed-game count. The
presence of pending Stack/Priority work is established by the accepted engine branch required to
return from the first damage call without advancing, combined with the second-call guard failure.

## Existing generic runner mechanism

`stage002._drain_priority(game, pilot)` already drives the represented engine-owned lifecycle:

- obtain only engine-generated legal Priority actions;
- ask the Pilot to choose among those immutable options;
- execute passes through `_checked_action()`;
- call `process_priority_resolution()` only when the engine marks resolution pending;
- continue until `priority_state` is empty.

The same runner already calls this mechanism after each main action, after attack declaration, and
after each Sneak action. Combat damage is the missing coordination boundary. No new gameplay,
trigger, Stack, Priority, Draw, or Pilot semantics are required.

## Engine rejection finding

The engine correctly rejected the second damage call. A completed damage step cannot be resolved
again merely because the turn remains in `COMBAT_DAMAGE` while triggered work is processed. The
guard prevented duplicated damage, repeated SBAs, duplicated triggers, and illegal state mutation.
The absence of a results artifact is the correct fail-closed outcome.

## Smallest evidence-backed correction

Correct only the Stage #002 runner's combat-damage driving loop:

1. request one authoritative combat-damage resolution when the engine says it is ready;
2. immediately drive any resulting Stack/Priority work through the runner's existing generic
   `_drain_priority()` mechanism;
3. only then reevaluate whether the engine remains in combat damage because a distinct later
   damage step is ready (for example, the regular step following First Strike/Double Strike), or
   has advanced to End of Combat;
4. preserve `_checked_action()` fail-closed mutation checks around every operation.

The correction must not inspect Buzz Bots, `DIES_DRAW`, Action #13, deck identity, or a Stage #002
game ID. It must not silently resolve Stack objects inside `resolve_combat_damage()` and must not
weaken the engine's damage-readiness guard.

Required regressions should cover no-trigger combat, one damage-created trigger, simultaneous
damage-created triggers, and a trigger between First Strike and regular damage. They must prove
that duplicate damage is not dealt and the existing Priority/pass sequence remains visible.

## Gate decision

- Action #13: **remains accepted**
- Combat-trigger/Priority engine correction: **remains accepted**
- Stage #002 runner combat coordination: **REJECTED pending the bounded runner-only correction**
- Stage #002 execution: **BLOCKED / INCOMPLETE**
- Next authorized work: preserve this audit, then make only the runner coordination correction and
  independently audit it before another Stage #002 execution
- Action #14, decks, Pilot, smoke/calibration, and Prototype 0.3: **not authorized**
