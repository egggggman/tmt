# Creature Dies → Draw One Acceptance Audit #2

Status: **ACCEPT**  
Audit date: 2026-08-22  
Branch: `agent/cardcade-dies-draw`  
Audited commit: `e4d00dc90f18f96eca1c0fba48a0480dafe21b5d`  
Audit #1 checkpoint: `22b3cae44bcdec5212cd624c5e10ef096202846f`  
Rejected candidate: `d65b21d352b9552e6d046ab2c2e7c2d984da2755`

## Evidence integrity

Audit #1 remains byte-identical at SHA-256
`a11362a2d98e304c7c964f718f8eb42dac75fc69efa5bee411b1b6480f6e96b0`.
The corrected commit is exactly one implementation commit beyond that evidence checkpoint and changes
only `src/tmnt_design_studio/engine07.py` and `tests/test_dies_draw_action.py`.

Exact-SHA GitHub Actions run `32603148190` passed, including Ruff format/check, the full pytest
suite, and the canonical terminology scan.

## Audit #1 blocker

The correction captures the permanent's authoritative evaluated battlefield type line immediately
before the zone change and derives last-known creature status from that state. `CREATURE_DIED` is
created only when the departing object was a creature at that moment.

The immutable rules event freezes:

- runtime object identity;
- controller;
- evaluated type line;
- last-known creature status.

Resolution and invariants authenticate the trigger against that registered event. They require the
recorded type line and creature flag to agree and no longer infer death qualification from the
printed card definition.

The adversarial printed-creature/current-noncreature case is covered: a Buzz Bots definition whose
authoritative battlefield type is `Artifact — Robot` reaches the graveyard without creating
`CREATURE_DIED` or a pending trigger. Fabricated last-known characteristics fail both invariant and
resolution checks without drawing.

## Preserved bounded behavior

- exact Oracle grammar remains `When this creature dies, draw a card.`;
- full-pool membership remains Buzz Bots only;
- neighboring death triggers remain unsupported;
- last-known controller, simultaneous deaths, and new-object zone identity remain coherent;
- delivery remains death event → trigger → Stack → Priority/pass → Draw;
- an empty-library Draw finishes trigger resolution before the failed-Draw state-based action;
- Acceptance #001 remains deterministic at 18 registrations / 6 pairs with unchanged trajectories
  and zero dies/Draw transactions.

Validation reproduced `596 passed / 1 skipped`, with Ruff and `git diff --check` clean. No Stage
#002 rerun, Pilot/deck change, smoke test, calibration, or Prototype 0.3 work occurred.

## Verdict

**ACCEPT — corrected bounded creature dies → Draw one trigger delivery is suitable to bank and
integrate with its preserved rejection history.**

