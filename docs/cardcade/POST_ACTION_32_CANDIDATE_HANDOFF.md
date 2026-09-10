# Action #32 candidate handoff ? Krang hand refill

Authorized base: `8923eb8e574b2b3a6be4b8ac4b318bc41dd17151` (Issue #104). Candidate SHA and unmerged PR URL are recorded in the GitHub handoff; no self-acceptance or merge is authorized.

The exact self-ETB hand-refill checks the frozen entering controller's hand at creation and again at actual all-pass resolution. False creation creates no trigger. True creation preserves its original controller through source departure/control changes/reentry. Resolution freezes max(0, 4 - hand_size) once and calls existing single-card Draw exactly that many times, including every genuine empty-library attempt. No variable expression grammar, new timing architecture or sibling Krang ability change is introduced.

A dedicated immutable creation/transaction ledger reconstructs entry identity and hand condition, original Trigger/Stack/Priority joins, resolution hand/library identities, ordered successful and failed Draw attempts, post-zones and consumed completion. EXECUTED requires the completed positive-count transaction. Genuine failed Draw requires subsequent failed-draw SBA loss evidence. Condition-false and terminal-pending cases receive no generic trigger-resolution credit.

## Final validation

- Focused Action #32: **95 tests**; focused plus relevant regressions: **333 passed**.
- Full pytest: **1,311 passed, 1 skipped**.
- Frozen Stage #002 **16/32**: **30 EXECUTED / 1 REACHED-UNSUPPORTED / 133 PRESENT-UNREACHED**, no stops or invariant violations. All 16 reports reconstruct; no natural Krang refill is credited.
- Unchanged Smoke **180/360**: **495 EXECUTED / 111 REACHED-UNSUPPORTED / 1,530 PRESENT-UNREACHED**; **114 mechanically clean coverage-complete / 66 coverage-limited / 0 invalid**.
- Smoke stops / violations / duplicate mismatches: **0 / 0 / 0**. All 180 reports and both duplicate snapshots authenticate.
- Natural Krang evidence: **7 entries, 4 condition-true and 3 condition-false; 4 completed transactions across 3 games**. No natural failed Draw or resolution-condition-false case. Nine separately preserved controlled snapshots cover success, partial/empty-library failures and condition-false outcomes under the final validator; they are not additional Stage/Smoke matrix games.
- Historical continuity: all **147 banked Stage references** and **2,828 banked merged-baseline Smoke references** authenticate under final validators. No per-game/semantic runtime EXECUTED count decreases in either matrix. Fresh Smoke contains **2,834** authenticated execution references. Counts are observed, not forced.
- Ruff check, Ruff format, canonical terminology scan and diff checks pass. Sidecars and compressed/decompressed SHA-256 round-trips are verified; staged bytes are checked before commit.

## Authoritative final packet

Use `POST_ACTION_32_FINAL_STAGE_002_RESULTS.json` and `POST_ACTION_32_FINAL_SMOKE01_RESULTS.json.gz` as the accepted final-source matrix runs. `POST_ACTION_32_FINAL_VALIDATION.json` records exact Git clean source/test blob IDs, tests, reconstruction and source manifest/aggregate digests. Both Smoke compressed and decompressed identities have sidecars.

`POST_ACTION_32_KRANG_TRANSACTIONS.json.gz` preserves complete authoritative event/evidence snapshots for every natural Krang-entry game, plus entries, commits and execution references. These chain snapshots and `POST_ACTION_32_SMOKE_INVENTORY.json` / `POST_ACTION_32_CONTINUITY.json` were extracted from the first successful run; **every one of the 180 complete game reports is byte-canonically identical in the final run**, independently verified. Thus the chain/inventory/continuity packet applies unchanged to the final result. The final result itself also contains all original and duplicate transaction evidence.

`POST_ACTION_32_CONTROLLED_TRANSACTIONS.json` contains nine focused proof snapshots independently reconstructed with the final validator. All derived evidence has SHA-256 sidecars.

The earlier `POST_ACTION_32_STAGE_002_RESULTS.json` and `POST_ACTION_32_SMOKE01_RESULTS.json.gz` remain preserved as successful predecessor validation, not substituted for the final-source runs. Final review tightened the failed-draw evidence guard and added a regression; final Stage/Smoke restarted unchanged at game 1. This was a validator-only improvement, with all final Smoke game reports identical. No Stage/Smoke execution failed; development test/bookkeeping failures are described in FINAL_VALIDATION. Historical pre-Action-32 artifacts were not overwritten.

## Changed scope

- `src/tmnt_design_studio/card_interpreter07.py`: exact self-reference recognition.
- `src/tmnt_design_studio/krang_refill07.py`: bounded condition, Draw transaction and reconstruction/provenance guards.
- `src/tmnt_design_studio/engine07.py`: protected ETB delivery, identity registration and live evidence credit.
- `src/tmnt_design_studio/stage002.py`: serialized exact transaction validation and credit.
- `src/tmnt_design_studio/smoke01.py`: frozen source identities and the new bounded module only; no matrix or policy change.
- `tests/test_krang_refill_action.py`: focused positive, negative and mutation proofs.
- `docs/cardcade/.gitattributes` and new `POST_ACTION_32_*` evidence: LF/binary hash preservation and review packet.

## Explicit exclusions

Tunnel Rats remains deferred. No generic variable-draw or conditional-trigger grammar, new Priority windows, scheduler, turn-engine, Pilot, deck, chooser, RNG, hidden-zone or unrelated rules work. Krang affinity/power bonus remain unchanged. Action #33 and Prototype 0.3 remain NOT AUTHORIZED; calibration remains BLOCKED. Candidate remains unmerged for independent HQ review.
