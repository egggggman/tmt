# Integrated Controlled-Readiness Audit

## Verdict

**BLOCKED — main-action casting cannot handle an authenticated artifact-cast trigger.** The accepted PR #401 pilot correction and the accumulated supported features pass the selected synthetic regression set, but an ordinary engine-issued artifact cast through the action path used by Stage 002 raises an exception when Ravenous Robots triggers. The cast has already consumed resources and left Stack objects behind when the exception escapes. Do not begin a complete-game diagnostic from this candidate until that dispatch/priority integration defect is corrected and revalidated.

This audit does not authorize a game, merge, calibration, deck change, or baseline promotion.

## Source chain and worktree

- Accepted `origin/main`: `10d2ac80ef5b81b3a209a3133eb0a84633a1f944`.
- Tested integrated candidate: PR #401 published HEAD `ad2034026d6d37904f66da7ef71874f2306e1571`; its tested pilot implementation commit is `d7a99aced66cd94998298356315d335f307017fe`.
- Independent validation worktree: `C:\projects\tmt\.integrated-readiness-pr401`, branch `review/cardcade-integrated-readiness`. The audit branch is report/test-only and starts directly from the tested candidate SHA.
- Python 3.12.10, pytest 8.4.2, Ruff 0.16.1; reused `C:\projects\tmt\.cardcade-fidelity-correction\.venv`.

All exact PR #381, #382, and #385 source heads are ancestors of PR #401 through combined PR #386. PR #386 HEAD `8f9ed012fc367118d457fa0b0629598b7f03c15e` is also an ancestor. The semantic correction chain then descends through PRs #388–#395, followed by PR #397, PR #399, and PR #401. The PR metadata confirms these implementation and integration PRs remain open, draft, and unmerged.

