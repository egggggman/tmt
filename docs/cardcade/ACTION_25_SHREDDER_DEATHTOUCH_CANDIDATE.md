# Action #25 — Shredder temporary deathtouch

This bounded candidate is based on main `71fe57e685c450056d9d837676792833d5ebed91`.

It recognizes Shredder, Unrelenting's exact trigger, registers ETB and attack triggers through the existing trigger and Stack/Priority lifecycle, selects and authenticates another creature you control, and grants deathtouch until end of turn with authoritative cleanup. Source departure, stale or relinked identities, illegal controllers, and missing targets fail closed.

## Validation

- Focused Action #25 and related regression tests: 225 passed.
- Full pytest: 915 passed, 1 skipped.
- Ruff check: passed.
- Ruff format --check: passed.
- `git diff --check`: passed.
- Existing Stage #002 runner: 16 games / 32 executions, deterministic and invariant-clean. The Shredder deathtouch witness classified as executed in 1 occurrence; the remaining copies were present but unreached.

The measurement is gameplay-priority evidence only and makes no balance claim. Action #26 remains unauthorized.
