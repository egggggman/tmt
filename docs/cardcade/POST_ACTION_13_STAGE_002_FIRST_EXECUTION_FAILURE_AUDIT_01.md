# Post-Action #13 Stage #002 First-Execution Failure Audit #1

## Verdict

**VALID FAIL-CLOSED STOP — a legitimate Action #13 trigger exposed an engine-owned
combat-damage → Stack/Priority progression defect.**

This is not evidence that the dies/Draw trigger is illegal, that the Stage #002 runner chose an
illegal action, or that any deck or Pilot behavior is defective. No Stage #002 result was produced,
and no gameplay result is accepted from the incomplete run.

## Frozen audit target

- Post-Action #13 baseline: `5dfa187192b8e6c017dc3fc6cc399f4145d82729`
- Runner: accepted Stage #002 runner already merged on `main`
- Attempted output: `docs/cardcade/ACCEPTANCE_STAGE_002_RESULTS_03.json`
- Output status: **not created**
- Worktree after stop: clean
- Implementation/tests modified during audit: none
- Stage #002 rerun during audit: none

The original execution stopped with:

```text
ValueError: cannot advance the turn with an unresolved stack
run_game() → _checked_action(... resolve_combat_damage ...) →
Game.resolve_combat_damage() → transition_to(END_OF_COMBAT)
```

## Exact reconstructed failure path

The frozen runner iterates `stage_games()` in manifest order. The stopped call was therefore the
first execution of `donatello-krang:canonical:7201`.

The accepted pre-Action result preserves the unchanged deterministic prefix through turn 9:

1. Donatello, Way with Machines (`object-000153`) and Buzz Bots (`object-000165`) assign one combat
   damage to each other in the regular combat-damage step.
2. Lethal-damage state-based actions move Buzz Bots from battlefield to its owner's graveyard. The
   zone-change replacement is `object-000169`.
3. On the post-Action baseline, Action #13 additionally creates the authoritative
   `CREATURE_DIED` event for source `object-000165`. From the unchanged prior event sequence, this
   is deterministically `event-000018`.
4. The exact Oracle fragment `When this creature dies, draw a card.` creates the first pending
   dies/Draw trigger. Stack placement allocates the next runtime identity, `object-000170`, with
   effect `DIES_DRAW`, controller Krang, and source identity `object-000165`.
5. `check_state_based_actions()` puts that trigger on the Stack and
   `_drain_triggered_abilities()` begins the represented Priority window. No Draw has resolved at
   this point.
6. Control returns inside `resolve_combat_damage()`, not to the runner. That method finishes its
   immutable combat evidence and then unconditionally calls `transition_to(END_OF_COMBAT)` for the
   completed regular damage step.
7. `transition_to()` correctly rejects advancement because the Stack still contains the dies/Draw
   trigger. The exception propagates through `_checked_action`; `run_game()` never returns and
   `execute_stage()` never serializes a result.

The exact runtime IDs in steps 3–4 are reconstructed from the accepted deterministic pre-Action
artifact and the frozen allocation/event order. They were not serialized by the failed run itself.

## Rules and architecture finding

The current official Magic Comprehensive Rules require the relevant ordering: combat damage is
dealt, state-based actions are checked, waiting triggered abilities are put on the Stack, and the
active player receives Priority. A step does not simply advance while the Stack still contains
business requiring the all-pass/resolution sequence. The authoritative reference is Wizards of the
Coast's current rules page: <https://magic.wizards.com/en/rules>.

Cardcade's represented architecture agrees:

- Action #13 owns only exact Oracle interpretation and trigger creation;
- the engine owns state-based actions, Stack state, Priority/pass, resolution, and turn-step state;
- the Pilot chooses only from engine-generated actions;
- the Stage #002 runner invokes one engine operation at a time and drains Priority only after that
  operation returns.

The dies/Draw object therefore **must** receive the represented Priority/pass sequence and resolve
before normal combat-step progression continues. Weakening Action #13, discarding the trigger,
advancing with a nonempty Stack, or teaching the runner to ignore the engine exception would all be
incorrect.

## Defect ownership

The incorrect progression attempt is engine-owned. `resolve_combat_damage()` calls
`check_state_based_actions()`, which legitimately creates the trigger and Priority state, but the
same method then proceeds to `transition_to(END_OF_COMBAT)` without suspending for that newly
created Stack/Priority work.

The runner cannot prevent the attempt: it calls `resolve_combat_damage()` through `_checked_action`
and does not regain control until the engine operation returns. Its existing `_drain_priority()`
placement is therefore not the immediate defect boundary.

## Smallest evidence-backed correction

Correct only the engine combat-to-Priority lifecycle:

1. finish and preserve immutable evidence for the completed combat-damage step;
2. when post-damage SBAs put a represented trigger on the Stack, leave combat in an authoritative
   completed-damage state without advancing to End of Combat;
3. allow the existing engine-owned Priority/pass and Stack-resolution lifecycle to run;
4. advance to End of Combat exactly once after the Stack is empty and no represented Priority work
   remains;
5. preserve First Strike/Double Strike sequencing, terminal first-step combat, SBAs, removed-object
   evidence, and ordinary no-trigger combat progression;
6. add an adversarial regression proving combat cannot advance while the death trigger is pending
   and does advance after that trigger resolves.

This correction must not change Action #13 grammar, Draw semantics, decks, Pilot strategy, or the
Stage #002 runner merely to make the execution continue.

## Gate decision

- Action #13 acceptance: **remains valid**
- Stage #002 execution: **BLOCKED / INCOMPLETE**
- Completed games and executions: **not established**
- Gameplay outcome from the failed run: **none accepted**
- Next authorized work: preserve this audit, then make only the bounded engine combat-to-Priority
  lifecycle correction and independently audit it before rerunning Stage #002
- Action #14, deck revisions, Pilot changes, smoke/calibration, and Prototype 0.3: **not authorized**

