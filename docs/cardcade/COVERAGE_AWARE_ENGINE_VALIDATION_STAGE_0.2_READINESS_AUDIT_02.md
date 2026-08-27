# Coverage-Aware Engine Validation Stage 0.2 Readiness Audit #2

## Verdict

**READY — the exact Evidence Runner accepted by Audit #5 survived integration onto `main`, merged-main
CI and local validation pass, frozen inputs and the complete plan reconstruct, and the external
evidence destination passed a non-game atomic persistence probe.**

This is a deployment/readiness decision, not another Evidence Runner acceptance audit. No Stage 0.2
game was executed during integration or readiness review.

## Integrated baseline

- PR: `#61`;
- merged `main`: `609765a4886b506dca9cf9776e771cdd6528b763`;
- merged-main CI: Test run `32912923454`, PASS;
- exact PR head: `148559adf66bbdac11545d07df9c4110c4f4116d`;
- exact-head push CI: Test run `32912795075`, PASS;
- PR CI: Test run `32912864719`, PASS;
- local `main == origin/main`: yes;
- local worktree before this report: clean.

The accepted five-file portable candidate fingerprint reconstructs unchanged:

`c00ed8cf427d5507b28c779bb7cbd45b517822d9`

Audit #5 remains byte-identical at:

`c29b188d322f4287a412c3e8726bae6011b077f36319f15d4c67d066d4f70a2f`

Audits #1–#4 also reconstruct their preserved SHA-256 values exactly. The squash merge retained the
specification, readiness history, all five adversarial audits, implementation and tests.

## Manifest and frozen inputs

The accepted pre-bank manifest was:

`9a8894750e5d57170398827e66bfb4ac7e289f17d29a88fea5a806eed4a7585a`

That manifest bound pre-bank execution checkpoint `901dd715ff431df5adcf2da6feca51bf0c513c52`.
Replacing only the manifest's expected execution checkpoint with the immutable merged-main SHA
produces the deployment manifest:

`f8a4c531f12f739f8964e31bb52fc9913398869bbe108e0f3695145da0f03449`

All other frozen identities, deck/card-data inputs, runner/launcher identities, hashing schemes,
matrix rows and policy fields remain reconstructively identical. The platform-independent hashing
contract remains `smoke-frozen-input-hashing-v2`.

## Plan reconstruction

The merged-main launcher was run in plan mode only. The generated plan reported `authorized: false`
and independently reconstructed:

- 45 unordered pairings;
- 225 unique pairing/seed assignments;
- seeds exactly 9001–9225;
- five seeds per pairing;
- both seat orientations;
- 450 distinct game identities;
- two duplicate executions per game;
- 900 executions total;
- duplicate executions carry reproducibility weight, not additional sample weight;
- `balance_valid: false` structurally for every game.

The temporary plan artifact was removed after verification. Plan mode created no Game and consumed no
gameplay RNG.

## Evidence destination readiness

The predeclared external evidence directory is:

`C:\Projects\tmt-evidence-archive\stage02`

The intended paths are currently absent and collision-free:

- `COVERAGE_AWARE_ENGINE_VALIDATION_STAGE_0.2_RESULTS.json`;
- its `.sha256` sidecar;
- `COVERAGE_AWARE_ENGINE_VALIDATION_STAGE_0.2_RESULTS.json.commitments/`;
- `COVERAGE_AWARE_ENGINE_VALIDATION_STAGE_0.2_FAILURE.json`;
- its `.sha256` sidecar.

A non-game probe used the accepted atomic JSON/sidecar writer in the intended execution environment.
The written JSON independently matched its sidecar at SHA-256
`5bbc98916b42b0375df23329a9a9196e99a11b1edab747647a7bf0e57069bdfd`. Both probe files were then
removed successfully, leaving the destination empty and unambiguous.

## Validation

- merged-main full pytest: **784 passed / 1 skipped**;
- merged-main Ruff check through the repository `uv` environment: PASS;
- merged-main Ruff format check: PASS;
- `git diff --check`: PASS;
- merged-main CI canonical terminology scan: PASS;
- candidate fingerprint: exact;
- Audit #1–#5 hashes: exact;
- Stage 0.2 games executed during readiness: **zero**.

The host's standalone Ruff launcher was initially blocked by Windows Application Control
(`WinError 4551`). This was an environment execution-policy event, not a lint result. The same checks
passed through the repository's accepted `uv run ruff` environment and in merged-main Linux CI.

## Fail-closed execution contract

Execution must start from game #1 and stop immediately on frozen-input drift, runner stop, invariant
violation, incomplete/turn-cap game, duplicate mismatch, provenance/authentication failure,
commitment inventory or sidecar failure, classification/aggregate reconstruction failure, or final
serialization/persistence failure. No failed game may be skipped, replaced or resumed around.

The raw success artifact, sidecar and independent commitment directory—or the atomic failure artifact
and all commitments genuinely established before failure—must be preserved before interpretation.

## Authorization boundary

**Coverage-Aware Engine Validation Stage 0.2 execution is READY and may be authorized against merged
baseline `609765a4886b506dca9cf9776e771cdd6528b763`: 450 distinct games / 900 deterministic executions.**

This readiness decision does not authorize balance conclusions, Action #17, calibration, Pilot/deck
changes, Design Studio revisions or Prototype 0.3. Every Stage 0.2 game remains
`balance_valid: false`, including coverage-complete games. Results require an independent Results
Audit and coverage/engine interpretation before any downstream decision.
