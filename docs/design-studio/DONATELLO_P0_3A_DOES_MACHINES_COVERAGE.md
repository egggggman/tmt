# Donatello P0.3a — Does Machines Semantic Coverage

Status: focused Cardcade coverage milestone; this does not declare Donatello balanced.

## Authority and exact card text

The authoritative card-data source is `cardcade/card-model-0.6.json`, cross-checked against the normalized Cardcade snapshot used by the engine. Does Machines is an Enchantment — Class with this text:

> (Gain the next level as a sorcery to add its ability.) When this Class enters, mill two cards, draw two cards, then discard two cards. {1}{U}: Level 2. When this Class becomes level 2, return up to two target artifact cards from your graveyard to your hand. {4}{U}: Level 3. At the beginning of combat on your turn, put three +1/+1 counters on target artifact you control. If it isn't a creature, it becomes a 0/0 Robot creature in addition to its other types.

| Clause | Coverage in this milestone |
| --- | --- |
| Gain the next level as a sorcery | Implemented for the supported level-2 activation; main-phase, no-stack timing is enforced |
| Enter: mill two, draw two, then discard two | Implemented as a reusable interpreted setup sequence |
| `{1}{U}: Level 2` | Implemented as reusable Class level advancement with `{1}{U}` payment |
| Become level 2: recover up to two artifacts | Implemented as a triggered, targeted recovery to the controller's hand |
| `{4}{U}: Level 3` | Unsupported |
| Beginning of combat: three counters and Robot conversion | Unsupported |

## Implemented semantics

The interpreter recognizes the exact bounded Class enter sequence, level-2 activation, and level-2 recovery fragment. The engine gives Class permanents an initial level of 1; pays and advances the level only during the active player's main phase with an empty stack; emits an authenticated `class_level_advanced` event; and enqueues the recovery trigger.

At trigger placement, only authoritative artifact cards in the controller's graveyard are offered. The deterministic default selection follows the existing first-options convention and chooses at most two sorted object IDs. Invalid, duplicate, non-artifact, and out-of-offer selections are rejected. Resolution moves selected cards from graveyard to hand, preserves zone ownership/order invariants, logs target selection and recovery, and safely resolves with zero legal targets. AcceptancePilot requires no strategy change: its existing activate-stage selection sees the legal level action, while the engine's deterministic chooser applies the same first-options convention for recovery targets.

## Deterministic regression

The existing Donatello P0.3a seed 3000 regression still records `spell_cast`, `permanent_resolved`, `etb_mill_draw_discard_committed`, and `trigger_resolved` without an engine/Pilot error. Synthetic deterministic states cover level initialization, payment, timing, level persistence, recovery, target restrictions, zero targets, exact zone movement, and replay-stable event logs.

## Remaining Does Machines and Donatello gaps

Level-3 artifact animation, Robot type creation, and +1/+1 counters remain unsupported. Other documented Donatello coverage gaps — including central permanent abilities on Donatello, Way with Machines, Donatello, Gadget Master, Donatello, Mutant Mechanic, Sewer-veillance Cam, and Bespoke Bō — remain unchanged. This is not a balance result.
