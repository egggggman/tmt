# Semantic Closure Family 5 - Ooze Spill Pre-Change Architecture Checkpoint

Baseline: 7bfe030464128a05630394ccd90f654bad31c6ed (merged Raphael mainline).

## Authorized Oracle surface

Ooze Spill is an instant: Counter target spell. Create a Mutagen token. A Mutagen token is an artifact with "{1}, {T}, Sacrifice this token: Put a +1/+1 counter on target creature. Activate only as a sorcery."

## Current architecture and gaps

- The counter-target spell action already represents an instant from hand, opposing authoritative Stack targets, normal timing and mana payment, and counter resolution.
- Generic token creation already creates authoritative token permanents through the Stack lifecycle, but no exact Mutagen token program or Ooze Spill compound effect joins the counter and token transactions.
- Activated abilities already support mana, tap, sacrifice, target selection, sorcery-speed checks, and counter placement for represented cards, but Mutagen token activation is not wired to the generated token identity.
- Counter replacement opportunities and authoritative counter-placement evidence exist and must remain in the Mutagen path.
- Stack and zone movement already create fresh identities and preserve event evidence; the Ooze spell, target spell, generated token, activation, and target permanent must remain linked by object IDs and event records.
- No deck, unrelated counterspell, token, or activated-ability redesign is authorized.

## Affected surfaces and evidence

Implementation is limited to the exact Ooze Spill interpreter coverage, counterspell plus Mutagen compound resolution, Mutagen token definition and activation path, target and timing legality, payment/tap/sacrifice lineage, counter replacement integration, and authoritative evidence. Focused tests must prove legal and illegal opposing Stack targets, counter resolution, token creation, Mutagen activation at sorcery speed with {1}, tap, sacrifice, legal and illegal creature targets, replacement behavior, deterministic identity lineage, and fail-closed terminal handling.
