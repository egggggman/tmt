# Donatello Prototype 0.3a Semantic Coverage

Status: capability milestone; not a balance authorization.

## Evidence and scope

This artifact follows [`DONATELLO_P0_3A_REPRESENTATION_AUDIT.md`](DONATELLO_P0_3A_REPRESENTATION_AUDIT.md),
which classified the problem as `SEMANTIC_COVERAGE_DOMINANT` and selected
`FIX_DONATELLO_SIMULATOR_COVERAGE_FIRST`. The change is limited to reusable Cardcade
semantics and regression coverage. No decklist or smoke schedule is changed.

## Improved cards and actions

### Donatello's Technique

The authoritative card data describes a Sorcery with:

`Sneak {U} (...)` followed by `Draw two cards.`

Cardcade now recognizes the direct draw clause, treats the noncreature Sneak spell as
executable when that clause is supported, and resolves it through the existing draw
operation. During Sneak, the existing return-an-unblocked-attacker payment and tapped-
and-attacking creature behavior remain unchanged; for this noncreature spell, no
permanent is invented. Resolution moves the spell to its graveyard and draws exactly two
cards, producing the normal `card_drawn` events plus a `draw_spell_resolved` event.

### Reusable semantic surface

- `DrawCardsProgram` and `InterpretedDrawCardsSemantics` represent deterministic direct
  spell draw quantities, including number words used by the card data.
- `CastKind.DRAW_CARDS` carries the generic cast and resolution path.
- Existing `Game.draw` remains the source of library depletion, hand movement, empty-
  library handling, and draw events.
- Existing Sneak payment, choice, and resolution machinery is extended only to permit a
  supported noncreature draw spell.

AcceptancePilot now selects a legal cast whose Oracle fragment begins with `Draw `.
This is a generic action choice and does not name or special-case Donatello.

## Regression evidence

The exact prior diagnostic seed 3000 (Shredder P0.3 / Donatello P0.3a) is replayed in
`tests/test_donatello_technique_semantics.py`. Before this capability change, the audit
recorded Technique as drawn but never cast or resolved. After the change, the same replay
contains `cost_paid`, `spell_cast`, `draw_spell_resolved` with quantity 2, and
`spell_resolved` for Donatello's Technique. The test does not require a winner change.

Focused Sneak tests also verify legal casting, two-card hand/library movement, resolution
events, deterministic replay, and safe refusal when no supported noncreature payload is
present.

## Remaining Donatello gaps

The following central semantics remain outside this focused milestone and are not silently
approximated:

- Does Machines: Class level progression, mill/draw/discard enter effect, artifact
  recovery at level 2, and level 3 artifact animation/counters.
- Sewer-veillance Cam: enter/leave tap-or-untap choice and sacrifice draw activation.
- Bespoke Bō: its exact static/triggered support behavior still requires separate audit.
- Donatello, Way with Machines: artifact-entry counter trigger is covered by the
  separate [`DONATELLO_P0_3A_WAY_WITH_MACHINES_COVERAGE.md`](DONATELLO_P0_3A_WAY_WITH_MACHINES_COVERAGE.md)
  artifact; flying and broader closing behavior remain outside this slice.
- Donatello, Gadget Master: Sneak is represented by the existing creature path, but the
  combat-damage artifact-copy trigger and target choice are not claimed here.
- Donatello, Mutant Mechanic: tap-to-counter/animate activation and graveyard counter
  transfer trigger are not claimed here.
- Other artifact-producing/support creatures may still have card-specific coverage gaps.

These limitations mean the simulator is not a complete Donatello model and this PR does
not declare Donatello balanced or ready for another smoke conclusion.
