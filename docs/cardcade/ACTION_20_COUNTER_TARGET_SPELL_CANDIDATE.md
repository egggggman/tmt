# Action #20 — Counter Target Spell

This bounded candidate implements the exact frozen Fugitive Droid activated ability:

`{U}, Sacrifice this creature: Counter target spell that targets an artifact or creature you control.`

The candidate is based on evidence-banked main commit `d1665aa09c4e93ef2cc343ab2954453345edf1c8`, whose parent is the accepted Action #19 baseline `34124fbd96ed56e683ffe855ecbbccba787c9ab6`.

## Resolve

The existing activated-ability, mana-payment, sacrifice, Stack/Priority, targeting, zone, provenance, incarnation, and event-history paths are extended for this exact ability. A response is offered only when a qualifying spell is on the Stack. The selected spell must target an artifact or creature permanent controlled by the activating player. The source incarnation, payment, sacrifice destination, target spell identity, and target relationship are authenticated. The ability revalidates those facts on resolution, then moves a legal countered spell from the Stack to its authoritative graveyard zone and records the result. Invalid, stale, fabricated, relinked, or wrong-zone objects fail closed.

## Exclusions

No universal counterspell framework, unrelated Fugitive Droid behavior, arbitrary target predicates, other counterspell cards, deck changes, balance tuning, calibration, broad simulation, Prototype 0.3, or GUI/infrastructure work is included. Frozen deck lists are unchanged.

## Validation

- Focused Action #20 tests: 20 passed.
- Focused and relevant Stage/Smoke/regression selection: 233 passed.
- Full pytest suite: 885 passed, 1 skipped.
- Ruff check, Ruff format check, and `git diff --check` are run before commit.

The implementation is intentionally bounded by the current StackObject spell and permanent target model; unsupported near-neighbor semantics remain unsupported.
