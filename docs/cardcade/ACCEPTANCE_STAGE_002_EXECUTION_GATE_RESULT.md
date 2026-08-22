# Acceptance Stage #002 Execution Gate Result

Execution checkpoint: `58bacdd819192195cccc89826a3b5717fa787641`

Merged runner baseline: `15b779fe865770d63df2e6aabd2a839aa9b54c65`

Status: **STOPPED — EVIDENCE-LAYER APPLICABILITY FAILURE**

## Authorized operation

The accepted frozen Stage #002 runner was invoked once with `--execute`, targeting the durable
output path `docs/cardcade/ACCEPTANCE_STAGE_002_RESULTS.json`. No engine, Action, Pilot, deck,
prototype, test, calibration, or smoke behavior was changed before or during execution.

## Stop evidence

The runner exited with code 1 during its first game execution path. While resolving a spell and
registering unsupported Oracle semantics, opportunity-witness construction attempted to join an
existing typed event to an occurrence. The shared authoritative applicability validator rejected
that join with:

`ValueError: event does not establish semantic applicability`

The exact command and traceback are preserved in
`ACCEPTANCE_STAGE_002_EXECUTION_FAILURE.log`. Because execution aborted before `execute_stage()`
returned, the requested results JSON was not written.

The traceback does not serialize the active `GameSpec`, so this evidence does not claim a pairing,
seed, orientation, completed-game count, or semantic classification that the failed run did not
authoritatively report.

## Gate interpretation

This is not evidence of an invariant violation, nondeterministic duplicate, illegal state mutation,
or gameplay defect. It is a prospective conformance/instrumentation failure: the broader frozen
environment reached an event/fragment combination that the accepted applicability join refused,
and the runner did not convert that refusal into a reconstructive canonical conformance-stop
artifact.

Per the Stage #002 governance rule, execution stopped immediately. The command was not rerun and
the implementation was not modified. No partial result is presented as Stage #002 evidence.

## Decision

**STAGE #002 INCOMPLETE — preserve and independently audit this failure before authorizing any
correction or rerun.**

Action #13, Pilot/deck changes, smoke testing, calibration, and Prototype 0.3 remain unauthorized.
