# CARDCade 300-Game Execution Readiness — November 2, 2026

**Decision: BLOCKED — specific technical and approval gates remain.** This package advances the trust-chain prototype for independent review. It does not authorize signing, grants, wrapper invocation, or gameplay. PR #374 remains draft; actual batch status remains 0/300.

## 1. Implementation status

Added isolated, explicitly non-production synthetic candidates under `.diag003-memory-independent-review/completion-receipt-chain-v1/`:

- `synthetic_candidate.py` models strict supervisor-attestation creation, batch receipt issuance only after validation, separate purpose/key checks, receipt verification with an independently pinned key, and a no-replace publisher interface.
- `test_synthetic_chain.py` constructs a deterministic ten-game block from the preserved Stage 002 manifest contract and runs the complete mock chain. It generates three distinct deterministic test-only RSA identities for authorization, supervisor attestations, and receipt signing.

The candidate does not open keys or access Windows, CNG, Job Objects, real output paths, grants, or historical data. It receives an in-memory `EvidenceSnapshot`; it does not implement a production snapshotter, a real supervisor integration, CNG provider, Windows service, or filesystem receipt publisher. The helper `create_execution_attestation` can authenticate only facts supplied to it; a production supervisor must obtain those facts itself from terminated process/Job Object handles and a locked snapshot. The mock publisher is an injected test double.

The previous verifier, wrapper, helper, schedule, manifests, dependencies, and reports remain unchanged. The currently referenced verifier candidate still uses the same public-key identity for grant and receipt verification; the new separate-key verifier function is only in the synthetic candidate and is not integrated into that verifier.

## 2. Artifact identities

| Artifact | SHA-256 | State |
|---|---|---|
| Draft PR #374 head | `41f8f8b10583e342dd2f9db85946a1998cd2a80a` | Open, draft; prior to this local synthetic package |
| Approved 300-game schedule digest | `9206c4267027473218f18e9482abcccb8a64dcfc62a7511d39b711a427a2179c` | Preserved; not regenerated |
| Original post-run verifier | `259c5f18edbfe262778ba351651c28f845901f687764193afb2d0ef85402f39a` | Preserved |
| Corrected verifier candidate | `45d920a2128e430574ab2eed96f3bc62281d8128ab4e81b0155b7bc710232385` | Candidate; not independently approved |
| Wrapper candidate | `f912753455f03013b484fde989a966fefc682aa41a16b2253d59a9dd8e8757ad` | Candidate; not signed or invoked |
| Schedule-integrity helper | `b1fafc333a3c4a0720c8b84c23639eac70c40a09c6f180ac70d9ab9fa93af41d` | Candidate |
| `stage002_authorization.py` dependency | `1fd4db87131a0fef996fc2df7aee5f6634fdbc2d7b90f226c76217596fdb6540` | Pinned reviewed source candidate |
| `stage002_batch.py` dependency | `30720c8d720b52a9538b79063d785e57dc37762bf5099215b7ee05cef0a80293` | Pinned reviewed source candidate |
| Synthetic chain model | `b4b2b811d6cec93e1423b51142602f22fff77a056121e15ee0ad4fab59be09a5` | Non-production candidate |
| Synthetic chain tests | `7f09f004720dd2e342a64c19850ce581e26790c5f34ba8c36e9c5726d9107d1c` | Test-only RSA keys/data |

The test source rechecks the two dependency hashes before import. No production private key or public-key file was read. Test-only 512-bit RSA keys are intentionally below production strength and must never be used outside disposable fixtures.

## 3. Trust model and binding

The prototype separates three purposes: one-use gameplay authorization, per-game execution attestation, and batch completion receipt. Each game attestation binds the approved batch/manifest, index/run ID, grant digest and nonce, source/runtime/supervisor identities, successful child exit, effective memory/runtime limits, and exact artifact inventory. The issuer validates ten ordered rows, ten distinct signed grants and consumption records, exact status rows, required result/manifest/status/log artifacts, output-path containment, resource/storage evidence, and result identity before it calls the receipt signer. In this test, the ten rows are generated from the preserved Stage 002 manifest constructor; they are **not** the authenticated 300-game schedule or its 30 issued block manifests. The receipt preserves the reviewed schema and signs batch ID, canonical approved manifest digest, raw status SHA-256, and count.

Production trust still needs three independently approved public-key identities and purposes. The verifier must retain the existing authorization-key pin for grants and receive a distinct receipt-key pin for receipt validation; the supervisor-attestation key is a third identity. A code constant or mutable key file alone does not constitute independent approval.

