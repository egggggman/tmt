# Acceptance Stage #002 First-Execution Correction Acceptance Audit

Corrected candidate: `f7aebf178b2cb8ea8efb922dd0abd820aa795ddb`

Failure-evidence baseline: `5d7e0e97f2ce358fdf802f01a5d1a17a802f653a`

Verdict: **ACCEPT**

## Scope and evidence preservation

This was an independent evidence-only audit of the bounded correction made after Stage #002's
first fail-closed execution stop. No implementation or test file was changed during this audit.
Stage #002 was not rerun.

The exact failure transcript and gate result committed at the evidence baseline are unchanged by
the candidate. The correction changes only:

- `src/tmnt_design_studio/engine07.py` — one applicability-prefilter predicate; and
- `tests/test_conformance07.py` — one stale-candidate regression and one positive exact-ETB
  regression.

No Action, game rule, Pilot, deck, Stage matrix, manifest, validator, or execution runner changed.

## Re-audit of the failure

The preserved failure occurred when `_witness_from_existing_events()` selected a historical
`CREATURE_ENTERED` event because it contained the source and the unsupported fragment had a
self-ETB-shaped prefix. `_witness_from_event()` then reached the shared authoritative validator,
which correctly rejected the event because its number did not equal the occurrence's
`registration_event_cursor`.

The corrected producer now applies that same authoritative cursor predicate before forwarding the
candidate. A historical matching event is skipped; it is not presented as an applicable event and
therefore creates neither a witness nor an exception.

The shared `_validate_opportunity_applicability()` boundary is byte-unchanged. In particular, the
correction does not weaken its requirements for exact self-ETB, later Alliance entry, or later
attack-declaration provenance.

## Adversarial and positive evidence

The negative regression constructs:

1. an authoritative source permanent with self-ETB-shaped unsupported text;
2. a real `CREATURE_ENTERED` event containing that source;
3. a later unrelated entry event, advancing the authoritative registration cursor; and
4. subsequent unsupported-fragment registration.

It proves the earlier event number is strictly less than the occurrence cursor and that no witness
is created. Registration completes without an exception.

The positive regression constructs the exact just-completed self-ETB event and immediately
registers the occurrence. It proves event number and registration cursor are equal, exactly one
witness is created, and the witness retains the authoritative event ID.

These tests reproduce both sides of the disputed boundary without executing a Stage #002 game.

## Validation

Cleaned-state validation on the immutable corrected checkpoint reproduced:

- full suite: **559 passed / 1 skipped**;
- runtime conformance: **37 passed**;
- Stage #002 runner: **23 passed**;
- card-data integrity: **5 passed**;
- Ruff format/check: clean;
- `git diff --check`: clean;
- tracked JSON parsing: clean;
- strict tracked UTF-8 scan: clean;
- canonical terminology scan: clean;
- mojibake scan: clean;
- production-placeholder scan: clean.

Acceptance #001 seeds 7001–7005 were replayed twice. Every duplicate artifact was byte-identical,
all trajectories remained unchanged, and all games reported zero invariant violations:

- seed 7001 — Raphael, turn 14;
- seed 7002 — Raphael, turn 18;
- seed 7003 — Leonardo, turn 19;
- seed 7004 — Leonardo, turn 43;
- seed 7005 — Raphael, turn 16.

The accepted prospective classification remains **11 REACHED / UNSUPPORTED**, **7 PRESENT /
UNREACHED**, and **18 authoritative witnesses**.

GitHub Actions run `32551482591` passed against the exact corrected candidate SHA.

## Verdict

**ACCEPT — the correction aligns historical-event candidate selection with the existing
authoritative self-ETB applicability boundary, preserves valid exact-ETB witnessing, changes no
gameplay behavior, and is suitable to merge before restarting Stage #002 from execution #1.**

Stage #002 remains frozen until this correction and audit evidence are banked, integrated, and
validated on merged `main`. Action #13, smoke testing, calibration, Prototype 0.3, Pilot changes,
and deck changes remain unauthorized.
