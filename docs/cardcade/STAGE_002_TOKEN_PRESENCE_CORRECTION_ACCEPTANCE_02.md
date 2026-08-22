# Stage #002 Token-Presence Correction Acceptance Audit #2

## Decision

**ACCEPT — the bounded runtime-token execution-evidence provenance bridge is suitable to merge.**

## Audited checkpoint

- Candidate: `6b8f5f8a9892d4eb1a4f714ca59df4281d8642f8`
- Historical Audit #1: **REJECT**, preserved in `STAGE_002_TOKEN_PRESENCE_CORRECTION_ACCEPTANCE.md`
- Candidate delta: Stage #002 runner reconciliation and its tests only
- Exact-SHA CI: PASS, GitHub Actions run `32578613473`
- Stage #002 was not executed during this audit

## Independent findings

The correction closes Audit #1's downstream reconciliation defect without changing gameplay. It reconstructs the runtime-token semantic key from immutable presence facts and authenticates that presence against the unique authoritative `tokens_created` event. The authenticated facts include runtime object identity, owner, controller, creation event and source, definition-derived identity, fragment index, and Oracle fragment.

Normalization is deliberately narrow. A mature execution reference is translated to the runtime-token key only when exactly one authoritative token-presence record matches its runtime source and fragment. Zero or multiple matches leave the reference unchanged, after which existing reconciliation rejects it fail-closed.

Executable regressions prove that legitimate Food-token `activated_ability` and `food_activation` evidence authenticates. Altered owner, controller, creation event, creation source, fragment, and borrowed/fabricated object provenance do not authenticate. Ordinary frozen-card execution keys do not enter token normalization.

The bridge does not invent an Oracle ID, weaken general execution authentication, modify ordinary card identity, or alter Create Token, Food, activated-ability, Pilot, deck, or gameplay behavior.

## Validation evidence

- Full suite: `571 passed / 1 skipped`
- Stage #002 runner: `35 passed`
- Ruff format/check: clean
- `git diff --check`: clean
- Acceptance #001 seeds 7001–7005: byte-identical duplicate runs
- Acceptance #001 trajectories: unchanged
- Invariant violations: `0`
- Conformance stops: `0`

## Gate

- Token-presence correction: **ACCEPTED**
- Eligible next operation: bank this evidence, merge the correction, and validate merged `main`
- Stage #002 execution remains blocked until merged-main validation succeeds
- Action #13, gameplay changes, smoke, calibration, Prototype 0.3, Pilot changes, and deck revisions remain unauthorized

**ACCEPT — the corrected bounded Stage #002 token-presence reconciliation is suitable to merge.**
