# Cardcade Engine 0.7 Rules Coverage Matrix

Status is scoped to the deterministic Engine 0.7 foundation and Acceptance Match #001. Current
Comprehensive Rules and current Oracle text take precedence over this implementation record.

| Concept | Rules anchor | Acceptance cards | Status / abstraction | Deterministic evidence | Known limitation |
| --- | --- | --- | --- | --- | --- |
| Zones, opening seven, 20 life | CR 103, 400 | both decks | Partial; library, hand, battlefield, graveyard | opening-state test | mulligans and exile unsupported |
| Starting player draw | CR 103.8 | both decks | Validated for two-player game one | first-player-draw test | play/draw choice is runner-fixed |
| Turn structure | CR 500–514 | both decks | Partial; beginning, two mains, combat, ending | runner event trace | priority, stack, upkeep actions and detailed steps unsupported |
| Land play | CR 305 | Plains, Mountain | Validated; one basic land per active turn | land-per-turn test | nonbasic lands unsupported |
| Mana and affordability | CR 106, 601 | mono-W / mono-R lists | Partial; untapped basics, mana value and colored symbols | casting and sickness test | costs, alternate costs and mana abilities beyond basics unsupported |
| Creature permanents | CR 110, 302 | 16 creatures | Partial; actual base P/T, tapped, damage, sickness | casting/combat tests | continuous effects, counters, characteristic changes unsupported |
| Attackers and blockers | CR 508–509 | both decks | Partial; basic one-to-one legal declarations | sickness and combat tests | restrictions/evasion, menace, must-block, vigilance, first/double strike unsupported |
| Combat damage / lethal | CR 510, 704 | both decks | Partial; simultaneous basic damage, lethal death, player damage | combat, graveyard and win tests | trample, lifelink and damage-order complexity unsupported |
| Targeted creature damage | CR 115, 120 | Manhole Missile | Partial; legal opposing creature, 3 damage | dead-target and lethal-state machinery | optional hand cycling unsupported |
| Restricted destruction | CR 115, 701.7 | Make Your Move | Partial; opposing creature with power 4+ | focused runner trace | artifact/enchantment targets unsupported in this slice |
| Losing the game | CR 104 | both decks | Validated for life ≤0 and empty-library draw | life/win and empty-library tests | concede and other loss/draw conditions unsupported |
| Card abilities | card Oracle text | both decks | Unsupported unless named above; every skipped semantic is logged | runner limitation list | Sneak, Alliance, Classes, Equipment, tokens, buffs, triggers and other text do not resolve |

## Governance boundary

The Leonardo and Raphael Prototype 0.1 files are inputs and remain frozen. Engine 0.1–0.6 code,
models, reports and run artifacts remain preserved. This slice does not claim a credible balance
result and does not authorize a broad smoke run or any deck revision.
