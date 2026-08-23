# Coverage-Aware Engine Smoke Stage 0.1 Execution Gate Result #1

## Verdict

**VALID FAIL-CLOSED EXECUTION STOP — Stage 0.1 is incomplete and blocked pending independent failure audit.**

This result establishes an authoritative semantic-registration exception during the first execution path. It does not establish a gameplay, matchup, card, Action, or Pilot diagnosis.

## Frozen execution baseline

- Merged `main`: `5b5cdf02452ebd77c2c1bcc9f885d85290d53cdd`
- Local `main` and `origin/main`: exact match
- Merged-main CI: PASS, run `32615513543`
- Local validation: `622 passed / 1 skipped`; Ruff and `git diff --check` clean
- Plan digest: `3fe9093e11c3057e7aeaf459e6ae7f9b1154ffe35adc73aec3273331c2658cf8`
- Matrix: 45 pairings / 180 distinct games / 360 executions
- Specification, readiness, runner-audit, and canonical-hashing evidence: canonical Git content hashes preserved

## Primary stop

During resolution of a main-action cast, `resolve_top_of_stack()` called `report_unsupported_abilities(..., source=permanent)`. Semantic occurrence registration rejected that source because it was not an authoritative runtime object:

`ValueError: semantic presence requires an authoritative runtime object`

The accepted fail-closed engine/evidence boundary rejected the attempted registration. No accepted Smoke result was produced.

The traceback alone does not safely establish the active matchup, seed, orientation, card, source identity, zone history, or completed-game count. Those facts must not be inferred.

## Failure-artifact serialization boundary

While preserving the structured failure artifact, the local execution environment denied creation of the temporary artifact file under `docs/cardcade`. Consequently:

- no success artifact exists;
- no structured failure JSON exists;
- no SHA-256 sidecar exists.

This second failure is an execution-environment/filesystem boundary, not evidence that the runner accepted a partial aggregate. It also means the specification's atomic failure-evidence contract was not completed for this launch. The console traceback is preserved separately as historical evidence.

## Gate

Do not rerun Stage 0.1 and do not modify the runner, engine, Actions, Pilot, or decks before an independent **Coverage-Aware Smoke Stage 0.1 First-Execution Failure Audit #1** reconstructs the primary semantic-registration failure and separately assesses the artifact-write environment.

Action #14, calibration, Prototype 0.3, deck revisions, Pilot changes, and the historical 900-game smoke remain blocked.
