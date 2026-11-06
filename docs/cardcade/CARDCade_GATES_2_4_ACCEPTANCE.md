# Cardcade Gates 2–4 Acceptance Package

**Review target:** PR #381, base `main` at `10d2ac80ef5b81b3a209a3133eb0a84633a1f944`.
**Pre-correction PR head:** `ef5d4fa44019cd744fdaf9fd9e725ad21787ca0b`.
**Correction commit:** `c8cd9407a7289b0cd87d7f4e6898a215d8216ade`.
**Working candidate engine Git blob:** `67ce3bf797d944c83c1fa02ca2287ea3b129bf93`.
**Status:** committed locally; pending publication and independent review.

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
executor. It should be a separate focused PR. The engine does not open ordinary
empty-stack priority windows between steps, so the separate change can cover
existing stack windows while that broader timing limitation remains explicit.

## Validation

Environment: Python 3.12.10, Ruff 0.16.1.

```powershell
& .venv\Scripts\ruff.exe format --check src/tmnt_design_studio/engine07.py tests/test_frog_butler_mana.py tests/test_fugitive_droid_unblockability.py tests/test_tunnel_rats_graveyard_return.py tools/cardcade_stage002_silent_stop_ledger.py
& .venv\Scripts\ruff.exe check src/tmnt_design_studio/engine07.py tests/test_frog_butler_mana.py tests/test_fugitive_droid_unblockability.py tests/test_tunnel_rats_graveyard_return.py tools/cardcade_stage002_silent_stop_ledger.py
$env:PYTHONDONTWRITEBYTECODE='1'; & .venv\Scripts\python.exe -B -m pytest -q tests/test_activated_abilities.py tests/test_tunnel_rats_graveyard_return.py tests/test_frog_butler_mana.py tests/test_frog_butler_reach.py tests/test_does_machines_level_three.py tests/test_fugitive_droid_unblockability.py tests/test_stage002_runner.py
git diff --check
```

Results: Ruff format check passed; Ruff lint passed; 115 selected synthetic
tests passed; `git diff --check` passed. No skips or failures. No complete-game
test or unrestricted suite was run. The stop-ledger builder separately passed
against all 300 preserved result files and produced 485 rows; CSV SHA-256 is
`4476cc931b91354c076dedc543c9fea89ef5c43c62c0cf786a889a3bc7b884c5`.

## Gate 5 — Readiness

**BLOCKED** for a controlled smoke test. PR #381 still needs independent review
of this updated candidate, and the narrow Frog Butler Reach priority omission
needs its own reviewable correction. In addition, the empty-stack end-step
priority window is not opened by the current Stage 002 driver. These are
demonstrated reachability/provenance limitations, not hypothetical mechanics
coverage. No complete games, calibration, merge, or deck changes are authorized
by this package.
