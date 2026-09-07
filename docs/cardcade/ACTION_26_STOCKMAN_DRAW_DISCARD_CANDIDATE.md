# Action #26: Stockman ETB Draw then discard

Implements Issue #88 from exact base `2373f1d0790b52dc62b485e986851e30a2056957`.

Stockman's exact self-ETB fragment now creates one authenticated trigger through Stack/Priority. Resolution draws one card, then requires one authoritative selection from the resulting hand when nonempty. A failed Draw leaves the existing loss pending, performs any possible discard, and allows the existing post-resolution SBA to apply the loss.

## Scope and identity

The Oracle-derived recognizer accepts only self-ETB mandatory Draw one then discard one, without card/deck-name gameplay dispatch. `DiscardDrawProgram` gains a bounded ordering flag; the existing option/view/plan and choice-validation path is reused. The optional discard-then-Draw path retains its behavior. A mandatory chooser uses the same immutable hand options and defaults to the first hand object; no Pilot change is required.

ETB event, source incarnation, trigger, Stack object, controller, fragment, and one-use resolution are authenticated. Source departure preserves a valid trigger. Fabricated/stale/relinked choices fail closed; chooser-initiated zone movements are rejected. If a chooser fails after Draw, the already completed Draw remains intentional, no discard transaction commits, and resolution stops; there is no retry that could draw twice.

Serialized evidence joins entry, pending trigger, Stack, all-pass Priority, Draw movement/result, post-draw offered identities, discard movement and resolution. Existing Stage reconciliation now invokes the bounded evidence validator. Supported occurrence registration preserves a comparable Stockman occurrence and existing classification rules.

## Changed paths

- `src/tmnt_design_studio/card_interpreter07.py`: bounded grammar and program ordering.
- `src/tmnt_design_studio/engine07.py`: ETB lifecycle, shared chooser validation, mandatory movement, evidence authentication.
- `src/tmnt_design_studio/stage002.py`: invoke the new evidence validator during existing reconstruction/validation.
- `src/tmnt_design_studio/smoke01.py`: refresh only the three changed input hashes.
- `tests/test_stockman_draw_discard_action.py`: 34 focused Stockman regressions.
- `docs/cardcade/.gitattributes`: LF-stable new Action #26 evidence.
- New Action #26 candidate report, Stage results, witness manifest, and SHA-256 sidecars.

## Validation

- Stockman plus existing discard/Draw regressions: 59 tests included in the final passing full suite (the preceding focused invocation passed 58 before the final Priority-entry test was added).
- Full pytest, including Stage/Smoke: **953 passed, 1 skipped**.
- Ruff check, Ruff format check, `git diff --check`, and canonical terminology scan: passed.
- Final bounded Stage #002: **16 games / 32 executions**, byte-equivalent duplicates, **0 invariant violations / 0 runner stops**.
- All 16 serialized reports reconstruct exactly; final-code rerun is canonically identical to the final saved results. Worktree and Git-index raw-byte sidecars are verified before commit.

The final inventory is **23 EXECUTED / 7 REACHED-UNSUPPORTED / 134 PRESENT-UNREACHED**. Stockman's semantic occurrence moves to EXECUTED in `donatello-krang:canonical:7202`, with the ETB/trigger/draw/discard witness in `POST_ACTION_26_STAGE_002_WITNESS.json`. Both Donatello continuity witnesses and the Shredder witness remain EXECUTED. No prior game/semantic EXECUTED count decreased. The additional PRESENT-UNREACHED occurrence is Fugitive Droid in that same game (3 to 4); no unsupported functionality was implemented for it.

`POST_ACTION_26_STAGE_002_RESULTS.json` is the final artifact; SHA-256: `4d1ad9215620a1ab4eae28c240191de916871ca9cc9166b2c2363f919828a49d`.

`POST_ACTION_26_STAGE_002_PRE_OCCURRENCE_FIX.json` preserves the preliminary development result, where Stockman had authenticated EXECUTED presence but lacked a semantic-occurrence row. It is diagnostic history, not the final acceptance measurement. Four bounded matrix runs occurred during development/revalidation (128 total executions); each used exactly the frozen 16-game/32-execution matrix. One cross-run comparison initially compared in-memory tuples with JSON lists; canonical serialization corrected that comparison. All runner-level duplicate checks passed.

## Review boundary

No Casey, Courier, Zoo Escapees, other draw/discard grammar, random discard, delayed trigger, library inspection, deck/Pilot, calibration/balance, GUI, or Action #27 implementation. All prior banked measurements remain unchanged. Candidate is for independent HQ review only; no self-acceptance or merge. Action #27 remains NOT AUTHORIZED.
