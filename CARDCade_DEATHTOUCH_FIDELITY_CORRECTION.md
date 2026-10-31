# Cardcade Deathtouch Fidelity Correction

## Result

**READY FOR INDEPENDENT REVIEW**

The correction is on branch `fix/deathtouch-sba`, based on accepted Diagnostic 002 source commit `ab383a17d23994e014b0817a2058f53d9db4202d`. The implementation and synthetic tests are in commit `a8e9701` (`Track Deathtouch damage for state-based destruction`). No gameplay was run. Diagnostic 001 and 002, frozen `fd28`, RUN_STOP, Durable 001, and deck inputs were not modified.

## Reproduction and rules basis

The accepted engine applied damage to `Permanent.damage`, but its lethal-damage state-based action destroyed a creature only when marked damage reached toughness. The receiving creature carried no record that a Deathtouch source had dealt damage. Consequently, one damage from a Deathtouch source did not destroy a 5-toughness creature.

Comprehensive Rules 702.2b and 704.5h require a creature with toughness greater than zero that was dealt damage by a Deathtouch source since the last state-based-action check to be destroyed. Rule 704.5g separately handles ordinary marked damage. Deathtouch does not reduce toughness. The rules are available from the [official Magic rules page](https://magic.wizards.com/en/rules); the September 25, 2026 rules text is [here](https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.txt).

## Changes

Exactly two files changed in the implementation commit:

- `src/tmnt_design_studio/engine07.py`
- `tests/test_deathtouch_damage_state_based.py`

`Permanent` now stores a separate `damage_from_deathtouch` marker. Both supported damage paths—`deal_damage` and combat damage assignment—set it only when positive damage is applied by an authoritative source that has intrinsic, active temporary, or currently supported continuous Deathtouch. The existing lethal-damage state-based action checks that marker for creatures with positive toughness while retaining the ordinary damage threshold and indestructible check.

The marker is included in authoritative-state fingerprint evidence while active, is cleared after each state-based-action pass (the rule's “since the last time” boundary), and is cleared with marked damage at cleanup. Damage remains recorded as damage; toughness is unchanged. The Menace telemetry events and combat assignment/pilot logic were not changed.

The implementation commit SHA is `a8e970106ac3eea3e2ea0156d4c0f5c82f78c0fb`. The report is committed separately so it can record the implementation commit without a self-referential hash.

## Synthetic coverage

The new 11-test module verifies:

- One positive Deathtouch damage destroys a higher-toughness creature at the next SBA check.
- Ordinary damage below toughness does not destroy it.
- Zero and fully prevented (zero actual damage) inputs do not mark or destroy it; the engine rejects zero-amount damage transactions before mutation.
- Multiple damage sources are considered together at one subsequent SBA check.
- Gaining or losing Deathtouch after damage does not rewrite whether that damage was dealt by a Deathtouch source.
- Indestructible prevents destruction; after that SBA check, removing indestructible alone does not reuse the old Deathtouch damage marker.
- Cleanup clears damage and the Deathtouch marker.
- First-strike and double-strike timing continue through the existing damage-step flow.
- A Deathtouch blocker can destroy a trampler without changing the non-Deathtouch trampler's ordinary toughness-based assignment.

The regression run covered the new tests plus `test_deal_damage_action.py`, `test_shredder_deathtouch_action.py`, `test_strike_damage_steps.py`, `test_trample_action.py`, `test_menace_action.py`, `test_block_option_enumeration.py`, `test_menace_decision_evidence.py`, `test_destroy_permanent_action.py`, and `test_frog_butler_reach.py`.

**Result: 153 passed.** These are synthetic unit and combat-step tests, not complete games.

## Checks

- Ruff check on both changed Python files: passed.
- Ruff format check on both changed Python files: passed.
- Git whitespace check (`git diff --check`): passed.
- Full repository suite and CI: not run; this correction was validated with the relevant synthetic combat regressions, and no game execution was authorized.

## Remaining limitations

- Deathtouch plus Trample combat assignment remains unsupported by the pre-existing interpreter (`trample_deathtouch_lethal_not_implemented`). This change deliberately does not adjust lethal assignment or other combat mechanics.
- The engine has no general damage-prevention replacement path in this scope. A zero actual-damage transaction is rejected before mutation; no individual prevention card or effect was simulated.
- Regeneration is not implemented in the inspected engine, so the correction cannot demonstrate a regeneration replacement. Indestructible is supported and tested.
- The damage transaction accepts only currently authoritative battlefield or stack sources. Last-known-information cases where the source changes zones before damage are not covered by this correction.
- Synthetic coverage supports independent review of this narrow SBA correction, but does not establish general Deathtouch rules completeness or retroactively change the classification of Diagnostics 001 or 002.

## Review recommendation

The demonstrated SBA defect is corrected on a separate branch with deterministic tests, while the accepted Menace evidence events and frozen gameplay checkout remain untouched. Request independent review of branch `fix/deathtouch-sba`, implementation commit `a8e970106ac3eea3e2ea0156d4c0f5c82f78c0fb`, and this report.

**READY FOR INDEPENDENT REVIEW**
