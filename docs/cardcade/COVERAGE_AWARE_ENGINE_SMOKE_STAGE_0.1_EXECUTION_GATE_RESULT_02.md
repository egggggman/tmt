# Coverage-Aware Engine Smoke Stage 0.1 Execution Gate Result #2

## Verdict

**VALID FAIL-CLOSED STOP — Stage 0.1 is incomplete and blocked pending independent opportunity-applicability failure audit.**

No accepted aggregate or success artifact was produced. The runner preserved a complete atomic failure artifact and matching SHA-256 sidecar.

## Frozen baseline and authorization probe

- Merged execution baseline: `16c99daf778b13bb446231e4fe9dd3e1adcd8a8e`
- Local `main` and `origin/main`: exact match before execution
- Frozen manifest digest: `247169fa22f946682ef82408a9b18876637798504d624c63857a7026c735fcb0`
- Matrix: 45 pairings / 180 distinct games / 360 executions
- Non-game atomic-write authorization probe: PASS
- Probe failure-artifact SHA-256 before cleanup: `abffe8be5f2e0b65ee8d6601a76764f716eac5951a840920d21e97c3f04a8cd4`
- Probe artifacts removed and worktree clean before Smoke execution

The probe instantiated no Game. It deliberately caused manifest preflight drift, verified `accepted_aggregate: false`, execution ordinal/completed count zero, independently matched the sidecar to the JSON bytes, and removed both temporary probe files.

## Authoritative Smoke failure evidence

- Failure artifact: `docs/cardcade/COVERAGE_AWARE_ENGINE_SMOKE_STAGE_0.1_FAILURE.json`
- Artifact SHA-256: `be47d78c62874e3fe8f73c1ffffe71d3270089be1440a211551bf907e77254b3`
- Sidecar: present and independently matched
- Success artifact: absent
- Accepted aggregate: false
- Completed distinct games: 0
- Execution ordinal: 1
- Duplicate member: first
- Game: `april_oneil--bebop_rocksteady:canonical:8001`
- Pairing: `april_oneil--bebop_rocksteady`
- Seed/orientation: 8001 / canonical
- Last authoritative state: turn 16, precombat main, empty Stack, no Priority
- Last state fingerprint: `d2e1a4f41195f2250f65ca61a637814fdeb2bc0d7d8439ec3a489074499f31a9`

## Stop

During creature resolution, the corrected ordering registered semantic presence and then created the authoritative `CREATURE_ENTERED` rules event. The event producer attempted to join a registered occurrence through `_witness_from_event()`. `_validate_opportunity_applicability()` rejected the proposed event/fragment relationship:

`ValueError: event does not establish semantic applicability`

The exception was preserved as `SmokeGameFailure`. The engine did not weaken applicability validation or manufacture a witness.

This gate report does not infer the card, fragment, runtime source ID, or the correctness of the producer/validator disagreement. Those facts must be reconstructed from the preserved snapshot and traceback in an independent audit.

## Gate

Do not rerun Smoke Stage 0.1 and do not modify engine, conformance, runner, Actions, Pilot, or decks before an independent **Coverage-Aware Smoke Stage 0.1 Opportunity-Applicability Failure Audit #1** determines:

1. the exact registered occurrence and authoritative event;
2. why `_witness_from_event()` proposed the join;
3. why the accepted applicability validator rejected it;
4. whether the producer, registration cursor/provenance, or validator owns the defect;
5. the smallest evidence-backed correction, if any.

Action #14, calibration, Prototype 0.3, Pilot/deck changes, and the historical 900-game smoke remain blocked.
