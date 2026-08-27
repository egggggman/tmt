# WP-0001 — Cardcade Engine Validation Stage 0.2 merged-main readiness

Owner: **TMNT the Cardcade Game**  
HQ tracking: **Yes**  
Status: **Authorized for readiness audit only**  
Starting ref: **current merged `main` after PR #61**

## Objective

Determine from merged-main evidence whether Coverage-Aware Engine Validation Stage 0.2 gameplay execution is authorized under the accepted Stage 0.2 specification and readiness contract.

## Scope

- validate the exact merged-main Stage 0.2 runner/tooling state;
- run the repository-prescribed readiness checks and exact-head CI/validation required by the accepted contract;
- verify frozen inputs, plan commitments, duplicate/reproducibility expectations, evidence directories, and fail-closed behavior;
- produce a durable readiness decision and evidence;
- if READY, state the exact authorized Stage 0.2 execution command/contract without broadening it.

## Prohibited changes

- no deck changes;
- no Pilot tuning;
- no new Action implementation;
- no calibration;
- no Prototype 0.3 authorization;
- no broad/historical smoke substitution;
- no changing simulator assumptions to improve win rates;
- no bypassing a failed readiness check.

## Inputs

- merged PR #61 and its Stage 0.2 specification/readiness/audit evidence;
- current `main`;
- Cardcade Stage/Smoke runner tests and conformance checks;
- frozen Prototype 0.2 deck/environment inputs;
- repository CI and validation configuration.

## Acceptance contract

The readiness audit must:

1. run against current merged `main`, not an older candidate branch;
2. reproduce the accepted Stage 0.2 plan contract: 45 pairings / 225 distinct planned games / 450 executions / 900 per-execution commitment artifacts;
3. confirm `balance_valid: false` remains enforced for engine-validation evidence;
4. confirm deterministic/frozen-input commitments and fail-closed validation;
5. run the exact applicable full/focused validation and record counts;
6. record CI status for the exact audited head when required by the accepted contract;
7. produce one explicit outcome: **READY**, **NOT READY**, or **BLOCKED BY NEW DEFECT**;
8. preserve failure evidence if any check fails.

## Stop conditions

Stop and report rather than improvise if:

- merged-main behavior differs from the accepted Stage 0.2 contract;
- evidence cannot be reconstructed/authenticated;
- the runner would execute balance-valid calibration behavior;
- a new engine defect is exposed;
- the required correction would broaden beyond readiness/evidence tooling.

## Required handoff

Report:

- audited `main` SHA;
- readiness outcome;
- commands/checks run;
- full and focused validation results;
- CI result;
- evidence paths and digests;
- any failure provenance;
- whether Stage 0.2 execution is now authorized;
- exact next action.

## Authority boundary

This packet can authorize only the **readiness decision**. If the accepted readiness contract says READY, Stage 0.2 may then be executed only within its exact existing contract. This packet cannot authorize calibration or Prototype 0.3.
