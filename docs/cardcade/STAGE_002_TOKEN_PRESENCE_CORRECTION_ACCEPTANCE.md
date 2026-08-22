# Stage #002 Token-Presence Correction Acceptance Audit

## Decision

**REJECT — runtime-token presence identity is deterministic and authoritative, but downstream execution-evidence reconciliation cannot authenticate mature token-sourced Action evidence.**

## Audited checkpoint

- Candidate: `f45b162175ef0d5658720ab93ae5a928c1dfec47`
- Candidate delta: exactly `src/tmnt_design_studio/stage002.py` and `tests/test_stage002_runner.py`
- Local branch and remote branch: synchronized at the audited SHA
- Candidate CI: PASS, GitHub Actions run `32577242232`
- Stage #002 was not executed during this audit

## Accepted properties

The correction fixes the original `TokenDefinition.oracle_id` crash without inventing an Oracle identity. Runtime-token presence keys are deterministically derived from authoritative token-definition characteristics and runtime provenance. Presence preserves the token definition identity, runtime object identity, owner, creation event/source, Oracle fragment, and subsequent zone lineage. Distinct token definitions do not collapse, duplicate construction is deterministic, and ordinary frozen-card semantic keys are unchanged.

The focused and full validation evidence passes, including actual `TokenDefinition` presence construction, movement/cessation lineage, and deterministic reconciliation tests.

## Material blocker

The new runtime-token namespace is not compatible with existing authoritative execution references for token-sourced Actions.

An independent probe used the existing canonical Food-token activation fixture and passed its real snapshot through Stage #002 presence/reconciliation logic. The runner produced this authoritative token-presence key:

`runtime-token:11e5b9c66c87a5121698e0d95f1863aaf1d4228efd9598fffc8fa25667c8e4f0:0:0:cb05e5757b1f515a43d62d11fadde4eeb00ee564d308757c27506b790ef3e0e5`

The mature `activated_ability` and `food_activation` execution references for the same authoritative source object (`object-000097`) and fragment instead used:

`definition:cb05e5757b1f515a43d62d11fadde4eeb00ee564d308757c27506b790ef3e0e5:0:0:cb05e5757b1f515a43d62d11fadde4eeb00ee564d308757c27506b790ef3e0e5`

Neither execution reference authenticated. Reconciliation emitted fail-closed `silent_approximation` stops for the unknown definition key and the affected evidence records. Thus a genuinely executed canonical Food-token activation cannot be classified `EXECUTED` under the new token-presence identity.

This is a runner/reconciliation identity defect, not a token-gameplay or Food-transaction defect. Fail-closed behavior is correct, but Stage #002 cannot proceed because its report would reject valid mature Action evidence.

## Smallest evidence-backed correction

Add a bounded runner-only authentication/normalization path from authoritative runtime-token presence to mature token-sourced execution references. It must require all of the following before normalizing the reference to the runtime-token semantic key:

- exact evidence kind and evidence ID resolving in the authoritative transaction index;
- exact runtime source lineage;
- exact Oracle fragment identity;
- the expected legacy engine token key derived from that same fragment and token definition;
- agreement with the authoritative runtime-token presence record.

Do not change engine Action evidence, token gameplay, Create Token, Food activation, or ordinary card semantic keys.

Add regressions using an actual canonical Food token activation proving that both `activated_ability` and `food_activation` references authenticate. Adversarially prove that a different token/source, wrong fragment, wrong evidence kind/ID, or different token definition cannot borrow the alias. Preserve deterministic runtime-token identity and fail-closed behavior.

## Validation

- Full suite: `563 passed / 1 skipped`
- Stage #002 runner: `27 passed`
- Create Token: `49 passed`
- Conformance: `37 passed`
- Card data: `5 passed`
- Ruff format/check: clean
- `git diff --check`: clean before this evidence-only report
- Gameplay and Acceptance #001 behavior: unchanged by the candidate

## Gate

- Token-presence correction audit: **REJECT**
- Stage #002: **BLOCKED; not rerun**
- Action #13: **BLOCKED**
- Smoke, calibration, Prototype 0.3, Pilot, deck, and gameplay changes: **not authorized**

**REJECT — correct only the bounded runner reconciliation between authoritative runtime-token presence and mature token-sourced execution evidence, then submit the immutable correction for a second independent audit.**
