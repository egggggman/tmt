# Cardcade Pilot Fidelity & Integrated Readiness Audit

## Audit identity

- Authorized source: `7ed476f4ded0ed59292f019320b3331688f2d2e4`, PR #395 head.
- Isolated worktree: `C:\projects\tmt\.cardcade-pilot-fidelity-audit`.
- Report branch: `review/cardcade-pilot-fidelity-audit`.
- Accepted main ref: `10d2ac80ef5b81b3a209a3133eb0a84633a1f944`.
- Frozen Baseline 005 manifest SHA-256: `532bad7e489eb25f3184b5a90487e1361f7a2b19b8c02cac3c4115a0fc3e14bc` (file contents and hash match the prior record).
- Frozen Smoke 001 code source: PR #386 head `8f9ed012fc367118d457fa0b0629598b7f03c15e`; diagnostic game `april-casey:canonical:7231`, seed `7231`.
- Smoke 001 artifact index SHA-256: `37302c21af43531ad43b91f559f0bf8ba44fe8cc079f32435e9a1a0c27d2a8d5`. All eight listed artifact files were read and rehashed successfully.
- Frozen card snapshot SHA-256: `56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402`; manifest SHA-256: `6b5271af75150a361f77e7b89306c709959dfdf497c448dfdc978e5dc9a17950`.
- Pizza identity: Oracle ID `9665f940-c0a4-4d3e-b889-8049cf549a4f`; Oracle fragment `When this artifact enters, it deals 4 damage to any target and 3 damage to you.`
- Purple Dragon Punks identity: Oracle ID `d1edb950-a118-4b4d-a0ef-9a6683d74c9f`; Oracle fragment `{T}: Add {R}. Spend this mana only to cast an artifact spell or to activate an ability.`

This was a read-only source audit. No pilot, rules engine, deck, diagnostic, or historical evidence file was changed. No test or game runner was executed.

## Draft source lineage

GitHub reports every listed PR open, draft, and unmerged. The source identities form this chain:

| PR | Base source | Head source | Relationship |
|---|---|---|---|
| #386 | `main` at `10d2ac80ef5b81b3a209a3133eb0a84633a1f944` | `integration/cardcade-pr381-382-385` at `8f9ed012fc367118d457fa0b0629598b7f03c15e` | Combined #381/#382/#385 integration candidate. |
| #388 | `review/cardcade-smoke001-semantic-closure` at `0c322b6ee75aa1da13b90d64cfe16e84ad632370` | `review/cardcade-smoke001-pizza-closure` at `738cc1cf1ea5b0d72f0e13edecb650af987e1723` | The base commit is a direct child of #386 head. #388 adds Pizza and terminal-draw closure. |
| #389 | #388 head `738cc1cf1ea5b0d72f0e13edecb650af987e1723` | `review/cardcade-april-end-step-draw` at `09d14fd7e968b35d06c30a6c5bf3a904fe28f2b3` | April draw. |
| #390 | #389 head `09d14fd7e968b35d06c30a6c5bf3a904fe28f2b3` | `review/cardcade-ravenous-robots` at `7121cd785d3f59b9952abe5631125b54acfc0d2d` | Ravenous Robots trigger. |
| #391 | #390 head `7121cd785d3f59b9952abe5631125b54acfc0d2d` | `review/cardcade-purple-mana-audit` at `992da84b4ec97248e55c6073fbfa038016fc576e` | Restricted-mana architecture report. |
| #392 | #391 head `992da84b4ec97248e55c6073fbfa038016fc576e` | `review/cardcade-restricted-mana-ledger` at `aa15c76e4e270562e317716866e0fd22b35ee873` | Mana ledger foundation. |
| #393 | #392 head `aa15c76e4e270562e317716866e0fd22b35ee873` | `review/cardcade-restricted-spell-payments` at `19a8fbd933ff199ebbe2821c6901c68d0f6eb148` | Typed spell payment. |
| #394 | #393 head `19a8fbd933ff199ebbe2821c6901c68d0f6eb148` | `review/cardcade-restricted-ability-payments` at `0d6f77ebcb39c4a58ddc74f388de58a309ce08e2` | Supported activated-ability payments. |
| #395 | #394 head `0d6f77ebcb39c4a58ddc74f388de58a309ce08e2` | `review/cardcade-purple-dragon-mana` at `7ed476f4ded0ed59292f019320b3331688f2d2e4` | Purple Dragon Punks fixed-red restricted production. |

