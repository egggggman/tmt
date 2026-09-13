# Leonardo graveyard casting + finality: pre-change architecture checkpoint

Baseline: main at 90ede67b0f9be880fa5f79228483790e618625a2 (Menace family merged).

- Graveyard permission: `legal_main_actions()` only generates hand casts. `_witness_graveyard_cast_permissions()` recognizes the Leonardo-shaped permission and records opportunity evidence for own-graveyard creature cards at the printed power/toughness threshold, but it does not create a cast option.
- Zone and identity: `move_object()` creates a fresh `CardObject`, `StackObject`, or `Permanent` identity for each zone transition; former objects cannot move and stale identities are rejected.
- Casting/payment: `execute_main_action()` accepts only `CardObject` cast objects; `announce_spell()` requires an authoritative hand card, normal main timing, owner/controller match, `payment_plan()`, and moves Hand -> Stack before resolution. No alternate-zone cast source is represented.
- Entry counters: `place_counters()` is authoritative and emits counter evidence, but creature resolution has no finality-specific entry hook or counter on the newly created incarnation.
- Death/SBA replacement: `LethalDamageStateBasedAction` and `put_into_graveyard()` always perform Battlefield -> Graveyard. There is no finality replacement that redirects a finality-marked incarnation to exile/former.
- Affected surfaces/tests: `legal_main_actions`, `execute_main_action`, `announce_spell`, `cast`, `resolve_top_of_stack`, `move_object`, `put_into_graveyard`, lethal SBAs, counter evidence, and conformance/identity tests around graveyard witnesses, stack casting, zone replacement, and finality counters.

This checkpoint records the missing alternate-zone cast transaction and finality lifecycle before implementation. No implementation decision is authorized by this note.
