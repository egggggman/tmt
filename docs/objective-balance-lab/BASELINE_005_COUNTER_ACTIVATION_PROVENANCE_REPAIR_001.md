# Baseline 005 — counter-activation provenance repair

## Decision

**Repair checkpoint: READY. Renewed calibration: BLOCKED pending separate HQ authorization.**

The preserved Attempt 6 failure was reproduced, explained, and repaired with a
generic provenance correction. No calibration run was repeated.

## Root cause

The failing activation was a legal Fugitive Droid token ability:

`{U}, Sacrifice this creature: Counter target spell that targets an artifact or creature you control.`

At resolution, the source permanent had correctly left the battlefield and its
ability remained independent on the stack. The paid token moved to graveyard,
then the normal token state-based action made it cease to exist. Its
authenticated destination object therefore had zone `former`. The generic
validator required `sacrificed.zone == "graveyard"` and rejected this valid
post-state-based-action activation as `counter activation provenance is
invalid`.

This was not an illegal action, source/controller mismatch, target mismatch,
or forged event. The invariant was too restrictive for token sacrifice costs.

## Exact reproduction

- Runtime before repair: `ee8d37b192a6eb37526283a458e54fb243e17d5e4dad68bd60cd863bfcf1a194`
- Matchup: `donatello|bebop_rocksteady`
- Orientation: canonical
- Block: 47
- Seed: `12506277166433065153407346632076121278501225696392466898823914761107207299783`
- Source: Fugitive Droid token, `object-000175`, controller Donatello
- Stack ability: `object-000199`
- Sacrifice destination: `object-000198`
- Target spell: `object-000197` (Mutant Chain Reaction)
- Mana source: `object-000185`
- Pre-failure event: token moved battlefield → graveyard, then `token_ceased`
- Original traceback: `stage002.py:681 → _drain_priority → process_priority_resolution → resolve_top_of_stack → _resolve_activated_ability → _validate_counterspell_provenance`

## Repair

The validator now accepts either:

1. a non-token sacrifice destination that remains in graveyard; or
2. a token destination in `former` only when an authenticated `token_ceased`
   event identifies that exact object and records `previous_zone == "graveyard"`.

All source, controller, source-card, stack-target, activation-evidence, and
mana-payment checks remain strict. Forged or stale token evidence still fails.

## Validation

- Preserved seed replayed repeatedly with matching deterministic snapshots.
- Focused counter/provenance suite: **25 passed**.
- Full regression: **2,117 passed, 10 skipped**.
- Ruff check and format: passed.
- 100-game Donatello/Bebop & Rocksteady diagnostic: **100/100**, zero errors,
  zero draws, 50/50 orientations; wins Donatello 59, Bebop & Rocksteady 41.
- Diagnostic artifact SHA-256:
  `96b024012c202a1d64ce4a949c00c25594c3db7b549892f86c65c9a15c341307`.
- New semantic runtime:
  `4978cdaa3c78d4e1f90498444d92850736c325df59c772e4bfaf8cc27ab27933`.

The diagnostic is repair evidence only and is excluded from balance
interpretation. The Attempt 6 fail-closed artifact remains immutable and
excluded.