Local ancestry confirms #386 is an ancestor of #388, and each later base is the preceding PR head. No source integration gap was found in the PR metadata/commit chain. This verifies ancestry, not combined behavior: the recorded validations were separate selected test sets on their component PR sources, and no combined all-mechanics synthetic selection is recorded at #395 head.

## Pizza target selection

### Current behavior

The engine’s `_select_damage_target` constructs an offered tuple containing both players and every authoritative battlefield creature, then calls `damage_target_chooser(controller, source_id, offered_ids)`. Its default callback always returns the opponent player ID. It does not receive player life, creature characteristics, or other game state. The Pizza path also does not apply hexproof, shroud, ward, or protection checks; the frozen card-data snapshot contains no cards with those target restrictions, so this does not invalidate a target in the frozen Smoke 001 card pool.

The Stage 002 `run_game` path installs the AcceptancePilot’s Scry, draw, and discard callbacks, but does not install a Pizza damage-target callback. `AcceptancePilot` has no `choose_damage_target` method. Its main-action `damage` stage handles Manhole Missile; Pizza is selected as a named utility artifact during the later `creature` stage, but the resulting ETB target is selected by the engine default rather than the pilot.

Consequences:

- A creature that is preferable to nonlethal opponent damage is never chosen by AcceptancePilot.
- An opponent at 4 or less life is targeted by default, which can win if the controller survives the mandatory 3 damage.
- At 3 or less controller life, the mandatory follow-up is lethal. If 4 damage also defeats the opponent, the engine’s simultaneous-life-loss boundary yields a draw; if the opponent survives, the controller loses. The default callback does not reason about either outcome.
- Multiple legal targets are exposed, but the pilot cannot compare them.
- The target is captured when the trigger is put on the Stack and rechecked on resolution. The selected Pizza tests cover target invalidation; an illegal target prevents both ordered damage events. A source leaving after the trigger is created does not erase its entry provenance.
- In this engine model, the chooser always receives at least both player IDs during a nonterminal game. There is no reachable active-game “no legal target” state in the current target model; if target legality is later narrowed, the current callback path has no no-target policy. The frozen card snapshot contains no Planeswalker card records, and the engine does not model Planeswalker damage targets.

**Legality is engine-owned; target quality is a pilot gap.** The default target is currently legal, but it is not state-informed.

### Smallest proposed policy change

Add a `choose_damage_target` method to the Pilot contract and AcceptancePilot. At trigger-stacking time, adapt the existing engine callback to pass the current recipient-specific `GameViewV2` plus the engine’s offered IDs. Keep target validation and resolution legality in the engine; the policy must return one of the offered IDs.

Use a deterministic lexicographic evaluation derived from visible state:

1. Simulate the ordered 4 damage and mandatory 3 controller damage through the existing life-loss boundary. Prefer a win over a draw, a draw over a loss, and avoid a controller loss when a legal alternative avoids it.
2. Prefer a legal target that removes a creature likely to create immediate combat loss over nonlethal opponent damage.
3. Prefer immediate opponent defeat when the controller survives; account for the self-damage so a lethal Pizza effect can correctly be chosen as a draw rather than mistakenly treated as a win.
4. Use opponent damage as the deterministic fallback when it does not worsen the terminal outcome. Never select the controller merely because the target list order puts that player first.
5. Resolve remaining ties by stable target ID ordering.

The policy should expose its score components in pure helper tests, not write gameplay events. Do not hardcode deck/opponent names. This policy uses only the game state represented by the public pilot view and does not attempt to predict unsupported effects.

## Purple Dragon Punks pilot behavior

### Main phase

The engine offers Purple Dragon Punks as an `ACTIVATE_ABILITY` when the source is untapped, has haste or is not summoning sick, and its parsed ability is supported. It creates one red lot restricted to `artifact_spell` and `activated_ability`. `payment_plan`/`activation_payment_plan` then expose only follow-on actions that can legally use eligible mana.

The AcceptancePilot’s `activate` stage chooses the first offered activation, with no relevance check. The Stage 002 runner executes that stage once per main phase; it does not re-enumerate the activation stage after Punks produces mana. As a result:

- It may tap Punks when there is no useful legal artifact spell or supported activation to follow.
- A red-restricted activation that becomes legal only after Punks produces mana is not offered until after the one activation-stage choice, so the pilot does not choose it in that pass.
- In the later `creature` stage, the pilot prioritizes any castable creature. It considers only the named `Skateboard` and `Spicy Oatmeal Pizza` as noncreature utility artifacts. Other legal artifact spells may be ignored; Pizza can also be deferred when another creature is castable.
- If the pilot activates Punks before casting an artifact, the engine correctly permits only an artifact payment. The pilot does not directly choose a payment plan; the legal cast action is the only evidence the selected spell can be paid.

