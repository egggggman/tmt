# Paramecia death / exile / reflexive return: pre-change architecture checkpoint

Baseline: main at b4a6eb8040f48c174002aaae9f3628b21c3596e1 (Leonardo family merged).

- Death anchoring: lethal state-based action calls `put_permanents_into_graveyard()` and `put_into_graveyard()`, which create a fresh graveyard incarnation and authoritative permanent-left/creature-died evidence. Existing dies support is limited to the fixed Draw-one trigger shape.
- Zone and identity: `move_object()` creates fresh identities for each transition and currently supports library, hand, stack, battlefield, graveyard, and exile. The prior Leonardo finality work established authoritative exile and distinct incarnation IDs.
- Paramecia Oracle: `When this creature dies, you may exile it. When you do, put target creature card from your graveyard on top of your library.` The engine has no optional death choice, no reflexive trigger object for this compound, no legal graveyard target chooser, and no death-to-exile/target-to-library transaction for this shape.
- Existing adjacent primitive: `mill_three` provides authoritative top-library-to-graveyard movement and evidence; generic `move_object(..., library_position="top")` provides zone identity creation. These must be reused without changing ETB mill semantics.
- Trigger/Stack: typed triggered abilities and priority delivery exist, but no Paramecia-specific trigger/evidence type or resolution validation exists. Existing dies/Draw trigger resolution and terminal handling are affected surfaces.
- Affected tests/surfaces: `put_into_graveyard`, lethal SBAs, `move_object`, `resolve_top_of_stack`, trigger queue/priority, library-top movement, target legality/invalidation, authoritative fingerprints/invariants, `tests/test_mill_three_action.py`, `tests/test_dies_draw_action.py`, and zone identity tests.

This checkpoint records the missing Paramecia compound lifecycle before implementation. No implementation decision is authorized by this note.
