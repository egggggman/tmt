# Cardcade Gates 2–4 Acceptance Package

**Review target:** PR #381, base `main` at `10d2ac80ef5b81b3a209a3133eb0a84633a1f944`.
**Pre-correction PR head:** `ef5d4fa44019cd744fdaf9fd9e725ad21787ca0b`.
**Correction commit:** `c8cd9407a7289b0cd87d7f4e6898a215d8216ade`.
**First evidence-package commit:** `b2bbe5827972aeca46e456a959fb01c1416e709a`.
**Working candidate engine Git blob:** `67ce3bf797d944c83c1fa02ca2287ea3b129bf93`.
**Status:** pushed to the still-draft PR; pending independent review.

## Gate 2 — Historical stop ledger

The source-linked 485-row ledger and its reproducible builder are documented in
[`CARDCade_STAGE_002_SILENT_STOP_LEDGER.md`](CARDCade_STAGE_002_SILENT_STOP_LEDGER.md)
and [`CARDCade_STAGE_002_SILENT_STOP_LEDGER.csv`](CARDCade_STAGE_002_SILENT_STOP_LEDGER.csv).
The frozen Stage 002 reconciler over the preserved archive yields 303
indeterminate, 126 conformance/provenance, and 56 reached unsupported records
across 201 games. This does not reproduce the earlier 317 / 126 / 42 aggregate.
The increase of 14 unsupported records is supported by exact stop-detail links
to the frozen reconciler's reached-unsupported set. No record membership map
for the old 42 total was present, so the ledger does not guess which old rows
would have moved. Historical game outputs remain unchanged.

## Gate 3 — Focused findings