### Priority window

The engine exposes Punks’ targetless immediate mana action to the current priority player. The AcceptancePilot chooses a priority action only when its `target_id` names an opposing Stack spell; otherwise it passes. Punks’ mana option has no target, so the pilot ignores it even when its mana would enable an otherwise legal response. Supported targetless activated abilities are likewise passed at priority.

The priority view contains current life, public battlefield, Stack, and legal options, but not the floating-mana ledger. The offered actions can communicate current legality; the pilot has no explicit engine-authenticated “this mana action enables these follow-ups” relation. Pilot code should not reconstruct payment legality from colors or card text.

### Smallest proposed policy change

Keep the legality planner authoritative. Have the engine attach or expose a pure, deterministic set of follow-on action identities that would become legal if a particular mana action resolved, computed using a hypothetical ledger lot with the parsed color, controller, restriction, and expiration. This is advisory decision context only; it must not reserve or mutate mana.

AcceptancePilot should:

- Choose Punks in main only when the engine reports a useful, currently legal follow-on action that can use `artifact_spell` or `activated_ability` mana.
- Prefer the associated follow-on after production by re-enumerating the activation decision once for the newly enabled action. Bound this continuation so free or repeatable abilities cannot create a pilot loop.
- At priority, activate Punks only when the engine reports that it enables a legal priority response; otherwise pass.
- Prefer actions that spend restricted mana before it expires, while leaving ordinary mana-source and action legality decisions to the engine.

This is a narrow decision-path addition, not a general pilot rewrite. It also avoids tapping Punks when its ability cannot enable a supported action.

## Integrated readiness classifications

| Finding | Classification | Evidence and reason |
|---|---|---|
| Pizza legal target selection | **BLOCKING** | The current player/creature target set is revalidated on resolution, but AcceptancePilot is not called and default target is always opponent. The Pizza path does not model hexproof/shroud/ward/protection; none occurs in the frozen card snapshot. This fails state-informed target choice and would require a legality extension if such restrictions enter scope. |
| Pizza outcome-aware self-damage choice | **BLOCKING** | Pilot does not compare the opponent’s 4-damage result with the mandatory 3 controller damage, including win/draw/loss outcomes. Engine terminal handling is separately covered by PR #388 synthetic evidence. |
| Punks main-phase useful activation | **BLOCKING** | Main `activate` chooses the first activation without payoff assessment, executes only once per phase, and does not revisit after producing mana. It can waste the tap or miss newly legal activated-ability payment. |
| Punks priority use | **BLOCKING** | Targetless mana actions are omitted by AcceptancePilot’s priority policy, even though the engine offers them. |
| Spell/ability payment restriction enforcement | **NONBLOCKING for the implemented paths** | PRs #393–#395 establish typed exact lots for artifact spells and supported battlefield/hand/graveyard activated abilities. Selected tests cover artifact acceptance, nonartifact rejection, and activation payment. Sneak and unsupported ability grammars remain outside scope. |
| Immediate mana execution / expiry / source departure | **NONBLOCKING** | PR #395’s selected tests cover immediate execution, stable priority epoch, step expiry, source departure, exact production/consumption identity, and reconciliation. |
| Pizza Stack ordering / stale target / source departure / terminal result | **NONBLOCKING in the represented model** | PR #388 report records selected synthetic tests for both-player priority, ordered damage, stale target, source departure, and simultaneous terminal draw. This audit did not rerun them. |
| Smoke 001 observed unsupported mechanics | **NONBLOCKING as source implementation gaps** | The forensic report’s Buzz Bots vigilance, April draw, Ravenous Robots trigger, Pizza damage, and Purple Dragon Punks ability each have a later implementation PR in the chain. Casey’s event-label issue was corrected. The frozen Smoke 001 itself remains historical and unchanged. |
| Future Planeswalker target | **NONBLOCKING for the frozen card pool; unsupported generally** | The frozen card snapshot has zero Planeswalker records, but engine target/damage modeling supports players and creatures only. |
| Full combined regression at final PR #395 source | **UNDETERMINED** | PR ancestry is exact, but the reports document per-checkpoint selected suites. No combined non-game acceptance selection at `7ed476f4...` is recorded. Run a named synthetic cross-feature selection after pilot changes and before considering a gameplay restart. |
| Broader ten-deck behavior outside Smoke 001 findings | **UNDETERMINED** | The audit checked the exact Smoke 001 findings and relevant decision paths; it did not run a roster-wide semantics or game audit. |

