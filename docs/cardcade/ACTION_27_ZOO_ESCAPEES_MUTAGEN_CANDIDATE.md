# Action #27: Zoo Escapees leave-battlefield Mutagen

Implements Issue #91 from exact evidence base `a0636651ed0cbd7e35993b2738683a99caf16273`.

The exact authoritative Zoo Escapees leave-battlefield fragment now creates one authenticated trigger. It waits for Stack/Priority resolution, then creates exactly one canonical Mutagen token through the existing token-creation machinery. Ownership and control belong to the controller of the departing source. The source's original incarnation and original leave event remain authoritative even if its card later returns as a new incarnation.

## Bounded implementation

The interpreter recognizes only the exact fragment, including its canonical reminder text, without card/deck-name gameplay dispatch. Existing permanent-left events, last-known battlefield evidence, trigger registration, APNAP Stack placement, Priority, token definitions, creation events and Stage classifications are reused. Source/event/trigger/Stack identity anchors and one-use delivery reject stale, fabricated, relinked and replayed provenance. Serialized validation reconstructs departure, original leave event, trigger, Stack/all-pass Priority, token creation and resolution.

Mutagen's activated ability is **not supported**. Its existing nonmana-cost, targeting/choice, child-semantic and sorcery-timing limitations remain. Token creation does not create an activation execution reference. Zoo Escapees' creation occurrence retains `token_activated_ability_not_implemented` as a limitation while the authenticated creation is EXECUTED; the token's own activation presence is classified separately.

## Changed paths

- `src/tmnt_design_studio/card_interpreter07.py`: exact leave/Mutagen delivery coverage; activation limitations retained.
- `src/tmnt_design_studio/engine07.py`: authenticated leave-trigger lifecycle, one canonical token creation, reconstructive evidence.
- `src/tmnt_design_studio/stage002.py`: invoke the bounded serialized-evidence validator.
- `src/tmnt_design_studio/smoke01.py`: refresh only the three changed input hashes.
- `tests/test_zoo_escapees_ltb_mutagen_action.py`: 37 new focused regressions.
- `docs/cardcade/.gitattributes`: LF-stable Action #27 artifacts.
- New Action #27 results, witness manifest, resumed validation, SHA-256 sidecars and this handoff.

## Validation

- Focused Zoo Escapees, permanent-left counter, dies/Draw and token suites: **146 passed**.
- Full pytest, including Stage/Smoke: **990 passed, 1 skipped**.
- Ruff check, Ruff format check, canonical terminology scan and `git diff --check`: passed.
- Frozen Stage #002: **16 games / 32 executions**, deterministic duplicates, **0 invariant violations / 0 runner stops**, all **16 reports reconstructed**.
- Resumed revalidation preserved the implementation, repeated the requested checks and one frozen matrix, and produced results identical to the saved candidate artifact. Two development/validation matrix runs total, each 16/32, are recorded separately from the per-run budget.
- SHA-256 sidecars match both working-tree and staged Git bytes; witness code hashes match the staged implementation.

## Stage witness and continuity

The final inventory is **24 EXECUTED / 6 REACHED-UNSUPPORTED / 134 PRESENT-UNREACHED**. Zoo Escapees moves to EXECUTED in `michelangelo-bebop-rocksteady:canonical:7212`. Its new Mutagen token's activated text is **PRESENT / UNREACHED and unsupported**, with no authenticated activation execution reference.

Stockman, both Action #21 Donatello witnesses, and Action #25 Shredder remain EXECUTED. No prior game/semantic EXECUTED count decreases relative to Issue #90. Exact references, original creation provenance, token identity and activation limitations are in `POST_ACTION_27_STAGE_002_WITNESS.json`.

Result: `POST_ACTION_27_STAGE_002_RESULTS.json`; raw SHA-256 `a199f67e2710d18d4208c51e5d1ea6b08e6f88196faacac5c57d4e42199bf2de`. The result is unchanged by the resumed validation recorded in `POST_ACTION_27_RESUMED_VALIDATION.json`.

## Review boundary

No Casey, Courier, Mutagen activation, unrelated grammar/token mechanics, deck/Pilot, calibration/balance, GUI, broad simulation or Action #28 implementation. All prior measurements are preserved. Independent HQ review is required before acceptance or merge; this candidate is not self-accepted. Action #28 remains NOT AUTHORIZED.
