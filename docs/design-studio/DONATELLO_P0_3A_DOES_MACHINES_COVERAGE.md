# Donatello P0.3a — Does Machines Semantic Coverage

Status: focused Cardcade coverage milestone; this does not declare Donatello balanced.

## Authority and exact card text

The authoritative card-data source is `cardcade/card-model-0.6.json`, cross-checked against the normalized Cardcade snapshot used by the engine. Does Machines is an Enchantment — Class with this text:

> (Gain the next level as a sorcery to add its ability.) When this Class enters, mill two cards, draw two cards, then discard two cards. {1}{U}: Level 2. When this Class becomes level 2, return up to two target artifact cards from your graveyard to your hand. {4}{U}: Level 3. At the beginning of combat on your turn, put three +1/+1 counters on target artifact you control. If it isn't a creature, it becomes a 0/0 Robot creature in addition to its other types.

The clauses are intentionally tracked separately:

| Clause | Coverage in this milestone |
| --- | --- |
| Gain the next level as a sorcery | Unsupported; no generic Class level state exists yet |
| Enter: mill two, draw two, discard two | Implemented faithfully as a reusable interpreted setup sequence |
| `{1}{U}: Level 2` | Unsupported |
| Become level 2: recover up to two artifacts | Unsupported |
| `{4}{U}: Level 3` | Unsupported |
| Beginning of combat: three counters and Robot conversion | Unsupported |

## Implemented semantics

The interpreter now recognizes the exact bounded Class enter sequence and exposes it as a permanent cast with a reusable mill/draw/discard program. The engine:

- allows the recognized Class permanent to be cast when its mana is payable;
- creates a permanent-entered trigger for the Class;
- mills up to the specified quantity from the library to the graveyard;
- draws the specified quantity through the canonical draw path;
- deterministically moves the specified number of cards from hand to the graveyard;
- logs the complete before/after zone evidence and trigger resolution.

AcceptancePilot selects the generated setup cast when present. No general Pilot strategy or balance policy was changed.

## Deterministic regression

The existing Donatello P0.3a seed 3000 diagnostic previously showed Does Machines as recognized but inert. With this milestone, the same deterministic game records `spell_cast`, `permanent_resolved`, `etb_mill_draw_discard_committed`, and `trigger_resolved` events. The committed setup record contains two distinct milled object IDs, two drawn cards, and two discarded object IDs. Replaying the seed produces identical event logs.

## Remaining Does Machines and Donatello gaps

Class progression, sorcery-speed level activation, level-2 artifact recovery, level-3 artifact animation, Robot type creation, and +1/+1 counters remain unsupported. Other documented Donatello coverage gaps—including central permanent abilities on Donatello, Way with Machines, Donatello, Gadget Master, Donatello, Mutant Mechanic, Sewer-veillance Cam, and Bespoke Bō—remain unchanged. This milestone makes only the setup clause executable and must not be interpreted as a balance result.
