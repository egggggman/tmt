# Coverage-Aware Engine Validation Stage 0.2 — Merged-Main Readiness Audit #2

## Verdict

**READY — the accepted Stage 0.2 evidence runner is merged on `main`, its five-audit acceptance chain closes the prior tooling defects, the experiment remains structurally excluded from balance claims, and no merged change after PR #61 alters Cardcade gameplay or the accepted Stage 0.2 runtime contract.**

This audit authorizes **only execution of Coverage-Aware Engine Validation Stage 0.2 under its exact accepted contract**. It does not authorize calibration, balance analysis, Action #17, Pilot changes, deck changes, Design Studio revisions, or Prototype 0.3.

No Stage 0.2 gameplay was executed by this readiness audit.

## Audited merged baseline

- merged `main` SHA: `3fcce8ca7c7edff49327ec123c319b6704f544f5`;
- Stage 0.2 tooling merge: PR #61 / `609765a4886b506dca9cf9776e771cdd6528b763`;
- PR #61 exact-head CI: run `32912795075` — PASS;
- PR #61 local validation: **784 passed / 1 skipped**;
- PR #62 changes after PR #61: HQ/documentation resilience only; no engine, interpreter, Pilot, deck, card-data, Stage 0.2 runner, launcher, or validation-tool behavior changed.

The merged-main delta after the accepted runner is therefore non-gameplay documentation and HQ dispatch material. The accepted runner/runtime identities remain the identities banked by PR #61.

## Accepted evidence chain reconstructed

Readiness Audit #1 correctly returned **NOT READY — TOOLING** because Smoke 0.1 could not satisfy the Stage 0.2 matrix, schema, atomic failure, external storage, aggregate, and balance-firewall contract unchanged.

The bounded evidence runner then passed five independent audits:

1. Audit #1 — REJECT: terminal-result evidence and failure-state preservation defects.
2. Audit #2 — REJECT: coordinated terminal/inherited snapshot substitution and nested stripping.
3. Audit #3 — REJECT: replaceable execution-boundary fingerprint/preimage and hidden-zone/phase trust boundary.
4. Audit #4 — REJECT: commitment-channel inventory could retain an orphan/partial sidecar.
5. Audit #5 — **ACCEPT**: exact canonical commitment-directory inventory closed the final identified blocker without reopening Audits #1–#3.

Audit #5 records:

- candidate fingerprint: `c00ed8cf427d5507b28c779bb7cbd45b517822d9`;
- manifest digest: `9a8894750e5d57170398827e66bfb4ac7e289f17d29a88fea5a806eed4a7585a`;
- focused validation: **204 passed**;
- full repository validation: **784 passed / 1 skipped**;
- Ruff check: PASS;
- Ruff format check: PASS;
- `git diff --check`: PASS;
- Stage 0.2 games executed during construction/audit: **zero**.

The accepted runner was then banked by PR #61 with exact-head CI passing.

## Matrix and execution contract

The accepted Stage 0.2 contract remains:

- 10 frozen decks;
- 45 unordered cross-deck pairings;
- 5 deterministic seeds per pairing;
- 225 pairing/seed assignments;
- seeds `9001–9225`;
- canonical and reversed seat orientations;
- **450 distinct games**;
- 2 exact executions from fresh state per distinct game;
- **900 total executions**;
- duplicate executions are reproducibility evidence and never independent balance samples;
- 120-turn cap;
- no retry, replacement, resume, or partial accepted aggregate after a material stop.

The earlier HQ shorthand that described 225 as a distinct-game count is superseded by the specification: **225 pairing/seed assignments → 450 distinct games → 900 executions**.

## Frozen inputs and execution identity

The Stage 0.2 specification and accepted runner authenticate the frozen roster, card-data snapshot/manifest, ten ordered deck manifests, engine, interpreter, Pilot, Stage #002 evidence model, conformance model, inherited Smoke machinery, Stage 0.2 runner/launcher/schema/validator, execution commit, and canonical hashing methods.

Tracked text uses Git-clean identity semantics so LF/CRLF checkout representation does not change authoritative identity. Dirty, missing, untracked, substituted, wrongly typed, or unreconstructable consumed inputs fail closed before game #1.

The accepted Stage 0.2 runner additionally preserves an independent per-execution commitment channel with exact canonical directory inventory validation.

## Plan and authorization boundary

Plan mode is non-gameplay and non-authorizing. Accepted Audit #5 independently reconstructed the complete matrix and confirmed plan reconstruction creates no `Game` and consumes no gameplay RNG.

This readiness decision is the separate authorization gate required by the specification and PR #61.

**Execution is now authorized only for the exact frozen Stage 0.2 experiment.**

The operator must not alter seeds, orientations, decks, Pilot, engine semantics, turn cap, duplicate policy, evidence paths/contracts, classification rules, or balance firewall to make the run complete.

## Fail-closed requirements

The experiment must stop immediately on the first material defect, including:

- duplicate mismatch or RNG inconsistency;
- runner/conformance stop;
- invariant violation;
- illegal/partial/silent mutation;
- incomplete game at turn cap;
- frozen-input or execution-commit drift;
- malformed/missing/borrowed/stale provenance or lineage evidence;
- unclassified/multiply classified semantic occurrence;
- unsupported semantic silently executed or approximated;
- aggregate/classification reconstruction failure;
- commitment inventory/authentication failure;
- success/failure serialization or sidecar failure.

A REACHED / UNSUPPORTED semantic occurrence is **not itself a stop** when positively authenticated. It makes the game coverage-limited.

No failed execution may be skipped, retried, replaced, or resumed. A material failure requires preserved atomic evidence and a new governed correction before restart from game #1.

## Balance firewall

Every Stage 0.2 game and projection remains structurally:

`balance_valid: false`

This includes coverage-complete games.

Stage 0.2 winner, turn, matchup, seat, and other terminal data are engine-validation evidence only. They may not be used for:

- deck rankings;
- win-rate balance claims;
- matchup-strength conclusions;
- calibration;
- Design Studio deck changes;
- Prototype 0.3 authorization.

## Merged-main validation judgment

PR #61's accepted runner passed the complete five-audit chain, 784/1 local suite, and exact-head CI before merge. PR #62 subsequently changed only project/HQ documentation and work-packet material.

The current GitHub connector can authenticate merged file content and PR/CI history but cannot execute the local Python suite itself. Because no executable Cardcade path changed after the exact-head accepted runner CI, rerunning the full suite is not required to establish that the merged gameplay/runtime candidate is unchanged. The Stage 0.2 execution environment must nevertheless perform its normal preflight/frozen-input authentication and fail closed if its checkout differs.

## Readiness outcome

**READY**

Stage 0.2 execution is authorized under the exact accepted specification and runner contract.

## Exact next action

From a clean, current checkout of `main` at or descended only by non-gameplay dispatch documentation:

1. inspect the accepted launcher help/plan mode;
2. generate and validate the Stage 0.2 plan;
3. verify external evidence storage/preflight succeeds;
4. execute the accepted Stage 0.2 launcher exactly once;
5. stop on the first material defect;
6. preserve the complete success or failure artifact plus sidecars and independent commitment directory;
7. perform an independent **Stage 0.2 Results Audit** before interpretation.

Do not begin calibration after execution merely because the run completes. Results Audit and a separate HQ/Cardcade gate remain required.
