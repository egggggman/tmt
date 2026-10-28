# Issue 289 — combat trigger engine checkpoint and calibration gate

**Owner:** 🕹️ Cardcade. **State:** Engine trigger implemented and deterministic regression validated; unchanged Baseline 005 calibration **blocked** by separately identified material rules coverage. No games were launched, no deck lists changed, and no historical runtime or result was overwritten.

## Provenance

- Synced base: `main` at `f1cf41f07347d7f65ed1db68eec726071d082031` (merged [readiness PR #288](https://github.com/egggggman/tmt/pull/288)); [Issue #289](https://github.com/egggggman/tmt/issues/289).
- Frozen catalog: `cardcade/scryfall-tmt-pza-tmc-2026-08-13.json` and its manifest. April, Reporter of the Weird has Oracle ID `1c371003-e4f0-4d7c-b021-273176772f97` and the exact line “Whenever April deals combat damage to a player, draw that many cards, then discard a card.”
- Existing Baseline 005 manifest and Combined 007 remain at semantic runtime `d4466241f0ffeaca809cd6a05210ad53b9af1011a1d7f833de88657c1cf00924`. The new working-tree runtime identity is `c0ea09ffdf52e3c6b9eb6d33d613ef79c08f35285090db14e9e3374982b59bea`; it has **no completed control** and must not be compared directly to the old balance rates.
- All ten Baseline 005 source deck lists are unchanged. Their manifest hashes authenticate in the stored byte representation; Michelangelo and Splinter manifest hashes use CRLF line endings while the Linux checkout has LF. The project's independent Baseline 005 promotion validator passes.

## Implemented semantic family

The interpreter recognizes a generic self-reference (“this creature,” the full source name, or the name before a comma) with the complete combat-damage-to-a-player draw-that-many/discard-one clause. It does not claim neighboring combat damage, creature-damage, modified-discard, or appended clauses.

Each **positive damage actually dealt to a player** creates a dedicated immutable combat-damage rules event with source identity, controller, damaged player, damage amount, step and battlefield authority. The generic trigger enters the existing pending queue, then the APNAP stack and Priority path after damage and state-based actions. A trigger remains independent of a source that dies in the same step or leaves before resolution. At resolution, the event amount determines the draw count; the controller chooses one actual hand object to discard after drawing. Zone moves, failed draws, loss at state-based actions, unique trigger provenance, and deterministic log records use existing engine paths. A terminal game does not put new triggers on the stack.

`tests/test_combat_damage_draw_discard.py` demonstrates the frozen April card and renamed synthetic source; unblocked and blocked attacks; first/double strike between damage steps; two simultaneous sources; trample with the source dying to simultaneous damage; later source removal and new zone identity; empty and partially empty libraries; tamper rejection; terminal damage; and replay-equal snapshots. Existing strike and stack tests continue to run.

The implementation follows the [official Magic Comprehensive Rules](https://magic.wizards.com/en/rules): 510.2 (simultaneous assigned combat damage), 510.3a (damage and state-based-action triggers before priority), 510.4 (first/double strike damage steps), 603.3 (trigger placement on the stack), and 121.4 (failed draw loss at the next state-based-action check).

## Separate pilot and rules audit — material calibration blocker

In a deterministic main-phase fixture with four untapped Islands, each of **Sewer-veillance Cam** and **Bespoke Bō** has one legal cast option, but `AcceptancePilot.choose_main_action(..., "creature")` chooses `PASS` with no creature in hand. Skateboard in the same fixture is chosen. The pilot's utility selection is explicitly limited to Skateboard and Spicy Oatmeal Pizza. This establishes a selection blind spot in a legal state, though zero historical selected casts alone could not establish actual legal opportunities in the historical games.

These cards also have material unsupported effects in the frozen catalog:

| Card | Current interpreter / execution observation |
|---|---|
| Sewer-veillance Cam | Flash, optional enter/leave tap or untap, and sacrifice-to-draw ability reported unsupported. A normal main-phase cast is legal, but its intended effects cannot be credited. |
| Bespoke Bō | Enter-the-battlefield bounce and equipped +2/+1/vigilance reported unsupported. Equip activation itself is represented. |
| Skateboard | Enter-the-battlefield tap and equipped +1/+0/haste reported unsupported. Cast and equip activation are represented, but attaching to a summoning-sick 2/2 leaves power at 2 and does not make it eligible to attack. |

This differs from Magic's equipment and haste rules: an attached Equipment's static ability applies to the equipped creature, and haste permits a creature to attack without having been controlled since its controller's turn began (Comprehensive Rules 301.5 and 702.10). The existing first/double strike engine's step order and inter-step priority passed focused tests, including the new combat trigger tests. Printed haste and existing temporary haste tests pass, but equipment-granted haste is not implemented. This audit does **not** attribute April's historical rate, Raphael's rate, or any human-play finding to a single cause.

## Validation and next gate

Focused combat, strike, and stage runner tests: **99 passed**. Full pytest: **1,644 passed, 10 skipped**; the final lethal-case addition also passed in the focused rerun. Ruff check and formatting, `git diff --check`, and the Baseline 005 independent structural validator pass. Historical Baseline 005 review remains a description of Combined 007 under its old runtime, not a new control.

**Do not start 4,500 games:** utility and equipment behavior remains materially incomplete. First enable the missing generic rules families and validate deterministic casting, targeting, attachment/static effects, haste and zone recalculation. Reassess generic pilot selection using semantic action coverage rather than a card-name list. Once the resulting runtime has passed focused and full regression gates, authenticate the same ten manifest deck lists, run a fresh unchanged 45-cell, balanced-start control and deterministic replays, then compare that new evidence with the preserved Combined 007 source. Design Studio owns subsequent deck hypotheses; no deck revision or promotion is implied here.
