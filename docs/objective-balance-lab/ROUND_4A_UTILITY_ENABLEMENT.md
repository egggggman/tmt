# Round 4A Utility Usage Enablement — Diagnostic and Scope

This diagnostic preserves the original Round 4A evidence and does not change either candidate deck.

## Frozen card definitions

| Card | Mana value | Type / subtype | Rules text | Supported timing |
|---|---:|---|---|---|
| Skateboard | 1 | Artifact — Equipment | When this Equipment enters, tap target permanent. Equipped creature gets +1/+0 and has haste. Equip {1} ({1}: Attach to target creature you control. Equip only as a sorcery.) | Cast as a permanent; Equip only as a sorcery |
| Spicy Oatmeal Pizza | 3 | Artifact — Food | When this artifact enters, it deals 4 damage to any target and 3 damage to you. {2}, {T}, Sacrifice this artifact: You gain 3 life. | Cast as a permanent; Food activation in a main phase |

Definitions are from `cardcade/scryfall-tmt-pza-tmc-2026-08-13.json`, the frozen authoritative snapshot.

## Decision-path diagnosis

Both cards are legal and affordable when their mana is available, but the interpreter returned `CastKind.UNSUPPORTED`. Consequently `Game.legal_main_actions()` emitted no CAST option, the AcceptancePilot never received a utility action, and no permanent-entry or activation opportunity could occur.

| Card | Primary blocker | Secondary blocker | Evidence |
|---|---|---|---|
| Skateboard | ACTION_NOT_GENERATED | ACTIVATION_UNSUPPORTED | `cast_program()` returned `UNSUPPORTED`; the existing activation interpreter intentionally rejects Equip nested context. |
| Spicy Oatmeal Pizza | ACTION_NOT_GENERATED | None for Food activation | `cast_program()` returned `UNSUPPORTED`; its canonical Food activation is already represented once the artifact is on the battlefield. |

## Minimal implementation boundary

The implementation adds generic noncreature permanent casting for bounded artifact/enchantment/permanent cards, reuses existing Food activation semantics, and adds a generic Equipment activation program for the existing Equip grammar. It does not alter deck lists, priority ordering, stack architecture, or historical Round 4A evidence.

Telemetry distinguishes legal opportunity, selection, cast, resolution, and activation/equip for these two cards. AcceptancePilot chooses utility casts only after existing draw/setup/creature priorities and chooses supported utility activations deterministically when available.

## Diagnostic gate and authenticated replay

The narrow diagnostic used 80 games (20 against Shredder and 20 against April for each candidate), with zero runtime errors. Skateboard produced legal opportunities and successful casts/equips. Candidate B also produced legal Pizza opportunities, casts, resolutions, and Food activations. Candidate A contains no Pizza copies, so its Pizza usage is correctly zero.

The exact frozen Round 4A schedule was then replayed: 1,800 games, 900 per candidate, 100 per opponent, 50 canonical and 50 reversed starts per opponent, with zero runtime errors. The post-support artifact is separate from `ROUND_4A_RAPHAEL_EVIDENCE.json`; the latter remains unchanged historical pre-support evidence.

The corrected telemetry is controller-scoped. It records drawn, legal opportunity, selected, cast, resolved, activated/equipped, and effect-used events for Raphael only. Repeated legal-action enumeration is retained as an opportunity count and is not presented as a unique-game count.