## Proposed individually named synthetic acceptance tests

These are proposed future nodes; they were not added or run during this read-only audit.

### Pizza targeting

- `tests/test_pizza_pilot_target_policy.py::test_acceptance_pilot_chooses_lethal_opponent_when_followup_is_survivable` — life totals set so 4 damage defeats the opponent and the controller survives 3; expected offered opponent target. Establishes policy result, not damage implementation.
- `tests/test_pizza_pilot_target_policy.py::test_acceptance_pilot_prefers_immediate_combat_threat_creature_to_nonlethal_player_damage` — a legal creature has visible stats/damage and opponent survives 4; expected that creature if the deterministic threat score is higher. Establishes visible-state selection, not long-horizon strategy quality.
- `tests/test_pizza_pilot_target_policy.py::test_acceptance_pilot_accounts_for_followup_lethal_as_draw_or_loss` — parameterize opponent at 4 and 5, controller at 3; expected draw-seeking opponent target in the first case and deterministic best available outcome in the second. Establishes the modeled terminal ranking only.
- `tests/test_pizza_pilot_target_policy.py::test_acceptance_pilot_target_tie_break_is_stable_and_returns_offered_id` — symmetric creatures and fixed offered set; repeated decisions return the same offered target. Establishes determinism and engine-option adherence.
- `tests/test_spicy_oatmeal_pizza_trigger.py::test_pizza_trigger_with_illegal_target_does_not_deal_either_damage` — existing engine regression; retain as compatibility coverage for target departure. Does not establish pilot choice quality.
- `tests/test_pizza_pilot_target_policy.py::test_empty_target_options_fail_closed_without_fabricating_target` — unit-level empty input; expected explicit no-choice result. It cannot establish a reachable no-target game state because current engine always offers both players in nonterminal games.

### Restricted-mana decisions

- `tests/test_purple_mana_pilot_policy.py::test_main_phase_activates_punks_for_newly_affordable_artifact_spell` — only an artifact spell is enabled by the hypothetical red lot; expected Punks activation followed by that legal cast.
- `tests/test_purple_mana_pilot_policy.py::test_main_phase_revisits_activation_after_punks_enables_supported_ability` — a `{R}` supported activation is unavailable before production and legal after; expected bounded follow-on activation with the exact production event consumed.
- `tests/test_purple_mana_pilot_policy.py::test_main_phase_does_not_tap_punks_without_supported_follow_on` — no qualifying artifact spell or supported activated ability; expected no Punks activation.
- `tests/test_purple_mana_pilot_policy.py::test_priority_uses_punks_only_when_it_enables_legal_response` — current priority has one artifact response enabled by restricted red; expected mana activation then that response, with unchanged epoch for mana production.
- `tests/test_purple_mana_pilot_policy.py::test_priority_passes_when_punks_mana_enables_no_response` — no enabled response; expected PASS and untouched source.
- `tests/test_purple_mana_pilot_policy.py::test_nonartifact_spell_is_never_reported_as_punks_mana_enabler` — hypothetical restriction must not make a nonartifact cast legal.
- `tests/test_purple_mana_pilot_policy.py::test_hypothetical_enabler_planning_is_pure_and_does_not_reserve_lot` — repeat option/view generation; expected identical actions, fingerprint, ledger revision, and object sequence.
- `tests/test_restricted_ability_payment.py::test_hand_landcycling_uses_activation_context_and_authenticated_allocation` and `tests/test_tunnel_rats_graveyard_return.py::test_tunnel_rats_spends_floating_black_mana_and_four_generic_sources` — existing payment-ID compatibility nodes; rerun with the pilot acceptance selection to ensure any option metadata preserves payment object identity.

The synthetic integration selection should also retain PR #395’s exact artifact/nonartifact spell, activated ability, expiry, source departure, and reconciliation nodes; PR #388’s Pizza trigger/terminal nodes; and PR #389/#390’s April and Robots authentication nodes. Execute individually named tests only.

## Recommendation

The chained sources and protected identities check out, and the implemented engine behaviors have component-level synthetic evidence. Pilot fidelity does not yet meet the requested behavior for Pizza target choice or useful Punks activation. The smallest changes are localized to a target-choice policy plus action-enablement context and bounded main/priority follow-up selection.

**READY FOR HQ PILOT IMPLEMENTATION AUTHORIZATION.** This recommendation authorizes only the proposed bounded pilot work and named synthetic validation. It does not authorize a complete game, smoke run, calibration, merge, deck change, or promotion.