Rules references use the official [Magic Comprehensive Rules, effective June
19, 2026](https://media.wizards.com/2026/downloads/MagicCompRules%2020260619.pdf):
117.1b (activated abilities may be activated with priority), 302.6 (tap-symbol
creature ability summoning-sickness restriction), 500.5 (mana empties as a
step/phase ends), 513.1 (the active player receives priority in the end step),
and 605.3b (mana abilities resolve immediately and do not use the stack).
Card text was read from the frozen card-data snapshot identified in the stop
ledger report.

### Tunnel Rats

The card fact is `{4}{B}: Return this card from your graveyard to the battlefield
tapped.` The frozen/accepted implementation supports its five-mana cost, black
requirement, floating-mana contribution, graveyard object authority, owner
restriction, and return as a new battlefield object tapped. The new synthetic
case advances to end step with an empty stack, opens an explicit empty-stack
`PriorityState`, then verifies the action, five-land payment, authenticated
execution, one return, and invariants. The action generator and announcement
validator now honor that existing priority state outside main phase.

Limitation: no caller currently opens an empty-stack priority window during
ordinary Stage 002 step advancement. `_begin_turn_with_priority` drains a window
only if one exists; normal end-step flow does not create one. Thus the action is
legal and executable in the represented end-step window, but the Stage 002
driver does not naturally offer that window. A general empty-stack priority
driver change would be a separate, broader proposal and is not included here.

### Frog Butler mana

The card data says `{T}: Add one mana of any color.` The ability resolves
immediately, taps its source, creates no stack object, records authenticated
activation evidence, and keeps the mana available during the producing step.
The floating-mana ledger previously was not emptied when a step ended. The
candidate empties all unspent mana on step transition and records its amount and
the step ended. A deterministic regression verifies immediate availability,
no stack use, and expiration at the next step boundary. Same-step spending and
mana lineage are covered by the existing synthetic test.

### Fugitive Droid artifact-entry condition

The existing tracker records artifact entries for setup/permanent creation,
token creation, and every zone transition that creates a battlefield
permanent. The expanded tests cover artifact creatures, noncreature artifacts,
tokens, graveyard-to-battlefield new object identity, departure after entry,
entry controller despite later control change, and clearing at a real cleanup
to next-turn transition. The existing counterexample confirms that a stolen
artifact entered under the opponent's control does not qualify.

### Frog Butler Reach

The card text is `{2}: This creature gains reach until end of turn.` It has no
sorcery-only restriction and no tap symbol, so the ability is legal whenever
its controller has priority and can pay `{2}`; a summoning-sick Frog may use
it. Current `legal_activated_ability_actions` offers it only to the active
player in an empty-stack main phase. `legal_priority_actions` omits it when a
non-mana ability or spell is on the stack. The resolution, temporary duration,
source departure, and flying-block interaction are already covered by focused
synthetics, but the response action is not offered.

This correction is narrow within the existing stack-priority model: enumerate
fully supported `GRANT_REACH_UNTIL_EOT` activations for the player holding
priority, and route them through the existing `announce_activated_ability`
executor. This is prepared separately in draft [PR #382](https://github.com/egggggman/tmt/pull/382),
HEAD `013248622442d58246274f90291be74ede9a2c23`. The engine does not open
ordinary empty-stack priority windows between steps, so that PR covers existing
stack windows while the broader timing limitation remains explicit.

## Validation

Environment: Python 3.12.10, Ruff 0.16.1.

```powershell
& .venv\Scripts\ruff.exe format --check src/tmnt_design_studio/engine07.py tests/test_frog_butler_mana.py tests/test_fugitive_droid_unblockability.py tests/test_tunnel_rats_graveyard_return.py tools/cardcade_stage002_silent_stop_ledger.py
& .venv\Scripts\ruff.exe check src/tmnt_design_studio/engine07.py tests/test_frog_butler_mana.py tests/test_fugitive_droid_unblockability.py tests/test_tunnel_rats_graveyard_return.py tools/cardcade_stage002_silent_stop_ledger.py
$env:PYTHONDONTWRITEBYTECODE='1'; $env:PYTHONPATH=(Resolve-Path src).Path; & .venv\Scripts\python.exe -B -m pytest -q tests/test_activated_abilities.py tests/test_tunnel_rats_graveyard_return.py tests/test_frog_butler_mana.py tests/test_frog_butler_reach.py tests/test_does_machines_level_three.py tests/test_fugitive_droid_unblockability.py
& .venv\Scripts\python.exe -B -m pytest -q tests/test_stage002_runner.py -k "not parameterized_runner_preserves_acceptance_001_gameplay and not calibration_member_b0011_p06_canonical_terminal_replay_is_identical and not v15_terminal_sneak_state_does_not_reenter_pilot"
git diff --check
```

Results: Ruff format check passed; Ruff lint passed; `git diff --check` passed.
The safe rerun passed 67 focused fidelity tests plus 45 non-game Stage 002
runner tests; the three runner test cases that call `run_game` were explicitly
deselected (112 passed, 3 deselected). The stop-ledger builder separately passed
against all 300 preserved result files and produced 485 rows; CSV SHA-256 is
`4476cc931b91354c076dedc543c9fea89ef5c43c62c0cf786a889a3bc7b884c5`.
The first broad selection of `tests/test_stage002_runner.py` mistakenly included
three complete-game test cases and ran six full games in memory. This violated
the no-game restriction. No workflow ran and those tests did not modify archived
results or persistent game evidence. The unfiltered result is not counted as
permitted validation. The command that caused this was `python -B -m pytest -q`
with the six focused fidelity modules followed by the whole
`tests/test_stage002_runner.py` file. Only the explicit safe rerun above is
counted as permitted validation. The
PR-triggered workflow lookup for the pushed commits returned no runs.

## Gate 5 — Readiness

**BLOCKED** for a controlled smoke test. PR #381 still needs independent review
of this updated candidate, and Frog Butler Reach PR #382 still needs independent
review. In addition, the empty-stack end-step
priority window is not opened by the current Stage 002 driver. These are
demonstrated reachability/provenance limitations, not hypothetical mechanics
coverage. No complete games, calibration, merge, or deck changes are authorized
by this package.

The frozen Baseline 005 deck manifest remains identified by SHA-256
`c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac`; the frozen
card-data snapshot is SHA-256
`56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402`. No deck
identity was changed. Gate 1's preservation-index note remains: one workspace
copy path for the historical `RUN_STOP.json` is absent, while the separate
`G:\cardcade\pre-reboot-20261103-200c45c808-39e99509\protected-state\RUN_STOP.json`
copy is intact at 718 bytes with SHA-256
`c85474eae9ed9c61fd8ce86dc352becaac9cdbe0d927fb9d1c5a215f2a4c03ff`.

## Independent PR #381 review follow-up — 2026-11-06

**Reviewed starting head:** `b4e1fc437079faac582a477259f93a0de277283a`, based on
accepted `main` `10d2ac80ef5b81b3a209a3133eb0a84633a1f944`. The protected
historical `G:` archive was read only; no archive file was written.

### Ledger source identity and row mapping

The builder was independently rerun against the 300 preserved `result.json`
files and the frozen Stage 002 source at blob
`bed173e3f4f3f13b0d1320a3a910153c38d844be`. It reproduced 300 unique runs,
485 unique ledger `record_id` values across 201 affected games, with
303 indeterminate / 126 conformance-provenance / 56 unsupported-semantic rows.
The committed CSV and read-only rebuilt output have the same SHA-256:
`4476cc931b91354c076dedc543c9fea89ef5c43c62c0cf786a889a3bc7b884c5`.
The row identities and CSV bytes therefore match the committed ledger exactly.
The existing ledger contains 0 direct raw-stop rows and 485 frozen-reconciler
derived rows. Those derived rows point to `/snapshot/conformance` and include
the reconciler stop index/hash in their record/evidence identity; no raw stop
index is claimed for them.

The frozen reconciler starts with `list(conformance["stop_records"])`, then
extends/appends its derived findings; it does not insert into or reorder that
prefix. The builder now verifies canonical equality of every raw stop against
the reconciler prefix for each run before creating any ledger source pointer.
It fails closed on raw-stop omission, insertion before the raw suffix, or raw
stop reordering. Four pure mapping regressions cover the preserved prefix,
derived identity, inserted record, reordered records, and omitted record.
The previous 317 / 126 / 42 aggregate remains unreconciled at the row level;
no old row membership map exists, so the 303 / 126 / 56 classification does
not invent identities for the old 42.

Read-only reproduction command (CSV output is local temp, not the protected
archive):

```powershell
$outPath=Join-Path $env:TEMP 'pr381-ledger-prefix-audit.csv'
$env:PYTHONDONTWRITEBYTECODE='1'
& .venv\Scripts\python.exe -B tools\cardcade_stage002_silent_stop_ledger.py --archive-root G:\cardcade\diagnostics --frozen-root C:\projects\tmt\.diag003-frozen-32a8022 --manifest docs\cardcade\ACCEPTANCE_STAGE_002_RESULTS.json --output $outPath
Get-FileHash -Algorithm SHA256 -LiteralPath $outPath
```

### Rules-path checks

- **Tunnel Rats:** the selected tests cover controller/owner, five-mana `{4}{B}`
  payment (including floating black), action freshness/source identity, the
  source remaining in the graveyard until resolution, one tapped new-object
  return, and authenticated execution. Its empty-stack end-step action is
  engine-legal when an empty `PriorityState` is explicitly open. The isolated
  PR #381 Stage 002 driver does not naturally open that window; PR #385 is the
  separately identified driver change needed for natural end-step availability.
- **Frog Butler mana:** authenticated execution indexing includes the
  immediate mana ability. Selected tests check non-stack resolution, unchanged
  priority/stack, one production event, source/tap provenance, same-step use,
  and expiration at the step boundary.
- **Fugitive Droid:** tested artifact entry through permanent creation, direct
  battlefield placement, token creation, and graveyard-to-battlefield zone
  transition. Tests cover entry controller (not later controller), one record
  per object, departure, and expiration at the next turn boundary.
- **Does Machines regression:** the previous-turn Fugitive Droid fixture now
  advances through two actual synthetic turn boundaries instead of deleting a
  private artifact-entry ledger row or editing `entered_battlefield_turn`.
  It retains an explicitly constructed synthetic blocker-decision context.

An initial version of that revised fixture failed because Does Machines only
triggers at the beginning of combat on its controller's turn. A subsequent
attempt correctly reached that trigger but tried to declare an attack for the
non-active player. The final fixture advances to the source controller's turn
and constructs only the blocker decision state under test; its selected test
passes. These were fixture errors, not engine failures.

### Bounded validation on the corrected worktree

Environment: Python 3.12.10, pytest 8.4.2, Ruff 0.16.1. Every selected test
body was inspected; the selection contains no `run_game`, launcher, runner
suite, or calibration call.

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONPATH=(Resolve-Path src).Path
& .venv\Scripts\python.exe -B -m pytest -q `
  tests/test_cardcade_stage002_silent_stop_ledger.py::test_raw_stops_keep_exact_indices_and_derived_stops_keep_distinct_identity `
  tests/test_cardcade_stage002_silent_stop_ledger.py::test_inserted_reconciler_stop_before_raw_suffix_is_rejected `
  tests/test_cardcade_stage002_silent_stop_ledger.py::test_reordered_reconciler_raw_stops_are_rejected `
  tests/test_cardcade_stage002_silent_stop_ledger.py::test_omitted_reconciler_raw_stop_is_rejected `
  tests/test_tunnel_rats_graveyard_return.py::test_tunnel_rats_exact_graveyard_semantics `
  tests/test_tunnel_rats_graveyard_return.py::test_tunnel_rats_can_activate_at_priority_and_remains_in_graveyard_until_resolution `
  tests/test_tunnel_rats_graveyard_return.py::test_tunnel_rats_is_offered_in_empty_stack_end_step_priority `
  tests/test_tunnel_rats_graveyard_return.py::test_tunnel_rats_main_action_exposes_only_when_five_lands_include_black `
  tests/test_tunnel_rats_graveyard_return.py::test_tunnel_rats_requires_a_black_source_even_with_five_available_lands `
  tests/test_tunnel_rats_graveyard_return.py::test_tunnel_rats_spends_floating_black_mana_and_four_generic_sources `
  tests/test_tunnel_rats_graveyard_return.py::test_tunnel_rats_does_not_return_if_graveyard_object_leaves_before_resolution `
  tests/test_frog_butler_mana.py::test_frog_butler_produces_chosen_color_with_source_provenance `
  tests/test_frog_butler_mana.py::test_frog_butler_mana_ability_rejects_summoning_sick_source `
  tests/test_frog_butler_mana.py::test_frog_butler_mana_is_immediate_and_empties_at_step_end `
  tests/test_fugitive_droid_unblockability.py::test_fugitive_droid_cannot_be_blocked_after_controlled_artifact_entry_even_if_it_left `
  tests/test_fugitive_droid_unblockability.py::test_fugitive_droid_does_not_get_unblockability_from_artifact_entering_for_opponent `
  tests/test_fugitive_droid_unblockability.py::test_artifact_token_entry_is_recorded_once_and_uses_entry_controller `
  tests/test_fugitive_droid_unblockability.py::test_direct_battlefield_placement_records_a_noncreature_artifact_once `
  tests/test_fugitive_droid_unblockability.py::test_artifact_moved_from_graveyard_enters_as_a_new_tracked_object `
  tests/test_fugitive_droid_unblockability.py::test_fugitive_droid_artifact_entry_condition_expires_at_next_turn `
  tests/test_does_machines_level_three.py::test_animated_artifact_can_block_as_a_creature
& .venv\Scripts\ruff.exe format --check tools\cardcade_stage002_silent_stop_ledger.py tests\test_cardcade_stage002_silent_stop_ledger.py tests\test_does_machines_level_three.py tests\test_frog_butler_mana.py tests\test_fugitive_droid_unblockability.py
& .venv\Scripts\ruff.exe check tools\cardcade_stage002_silent_stop_ledger.py tests\test_cardcade_stage002_silent_stop_ledger.py tests\test_does_machines_level_three.py tests\test_frog_butler_mana.py tests\test_fugitive_droid_unblockability.py
git diff --check
```

Result on the corrected #381 worktree: **21 passed, 0 failed, 0 skipped**;
Ruff format, Ruff lint, and `git diff --check` passed. The ledger builder also
reproduced the committed CSV hash with the new source-prefix guard enabled.
No complete game, smoke batch, calibration, merge, deck change, or archive
write occurred in this validation.

**Disposition:** the ledger mapping, Tunnel Rats engine legality, Frog Butler
mana authentication, and artifact-entry checks are locally validated. Natural
empty-stack end-step reachability remains an integration requirement for #385;
this isolated #381 head does not claim to satisfy it.
