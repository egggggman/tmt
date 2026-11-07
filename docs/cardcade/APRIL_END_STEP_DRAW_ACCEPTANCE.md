# Cardcade — April O'Neil End-Step Draw

**Authorization:** HQ Issue #387
**Validated code commit:** `64bbfacd281b45d70d5daf45e224653af67bff2e`
**Starting source:** `738cc1cf1ea5b0d72f0e13edecb650af987e1723`
**Branch:** `review/cardcade-april-end-step-draw`
**Base:** `review/cardcade-smoke001-pizza-closure` at the starting source above
**Status:** draft follow-up; no merge or complete-game run

## Source preservation

The isolated worktree was created from the exact approved Pizza HEAD. Accepted
`main` remains `10d2ac80ef5b81b3a209a3133eb0a84633a1f944`. PR #386 remains draft,
open, unmerged at `8f9ed012fc367118d457fa0b0629598b7f03c15e`; PR #388 remains
draft, open, unmerged at the starting source. Neither branch was changed.

Smoke 001's nine retained files were rehashed against its
`artifact_sha256.json`; all eight listed artifacts match. The frozen card-data
snapshot and manifest remain SHA-256
`56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402` and
`6b5271af75150a361f77e7b89306c709959dfdf497c448dfdc978e5dc9a17950`.
The April record is Oracle ID `d379a919-02cd-46fd-a6ce-b66a77745ae7`, type line
`Legendary Creature — Human Scientist`, with exact text:

> At the beginning of your end step, draw a card for each card type among
> spells you've cast this turn.

Frozen OBL Baseline 005 manifest SHA-256 remains
`532bad7e489eb25f3184b5a90487e1361f7a2b19b8c02cac3c4115a0fc3e14bc` and its
frozen deck file remains
`3323ea89d62e1b05d5482f2ad30076081cb5f54b6ea6991546fa266b230e945f`.
These artifacts were read only. The protected G: archive was not accessed.

## Defect reproduction and correction

Before the implementation, the named synthetic case advanced into the
controller's end step with April on the battlefield and found zero April
trigger objects. That failing reproduction was preserved in the test history
and recorded before the correction.

The correction uses one immutable `SPELL_CAST` rules event at each supported
spell's actual authoritative move-to-Stack announcement boundary (including
the existing Sneak cast commitment). The event authenticates the original Stack object,
controller, Oracle ID, type line, event ID, turn, and source ID. Countering a
spell or moving its permanent does not erase that historical event. Card types
are parsed from the type-line type segment, excluding supertypes and subtypes;
each distinct type is counted once. Opponent casts are filtered by controller.
The type vocabulary includes the full card-type set, including Artifact,
Creature, Enchantment, Instant, Kindred, Planeswalker, Sorcery, and the
nontraditional card types.

At the beginning of the active player's end step, each eligible April on that
player's battlefield receives one authenticated beginning-of-end-step event and
one normal triggered Stack object. The ordinary Stage 002 step-priority driver
then gives both players priority. The effect counts qualifying cast events
when it resolves; this follows the Oracle's “spells you've cast this turn”
condition and includes a qualifying spell cast in response before resolution.
Resolution draws that many cards through the existing draw path and logs the
April source, trigger/event identity, distinct types, cast-event lineage, and
drawn card identities. The current-turn event filter naturally expires old
cast records at a turn boundary without a duplicate mutable history ledger.
`stage002` semantic coverage recognizes the exact April Oracle fragment, so
snapshot reconciliation can authenticate execution rather than mislabel it
unsupported.

## Synthetic validation

Environment: Python 3.12.10, pytest 8.4.2, Ruff 0.16.1. All selected test
bodies were inspected and are deterministic in-memory synthetic fixtures; none
calls a complete-game runner.

The exact post-commit command selected these 14 nodes:

```powershell
$env:PYTHONPATH='C:\projects\tmt\.cardcade-april-end-step-draw\src'
$env:PYTHONDONTWRITEBYTECODE='1'
& 'C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\python.exe' -B -m pytest -q `
  tests\test_april_end_step_draw.py::test_april_creates_authenticated_trigger_at_its_controllers_end_step `
  tests\test_april_end_step_draw.py::test_zero_spell_types_draw_zero `
  tests\test_april_end_step_draw.py::test_distinct_card_types_count_once_with_multitype_spell_and_repeated_casts `
  tests\test_april_end_step_draw.py::test_april_departure_before_trigger_and_after_trigger_boundaries `
  tests\test_april_end_step_draw.py::test_april_entering_after_end_step_begins_does_not_trigger_retroactively `
  tests\test_april_end_step_draw.py::test_april_execution_reconciles_with_authenticated_spell_cast_lineage `
  tests\test_april_end_step_draw.py::test_countered_spell_remains_in_april_cast_history `
  tests\test_april_end_step_draw.py::test_spell_type_cast_during_response_is_counted_at_resolution `
  tests\test_april_end_step_draw.py::test_opponent_cast_during_april_priority_is_excluded `
  tests\test_april_end_step_draw.py::test_previous_turn_spell_events_are_excluded_after_turn_boundary `
  tests\test_spicy_oatmeal_pizza_trigger.py::test_pizza_etb_target_damage_then_controller_damage_has_authenticated_priority `
  tests\test_spicy_oatmeal_pizza_trigger.py::test_pizza_trigger_resolves_after_source_leaves_and_simultaneous_lethal_effects `
  tests\test_spicy_oatmeal_pizza_trigger.py::test_ordinary_life_loss_remains_a_terminal_win `
  tests\test_spicy_oatmeal_pizza_trigger.py::test_pizza_damage_semantics_are_card_name_independent_and_fully_supported
```

Result: **14 passed, 0 failed, 0 skipped**. The April cases cover zero and
multiple distinct types; Artifact Creature contributing two types; repeated
Creature casts; resolution-time counting; opponent exclusion; a countered
spell; source present/absent at trigger time and source departure afterward;
turn filtering; two-player priority epochs; duplicate enqueue prevention;
single authenticated execution; and snapshot reconciliation without stop
records. Four selected Pizza regressions passed unchanged, including Stack
resolution, source departure, simultaneous lethal handling, and ordinary win
compatibility. No complete games were run.

Quality checks on the validated code files:

```powershell
& 'C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\ruff.exe' format --check src\tmnt_design_studio\engine07.py src\tmnt_design_studio\card_interpreter07.py src\tmnt_design_studio\stage002.py tests\test_april_end_step_draw.py
& 'C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\ruff.exe' check src\tmnt_design_studio\engine07.py src\tmnt_design_studio\card_interpreter07.py src\tmnt_design_studio\stage002.py tests\test_april_end_step_draw.py
git diff --check
```

Ruff format check passed, Ruff lint passed, and `git diff --check` passed.
The initial post-implementation priority assertion was corrected in the
synthetic test to match the established Stage 002 contract: step transition
queues the trigger; the ordinary-step driver opens priority immediately after.

## Scope and limitations

Only the exact April Oracle fragment is recognized. Cast type evidence is
derived only from the engine's existing supported spell-announcement paths;
unsupported card casting remains outside this implementation. No new pilot
policy, deck/card data, archived evidence, or game runner was changed. The
trigger counts at resolution, not creation. No complete games, retries, smoke,
calibration, unrestricted CI, merges, or deck revisions were performed.

**Recommendation: READY FOR HQ REVIEW.**
