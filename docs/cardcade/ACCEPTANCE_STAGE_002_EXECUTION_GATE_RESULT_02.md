# Acceptance Stage #002 Fresh Execution Gate Result #2

Execution baseline: `41cde4871b8346b72104b11606f46b89c542e1d7`

Execution branch: `agent/cardcade-stage-002-execution-02`

Status: **STOPPED — TOKEN-PRESENCE RECONCILIATION DEFECT**

## Authorized operation

After PR #46 merged the independently accepted stale self-ETB candidate correction, merged `main`
passed 559/1 validation, focused conformance/runner/card-data suites, Ruff, Acceptance #001
duplicate replay, and exact-SHA GitHub CI. A new branch was created from that merged baseline and
the unchanged frozen Stage #002 runner was invoked once from game #1.

## Stop evidence

The run exited with code 1 in `_add_created_token_presence()`. While adding runtime presence for a
created token, the runner attempted to derive a semantic key from `obj.card.oracle_id`. The runtime
card was a `TokenDefinition`, which has no `oracle_id` attribute, producing:

`AttributeError: 'TokenDefinition' object has no attribute 'oracle_id'`

The exact command and traceback are preserved in
`ACCEPTANCE_STAGE_002_EXECUTION_FAILURE_02.log`. Execution aborted before `execute_stage()`
returned, so `ACCEPTANCE_STAGE_002_RESULTS.json` was not written.

The traceback does not serialize the active pairing, seed, orientation, token identity, or
completed-game count. This record therefore makes no claim about any of those facts.

## Gate interpretation

This is a Stage #002 runner/conformance reconciliation defect. It does not establish an engine,
token-transaction, Pilot, deck, gameplay, invariant, illegal-mutation, or nondeterminism defect.
The run stopped before it could produce a conformance result, preventing token presence from being
silently omitted or misclassified.

No correction was attempted and Stage #002 was not rerun.

## Decision

**STAGE #002 INCOMPLETE — preserve and independently audit the TokenDefinition presence failure
before authorizing any correction or another execution.**

Action #13, Pilot/deck changes, smoke testing, calibration, and Prototype 0.3 remain unauthorized.
