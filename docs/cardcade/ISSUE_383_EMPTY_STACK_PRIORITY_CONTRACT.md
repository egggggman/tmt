# Cardcade Issue #383 — Empty-Stack Priority Integration Contract

**Status:** REVIEW CANDIDATE / DESIGN ONLY — not an accepted engine implementation or gameplay authorization.
**Source examined:** accepted `main` `10d2ac80ef5b81b3a209a3133eb0a84633a1f944` (2026-11-06).
**Related draft changes:** PR #381 `b4e1fc437079faac582a477259f93a0de277283a`, PR #382 `013248622442d58246274f90291be74ede9a2c23`.
**Governance:** Baseline 005 and historical G: evidence frozen. No complete-game tests, calibration, deck edits, merge or unrestricted CI authorized by this contract.

## Reproduced source-level omission (no games executed)

- `src/tmnt_design_studio/stage002.py::_drain_priority` acts **only if** `game.priority_state is not None`. It does not establish a window.
- `_begin_turn_with_priority` advances steps, then drains existing priority. It does not open an empty-stack window if entering a step produced no stack object.
- `run_game` advances **precombat main → beginning of combat → declare attackers** with two calls to `advance_step` and no intervening priority drain. It progresses through combat and later calls `end_turn` without a normal empty-stack end-step priority decision.
- `src/tmnt_design_studio/engine07.py::transition_to` checks an unresolved **stack**, but does not require closure of an open priority window; `_on_enter_step` can enqueue triggers. `legal_priority_actions` requires a preexisting `PriorityState`.
- `execute_priority_action` already models the two-player pass sequence and `process_priority_resolution` already closes an all-pass **empty-stack** window by clearing `priority_state`. Reuse these implementations; do not invent a second pass protocol.
- PR #381 exposes Tunnel Rats at an already-open empty-stack window and PR #382 exposes Frog Butler Reach at an already-open stack window. Neither creates the missing natural empty-stack windows.

## Required rules-facing contract

1. **Window ownership:** an eligible step/phase requires its legal entry events and mandatory triggers to be processed first. Then the **active player** receives priority, except where actual rules or existing accepted machinery require a different continuation. An existing stack window must not be duplicated or reset.
2. **Passing with an empty stack:** the first pass transfers priority to the other player. Both consecutive passes close the window without resolving an object. A legal action resets the pass cycle and follows the existing legal-action/revalidation machinery.
3. **Passing with a nonempty stack:** both passes resolve exactly the top stack object via existing `process_priority_resolution`; subsequently grant priority again as required, including when the stack has become empty. Do not automatically advance steps after one object resolves.
4. **Step boundary:** do not progress to the next step while an eligible window is open, passes incomplete, or the stack unresolved. Expire unspent floating mana at **step/phase exit**, not at priority pass, spell announcement, or resolution. Preserve all existing same-step resource accounting.
5. **Representative natural windows:** draw and upkeep after required events; beginning of combat before attackers are declared; after attackers are declared before blockers; after blockers are declared before combat damage; end of combat; end step. Confirm main-phase policy and any damage-step special handling instead of duplicating them. Never offer a normal priority window in untap or routine cleanup.
6. **Trigger interaction:** entering beginning of combat with Does Machines Level 3 must preserve its target/trigger ordering and authenticated event identity. Resolve pending triggers before advancing past their step. Never overwrite `priority_state` for a pending stack item.
7. **Opponent choices:** both players can act in any appropriate legal window; the pilot must see immutable engine-generated legal options. A player cannot activate a tap ability while summoning-sick, cannot spend unavailable mana, and cannot act in the other player's priority turn.
8. **Provenance:** preserve source IDs, event IDs, activation timing, counter/zone state, `priority_epoch`, and end-step data in deterministic telemetry. Passing without effects is not an authenticated activation.

## Required integration approach

**A. Capture failing non-game reproductions first.** Use directly constructed `Game` states and `_drain_priority`/step coordination only. Demonstrate that an ordinary end-step transition without a stack currently offers no Tunnel Rats activation to the Stage 002 pilot, despite sufficient resources; demonstrate a beginning-of-combat no-stack case and a post-declare-blockers Reach opportunity. The tests must fail under accepted `main` for exactly the missing window, not for unrelated semantic support absent from the old base.

**B. Minimal engine/driver coordination.** Prefer a single explicit, idempotent `ensure_priority_window`-style entrypoint in Engine that can open an eligible empty-stack window only when appropriate, plus a Stage 002 driver call at each genuinely required boundary. Guard against duplicate entry and prevent step progression until the last window closes. Do not call private window machinery without owning a documented sequencing contract. Ensure `_begin_priority_window` semantics for existing nonempty stack users are unchanged.

**C. Reconcile shared PRs.** PRs #381 and #382 both modify `engine07.py`. Finish their existing independent review requirements first; integrate serially and revalidate all selected synthetic cases at the **combined exact source head**. Do not claim the historical 112 tests cover a combined future head.

## Explicit non-game acceptance matrix

| Scenario | Required result |
| --- | --- |
| Ordinary empty-stack end step, Tunnel Rats in graveyard, five payable mana | Natural pilot-facing action before cleanup, legal return via existing stack/Priority; source remains in graveyard until resolution |
| Same window with opponent holding priority | No out-of-turn activation option for the first player |
| Beginning of combat with no trigger | Window opens before attack declaration; two passes close and permit declaration |
| Beginning of combat with Does Machines L3 trigger | Existing mandatory stack/triggers and target provenance preserved; no phantom empty window or duplicate trigger |
| Declare attackers, then non-active player responding before blocks | Both players receive legitimate priority; blocks cannot be declared until window closed |
| After attackers are declared, before blockers are declared: Frog Butler Reach | Defending player can pay `{2}` and resolve Reach so Frog can legally block a flying attacker in the upcoming declare-blockers action |\n| After blockers are declared: Frog Butler Reach | Ability can still be activated with priority, but does **not** retroactively make a previously illegal block legal; existing block assignments stay fixed |
| Two passes, no actions, empty stack | Exactly one window completes, no phantom Stack object and no duplicate progression |
| Stack resolves then empties | A follow-on legal priority opportunity exists before the step advances |
| Floating mana at same-step window and step exit | Mana remains within step; unspent mana expires only on transition |
| Win during priority or resolution | Stop promptly; no post-terminal pilot action/step |
| Duplicate/open-window or forged priority epoch | Rejected or idempotently handled; no illegal mutation |
| Game-only test collection guards | Explicitly selected synthetic node IDs; zero `run_game`/complete-game invocations |

## HOLD / exit criteria

- Draft an isolated, reviewable implementation PR with `[skip ci]` safeguards; do not trigger unrestricted tests.
- Run only **enumerated synthetic** tests and Ruff with exact SHA, tool versions, and counts. Verify tests cannot instantiate full games.
- Return an engine/driver diff, deterministic priority traces, source identities, a blocked/ready assessment, and any residual generic instant/priority limitations.
- Do **not** merge #381, #382, or the Issue #383 candidate; no complete games or calibration without separate HQ acceptance.

**Current disposition:** BLOCKED for controlled smoke until this missing natural priority opportunity is accepted and verified alongside the related mechanics.