The principal implementation overlaps are in `engine07.py` (PR #386, #388–#395, #397), `card_interpreter07.py` (PR #386, #388–#395), `mana_ledger07.py` (PR #392 onward), `stage002.py` (PR #386, #388–#395, #397, #399, #401), and `pilot07.py` (PR #397). The current candidate is a stacked history with those overlaps already resolved; no branch rewriting or merges were performed for this audit.

Report-only branches excluded from the implementation ancestry include PR #396, PR #398, PR #400, and the accepted audit PR #402. PR #391 is a report-only source commit that is an ancestor because PR #392 was based on it. PR #387 is the authorization issue, not an implementation PR. The independent reproduction source blobs and original historical branches were preserved.

## Frozen identity and preservation

The candidate diff from accepted main contains no deck or Baseline 005 file changes. The following Smoke 001 inputs were rehashed read-only and matched the frozen run metadata:

- Card snapshot `cardcade/scryfall-tmt-pza-tmc-2026-08-13.json`: SHA-256 `56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402`.
- Card-data manifest: SHA-256 `6b5271af75150a361f77e7b89306c709959dfdf497c448dfdc978e5dc9a17950`.
- April `PROTOTYPE_0.1.txt`: SHA-256 `684c898760a39c5dfc584206ef4675c49d96cfe6bd419f03f86bd0b8358d09f4`.
- Casey `PROTOTYPE_0.1.txt`: SHA-256 `0fc0adbb370ecfddad03692a4229a04b23268739914a8f2a004b8e042ff3cebb`.
- OBL Baseline 005 manifest: SHA-256 `532bad7e489eb25f3184b5a90487e1361f7a2b19b8c02cac3c4115a0fc3e14bc`.
- The eight Smoke 001 artifacts listed by `artifact_sha256.json` all matched their recorded hashes. The event, snapshot, and reconciliation hashes remain `5e444eeb7b86172486e771682eb21a477b4882c791859a7912e7dd17033d4d51`, `c318ea8f43c0aa3235f441c5ef070348e681633438500e22daa4fb4c9483a25f`, and `0827ac266048d869000fc50616462ce1bdd81f9aa3da3462eb7ebd2e245546c5`.

The 485-row Stage 002 ledger's committed Git blob matches SHA-256 `4476cc931b91354c076dedc543c9fea89ef5c43c62c0cf786a889a3bc7b884c5`; its row classifications remain 303 indeterminate, 126 conformance/provenance, and 56 unsupported semantic across 201 games. Its four selected pointer/mapping tests passed. The worktree checkout has platform line endings, so its working-file digest differs from the committed-blob digest; the committed blob was hashed directly.

One older gates report calls `c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac` a “frozen Baseline 005 deck manifest.” The Smoke 001 run metadata instead identifies the OBL manifest above (`532bad…`), which rehashes correctly. The `c6111…` artifact was not present under that name in this candidate checkout. It does not prevent identifying the Smoke 001 deck files above, but should be reconciled before a Baseline 005 comparative run.

## Synthetic selection and results

Test bodies were inspected before execution. The selection contained only individually named direct `Game` fixtures and deterministic engine/reconciliation checks; no game runner, unrestricted module, smoke harness, or calibration path was invoked.

The 110 named nodes comprised:

- The 71 nodes/75 cases independently accepted for PR #401, reconstructed from `PILOT_FIDELITY_CORRECTION_ACCEPTANCE.md` and `PR399_TARGET_POLICY_CORRECTION_ACCEPTANCE.md`.
- The two PR #402 reviewer-only probes for cast-stage deferral and pilot PASS (part of the accepted 77 pilot cases).
- Fourteen named PR #386 final-fidelity tests covering transition rejection, Stack/legacy combat, Tunnel Rats, Frog Butler mana/Reach, Fugitive Droid, second main, combat epochs, and terminal priority.
- Two PR #386 combined driver tests for natural Tunnel Rats end-step priority and defender Reach after attackers.
- Four stop-ledger pointer/order tests.
- Five Food ability and restricted-payment tests, the Casey ETB witness test, two Vigilance regressions, the selected Casey delayed-upkeep case, and six Ravenous token-haste tests.
- Two new composed integration tests recorded in `tests/test_integrated_readiness_audit.py`.

At candidate HEAD `ad2034026d6d37904f66da7ef71874f2306e1571`, the selection returned **114 passed, 0 failed, 0 skipped**. The first 108 nodes (before adding the two composed cases) returned 112 passed. One command-construction attempt used an incorrect test path and collected no tests; the corrected exact selection ran successfully.

Quality checks on all 28 Python files changed from accepted main passed: Ruff 0.16.1 format check, Ruff lint, and `git diff --check`. The new audit-only composed test file also passes Ruff format and lint. No candidate source file was changed.

### Composed interaction results

`test_announce_spell_composes_punks_payment_robot_trigger_and_pizza_etb` passes. Using the supported announcement path, it verifies that Punks produces one red lot, Pizza consumes that lot as `artifact_spell`, one authenticated Ravenous Robots trigger references Pizza's exact `SPELL_CAST` event, and the trigger and Pizza ETB resolve through priority. It observes one Robot token, then four damage to the opponent and three to the controller from Pizza.

`test_main_cast_wrapper_raises_on_pending_artifact_cast_trigger` characterizes the blocker. It obtains a current legal Pizza `CAST` option after the Punks activation and calls `Game.execute_main_action`, the method Stage 002 calls at `stage002.py:543`. The operation raises:

```text
ValueError: artifact-cast token trigger requires Priority resolution
```

`execute_main_action` delegates to `Game.cast` (`engine07.py:8559`, `11330`); that compatibility wrapper immediately calls `resolve_top_of_stack`. The cast event has already created Ravenous Robots' `CREATE_TOKEN` trigger, and `resolve_top_of_stack` rejects resolving that trigger outside a processed priority window (`engine07.py:11539`). The reproduced post-exception state has consumed the exact restricted lot, tapped Punks and the lands, moved Pizza out of hand, left the spell and trigger on the Stack, and has `priority_state is None`. The Stage 002 caller does not catch this exception. This means the pilot's otherwise-legal advertised follow-up can terminate the runner before either player receives priority.

The lower-level `announce_spell` composition succeeds, so the defect is localized to the immediate-resolution compatibility path used by the main-action executor, rather than the cast-event trigger, restricted allocation, or Pizza trigger resolution in isolation.

## Remaining mechanics and boundaries

The prior Smoke 001 findings now have focused synthetic coverage: Buzz Bots Flying/Vigilance; Pizza damage, target and terminal ordering; April end-step type draw; Ravenous Robots' artifact-cast token trigger and separate token-haste activation; Punks restricted red production and spending; and Casey's authenticated ETB/upkeep behavior and semantic-opportunity label. Pizza's Food life-gain ability is supported through the generic Food path and its selected atomicity/payment tests passed.

The frozen engine represents Pizza's “any target” as players and creatures; it has no planeswalker target state. The frozen Smoke 001 card/game model has no planeswalker object, so this does not block the documented ten-deck diagnostic scope. The pilot remains deterministic heuristic policy, not multi-turn strategy. The selected run does not exhaustively validate every Oracle line in the 472-print card snapshot, and second-main or full-game outcome impact remains unmeasured.

## Recommendation and next gate

**BLOCKED.** Before a complete-game diagnostic, correct the `execute_main_action`/`Game.cast` path so a cast that creates an authenticated `SPELL_CAST` trigger enters the normal priority/Stack lifecycle rather than immediately trying to resolve the trigger. Preserve the legacy `Game.cast()` compatibility contract and add a synthetic end-to-end regression using Punks-paid Pizza with Ravenous Robots present. Then rerun the 110-node selection and the composed priority/provenance assertions at the new source SHA.

After that correction passes, HQ can decide whether to authorize one isolated diagnostic game. This audit provides no calibration, balance, smoke-restart, or baseline-promotion conclusion.
