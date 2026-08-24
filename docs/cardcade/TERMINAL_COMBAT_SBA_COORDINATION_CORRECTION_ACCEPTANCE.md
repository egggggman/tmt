# Terminal Combat / SBA Coordination Correction Acceptance Audit #1

## Verdict

**ACCEPT — the bounded Terminal Combat / SBA Coordination correction is suitable to freeze and integrate.**

## Audit target

- Branch: `agent/cardcade-terminal-combat-sba`
- Candidate fingerprint: `41b0a80d3050f031a9c66377f72b0a93ad769963`
- Historical pre-format fingerprint: `9c68c98f042f08f10a9cace5e72530e2abe98f7d`
- Historical pre-normalization fingerprint: `41b0a80d3050f031a9c66377f72b0a93ad769963`
- Failure evidence checkpoint: `7a15cee`
- Failure Audit #1 checkpoint: `ed774d8`
- Recorded and reconstructed engine identity: `fa29895b7f114ae98696c4ea77cf50dac46745c2`

The audit did not modify the five candidate files and did not execute Coverage-Aware Engine Smoke Stage 0.1.

## Scope integrity

The candidate contains exactly five modified files:

- `scripts/run_acceptance_match_001.py`
- `src/tmnt_design_studio/engine07.py`
- `src/tmnt_design_studio/smoke01.py`
- `src/tmnt_design_studio/stage002.py`
- `tests/test_stage002_runner.py`

The engine change is generic SBA/terminal-state ordering. Stage #002 and Smoke share the same `_drain_priority()` and `_resolve_combat_damage_steps()` implementation. Acceptance #001 retains its established driver but applies the same generic winner guards at its Priority and combat-damage boundaries. No file dispatches on a card, deck, Action #13, Buzz Bots, Pilot choice, matchup, or Smoke game identity.

The `smoke01.py` frozen identities record only the independently reconstructed Git-clean identities for the changed engine and shared Stage #002 driver. The engine identity independently reconstructed as `fa29895b7f114ae98696c4ea77cf50dac46745c2`, exactly matching the manifest value.

## Terminal SBA ordering

`check_state_based_actions()` now establishes life-total loss before dies/Draw triggers are put on the Stack or exposed to Priority. Trigger detection and immutable pending-trigger provenance remain intact, but a terminal game does not promote that pending work into an actionable Stack/Priority cycle.

`check_life()` is idempotent for a player already marked lost, preventing duplicate terminal evidence when existing callers retain their explicit life check.

Independent reconstruction of lethal player damage simultaneous with creature death established this event boundary:

1. combat damage is applied;
2. lethal creature damage creates the authoritative departure and pending dies trigger;
3. terminal life loss establishes the winner;
4. no trigger is stacked;
5. no Priority is granted or passed;
6. no trigger resolves and no card is drawn;
7. combat damage is recorded exactly once.

The pending trigger is historical evidence of the legitimate death event, not post-terminal executable work.

## Winner-aware shared driving

The shared Priority drain now stops whenever `winner` is non-`None`. The shared combat-damage driver checks the winner both before requesting a damage step and before draining damage-created Priority work. Stage #002 and Smoke stop their per-turn drivers after that shared helper reports a terminal game. Acceptance #001 applies equivalent generic guards to its legacy driver.

An adversarial audit state with an already-exposed Stack/Priority cycle was marked terminal before `_drain_priority()`. The driver left the Stack and Priority untouched, did not resolve the trigger, and did not draw. This proves the driver does not rely solely on the corrected natural SBA ordering.

## Nonterminal preservation

The equivalent nonlethal combat pattern retained the accepted lifecycle:

`creature death → trigger Stack object → Priority → two passes → resolution → Draw → combat progression`

Independent probes also established:

- two simultaneous nonterminal deaths create two distinct Stack objects and resolve two draws;
- First Strike damage can create trigger work, that work resolves through Priority, and the distinct regular damage step occurs afterward;
- ordinary nonterminal combat continues to `END_OF_COMBAT` normally.

## Terminal First Strike

An independent terminal First Strike probe used two first-striking attackers: one killed the dies/Draw blocker while the other dealt lethal player damage. Exactly one `FIRST_STRIKE` damage record was created. No regular damage step started, no trigger was stacked or resolved, and no post-terminal Priority work occurred.

This demonstrates the winner guard is not limited to the single regular-damage path that originally exposed the defect.

## Duplicate readiness guard

The existing engine readiness guard remains unchanged. An audit probe attempted a second combat-damage resolution after the first step was already resolved. The engine raised `combat damage step is not ready to resolve`, and its authoritative state fingerprint remained byte-identical before and after the rejected request.

The correction prevents valid drivers from making that request after terminal state; it does not weaken or bypass the guard.

## No special cases

The candidate contains no references to Buzz Bots, Action #13, a named deck, a named game, or a Smoke pairing. It does not alter dies-trigger interpretation, trigger payloads, card data, Pilot strategy, deck contents, combat assignment, First/Double Strike semantics, or the Smoke matrix.

## Independent validation

- Candidate fingerprint before and after audit: `41b0a80d3050f031a9c66377f72b0a93ad769963`
- Independent terminal/nonterminal/First Strike/duplicate-guard probe: PASS
- Full pytest suite: `627 passed / 1 skipped`
- Focused Terminal Combat / dies-trigger / strike suite: `103 passed`
- Ruff check: clean
- Ruff format check: `234 files already formatted`
- `git diff --check`: clean
- Smoke Stage 0.1 executions during audit: `0`

## Decision

The correction closes the terminal combat/SBA coordination defect while preserving the previously accepted nonterminal Stack/Priority and strike-step behavior. The candidate is generic, deterministic, fail-closed, and suitable for integration.

**ACCEPT — the bounded Terminal Combat / SBA Coordination correction is suitable to freeze and integrate.**
