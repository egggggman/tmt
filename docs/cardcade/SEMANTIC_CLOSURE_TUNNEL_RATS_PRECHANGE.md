# Tunnel Rats Graveyard Return — Pre-change Checkpoint

Exact Oracle fragment:

`{4}{B}: Return this card from your graveyard to the battlefield tapped.`

Current architecture has authoritative CardObject identities in graveyard, a generic `move_object` zone transition, represented mana payment, and battlefield casting/activation paths. `announce_activated_ability` currently requires a battlefield Permanent source, so it cannot announce this graveyard ability. Existing graveyard support is limited to permission-based spell casting and does not model a graveyard activation that returns its own card.

The closure must add only the missing lifecycle: own graveyard source authority, main-phase timing and `{4}{B}` payment, tapped battlefield entry with a fresh incarnation, source departure from graveyard, and fail-closed stale or illegal activation evidence. Affected surfaces are the interpreter’s activated-effect grammar, priority action generation/announcement, zone movement and identity evidence, and focused activation/invariant tests. Existing graveyard casting, finality, combat, and unrelated activated abilities remain regression surfaces.
