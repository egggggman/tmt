# Frog Butler Any-Color Mana — Pre-change Checkpoint

Exact Oracle fragment:

`{T}: Add one mana of any color.`

Current architecture has authoritative battlefield Permanents, tap costs, represented colored mana requirements, and payment ledgers for fixed-color sources. The interpreter and activation path intentionally do not yet model an any-color choice: generic token any-color text is recorded as unsupported, and mana payment consumes sources selected from fixed `_mana_color` values. Frog Butler therefore needs a bounded choice-bearing mana activation that validates an untapped authoritative source, records the chosen color, and exposes that color to one actual payment.

The closure must preserve summoning-sickness and tap legality, deterministic chooser evidence, stale-source invalidation, and existing mana/payment behavior. Affected surfaces are the activated-ability grammar, priority action/announcement, mana ledger, and focused tests. No general mana-system redesign or Reach work is included.
