# Cardcade Completion-Receipt Signing Design & Synthetic Validation Report

**Assessment: DESIGN READY FOR HQ REVIEW; PRODUCTION SIGNING BLOCKED.** PR #374 remains draft. Batch status is 0/300; no production private key was opened, no certificate or trust-store changes were made, no production receipt was issued, and no grant or game was launched.

## Trust-boundary finding

A completion service must not sign a mutable `status.json` simply because it says `COMPLETE` or because its neighboring hashes agree. The corrected verifier candidate adds a detached receipt over the batch ID, approved manifest digest, raw status SHA-256, and completion count, but that receipt is meaningful only if a trusted issuer independently verifies the batch before signing. Signing an unvalidated status would convert untrusted claims into authenticated untrusted claims.

The current corrected verifier checks internal consistency, grants, consumption records, artifact inventory and the receipt. It does **not** receive a cryptographically authenticated per-game execution attestation from the supervisor. Therefore, the existing artifacts alone cannot establish that a self-consistent result set was actually produced by the authorized workers if an actor can rewrite the result files and status before receipt issuance. A production issuer must not be built on the assumption that a fresh hash scan alone closes this gap.

## Proposed signer architecture

Use two independently controlled components and three purpose-separated signing identities:

1. **HQ authorization issuer (existing authority):** signs one-use per-game grants. It remains separate from the completion path and does not sign completion receipts.
2. **Trusted Stage 002 supervisor (execution attestor):** after the worker and its Job Object have terminated, emits one signed per-game execution attestation. It binds the approved batch/manifest digests, game index and run ID, grant digest and consumed nonce, child exit/termination state, source/runtime/input identities, effective resource-limit readback, and exact required output inventory and hashes. Its signing operation is unavailable to the worker and batch controller.
3. **Completion Receipt Issuer (new, independently controlled authority):** runs under a restricted Windows service identity and has the only permission to use a dedicated non-exportable CNG key for `cardcade-stage002-batch-completion-v1` receipts. It verifies all ten attestations and their evidence before signing a receipt. Neither the gameplay authorization key nor supervisor-attestation key is reused for this purpose.

The Completion Receipt Issuer is the sole component authorized to create `*.completion-receipt.json`. It accepts only a batch identifier and a manifest whose digest is independently pinned to the approved 300-game schedule and current block. Callers cannot supply a key, validator path, public-key pin, output root, or alternate manifest policy. The issuer loads exact reviewed dependency identities and fails if any dependency or trust configuration differs.

### Key purpose and trust anchor

The receipt key is a **new dedicated identity**, purpose-limited to batch-completion receipts. It is not created or accessed during this design review. Its private key should be non-exportable in CNG and accessible only to the receipt-issuer service identity. The worker, AppContainer, controller, and ordinary interactive user receive no private-key or signing API access. The public key is distributed separately and pinned by an independently approved SHA-256 identity in the reviewed verifier configuration/release record. A public-key file at a mutable path, or a constant copied from the authorization issuer, is not sufficient proof of receipt-key approval.

The verifier's current one-key configuration must be separated: retain the authorization public-key pin for grant verification and add an independent receipt public-key path, fingerprint, and RSA-3072 profile for receipt verification. The existing receipt field set can remain unchanged; the signature is verified with the receipt key, while grants continue to use the authorization key. HQ must approve the receipt key's identity and signing purpose separately from the wrapper, verifier, and execution authorization.

## Receipt issuance sequence

1. Require exactly the approved block manifest and verify its canonical digest and row order against the approved schedule; reject extra, missing, duplicated, or substituted games.
2. Require all ten workers and Job Objects to be terminated. Verify the supervisor's signed per-game attestation for each manifest row, including exit status, identities, resource readback, grant digest, consumed nonce, and output-inventory digest.
3. Independently verify each grant signature and exact claim binding; verify each consumption record against the signed grant digest and require ten distinct nonces. The receipt issuer has read-only access to these records.
4. Take a stable evidence snapshot. First ensure the assigned tree has no reparse points and is rooted at the approved destination. Open and enumerate files by handle without following reparse points; hold handles that deny write/delete sharing while reading. Copy the exact bytes into a signer-controlled staging directory, verify file identities and signed supervisor inventory there, and perform all schema/identity/hash checks against that snapshot. Any mutation, replacement, missing file, mismatch, or inability to lock/read the snapshot aborts. The controller cannot write to signer staging.
5. Validate each result, run manifest, telemetry, stdout/stderr, status row, resource evidence, and inventory against the signed attestation and approved manifest. The status file is input data, never the trust source. Require full required artifact coverage and exact output-tree coverage.
6. Construct the reviewed receipt fields: schema, batch ID, approved manifest SHA-256, SHA-256 of the exact raw completed-status bytes from the snapshot, and completed-game count 10. Sign only after every validation succeeds.
7. Write the signed receipt to a unique temporary file in a signer-controlled directory using create-new semantics; flush file contents and metadata; atomically rename to the final receipt name without replacement. If the final receipt or conflicting temp file already exists, fail closed. A crash before the final rename leaves no accepted receipt. Never replace or silently retry a receipt.

