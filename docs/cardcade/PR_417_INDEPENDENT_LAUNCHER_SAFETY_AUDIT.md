# PR #417 Independent Launcher Safety Audit

## Verdict

**REWORK — do not issue a real-game authorization or run Diagnostic Game 002 from this candidate.** The candidate corrects the three PR #416 launcher defects, but two additional acceptance gaps remain:

1. The launcher accepts unsigned, locally fabricated approval JSON. It verifies fields and hashes but cannot authenticate that HQ issued either document.
2. It accepts an incomplete reconciliation object as `READY` and returns CLI exit code 0.

Both findings were reproduced without entering gameplay. PR #417 was not modified.

## Source and environment

- PR #417 audited HEAD: `6ded938a7680e767f9ac5e231774591ef461a27b`.
- PR #415 historical source: `188da5fabc231c91b222c642b6c9cf6fe4377c9f`.
- PR #415 supported ancestry base: `6612ba7ee36d7eeeb2b090a3a7664662d6fcdeac`.
- Accepted main observed in both worktrees: `10d2ac80ef5b81b3a209a3133eb0a84633a1f944`.
- Candidate reviewer worktree: `.audit-pr417-independent` (detached at audited HEAD).
- Historical-source worktree: `.audit-pr417-original-red` (detached at PR #415).
- Runtime: Python 3.12.10, pytest 8.4.2, Ruff 0.16.1.
- The candidate imports `engine07` and `stage002` from the audited checkout; the 36-case selection passed source-path and shared-`Game` checks.
- All executor probes constructed initial synthetic state/snapshots only. No gameplay function entered the game loop.

## Historical PR #415 defect reproductions

The original launcher had no source-approval or run-authorization input. `_verify_source()` only checked whether HEAD descended from PR #413's supported base. Against the exact PR #415 worktree, `_verify_source()` accepted HEAD `188da5f...` without any per-implementation approval or run-specific authorization.

Three setup-only probes reproduced the original behaviors:

| Defect | PR #415 observation |
| --- | --- |
| Source approval | Ancestry check accepted the checkout without an exact authorized SHA. |
| Reconciliation failure | Injected reconciliation exception left `reconciliation_completed: false`; CLI returned **0**, with `run_returned_normally: true`, `terminal: false`, and no blocked status. |
| Reuse across launcher instances | Two fresh launcher instances with separate output directories invoked the synthetic executor twice; there was no shared authorization identity or persistent claim. |

The original eight named launcher regression tests also passed on PR #415: **8 passed**. The three manual probes above are the historical RED evidence; they do not invoke complete games.

## PR #417 independent validation

The complete 36-case selected synthetic regression command documented in `docs/cardcade/DIAGNOSTIC_LAUNCHER_SAFETY_CORRECTION.md` was independently rerun on exact HEAD `6ded938...`:

- Launcher: 8 cases.
- Authorization/evidence safety: 12 cases, including the parameterized stop/invariant cases.
- Capture lifecycle: 10 cases.
- Terminal combat: 6 cases.
- Result: **36 passed, 0 failed, 0 skipped**.

The suite independently covered the prior cross-process claim behavior, claim persistence after an execution exception, exact source mismatch, frozen-input mismatch, missing/failed reconciliation, stop records, invariant violations, missing presence, nonterminal output, CLI nonzero status, capture binding, original exception preservation, and terminal-combat regressions.

Additional malformed-document probes rejected malformed JSON, a mismatched source SHA, a mismatched run SHA, and a run authorization referencing a different approval. The six frozen input hashes matched PR #417's documented allowlist.

## Confirmed residual defect: unauthenticated authorization documents

The current tests construct source-approval and run-authorization JSON in a temporary directory using the public schemas. `_verify_source()` accepts those files when their fields match the current HEAD and compiled input allowlist. The documents have no signature or MAC, and the launcher accepts caller-selected file paths without checking a protected location or Windows ACL.

This means the SHA checks establish document/content consistency, not HQ authorship. Any local principal able to invoke the launcher and provide files can mint an `approval_id`, exact source SHA, allowed input hashes, and a fresh `authorization_id`. The durable claim prevents reuse of an ID after a run; it does not prevent an unauthorized caller from minting a new ID.

Trusted issuance plus controlled file access could be sufficient only if that trust boundary is enforced operationally (restricted launcher identity, protected authorization directory and ACL, and no arbitrary path selection). PR #417 does not enforce those conditions. For a self-contained launcher acceptance contract, require a cryptographic signature over both approval records, validate the signer against an out-of-band trusted key, and bind the signature to source SHA, input hashes, match parameters, and unique authorization ID. Do not issue real-game credentials until the trust boundary is accepted and enforced.

## Confirmed residual defect: incomplete reconciliation accepted

An adversarial synthetic fixture returned a normal snapshot with `terminal: true`, event list and presence list, while a patched reconciler returned only:

```json
{"stop_records": [], "invariant_violations": []}
```

`_blocking_findings()` returned no blockers. `run_status.json` recorded `diagnostic_status: READY`, and the actual CLI exited **0**. The report lacked the normal reconciliation fields/digest and was not an authenticated complete reconciler result. This violates the requirement that incomplete or unauthenticated evidence remain BLOCKED.

The launcher should validate a strict reconciliation schema, report digest, source/manifest binding, and required evidence fields (or use an existing authenticated reconciliation validator) before setting `READY`. Add RED/GREEN tests for missing required fields, missing/invalid report digest, wrong manifest/source, and fabricated minimal reports. Keep exception/snapshot artifacts when blocking.

## Historical evidence preservation

All nine PR #406 Diagnostic Game 001 artifacts were rehashed and matched their recorded full SHA-256 values. The three original reconciliation stops remain present and unchanged:

1. `stop-000001`, `illegal_mutation`, turn 16 / combat_damage.
2. `silent_approximation`, `presence_evidence_missing`.
3. `silent_approximation`, the preserved trample/combat event and object identity list.

All six frozen input hashes matched the PR #417 allowlist. No frozen inputs or historical artifacts were modified.

## Required correction before acceptance

1. Authenticate HQ authorization records (prefer signature verification with an out-of-band trust key; otherwise enforce and independently audit a protected issuance/ACL boundary).
2. Reject structurally incomplete or unauthenticated reconciliation reports and return nonzero from the CLI.
3. Add deterministic synthetic tests for both corrections and rerun the existing 36-case selection.

No gameplay, calibration, Smoke restart, merge, deck change, baseline promotion, or real-game authorization is included in this audit.

**Recommendation: REWORK.** The source pinning, one-use claim, and previously tested exception and terminal controls are useful, but the two residual blockers make this launcher unsuitable for a future single-game diagnostic at this source identity.
