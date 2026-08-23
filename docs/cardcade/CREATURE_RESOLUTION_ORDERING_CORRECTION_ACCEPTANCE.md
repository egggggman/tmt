# Creature-Resolution Ordering Correction Acceptance Audit #1

## Verdict

**ACCEPT — the bounded generic creature-resolution ordering correction is suitable to freeze and integrate.**

This verdict applies to uncommitted candidate fingerprint `c025697926e7c3a3b71326b0227ae3227be5f126`. It does not authorize Smoke Stage 0.1 execution or the atomic-write environment probe.

## Audit target and scope

- Parent baseline: `b7d212e6de6e3a9c6969a47c5bc70db570562214`
- Candidate files:
  - `src/tmnt_design_studio/engine07.py`
  - `tests/test_engine07.py`
  - `src/tmnt_design_studio/smoke01.py` — frozen identity bookkeeping only
- Implementation/tests modified during audit: none
- Smoke games executed: zero
- Atomic-write probe executed: no

The engine diff moves one existing call. Unsupported semantic presence is registered after the resolved creature has become an authoritative battlefield permanent and before `_process_creature_entered_triggers()` can deliver synchronous triggers and state-based actions. The strict authority check in `_register_semantic_occurrence()` is unchanged.

## Authoritative incarnation and ordering

The adversarial regression resolves a generic legendary creature with a supported token-creating ETB instruction while an older permanent with the same legendary name already exists. The new permanent receives its own runtime identity on battlefield entry. Semantic presence is recorded against that exact identity before the `CREATURE_ENTERED` rules event.

ETB processing then creates the token and reaches its existing SBA boundary. The legend rule retains the older permanent and moves the newly resolved incarnation away. The resulting evidence proves:

- presence names the departed new incarnation, not the older kept permanent;
- the two runtime identities remain distinct;
- semantic presence precedes the authoritative ETB event;
- token creation and legend-rule processing still occur;
- the departed source becomes `former` without invalidating the already recorded historical presence;
- engine invariants remain clean.

This is legitimate PRESENT evidence, not a claim that the fragment executed. EXECUTED classification continues to require mature authenticated transaction/event evidence. Merely preserving a semantic occurrence for a later-departed object cannot promote it to EXECUTED.

## Surviving, stale, and fabricated sources

Ordinary creature resolution still produces the same permanent, unsupported telemetry, ETB processing, and final SBA behavior. Existing regressions for normal resolution, both legend-rule choices, semantic provenance, zone identity, and surviving permanents remain passing.

The correction does not change `is_authoritative()` or `_register_semantic_occurrence()`. Direct attempts to register against stale, former, unregistered, fabricated, or relinked runtime objects therefore continue to fail before evidence mutation. The fix succeeds by calling the existing strict registration boundary at the truthful lifecycle point, not by weakening it.

## ETB and Create Token isolation

No token-creation implementation, token definition, token identity, direct `create_tokens()` path, trigger resolver, Priority path, or SBA implementation changed. The only ordering difference is in the creature-spell resolution branch. Existing Create Token and conformance regressions prove direct and triggered token creation retain their authoritative transactions, runtime identities, event provenance, and invariant behavior.

Registering presence before `_new_rules_event(CREATURE_ENTERED)` preserves prospective opportunity witnessing: the event producer already joins all registered occurrences to the new authoritative event. It does not retroactively borrow an unrelated event.

## Generic architecture

The correction contains no card name, legend-rule name, deck identity, matchup, Pilot, Smoke stage, Oracle phrase, or Action-specific branch. It applies uniformly to every creature permanent resolved through the authoritative Stack path.

## Smoke identity bookkeeping

The `smoke01.py` delta changes exactly one frozen value:

- prior accepted engine Git-clean identity: `6e09f224fc75b8afe6cb6945a403ab43ab64f70e`
- corrected candidate engine Git-clean identity: `590db7fe144963be52b8c7abaa0e20f3fc6da2d9`

Independent Git clean-filter reconstruction of the modified `engine07.py` produces exactly `590db7fe144963be52b8c7abaa0e20f3fc6da2d9`. No matrix, runner, classification, artifact, balance, or gameplay code changed. The Smoke plan remains exactly 45 pairings / 180 distinct games / 360 executions.

## Validation

- Candidate fingerprint before/after audit: `c025697926e7c3a3b71326b0227ae3227be5f126`
- Full suite: **623 passed / 1 skipped**
- Focused engine + Create Token + conformance + Smoke-runner regressions: **144 passed**
- Ruff check: clean
- Ruff format: **48 files already formatted**
- `git diff --check`: clean
- Smoke executions: **0**

## Gate

Freeze the accepted implementation and tests, confirm exact-SHA CI, integrate through the normal PR gate, and validate merged `main`. Then perform the separately authorized non-game atomic-write environment probe. Smoke Stage 0.1 may restart from game #1 only after both the integrated correction and write probe are green.

Action #14, calibration, Pilot/deck changes, Prototype 0.3, and the historical 900-game smoke remain blocked.