Downstream verification recomputes the raw status digest and independently verifies the signed receipt, all ten supervisor attestations, required artifacts, grants and consumption records. Post-sign status modification invalidates the receipt. The signed attestations prevent a controller from making a changed result appear authentic by merely recomputing unsigned inventory hashes.

## Failure behavior

Missing/incorrect keys or trust pins, unavailable dependencies, wrong schedule, incomplete batch, a nonzero worker exit, absent/invalid attestation, grant or consumption mismatch, incomplete or unsafe artifact tree, changed file identity, failed lock/readback, interrupted signing, or an existing receipt all produce a non-success status and **no final receipt**. Preserve the partial evidence and diagnostic cause. Do not issue a replacement grant or retry signing automatically.

## Existing contract and exact candidates

The corrected verifier's receipt schema remains `cardcade-stage002-batch-completion-v1` with its existing five signed fields plus signature. Candidate identities from draft PR #374:

| Artifact | SHA-256 | Trust status |
|---|---|---|
| Corrected verifier candidate | `45d920a2128e430574ab2eed96f3bc62281d8128ab4e81b0155b7bc710232385` | Candidate only; independent approval outstanding |
| `stage002_authorization.py` | `1fd4db87131a0fef996fc2df7aee5f6634fdbc2d7b90f226c76217596fdb6540` | Exact dependency pin; not receipt-signer approval |
| `stage002_batch.py` | `30720c8d720b52a9538b79063d785e57dc37762bf5099215b7ee05cef0a80293` | Exact dependency pin; not receipt-signer approval |
| Corrected wrapper candidate | `f912753455f03013b484fde989a966fefc682aa41a16b2253d59a9dd8e8757ad` | Candidate only; PR remains draft |
| Integrity helper candidate | `b1fafc333a3c4a0720c8b84c23639eac70c40a09c6f180ac70d9ab9fa93af41d` | Candidate only |

No receipt-issuer executable, supervisor attestation signer, or production receipt key currently exists in this correction package. These are design requirements, not claims of implemented controls.

## Synthetic validation evidence

The existing test-only receipt fixture uses disposable temporary directories and a fixed test-only RSA key. It is not a production issuer and exercises no owner key. Re-run command:

```powershell
& '.diag003-preparation\python-nuget-3.13.15\tools\python.exe' -P -s -B -m unittest discover -s '.diag003-memory-independent-review\verifier-trust-review' -p 'test_corrected_verifier_integrity.py' -v
```

Result on this review: **15 tests run, 14 passed, 1 skipped**. The skipped symlink creation was denied by Windows (`WinError 1314`); the disposable Windows junction/reparse escape test passed. The positive fixture creates a complete ten-game mock batch, signs its mock completion receipt, and the corrected verifier accepts it. Negative fixtures reject a changed result with stale receipt, a changed result with recomputed unsigned status hashes but no valid new receipt, missing/empty required artifact inventories, traversal and out-of-tree paths, a modified dependency, unexpected public key, tampered grant, and missing/modified consumption record.

These results verify the **verifier-side receipt and evidence checks**. They do not prove that a production issuer validates before signing, that supervisor evidence is authenticated, that production ACLs prevent time-of-check/time-of-use changes, or that any production key is correctly isolated. The proposed signer design must receive its own synthetic tests before implementation approval: valid ten-attestation issuance; altered status/result/artifact; re-signed unsigned hashes; missing/invalid attestation; wrong grant/consumption; missing mandatory file; reparse escape; mutation during snapshot; missing key; conflicting receipt; and interruption before atomic publication. Each negative must demonstrate zero final receipt output.

## Independent review gates

- Approve the trust model and threat boundary, including supervisor attestation provenance.
- Review the exact issuer, supervisor-attestation, and verifier source identities before any key operation.
- Approve separate CNG key identities, purposes, service accounts, ACLs, and public-key pins; do not create keys or alter trust stores as part of this design step.
- Independently verify signer isolation, snapshot/locking behavior, and no-replace atomic publication on Windows.
- Verify receipt schema compatibility and require the verifier to use a distinct receipt public-key pin from the grant-verification key.
- Keep PR #374 draft; workstation-owner signing approval and explicit HQ gameplay authorization remain separate.

## Assessment and next action

**BLOCKED FOR PRODUCTION SIGNING AND GAMEPLAY.** The design is ready for HQ review, but the existing status/artifact set lacks a supervisor-authenticated execution attestation, the verifier currently uses one public-key identity for both grants and receipts, and no production receipt issuer exists. Smallest next action: HQ approves or revises this trust design and authorizes a separate, narrowly scoped synthetic implementation/review of supervisor attestations, the receipt issuer, and verifier key separation. Until then PR #374 stays draft and batch status remains 0/300.
