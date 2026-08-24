# Coverage-Aware Engine Smoke Stage 0.1 — Combat-Damage Readiness Failure Audit #1

## Verdict

**VALID FAIL-CLOSED STOP — a previously unexercised terminal combat/SBA and shared-driver coordination defect caused an already-resolved combat-damage step to be requested again.**

No Action, Pilot, deck, Smoke matrix, or semantic-evidence defect is established by this failure.

## Frozen evidence

- Execution baseline: `33418ccd956a2387ac8c15ec6c9493cd527c0b0e`
- Failure evidence commit: `7a15cee`
- Failure artifact: `COVERAGE_AWARE_ENGINE_SMOKE_STAGE_0.1_FAILURE_02.json`
- Failure SHA-256: `1824cdd3be58a6f52a4a8c942d86ba42127867f874eff8e433500e49f3984082`
- Sidecar verification: exact match
- Results artifact: absent
- Completed distinct games: `20`
- Completed duplicate executions: `40`
- Failed execution ordinal: `41`, duplicate member `first`
- Failed game: `april_oneil--michelangelo:canonical:8011`
- Failure state: turn 16, `combat_damage`, empty Stack, no Priority

The audit did not modify implementation or tests and did not restart Smoke Stage 0.1. It performed one isolated deterministic replay of the failed game with an external read-only tracing wrapper around `resolve_combat_damage()`.

## Reconstruction

The failed combat had one regular combat-damage step; First Strike and Double Strike were not involved.

During turn 16 combat damage:

1. Michelangelo's attacking creatures assigned combat damage, including lethal player damage.
2. `Zoo Escapees` and `Buzz Bots` dealt combat damage to one another.
3. The lethal-damage SBA moved Buzz Bots from the battlefield to its owner's graveyard.
4. The authoritative `CREATURE_DIED` event created the accepted dies/Draw trigger.
5. That trigger was put on the Stack and Priority epoch 1 began.
6. The life check then recorded April's loss for life zero or less and set Michelangelo as winner.
7. `resolve_combat_damage()` returned with the regular step authoritatively resolved, winner set, and the dies/Draw Stack/Priority work still exposed.
8. The shared Stage #002/Smoke driver drained Priority despite the terminal winner state. Both players passed and the Buzz Bots trigger resolved, drawing an Island after the game had already ended.
9. Priority and Stack were now empty, but the engine remained at `COMBAT_DAMAGE` with `_combat_damage_resolved = True` because terminal state prevented normal post-damage advancement.
10. `_resolve_combat_damage_steps()` loops solely on the turn step. It therefore called `resolve_combat_damage()` a second time.
11. The engine's readiness guard correctly rejected the duplicate request with `combat damage step is not ready to resolve` before mutation.

The final serialized state—combat damage step, empty Stack, no Priority—is therefore the state after the inappropriate post-game Priority drain, not the state immediately after the first damage resolution.

## Question 1 — What made the step not ready?

The one regular damage step had already resolved. `_combat_damage_resolved` was `True`; this was not a pending second strike step. The authoritative trace showed:

- before first turn-16 call: `kind=regular`, `resolved=False`, `winner=None`;
- after first call: `kind=regular`, `resolved=True`, `winner=michelangelo`, one Stack object, Priority epoch 1;
- before rejected call: `kind=regular`, `resolved=True`, `winner=michelangelo`, empty Stack, no Priority.

Thus the readiness rejection was correct.

## Question 2 — Which layer requested resolution anyway?

The shared driver in `stage002._resolve_combat_damage_steps()` made the rejected request. Smoke reuses that accepted helper; it contains no separate Smoke combat implementation.

The helper currently repeats while `game.step == COMBAT_DAMAGE`, without treating `game.winner` as terminal before draining Priority or before requesting another damage step.

There is also a contributing generic engine boundary: combat damage currently calls `check_state_based_actions()`—which may place dies/Draw triggers on the Stack and begin Priority—before the separate life check establishes the winner. This exposed Stack/Priority work for a game that had already ended from the same combat-damage/SBA boundary.

Stage #002's accepted regressions covered ordinary combat, single and simultaneous damage-created triggers, and First Strike followed by regular damage. They did not cover combat that both creates trigger work and ends the game. The latent shared assumption therefore survived Stage #002 and was first reached by Smoke execution #41.

## Question 3 — Smallest generic correction

The correction should be bounded to terminal-state coordination and must preserve the accepted nonterminal combat/Priority paths:

1. At the authoritative post-damage SBA boundary, establish terminal life-loss state before exposing pending trigger work to Priority. If the game has a winner, no new Priority cycle or trigger resolution may proceed.
2. Make the shared combat-damage driver stop immediately when `game.winner` becomes non-`None`, both before draining Priority and before another loop iteration.
3. Retain the existing readiness guard; do not make duplicate combat-damage resolution legal.
4. Preserve ordinary one-step combat, simultaneous nonterminal triggers, and First Strike → Priority → distinct regular-damage progression.

The regression that closes this defect must prove that combat damage can simultaneously create a dies trigger and produce lethal player damage; the player loss ends execution, the trigger does not resolve or draw, combat damage is recorded exactly once, and no second damage call occurs. A nonterminal version of the same combat must retain the accepted Stack/Priority lifecycle.

No Buzz Bots, named-card, deck, Action #13, or Smoke-specific branch is justified.

## Fail-closed assessment

The engine correctly rejected the duplicate damage request without mutation. The Smoke runner wrote a valid atomic failure artifact and matching sidecar and did not write a successful results artifact. The 20 completed games remain diagnostic progress only and are not resumable or balance evidence.

## Gate

- Smoke Stage 0.1: **BLOCKED**
- Action #13: remains accepted
- Engine readiness guard: behaved correctly
- Shared terminal combat/Priority coordination: correction required
- Action #14, Pilot/deck changes, calibration, and Prototype 0.3: not authorized

**VALID FAIL-CLOSED STOP — correct the generic terminal combat/SBA and shared-driver boundary, independently audit it, integrate it, and restart Smoke from game #1.**
