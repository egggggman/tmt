# Semantic Closure Family 4 - Raphael Pre-Change Architecture Checkpoint

Baseline: 51552b9ef18e3d6ddfcd5e2619f854a9ebb95560 (merged Paramecia mainline).

## Authorized Oracle surface

Raphael, Most Attitude is a legendary creature with:

- Menace (This creature cannot be blocked except by two or more creatures.)
- Alliance - Whenever another creature you control enters, you may exile the top card of your library.
- Whenever Raphael attacks, until end of turn, you may play a card exiled with Raphael.

The implementation must preserve source identity and controller ownership through each linked exile, then expose only those linked cards to the attack-time permission.

## Current architecture and gaps

- PlayerState.exile and move_object(..., "exile") already provide authoritative exile incarnations with fresh object IDs, but no source-linked Raphael collection exists.
- Alliance detection supports existing counter, modal, temporary-keyword, token, and other bounded Alliance forms. The optional exile-top clause has no executable effect or chooser.
- Attack delivery creates ATTACKERS_DECLARED events and supported attack triggers, but no Raphael attack-time play-permission trigger or source-linked candidate snapshot.
- Existing casting and payment paths enforce normal timing, mana plans, and authoritative zone movement for ordinary cards; play-from-exile permission and land-play accounting are not connected to Raphael.
- Zone movement creates a new incarnation and marks the source former; linkage must therefore be stored as immutable source and card identity facts rather than inferred from names or current zones.
- Existing cleanup and turn transitions provide end-of-turn expiry hooks for temporary effects, but no Raphael permission record is present.

## Affected surfaces and evidence

Implementation surfaces are limited to the Alliance trigger detector and stack lifecycle, attack trigger delivery, linked-exile registry, casting and play legality and payment, cleanup expiry, and authoritative event and fingerprint evidence. Focused tests must prove optional top-card exile, source-linked identity across movement, attack trigger creation, legal land and spell play with normal timing and payment, unrelated-exile exclusion, source departure handling, and permission expiry. No unrelated exile redesign or deck changes are authorized.
