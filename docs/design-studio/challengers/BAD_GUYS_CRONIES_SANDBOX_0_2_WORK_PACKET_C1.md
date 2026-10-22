# Bad Guys 0.2 — Work Packet C1: Generic block restrictions

**Status: READY for independent C1 acceptance; BLOCKED for gameplay testing and C2.**

No deck, Baseline 005 artifact, R9-B evidence, historical simulation, or gameplay
run was changed or launched.

## Provenance

- Accepted A/B runtime: `00fc49eb47d9ffd3d0243564cc7c9763d11738ca9698811306102747a060d374`
- C1 runtime: `960df6898bcfa765a572f6128391dba735d322f9ce579e2866dcc3d1874bca4b`
- Candidate SHA-256: `cacc77648a4d1659b8ae640d95ac2672694e6951553980246e6d001e5152bfb4`
- Baseline 005 SHA-256: `aaa61d3a3d65f7c8ab74062cc8f41d220a46066b44c28e3c71921c570a6b66ed`
- Audit publication commit: `6b59ab0e87d550514c2fb058f15b493fcc11ba01`

The C1 runtime digest is calculated deterministically from normalized LF bytes of
the semantic interpreter, engine, and pilot-observation source files, in path
order. It is distinct from the accepted A/B identity because block legality now
has a new executable semantic path.

## Implementation

The interpreter now recognizes the generic Oracle grammar:

`<subject> can't be blocked by more than one creature.`

The engine evaluates the restriction at blocker declaration rather than by card
name. It supports:

- direct self restrictions (`This creature` or the printed source name);
- controller-scoped quality restrictions such as `Boars you control`;
- one blocker as legal, two or more blockers as illegal;
- independent treatment of multiple attackers;
- live source authority, controller, type-line quality, and zone checks;
- interaction with existing Menace (the intersection can be effectively
  unblockable when neither one- nor two-block assignments are legal);
- normal combat resolution once a legal declaration is selected.

The previous literal phrase check was replaced with the generic interpreter and
live applicability predicate. No Bad Guys, Rocksteady, Boar, or deck-name branch
was added.

## Deterministic validation

Focused C1 fixtures: **22 passed**. They cover zero/one/two blockers, explicit
illegal declarations, simultaneous attackers, direct and quality restrictions,
control changes, source departure, combat resolution, Menace interaction, and
repeat identity observations. Existing combat suites passed unchanged.

Full regression: **1,633 passed, 10 skipped**.

Static checks passed:

- `uv run ruff check src/tmnt_design_studio/card_interpreter07.py src/tmnt_design_studio/engine07.py tests/test_block_restriction_c1.py`
- `uv run ruff format --check .`
- `git diff --check`

No gameplay simulation was run.

## Refreshed coverage

C1 closes the Rocksteady/Boar single-block restriction family. Menace and
Rhino-wide menace grants remain explicitly unsupported and are not included in
this packet. The next ranked family is Bebop & Rocksteady's mandatory
sacrifice-or-discard combat obligation, but C2 is not authorized by this report.

**Recommendation:** READY for independent C1 acceptance; BLOCKED for C2 and all
gameplay testing pending HQ review.
