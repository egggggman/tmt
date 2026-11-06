# Controlled Smoke 001 — Semantic Closure

## Scope and provenance

- Frozen diagnostic source: `8f9ed012fc367118d457fa0b0629598b7f03c15e` (PR #386).
- Validated code commit represented by that diagnostic: `4af1f08aa18b9a164160ddb0cfba328535a85464`.
- Stage 002 runner source SHA-256 recorded by the frozen run: `6281cd933dac15502d20a1d89cf4ae9b79e1bfaa1287bc6372240dd768c1c6f7`.
- Diagnostic game: `april-casey:canonical:7231`, seed `7231`, April O'Neil first and Casey Jones second.
- Frozen diagnostic directory: `C:\projects\tmt\.cardcade-smoke-001-8f9ed012-20261106`.
- All eight diagnostic artifact digests listed in `artifact_sha256.json` were recomputed and matched. The index SHA-256 is `37302c21af43531ad43b91f559f0bf8ba44fe8cc079f32435e9a1a0c27d2a8d5`; event, snapshot, and reconciliation digests are `5e444eeb7b86172486e771682eb21a477b4882c791859a7912e7dd17033d4d51`, `c318ea8f43c0aa3235f441c5ef070348e681633438500e22daa4fb4c9483a25f`, and `0827ac266048d869000fc50616462ce1bdd81f9aa3da3462eb7ebd2e245546c5` respectively.
- The diagnostic directory was read only. The OBL Baseline 005 manifest SHA-256 remains `532bad7e489eb25f3184b5a90487e1361f7a2b19b8c02cac3c4115a0fc3e14bc`; the Stage 002 card-data snapshot remains `56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402` and matches its data manifest.
- Investigation and changes are isolated on `review/cardcade-smoke001-semantic-closure`, created from the frozen PR #386 HEAD. PR #386 and the original PR branches were not changed.

## Classification of all findings

The eight `unsupported_semantics` events reduce to five distinct source-card findings. The two Casey Jones opportunity events are listed separately.

| Finding | Source, event context, and observed state | Classification and likely impact |
|---|---|---|
| Buzz Bots — two events | `Flying, vigilance`; `oracle_ability_not_implemented`; controller April; objects `object-000141` at turn 3 precombat main and `object-000176` at turn 11 precombat main. The first copy attacked on turns 5, 7, 9, 11, 13, and 15; the second died before attacking. | Flying legality is implemented, but vigilance was not: all attackers were tapped. Confirmed gameplay defect, medium to high impact because an attacker should remain available to block. The broad unsupported marker covered both keywords; the correction recognizes the implemented keyword line and enforces vigilance. |
| Ravenous Robots — one event | “Whenever you cast an artifact spell, create a 1/1 colorless Robot artifact creature token.”; `token_trigger_context_not_implemented`; controller Casey; source `object-000145`; turn 4 precombat main on entry. Ravenous remained on the battlefield when Casey cast Spicy Oatmeal Pizza on turn 14; no Robot token was created. | Missing gameplay behavior, high impact if artifact spells recur. A synthetic artifact cast with Ravenous in play also produced no token. Correct timing requires an authenticated cast event and a trigger placed on the stack while the artifact spell is still resolving; current engine event provenance has no generic spell-cast RulesEvent. No timing approximation was added. |
| Casey Jones, Vigilante — two opportunity records | “When Casey Jones enters, draw three cards. At the beginning of your next upkeep, discard three cards at random.” Controller Casey; `object-000156` at turn 8 precombat main and `object-000193` at turn 14 precombat main. Both triggers drew three and scheduled delayed discards; they resolved at Casey's turn 10 and turn 16 upkeeps. The second source then left by the legend rule, but its trigger still resolved. | Gameplay is supported and authenticated. The `unsupported_opportunity_witnessed` event name was a telemetry classification error: each semantic occurrence had no limitations and resolved. The new branch renames future emissions to `semantic_opportunity_witnessed`; the frozen trace remains unchanged. |
| April O'Neil, Hacktivist — one event | “At the beginning of your end step, draw a card for each card type among spells you've cast this turn.”; `oracle_ability_not_implemented`; controller April; source `object-000164`; turn 9 precombat main on entry. April then cast itself (creature) on turn 9, Buzz Bots (artifact creature) on turn 11, and Fugitive Droid (artifact creature) on turn 13. The trace contains no corresponding end-step draws. | Missing gameplay behavior, high impact through recurring card advantage. The engine does not track cast card types for this end-step trigger. The observed normal draw-step cards are unrelated. Implementing it needs an authenticated per-turn cast-type ledger and an end-step trigger path. |
| Spicy Oatmeal Pizza — three events | “When this artifact enters, it deals 4 damage to any target and 3 damage to you.” Controller Casey; artifact `object-000204`; turn 14 postcombat main. The artifact entered, but no damage trigger was put on the stack and no damage was dealt. | One missing gameplay effect reported at three layers: `damage_any_target_not_implemented`, `damage_trigger_context_not_implemented`, and `damage_followup_semantics_not_implemented`. High impact: target choice, 4 damage, and the following 3 damage to its controller all matter. Supporting this safely requires authenticated trigger provenance, any-target selection, damage resolution, and follow-up ordering. |
| Purple Dragon Punks — one event | “{T}: Add {R}. Spend this mana only to cast an artifact spell or to activate an ability.”; `activation_child_semantics_not_implemented`; controller Casey; source `object-000214`; turn 16 precombat main on entry. No activation was recorded before the game ended in combat that turn. | Unsupported engine action, but unreached in this game. Synthetic inspection confirms the engine does not offer the ability. Its actual impact here is none; future impact depends on having a legal artifact spell or activated ability to pay for. General restricted mana needs a typed production/payment restriction path. |

### Impact ranking

1. Spicy Oatmeal Pizza's missing target-and-damage trigger and April's missing recurring end-step draw are the strongest immediate outcome risks.
2. Ravenous Robots' missed artifact-cast token is a confirmed, repeatable board-development defect.
3. Vigilance was a confirmed combat defect; it is corrected in this branch.
4. Purple Dragon Punks is an engine capability gap, but the ability was not activated in this match.
5. Casey's two opportunity records are a telemetry-label issue only; the effects and delayed discards resolved.

## Mana-event interpretation

The game recorded 11 `cost_paid` entries with land `source_ids` and six `activation_cost_paid` entries. Basic lands are selected and tapped directly by the payment plan; they do not first create floating mana records. No mana-producing ability was selected, so the absence of `floating_mana_produced` events is expected for this trace. Purple Dragon Punks' ability was not exposed or used. Its unsupported restriction remains a latent engine gap, not an explanation for the lack of land-mana events.

## Correction and synthetic validation

The smallest confirmed implementation correction was made:

- Attacking creatures with the static Vigilance keyword now remain untapped.
- The interpreter recognizes only creature keyword lines composed of Flying and/or Vigilance when card metadata confirms the keywords. Unsupported abilities remain reported.
- Opportunity records now use the neutral `semantic_opportunity_witnessed` event name so fully supported triggers are not labeled unsupported.
- Added two focused Vigilance tests and five semantic-classification probes. The probes verify Casey's resolved ETB, Ravenous's missing artifact-cast trigger, April's explicit unsupported classification, Spicy Oatmeal Pizza's unsupported damage layers, and Purple Dragon Punks' unavailable mana action.

Before the correction, a direct synthetic attack on the exact PR #386 source produced `tapped=True` for a Vigilance attacker (expected `False`). The corrected branch's selected tests pass.

Validation used Python 3.12.10, pytest 8.4.2, and Ruff 0.16.1. The selected ten synthetic test nodes were individually inspected; none invokes the Stage 002 runner or a complete game. Result: 10 passed, 0 failed, 0 skipped. Ruff format check, Ruff lint, and `git diff --check` passed on the four changed Python files.

The selected test nodes were:

```text
tests/test_flying_action.py::test_vigilance_attacker_remains_untapped_after_attack
tests/test_flying_action.py::test_flying_vigilance_keyword_line_is_not_reported_as_unsupported
tests/test_flying_action.py::test_flying_attacker_filters_ordinary_blocker_and_attacks_unblocked
tests/test_conformance07.py::test_etb_and_attack_witnesses_join_authoritative_events_to_exact_fragments
tests/test_smoke001_semantic_triage.py::test_casey_witness_marker_can_coexist_with_authenticated_resolving_etb
tests/test_smoke001_semantic_triage.py::test_ravenous_artifact_spell_trigger_is_not_executed
tests/test_smoke001_semantic_triage.py::test_april_end_step_draw_remains_classified_unimplemented
tests/test_smoke001_semantic_triage.py::test_spicy_pizza_damage_parent_is_not_enqueued_on_entry
tests/test_smoke001_semantic_triage.py::test_purple_dragon_restricted_mana_ability_is_not_offered
tests/test_vigilante_upkeep_action.py::test_both_priority_windows_and_first_subsequent_upkeep[False-1]
```

The first targeted pytest attempt imported the editable package from the older fidelity worktree; two assertions therefore exercised the wrong source and failed. The suite was rerun with the correction worktree's `src` explicitly first on `PYTHONPATH`; all ten selected nodes passed against this branch.

No complete game, unrestricted CI, smoke batch, calibration, deck edit, merge, or G: archive operation occurred during this investigation.

## Remaining blockers and recommendation

The Vigilance correction and Casey telemetry rename are small and validated. Ravenous Robots, April's end-step draw, Spicy Oatmeal Pizza damage, and Purple Dragon Punks restricted mana remain unsupported. The first three need authenticated cast/step trigger inputs and expanded serialized evidence; Pizza also needs a complete target-and-damage follow-up path. Purple Dragon Punks needs generic restricted-mana accounting. These are architectural engine decisions, not safe local patches.

**BLOCKED — HQ architecture direction is needed before implementing the remaining trigger and restricted-mana families.** No further complete game was run.