For production race resistance, an owner-approved Windows snapshot adapter must capture evidence after all workers terminate, reject reparse points, hold no-write/no-delete handles or copy from protected handles into signer-owned staging, and validate the same captured bytes it signs. The receipt issuer must be unable to modify evidence, and the worker/controller must be unable to invoke its signing operation. Publication must use signer-owned staging plus an atomic same-volume no-replace operation; conflicting destinations, temp remnants, or interruption produce no final receipt. These Windows controls have not been implemented or exercised.

## 4. Validation and CI

The following deterministic disposable suites ran successfully:

| Suite | Result | Meaning |
|---|---:|---|
| New end-to-end synthetic chain | 10 passed | Positive ten-game block issuance/verification; negative mutated result with recomputed unsigned inventory, incomplete batch, missing artifact, invalid attestation/grant, consumption mismatch, key substitution, path escape, unavailable signing key, interrupted publication, and existing receipt |
| Corrected verifier tests | 14 passed, 1 skipped | Verifier rejects trust/evidence attacks; Windows denied symlink creation (`WinError 1314`), while junction escape test passed |
| Historical vulnerability characterization | 9 passed | Assertions intentionally demonstrate that the preserved original verifier accepts three attack forms; these are not passes for the corrected verifier |

Total across the three invocations: **34 tests, 33 passed, 1 skipped**. The synthetic chain positive path signs only with test keys and independently verifies the receipt with the separate test receipt key. Invalid batch inputs and existing destinations are rejected before receipt signing; injected key failure and publication interruption leave no final receipt. The interruption/conflict test uses a mock atomic publisher and is not proof of Windows filesystem atomicity.

AST parsing and trailing-whitespace checks passed for the synthetic candidate files. Ruff is not installed in the qualified local interpreter. GitHub Actions run **41371824932** for PR #374 head `41f8f8b10583e342dd2f9db85946a1998cd2a80a` failed at `ruff format --check .`; lint and pytest were skipped. Run **41481911285** for head `cba82e68b576f566fda5cbb1bf7ada5587a3a143` identified formatting differences in both new candidates and three preserved verifier-review files. Run **41482237861** for head `d2499d85cd78578d2f463c98f926b7d9b093ff85` found four files to reformat: one trailing blank line in the synthetic model plus three pre-existing verifier-review files. After formatting the new candidates, exact-head run **41482520983** for `b2c9861da6ff5d3cc02b85fbf8175dc41f0f14f0` still failed at the format step on only those three preserved files (`corrected/verify_completed_batch.py`, `test_corrected_verifier_integrity.py`, and `test_verify_completed_batch_trust.py`). Lint and pytest were skipped. The two new candidates no longer appear in Ruff's failure list. The three prior files remain unchanged to preserve the existing review artifacts. No full gameplay test was run.

## 5. Independent review findings and readiness

Independent review of the complete new chain has **not** occurred. The current PR verifier does not verify signed per-game supervisor attestations with a separate key, and the actual Stage 002 supervisor has not been modified to emit them. There is no production receipt issuer, CNG key, Windows service identity, ACL policy, stable snapshot implementation, or real atomic no-replace publisher. The existing verifier's single public-key identity must be separated. CI is not green, and no CI run covers these new local candidates.

No production key creation, certificate/trust-store operation, PowerShell execution-policy change, grant issuance, wrapper launch, output write, game, deck change, or historical evidence access occurred. PR #374 remains draft.

## 6. Remaining approvals and next move

**BLOCKED.** Exact remaining requirements are: (1) independent review of the integrated attestation/issuer/verifier source chain; (2) owner/HQ approval of dedicated production key purposes, CNG identities, Windows service account and ACLs; (3) implementation and independent verification of the locked snapshot and atomic publisher; (4) separate-key integration into the verifier and real supervisor; (5) resolve the current Ruff-format CI failure and obtain exact-head CI without launching gameplay; (6) owner approval of trusted wrapper signing and process-only `AllSigned`; (7) approval of the final signed artifact; and (8) explicit HQ gameplay authorization.

**NEXT MOVE:** Send the isolated synthetic package and this report for independent source review. Resolve CI formatting in a separate reviewed correction and use a synthetic-only validation path; do not trigger a CI route that runs gameplay tests without approval. Do not create keys or alter service/ACL/trust policy until the workstation owner and HQ approve those exact boundaries. Keep PR #374 draft and gameplay blocked at 0/300.
